from __future__ import annotations
import os
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from graph.schema import (
    InfrastructureGraph,
    CycloneScenario,
    SimulationResult,
    AssetFailureDistribution,
    InterventionAction,
)
from graph.build import DependencyGraphManager
from data.seed_data import get_puri_infrastructure_graph, get_cyclone_scenarios
from sim.cascade import MonteCarloCascadeSimulator
from sim.aggregate import SimulationAggregator
from actions.catalogue import generate_candidate_actions
from actions.rank import ActionRanker
from actions.wow_layer import WowLayerEngine

app = FastAPI(
    title="Failure Clock API",
    description="Cyclone Impact & Infrastructure Vulnerability Forecaster API",
    version="1.0.0",
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory singletons and cache
graph_manager = DependencyGraphManager()
scenarios_list = get_cyclone_scenarios()
scenarios_dict: Dict[str, CycloneScenario] = {s.id: s for s in scenarios_list}
sim_engine = MonteCarloCascadeSimulator(graph_manager)
ranker = ActionRanker(graph_manager, sim_engine)
wow_engine = WowLayerEngine(graph_manager, sim_engine)

# Cache store: scenario_id -> { "raw": ..., "dist": ..., "clli": ..., "metrics": ..., "ranked_actions": ... }
sim_cache: Dict[str, Dict[str, Any]] = {}


def ensure_scenario_simulated(scenario_id: str, num_runs: int = 50) -> Dict[str, Any]:
    if scenario_id in sim_cache:
        return sim_cache[scenario_id]

    scenario = scenarios_dict.get(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")

    raw = sim_engine.run_simulation(
        track=scenario.track,
        num_runs=num_runs,
        time_horizon_h=36.0,
        dt_h=1.0,
        random_seed=42,
    )
    asset_dist, clli_timeline, metrics = SimulationAggregator.aggregate(raw, graph_manager)

    candidates = generate_candidate_actions(graph_manager)
    ranked_actions = ranker.rank_actions(
        candidate_actions=candidates,
        baseline_sim_raw=raw,
        baseline_asset_dist=asset_dist,
        track=scenario.track,
        num_runs=15,
        random_seed=42,
    )

    cache_entry = {
        "raw": raw,
        "dist": asset_dist,
        "clli": clli_timeline,
        "metrics": metrics,
        "ranked_actions": ranked_actions,
    }
    sim_cache[scenario_id] = cache_entry
    return cache_entry


@app.get("/api/health")
def get_health() -> Dict[str, str]:
    return {"status": "ok", "app": "Failure Clock", "version": "1.0.0"}


@app.get("/api/scenarios", response_model=List[CycloneScenario])
def list_scenarios() -> List[CycloneScenario]:
    return scenarios_list


@app.get("/api/graph", response_model=InfrastructureGraph)
def get_graph() -> InfrastructureGraph:
    return graph_manager.infra_graph


@app.post("/api/scenario/{scenario_id}/run")
def run_scenario(
    scenario_id: str,
    num_runs: int = Query(50, ge=10, le=500),
    force_refresh: bool = False,
) -> Dict[str, Any]:
    if force_refresh and scenario_id in sim_cache:
        del sim_cache[scenario_id]

    data = ensure_scenario_simulated(scenario_id, num_runs=num_runs)
    return {
        "scenario_id": scenario_id,
        "status": "completed",
        "num_runs": num_runs,
        "metrics": data["metrics"],
        "clli_timeline": data["clli"],
        "asset_count": len(data["dist"]),
    }


@app.get("/api/scenario/{scenario_id}/assets")
def get_scenario_assets(scenario_id: str) -> Dict[str, Any]:
    data = ensure_scenario_simulated(scenario_id)
    scenario = scenarios_dict[scenario_id]
    return {
        "scenario_id": scenario_id,
        "time_steps": data["raw"]["time_steps"],
        "assets": data["dist"],
        "metrics": data["metrics"],
        "clli_timeline": data["clli"],
        "track": [t.model_dump() for t in scenario.track],
    }


@app.get("/api/scenario/{scenario_id}/assets/{asset_id}/explain")
def explain_asset_failure(scenario_id: str, asset_id: str) -> Dict[str, Any]:
    data = ensure_scenario_simulated(scenario_id)
    dist = data["dist"].get(asset_id)
    if not dist:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found.")

    node = graph_manager.node_dict.get(asset_id)
    upstream = graph_manager.get_upstream_power_sources(asset_id)
    routes = graph_manager.get_resupply_routes_for_target(asset_id)

    return {
        "asset_id": asset_id,
        "name": dist.name,
        "type": dist.type,
        "criticality": dist.criticality,
        "p10_fail_time_h": dist.p10_fail_time_h,
        "p50_fail_time_h": dist.p50_fail_time_h,
        "p90_fail_time_h": dist.p90_fail_time_h,
        "dominant_cause": dist.dominant_cause,
        "cause_breakdown": dist.cause_breakdown,
        "causal_chain": dist.causal_chain,
        "upstream_power_nodes": upstream,
        "resupply_routes": routes,
        "node_attributes": node.attrs if node else {},
    }


@app.get("/api/scenario/{scenario_id}/asset/{asset_id}/explain")
def explain_asset_failure_alias(scenario_id: str, asset_id: str) -> Dict[str, Any]:
    """Alias for singular route compatibility."""
    return explain_asset_failure(scenario_id, asset_id)


@app.get("/api/scenario/{scenario_id}/actions", response_model=List[InterventionAction])
def get_scenario_actions(scenario_id: str) -> List[InterventionAction]:
    data = ensure_scenario_simulated(scenario_id)
    return data["ranked_actions"]


class WhatIfRequest(BaseModel):
    selected_action_ids: List[str]
    branch_time_h: float = -6.0


@app.post("/api/scenario/{scenario_id}/whatif")
def run_whatif_branch(scenario_id: str, req: WhatIfRequest) -> Dict[str, Any]:
    """
    Time Machine (F1): Fork a new timeline with user-selected interventions.
    Compares baseline vs branch with Common Random Numbers.
    """
    baseline_data = ensure_scenario_simulated(scenario_id)
    scenario = scenarios_dict[scenario_id]

    all_actions = baseline_data["ranked_actions"]
    selected_actions = [a for a in all_actions if a.id in req.selected_action_ids]

    baseline_clli_p50 = [pt[2] for pt in baseline_data["clli"]]

    # Pure identity branch if no interventions are selected
    if not selected_actions:
        return {
            "scenario_id": scenario_id,
            "branch_time_h": req.branch_time_h,
            "applied_actions": [],
            "baseline_metrics": baseline_data["metrics"],
            "branch_metrics": baseline_data["metrics"],
            "total_lifeline_points_saved": 0.0,
            "clli_comparison": {
                "time_steps": baseline_data["raw"]["time_steps"],
                "baseline_clli_p50": baseline_clli_p50,
                "branch_clli_p50": baseline_clli_p50,
                "reduction": [0.0] * len(baseline_clli_p50),
            },
            "branch_assets": {
                nid: {
                    "name": d.name,
                    "p50_fail_time_h": d.p50_fail_time_h,
                    "dominant_cause": d.dominant_cause,
                }
                for nid, d in baseline_data["dist"].items()
            },
        }

    # Run counterfactual branch with exact same 20 seeds
    num_branch_runs = 20
    branch_raw = sim_engine.run_simulation(
        track=scenario.track,
        num_runs=num_branch_runs,
        time_horizon_h=36.0,
        dt_h=1.0,
        random_seed=42,
        interventions=selected_actions,
    )
    branch_dist, branch_clli, branch_metrics = SimulationAggregator.aggregate(branch_raw, graph_manager)

    # Compute baseline reference on the identical 20 seeds for variance reduction
    base_raw_sub = {
        "time_steps": baseline_data["raw"]["time_steps"],
        "first_fails": {k: v[:num_branch_runs] for k, v in baseline_data["raw"]["first_fails"].items()},
        "causes": {k: v[:num_branch_runs] for k, v in baseline_data["raw"]["causes"].items()},
        "timelines": {k: v[:num_branch_runs] for k, v in baseline_data["raw"]["timelines"].items()},
        "clli_all_runs": baseline_data["raw"]["clli_all_runs"][:num_branch_runs],
        "causal_chains": baseline_data["raw"]["causal_chains"],
    }
    _, base_sub_clli, _ = SimulationAggregator.aggregate(base_raw_sub, graph_manager)

    base_p50_sub = [pt[2] for pt in base_sub_clli]
    branch_clli_p50 = [pt[2] for pt in branch_clli]
    pointwise_reduction = [
        round(max(b - br, 0.0), 2)
        for b, br in zip(base_p50_sub, branch_clli_p50)
    ]
    total_saved_points = round(sum(pointwise_reduction), 1)

    return {
        "scenario_id": scenario_id,
        "branch_time_h": req.branch_time_h,
        "applied_actions": [a.id for a in selected_actions],
        "baseline_metrics": baseline_data["metrics"],
        "branch_metrics": branch_metrics,
        "total_lifeline_points_saved": total_saved_points,
        "clli_comparison": {
            "time_steps": baseline_data["raw"]["time_steps"],
            "baseline_clli_p50": base_p50_sub,
            "branch_clli_p50": branch_clli_p50,
            "reduction": pointwise_reduction,
        },
        "branch_assets": {
            nid: {
                "name": d.name,
                "p50_fail_time_h": d.p50_fail_time_h,
                "dominant_cause": d.dominant_cause,
            }
            for nid, d in branch_dist.items()
        },
    }


@app.get("/api/scenario/{scenario_id}/doomsday")
def get_doomsday_board(
    scenario_id: str,
    current_time_h: float = Query(-12.0, ge=-48.0, le=48.0),
) -> Dict[str, Any]:
    """Last Safe Minute (F2) countdown board."""
    data = ensure_scenario_simulated(scenario_id)
    board = wow_engine.get_last_safe_minute_board(data["ranked_actions"], current_time_h)
    return {
        "scenario_id": scenario_id,
        "current_time_h": current_time_h,
        "actions_board": board,
    }


@app.get("/api/scenario/{scenario_id}/keystones")
def get_keystones_and_shapley(scenario_id: str) -> Dict[str, Any]:
    """Keystone Finder and Shapley Blame Graph (F6)."""
    data = ensure_scenario_simulated(scenario_id)
    if "keystones" not in data:
        scenario = scenarios_dict[scenario_id]
        data["keystones"] = wow_engine.compute_keystones_and_shapley(
            scenario.track, data["raw"], num_mc_runs=10
        )
    return data["keystones"]


@app.get("/api/scenario/{scenario_id}/crisis-council")
def get_crisis_council(scenario_id: str) -> Dict[str, Any]:
    """Grounded AI Crisis Council Deliberation (F4)."""
    data = ensure_scenario_simulated(scenario_id)
    scenario = scenarios_dict[scenario_id]
    result = wow_engine.simulate_crisis_council_deliberation(
        scenario.name, data["dist"], data["ranked_actions"]
    )
    return result


class RedTeamRequest(BaseModel):
    action_ids: Optional[List[str]] = None


@app.post("/api/scenario/{scenario_id}/redteam")
def run_redteam_test(
    scenario_id: str,
    req: Optional[RedTeamRequest] = Body(default=None),
) -> Dict[str, Any]:
    """Red Team Adversarial Stress Test (F3)."""
    data = ensure_scenario_simulated(scenario_id)
    redteam_scenario = scenarios_dict.get("red_team_storm") or scenarios_dict[scenario_id]

    if req and req.action_ids is not None:
        custom_actions = [a for a in data["ranked_actions"] if a.id in req.action_ids]
        return wow_engine.run_red_team_stress_test(
            redteam_scenario.track, custom_actions, num_mc_runs=20
        )

    if "redteam" not in data:
        data["redteam"] = wow_engine.run_red_team_stress_test(
            redteam_scenario.track, data["ranked_actions"][:3], num_mc_runs=20
        )
    return data["redteam"]


# Mount web directory if it exists
static_dir = os.path.join(os.path.dirname(__file__), "..", "web")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

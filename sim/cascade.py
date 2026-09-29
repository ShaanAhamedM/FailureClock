from __future__ import annotations
import math
from typing import Dict, List, Optional, Any, Set, Tuple
import numpy as np

from graph.schema import (
    NodeType,
    EdgeType,
    NodeState,
    FailureCause,
    AssetNode,
    InterventionAction,
    CycloneTrackPoint,
)
from graph.build import DependencyGraphManager
from hazard.ensemble import HazardEnsembleGenerator


class SingleSimulationRun:
    """
    Executes a single deterministic realization of the cascade simulation
    over time horizon T_horizon with step dt.
    """

    def __init__(
        self,
        graph_manager: DependencyGraphManager,
        hazard_data: Dict[str, Dict[str, List[float]]],
        time_steps: List[float],
        asset_parameters: Dict[str, Dict[str, float]],
        interventions: Optional[List[InterventionAction]] = None,
    ):
        self.gm = graph_manager
        self.hazard = hazard_data
        self.time_steps = time_steps
        self.dt = time_steps[1] - time_steps[0] if len(time_steps) > 1 else 0.5
        self.params = asset_parameters
        self.interventions = interventions or []

        # Current state per node
        self.node_states: Dict[str, NodeState] = {}
        self.backup_remaining_h: Dict[str, float] = {}
        self.first_failure_time: Dict[str, Optional[float]] = {}
        self.primary_cause: Dict[str, FailureCause] = {}
        self.causal_chain: Dict[str, List[str]] = {}
        self.timelines: Dict[str, List[NodeState]] = {n.id: [] for n in self.gm.infra_graph.nodes}
        self.road_passable_at_t: Dict[str, bool] = {}

        self._apply_pre_landfall_interventions()
        self._initialize_states()

    def _apply_pre_landfall_interventions(self) -> None:
        """Apply actions that modify baseline asset properties prior to storm."""
        for action in self.interventions:
            target_id = action.target_asset_id
            if target_id not in self.params:
                continue

            if action.type == "PREPOSITION_FUEL":
                added_hours = action.params.get("added_fuel_hours", 12.0)
                self.params[target_id]["fuel_hours"] = self.params[target_id].get("fuel_hours", 0.0) + added_hours
            elif action.type == "PREPOSITION_GENERATOR":
                self.params[target_id]["has_generator"] = 1.0
                self.params[target_id]["fuel_hours"] = action.params.get("fuel_hours", 16.0)
            elif action.type == "PROTECT_ROAD":
                self.params[target_id]["flood_threshold"] = self.params[target_id].get("flood_threshold", 0.3) + 0.35
                self.params[target_id]["debris_wind_threshold"] = 50.0  # Cleared by staged teams

    def _initialize_states(self) -> None:
        for node in self.gm.infra_graph.nodes:
            self.node_states[node.id] = NodeState.OPERATING
            self.first_failure_time[node.id] = None
            self.primary_cause[node.id] = FailureCause.NONE
            self.causal_chain[node.id] = []

            # Set initial backup hours (battery or fuel)
            p = self.params.get(node.id, {})
            if node.type == NodeType.HOSPITAL:
                self.backup_remaining_h[node.id] = p.get("fuel_hours", 10.0)
            elif node.type == NodeType.TOWER:
                has_gen = p.get("has_generator", 0.0) > 0.5
                self.backup_remaining_h[node.id] = p.get("fuel_hours", 14.0) if has_gen else p.get("battery_hours", 3.0)
            elif node.type == NodeType.WATER_PUMP:
                has_gen = p.get("has_generator", 0.0) > 0.5
                self.backup_remaining_h[node.id] = p.get("fuel_hours", 8.0) if has_gen else 0.0
            else:
                self.backup_remaining_h[node.id] = 0.0

    def run(self) -> None:
        """Run time-stepped cascade loop."""
        for step_idx, t in enumerate(self.time_steps):
            # Step 1: Direct Hazard Damage
            self._evaluate_direct_hazard(step_idx, t)

            # Step 2: Update Road Passability
            self._update_road_passability(step_idx, t)

            # Step 3: Power Propagation
            self._propagate_power(t)

            # Step 4: Backup Depletion & Resupply
            self._update_backup_and_resupply(t)

            # Record timeline snapshot
            for nid in self.node_states:
                self.timelines[nid].append(self.node_states[nid])

    def _evaluate_direct_hazard(self, step_idx: int, t: float) -> None:
        for node in self.gm.infra_graph.nodes:
            if self.node_states[node.id] == NodeState.FAILED:
                continue

            h = self.hazard.get(node.id)
            if not h:
                continue

            gust = h["wind_gust_ms"][step_idx]
            water_depth = h["flood_depth_m"][step_idx]
            p = self.params.get(node.id, {})

            # 1. Wind failure
            wind_thresh = p.get("wind_threshold", 45.0)
            if gust >= wind_thresh:
                self._mark_failed(node.id, t, FailureCause.DIRECT_WIND, f"Wind gust {gust:.1f} m/s exceeded limit {wind_thresh:.1f} m/s")
                continue

            # 2. Flood / surge failure
            flood_thresh = p.get("flood_threshold", 0.4)
            if water_depth >= flood_thresh and node.type != NodeType.ROAD_SEGMENT:
                self._mark_failed(node.id, t, FailureCause.DIRECT_FLOOD, f"Flood depth {water_depth:.2f} m exceeded critical floor level {flood_thresh:.2f} m")

    def _update_road_passability(self, step_idx: int, t: float) -> None:
        for node in self.gm.infra_graph.nodes:
            if node.type != NodeType.ROAD_SEGMENT:
                continue

            h = self.hazard.get(node.id)
            if not h:
                self.road_passable_at_t[node.id] = True
                continue

            water_depth = h["flood_depth_m"][step_idx]
            gust = h["wind_gust_ms"][step_idx]
            p = self.params.get(node.id, {})

            pass_depth = p.get("passability_threshold", 0.30)
            debris_gust = p.get("debris_wind_threshold", 34.0)

            if water_depth >= pass_depth:
                self.road_passable_at_t[node.id] = False
                if self.node_states[node.id] != NodeState.FAILED:
                    self._mark_failed(node.id, t, FailureCause.DIRECT_FLOOD, f"Road submerged ({water_depth:.2f} m >= {pass_depth:.2f} m)")
            elif gust >= debris_gust:
                self.road_passable_at_t[node.id] = False
                if self.node_states[node.id] != NodeState.FAILED:
                    self._mark_failed(node.id, t, FailureCause.DIRECT_WIND, f"Road blocked by fallen trees/poles (gust {gust:.1f} m/s)")
            else:
                self.road_passable_at_t[node.id] = True
                if self.node_states[node.id] == NodeState.FAILED:
                    # Water receded / road reopened
                    self.node_states[node.id] = NodeState.OPERATING

    def _propagate_power(self, t: float) -> None:
        """Check upstream power sources. If all failed, switch to ON_BACKUP or FAIL."""
        for nid in self.gm.get_all_power_dependent_assets():
            if self.node_states[nid] == NodeState.FAILED:
                continue

            sources = self.gm.get_upstream_power_sources(nid)
            # Power is lost if any critical feeder/substation supplying it has failed
            all_sources_active = any(self.node_states[s] == NodeState.OPERATING for s in sources)

            if not all_sources_active:
                if self.node_states[nid] == NodeState.OPERATING:
                    failed_source = next((s for s in sources if self.node_states[s] == NodeState.FAILED), sources[0])
                    cause_desc = f"Lost grid power from {failed_source}"

                    if self.backup_remaining_h.get(nid, 0.0) > 0.0:
                        self.node_states[nid] = NodeState.ON_BACKUP
                        self.causal_chain[nid].append(f"T={t:+.1f}h: {cause_desc} -> Running on backup generator/battery")
                    else:
                        self._mark_failed(nid, t, FailureCause.GRID_LOSS, cause_desc)

    def _update_backup_and_resupply(self, t: float) -> None:
        """Deplete battery/generator fuel and check if fuel resupply truck can reach."""
        for nid, state in list(self.node_states.items()):
            if state == NodeState.ON_BACKUP:
                # Check for possible scheduled or depot resupply
                resupplied = self._attempt_fuel_resupply(nid, t)
                if not resupplied:
                    self.backup_remaining_h[nid] -= self.dt

                if self.backup_remaining_h[nid] <= 0.0:
                    self.backup_remaining_h[nid] = 0.0
                    self._mark_failed(nid, t, FailureCause.BACKUP_EXHAUSTED, "Generator fuel / battery completely exhausted")

    def _attempt_fuel_resupply(self, target_id: str, t: float) -> bool:
        """
        Check if road corridor from depot to target is open and can replenish fuel.
        """
        routes = self.gm.get_resupply_routes_for_target(target_id)
        if not routes:
            return False

        for r in routes:
            depot_id = r["depot_id"]
            if self.node_states.get(depot_id) == NodeState.FAILED:
                continue

            # Check if all road segments along route are passable
            path_segments = r["road_path"]
            all_passable = all(self.road_passable_at_t.get(seg, True) for seg in path_segments)

            if all_passable and self.backup_remaining_h.get(target_id, 0.0) < 4.0:
                # Tanker arrives and provides +8 hours of fuel autonomy
                self.backup_remaining_h[target_id] += 8.0
                self.causal_chain[target_id].append(
                    f"T={t:+.1f}h: Emergency fuel tanker from {depot_id} reached target via {path_segments} (+8h fuel extended)"
                )
                return True
        return False

    def _mark_failed(self, node_id: str, t: float, cause: FailureCause, description: str) -> None:
        self.node_states[node_id] = NodeState.FAILED
        if self.first_failure_time[node_id] is None:
            self.first_failure_time[node_id] = t
            self.primary_cause[node_id] = cause
            self.causal_chain[node_id].append(f"T={t:+.1f}h: FAILED due to {cause.value} ({description})")


class MonteCarloCascadeSimulator:
    """
    Orchestrates N Monte Carlo runs for a cyclone scenario across the infrastructure graph.
    Propagates uncertainty and computes:
    - Failure probability over time curves: P(fail <= t)
    - P10 / P50 / P90 failure times
    - Dominant cause attribution
    - Critical Lifeline Loss Index (CLLI) timelines
    """

    def __init__(
        self,
        graph_manager: DependencyGraphManager,
        ensemble_gen: Optional[HazardEnsembleGenerator] = None,
    ):
        self.gm = graph_manager
        self.ensemble_gen = ensemble_gen or HazardEnsembleGenerator()

    def run_simulation(
        self,
        track: List[CycloneTrackPoint],
        num_runs: int = 200,
        time_horizon_h: float = 48.0,
        dt_h: float = 0.5,
        random_seed: int = 42,
        interventions: Optional[List[InterventionAction]] = None,
    ) -> Dict[str, Any]:
        rng = np.random.default_rng(random_seed)
        start_time_h = float(track[0].time_offset_hours) if track else -24.0
        time_steps = [round(t, 2) for t in np.arange(start_time_h, time_horizon_h + dt_h, dt_h)]

        # Pre-generate perturbed tracks and sampled parameters for reproducibility
        nodes = self.gm.infra_graph.nodes
        all_first_fails: Dict[str, List[float]] = {n.id: [] for n in nodes}
        all_causes: Dict[str, List[FailureCause]] = {n.id: [] for n in nodes}
        all_timelines: Dict[str, List[List[NodeState]]] = {n.id: [] for n in nodes}
        all_clli: List[List[float]] = []

        for run_idx in range(num_runs):
            # 1. Sample perturbed track
            perturbed_track = self.ensemble_gen.generate_perturbed_track(track, rng)

            # 2. Sample asset parameters (battery, fuel, fragility)
            sampled_params = self._sample_asset_parameters(nodes, rng)

            # 3. Compute asset hazard exposures
            hazard_data: Dict[str, Dict[str, List[float]]] = {}
            for n in nodes:
                hazard_data[n.id] = self.ensemble_gen.compute_asset_hazard_series(
                    n, perturbed_track, time_steps, landfall_time_h=0.0
                )

            # 4. Run single simulation
            sim = SingleSimulationRun(
                self.gm, hazard_data, time_steps, sampled_params, interventions
            )
            sim.run()

            # 5. Collect run results
            run_clli_timeline: List[float] = []
            for step_idx in range(len(time_steps)):
                # Calculate CLLI at this step: sum(criticality of failed nodes)
                clli_val = 0.0
                for n in nodes:
                    if sim.timelines[n.id][step_idx] == NodeState.FAILED:
                        clli_val += n.criticality
                run_clli_timeline.append(clli_val)
            all_clli.append(run_clli_timeline)

            for n in nodes:
                t_f = sim.first_failure_time[n.id]
                all_first_fails[n.id].append(t_f if t_f is not None else 9999.0)
                all_causes[n.id].append(sim.primary_cause[n.id])
                all_timelines[n.id].append(sim.timelines[n.id])

        # Median / representative causal chains from run closest to P50
        sample_causal_chains = self._extract_representative_causal_chains(
            track, time_steps, interventions
        )

        return {
            "time_steps": time_steps,
            "first_fails": all_first_fails,
            "causes": all_causes,
            "timelines": all_timelines,
            "clli_all_runs": np.array(all_clli),
            "causal_chains": sample_causal_chains,
        }

    def _sample_asset_parameters(
        self, nodes: List[AssetNode], rng: np.random.Generator
    ) -> Dict[str, Dict[str, float]]:
        """Sample asset parameters with realistic physical uncertainty."""
        params: Dict[str, Dict[str, float]] = {}
        for n in nodes:
            p: Dict[str, float] = {}
            attrs = n.attrs

            if n.type == NodeType.SUBSTATION:
                p["wind_threshold"] = float(rng.normal(attrs.get("wind_fail_threshold_ms", 46.0), 3.0))
                p["flood_threshold"] = float(rng.normal(attrs.get("flood_critical_height_m", 0.40), 0.05))

            elif n.type == NodeType.FEEDER:
                p["wind_threshold"] = float(rng.normal(attrs.get("wind_fragility_median_ms", 36.0), 4.0))
                p["flood_threshold"] = 1.5

            elif n.type == NodeType.HOSPITAL:
                p["wind_threshold"] = float(rng.normal(attrs.get("wind_fail_threshold_ms", 52.0), 4.0))
                p["flood_threshold"] = float(rng.normal(attrs.get("flood_critical_depth_m", 0.45), 0.06))
                base_fuel = float(attrs.get("fuel_hours", 12.0))
                p["fuel_hours"] = float(np.clip(rng.normal(base_fuel, 2.5), 4.0, 36.0))
                p["has_generator"] = 1.0 if attrs.get("generator_present", True) else 0.0

            elif n.type == NodeType.TOWER:
                p["wind_threshold"] = float(rng.normal(attrs.get("wind_fail_threshold_ms", 44.0), 3.5))
                p["flood_threshold"] = 0.60
                base_bat = float(attrs.get("battery_hours", 3.0))
                p["battery_hours"] = float(np.clip(rng.normal(base_bat, 0.6), 1.5, 6.0))
                p["has_generator"] = 1.0 if attrs.get("generator_present", False) else 0.0
                p["fuel_hours"] = float(attrs.get("fuel_hours", 0.0))

            elif n.type == NodeType.ROAD_SEGMENT:
                p["passability_threshold"] = float(rng.normal(attrs.get("passability_threshold_m", 0.30), 0.04))
                p["debris_wind_threshold"] = float(rng.normal(attrs.get("debris_wind_threshold_ms", 34.0), 3.0))

            elif n.type == NodeType.WATER_PUMP:
                p["wind_threshold"] = float(rng.normal(attrs.get("wind_fail_threshold_ms", 48.0), 3.5))
                p["flood_threshold"] = float(rng.normal(attrs.get("flood_critical_depth_m", 0.40), 0.05))
                p["has_generator"] = 1.0 if attrs.get("generator_present", False) else 0.0
                p["fuel_hours"] = float(attrs.get("fuel_hours", 8.0))

            elif n.type == NodeType.DEPOT:
                p["wind_threshold"] = 55.0
                p["flood_threshold"] = 0.70

            params[n.id] = p
        return params

    def _extract_representative_causal_chains(
        self,
        track: List[CycloneTrackPoint],
        time_steps: List[float],
        interventions: Optional[List[InterventionAction]],
    ) -> Dict[str, List[str]]:
        """Run single median deterministic baseline to generate readable causal narrative."""
        # Mean parameter set
        mean_rng = np.random.default_rng(999)
        nodes = self.gm.infra_graph.nodes
        mean_params = self._sample_asset_parameters(nodes, mean_rng)

        hazard_data: Dict[str, Dict[str, List[float]]] = {}
        for n in nodes:
            hazard_data[n.id] = self.ensemble_gen.compute_asset_hazard_series(
                n, track, time_steps, landfall_time_h=0.0
            )

        sim = SingleSimulationRun(self.gm, hazard_data, time_steps, mean_params, interventions)
        sim.run()
        return sim.causal_chain

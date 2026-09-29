from __future__ import annotations
from typing import Dict, List, Any, Tuple
import numpy as np

from graph.schema import (
    AssetFailureDistribution,
    NodeState,
    FailureCause,
    NodeType,
)
from graph.build import DependencyGraphManager


class SimulationAggregator:
    """
    Aggregates Monte Carlo cascade outputs into percentile distributions,
    probability curves, dominant cause attributions, and CLLI metrics.
    """

    @staticmethod
    def aggregate(
        raw_sim: Dict[str, Any],
        graph_manager: DependencyGraphManager,
    ) -> Tuple[Dict[str, AssetFailureDistribution], List[Tuple[float, float, float, float]], Dict[str, float]]:
        time_steps: List[float] = raw_sim["time_steps"]
        first_fails: Dict[str, List[float]] = raw_sim["first_fails"]
        causes: Dict[str, List[FailureCause]] = raw_sim["causes"]
        timelines: Dict[str, List[List[NodeState]]] = raw_sim["timelines"]
        clli_all: np.ndarray = raw_sim["clli_all_runs"]
        causal_chains: Dict[str, List[str]] = raw_sim["causal_chains"]

        asset_dist: Dict[str, AssetFailureDistribution] = {}
        nodes = graph_manager.infra_graph.nodes
        num_runs = clli_all.shape[0]

        # 1. Asset Distributions
        for node in nodes:
            fails = np.array(first_fails[node.id])
            finite_fails = fails[fails < 9000.0]

            if len(finite_fails) > 0:
                p10 = float(np.percentile(finite_fails, 10))
                p50 = float(np.percentile(finite_fails, 50))
                p90 = float(np.percentile(finite_fails, 90))
            else:
                p10, p50, p90 = None, None, None

            # Probability of failure curve P(fail <= t)
            prob_curve: List[Tuple[float, float]] = []
            for t in time_steps:
                prob = float(np.mean(fails <= t))
                prob_curve.append((t, round(prob, 3)))

            # Cause breakdown
            node_causes = causes[node.id]
            cause_counts: Dict[str, int] = {}
            for c in node_causes:
                if c != FailureCause.NONE:
                    c_name = c.value
                    cause_counts[c_name] = cause_counts.get(c_name, 0) + 1

            total_failed_runs = max(len(finite_fails), 1)
            cause_pcts: Dict[str, float] = {}
            for c_name, count in cause_counts.items():
                cause_pcts[c_name] = round((count / total_failed_runs) * 100.0, 1)

            dominant = max(cause_pcts.items(), key=lambda x: x[1])[0] if cause_pcts else "NONE"

            # Median state timeline
            node_timelines = timelines[node.id]  # list of runs, each has len(time_steps)
            state_timeline_p50: List[Tuple[float, NodeState]] = []
            for step_idx, t in enumerate(time_steps):
                step_states = [node_timelines[r][step_idx] for r in range(num_runs)]
                # Majority vote for state
                if step_states.count(NodeState.FAILED) >= num_runs * 0.5:
                    rep_state = NodeState.FAILED
                elif step_states.count(NodeState.ON_BACKUP) >= num_runs * 0.3:
                    rep_state = NodeState.ON_BACKUP
                else:
                    rep_state = NodeState.OPERATING
                state_timeline_p50.append((t, rep_state))

            asset_dist[node.id] = AssetFailureDistribution(
                asset_id=node.id,
                name=node.name,
                type=node.type,
                criticality=node.criticality,
                p10_fail_time_h=round(p10, 1) if p10 is not None else None,
                p50_fail_time_h=round(p50, 1) if p50 is not None else None,
                p90_fail_time_h=round(p90, 1) if p90 is not None else None,
                prob_fail_curve=prob_curve,
                dominant_cause=dominant,
                cause_breakdown=cause_pcts,
                causal_chain=causal_chains.get(node.id, []),
                state_timeline_p50=state_timeline_p50,
            )

        # 2. CLLI Timeline (P10, P50, P90)
        # clli_all has shape (num_runs, len(time_steps))
        clli_timeline: List[Tuple[float, float, float, float]] = []
        for step_idx, t in enumerate(time_steps):
            vals = clli_all[:, step_idx]
            p10 = float(np.percentile(vals, 10))
            p50 = float(np.percentile(vals, 50))
            p90 = float(np.percentile(vals, 90))
            clli_timeline.append((t, round(p10, 2), round(p50, 2), round(p90, 2)))

        # 3. Healthcare Impact & Patient Hours at Risk (F11)
        # Integration of bed capacity * hours without power/road access
        dt = time_steps[1] - time_steps[0] if len(time_steps) > 1 else 0.5
        total_patient_hours_at_risk = 0.0
        hospitals = [n for n in nodes if n.type == NodeType.HOSPITAL]
        for h in hospitals:
            beds = h.attrs.get("beds", 50)
            h_timeline = asset_dist[h.id].state_timeline_p50
            for t, st in h_timeline:
                if st in (NodeState.FAILED, NodeState.ON_BACKUP):
                    total_patient_hours_at_risk += beds * dt

        summary_metrics = {
            "total_patient_hours_at_risk": round(total_patient_hours_at_risk, 0),
            "peak_clli_p50": max(p[2] for p in clli_timeline),
            "median_landfall_outage_pct": round(
                np.mean([asset_dist[n.id].prob_fail_curve[len(time_steps)//2][1] for n in nodes]) * 100, 1
            ),
        }

        return asset_dist, clli_timeline, summary_metrics

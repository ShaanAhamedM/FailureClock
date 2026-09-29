from __future__ import annotations
from typing import List, Dict, Any, Optional
import numpy as np

from graph.schema import InterventionAction, CycloneTrackPoint, AssetFailureDistribution
from graph.build import DependencyGraphManager
from sim.cascade import MonteCarloCascadeSimulator


class ActionRanker:
    """
    Ranks interventions using counterfactual Monte Carlo simulation with
    Common Random Numbers (CRN) and computes route-dependent Last Safe Minute deadlines.
    """

    def __init__(
        self,
        graph_manager: DependencyGraphManager,
        simulator: MonteCarloCascadeSimulator,
    ):
        self.gm = graph_manager
        self.sim = simulator

    def rank_actions(
        self,
        candidate_actions: List[InterventionAction],
        baseline_sim_raw: Dict[str, Any],
        baseline_asset_dist: Dict[str, AssetFailureDistribution],
        track: List[CycloneTrackPoint],
        num_runs: int = 50,  # Fast CRN counterfactual evaluation
        random_seed: int = 42,
    ) -> List[InterventionAction]:
        baseline_clli_mean = np.mean(baseline_sim_raw["clli_all_runs"], axis=0)
        time_steps = baseline_sim_raw["time_steps"]
        time_horizon_h = max(time_steps)
        dt_h = time_steps[1] - time_steps[0] if len(time_steps) > 1 else 0.5
        ranked_actions: List[InterventionAction] = []

        for act in candidate_actions:
            # 1. Compute Route-Dependent Last Safe Minute (F2)
            self._compute_last_safe_minute(act, baseline_asset_dist)

            # 2. Run Counterfactual Simulation with CRN (Common Random Numbers)
            cf_raw = self.sim.run_simulation(
                track=track,
                num_runs=num_runs,
                time_horizon_h=time_horizon_h,
                dt_h=dt_h,
                random_seed=random_seed,
                interventions=[act],
            )
            cf_clli_mean = np.mean(cf_raw["clli_all_runs"], axis=0)

            # 3. Expected CLLI Reduction = sum of CLLI reduction across all time steps
            clli_reduction = float(np.sum(np.maximum(baseline_clli_mean - cf_clli_mean, 0.0)))
            act.expected_benefit_clli_reduction = round(clli_reduction, 2)

            target_node = self.gm.node_dict.get(act.target_asset_id)
            target_name = target_node.name if target_node else act.target_asset_id
            act.benefit_summary = (
                f"Reduces total cumulative lifeline loss by {clli_reduction:.1f} point-hours. "
                f"Secures {target_name} during peak storm impact."
            )

            ranked_actions.append(act)

        # Sort descending by benefit
        ranked_actions.sort(key=lambda a: a.expected_benefit_clli_reduction, reverse=True)
        return ranked_actions

    def _compute_last_safe_minute(
        self, action: InterventionAction, asset_dist: Dict[str, AssetFailureDistribution]
    ) -> None:
        """
        Compute latest feasible departure deadline before route corridors flood/block.
        """
        if not action.route_asset_ids:
            action.deadline_h = -4.0
            action.deadline_confidence_p10_h = -6.0
            action.deadline_confidence_p50_h = -4.0
            action.deadline_confidence_p90_h = -2.0
            return

        p10_closures: List[float] = []
        p50_closures: List[float] = []
        p90_closures: List[float] = []

        for road_id in action.route_asset_ids:
            dist = asset_dist.get(road_id)
            if dist:
                if dist.p10_fail_time_h is not None:
                    p10_closures.append(dist.p10_fail_time_h)
                if dist.p50_fail_time_h is not None:
                    p50_closures.append(dist.p50_fail_time_h)
                if dist.p90_fail_time_h is not None:
                    p90_closures.append(dist.p90_fail_time_h)

        travel_buffer_h = 1.0  # 1 hour tanker transit + deployment time

        if p50_closures:
            earliest_p50 = min(p50_closures) - travel_buffer_h
            earliest_p10 = (min(p10_closures) - travel_buffer_h) if p10_closures else (earliest_p50 - 2.0)
            earliest_p90 = (min(p90_closures) - travel_buffer_h) if p90_closures else (earliest_p50 + 2.0)

            action.deadline_h = round(earliest_p50, 1)
            action.deadline_confidence_p10_h = round(earliest_p10, 1)  # Conservative (P10 road closure)
            action.deadline_confidence_p50_h = round(earliest_p50, 1)  # Expected
            action.deadline_confidence_p90_h = round(earliest_p90, 1)  # Optimistic
        else:
            action.deadline_h = -5.0
            action.deadline_confidence_p10_h = -7.0
            action.deadline_confidence_p50_h = -5.0
            action.deadline_confidence_p90_h = -3.0

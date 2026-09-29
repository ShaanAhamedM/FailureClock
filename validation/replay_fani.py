#!/usr/bin/env python3
"""
Failure Clock Validation: Cyclone Fani (May 2019) Historical Replay
Compares model predictions against curated ground-truth records from
OSDMA, OPTCL, and NDMA post-disaster assessments.
"""

import csv
import os
from typing import List, Dict, Any
import numpy as np
from scipy.stats import spearmanr

from graph.build import DependencyGraphManager
from data.seed_data import get_cyclone_scenarios
from sim.cascade import MonteCarloCascadeSimulator
from sim.aggregate import SimulationAggregator


def run_validation_evaluation():
    print("=" * 70)
    print("FAILURE CLOCK: HISTORICAL VALIDATION REPORT (Cyclone Fani, May 2019)")
    print("=" * 70)

    # 1. Load Ground Truth
    gt_file = os.path.join(os.path.dirname(__file__), "ground_truth.csv")
    ground_truth = []
    with open(gt_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ground_truth.append({
                "asset_id": row["asset_id"],
                "name": row["name"],
                "actual_failed": row["actual_failed"].lower() == "true",
                "actual_fail_time_h": float(row["actual_fail_time_rel_landfall_h"]),
                "source": row["source"],
            })

    print(f"Loaded {len(ground_truth)} curated ground-truth validation points from official records.\n")

    # 2. Run Failure Clock Simulation on Cyclone Fani Track
    gm = DependencyGraphManager()
    scenarios = get_cyclone_scenarios()
    fani_scenario = next(s for s in scenarios if s.id == "fani_2019")

    print("Running 100 Monte Carlo cascade simulations on Fani track & error cone...")
    sim = MonteCarloCascadeSimulator(gm)
    raw = sim.run_simulation(
        track=fani_scenario.track,
        num_runs=100,
        time_horizon_h=36.0,
        dt_h=0.5,
        random_seed=42,
    )
    asset_dist, clli_timeline, metrics = SimulationAggregator.aggregate(raw, gm)

    # 3. Compute Metrics
    actual_times = []
    pred_times_p50 = []
    correct_failure_detection = 0

    print("\nDetailed Asset-by-Asset Replay Comparison:")
    print("-" * 75)
    print(f"{'Asset ID':<18} | {'Actual (T)':<10} | {'P10':<6} | {'P50':<6} | {'P90':<6} | {'Abs Err':<7} | {'Cause':<15}")
    print("-" * 75)

    errors = []
    for gt in ground_truth:
        aid = gt["asset_id"]
        pred = asset_dist.get(aid)
        if not pred:
            continue

        p10 = f"{pred.p10_fail_time_h:+.1f}h" if pred.p10_fail_time_h is not None else "N/A"
        p50 = f"{pred.p50_fail_time_h:+.1f}h" if pred.p50_fail_time_h is not None else "N/A"
        p90 = f"{pred.p90_fail_time_h:+.1f}h" if pred.p90_fail_time_h is not None else "N/A"

        p_fail_final = pred.prob_fail_curve[-1][1] if pred.prob_fail_curve else 0.0
        if p_fail_final >= 0.5:
            correct_failure_detection += 1

        if pred.p50_fail_time_h is not None:
            err = abs(pred.p50_fail_time_h - gt["actual_fail_time_h"])
            errors.append(err)
            actual_times.append(gt["actual_fail_time_h"])
            pred_times_p50.append(pred.p50_fail_time_h)
            err_str = f"{err:.1f}h"
        else:
            err_str = "N/A"

        print(f"{aid:<18} | {gt['actual_fail_time_h']:+6.1f}h    | {p10:<6} | {p50:<6} | {p90:<6} | {err_str:<7} | {pred.dominant_cause:<15}")

    print("-" * 75)

    # Summary Statistics
    recall = (correct_failure_detection / len(ground_truth)) * 100.0
    mae = float(np.median(errors)) if errors else 0.0
    mean_err = float(np.mean(errors)) if errors else 0.0

    rank_corr = 0.0
    if len(actual_times) > 2:
        res = spearmanr(actual_times, pred_times_p50)
        rank_corr = float(res.statistic)

    print("\nEVALUATION METRICS SUMMARY (Per Spec Section 12):")
    print(f"  • Failure Detection Recall:     {recall:.1f}% ({correct_failure_detection}/{len(ground_truth)} correct)")
    print(f"  • Median Absolute Timing Error: {mae:.2f} hours (Mean: {mean_err:.2f} h)")
    print(f"  • Spearman Sequence Correlation: {rank_corr:.2f} (Target > 0.70)")
    print(f"  • Total Ground Truth Points:    {len(ground_truth)} (Puri District, Fani 2019)")
    print("=" * 70)

    return {
        "recall": recall,
        "mae": mae,
        "rank_corr": rank_corr,
        "ground_truth_count": len(ground_truth),
    }


if __name__ == "__main__":
    run_validation_evaluation()

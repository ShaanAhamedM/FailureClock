import pytest
from validation.replay_fani import run_validation_evaluation


def test_fani_historical_validation():
    metrics = run_validation_evaluation()
    assert metrics["ground_truth_count"] >= 9
    assert metrics["recall"] >= 90.0
    assert metrics["rank_corr"] >= 0.70

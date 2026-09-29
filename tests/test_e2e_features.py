import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_all_scenarios_assets():
    for scenario_id in ["severe_cyclone_live", "fani_2019", "red_team_storm"]:
        res = client.get(f"/api/scenario/{scenario_id}/assets")
        assert res.status_code == 200, f"Failed for {scenario_id}"
        data = res.json()
        assert "assets" in data
        assert len(data["assets"]) == 29
        assert "track" in data and len(data["track"]) > 0
        assert "time_steps" in data and len(data["time_steps"]) > 0
        assert "metrics" in data


def test_all_nodes_explain_both_routes():
    res = client.get("/api/graph")
    nodes = res.json()["nodes"]
    for n in nodes:
        nid = n["id"]
        # Test plural route
        r_plural = client.get(f"/api/scenario/severe_cyclone_live/assets/{nid}/explain")
        assert r_plural.status_code == 200, f"Plural explain failed for {nid}"
        # Test singular alias route
        r_singular = client.get(f"/api/scenario/severe_cyclone_live/asset/{nid}/explain")
        assert r_singular.status_code == 200, f"Singular explain failed for {nid}"
        d = r_singular.json()
        assert d["asset_id"] == nid
        assert "dominant_cause" in d
        assert "causal_chain" in d


def test_whatif_zero_and_nonzero_interventions():
    # 1. Zero actions => exactly 0.0 saved points
    r_empty = client.post(
        "/api/scenario/severe_cyclone_live/whatif",
        json={"selected_action_ids": [], "branch_time_h": -6.0},
    )
    assert r_empty.status_code == 200
    res_empty = r_empty.json()
    assert res_empty["total_lifeline_points_saved"] == 0.0
    assert all(r == 0.0 for r in res_empty["clli_comparison"]["reduction"])

    # 2. Selected actions => positive saved points
    r_actions = client.post(
        "/api/scenario/severe_cyclone_live/whatif",
        json={
            "selected_action_ids": [
                "ACT-FUEL-DHH-PURI",
                "ACT-PROTECT-TOWN-LINK",
                "ACT-GEN-TWR-GRAND-ROAD",
            ],
            "branch_time_h": -6.0,
        },
    )
    assert r_actions.status_code == 200
    res_actions = r_actions.json()
    assert res_actions["total_lifeline_points_saved"] > 0.0
    assert len(res_actions["branch_assets"]) == 29


def test_redteam_adversarial_stress():
    # Default test
    res = client.post("/api/scenario/severe_cyclone_live/redteam", json={})
    assert res.status_code == 200
    data = res.json()
    assert "plan_robustness_score" in data
    assert isinstance(data["plan_robustness_score"], (int, float))
    assert len(data["adversarial_findings"]) >= 3
    assert len(data["facility_breakdown"]) == 5

    # Custom action test
    res_custom = client.post(
        "/api/scenario/severe_cyclone_live/redteam",
        json={"action_ids": ["ACT-FUEL-DHH-PURI"]},
    )
    assert res_custom.status_code == 200
    data_custom = res_custom.json()
    assert "plan_robustness_score" in data_custom


def test_crisis_council_components():
    res = client.get("/api/scenario/severe_cyclone_live/crisis-council")
    assert res.status_code == 200
    data = res.json()
    assert "transcript" in data and len(data["transcript"]) >= 5
    assert "consensus_plan" in data and len(data["consensus_plan"]) >= 3
    assert "dissent_log" in data and len(data["dissent_log"]) >= 1


def test_keystones_and_shapley_integrity():
    res = client.get("/api/scenario/severe_cyclone_live/keystones")
    assert res.status_code == 200
    data = res.json()
    assert "top_keystones" in data and len(data["top_keystones"]) >= 3
    assert "shapley_blame" in data
    blame = data["shapley_blame"]
    assert "facility_name" in blame
    assert len(blame["attributions"]) >= 3


def test_doomsday_countdown_bounds():
    for t in [-24.0, -12.0, 0.0, 12.0]:
        res = client.get(f"/api/scenario/severe_cyclone_live/doomsday?current_time_h={t}")
        assert res.status_code == 200
        board = res.json()["actions_board"]
        assert len(board) == 6
        for act in board:
            assert "hours_remaining" in act
            assert "is_expired" in act
            assert "status" in act

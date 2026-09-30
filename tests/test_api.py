import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_list_scenarios():
    res = client.get("/api/scenarios")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 3
    scenario_ids = [s["id"] for s in data]
    assert "fani_2019" in scenario_ids
    assert "severe_cyclone_live" in scenario_ids


def test_get_graph():
    res = client.get("/api/graph")
    assert res.status_code == 200
    graph = res.json()
    assert graph["district"] == "Puri, Odisha"
    assert len(graph["nodes"]) > 10
    assert len(graph["edges"]) > 10


def test_get_parameters():
    res = client.get("/api/parameters")
    assert res.status_code == 200
    data = res.json()
    assert "categories" in data
    assert "hospitals" in data["categories"]
    assert "roads" in data["categories"]
    assert "metadata" in data


def test_scenario_run_and_assets():
    # Pre-run or fetch assets for fani_2019
    res = client.get("/api/scenario/fani_2019/assets")
    assert res.status_code == 200
    data = res.json()
    assert "assets" in data
    assert "HOSP-DHH-PURI" in data["assets"]
    dhh = data["assets"]["HOSP-DHH-PURI"]
    assert dhh["criticality"] == 1.0
    assert "dominant_cause" in dhh


def test_asset_explain():
    res = client.get("/api/scenario/fani_2019/assets/HOSP-DHH-PURI/explain")
    assert res.status_code == 200
    data = res.json()
    assert data["asset_id"] == "HOSP-DHH-PURI"
    assert len(data["upstream_power_nodes"]) > 0
    assert len(data["resupply_routes"]) > 0
    assert len(data["causal_chain"]) > 0


def test_actions_and_doomsday():
    res = client.get("/api/scenario/fani_2019/actions")
    assert res.status_code == 200
    actions = res.json()
    assert len(actions) > 0
    first_act = actions[0]
    assert "deadline_h" in first_act

    # Doomsday countdown board (F2)
    res_d = client.get("/api/scenario/fani_2019/doomsday?current_time_h=-12.0")
    assert res_d.status_code == 200
    board = res_d.json()["actions_board"]
    assert len(board) > 0
    assert "urgency" in board[0]


def test_whatif_time_machine():
    actions_res = client.get("/api/scenario/fani_2019/actions")
    action_id = actions_res.json()[0]["id"]

    res = client.post(
        "/api/scenario/fani_2019/whatif",
        json={"selected_action_ids": [action_id], "branch_time_h": -6.0},
    )
    assert res.status_code == 200
    data = res.json()
    assert "clli_comparison" in data
    assert "total_lifeline_points_saved" in data


def test_wow_features():
    # Keystone & Shapley (F6)
    k_res = client.get("/api/scenario/fani_2019/keystones")
    assert k_res.status_code == 200
    assert "top_keystones" in k_res.json()
    assert "shapley_blame" in k_res.json()

    # Crisis Council (F4)
    c_res = client.get("/api/scenario/fani_2019/crisis-council")
    assert c_res.status_code == 200
    assert len(c_res.json()["transcript"]) >= 4

    # Red Team Stress Test (F3)
    r_res = client.post("/api/scenario/fani_2019/redteam")
    assert r_res.status_code == 200
    assert "plan_robustness_score" in r_res.json()

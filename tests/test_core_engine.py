import pytest
import numpy as np

from graph.schema import NodeType, NodeState, FailureCause
from graph.build import DependencyGraphManager
from data.seed_data import get_puri_infrastructure_graph, get_cyclone_scenarios
from hazard.wind import HollandWindModel
from hazard.surge import CoastalSurgeModel
from hazard.flood import PluvialFloodModel
from hazard.ensemble import HazardEnsembleGenerator
from sim.cascade import MonteCarloCascadeSimulator
from sim.aggregate import SimulationAggregator
from actions.catalogue import generate_candidate_actions
from actions.rank import ActionRanker
from actions.wow_layer import WowLayerEngine


def test_wind_model():
    model = HollandWindModel()
    # At storm center (radius ~ 0), sustained wind should be small (eye of cyclone)
    # At RMW (~35km), wind should reach near peak
    v_peak = model.wind_speed_at_radius(radius_km=35.0, rmw_km=35.0, p_c=940.0, lat=19.8, v_max_ms=55.0)
    v_outer = model.wind_speed_at_radius(radius_km=150.0, rmw_km=35.0, p_c=940.0, lat=19.8, v_max_ms=55.0)
    assert v_peak > 30.0
    assert v_peak > v_outer

    # At center (eye), sustained wind drops
    v_eye = model.wind_speed_at_radius(radius_km=1.0, rmw_km=35.0, p_c=940.0, lat=19.8, v_max_ms=55.0)
    assert v_eye < v_peak

    # Peak gust at eyewall (~35 km from center)
    gust_eyewall = model.calculate_peak_gust(19.8, 85.8, 19.8, 85.8 + 0.33, p_c=940.0, v_max_knots=100.0, rmw_km=35.0)
    assert gust_eyewall > 35.0


def test_surge_model():
    surge = CoastalSurgeModel()
    peak = surge.calculate_peak_coastal_surge_m(p_c=935.0, v_max_knots=115.0, along_coast_dist_km=10.0, is_right_of_track=True)
    assert peak > 2.0  # Significant surge on right quadrant

    # Low elevation coastal asset inundation
    depth = surge.calculate_inundation_depth(asset_elevation_m=2.0, distance_to_coast_km=1.0, peak_coastal_surge_m=peak)
    assert depth > 0.0


def test_flood_model():
    flood = PluvialFloodModel()
    rain = flood.rainfall_intensity_mm_per_hour(dist_to_center_km=25.0, v_max_knots=100.0)
    assert rain > 20.0

    passable, reason = flood.is_road_passable(flood_depth_m=0.45, wind_gust_ms=25.0)
    assert not passable
    assert reason == "FLOODED"


def test_dependency_graph():
    gm = DependencyGraphManager()
    assert len(gm.infra_graph.nodes) > 15
    assert len(gm.infra_graph.edges) > 15

    # Check that DHH Puri has upstream power
    sources = gm.get_upstream_power_sources("HOSP-DHH-PURI")
    assert "FDR-HOSPITAL" in sources

    # Check resupply route exists from depot to DHH Puri
    routes = gm.get_resupply_routes_for_target("HOSP-DHH-PURI")
    assert len(routes) > 0
    assert routes[0]["depot_id"] == "DEPOT-TALABANIA"


def test_cascade_simulation_and_aggregation():
    gm = DependencyGraphManager()
    scenarios = get_cyclone_scenarios()
    fani = scenarios[0]

    sim = MonteCarloCascadeSimulator(gm)
    raw_res = sim.run_simulation(
        track=fani.track,
        num_runs=15,  # Fast unit test run
        time_horizon_h=24.0,
        dt_h=1.0,
        random_seed=42,
    )

    assert "first_fails" in raw_res
    assert "clli_all_runs" in raw_res
    assert raw_res["clli_all_runs"].shape[0] == 15

    asset_dist, clli_timeline, metrics = SimulationAggregator.aggregate(raw_res, gm)
    assert "HOSP-DHH-PURI" in asset_dist
    assert len(clli_timeline) > 0
    assert "total_patient_hours_at_risk" in metrics

    # DHH Puri should have a probability curve and causal chain
    dhh = asset_dist["HOSP-DHH-PURI"]
    assert len(dhh.prob_fail_curve) > 0
    assert dhh.criticality == 1.0


def test_action_ranking_and_wow_layer():
    gm = DependencyGraphManager()
    scenarios = get_cyclone_scenarios()
    fani = scenarios[0]

    sim = MonteCarloCascadeSimulator(gm)
    raw_res = sim.run_simulation(track=fani.track, num_runs=10, time_horizon_h=24.0, dt_h=1.0, random_seed=42)
    asset_dist, clli_timeline, _ = SimulationAggregator.aggregate(raw_res, gm)

    candidates = generate_candidate_actions(gm)
    ranker = ActionRanker(gm, sim)
    ranked = ranker.rank_actions(candidates[:3], raw_res, asset_dist, fani.track, num_runs=5, random_seed=42)

    assert len(ranked) == 3
    assert ranked[0].deadline_h is not None

    wow = WowLayerEngine(gm, sim)
    doomsday = wow.get_last_safe_minute_board(ranked, current_time_h=-12.0)
    assert len(doomsday) == 3
    assert "urgency" in doomsday[0]

    council = wow.simulate_crisis_council_deliberation(fani.name, asset_dist, ranked)
    assert len(council["transcript"]) >= 4
    assert len(council["consensus_plan"]) >= 2

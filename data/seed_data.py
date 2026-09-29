from typing import List, Dict, Any
from graph.schema import (
    NodeType,
    EdgeType,
    AssetNode,
    DependencyEdge,
    InfrastructureGraph,
    CycloneTrackPoint,
    CycloneScenario,
)


def get_puri_infrastructure_graph() -> InfrastructureGraph:
    """
    Returns high-fidelity infrastructure dependency graph for Puri District, Odisha.
    Covering 4 core asset types + roads, water, and fuel depots as specified in Section 8.
    """
    nodes: List[AssetNode] = [
        # --- SUBSTATIONS ---
        AssetNode(
            id="SS-PURI-GRID",
            name="Puri 132/33kV Grid Substation (Samang)",
            type=NodeType.SUBSTATION,
            lat=19.825,
            lon=85.828,
            elevation_m=6.5,
            criticality=1.0,
            attrs={
                "voltage": "132/33kV",
                "flood_critical_height_m": 0.50,
                "wind_trip_threshold_ms": 36.0,
                "wind_fail_threshold_ms": 48.0,
            },
        ),
        AssetNode(
            id="SS-TOWN-33",
            name="Puri Town 33/11kV Substation",
            type=NodeType.SUBSTATION,
            lat=19.810,
            lon=85.832,
            elevation_m=4.8,
            criticality=0.9,
            attrs={
                "voltage": "33/11kV",
                "flood_critical_height_m": 0.35,
                "wind_trip_threshold_ms": 35.0,
                "wind_fail_threshold_ms": 46.0,
            },
        ),
        AssetNode(
            id="SS-BALIGHAI",
            name="Balighai 33/11kV Substation (Marine Drive)",
            type=NodeType.SUBSTATION,
            lat=19.851,
            lon=85.918,
            elevation_m=3.2,
            criticality=0.75,
            attrs={
                "voltage": "33/11kV",
                "flood_critical_height_m": 0.30,
                "wind_trip_threshold_ms": 34.0,
                "wind_fail_threshold_ms": 44.0,
            },
        ),
        AssetNode(
            id="SS-BRAHMAGIRI",
            name="Brahmagiri 33/11kV Substation",
            type=NodeType.SUBSTATION,
            lat=19.802,
            lon=85.678,
            elevation_m=2.8,
            criticality=0.8,
            attrs={
                "voltage": "33/11kV",
                "flood_critical_height_m": 0.30,
                "wind_trip_threshold_ms": 34.0,
                "wind_fail_threshold_ms": 44.0,
            },
        ),
        AssetNode(
            id="SS-GOP",
            name="Gop 33/11kV Substation",
            type=NodeType.SUBSTATION,
            lat=19.998,
            lon=86.010,
            elevation_m=5.5,
            criticality=0.7,
            attrs={
                "voltage": "33/11kV",
                "flood_critical_height_m": 0.40,
                "wind_trip_threshold_ms": 36.0,
                "wind_fail_threshold_ms": 46.0,
            },
        ),
        AssetNode(
            id="SS-KONARK",
            name="Konark 33/11kV Substation",
            type=NodeType.SUBSTATION,
            lat=19.892,
            lon=86.095,
            elevation_m=3.5,
            criticality=0.75,
            attrs={
                "voltage": "33/11kV",
                "flood_critical_height_m": 0.32,
                "wind_trip_threshold_ms": 34.0,
                "wind_fail_threshold_ms": 45.0,
            },
        ),

        # --- DISTRIBUTION FEEDERS ---
        AssetNode(
            id="FDR-HOSPITAL",
            name="11kV Hospital Dedicated Feeder",
            type=NodeType.FEEDER,
            lat=19.815,
            lon=85.830,
            elevation_m=5.0,
            criticality=0.95,
            attrs={
                "pole_type": "spun_concrete",
                "wind_fragility_median_ms": 42.0,
                "length_km": 3.8,
            },
        ),
        AssetNode(
            id="FDR-TOWN-CORE",
            name="11kV Puri Town Urban Feeder",
            type=NodeType.FEEDER,
            lat=19.808,
            lon=85.825,
            elevation_m=4.5,
            criticality=0.8,
            attrs={
                "pole_type": "rs_joist",
                "wind_fragility_median_ms": 38.0,
                "length_km": 6.2,
            },
        ),
        AssetNode(
            id="FDR-MARINE-DRIVE",
            name="11kV Balighai-Marine Drive Feeder",
            type=NodeType.FEEDER,
            lat=19.840,
            lon=85.890,
            elevation_m=3.0,
            criticality=0.7,
            attrs={
                "pole_type": "pcc_poles",
                "wind_fragility_median_ms": 35.0,
                "length_km": 14.5,
            },
        ),
        AssetNode(
            id="FDR-BRAHMAGIRI",
            name="11kV Brahmagiri Coastal Feeder",
            type=NodeType.FEEDER,
            lat=19.800,
            lon=85.710,
            elevation_m=2.5,
            criticality=0.75,
            attrs={
                "pole_type": "pcc_poles",
                "wind_fragility_median_ms": 34.0,
                "length_km": 12.0,
            },
        ),

        # --- HOSPITALS & HEALTHCARE ---
        AssetNode(
            id="HOSP-DHH-PURI",
            name="District Headquarter Hospital (DHH Puri)",
            type=NodeType.HOSPITAL,
            lat=19.814,
            lon=85.827,
            elevation_m=5.8,
            criticality=1.0,
            attrs={
                "beds": 350,
                "icu": True,
                "dialysis": True,
                "cold_chain_vaccines": True,
                "generator_present": True,
                "fuel_hours": 14.0,
                "fuel_burn_rate_lph": 30.0,
                "tank_capacity_l": 800.0,
                "flood_critical_depth_m": 0.50,
                "wind_fail_threshold_ms": 55.0,
            },
        ),
        AssetNode(
            id="HOSP-CHC-BRAHMAGIRI",
            name="Community Health Centre (CHC) Brahmagiri",
            type=NodeType.HOSPITAL,
            lat=19.799,
            lon=85.682,
            elevation_m=3.1,
            criticality=0.85,
            attrs={
                "beds": 50,
                "icu": False,
                "dialysis": True,
                "cold_chain_vaccines": True,
                "generator_present": True,
                "fuel_hours": 8.0,
                "fuel_burn_rate_lph": 18.0,
                "tank_capacity_l": 400.0,
                "flood_critical_depth_m": 0.40,
                "wind_fail_threshold_ms": 50.0,
            },
        ),
        AssetNode(
            id="HOSP-PHC-BALIGHAI",
            name="Primary Health Centre (PHC) Balighai",
            type=NodeType.HOSPITAL,
            lat=19.848,
            lon=85.912,
            elevation_m=3.4,
            criticality=0.75,
            attrs={
                "beds": 20,
                "icu": False,
                "dialysis": False,
                "cold_chain_vaccines": True,
                "generator_present": True,
                "fuel_hours": 6.0,
                "fuel_burn_rate_lph": 12.0,
                "tank_capacity_l": 250.0,
                "flood_critical_depth_m": 0.35,
                "wind_fail_threshold_ms": 48.0,
            },
        ),
        AssetNode(
            id="HOSP-CHC-GOP",
            name="Community Health Centre (CHC) Gop",
            type=NodeType.HOSPITAL,
            lat=19.995,
            lon=86.012,
            elevation_m=6.0,
            criticality=0.8,
            attrs={
                "beds": 60,
                "icu": False,
                "dialysis": False,
                "cold_chain_vaccines": True,
                "generator_present": True,
                "fuel_hours": 10.0,
                "fuel_burn_rate_lph": 15.0,
                "tank_capacity_l": 350.0,
                "flood_critical_depth_m": 0.45,
                "wind_fail_threshold_ms": 52.0,
            },
        ),
        AssetNode(
            id="HOSP-CHC-KONARK",
            name="CHC Konark (Hospital & First Aid)",
            type=NodeType.HOSPITAL,
            lat=19.889,
            lon=86.098,
            elevation_m=3.8,
            criticality=0.8,
            attrs={
                "beds": 40,
                "icu": False,
                "dialysis": False,
                "cold_chain_vaccines": True,
                "generator_present": True,
                "fuel_hours": 7.0,
                "fuel_burn_rate_lph": 14.0,
                "tank_capacity_l": 300.0,
                "flood_critical_depth_m": 0.35,
                "wind_fail_threshold_ms": 50.0,
            },
        ),

        # --- TELECOM TOWERS ---
        AssetNode(
            id="TWR-PURI-CENTRAL",
            name="BSNL / Jio Central Hub Tower Puri",
            type=NodeType.TOWER,
            lat=19.812,
            lon=85.831,
            elevation_m=5.2,
            criticality=0.9,
            attrs={
                "operator": "BSNL/Jio",
                "battery_hours": 3.5,
                "generator_present": True,
                "fuel_hours": 18.0,
                "wind_fail_threshold_ms": 48.0,
                "serves_population": 85000,
            },
        ),
        AssetNode(
            id="TWR-GRAND-ROAD",
            name="Grand Road Telecom Tower (Airtel)",
            type=NodeType.TOWER,
            lat=19.805,
            lon=85.821,
            elevation_m=4.9,
            criticality=0.75,
            attrs={
                "operator": "Airtel",
                "battery_hours": 2.5,
                "generator_present": False,
                "fuel_hours": 0.0,
                "wind_fail_threshold_ms": 44.0,
                "serves_population": 42000,
            },
        ),
        AssetNode(
            id="TWR-BALIGHAI",
            name="Balighai Coastal Relay Tower",
            type=NodeType.TOWER,
            lat=19.849,
            lon=85.915,
            elevation_m=3.3,
            criticality=0.7,
            attrs={
                "operator": "Jio",
                "battery_hours": 3.0,
                "generator_present": False,
                "fuel_hours": 0.0,
                "wind_fail_threshold_ms": 42.0,
                "serves_population": 18000,
            },
        ),
        AssetNode(
            id="TWR-BRAHMAGIRI",
            name="Brahmagiri Emergency Comms Tower",
            type=NodeType.TOWER,
            lat=19.801,
            lon=85.680,
            elevation_m=2.9,
            criticality=0.8,
            attrs={
                "operator": "BSNL",
                "battery_hours": 4.0,
                "generator_present": True,
                "fuel_hours": 12.0,
                "wind_fail_threshold_ms": 45.0,
                "serves_population": 31000,
            },
        ),
        AssetNode(
            id="TWR-KONARK",
            name="Konark Hub Telecom Tower",
            type=NodeType.TOWER,
            lat=19.891,
            lon=86.092,
            elevation_m=3.6,
            criticality=0.75,
            attrs={
                "operator": "Airtel/Jio",
                "battery_hours": 3.0,
                "generator_present": False,
                "fuel_hours": 0.0,
                "wind_fail_threshold_ms": 43.0,
                "serves_population": 25000,
            },
        ),

        # --- WATER PUMPING STATIONS ---
        AssetNode(
            id="PUMP-MANGALAGHAT",
            name="Mangalaghat Main Water Works Pump",
            type=NodeType.WATER_PUMP,
            lat=19.809,
            lon=85.815,
            elevation_m=3.8,
            criticality=0.85,
            attrs={
                "grid_dependent": True,
                "generator_present": True,
                "fuel_hours": 8.0,
                "population_served": 110000,
                "flood_critical_depth_m": 0.40,
                "wind_fail_threshold_ms": 50.0,
            },
        ),
        AssetNode(
            id="PUMP-TALABANIA",
            name="Talabania Water Distribution Pumping Station",
            type=NodeType.WATER_PUMP,
            lat=19.824,
            lon=85.845,
            elevation_m=5.0,
            criticality=0.8,
            attrs={
                "grid_dependent": True,
                "generator_present": False,
                "fuel_hours": 0.0,
                "population_served": 65000,
                "flood_critical_depth_m": 0.45,
                "wind_fail_threshold_ms": 48.0,
            },
        ),

        # --- FUEL / EMERGENCY DEPOTS ---
        AssetNode(
            id="DEPOT-TALABANIA",
            name="Talabania Emergency Fuel & Civil Logistics Depot",
            type=NodeType.DEPOT,
            lat=19.826,
            lon=85.841,
            elevation_m=5.5,
            criticality=0.9,
            attrs={
                "diesel_stock_litres": 25000,
                "available_tankers": 3,
                "mobile_dg_sets": 2,
                "flood_critical_depth_m": 0.60,
                "wind_fail_threshold_ms": 55.0,
            },
        ),
        AssetNode(
            id="DEPOT-GOP",
            name="Gop Inland Emergency Supply Staging Area",
            type=NodeType.DEPOT,
            lat=19.996,
            lon=86.008,
            elevation_m=6.2,
            criticality=0.8,
            attrs={
                "diesel_stock_litres": 15000,
                "available_tankers": 2,
                "mobile_dg_sets": 1,
                "flood_critical_depth_m": 0.70,
                "wind_fail_threshold_ms": 60.0,
            },
        ),

        # --- ROAD SEGMENTS ---
        AssetNode(
            id="RD-NH316-NORTH",
            name="NH-316 (Bhubaneswar-Puri Expressway North Segment)",
            type=NodeType.ROAD_SEGMENT,
            lat=19.860,
            lon=85.830,
            elevation_m=6.8,
            criticality=0.95,
            attrs={
                "length_km": 15.0,
                "passability_threshold_m": 0.35,
                "debris_wind_threshold_ms": 38.0,
                "is_lifeline_corridor": True,
            },
        ),
        AssetNode(
            id="RD-PURI-TOWN-LINK",
            name="Samang-Town Access Link Road",
            type=NodeType.ROAD_SEGMENT,
            lat=19.818,
            lon=85.828,
            elevation_m=4.5,
            criticality=0.9,
            attrs={
                "length_km": 3.2,
                "passability_threshold_m": 0.30,
                "debris_wind_threshold_ms": 34.0,
            },
        ),
        AssetNode(
            id="RD-MARINE-DRIVE",
            name="SH-60 Puri-Konark Marine Drive Coastal Corridor",
            type=NodeType.ROAD_SEGMENT,
            lat=19.865,
            lon=85.980,
            elevation_m=2.6,  # Very low coastal road, prone to surge & sand blockage
            criticality=0.85,
            attrs={
                "length_km": 28.0,
                "passability_threshold_m": 0.25,
                "debris_wind_threshold_ms": 32.0,
                "surge_exposed": True,
            },
        ),
        AssetNode(
            id="RD-BRAHMAGIRI-LINK",
            name="Puri-Brahmagiri Link Highway",
            type=NodeType.ROAD_SEGMENT,
            lat=19.805,
            lon=85.740,
            elevation_m=2.9,
            criticality=0.8,
            attrs={
                "length_km": 18.0,
                "passability_threshold_m": 0.28,
                "debris_wind_threshold_ms": 33.0,
            },
        ),
        AssetNode(
            id="RD-GOP-INLAND",
            name="Puri-Gop Inland Trunk Road",
            type=NodeType.ROAD_SEGMENT,
            lat=19.920,
            lon=85.920,
            elevation_m=5.4,
            criticality=0.75,
            attrs={
                "length_km": 22.0,
                "passability_threshold_m": 0.32,
                "debris_wind_threshold_ms": 36.0,
            },
        ),
    ]

    # --- EDGES (POWERS, ACCESSED_VIA, RESUPPLIED_FROM, SERVES) ---
    edges: List[DependencyEdge] = [
        # Grid to town / substations
        DependencyEdge(src="SS-PURI-GRID", dst="SS-TOWN-33", type=EdgeType.POWERS),
        DependencyEdge(src="SS-PURI-GRID", dst="SS-BALIGHAI", type=EdgeType.POWERS),
        DependencyEdge(src="SS-PURI-GRID", dst="SS-BRAHMAGIRI", type=EdgeType.POWERS),
        DependencyEdge(src="SS-PURI-GRID", dst="SS-GOP", type=EdgeType.POWERS),
        DependencyEdge(src="SS-GOP", dst="SS-KONARK", type=EdgeType.POWERS),

        # Substations to Feeders
        DependencyEdge(src="SS-TOWN-33", dst="FDR-HOSPITAL", type=EdgeType.POWERS),
        DependencyEdge(src="SS-TOWN-33", dst="FDR-TOWN-CORE", type=EdgeType.POWERS),
        DependencyEdge(src="SS-BALIGHAI", dst="FDR-MARINE-DRIVE", type=EdgeType.POWERS),
        DependencyEdge(src="SS-BRAHMAGIRI", dst="FDR-BRAHMAGIRI", type=EdgeType.POWERS),

        # Feeders to Hospital / Critical Assets
        DependencyEdge(src="FDR-HOSPITAL", dst="HOSP-DHH-PURI", type=EdgeType.POWERS),
        DependencyEdge(src="FDR-TOWN-CORE", dst="TWR-PURI-CENTRAL", type=EdgeType.POWERS),
        DependencyEdge(src="FDR-TOWN-CORE", dst="TWR-GRAND-ROAD", type=EdgeType.POWERS),
        DependencyEdge(src="FDR-TOWN-CORE", dst="PUMP-MANGALAGHAT", type=EdgeType.POWERS),
        DependencyEdge(src="FDR-TOWN-CORE", dst="PUMP-TALABANIA", type=EdgeType.POWERS),
        DependencyEdge(src="FDR-MARINE-DRIVE", dst="HOSP-PHC-BALIGHAI", type=EdgeType.POWERS),
        DependencyEdge(src="FDR-MARINE-DRIVE", dst="TWR-BALIGHAI", type=EdgeType.POWERS),
        DependencyEdge(src="FDR-BRAHMAGIRI", dst="HOSP-CHC-BRAHMAGIRI", type=EdgeType.POWERS),
        DependencyEdge(src="FDR-BRAHMAGIRI", dst="TWR-BRAHMAGIRI", type=EdgeType.POWERS),
        DependencyEdge(src="SS-GOP", dst="HOSP-CHC-GOP", type=EdgeType.POWERS),
        DependencyEdge(src="SS-KONARK", dst="HOSP-CHC-KONARK", type=EdgeType.POWERS),
        DependencyEdge(src="SS-KONARK", dst="TWR-KONARK", type=EdgeType.POWERS),

        # Road Access Relations (ACCESSED_VIA)
        DependencyEdge(src="RD-PURI-TOWN-LINK", dst="HOSP-DHH-PURI", type=EdgeType.ACCESSED_VIA),
        DependencyEdge(src="RD-PURI-TOWN-LINK", dst="PUMP-MANGALAGHAT", type=EdgeType.ACCESSED_VIA),
        DependencyEdge(src="RD-PURI-TOWN-LINK", dst="DEPOT-TALABANIA", type=EdgeType.ACCESSED_VIA),
        DependencyEdge(src="RD-BRAHMAGIRI-LINK", dst="HOSP-CHC-BRAHMAGIRI", type=EdgeType.ACCESSED_VIA),
        DependencyEdge(src="RD-BRAHMAGIRI-LINK", dst="TWR-BRAHMAGIRI", type=EdgeType.ACCESSED_VIA),
        DependencyEdge(src="RD-MARINE-DRIVE", dst="HOSP-PHC-BALIGHAI", type=EdgeType.ACCESSED_VIA),
        DependencyEdge(src="RD-MARINE-DRIVE", dst="TWR-BALIGHAI", type=EdgeType.ACCESSED_VIA),
        DependencyEdge(src="RD-MARINE-DRIVE", dst="HOSP-CHC-KONARK", type=EdgeType.ACCESSED_VIA),
        DependencyEdge(src="RD-GOP-INLAND", dst="HOSP-CHC-GOP", type=EdgeType.ACCESSED_VIA),

        # Consumable Resupply Paths (RESUPPLIED_FROM)
        DependencyEdge(
            src="DEPOT-TALABANIA",
            dst="HOSP-DHH-PURI",
            type=EdgeType.RESUPPLIED_FROM,
            attrs={"path": ["RD-PURI-TOWN-LINK"], "distance_km": 3.5},
        ),
        DependencyEdge(
            src="DEPOT-TALABANIA",
            dst="HOSP-CHC-BRAHMAGIRI",
            type=EdgeType.RESUPPLIED_FROM,
            attrs={"path": ["RD-PURI-TOWN-LINK", "RD-BRAHMAGIRI-LINK"], "distance_km": 21.0},
        ),
        DependencyEdge(
            src="DEPOT-TALABANIA",
            dst="HOSP-PHC-BALIGHAI",
            type=EdgeType.RESUPPLIED_FROM,
            attrs={"path": ["RD-MARINE-DRIVE"], "distance_km": 11.0},
        ),
        DependencyEdge(
            src="DEPOT-GOP",
            dst="HOSP-CHC-KONARK",
            type=EdgeType.RESUPPLIED_FROM,
            attrs={"path": ["RD-GOP-INLAND", "RD-MARINE-DRIVE"], "distance_km": 14.0},
        ),
        DependencyEdge(
            src="DEPOT-TALABANIA",
            dst="PUMP-MANGALAGHAT",
            type=EdgeType.RESUPPLIED_FROM,
            attrs={"path": ["RD-PURI-TOWN-LINK"], "distance_km": 4.2},
        ),

        # Comms service relations (SERVES)
        DependencyEdge(src="TWR-PURI-CENTRAL", dst="HOSP-DHH-PURI", type=EdgeType.SERVES),
        DependencyEdge(src="TWR-BRAHMAGIRI", dst="HOSP-CHC-BRAHMAGIRI", type=EdgeType.SERVES),
        DependencyEdge(src="TWR-BALIGHAI", dst="HOSP-PHC-BALIGHAI", type=EdgeType.SERVES),
        DependencyEdge(src="TWR-KONARK", dst="HOSP-CHC-KONARK", type=EdgeType.SERVES),
    ]

    return InfrastructureGraph(
        district="Puri, Odisha",
        nodes=nodes,
        edges=edges,
    )


def get_cyclone_scenarios() -> List[CycloneScenario]:
    """
    Returns available cyclone scenarios:
    1. Historical Replay: Cyclone Fani (May 2019, landfall south of Puri)
    2. Severe Cyclone Forecast: Real-time Category 4 approaching coast
    3. Red Team Adversarial Storm: Worst-case angle and high surge directly hitting Puri Town
    """
    # Track 1: Cyclone Fani 2019 (Ground Truth Replay)
    fani_track = [
        CycloneTrackPoint(time_offset_hours=-24.0, lat=17.2, lon=84.8, central_pressure_hpa=928.0, max_sustained_wind_knots=125.0, radius_max_wind_km=32.0, forward_speed_kmh=16.0),
        CycloneTrackPoint(time_offset_hours=-18.0, lat=17.8, lon=85.0, central_pressure_hpa=932.0, max_sustained_wind_knots=120.0, radius_max_wind_km=34.0, forward_speed_kmh=17.0),
        CycloneTrackPoint(time_offset_hours=-12.0, lat=18.5, lon=85.3, central_pressure_hpa=935.0, max_sustained_wind_knots=115.0, radius_max_wind_km=35.0, forward_speed_kmh=18.0),
        CycloneTrackPoint(time_offset_hours=-6.0, lat=19.2, lon=85.6, central_pressure_hpa=937.0, max_sustained_wind_knots=115.0, radius_max_wind_km=35.0, forward_speed_kmh=19.0),
        # Landfall at T=0 near Puri (lat ~ 19.78, lon ~ 85.80)
        CycloneTrackPoint(time_offset_hours=0.0, lat=19.78, lon=85.80, central_pressure_hpa=940.0, max_sustained_wind_knots=110.0, radius_max_wind_km=35.0, forward_speed_kmh=20.0),
        CycloneTrackPoint(time_offset_hours=6.0, lat=20.35, lon=86.05, central_pressure_hpa=965.0, max_sustained_wind_knots=85.0, radius_max_wind_km=42.0, forward_speed_kmh=22.0),
        CycloneTrackPoint(time_offset_hours=12.0, lat=20.95, lon=86.35, central_pressure_hpa=982.0, max_sustained_wind_knots=65.0, radius_max_wind_km=50.0, forward_speed_kmh=24.0),
        CycloneTrackPoint(time_offset_hours=24.0, lat=22.10, lon=87.20, central_pressure_hpa=995.0, max_sustained_wind_knots=45.0, radius_max_wind_km=60.0, forward_speed_kmh=26.0),
    ]

    # Track 2: Severe Cyclone Live Forecast (Current storm approaching)
    forecast_track = [
        CycloneTrackPoint(time_offset_hours=-36.0, lat=16.8, lon=85.1, central_pressure_hpa=955.0, max_sustained_wind_knots=100.0, radius_max_wind_km=40.0, forward_speed_kmh=15.0),
        CycloneTrackPoint(time_offset_hours=-24.0, lat=17.7, lon=85.3, central_pressure_hpa=948.0, max_sustained_wind_knots=105.0, radius_max_wind_km=38.0, forward_speed_kmh=16.0),
        CycloneTrackPoint(time_offset_hours=-12.0, lat=18.7, lon=85.55, central_pressure_hpa=942.0, max_sustained_wind_knots=110.0, radius_max_wind_km=36.0, forward_speed_kmh=17.0),
        CycloneTrackPoint(time_offset_hours=0.0, lat=19.75, lon=85.78, central_pressure_hpa=945.0, max_sustained_wind_knots=105.0, radius_max_wind_km=35.0, forward_speed_kmh=18.0),
        CycloneTrackPoint(time_offset_hours=12.0, lat=20.7, lon=86.1, central_pressure_hpa=972.0, max_sustained_wind_knots=75.0, radius_max_wind_km=45.0, forward_speed_kmh=20.0),
        CycloneTrackPoint(time_offset_hours=24.0, lat=21.8, lon=86.8, central_pressure_hpa=990.0, max_sustained_wind_knots=50.0, radius_max_wind_km=55.0, forward_speed_kmh=22.0),
        CycloneTrackPoint(time_offset_hours=48.0, lat=23.5, lon=88.2, central_pressure_hpa=1002.0, max_sustained_wind_knots=30.0, radius_max_wind_km=70.0, forward_speed_kmh=25.0),
    ]

    # Track 3: Red Team Adversarial Storm (F3) - tracks directly over low-lying coastal road corridors with max surge
    redteam_track = [
        CycloneTrackPoint(time_offset_hours=-24.0, lat=17.5, lon=85.0, central_pressure_hpa=920.0, max_sustained_wind_knots=135.0, radius_max_wind_km=30.0, forward_speed_kmh=14.0),
        CycloneTrackPoint(time_offset_hours=-12.0, lat=18.6, lon=85.4, central_pressure_hpa=922.0, max_sustained_wind_knots=130.0, radius_max_wind_km=30.0, forward_speed_kmh=15.0),
        CycloneTrackPoint(time_offset_hours=0.0, lat=19.82, lon=85.82, central_pressure_hpa=925.0, max_sustained_wind_knots=125.0, radius_max_wind_km=30.0, forward_speed_kmh=16.0),
        CycloneTrackPoint(time_offset_hours=12.0, lat=20.80, lon=86.20, central_pressure_hpa=960.0, max_sustained_wind_knots=90.0, radius_max_wind_km=40.0, forward_speed_kmh=18.0),
        CycloneTrackPoint(time_offset_hours=24.0, lat=21.90, lon=86.90, central_pressure_hpa=985.0, max_sustained_wind_knots=60.0, radius_max_wind_km=50.0, forward_speed_kmh=20.0),
    ]

    return [
        CycloneScenario(
            id="fani_2019",
            name="Cyclone Fani (May 2019 Replay)",
            description="Ground-truth validation replay of Category 5 / Extremely Severe Cyclone Fani making landfall at Puri with 215 km/h gusts and complete grid blackout.",
            is_historical=True,
            landfall_time_iso="2019-05-03T08:00:00+05:30",
            track=fani_track,
        ),
        CycloneScenario(
            id="severe_cyclone_live",
            name="Severe Cyclone (48h Pre-Landfall Live)",
            description="Active operational forecast with IMD track cone, expected landfall at Puri within 24 hours. Primary planning baseline.",
            is_historical=False,
            landfall_time_iso="2026-09-30T14:00:00+05:30",
            track=forecast_track,
        ),
        CycloneScenario(
            id="red_team_storm",
            name="Red Team Adversarial Stress Test (F3)",
            description="Adversarial stress-test storm: maximum intensity, slow forward speed, and right-quadrant alignment directly flooding Marine Drive and Samang link.",
            is_historical=False,
            landfall_time_iso="2026-09-30T10:00:00+05:30",
            track=redteam_track,
        ),
    ]

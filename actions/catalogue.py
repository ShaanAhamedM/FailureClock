from typing import List, Dict, Any
from graph.schema import InterventionAction, NodeType
from graph.build import DependencyGraphManager


def generate_candidate_actions(gm: DependencyGraphManager) -> List[InterventionAction]:
    """
    Generates a domain-grounded catalogue of candidate pre-landfall interventions
    for disaster managers in Puri District.
    """
    actions: List[InterventionAction] = [
        # Action 1: Pre-position diesel at District Headquarter Hospital
        InterventionAction(
            id="ACT-FUEL-DHH-PURI",
            type="PREPOSITION_FUEL",
            target_asset_id="HOSP-DHH-PURI",
            title="Pre-position 1,500 L Diesel at DHH Puri (ICU/Dialysis)",
            description="Dispatch tanker from Talabania Depot to top up hospital underground tanks, extending generator autonomy by +18 hours for ventilator and cold-chain survival.",
            deadline_h=-4.0,  # 4 hours before landfall
            expected_benefit_clli_reduction=0.0,
            benefit_summary="Prevents complete ICU/dialysis power loss during landfall window.",
            resources_needed="1 Fuel Bowser (2,000 L), 2 Civil Defense Escorts",
            route_asset_ids=["RD-PURI-TOWN-LINK"],
            params={"added_fuel_hours": 18.0, "structural_hardening": 8.0},
        ),

        # Action 2: Mobile generator for Grand Road telecom tower
        InterventionAction(
            id="ACT-GEN-TWR-GRAND-ROAD",
            type="PREPOSITION_GENERATOR",
            target_asset_id="TWR-GRAND-ROAD",
            title="Stage 25 kVA Mobile Generator at Grand Road Telecom Hub",
            description="Deploy trailer-mounted generator with 16h fuel to unbacked telecom tower before urban grid feeder trips, keeping emergency mobile 112/alerts online.",
            deadline_h=-6.0,
            expected_benefit_clli_reduction=0.0,
            benefit_summary="Maintains mobile network coverage for 42,000 residents in Puri town center.",
            resources_needed="1 Mobile DG Set (25 kVA), 1 Utility Pickup",
            route_asset_ids=["RD-PURI-TOWN-LINK"],
            params={"fuel_hours": 16.0},
        ),

        # Action 3: Pre-position fuel at CHC Brahmagiri
        InterventionAction(
            id="ACT-FUEL-CHC-BRAHMAGIRI",
            type="PREPOSITION_FUEL",
            target_asset_id="HOSP-CHC-BRAHMAGIRI",
            title="Emergency Fuel Dispatch to CHC Brahmagiri",
            description="Brahmagiri link highway floods early from Chilika/river backwaters. Deliver 800 L diesel before road cuts off to sustain dialysis unit.",
            deadline_h=-8.0,
            expected_benefit_clli_reduction=0.0,
            benefit_summary="Protects dialysis patients from evacuation crisis during gale winds.",
            resources_needed="1 Small 4x4 Fuel Tanker (1,000 L)",
            route_asset_ids=["RD-PURI-TOWN-LINK", "RD-BRAHMAGIRI-LINK"],
            params={"added_fuel_hours": 14.0},
        ),

        # Action 4: Protect Puri-Town Link Corridor
        InterventionAction(
            id="ACT-PROTECT-TOWN-LINK",
            type="PROTECT_ROAD",
            target_asset_id="RD-PURI-TOWN-LINK",
            title="Stage PWD Tree-Clearing & Sandbag Squad on Samang-Town Link",
            description="Deploy NDRF tree-cutters and high-clearance earthmovers to prevent uprooted banyan trees and flood water from isolating DHH Puri from IOCL Depot.",
            deadline_h=-5.0,
            expected_benefit_clli_reduction=0.0,
            benefit_summary="Keeps primary hospital lifeline corridor passable for ambulances and fuel tankers.",
            resources_needed="1 JCB Excavator, 2 Chainsaw squads, 500 sandbags",
            route_asset_ids=["RD-PURI-TOWN-LINK"],
            params={},
        ),

        # Action 5: Mobile generator at Talabania Water Pumping Station
        InterventionAction(
            id="ACT-GEN-PUMP-TALABANIA",
            type="PREPOSITION_GENERATOR",
            target_asset_id="PUMP-TALABANIA",
            title="Deploy Backup Generator to Talabania Water Works",
            description="Pumping station serves 65,000 people and has 0h backup. Pre-position 60 kVA DG set to avert acute post-storm drinking water crisis.",
            deadline_h=-7.0,
            expected_benefit_clli_reduction=0.0,
            benefit_summary="Prevents drinking water shutoff for 65,000 citizens in relief camps.",
            resources_needed="1 Heavy Mobile DG set (60 kVA)",
            route_asset_ids=["RD-PURI-TOWN-LINK"],
            params={"fuel_hours": 14.0},
        ),

        # Action 6: Pre-position fuel at CHC Konark
        InterventionAction(
            id="ACT-FUEL-CHC-KONARK",
            type="PREPOSITION_FUEL",
            target_asset_id="HOSP-CHC-KONARK",
            title="Deliver 600 L Fuel to CHC Konark via Inland Route",
            description="Marine drive floods early with storm surge. Dispatch fuel tanker from Gop Depot via inland trunk road before rain intensifies.",
            deadline_h=-6.5,
            expected_benefit_clli_reduction=0.0,
            benefit_summary="Keeps emergency first-aid station and snakebite antivenom cold chain operational.",
            resources_needed="1 Tanker from Gop staging area",
            route_asset_ids=["RD-GOP-INLAND"],
            params={"added_fuel_hours": 12.0},
        ),
    ]

    return actions

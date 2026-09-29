from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    SUBSTATION = "SUBSTATION"
    FEEDER = "FEEDER"
    TOWER = "TOWER"
    HOSPITAL = "HOSPITAL"
    WATER_PUMP = "WATER_PUMP"
    ROAD_SEGMENT = "ROAD_SEGMENT"
    DEPOT = "DEPOT"


class EdgeType(str, Enum):
    POWERS = "POWERS"
    ACCESSED_VIA = "ACCESSED_VIA"
    SERVES = "SERVES"
    RESUPPLIED_FROM = "RESUPPLIED_FROM"


class NodeState(str, Enum):
    OPERATING = "OPERATING"
    ON_BACKUP = "ON_BACKUP"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"


class FailureCause(str, Enum):
    NONE = "NONE"
    DIRECT_WIND = "DIRECT_WIND"
    DIRECT_FLOOD = "DIRECT_FLOOD"
    DIRECT_SURGE = "DIRECT_SURGE"
    GRID_LOSS = "GRID_LOSS"
    BACKUP_EXHAUSTED = "BACKUP_EXHAUSTED"
    ROAD_CUT_OFF = "ROAD_CUT_OFF"
    CASCADE = "CASCADE"


class AssetNode(BaseModel):
    id: str
    name: str
    type: NodeType
    lat: float
    lon: float
    elevation_m: float = 5.0
    criticality: float = 0.5  # 0.0 to 1.0 impact weight
    attrs: Dict[str, Any] = Field(default_factory=dict)


class DependencyEdge(BaseModel):
    src: str
    dst: str
    type: EdgeType
    attrs: Dict[str, Any] = Field(default_factory=dict)


class InfrastructureGraph(BaseModel):
    district: str
    nodes: List[AssetNode]
    edges: List[DependencyEdge]


class CycloneTrackPoint(BaseModel):
    time_offset_hours: float  # e.g. -24h to +48h (0h = landfall)
    lat: float
    lon: float
    central_pressure_hpa: float = 950.0
    max_sustained_wind_knots: float = 115.0  # knots
    radius_max_wind_km: float = 35.0         # RMW
    forward_speed_kmh: float = 18.0


class CycloneScenario(BaseModel):
    id: str
    name: str
    description: str
    is_historical: bool = False
    landfall_time_iso: str = "2024-05-03T08:00:00Z"
    track: List[CycloneTrackPoint]
    parameters: Dict[str, Any] = Field(default_factory=dict)


class HazardTimeSeries(BaseModel):
    times_h: List[float]
    wind_gust_ms: List[float]
    surge_depth_m: List[float]
    flood_depth_m: List[float]


class AssetFailureDistribution(BaseModel):
    asset_id: str
    name: str
    type: NodeType
    criticality: float
    p10_fail_time_h: Optional[float] = None
    p50_fail_time_h: Optional[float] = None
    p90_fail_time_h: Optional[float] = None
    prob_fail_curve: List[Tuple[float, float]] = Field(default_factory=list)  # [(t, P(fail <= t))]
    dominant_cause: str = "NONE"
    cause_breakdown: Dict[str, float] = Field(default_factory=dict)
    causal_chain: List[str] = Field(default_factory=list)
    state_timeline_p50: List[Tuple[float, NodeState]] = Field(default_factory=list)


class InterventionAction(BaseModel):
    id: str
    type: str  # PREPOSITION_FUEL, PREPOSITION_GENERATOR, PROTECT_ROAD, etc.
    target_asset_id: str
    title: str
    description: str
    deadline_h: float
    deadline_confidence_p10_h: Optional[float] = None
    deadline_confidence_p50_h: Optional[float] = None
    deadline_confidence_p90_h: Optional[float] = None
    expected_benefit_clli_reduction: float
    benefit_summary: str
    resources_needed: str
    route_asset_ids: List[str] = Field(default_factory=list)
    params: Dict[str, Any] = Field(default_factory=dict)


class SimulationResult(BaseModel):
    scenario_id: str
    district: str
    num_mc_runs: int
    time_horizon_h: float
    dt_h: float
    time_steps: List[float]
    clli_baseline_timeline: List[Tuple[float, float, float, float]]  # [(t, p10, p50, p90)]
    asset_distributions: Dict[str, AssetFailureDistribution]
    actions: List[InterventionAction]
    keystone_assets: List[Dict[str, Any]] = Field(default_factory=list)

import math
from typing import Dict, Any, Tuple


class PluvialFloodModel:
    """
    Pluvial and surface water ponding model for cyclone rainfall.
    Computes:
    - Time-varying rainfall rate (mm/h) based on core distance and storm rain bands.
    - Surface runoff accumulation and water depth over low-lying topography.
    - Road passability status based on water depth and tree-fall debris.
    """

    def __init__(
        self,
        default_passability_depth_m: float = 0.30,
        drainage_capacity_mm_per_hour: float = 15.0,  # Natural infiltration & urban storm drainage
    ):
        self.default_passability = default_passability_depth_m
        self.drainage_capacity = drainage_capacity_mm_per_hour

    def rainfall_intensity_mm_per_hour(
        self,
        dist_to_center_km: float,
        v_max_knots: float,
        rmw_km: float = 35.0,
    ) -> float:
        """
        Estimate rain rate (mm/hr) using tropical cyclone radial rainfall profiles.
        Heavy inner eyewall core rain + outer rain bands.
        """
        # Peak core rainfall scale (typically 30-70 mm/hr for severe cyclonic storms)
        peak_rate = 20.0 + 0.35 * v_max_knots

        if dist_to_center_km <= rmw_km:
            rate = peak_rate * (0.6 + 0.4 * (dist_to_center_km / max(rmw_km, 1.0)))
        elif dist_to_center_km <= rmw_km * 3.0:
            rate = peak_rate * math.exp(-0.8 * ((dist_to_center_km - rmw_km) / rmw_km))
        else:
            outer_dist = dist_to_center_km - 3.0 * rmw_km
            rate = max(15.0 * math.exp(-outer_dist / 60.0), 0.0)

        return float(rate)

    def calculate_ponding_depth_m(
        self,
        cumulative_rain_mm: float,
        elevation_m: float,
        drainage_factor: float = 1.0,
    ) -> float:
        """
        Calculate local water depth (meters) in depression/low areas.
        Low elevation (<4 m) near rivers/coast has poor drainage.
        """
        effective_rain_mm = max(cumulative_rain_mm - (self.drainage_capacity * 4.0 * drainage_factor), 0.0)
        # Low-lying topographic convergence factor
        topo_factor = max(1.0 + (5.0 - min(elevation_m, 5.0)) * 0.4, 0.4)
        depth_m = (effective_rain_mm / 1000.0) * topo_factor * 0.35
        return float(max(depth_m, 0.0))

    def is_road_passable(
        self,
        flood_depth_m: float,
        wind_gust_ms: float,
        passability_threshold_m: float = 0.30,
        tree_fall_threshold_ms: float = 35.0,
    ) -> Tuple[bool, str]:
        """
        Determine if a road segment is passable, and if not, the primary cut cause.
        """
        if flood_depth_m >= passability_threshold_m:
            return False, "FLOODED"
        if wind_gust_ms >= tree_fall_threshold_ms:
            return False, "DEBRIS_TREE_FALL"
        return True, "PASSABLE"

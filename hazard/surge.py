import math
from typing import Tuple


class CoastalSurgeModel:
    """
    Empirical-parametric coastal storm surge inundation model.
    Accounts for:
    - Inverse barometer effect (hydrostatic sea surface elevation)
    - Wind setup on shallow coastal shelf (function of V_max^2 and coastline orientation)
    - Asymmetry (maximum surge in the right-front quadrant in the Northern Hemisphere)
    - Inland penetration attenuation based on distance from coastline and elevation.
    """

    def __init__(
        self,
        ambient_pressure_hpa: float = 1013.0,
        inland_decay_rate_m_per_km: float = 0.65,  # Surge height drop per km inland
        coastline_base_lon: float = 85.80,         # Approximate longitude of Puri district coastline
    ):
        self.p_env = ambient_pressure_hpa
        self.inland_decay_rate = inland_decay_rate_m_per_km
        self.coastline_lon = coastline_base_lon

    def calculate_peak_coastal_surge_m(
        self,
        p_c: float,
        v_max_knots: float,
        along_coast_dist_km: float,
        rmw_km: float = 35.0,
        is_right_of_track: bool = True,
    ) -> float:
        """
        Estimate peak surge height (meters above mean sea level) at the shoreline.
        """
        # 1. Inverted Barometer Effect: ~1 cm per hPa pressure deficit
        delta_p = max(self.p_env - p_c, 0.0)
        eta_ib = 0.01 * delta_p  # in meters

        # 2. Wind stress setup: proportional to V_max^2 / (g * H_shelf)
        # For coastal Bay of Bengal (shallow shelf off Odisha), 100-knot winds generate 3.0-5.5 m surge
        v_max_ms = v_max_knots * 0.514444
        eta_wind = 0.0016 * (v_max_ms ** 1.8)

        # 3. Asymmetric quadrant multiplier (right side receives onshore winds in Bay of Bengal)
        quadrant_factor = 1.25 if is_right_of_track else 0.45

        # 4. Along-coast spatial decay away from RMW
        dist_from_max = abs(along_coast_dist_km - (rmw_km if is_right_of_track else -rmw_km))
        spatial_decay = math.exp(-0.5 * (dist_from_max / max(rmw_km * 1.5, 10.0)) ** 2)

        peak_surge = (eta_ib + eta_wind) * quadrant_factor * spatial_decay
        return float(max(peak_surge, 0.0))

    def calculate_inundation_depth(
        self,
        asset_elevation_m: float,
        distance_to_coast_km: float,
        peak_coastal_surge_m: float,
    ) -> float:
        """
        Calculate local surge flood depth at an asset location given its elevation
        and inland distance.
        """
        if distance_to_coast_km < 0.0:
            distance_to_coast_km = 0.0

        surge_at_location = peak_coastal_surge_m - (self.inland_decay_rate * distance_to_coast_km)
        surge_at_location = max(surge_at_location, 0.0)

        inundation = surge_at_location - asset_elevation_m
        return float(max(inundation, 0.0))

import math
from typing import List, Tuple
import numpy as np


class HollandWindModel:
    """
    Parametric tropical cyclone wind profile (Holland 1980) combined with
    Kaplan-DeMaria empirical post-landfall inland decay.
    """

    def __init__(
        self,
        ambient_pressure_hpa: float = 1013.0,
        air_density: float = 1.15,  # kg/m^3
        gust_factor: float = 1.35,  # Ratio of 3-second gust to sustained wind
        decay_rate_per_hour: float = 0.095,  # Kaplan-DeMaria alpha
        inland_residual_wind_ms: float = 10.0,
    ):
        self.p_env = ambient_pressure_hpa
        self.rho = air_density
        self.gust_factor = gust_factor
        self.decay_rate = decay_rate_per_hour
        self.inland_residual_wind = inland_residual_wind_ms

    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great-circle distance between two points in km."""
        r = 6371.0
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2.0) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c

    def compute_holland_b(self, p_c: float, v_max_ms: float) -> float:
        """Estimate Holland B parameter from central pressure and max wind."""
        delta_p = (self.p_env - p_c) * 100.0  # Convert hPa to Pa
        if delta_p <= 500.0:
            return 1.2
        # V_max ~ sqrt(B / (rho * e) * delta_p) => B ~ (v_max^2 * rho * e) / delta_p
        b = (v_max_ms**2 * self.rho * math.e) / max(delta_p, 1000.0)
        return float(np.clip(b, 1.1, 2.3))

    def wind_speed_at_radius(
        self,
        radius_km: float,
        rmw_km: float,
        p_c: float,
        lat: float,
        v_max_ms: float,
        hours_since_landfall: float = 0.0,
    ) -> float:
        """
        Compute sustained surface wind speed (m/s) at distance radius_km from storm center.
        Applies inland decay if hours_since_landfall > 0.
        """
        r_m = max(radius_km * 1000.0, 500.0)  # Convert km to meters
        rmw_m = max(rmw_km * 1000.0, 1000.0)
        delta_p = max((self.p_env - p_c) * 100.0, 500.0)  # Pa

        b = self.compute_holland_b(p_c, v_max_ms)

        # Coriolis parameter f = 2 * omega * sin(phi)
        omega = 7.2921e-5
        f = 2.0 * omega * math.sin(math.radians(abs(lat)))

        ratio = rmw_m / r_m
        term1 = (ratio**b) * (b * delta_p / self.rho) * math.exp(-(ratio**b))
        term2 = (r_m * f / 2.0) ** 2

        v_geom = math.sqrt(max(term1 + term2, 0.0)) - (r_m * f / 2.0)
        v_sustained = max(v_geom, 0.0)

        # Post-landfall exponential decay
        if hours_since_landfall > 0.0:
            decay_factor = math.exp(-self.decay_rate * hours_since_landfall)
            v_sustained = self.inland_residual_wind + (v_sustained - self.inland_residual_wind) * decay_factor

        return float(max(v_sustained, 0.0))

    def calculate_peak_gust(
        self,
        asset_lat: float,
        asset_lon: float,
        storm_lat: float,
        storm_lon: float,
        p_c: float,
        v_max_knots: float,
        rmw_km: float,
        hours_since_landfall: float = 0.0,
    ) -> float:
        """
        Calculate 3-second peak wind gust (m/s) at asset location.
        """
        v_max_ms = v_max_knots * 0.514444
        dist_km = self.haversine_distance_km(asset_lat, asset_lon, storm_lat, storm_lon)
        v_sustained = self.wind_speed_at_radius(
            dist_km, rmw_km, p_c, asset_lat, v_max_ms, hours_since_landfall
        )
        return float(v_sustained * self.gust_factor)

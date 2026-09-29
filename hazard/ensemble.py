from __future__ import annotations
import math
from typing import List, Dict, Tuple
import numpy as np

from graph.schema import CycloneTrackPoint, CycloneScenario, AssetNode
from hazard.wind import HollandWindModel
from hazard.surge import CoastalSurgeModel
from hazard.flood import PluvialFloodModel


class HazardEnsembleGenerator:
    """
    Generates Monte Carlo hazard realisations along the cyclone track.
    Perturbs:
    - Cross-track error (perpendicular offset following IMD cone statistics)
    - Along-track error (forward speed / landfall timing jitter)
    - Intensity error (central pressure and max wind speed perturbations)
    - RMW variations
    """

    def __init__(
        self,
        wind_model: HollandWindModel | None = None,
        surge_model: CoastalSurgeModel | None = None,
        flood_model: PluvialFloodModel | None = None,
    ):
        self.wind_model = wind_model or HollandWindModel()
        self.surge_model = surge_model or CoastalSurgeModel()
        self.flood_model = flood_model or PluvialFloodModel()

    def generate_perturbed_track(
        self,
        base_track: List[CycloneTrackPoint],
        rng: np.random.Generator,
        cross_track_sigma_km: float = 18.0,
        timing_jitter_hours: float = 2.0,
        intensity_sigma_pct: float = 0.08,
    ) -> List[CycloneTrackPoint]:
        """
        Create a single perturbed track realisation.
        """
        # Perturbation parameters for this realisation
        dt_offset = float(rng.normal(0.0, timing_jitter_hours))
        dx_km = float(rng.normal(0.0, cross_track_sigma_km))
        intensity_mult = float(rng.normal(1.0, intensity_sigma_pct))
        intensity_mult = max(0.75, min(intensity_mult, 1.25))

        perturbed = []
        for pt in base_track:
            # Shift coordinates approximately (1 deg lat ~ 111 km, 1 deg lon ~ 105 km in Odisha)
            d_lat = (dx_km / 111.0) * 0.707
            d_lon = (dx_km / 105.0) * 0.707

            p_drop = max(1013.0 - pt.central_pressure_hpa, 10.0) * intensity_mult
            new_p_c = 1013.0 - p_drop
            new_v_max = pt.max_sustained_wind_knots * math.sqrt(intensity_mult)

            perturbed.append(
                CycloneTrackPoint(
                    time_offset_hours=round(pt.time_offset_hours + dt_offset, 2),
                    lat=pt.lat + d_lat,
                    lon=pt.lon + d_lon,
                    central_pressure_hpa=new_p_c,
                    max_sustained_wind_knots=new_v_max,
                    radius_max_wind_km=pt.radius_max_wind_km * (1.0 + float(rng.normal(0.0, 0.05))),
                    forward_speed_kmh=pt.forward_speed_kmh,
                )
            )
        return perturbed

    @staticmethod
    def interpolate_storm_at_time(
        track: List[CycloneTrackPoint],
        t_target: float,
    ) -> CycloneTrackPoint:
        """
        Interpolate track point at time t_target (hours relative to landfall).
        """
        if t_target <= track[0].time_offset_hours:
            return track[0]
        if t_target >= track[-1].time_offset_hours:
            return track[-1]

        for i in range(len(track) - 1):
            t1 = track[i].time_offset_hours
            t2 = track[i + 1].time_offset_hours
            if t1 <= t_target <= t2:
                alpha = (t_target - t1) / max(t2 - t1, 0.001)
                p1, p2 = track[i], track[i + 1]
                return CycloneTrackPoint(
                    time_offset_hours=t_target,
                    lat=p1.lat + alpha * (p2.lat - p1.lat),
                    lon=p1.lon + alpha * (p2.lon - p1.lon),
                    central_pressure_hpa=p1.central_pressure_hpa + alpha * (p2.central_pressure_hpa - p1.central_pressure_hpa),
                    max_sustained_wind_knots=p1.max_sustained_wind_knots + alpha * (p2.max_sustained_wind_knots - p1.max_sustained_wind_knots),
                    radius_max_wind_km=p1.radius_max_wind_km + alpha * (p2.radius_max_wind_km - p1.radius_max_wind_km),
                    forward_speed_kmh=p1.forward_speed_kmh + alpha * (p2.forward_speed_kmh - p1.forward_speed_kmh),
                )
        return track[-1]

    def compute_asset_hazard_series(
        self,
        asset: AssetNode,
        track: List[CycloneTrackPoint],
        time_steps: List[float],
        landfall_time_h: float = 0.0,
    ) -> Dict[str, List[float]]:
        """
        Compute wind gust (m/s), surge depth (m), and flood depth (m) for an asset over time.
        """
        wind_gusts: List[float] = []
        surge_depths: List[float] = []
        flood_depths: List[float] = []

        cumulative_rain_mm = 0.0
        prev_t = time_steps[0]

        # Approximate distance to coastline (Odisha coastline ~ lon 85.83 at Puri)
        # Puri coast is roughly southeast: distance from shoreline approx:
        dist_to_coast_km = max((asset.lon - 85.83) * 80.0 + (asset.lat - 19.80) * 40.0, 0.5)

        for t in time_steps:
            storm = self.interpolate_storm_at_time(track, t)
            dist_km = self.wind_model.haversine_distance_km(asset.lat, asset.lon, storm.lat, storm.lon)
            hours_post_landfall = max(t - landfall_time_h, 0.0)

            # 1. Wind Gust
            gust = self.wind_model.calculate_peak_gust(
                asset.lat,
                asset.lon,
                storm.lat,
                storm.lon,
                storm.central_pressure_hpa,
                storm.max_sustained_wind_knots,
                storm.radius_max_wind_km,
                hours_since_landfall=hours_post_landfall,
                forward_speed_kmh=storm.forward_speed_kmh,
            )
            wind_gusts.append(round(gust, 2))

            # 2. Surge Depth
            along_coast_dist = (asset.lat - storm.lat) * 111.0
            is_right = (asset.lat >= storm.lat)  # Northern side in Bay of Bengal
            peak_coast_surge = self.surge_model.calculate_peak_coastal_surge_m(
                storm.central_pressure_hpa,
                storm.max_sustained_wind_knots,
                along_coast_dist,
                storm.radius_max_wind_km,
                is_right_of_track=is_right,
            )
            # Surge peaks around landfall (-2h to +4h)
            time_factor = math.exp(-0.5 * ((t - landfall_time_h) / 3.0) ** 2) if abs(t - landfall_time_h) < 12.0 else 0.0
            curr_surge = peak_coast_surge * time_factor
            surge_inundation = self.surge_model.calculate_inundation_depth(
                asset.elevation_m, dist_to_coast_km, curr_surge
            )
            surge_depths.append(round(surge_inundation, 2))

            # 3. Pluvial Flooding
            dt = max(t - prev_t, 0.25)
            rain_rate = self.flood_model.rainfall_intensity_mm_per_hour(
                dist_km, storm.max_sustained_wind_knots, storm.radius_max_wind_km
            )
            cumulative_rain_mm += rain_rate * dt
            # Natural drainage reduces accumulated water over time
            drainage_loss = self.flood_model.drainage_capacity * dt
            cumulative_rain_mm = max(cumulative_rain_mm - drainage_loss, 0.0)

            flood_depth = self.flood_model.calculate_ponding_depth_m(
                cumulative_rain_mm, asset.elevation_m
            )
            # Combined water depth (surge + pluvial)
            total_water_depth = max(surge_inundation, flood_depth)
            flood_depths.append(round(total_water_depth, 2))

            prev_t = t

        return {
            "wind_gust_ms": wind_gusts,
            "surge_depth_m": surge_depths,
            "flood_depth_m": flood_depths,
        }

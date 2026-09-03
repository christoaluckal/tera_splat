"""Lightweight calculations for Genesis pre-settle motion diagnostics."""

from __future__ import annotations

import numpy as np


def pre_settle_diagnostic_row(
    *,
    step: int,
    dt: float,
    speeds: np.ndarray,
    positions: np.ndarray,
    source_points: np.ndarray,
    query_xy: np.ndarray,
    footprint_radius: float,
    particle_size: float,
    top_fraction: float,
    stable_steps: int,
    equilibrium_seen: bool,
) -> tuple[dict[str, float | int | bool], np.ndarray]:
    """Summarize whole-bed motion and spatially localize the fastest tail."""
    speeds = np.asarray(speeds, dtype=float).reshape(-1)
    positions = np.asarray(positions, dtype=float)
    source_points = np.asarray(source_points, dtype=float)
    if positions.shape != source_points.shape or positions.shape != (speeds.size, 3):
        raise ValueError("speed and particle-position arrays must describe the same N x 3 particles")
    if not 0.0 < top_fraction <= 1.0:
        raise ValueError("top_fraction must satisfy 0 < fraction <= 1")

    top_count = max(1, int(np.ceil(top_fraction * speeds.size)))
    top_indices = np.argpartition(speeds, speeds.size - top_count)[-top_count:]
    top_positions = positions[top_indices]
    xy_radius = np.linalg.norm(top_positions[:, :2] - query_xy[None, :], axis=1)
    lower = np.min(source_points, axis=0)
    upper = np.max(source_points, axis=0)
    margin = max(2.0 * particle_size, 1.0e-9)
    near_side_wall = (
        (top_positions[:, 0] <= lower[0] + margin)
        | (top_positions[:, 0] >= upper[0] - margin)
        | (top_positions[:, 1] <= lower[1] + margin)
        | (top_positions[:, 1] >= upper[1] - margin)
    )
    near_ground = top_positions[:, 2] <= lower[2] + margin
    near_surface = top_positions[:, 2] >= upper[2] - margin
    inside_footprint = xy_radius <= footprint_radius
    percentiles = np.percentile(speeds, (50.0, 90.0, 95.0, 99.0, 99.5))
    top_speeds = speeds[top_indices]
    row: dict[str, float | int | bool] = {
        "step": int(step),
        "time_s": float(step * dt),
        "particle_count": int(speeds.size),
        "stable_duration_s": float(stable_steps * dt),
        "equilibrium_seen": bool(equilibrium_seen),
        "speed_p50_mps": float(percentiles[0]),
        "speed_p90_mps": float(percentiles[1]),
        "speed_p95_mps": float(percentiles[2]),
        "speed_p99_mps": float(percentiles[3]),
        "speed_p99p5_mps": float(percentiles[4]),
        "speed_max_mps": float(np.max(speeds)),
        "speed_rms_mps": float(np.sqrt(np.mean(speeds * speeds))),
        "mean_squared_speed_m2ps2": float(np.mean(speeds * speeds)),
        "top_fraction": float(top_fraction),
        "top_count": int(top_count),
        "top_speed_mean_mps": float(np.mean(top_speeds)),
        "top_speed_min_mps": float(np.min(top_speeds)),
        "top_speed_max_mps": float(np.max(top_speeds)),
        "top_x_mean_m": float(np.mean(top_positions[:, 0])),
        "top_y_mean_m": float(np.mean(top_positions[:, 1])),
        "top_z_mean_m": float(np.mean(top_positions[:, 2])),
        "top_xy_radius_mean_m": float(np.mean(xy_radius)),
        "top_xy_radius_p95_m": float(np.quantile(xy_radius, 0.95)),
        "top_near_side_wall_fraction": float(np.mean(near_side_wall)),
        "top_near_ground_fraction": float(np.mean(near_ground)),
        "top_near_surface_fraction": float(np.mean(near_surface)),
        "top_inside_action_footprint_fraction": float(np.mean(inside_footprint)),
    }
    for axis_index, axis_name in enumerate(("x", "y", "z")):
        row[f"top_{axis_name}_p05_m"] = float(np.quantile(top_positions[:, axis_index], 0.05))
        row[f"top_{axis_name}_median_m"] = float(np.median(top_positions[:, axis_index]))
        row[f"top_{axis_name}_p95_m"] = float(np.quantile(top_positions[:, axis_index], 0.95))
    return row, top_indices

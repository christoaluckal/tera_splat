"""Shared I/O helpers for the initial Chrono-to-Genesis validity bridge."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

from particle_io import write_particle_ply


def load_episode(episode_dir: Path) -> tuple[dict, dict, np.ndarray, np.ndarray]:
    with (episode_dir / "manifest.yaml").open("r", encoding="utf-8") as file:
        manifest = yaml.safe_load(file)
    with (episode_dir / "action.json").open("r", encoding="utf-8") as file:
        action = json.load(file)
    initial = np.load(episode_dir / manifest["states"]["initial"])
    valid_mask = np.load(episode_dir / "valid_heightmap_mask.npy").astype(bool)
    if initial.shape != tuple(manifest["heightmap"]["shape"]):
        raise ValueError("Chrono initial heightmap does not match manifest shape")
    if valid_mask.shape != initial.shape:
        raise ValueError("Chrono valid mask does not match heightmap shape")
    if not np.isfinite(initial).all():
        raise ValueError("Chrono initial heightmap contains non-finite values")
    return manifest, action, initial.astype(np.float32), valid_mask


def heightmap_axes(manifest: dict) -> tuple[np.ndarray, np.ndarray]:
    heightmap = manifest["heightmap"]
    rows, cols = (int(value) for value in heightmap["shape"])
    spacing = float(heightmap["spacing_m"])
    origin_x, origin_y = (float(value) for value in heightmap["origin_xy_m"])
    return origin_x + np.arange(cols) * spacing, origin_y + np.arange(rows) * spacing


def build_metric_bed(
    initial_heightmap: np.ndarray,
    manifest: dict,
    *,
    bed_depth_m: float,
    particle_spacing_m: float,
) -> tuple[np.ndarray, dict]:
    if bed_depth_m <= 0.0 or particle_spacing_m <= 0.0:
        raise ValueError("bed depth and particle spacing must be positive")
    xs, ys = heightmap_axes(manifest)
    source_spacing = float(manifest["heightmap"]["spacing_m"])
    sample_x = np.arange(xs[0], xs[-1] + 0.5 * particle_spacing_m, particle_spacing_m)
    sample_y = np.arange(ys[0], ys[-1] + 0.5 * particle_spacing_m, particle_spacing_m)
    source_x = np.clip(np.rint((sample_x - xs[0]) / source_spacing).astype(int), 0, len(xs) - 1)
    source_y = np.clip(np.rint((sample_y - ys[0]) / source_spacing).astype(int), 0, len(ys) - 1)
    grid_x, grid_y = np.meshgrid(sample_x, sample_y, indexing="xy")
    surface_z = initial_heightmap[np.ix_(source_y, source_x)]
    surface_points = np.column_stack((grid_x.ravel(), grid_y.ravel(), surface_z.ravel()))
    layer_depths = np.arange(particle_spacing_m, bed_depth_m + 0.5 * particle_spacing_m, particle_spacing_m)
    layers = [surface_points - np.array([0.0, 0.0, depth], dtype=np.float32) for depth in layer_depths]
    points = np.concatenate([surface_points, *layers], axis=0).astype(np.float32)
    ground_z = float(np.min(points[:, 2]) - particle_spacing_m)
    metadata = {
        "source": "chrono_metric_heightmap",
        "coordinate_frame": manifest["coordinate_frame"],
        "surface_particle_count": int(surface_points.shape[0]),
        "particle_count": int(points.shape[0]),
        "particle_spacing_m": float(particle_spacing_m),
        "bed_depth_m": float(bed_depth_m),
        "chrono_heightmap": manifest["heightmap"],
        "ground_plane_mpm": {
            "point": [0.0, 0.0, ground_z],
            "normal": [0.0, 0.0, 1.0],
            "surface": "sticky",
            "height_source": "metric_bed_bottom_minus_particle_spacing",
        },
    }
    return points, metadata


def write_metric_bed(output_dir: Path, initial_heightmap: np.ndarray, manifest: dict, bed_depth_m: float, particle_spacing_m: float) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    points, metadata = build_metric_bed(
        initial_heightmap,
        manifest,
        bed_depth_m=bed_depth_m,
        particle_spacing_m=particle_spacing_m,
    )
    write_particle_ply(points, output_dir / "particles_initial_mpm.ply")
    with (output_dir / "ground_plane_metadata.json").open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)
    return metadata


def project_surface_to_chrono_grid(points: np.ndarray, manifest: dict, max_fill_distance_m: float) -> tuple[np.ndarray, np.ndarray]:
    """Return a nearest-particle upper envelope and a mask of supported bins."""
    xs, ys = heightmap_axes(manifest)
    spacing = float(manifest["heightmap"]["spacing_m"])
    cols, rows = len(xs), len(ys)
    col = np.rint((points[:, 0] - xs[0]) / spacing).astype(int)
    row = np.rint((points[:, 1] - ys[0]) / spacing).astype(int)
    in_bounds = (col >= 0) & (col < cols) & (row >= 0) & (row < rows)
    heightmap = np.full((rows, cols), np.nan, dtype=np.float32)
    for r, c, z in zip(row[in_bounds], col[in_bounds], points[in_bounds, 2], strict=False):
        if not np.isfinite(heightmap[r, c]) or z > heightmap[r, c]:
            heightmap[r, c] = z
    observed = np.isfinite(heightmap)
    if not np.any(observed):
        return heightmap, observed
    from scipy.spatial import cKDTree

    observed_y, observed_x = np.nonzero(observed)
    tree = cKDTree(np.column_stack((xs[observed_x], ys[observed_y])))
    grid_x, grid_y = np.meshgrid(xs, ys, indexing="xy")
    distance, nearest = tree.query(np.column_stack((grid_x.ravel(), grid_y.ravel())))
    missing = ~observed.ravel()
    supported = distance <= max_fill_distance_m
    filled = heightmap.ravel()
    observed_values = heightmap[observed]
    filled[missing & supported] = observed_values[nearest[missing & supported]]
    heightmap = filled.reshape(heightmap.shape)
    return heightmap, (observed | supported.reshape(observed.shape))

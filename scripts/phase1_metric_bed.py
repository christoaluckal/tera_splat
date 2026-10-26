#!/usr/bin/env python3
"""Build a Phase 1 metric particle bed with an exact top and common flat base."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from chrono_episode_bridge import heightmap_axes
from particle_io import write_particle_ply


BUILDER_SCHEMA_VERSION = 1


def build_common_base_metric_bed(
    initial_heightmap: np.ndarray,
    manifest: dict[str, Any],
    *,
    bed_depth_m: float,
    particle_spacing_m: float,
    minimum_top_gap_fraction: float = 0.95,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Return particles whose top follows the heightmap over one flat base.

    The legacy builder placed the same column depth below every varying surface
    point, which also made the bottom vary. Here the bed datum is the mean
    surface elevation, the base is one nominal bed depth below that datum, and
    all interior particles lie on one global vertical lattice. An exact surface
    particle is retained in every x-y column.
    """
    surface = np.asarray(initial_heightmap, dtype=np.float64)
    if surface.ndim != 2 or not np.isfinite(surface).all():
        raise ValueError("initial_heightmap must be a finite two-dimensional array")
    if bed_depth_m <= 0.0 or particle_spacing_m <= 0.0:
        raise ValueError("bed depth and particle spacing must be positive")
    if not 0.5 <= minimum_top_gap_fraction <= 1.0:
        raise ValueError("minimum_top_gap_fraction must be in [0.5, 1.0]")

    xs, ys = heightmap_axes(manifest)
    expected_shape = (len(ys), len(xs))
    if surface.shape != expected_shape:
        raise ValueError(
            f"heightmap shape {surface.shape} differs from manifest {expected_shape}"
        )
    source_spacing = float(manifest["heightmap"]["spacing_m"])
    if not np.isclose(particle_spacing_m, source_spacing):
        raise ValueError(
            "Phase 1 common-base screening requires particle and heightmap spacing to match"
        )

    grid_x, grid_y = np.meshgrid(xs, ys, indexing="xy")
    surface_points = np.column_stack(
        (grid_x.ravel(), grid_y.ravel(), surface.ravel())
    )
    datum_z = float(np.mean(surface))
    base_z = datum_z - float(bed_depth_m)
    top_gap = float(minimum_top_gap_fraction * particle_spacing_m)
    highest_surface = float(np.max(surface))
    vertical_lattice = np.arange(
        base_z,
        highest_surface + 0.5 * particle_spacing_m,
        particle_spacing_m,
        dtype=np.float64,
    )

    interior_columns: list[np.ndarray] = []
    column_counts = np.empty(surface_points.shape[0], dtype=np.int32)
    for index, (x, y, top_z) in enumerate(surface_points):
        interior_z = vertical_lattice[vertical_lattice <= top_z - top_gap]
        if interior_z.size == 0 or not np.isclose(interior_z[0], base_z):
            raise RuntimeError("common-base column does not include the flat base")
        column_counts[index] = int(interior_z.size + 1)
        interior_columns.append(
            np.column_stack(
                (
                    np.full(interior_z.size, x),
                    np.full(interior_z.size, y),
                    interior_z,
                )
            )
        )

    points = np.concatenate([surface_points, *interior_columns], axis=0).astype(
        np.float32
    )
    ground_z = float(base_z - particle_spacing_m)
    metadata: dict[str, Any] = {
        "schema_version": BUILDER_SCHEMA_VERSION,
        "source": "chrono_metric_heightmap_common_flat_base",
        "coordinate_frame": manifest["coordinate_frame"],
        "surface_particle_count": int(surface_points.shape[0]),
        "particle_count": int(points.shape[0]),
        "particle_spacing_m": float(particle_spacing_m),
        "bed_depth_m": float(bed_depth_m),
        "chrono_heightmap": manifest["heightmap"],
        "base_contract": {
            "mode": "common_flat_base",
            "surface_datum_m": datum_z,
            "base_z_m": base_z,
            "nominal_depth_m": float(bed_depth_m),
            "minimum_top_gap_fraction": float(minimum_top_gap_fraction),
            "minimum_column_particles": int(np.min(column_counts)),
            "maximum_column_particles": int(np.max(column_counts)),
            "all_columns_include_base": True,
        },
        "ground_plane_mpm": {
            "point": [0.0, 0.0, ground_z],
            "normal": [0.0, 0.0, 1.0],
            "surface": "sticky",
            "height_source": "common_flat_base_minus_particle_spacing",
        },
    }
    return points, metadata


def write_common_base_metric_bed(
    output_dir: Path,
    initial_heightmap: np.ndarray,
    manifest: dict[str, Any],
    *,
    bed_depth_m: float,
    particle_spacing_m: float,
    minimum_top_gap_fraction: float = 0.95,
) -> dict[str, Any]:
    """Write a common-base PLY and its complete construction metadata."""
    output_dir.mkdir(parents=True, exist_ok=True)
    points, metadata = build_common_base_metric_bed(
        initial_heightmap,
        manifest,
        bed_depth_m=bed_depth_m,
        particle_spacing_m=particle_spacing_m,
        minimum_top_gap_fraction=minimum_top_gap_fraction,
    )
    write_particle_ply(points, output_dir / "particles_initial_mpm.ply")
    (output_dir / "ground_plane_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    return metadata

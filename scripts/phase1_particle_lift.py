#!/usr/bin/env python3
"""Deterministically lift a Phase 1 surface prediction onto Newton particles.

The lift changes only particle ``position_m[:, 2]``.  A linear depth taper is
used because, unlike an unconstrained exponential taper, it preserves vertical
particle ordering for every downward correction smaller than the frozen cutoff
depth.  Surface particles receive the full correction, so reprojection recovers
the requested surface on every valid grid cell.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

import numpy as np


ADDED_STATE_FIELDS = ("phase1_model_id", "position_correction_m")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validated_axis(values: np.ndarray, name: str) -> tuple[np.ndarray, float]:
    axis = np.asarray(values, dtype=np.float64)
    if axis.ndim != 1 or axis.size < 2 or not np.isfinite(axis).all():
        raise ValueError(f"{name} coordinates must be a finite 1D array")
    differences = np.diff(axis)
    spacing = float(np.median(differences))
    # Phase 1 grid coordinates are stored as float32 tensors.  At the 0.3 m
    # domain edge their adjacent differences vary by several float32 ULPs.
    precision_tolerance = max(1.0e-9, abs(spacing) * 5.0e-5)
    if spacing <= 0.0 or not np.allclose(
        differences, spacing, rtol=0.0, atol=precision_tolerance
    ):
        raise ValueError(f"{name} coordinates must be uniformly increasing")
    return axis, spacing


def particle_grid_indices(
    positions: np.ndarray,
    x_coordinates_m: np.ndarray,
    y_coordinates_m: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    points = np.asarray(positions)
    if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
        raise ValueError("particle positions must be finite [N,3]")
    xs, spacing_x = _validated_axis(x_coordinates_m, "x")
    ys, spacing_y = _validated_axis(y_coordinates_m, "y")
    if not np.isclose(
        spacing_x,
        spacing_y,
        rtol=0.0,
        atol=max(1.0e-9, max(abs(spacing_x), abs(spacing_y)) * 5.0e-5),
    ):
        raise ValueError("Phase 1 particle lift requires square grid cells")
    columns = np.rint((points[:, 0].astype(np.float64) - xs[0]) / spacing_x).astype(
        np.int64
    )
    rows = np.rint((points[:, 1].astype(np.float64) - ys[0]) / spacing_y).astype(
        np.int64
    )
    in_bounds = (
        (columns >= 0)
        & (columns < xs.size)
        & (rows >= 0)
        & (rows < ys.size)
    )
    return rows, columns, in_bounds


def project_particle_surface(
    positions: np.ndarray,
    x_coordinates_m: np.ndarray,
    y_coordinates_m: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return the highest particle center in each nearest grid column."""
    xs, _ = _validated_axis(x_coordinates_m, "x")
    ys, _ = _validated_axis(y_coordinates_m, "y")
    points = np.asarray(positions)
    rows, columns, in_bounds = particle_grid_indices(points, xs, ys)
    surface = np.full((ys.size, xs.size), -np.inf, dtype=np.float64)
    np.maximum.at(
        surface,
        (rows[in_bounds], columns[in_bounds]),
        points[in_bounds, 2].astype(np.float64),
    )
    observed = np.isfinite(surface)
    surface[~observed] = np.nan
    return surface, observed


def lift_surface_to_particles(
    positions: np.ndarray,
    predicted_surface_m: np.ndarray,
    valid_support: np.ndarray,
    x_coordinates_m: np.ndarray,
    y_coordinates_m: np.ndarray,
    *,
    cutoff_depth_m: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Apply a surface correction with a monotone linear subsurface taper."""
    points = np.asarray(positions)
    predicted = np.asarray(predicted_surface_m, dtype=np.float64)
    valid = np.asarray(valid_support, dtype=bool)
    xs, _ = _validated_axis(x_coordinates_m, "x")
    ys, _ = _validated_axis(y_coordinates_m, "y")
    expected_shape = (ys.size, xs.size)
    if predicted.shape != expected_shape or valid.shape != expected_shape:
        raise ValueError("predicted surface/support shape does not match grid axes")
    if not np.isfinite(predicted[valid]).all() or not np.any(valid):
        raise ValueError("predicted surface must be finite on nonempty valid support")
    cutoff = float(cutoff_depth_m)
    if not np.isfinite(cutoff) or cutoff <= 0.0:
        raise ValueError("particle-lift cutoff depth must be positive and finite")

    source_surface, observed = project_particle_surface(points, xs, ys)
    if not np.all(observed[valid]):
        missing = int(np.count_nonzero(valid & ~observed))
        raise ValueError(f"{missing} valid surface cells have no particle support")
    surface_delta = np.zeros(expected_shape, dtype=np.float64)
    surface_delta[valid] = predicted[valid] - source_surface[valid]
    minimum_delta = float(np.min(surface_delta[valid]))
    if minimum_delta <= -cutoff:
        raise ValueError(
            "downward surface correction must be smaller than the lift cutoff "
            "to preserve particle ordering"
        )

    rows, columns, in_bounds = particle_grid_indices(points, xs, ys)
    supported_particles = np.zeros(points.shape[0], dtype=bool)
    supported_particles[in_bounds] = valid[rows[in_bounds], columns[in_bounds]]
    indices = np.flatnonzero(supported_particles)
    local_surface = source_surface[rows[indices], columns[indices]]
    depth = np.maximum(local_surface - points[indices, 2].astype(np.float64), 0.0)
    weight = np.clip(1.0 - depth / cutoff, 0.0, 1.0)
    displacement = np.zeros(points.shape[0], dtype=np.float64)
    displacement[indices] = (
        surface_delta[rows[indices], columns[indices]] * weight
    )
    stored_displacement = displacement.astype(points.dtype)
    corrected = np.array(points, copy=True)
    corrected[:, 2] = (
        points[:, 2].astype(np.float64) + stored_displacement.astype(np.float64)
    ).astype(points.dtype)
    return corrected, stored_displacement, source_surface


def write_corrected_state(
    source_path: Path,
    output_path: Path,
    corrected_positions: np.ndarray,
    displacement_z_m: np.ndarray,
    *,
    model_id: str,
) -> None:
    """Write a corrected archive while preserving every source field but z."""
    if not model_id:
        raise ValueError("model_id must be nonempty")
    with np.load(source_path, allow_pickle=False) as source:
        source_positions = np.asarray(source["position_m"])
        corrected = np.asarray(corrected_positions)
        displacement = np.asarray(displacement_z_m)
        if corrected.shape != source_positions.shape or displacement.shape != (
            source_positions.shape[0],
        ):
            raise ValueError("corrected particle arrays do not match source state")
        arrays = {name: np.array(source[name], copy=True) for name in source.files}
    arrays["position_m"] = np.array(corrected, dtype=source_positions.dtype, copy=True)
    correction = np.zeros_like(source_positions)
    correction[:, 2] = displacement.astype(source_positions.dtype)
    arrays["position_correction_m"] = correction
    arrays["phase1_model_id"] = np.asarray(model_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_path, **arrays)


def _numeric_array_is_finite(array: np.ndarray) -> bool:
    return array.dtype.kind not in "fc" or bool(np.all(np.isfinite(array)))


def audit_corrected_state(
    source_path: Path,
    corrected_path: Path,
    predicted_surface_path: Path,
    valid_support: np.ndarray,
    x_coordinates_m: np.ndarray,
    y_coordinates_m: np.ndarray,
    *,
    model_id: str,
    surface_tolerance_m: float,
) -> dict[str, Any]:
    """Audit surface reproduction and bitwise preservation of source fields."""
    valid = np.asarray(valid_support, dtype=bool)
    tolerance = float(surface_tolerance_m)
    if tolerance <= 0.0 or not np.isfinite(tolerance):
        raise ValueError("surface tolerance must be positive and finite")
    predicted = np.load(predicted_surface_path, allow_pickle=False)
    with np.load(source_path, allow_pickle=False) as source, np.load(
        corrected_path, allow_pickle=False
    ) as corrected:
        source_names = set(source.files)
        corrected_names = set(corrected.files)
        source_positions = np.asarray(source["position_m"])
        corrected_positions = np.asarray(corrected["position_m"])
        correction = np.asarray(corrected["position_correction_m"])
        preserved_names = sorted(source_names - {"position_m"})
        expected_z = (
            source_positions[:, 2].astype(np.float64)
            + correction[:, 2].astype(np.float64)
        ).astype(corrected_positions.dtype)
        z_error = np.abs(
            corrected_positions[:, 2].astype(np.float64)
            - expected_z.astype(np.float64)
        )
        rows, columns, in_bounds = particle_grid_indices(
            source_positions, x_coordinates_m, y_coordinates_m
        )
        outside_support = ~in_bounds
        outside_support[in_bounds] = ~valid[rows[in_bounds], columns[in_bounds]]
        reprojected, observed = project_particle_surface(
            corrected_positions, x_coordinates_m, y_coordinates_m
        )
        comparable = valid & observed & np.isfinite(predicted)
        reproduction_error = np.abs(
            reprojected[comparable].astype(np.float64)
            - predicted[comparable].astype(np.float64)
        )
        checks = {
            "particle_count_preserved": corrected_positions.shape
            == source_positions.shape,
            "source_fields_retained": source_names.issubset(corrected_names),
            "only_declared_fields_added": corrected_names - source_names
            == set(ADDED_STATE_FIELDS),
            "all_source_numeric_arrays_finite": all(
                _numeric_array_is_finite(source[name]) for name in source.files
            ),
            "all_corrected_numeric_arrays_finite": all(
                _numeric_array_is_finite(corrected[name]) for name in corrected.files
            ),
            "xy_preserved_bitwise": bool(
                np.array_equal(corrected_positions[:, :2], source_positions[:, :2])
            ),
            "z_matches_stored_correction": bool(np.count_nonzero(z_error) == 0),
            "correction_xy_zero_bitwise": bool(
                np.count_nonzero(correction[:, :2]) == 0
            ),
            "all_non_position_source_fields_preserved_bitwise": all(
                np.array_equal(corrected[name], source[name]) for name in preserved_names
            ),
            "particles_outside_valid_support_preserved_bitwise": bool(
                np.array_equal(
                    corrected_positions[outside_support],
                    source_positions[outside_support],
                )
            ),
            "every_valid_cell_reprojected": bool(np.all(observed[valid])),
            "predicted_surface_reproduced": bool(
                comparable.sum() == valid.sum()
                and reproduction_error.size > 0
                and float(np.max(reproduction_error)) <= tolerance
            ),
            "model_identity_matches": str(corrected["phase1_model_id"].item())
            == model_id,
        }
        source_count = int(source_positions.shape[0])
        corrected_count = int(corrected_positions.shape[0])
    return {
        "schema_version": 1,
        "source_state_sha256": sha256_file(source_path),
        "corrected_state_sha256": sha256_file(corrected_path),
        "predicted_surface_sha256": sha256_file(predicted_surface_path),
        "source_particle_count": source_count,
        "corrected_particle_count": corrected_count,
        "preserved_source_field_names": preserved_names,
        "maximum_surface_reproduction_error_m": (
            float(np.max(reproduction_error)) if reproduction_error.size else None
        ),
        "surface_reproduction_tolerance_m": tolerance,
        "maximum_z_reconstruction_error_m": float(np.max(z_error)),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }

#!/usr/bin/env python3
"""Deterministic bounded initial surfaces for the Phase 1 bed-state study."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class SurfaceLimits:
    size_x_m: float
    size_y_m: float
    spacing_m: float
    relief_limit_m: float
    maximum_local_slope_deg: float
    minimum_correlation_length_m: float
    mode_count: int
    wavelength_min_m: float
    wavelength_max_m: float


def limits_from_contract(contract: dict[str, Any]) -> SurfaceLimits:
    domain = contract["initial_surface_domain"]
    generator = domain["generator"]
    return SurfaceLimits(
        size_x_m=float(domain["bed_size_m"][0]),
        size_y_m=float(domain["bed_size_m"][1]),
        spacing_m=float(domain["grid_spacing_m"]),
        relief_limit_m=float(domain["relief_limit_m"]),
        maximum_local_slope_deg=float(domain["maximum_local_slope_deg"]),
        minimum_correlation_length_m=float(domain["minimum_correlation_length_m"]),
        mode_count=int(generator["mode_count"]),
        wavelength_min_m=float(generator["wavelength_range_m"][0]),
        wavelength_max_m=float(generator["wavelength_range_m"][1]),
    )


def coordinates(limits: SurfaceLimits) -> tuple[np.ndarray, np.ndarray]:
    columns = int(round(limits.size_x_m / limits.spacing_m)) + 1
    rows = int(round(limits.size_y_m / limits.spacing_m)) + 1
    xs = np.linspace(-0.5 * limits.size_x_m, 0.5 * limits.size_x_m, columns)
    ys = np.linspace(-0.5 * limits.size_y_m, 0.5 * limits.size_y_m, rows)
    return xs, ys


def array_sha256(array: np.ndarray) -> str:
    value = np.ascontiguousarray(array.astype("<f4", copy=False))
    descriptor = json.dumps(
        {"dtype": str(value.dtype), "shape": list(value.shape)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(descriptor + b"\0" + value.tobytes()).hexdigest()


def surface_metrics(
    heightmap_m: np.ndarray,
    limits: SurfaceLimits,
    mode_wavelengths_m: np.ndarray,
) -> dict[str, Any]:
    surface = np.asarray(heightmap_m, dtype=np.float64)
    grad_y, grad_x = np.gradient(surface, limits.spacing_m, limits.spacing_m)
    slope = np.hypot(grad_x, grad_y)
    minimum_mode_wavelength = float(np.min(mode_wavelengths_m))
    # A sinusoidal component remains positively correlated over its first
    # quarter wavelength. Restricting every mode to >= 4L gives an explicit,
    # conservative spectral correlation floor L for this finite mode family.
    correlation_floor = minimum_mode_wavelength / 4.0
    return {
        "shape": list(surface.shape),
        "finite": bool(np.isfinite(surface).all()),
        "mean_m": float(np.mean(surface)),
        "minimum_m": float(np.min(surface)),
        "maximum_m": float(np.max(surface)),
        "maximum_absolute_relief_m": float(np.max(np.abs(surface))),
        "standard_deviation_m": float(np.std(surface)),
        "maximum_local_slope_ratio": float(np.max(slope)),
        "maximum_local_slope_deg": float(np.degrees(np.arctan(np.max(slope)))),
        "minimum_mode_wavelength_m": minimum_mode_wavelength,
        "spectral_correlation_floor_m": correlation_floor,
        "boundary_maximum_absolute_m": float(
            max(
                np.max(np.abs(surface[[0, -1], :])),
                np.max(np.abs(surface[:, [0, -1]])),
            )
        ),
        "array_sha256": array_sha256(surface),
    }


def validate_surface(
    heightmap_m: np.ndarray,
    limits: SurfaceLimits,
    metrics: dict[str, Any],
) -> dict[str, bool]:
    expected_shape = (
        int(round(limits.size_y_m / limits.spacing_m)) + 1,
        int(round(limits.size_x_m / limits.spacing_m)) + 1,
    )
    checks = {
        "shape": tuple(heightmap_m.shape) == expected_shape,
        "finite": bool(metrics["finite"]),
        "zero_mean": abs(float(metrics["mean_m"])) <= 1.0e-9,
        "nonconstant": float(metrics["standard_deviation_m"]) > 1.0e-6,
        "relief": float(metrics["maximum_absolute_relief_m"])
        <= limits.relief_limit_m + 1.0e-9,
        "slope": float(metrics["maximum_local_slope_deg"])
        <= limits.maximum_local_slope_deg + 1.0e-7,
        "correlation_floor": float(metrics["spectral_correlation_floor_m"])
        >= limits.minimum_correlation_length_m - 1.0e-12,
        "flat_boundary": float(metrics["boundary_maximum_absolute_m"]) <= 1.0e-9,
    }
    return checks


def generate_surface(
    seed: int,
    limits: SurfaceLimits,
) -> tuple[np.ndarray, dict[str, Any]]:
    if limits.mode_count < 1:
        raise ValueError("mode_count must be positive")
    if limits.spacing_m <= 0.0 or limits.size_x_m <= 0.0 or limits.size_y_m <= 0.0:
        raise ValueError("surface size and spacing must be positive")
    if limits.relief_limit_m <= 0.0 or limits.maximum_local_slope_deg <= 0.0:
        raise ValueError("surface relief and slope limits must be positive")

    # The contract's correlation length is made operational as the first
    # positive-correlation quarter wavelength of every sampled cosine mode.
    effective_wavelength_min = max(
        limits.wavelength_min_m,
        4.0 * limits.minimum_correlation_length_m,
    )
    if effective_wavelength_min > limits.wavelength_max_m:
        raise ValueError(
            "wavelength range cannot satisfy the required spectral correlation floor"
        )

    rng = np.random.default_rng(int(seed))
    wavelengths = rng.uniform(
        effective_wavelength_min,
        limits.wavelength_max_m,
        size=limits.mode_count,
    )
    angles = rng.uniform(0.0, 2.0 * math.pi, size=limits.mode_count)
    phases = rng.uniform(0.0, 2.0 * math.pi, size=limits.mode_count)
    weights = rng.normal(0.0, 1.0, size=limits.mode_count)
    weights /= float(np.linalg.norm(weights))

    xs, ys = coordinates(limits)
    xx, yy = np.meshgrid(xs, ys)
    raw = np.zeros_like(xx, dtype=np.float64)
    for wavelength, angle, phase, weight in zip(
        wavelengths, angles, phases, weights, strict=True
    ):
        projected = xx * math.cos(angle) + yy * math.sin(angle)
        raw += weight * np.cos(2.0 * math.pi * projected / wavelength + phase)

    taper_x = np.sin(math.pi * (xs - xs[0]) / limits.size_x_m) ** 2
    taper_y = np.sin(math.pi * (ys - ys[0]) / limits.size_y_m) ** 2
    taper = np.outer(taper_y, taper_x)
    # Solve for the pre-taper offset that makes the tapered field zero mean;
    # this preserves an exactly flat boundary at the datum.
    raw -= float(np.sum(taper * raw) / np.sum(taper))
    surface = taper * raw

    grad_y, grad_x = np.gradient(surface, limits.spacing_m, limits.spacing_m)
    raw_relief = float(np.max(np.abs(surface)))
    raw_slope = float(np.max(np.hypot(grad_x, grad_y)))
    if raw_relief <= 0.0 or raw_slope <= 0.0:
        raise RuntimeError("surface generator produced a degenerate field")
    scale = 0.95 * min(
        limits.relief_limit_m / raw_relief,
        math.tan(math.radians(limits.maximum_local_slope_deg)) / raw_slope,
    )
    surface = np.asarray(surface * scale, dtype=np.float32)
    metrics = surface_metrics(surface, limits, wavelengths)
    checks = validate_surface(surface, limits, metrics)
    if not all(checks.values()):
        failed = sorted(name for name, passed in checks.items() if not passed)
        raise RuntimeError(f"generated surface failed qualification: {failed}")
    metadata = {
        "schema_version": 1,
        "family": "seeded_smooth_zero_mean_heightfield",
        "seed": int(seed),
        "generator": "sum_of_random_phase_low_frequency_cosine_modes",
        "correlation_definition": "minimum constituent wavelength divided by four",
        "limits": {
            "size_m": [limits.size_x_m, limits.size_y_m],
            "spacing_m": limits.spacing_m,
            "relief_limit_m": limits.relief_limit_m,
            "maximum_local_slope_deg": limits.maximum_local_slope_deg,
            "minimum_correlation_length_m": limits.minimum_correlation_length_m,
            "mode_count": limits.mode_count,
            "declared_wavelength_range_m": [
                limits.wavelength_min_m,
                limits.wavelength_max_m,
            ],
            "effective_wavelength_range_m": [
                effective_wavelength_min,
                limits.wavelength_max_m,
            ],
        },
        "modes": [
            {
                "wavelength_m": float(wavelength),
                "angle_rad": float(angle),
                "phase_rad": float(phase),
                "normalized_weight": float(weight),
            }
            for wavelength, angle, phase, weight in zip(
                wavelengths, angles, phases, weights, strict=True
            )
        ],
        "amplitude_scale_m": float(scale),
        "metrics": metrics,
        "checks": checks,
        "qualified": bool(all(checks.values())),
    }
    return surface, metadata

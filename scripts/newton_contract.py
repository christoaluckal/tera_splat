"""Pure validation and geometry helpers for the Newton MPM backend."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


SCHEMA_VERSION = 1
BACKEND_NAME = "newton"


@dataclass(frozen=True)
class NewtonMaterial:
    density_kg_m3: float
    young_modulus_pa: float
    poisson_ratio: float
    friction_coefficient: float
    damping_s: float
    yield_pressure_pa: float
    tensile_yield_ratio: float
    yield_stress_pa: float
    hardening: float
    dilatancy: float
    viscosity: float


@dataclass(frozen=True)
class NewtonSolver:
    voxel_size_m: float
    grid_type: str
    grid_padding: int
    transfer_scheme: str
    integration_scheme: str
    strain_basis: str
    collider_basis: str
    velocity_basis: str
    max_iterations: int
    tolerance: float
    air_drag: float
    critical_fraction: float


@dataclass(frozen=True)
class NewtonContact:
    ground_friction_coefficient: float
    wall_friction_coefficient: float
    wall_height_m: float
    wall_thickness_m: float


@dataclass(frozen=True)
class NewtonConfig:
    material: NewtonMaterial
    solver: NewtonSolver
    contact: NewtonContact
    raw: dict[str, Any]


def _positive(name: str, value: Any) -> float:
    result = float(value)
    if not np.isfinite(result) or result <= 0.0:
        raise ValueError(f"{name} must be finite and positive")
    return result


def _nonnegative(name: str, value: Any) -> float:
    result = float(value)
    if not np.isfinite(result) or result < 0.0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return result


def load_newton_config(path: Path) -> NewtonConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if int(raw.get("schema_version", 0)) != SCHEMA_VERSION:
        raise ValueError(f"Newton config schema must be {SCHEMA_VERSION}")
    if raw.get("backend") != BACKEND_NAME:
        raise ValueError("Newton config must declare backend='newton'")

    material_raw = raw.get("material", {})
    if "friction_coefficient" not in material_raw:
        raise ValueError(
            "Newton material requires an explicit friction_coefficient; "
            "friction_angle is not converted implicitly"
        )
    if "friction_angle" in material_raw or "friction_angle_deg" in material_raw:
        raise ValueError("Genesis friction-angle keys are not valid Newton material fields")

    material = NewtonMaterial(
        density_kg_m3=_positive("density_kg_m3", material_raw["density_kg_m3"]),
        young_modulus_pa=_positive("young_modulus_pa", material_raw["young_modulus_pa"]),
        poisson_ratio=float(material_raw["poisson_ratio"]),
        friction_coefficient=_nonnegative(
            "friction_coefficient", material_raw["friction_coefficient"]
        ),
        damping_s=_nonnegative("damping_s", material_raw.get("damping_s", 0.0)),
        yield_pressure_pa=_nonnegative(
            "yield_pressure_pa", material_raw.get("yield_pressure_pa", 0.0)
        ),
        tensile_yield_ratio=_nonnegative(
            "tensile_yield_ratio", material_raw.get("tensile_yield_ratio", 0.0)
        ),
        yield_stress_pa=_nonnegative(
            "yield_stress_pa", material_raw.get("yield_stress_pa", 0.0)
        ),
        hardening=float(material_raw.get("hardening", 0.0)),
        dilatancy=float(material_raw.get("dilatancy", 0.0)),
        viscosity=_nonnegative("viscosity", material_raw.get("viscosity", 0.0)),
    )
    if not -1.0 < material.poisson_ratio < 0.5:
        raise ValueError("poisson_ratio must be between -1 and 0.5")
    if not np.isfinite(material.hardening) or not np.isfinite(material.dilatancy):
        raise ValueError("hardening and dilatancy must be finite")

    solver_raw = raw.get("solver", {})
    solver = NewtonSolver(
        voxel_size_m=_positive("voxel_size_m", solver_raw["voxel_size_m"]),
        grid_type=str(solver_raw.get("grid_type", "sparse")),
        grid_padding=int(solver_raw.get("grid_padding", 0)),
        transfer_scheme=str(solver_raw.get("transfer_scheme", "apic")),
        integration_scheme=str(solver_raw.get("integration_scheme", "pic")),
        strain_basis=str(solver_raw.get("strain_basis", "P0")),
        collider_basis=str(solver_raw.get("collider_basis", "S2")),
        velocity_basis=str(solver_raw.get("velocity_basis", "Q1")),
        max_iterations=int(solver_raw.get("max_iterations", 250)),
        tolerance=_positive("tolerance", solver_raw.get("tolerance", 1.0e-4)),
        air_drag=_nonnegative("air_drag", solver_raw.get("air_drag", 1.0)),
        critical_fraction=_nonnegative(
            "critical_fraction", solver_raw.get("critical_fraction", 0.0)
        ),
    )
    if solver.grid_type not in {"sparse", "fixed", "dense"}:
        raise ValueError("grid_type must be sparse, fixed, or dense")
    if solver.transfer_scheme not in {"apic", "pic"}:
        raise ValueError("transfer_scheme must be apic or pic")
    if solver.integration_scheme not in {"pic", "gimp"}:
        raise ValueError("integration_scheme must be pic or gimp")
    if solver.grid_padding < 0 or solver.max_iterations <= 0:
        raise ValueError("grid_padding must be nonnegative and max_iterations positive")

    contact_raw = raw.get("contact", {})
    contact = NewtonContact(
        ground_friction_coefficient=_nonnegative(
            "ground_friction_coefficient",
            contact_raw.get("ground_friction_coefficient", 0.2),
        ),
        wall_friction_coefficient=_nonnegative(
            "wall_friction_coefficient",
            contact_raw.get("wall_friction_coefficient", 0.2),
        ),
        wall_height_m=_positive("wall_height_m", contact_raw.get("wall_height_m", 0.2)),
        wall_thickness_m=_positive(
            "wall_thickness_m", contact_raw.get("wall_thickness_m", 0.02)
        ),
    )
    return NewtonConfig(material=material, solver=solver, contact=contact, raw=raw)


def validate_metric_bed(points: np.ndarray, metadata: dict[str, Any]) -> tuple[int, float, float]:
    points = np.asarray(points)
    if points.ndim != 2 or points.shape[1] != 3 or points.shape[0] == 0:
        raise ValueError("metric-bed points must have shape [particles, 3]")
    if not np.isfinite(points).all():
        raise ValueError("metric-bed points contain non-finite values")
    if metadata.get("coordinate_frame") != "bed":
        raise ValueError("metric bed must use the Chrono bed coordinate frame")
    particle_count = int(metadata.get("particle_count", -1))
    if particle_count != points.shape[0]:
        raise ValueError(
            f"metric-bed particle count mismatch: metadata={particle_count}, points={points.shape[0]}"
        )
    surface_count = int(metadata.get("surface_particle_count", 0))
    if surface_count <= 0 or points.shape[0] % surface_count:
        raise ValueError("metric bed must contain complete equal-sized vertical layers")
    spacing = _positive("particle_spacing_m", metadata.get("particle_spacing_m"))
    ground = metadata.get("ground_plane_mpm", {})
    normal = np.asarray(ground.get("normal", []), dtype=float)
    if normal.shape != (3,) or not np.allclose(normal, (0.0, 0.0, 1.0)):
        raise ValueError("Newton stage 1 requires a horizontal +Z ground plane")
    ground_z = float(ground.get("point", [0.0, 0.0, np.nan])[2])
    if not np.isfinite(ground_z):
        raise ValueError("ground-plane height must be finite")
    if np.min(points[:, 2]) <= ground_z:
        raise ValueError("metric-bed particles must start above the ground plane")
    return surface_count, spacing, ground_z


def select_center_crop(
    points: np.ndarray,
    surface_count: int,
    radius_m: float,
) -> tuple[np.ndarray, int, np.ndarray]:
    points = np.asarray(points)
    if radius_m <= 0.0:
        return np.array(points, copy=True), surface_count, np.ones(points.shape[0], dtype=bool)
    keep = np.maximum(np.abs(points[:, 0]), np.abs(points[:, 1])) <= float(radius_m)
    cropped = np.asarray(points[keep], dtype=np.float32)
    cropped_surface_count = int(np.count_nonzero(keep[:surface_count]))
    if cropped_surface_count == 0 or cropped.shape[0] % cropped_surface_count:
        raise ValueError("center crop did not preserve complete vertical layers")
    return cropped, cropped_surface_count, keep


def particle_mass_kg(density_kg_m3: float, particle_spacing_m: float) -> float:
    return _positive("density_kg_m3", density_kg_m3) * _positive(
        "particle_spacing_m", particle_spacing_m
    ) ** 3


def containment_bounds(points: np.ndarray, particle_spacing_m: float) -> tuple[float, float, float, float]:
    margin = 0.5 * _positive("particle_spacing_m", particle_spacing_m)
    return (
        float(np.min(points[:, 0]) - margin),
        float(np.max(points[:, 0]) + margin),
        float(np.min(points[:, 1]) - margin),
        float(np.max(points[:, 1]) + margin),
    )


def speed_summary(velocities: np.ndarray) -> dict[str, float]:
    velocities = np.asarray(velocities)
    if velocities.ndim != 2 or velocities.shape[1] != 3 or not np.isfinite(velocities).all():
        raise ValueError("velocities must be finite with shape [particles, 3]")
    speed = np.linalg.norm(velocities, axis=1)
    return {
        "p50_mps": float(np.percentile(speed, 50.0)),
        "p95_mps": float(np.percentile(speed, 95.0)),
        "p99_mps": float(np.percentile(speed, 99.0)),
        "max_mps": float(np.max(speed)),
    }

#!/usr/bin/env python3
"""Extract and validate Newton particle-state fields for Phase 1.

Newton's coupled solver reconciles public position and velocity arrays into the
parent state, while solver-specific MPM history remains on the MPM entry state.
This module makes that distinction explicit and derives rotation-invariant
mechanics scalars without depending on Warp at analysis time.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import numpy as np


STATE_SCHEMA_VERSION = 2

PARTICLE_FIELDS = (
    "position_m",
    "velocity_mps",
    "velocity_gradient_per_s",
    "elastic_strain",
    "plastic_jacobian",
    "stress_pa",
    "deformation_transform",
)

MPM_STATE_ATTRIBUTES = {
    "velocity_gradient_per_s": "particle_qd_grad",
    "elastic_strain": "particle_elastic_strain",
    "plastic_jacobian": "particle_Jp",
    "stress_pa": "particle_stress",
    "deformation_transform": "particle_transform",
}

FIELD_SEMANTICS = {
    "position_m": {
        "units": "m",
        "frame": "bed/world Cartesian frame",
        "meaning": "particle center position",
    },
    "velocity_mps": {
        "units": "m/s",
        "frame": "bed/world Cartesian frame; z is the action axis",
        "meaning": "particle translational velocity",
    },
    "velocity_gradient_per_s": {
        "units": "1/s",
        "frame": "bed/world Cartesian tensor basis",
        "meaning": "Newton implicit-MPM APIC velocity gradient",
    },
    "elastic_strain": {
        "units": "dimensionless",
        "frame": "bed/world Cartesian tensor basis",
        "meaning": "Newton implicit-MPM elastic deformation gradient F_e",
    },
    "plastic_jacobian": {
        "units": "dimensionless",
        "frame": "rotation invariant",
        "meaning": "Newton implicit-MPM determinant of plastic deformation J_p",
    },
    "stress_pa": {
        "units": "Pa",
        "frame": "bed/world Cartesian tensor basis",
        "meaning": "Newton implicit-MPM symmetric Cauchy stress",
    },
    "deformation_transform": {
        "units": "dimensionless",
        "frame": "bed/world Cartesian tensor basis",
        "meaning": "optional rendering deformation transform; not advanced unless explicitly requested",
    },
}

CHECKPOINTS = ("initial", "loaded", "post_unload")
NONKINEMATIC_FAMILY_FIELDS = {
    "stress": ("stress_mean_pa", "stress_von_mises_pa"),
    "elastic": ("elastic_jacobian", "elastic_isochoric_shear"),
    "plastic": ("plastic_jacobian",),
}


def _numpy_copy(value: Any) -> np.ndarray:
    """Copy a Warp-like or NumPy array into host-owned NumPy storage."""
    if hasattr(value, "numpy"):
        value = value.numpy()
    return np.asarray(value).copy()


def extract_particle_state(
    state: Any,
    *,
    coupled_solver: Any | None = None,
    entry_name: str = "mpm",
) -> dict[str, np.ndarray]:
    """Extract public kinematics and entry-local MPM history.

    When ``coupled_solver`` is supplied, mechanics arrays are read from its
    public MPM entry state. Position and velocity remain sourced from the
    reconciled parent state so rigid/particle coupling and projection updates
    use the exact state consumed by the response pipeline.
    """
    arrays = {
        "position_m": _numpy_copy(state.particle_q),
        "velocity_mps": _numpy_copy(state.particle_qd),
    }
    mechanics_state = (
        coupled_solver.entry_state(entry_name, phase="current")
        if coupled_solver is not None
        else state
    )
    namespace = mechanics_state.mpm
    for output_name, attribute_name in MPM_STATE_ATTRIBUTES.items():
        if not hasattr(namespace, attribute_name):
            raise AttributeError(
                f"MPM state is missing required attribute {attribute_name!r}"
            )
        arrays[output_name] = _numpy_copy(getattr(namespace, attribute_name))
    validate_particle_state(arrays)
    return arrays


def validate_particle_state(arrays: Mapping[str, np.ndarray]) -> int:
    """Validate the Phase 1 particle-state schema and return particle count."""
    missing = sorted(set(PARTICLE_FIELDS) - set(arrays))
    if missing:
        raise ValueError(f"particle state is missing fields: {missing}")
    values = {name: np.asarray(arrays[name]) for name in PARTICLE_FIELDS}
    count = int(values["position_m"].shape[0])
    expected_shapes = {
        "position_m": (count, 3),
        "velocity_mps": (count, 3),
        "velocity_gradient_per_s": (count, 3, 3),
        "elastic_strain": (count, 3, 3),
        "plastic_jacobian": (count,),
        "stress_pa": (count, 3, 3),
        "deformation_transform": (count, 3, 3),
    }
    for name, expected in expected_shapes.items():
        if values[name].shape != expected:
            raise ValueError(
                f"particle state field {name} has shape {values[name].shape}; "
                f"expected {expected}"
            )
        if not np.isfinite(values[name]).all():
            raise ValueError(f"particle state field {name} contains non-finite values")
    return count


def mechanics_invariants(
    arrays: Mapping[str, np.ndarray],
) -> dict[str, np.ndarray]:
    """Derive rotation-invariant per-particle mechanics scalars.

    Stress is symmetrized before reduction. ``stress_mean_pa`` preserves the
    package sign convention rather than relabeling it as pressure. Elastic
    invariants are taken from ``F_e`` and remain dimensionless.
    """
    validate_particle_state(arrays)
    stress = np.asarray(arrays["stress_pa"], dtype=np.float64)
    symmetric_stress = 0.5 * (stress + np.swapaxes(stress, 1, 2))
    stress_trace = np.trace(symmetric_stress, axis1=1, axis2=2)
    stress_mean = stress_trace / 3.0
    identity = np.eye(3, dtype=np.float64)[None, :, :]
    deviator = symmetric_stress - stress_mean[:, None, None] * identity
    stress_von_mises = np.sqrt(
        np.maximum(0.0, 1.5 * np.sum(deviator * deviator, axis=(1, 2)))
    )

    elastic = np.asarray(arrays["elastic_strain"], dtype=np.float64)
    elastic_jacobian = np.linalg.det(elastic)
    right_cauchy_green = np.swapaxes(elastic, 1, 2) @ elastic
    c_mean = np.trace(right_cauchy_green, axis1=1, axis2=2) / 3.0
    c_deviator = right_cauchy_green - c_mean[:, None, None] * identity

    velocity = np.asarray(arrays["velocity_mps"], dtype=np.float64)
    velocity_gradient = np.asarray(
        arrays["velocity_gradient_per_s"], dtype=np.float64
    )
    return {
        "speed_mps": np.linalg.norm(velocity, axis=1),
        "velocity_gradient_frobenius_per_s": np.linalg.norm(
            velocity_gradient, axis=(1, 2)
        ),
        "velocity_divergence_per_s": np.trace(
            velocity_gradient, axis1=1, axis2=2
        ),
        "stress_mean_pa": stress_mean,
        "stress_von_mises_pa": stress_von_mises,
        "stress_frobenius_pa": np.linalg.norm(
            symmetric_stress, axis=(1, 2)
        ),
        "elastic_jacobian": elastic_jacobian,
        "elastic_isochoric_shear": np.linalg.norm(c_deviator, axis=(1, 2)),
        "plastic_jacobian": np.asarray(
            arrays["plastic_jacobian"], dtype=np.float64
        ).copy(),
    }


def _nearest_grid_indices(
    xy_m: np.ndarray,
    x_coordinates_m: np.ndarray,
    y_coordinates_m: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Map x-y points to nearest nodes on a regular metric grid."""
    xy = np.asarray(xy_m, dtype=np.float64)
    xs = np.asarray(x_coordinates_m, dtype=np.float64)
    ys = np.asarray(y_coordinates_m, dtype=np.float64)
    if xy.ndim != 2 or xy.shape[1] != 2:
        raise ValueError("xy_m must have shape (N, 2)")
    if xs.ndim != 1 or ys.ndim != 1 or xs.size < 2 or ys.size < 2:
        raise ValueError("grid coordinate arrays must be one-dimensional with size >= 2")
    dx = float(xs[1] - xs[0])
    dy = float(ys[1] - ys[0])
    if dx <= 0.0 or dy <= 0.0:
        raise ValueError("grid coordinates must increase")
    if not np.allclose(np.diff(xs), dx) or not np.allclose(np.diff(ys), dy):
        raise ValueError("grid coordinates must be regular")
    ix = np.rint((xy[:, 0] - xs[0]) / dx).astype(np.int64)
    iy = np.rint((xy[:, 1] - ys[0]) / dy).astype(np.int64)
    inside = (ix >= 0) & (ix < xs.size) & (iy >= 0) & (iy < ys.size)
    return iy, ix, inside


def particle_column_fields(
    arrays: Mapping[str, np.ndarray],
    *,
    x_coordinates_m: np.ndarray,
    y_coordinates_m: np.ndarray,
    particle_mass_kg: float,
) -> dict[str, np.ndarray]:
    """Reduce 3D particle state to deterministic 2D metric-grid columns."""
    count = validate_particle_state(arrays)
    mass = float(particle_mass_kg)
    if not np.isfinite(mass) or mass <= 0.0:
        raise ValueError("particle_mass_kg must be finite and positive")
    xs = np.asarray(x_coordinates_m, dtype=np.float64)
    ys = np.asarray(y_coordinates_m, dtype=np.float64)
    iy, ix, inside = _nearest_grid_indices(
        np.asarray(arrays["position_m"])[:, :2], xs, ys
    )
    shape = (ys.size, xs.size)
    column_count = np.zeros(shape, dtype=np.int64)
    np.add.at(column_count, (iy[inside], ix[inside]), 1)

    velocity = np.asarray(arrays["velocity_mps"], dtype=np.float64)
    velocity_sum = np.zeros((*shape, 3), dtype=np.float64)
    speed_squared_sum = np.zeros(shape, dtype=np.float64)
    for component in range(3):
        np.add.at(
            velocity_sum[..., component],
            (iy[inside], ix[inside]),
            velocity[inside, component],
        )
    np.add.at(
        speed_squared_sum,
        (iy[inside], ix[inside]),
        np.sum(velocity[inside] ** 2, axis=1),
    )
    denominator = np.maximum(column_count, 1)
    mean_velocity = velocity_sum / denominator[..., None]
    rms_speed = np.sqrt(speed_squared_sum / denominator)

    invariants = mechanics_invariants(arrays)
    invariant_means: dict[str, np.ndarray] = {}
    invariant_maxima: dict[str, np.ndarray] = {}
    for name, raw_values in invariants.items():
        values = np.asarray(raw_values, dtype=np.float64)
        sums = np.zeros(shape, dtype=np.float64)
        np.add.at(sums, (iy[inside], ix[inside]), values[inside])
        invariant_means[f"column_mean_{name}"] = sums / denominator
        maxima = np.full(shape, -np.inf, dtype=np.float64)
        np.maximum.at(maxima, (iy[inside], ix[inside]), values[inside])
        maxima[column_count == 0] = 0.0
        invariant_maxima[f"column_max_{name}"] = maxima

    if int(np.sum(column_count)) != count:
        outside_count = int(count - np.count_nonzero(inside))
        raise ValueError(
            f"{outside_count} particles fall outside the declared metric grid"
        )
    return {
        "column_particle_count": column_count,
        "column_mass_kg": column_count.astype(np.float64) * mass,
        "column_mean_velocity_xyz_mps": mean_velocity,
        "column_rms_speed_mps": rms_speed,
        **invariant_means,
        **invariant_maxima,
    }


def contact_column_fields(
    contact_position_m: np.ndarray,
    contact_impulse_ns: np.ndarray,
    *,
    x_coordinates_m: np.ndarray,
    y_coordinates_m: np.ndarray,
    active_impulse_threshold_ns: float = 1.0e-9,
) -> dict[str, np.ndarray]:
    """Reduce active 3D MPM contact nodes to 2D count and impulse fields."""
    positions = np.asarray(contact_position_m, dtype=np.float64)
    impulses = np.asarray(contact_impulse_ns, dtype=np.float64)
    if positions.ndim != 2 or positions.shape[1] != 3:
        raise ValueError("contact_position_m must have shape (N, 3)")
    if impulses.shape != positions.shape:
        raise ValueError("contact_impulse_ns must match contact_position_m")
    if not np.isfinite(positions).all() or not np.isfinite(impulses).all():
        raise ValueError("contact arrays must be finite")
    threshold = float(active_impulse_threshold_ns)
    if not np.isfinite(threshold) or threshold < 0.0:
        raise ValueError("active contact threshold must be finite and nonnegative")
    xs = np.asarray(x_coordinates_m, dtype=np.float64)
    ys = np.asarray(y_coordinates_m, dtype=np.float64)
    shape = (ys.size, xs.size)
    counts = np.zeros(shape, dtype=np.int64)
    impulse_sum = np.zeros((*shape, 3), dtype=np.float64)
    normal_impulse = np.zeros(shape, dtype=np.float64)
    if positions.shape[0] == 0:
        return {
            "contact_node_count": counts,
            "contact_impulse_xyz_ns": impulse_sum,
            "contact_normal_impulse_ns": normal_impulse,
        }
    iy, ix, inside = _nearest_grid_indices(positions[:, :2], xs, ys)
    active = np.linalg.norm(impulses, axis=1) > threshold
    selected = inside & active
    if np.any(active & ~inside):
        raise ValueError("active contact nodes fall outside the declared metric grid")
    np.add.at(counts, (iy[selected], ix[selected]), 1)
    for component in range(3):
        np.add.at(
            impulse_sum[..., component],
            (iy[selected], ix[selected]),
            impulses[selected, component],
        )
    np.add.at(normal_impulse, (iy[selected], ix[selected]), impulses[selected, 2])
    return {
        "contact_node_count": counts,
        "contact_impulse_xyz_ns": impulse_sum,
        "contact_normal_impulse_ns": normal_impulse,
    }


def select_active_collider_contacts(
    impulses_ns: np.ndarray,
    positions_m: np.ndarray,
    collider_ids: np.ndarray,
    collider_body_indices: np.ndarray,
    *,
    body_index: int,
    active_impulse_threshold_ns: float = 1.0e-9,
) -> dict[str, np.ndarray]:
    """Select active MPM grid contacts assigned to one collider body."""
    impulses = np.asarray(impulses_ns, dtype=np.float64)
    positions = np.asarray(positions_m, dtype=np.float64)
    ids = np.asarray(collider_ids, dtype=np.int64)
    body_for_collider = np.asarray(collider_body_indices, dtype=np.int64)
    if impulses.ndim != 2 or impulses.shape[1] != 3:
        raise ValueError("impulses_ns must have shape (N, 3)")
    if positions.shape != impulses.shape or ids.shape != (impulses.shape[0],):
        raise ValueError("contact positions/ids must match the impulse rows")
    if not np.isfinite(impulses).all() or not np.isfinite(positions).all():
        raise ValueError("contact inputs must be finite")
    threshold = float(active_impulse_threshold_ns)
    if not np.isfinite(threshold) or threshold < 0.0:
        raise ValueError("active contact threshold must be finite and nonnegative")
    valid_id = (ids >= 0) & (ids < body_for_collider.size)
    assigned = np.zeros(ids.shape, dtype=bool)
    assigned[valid_id] = body_for_collider[ids[valid_id]] == int(body_index)
    active = np.linalg.norm(impulses, axis=1) > threshold
    selected = assigned & active
    return {
        "contact_position_m": positions[selected].copy(),
        "contact_impulse_ns": impulses[selected].copy(),
        "contact_collider_id": ids[selected].copy(),
    }


def local_particle_mask(
    initial_position_m: np.ndarray,
    *,
    center_xy_m: tuple[float, float] | list[float] | np.ndarray,
    radius_m: float,
    radius_multiplier: float,
) -> np.ndarray:
    """Select persistent particle identities in an action-centered x-y crop."""
    positions = np.asarray(initial_position_m, dtype=np.float64)
    center = np.asarray(center_xy_m, dtype=np.float64)
    radius = float(radius_m)
    multiplier = float(radius_multiplier)
    if positions.ndim != 2 or positions.shape[1] != 3:
        raise ValueError("initial_position_m must have shape (N, 3)")
    if center.shape != (2,) or not np.isfinite(center).all():
        raise ValueError("center_xy_m must contain two finite values")
    if not np.isfinite(radius) or radius <= 0.0:
        raise ValueError("radius_m must be finite and positive")
    if not np.isfinite(multiplier) or multiplier <= 0.0:
        raise ValueError("radius_multiplier must be finite and positive")
    return np.linalg.norm(positions[:, :2] - center[None, :], axis=1) <= (
        radius * multiplier
    )


def _rms_difference(a: np.ndarray, b: np.ndarray) -> float:
    delta = np.asarray(a, dtype=np.float64) - np.asarray(b, dtype=np.float64)
    return float(np.sqrt(np.mean(delta * delta)))


def _robust_span(values: np.ndarray) -> float:
    value = np.asarray(values, dtype=np.float64)
    return float(np.percentile(value, 95.0) - np.percentile(value, 5.0))


def _pearson_or_exact(a: np.ndarray, b: np.ndarray) -> float:
    left = np.asarray(a, dtype=np.float64).reshape(-1)
    right = np.asarray(b, dtype=np.float64).reshape(-1)
    if np.array_equal(left, right):
        return 1.0
    left_centered = left - np.mean(left)
    right_centered = right - np.mean(right)
    denominator = float(
        np.linalg.norm(left_centered) * np.linalg.norm(right_centered)
    )
    if denominator == 0.0:
        return 0.0
    return float(np.dot(left_centered, right_centered) / denominator)


def triplet_field_evidence(
    states: Mapping[str, Mapping[str, np.ndarray]],
    *,
    center_xy_m: tuple[float, float] | list[float] | np.ndarray,
    radius_m: float,
    radius_multiplier: float,
    minimum_local_particles: int,
) -> dict[str, Any]:
    """Measure local variation and checkpoint changes for invariant fields."""
    if set(states) != set(CHECKPOINTS):
        raise ValueError(f"states must contain exactly {CHECKPOINTS}")
    counts = {name: validate_particle_state(states[name]) for name in CHECKPOINTS}
    if len(set(counts.values())) != 1:
        raise ValueError("checkpoint particle counts differ")
    local = local_particle_mask(
        states["initial"]["position_m"],
        center_xy_m=center_xy_m,
        radius_m=radius_m,
        radius_multiplier=radius_multiplier,
    )
    local_count = int(np.count_nonzero(local))
    if local_count < int(minimum_local_particles):
        raise ValueError(
            f"local crop contains {local_count} particles; "
            f"requires {minimum_local_particles}"
        )
    invariant_states = {
        name: mechanics_invariants(states[name]) for name in CHECKPOINTS
    }
    fields: dict[str, Any] = {}
    for field in invariant_states["initial"]:
        values = {
            name: np.asarray(invariant_states[name][field])[local]
            for name in CHECKPOINTS
        }
        pairwise = {
            "initial_to_loaded": _rms_difference(values["initial"], values["loaded"]),
            "initial_to_post_unload": _rms_difference(
                values["initial"], values["post_unload"]
            ),
            "loaded_to_post_unload": _rms_difference(
                values["loaded"], values["post_unload"]
            ),
        }
        fields[field] = {
            "loaded_local_robust_span": _robust_span(values["loaded"]),
            "pairwise_checkpoint_rms_change": pairwise,
            "minimum_pairwise_checkpoint_rms_change": min(pairwise.values()),
            "maximum_pairwise_checkpoint_rms_change": max(pairwise.values()),
            "checkpoint": {
                name: {
                    "minimum": float(np.min(value)),
                    "maximum": float(np.max(value)),
                    "mean": float(np.mean(value)),
                    "standard_deviation": float(np.std(value)),
                }
                for name, value in values.items()
            },
        }

    stress = np.asarray(states["loaded"]["stress_pa"], dtype=np.float64)[local]
    antisymmetric = 0.5 * (stress - np.swapaxes(stress, 1, 2))
    symmetric = 0.5 * (stress + np.swapaxes(stress, 1, 2))
    relative_antisymmetric = float(
        np.linalg.norm(antisymmetric)
        / max(float(np.linalg.norm(symmetric)), np.finfo(np.float64).tiny)
    )
    positive = {
        "elastic_jacobian": all(
            bool(np.all(invariant_states[name]["elastic_jacobian"][local] > 0.0))
            for name in CHECKPOINTS
        ),
        "plastic_jacobian": all(
            bool(np.all(invariant_states[name]["plastic_jacobian"][local] > 0.0))
            for name in CHECKPOINTS
        ),
    }
    return {
        "local_particle_count": local_count,
        "local_particle_mask": local,
        "fields": fields,
        "stress_relative_antisymmetric_norm": relative_antisymmetric,
        "positive_jacobians": positive,
    }


def repeat_field_evidence(
    runs: list[Mapping[str, Mapping[str, np.ndarray]]],
    *,
    local_mask: np.ndarray,
    action_signal: Mapping[str, float],
) -> dict[str, Any]:
    """Measure pairwise same-build repeat stability for invariant fields."""
    if len(runs) < 2:
        raise ValueError("repeat evidence requires at least two runs")
    mask = np.asarray(local_mask, dtype=bool)
    invariant_runs = [
        {name: mechanics_invariants(run[name]) for name in CHECKPOINTS}
        for run in runs
    ]
    result: dict[str, Any] = {}
    for field in invariant_runs[0]["initial"]:
        pairwise_rms: list[float] = []
        correlations: list[float] = []
        for left_index in range(len(runs)):
            for right_index in range(left_index + 1, len(runs)):
                for checkpoint in CHECKPOINTS:
                    left = invariant_runs[left_index][checkpoint][field][mask]
                    right = invariant_runs[right_index][checkpoint][field][mask]
                    pairwise_rms.append(_rms_difference(left, right))
                    correlations.append(_pearson_or_exact(left, right))
        maximum_rms = max(pairwise_rms)
        signal = float(action_signal[field])
        result[field] = {
            "maximum_pairwise_repeat_rms": maximum_rms,
            "minimum_pairwise_repeat_pearson": min(correlations),
            "action_signal_rms": signal,
            "repeat_rms_over_action_signal": (
                maximum_rms / signal if signal > 0.0 else None
            ),
        }
    return result


def qualify_nonkinematic_families(
    triplet: Mapping[str, Any],
    repeat: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply the frozen signal, tensor, and repeat gates by field family."""
    repeat_contract = contract["repeatability"]
    family_contracts = contract["candidate_nonkinematic_families"]
    results: dict[str, Any] = {}
    for family, fields in NONKINEMATIC_FAMILY_FIELDS.items():
        spec = family_contracts[family]
        checks: dict[str, bool] = {}
        for field in fields:
            signal = triplet["fields"][field]
            stability = repeat[field]
            checks[f"{field}_nonconstant"] = (
                float(signal["loaded_local_robust_span"])
                >= float(spec["minimum_loaded_local_robust_span"])
            )
            checks[f"{field}_checkpoint_changes"] = (
                float(signal["minimum_pairwise_checkpoint_rms_change"])
                >= float(spec["minimum_pairwise_checkpoint_rms_change"])
            )
            ratio = stability["repeat_rms_over_action_signal"]
            checks[f"{field}_repeat_ratio"] = (
                ratio is not None
                and float(ratio)
                <= float(repeat_contract["maximum_repeat_rms_over_action_signal"])
            )
            checks[f"{field}_repeat_correlation"] = (
                float(stability["minimum_pairwise_repeat_pearson"])
                >= float(repeat_contract["minimum_repeat_pearson_correlation"])
            )
        if family == "stress":
            checks["stress_symmetric"] = (
                float(triplet["stress_relative_antisymmetric_norm"])
                <= float(spec["maximum_relative_antisymmetric_norm"])
            )
        elif bool(spec.get("require_positive_jacobian")):
            checks[f"{family}_positive_jacobian"] = bool(
                triplet["positive_jacobians"][f"{family}_jacobian"]
            )
        results[family] = {
            "qualified": all(checks.values()),
            "checks": checks,
            "fields": list(fields),
        }
    return results


def write_state_archive(
    path: Path,
    arrays: Mapping[str, np.ndarray],
    *,
    extra_arrays: Mapping[str, np.ndarray] | None = None,
) -> None:
    """Write a versioned Phase 1 Newton state archive."""
    validate_particle_state(arrays)
    payload: dict[str, np.ndarray] = {
        "schema_version": np.asarray(STATE_SCHEMA_VERSION, dtype=np.int64),
        "backend": np.asarray("newton"),
        **{name: np.asarray(arrays[name]) for name in PARTICLE_FIELDS},
    }
    if extra_arrays:
        overlap = sorted(set(payload) & set(extra_arrays))
        if overlap:
            raise ValueError(f"extra state arrays replace reserved fields: {overlap}")
        for name, raw_value in extra_arrays.items():
            value = np.asarray(raw_value)
            if not np.isfinite(value).all():
                raise ValueError(f"extra state field {name} contains non-finite values")
            payload[name] = value
    np.savez_compressed(path, **payload)


def load_state_archive(path: Path) -> dict[str, np.ndarray]:
    """Load and validate a Phase 1-compatible Newton state archive."""
    with np.load(path, allow_pickle=False) as archive:
        arrays = {name: archive[name].copy() for name in archive.files}
    validate_particle_state(arrays)
    return arrays

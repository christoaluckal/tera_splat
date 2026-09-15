#!/usr/bin/env python3
"""Run an uncalibrated vertically guided Newton cylinder loading/removal diagnostic."""

from __future__ import annotations

import argparse
import csv
import json
import math
import platform
import time
from pathlib import Path
from typing import Any

import numpy as np

from newton_contract import (
    containment_bounds,
    load_newton_config,
    particle_mass_kg,
    speed_summary,
    validate_metric_bed,
)
from run_newton_prepared_bed import (
    DEFAULT_ORACLE,
    REPO_ROOT,
    add_static_containment,
    assign_material,
    load_oracle,
    project_surface,
    read_particle_ply,
    state_arrays,
    surface_match,
    write_particle_ply,
    write_state,
)


DEFAULT_PREPARED = (
    REPO_ROOT
    / "outputs"
    / "validity_experiment"
    / "newton"
    / "preparation_pic_convergence_20260906"
    / "dt0p5ms_2s"
)
DEFAULT_PREPARATION_CONVERGENCE = (
    REPO_ROOT
    / "outputs"
    / "validity_experiment"
    / "newton"
    / "preparation_pic_convergence_20260906"
    / "analysis"
    / "summary.json"
)
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "outputs"
    / "validity_experiment"
    / "newton"
    / "cylinder_diagnostic_20260906"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared-dir", type=Path, default=DEFAULT_PREPARED)
    parser.add_argument(
        "--preparation-convergence-summary",
        type=Path,
        default=DEFAULT_PREPARATION_CONVERGENCE,
    )
    parser.add_argument(
        "--candidate-preparation",
        action="store_true",
        help=(
            "Accept one freshly qualified, same-material preparation as a BayesOpt "
            "candidate preflight. The response still performs fresh in-process "
            "preparation; this does not claim a candidate-specific timestep matrix."
        ),
    )
    parser.add_argument("--chrono-episode", type=Path, default=DEFAULT_ORACLE)
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "configs" / "newton_sand_smoke.json",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--dt-s", type=float, default=0.0005)
    parser.add_argument("--pre-settle-duration-s", type=float, default=2.0)
    parser.add_argument("--pre-settle-required-duration-s", type=float, default=0.02)
    parser.add_argument("--particle-speed-threshold-mps", type=float, default=0.0005)
    parser.add_argument(
        "--loaded-duration-s",
        type=float,
        default=3.595,
        help="Fixed Newton loading observation time; default matches the Chrono accepted time.",
    )
    parser.add_argument("--residual-duration-s", type=float, default=0.25)
    parser.add_argument("--diagnostic-every", type=int, default=10)
    parser.add_argument("--cylinder-friction-coefficient", type=float, default=0.2)
    parser.add_argument(
        "--cylinder-collider-mode",
        choices=("primitive", "circumscribed_mesh"),
        default="circumscribed_mesh",
        help=(
            "Use Newton's 32-segment primitive conversion or a higher-resolution "
            "mesh whose facets circumscribe the analytic action cylinder."
        ),
    )
    parser.add_argument("--cylinder-collider-segments", type=int, default=128)
    parser.add_argument(
        "--cylinder-collision-guard-m",
        type=float,
        default=0.00001,
        help=(
            "Conservative outward guard added to the circumscribed collision "
            "envelope; does not change the analytic action/scoring cylinder."
        ),
    )
    parser.add_argument(
        "--cylinder-collision-bottom-inset-m",
        type=float,
        default=0.0,
        help=(
            "Raise only the body-local collision proxy so its lower cap is this "
            "distance above the analytic cylinder bottom. The analytic action, "
            "body inertia, pose reporting, and penetration gate remain unchanged."
        ),
    )
    parser.add_argument(
        "--cylinder-contact-activation-distance-voxels",
        type=float,
        default=None,
        help=(
            "Override only the cylinder's rasterized MPM contact-node activation "
            "distance, in grid voxels. The Newton S2 default is 0.25 voxel. "
            "Negative values require nodes to lie inside the signed-distance "
            "surface; containment and project_outside remain unchanged."
        ),
    )
    parser.add_argument(
        "--cylinder-projection-threshold-m",
        type=float,
        default=0.0,
        help=(
            "Override allowed project_outside penetration for the cylinder only; "
            "use 0 for the strict analytic-center diagnostic."
        ),
    )
    parser.add_argument(
        "--guide-coupling-mode",
        choices=("native_proxy", "explicit_impulse"),
        default="native_proxy",
        help=(
            "Use Newton's native Kamino/MPM proxy coupling with a prismatic guide, "
            "or retain the historical explicit impulse update as a diagnostic control."
        ),
    )
    parser.add_argument(
        "--guided-body-position-update",
        choices=("semi_implicit", "forward_consistent"),
        default="forward_consistent",
        help=(
            "Position integration for explicit_impulse mode only. forward_consistent "
            "uses the pre-impulse velocity, matching Newton's forward collider pose."
        ),
    )
    parser.add_argument(
        "--proxy-iterations",
        type=int,
        default=2,
        help="Native proxy relaxation passes per MPM step.",
    )
    parser.add_argument(
        "--rigid-substeps",
        type=int,
        default=4,
        help="Kamino substeps per MPM step in native_proxy mode.",
    )
    parser.add_argument(
        "--rigid-solver-tolerance",
        type=float,
        default=1.0e-6,
        help=(
            "Kamino PADMM primal, dual, and complementarity tolerance in "
            "native_proxy mode. The default matches the guide acceptance gate."
        ),
    )
    parser.add_argument("--max-fill-distance-m", type=float, default=0.0075)
    parser.add_argument(
        "--removal-height-m",
        type=float,
        default=1.0,
        help="Distance above the current bed top used to emulate instantaneous body removal.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    for name in (
        "dt_s",
        "pre_settle_duration_s",
        "pre_settle_required_duration_s",
        "particle_speed_threshold_mps",
        "loaded_duration_s",
        "residual_duration_s",
        "removal_height_m",
        "rigid_solver_tolerance",
    ):
        value = float(getattr(args, name))
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"{name} must be finite and positive")
    if args.diagnostic_every <= 0:
        raise ValueError("diagnostic-every must be positive")
    if args.proxy_iterations <= 0:
        raise ValueError("proxy-iterations must be positive")
    if args.rigid_substeps <= 0:
        raise ValueError("rigid-substeps must be positive")
    if args.cylinder_friction_coefficient < 0.0:
        raise ValueError("cylinder friction coefficient must be nonnegative")
    if args.cylinder_collider_segments < 8:
        raise ValueError("cylinder-collider-segments must be at least 8")
    if (
        not math.isfinite(args.cylinder_collision_guard_m)
        or args.cylinder_collision_guard_m < 0.0
    ):
        raise ValueError("cylinder-collision-guard-m must be finite and nonnegative")
    if (
        args.cylinder_collision_guard_m > 0.0
        and args.cylinder_collider_mode != "circumscribed_mesh"
    ):
        raise ValueError("cylinder-collision-guard-m requires circumscribed_mesh mode")
    if (
        not math.isfinite(args.cylinder_collision_bottom_inset_m)
        or args.cylinder_collision_bottom_inset_m < 0.0
    ):
        raise ValueError(
            "cylinder-collision-bottom-inset-m must be finite and nonnegative"
        )
    if (
        args.cylinder_contact_activation_distance_voxels is not None
        and not math.isfinite(args.cylinder_contact_activation_distance_voxels)
    ):
        raise ValueError(
            "cylinder-contact-activation-distance-voxels must be finite"
        )
    if (
        args.cylinder_contact_activation_distance_voxels is not None
        and args.cylinder_collision_bottom_inset_m != 0.0
    ):
        raise ValueError(
            "contact activation override requires the full-volume zero-inset cylinder"
        )
    if args.cylinder_projection_threshold_m is not None and (
        not math.isfinite(args.cylinder_projection_threshold_m)
        or args.cylinder_projection_threshold_m < 0.0
    ):
        raise ValueError(
            "cylinder-projection-threshold-m must be finite and nonnegative"
        )


def circumscribed_cylinder_radius(radius: float, segments: int) -> float:
    """Radius whose regular-polygon facets do not enter the analytic cylinder."""
    if not math.isfinite(radius) or radius <= 0.0:
        raise ValueError("radius must be finite and positive")
    if segments < 8:
        raise ValueError("segments must be at least 8")
    return radius / math.cos(math.pi / segments)


def cylinder_collision_center_offset_z(
    bottom_inset_m: float,
    analytic_half_height_m: float,
    collision_half_height_m: float,
) -> float:
    """Body-local shift that places the proxy bottom at the requested inset."""
    values = (bottom_inset_m, analytic_half_height_m, collision_half_height_m)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("collision proxy dimensions must be finite")
    if bottom_inset_m < 0.0:
        raise ValueError("bottom inset must be nonnegative")
    if analytic_half_height_m <= 0.0 or collision_half_height_m <= 0.0:
        raise ValueError("collision proxy half heights must be positive")
    return bottom_inset_m + collision_half_height_m - analytic_half_height_m


def cylinder_projection_thresholds(
    collider_body_indices: np.ndarray,
    cylinder_body: int,
    threshold_m: float,
) -> list[float | None]:
    """Build an override that leaves static containment defaults unchanged."""
    return [
        float(threshold_m) if int(body) == int(cylinder_body) else None
        for body in np.asarray(collider_body_indices).ravel()
    ]


def advance_guided_body(
    z: float,
    vz: float,
    upward_impulse_ns: float,
    mass_kg: float,
    dt_s: float,
    position_update: str,
) -> tuple[float, float]:
    """Advance the vertical guide using the requested position convention."""
    new_vz = vz - 9.81 * dt_s + upward_impulse_ns / mass_kg
    position_velocity = vz if position_update == "forward_consistent" else new_vz
    return z + position_velocity * dt_s, new_vz


def body_vertical_state(state, body_index: int) -> tuple[float, float]:
    """Read the cylinder's world-frame vertical position and linear speed."""
    return (
        float(state.body_q.numpy()[body_index, 2]),
        float(state.body_qd.numpy()[body_index, 2]),
    )


def guide_constraint_error(
    body_pose: np.ndarray,
    body_velocity: np.ndarray,
    expected_xy: tuple[float, float],
) -> dict[str, float]:
    """Summarize motion forbidden by the ideal vertical prismatic guide."""
    pose = np.asarray(body_pose, dtype=float)
    velocity = np.asarray(body_velocity, dtype=float)
    identity = np.array((0.0, 0.0, 0.0, 1.0))
    quaternion_error = min(
        float(np.linalg.norm(pose[3:7] - identity)),
        float(np.linalg.norm(pose[3:7] + identity)),
    )
    return {
        "horizontal_position_error_m": float(
            np.linalg.norm(pose[:2] - np.asarray(expected_xy))
        ),
        "orientation_quaternion_error": quaternion_error,
        "horizontal_speed_mps": float(np.linalg.norm(velocity[:2])),
        "angular_speed_radps": float(np.linalg.norm(velocity[3:6])),
    }


def convergence_qualifies_preparation(
    convergence: dict[str, Any], prepared_root: Path
) -> bool:
    """Require a passed matrix that explicitly contains the selected preparation."""
    case_paths = {
        Path(case["path"]).resolve()
        for case in convergence.get("cases", [])
        if isinstance(case, dict) and case.get("path")
    }
    return bool(
        convergence.get("backend") == "newton"
        and convergence.get("status") == "passed"
        and convergence.get("matrix_complete")
        and convergence.get("all_cases_accepted")
        and convergence.get("consistency_passed")
        and prepared_root.resolve() in case_paths
    )


def set_body_state(
    state,
    body_index: int,
    center_xy: tuple[float, float],
    z: float,
    vz: float,
) -> tuple[float, float]:
    z = float(np.float32(z))
    vz = float(np.float32(vz))
    body_q = state.body_q.numpy()
    body_q[body_index] = (
        center_xy[0],
        center_xy[1],
        z,
        0.0,
        0.0,
        0.0,
        1.0,
    )
    state.body_q.assign(body_q)
    body_qd = state.body_qd.numpy()
    body_qd[body_index] = (0.0, 0.0, vz, 0.0, 0.0, 0.0)
    state.body_qd.assign(body_qd)
    return z, vz


def cylinder_penetration(
    points: np.ndarray,
    center_xy: tuple[float, float],
    center_z: float,
    radius: float,
    half_height: float,
) -> dict[str, float | int]:
    radial = np.linalg.norm(points[:, :2] - np.asarray(center_xy), axis=1)
    radial_inside = radius - radial
    vertical_inside = half_height - np.abs(points[:, 2] - center_z)
    signed_inside = np.minimum(radial_inside, vertical_inside)
    inside = signed_inside > 0.0
    return {
        "inside_particle_centers": int(np.count_nonzero(inside)),
        "max_center_penetration_m": (
            float(np.max(signed_inside[inside])) if np.any(inside) else 0.0
        ),
    }


def finite_cylinder_signed_distance(
    points: np.ndarray,
    center_xy: tuple[float, float],
    center_z: float,
    radius: float,
    half_height: float,
) -> np.ndarray:
    """Signed distance to the finite analytic cylinder (negative is inside)."""
    values = np.asarray(points, dtype=float)
    radial = np.linalg.norm(values[:, :2] - np.asarray(center_xy), axis=1)
    q = np.column_stack(
        (radial - float(radius), np.abs(values[:, 2] - center_z) - half_height)
    )
    outside = np.linalg.norm(np.maximum(q, 0.0), axis=1)
    inside = np.minimum(np.maximum(q[:, 0], q[:, 1]), 0.0)
    return outside + inside


def summarize_cylinder_contacts(
    impulses: np.ndarray,
    positions: np.ndarray,
    collider_ids: np.ndarray,
    collider_body_indices: np.ndarray,
    body_index: int,
    center_xy: tuple[float, float],
    center_z: float,
    radius: float,
    half_height: float,
) -> dict[str, float | int | None]:
    """Summarize assigned and impulse-carrying nodes against analytic geometry."""
    impulse_values = np.asarray(impulses, dtype=float)
    position_values = np.asarray(positions, dtype=float)
    ids = np.asarray(collider_ids, dtype=int)
    body_for_collider = np.asarray(collider_body_indices, dtype=int)
    valid = (ids >= 0) & (ids < body_for_collider.size)
    selected = np.zeros(valid.shape, dtype=bool)
    selected[valid] = body_for_collider[ids[valid]] == int(body_index)
    selected_count = int(np.count_nonzero(selected))
    upward_impulse = float(np.sum(impulse_values[selected, 2]))
    if selected_count == 0:
        return {
            "upward_impulse_ns": upward_impulse,
            "assigned_nodes": 0,
            "impulse_nodes": 0,
            "assigned_sdf_min_m": None,
            "assigned_sdf_max_m": None,
            "impulse_sdf_min_m": None,
            "impulse_sdf_max_m": None,
        }

    sdf = finite_cylinder_signed_distance(
        position_values[selected], center_xy, center_z, radius, half_height
    )
    # Ignore floating-point residue from nominally inactive coupling rows.
    nonzero = np.linalg.norm(impulse_values[selected], axis=1) > 1.0e-9
    impulse_sdf = sdf[nonzero]
    return {
        "upward_impulse_ns": upward_impulse,
        "assigned_nodes": selected_count,
        "impulse_nodes": int(np.count_nonzero(nonzero)),
        "assigned_sdf_min_m": float(np.min(sdf)),
        "assigned_sdf_max_m": float(np.max(sdf)),
        "impulse_sdf_min_m": (
            float(np.min(impulse_sdf)) if impulse_sdf.size else None
        ),
        "impulse_sdf_max_m": (
            float(np.max(impulse_sdf)) if impulse_sdf.size else None
        ),
    }


def collect_cylinder_contacts(
    solver,
    state,
    body_index: int,
    center_xy: tuple[float, float],
    center_z: float,
    radius: float,
    half_height: float,
) -> dict[str, float | int | None]:
    impulses, positions, collider_ids = solver.collect_collider_impulses(state)
    return summarize_cylinder_contacts(
        impulses.numpy(),
        positions.numpy(),
        collider_ids.numpy(),
        solver.collider_body_index.numpy(),
        body_index,
        center_xy,
        center_z,
        radius,
        half_height,
    )


def response_error(
    candidate: np.ndarray,
    initial: np.ndarray,
    target: np.ndarray,
    target_initial: np.ndarray,
    valid: np.ndarray,
) -> dict[str, float | int | None]:
    common = valid & np.isfinite(candidate) & np.isfinite(initial)
    if not np.any(common):
        return {"valid_cells": 0, "rmse_m": None, "signed_mean_m": None}
    error = (candidate - initial) - (target - target_initial)
    return {
        "valid_cells": int(np.count_nonzero(common)),
        "rmse_m": float(np.sqrt(np.mean(error[common] ** 2))),
        "signed_mean_m": float(np.mean(error[common])),
    }


def write_trace(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        fieldnames = list(dict.fromkeys(key for row in rows for key in row))
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    validate_args(args)
    prepared_root = args.prepared_dir.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    prepared_manifest = json.loads(
        (prepared_root / "newton_prepared_bed_manifest.json").read_text(encoding="utf-8")
    )
    convergence_path = (
        None
        if args.candidate_preparation
        else args.preparation_convergence_summary.resolve()
    )
    if convergence_path is None:
        preparation_convergence_passed = bool(prepared_manifest.get("accepted"))
    else:
        convergence = json.loads(convergence_path.read_text(encoding="utf-8"))
        preparation_convergence_passed = convergence_qualifies_preparation(
            convergence, prepared_root
        )
    if prepared_manifest.get("backend") != "newton" or not prepared_manifest.get("accepted"):
        raise ValueError("cylinder diagnostics require an accepted Newton preparation")
    if not math.isclose(
        float(prepared_manifest["solver"]["dt_s"]),
        args.dt_s,
        rel_tol=1.0e-9,
        abs_tol=1.0e-12,
    ):
        raise ValueError("diagnostic timestep must match the prepared Newton state")

    source_ply = Path(prepared_manifest["source"]["particles_ply"]).resolve()
    source_metadata_path = Path(prepared_manifest["source"]["metadata_json"]).resolve()
    source_metadata = json.loads(source_metadata_path.read_text(encoding="utf-8"))
    prepared_points = read_particle_ply(source_ply)
    _surface_count, spacing, source_ground_z = validate_metric_bed(
        prepared_points, source_metadata
    )
    config = load_newton_config(args.config.resolve())
    if config.raw["material"] != prepared_manifest["material"]:
        raise ValueError("cylinder material differs from the accepted preparation contract")
    for key, value in config.raw["solver"].items():
        if prepared_manifest["solver"].get(key) != value:
            raise ValueError(
                f"cylinder solver field {key} differs from the accepted preparation contract"
            )
    for key, value in config.raw["contact"].items():
        if prepared_manifest["contact"].get(key) != value:
            raise ValueError(
                f"cylinder contact field {key} differs from the accepted preparation contract"
            )
    oracle_manifest, chrono_initial, chrono_valid = load_oracle(args.chrono_episode.resolve())
    action = json.loads(
        (args.chrono_episode.resolve() / oracle_manifest["action"]).read_text(encoding="utf-8")
    )
    chrono_loaded = np.load(
        args.chrono_episode.resolve() / oracle_manifest["states"]["loaded"]
    )
    chrono_residual = np.load(
        args.chrono_episode.resolve() / oracle_manifest["states"]["residual"]
    )
    center_xy = tuple(float(value) for value in action["center_xy_m"])
    radius = float(action["radius_m"])
    height = float(action["height_m"])
    half_height = 0.5 * height
    if args.cylinder_collision_bottom_inset_m >= height:
        raise ValueError("cylinder collision bottom inset must be less than cylinder height")
    mass = float(action["mass_kg"])
    if not math.isclose(
        spacing,
        float(prepared_manifest["particle"]["spacing_m"]),
        rel_tol=1.0e-9,
        abs_tol=1.0e-12,
    ):
        raise ValueError("source spacing differs from the accepted preparation contract")
    bounds = containment_bounds(prepared_points, spacing)
    ground_z = float(prepared_manifest["contact"]["ground_z_m"])
    if not math.isclose(ground_z, source_ground_z, rel_tol=1.0e-7, abs_tol=1.0e-7):
        raise ValueError("source ground differs from the accepted preparation contract")
    local = (
        np.linalg.norm(prepared_points[:, :2] - np.asarray(center_xy), axis=1)
        <= radius + spacing
    )
    if not np.any(local):
        raise ValueError("no prepared particles lie beneath the cylinder")
    initial_surface_z = float(np.max(prepared_points[local, 2]))
    initial_center_z = initial_surface_z + float(action["start_clearance_m"]) + half_height
    pre_settle_center_z = initial_surface_z + args.removal_height_m

    import newton
    import warp as wp
    from newton.solvers import SolverImplicitMPM, SolverKamino
    from newton.solvers.experimental.coupled import SolverCoupledProxy

    wp.init()
    newton.use_coord_layout_targets = True
    device = wp.get_device(args.device)
    builder = newton.ModelBuilder()
    SolverImplicitMPM.register_custom_attributes(builder)
    if args.guide_coupling_mode == "native_proxy":
        SolverKamino.register_custom_attributes(builder)
    count = prepared_points.shape[0]
    particle_mass = particle_mass_kg(config.material.density_kg_m3, spacing)
    builder.add_particles(
        pos=prepared_points,
        vel=np.zeros_like(prepared_points),
        mass=np.full(count, particle_mass, dtype=np.float32),
        radius=np.full(count, 0.5 * spacing, dtype=np.float32),
    )
    add_static_containment(
        builder,
        newton,
        wp,
        bounds=bounds,
        ground_z=ground_z,
        wall_height=config.contact.wall_height_m,
        wall_thickness=config.contact.wall_thickness_m,
        ground_mu=config.contact.ground_friction_coefficient,
        wall_mu=config.contact.wall_friction_coefficient,
    )
    inertia_xy = mass * (3.0 * radius * radius + height * height) / 12.0
    inertia_z = 0.5 * mass * radius * radius
    add_cylinder_body = (
        builder.add_link
        if args.guide_coupling_mode == "native_proxy"
        else builder.add_body
    )
    cylinder_body = add_cylinder_body(
        xform=wp.transform(
            wp.vec3(center_xy[0], center_xy[1], pre_settle_center_z),
            wp.quat_identity(),
        ),
        inertia=wp.mat33(
            inertia_xy, 0.0, 0.0,
            0.0, inertia_xy, 0.0,
            0.0, 0.0, inertia_z,
        ),
        mass=mass,
        label="newton_guided_cylinder",
        lock_inertia=True,
    )
    guide_joint = None
    if args.guide_coupling_mode == "native_proxy":
        guide_joint = builder.add_joint_prismatic(
            parent=-1,
            child=cylinder_body,
            parent_xform=wp.transform(
                wp.vec3(center_xy[0], center_xy[1], pre_settle_center_z),
                wp.quat_identity(),
            ),
            child_xform=wp.transform(wp.vec3(0.0), wp.quat_identity()),
            axis=wp.vec3(0.0, 0.0, 1.0),
            damping=0.0,
            friction=0.0,
            limit_lower=-2.0,
            limit_upper=2.0,
            label="newton_vertical_guide",
        )
        builder.add_articulation(
            [guide_joint], label="newton_vertical_guide_articulation"
        )
    cylinder_cfg = newton.ModelBuilder.ShapeConfig(
        mu=args.cylinder_friction_coefficient,
        density=0.0,
    )
    collision_radius = radius
    collision_half_height = half_height
    if args.cylinder_collider_mode == "circumscribed_mesh":
        collision_radius = circumscribed_cylinder_radius(
            radius + args.cylinder_collision_guard_m,
            args.cylinder_collider_segments,
        )
        collision_half_height = half_height + args.cylinder_collision_guard_m
        cylinder_mesh = newton.Mesh.create_cylinder(
            collision_radius,
            collision_half_height,
            up_axis=newton.Axis.Z,
            segments=args.cylinder_collider_segments,
            compute_normals=False,
            compute_uvs=False,
            compute_inertia=False,
        )
        collision_center_offset_z = cylinder_collision_center_offset_z(
            args.cylinder_collision_bottom_inset_m,
            half_height,
            collision_half_height,
        )
        builder.add_shape_mesh(
            cylinder_body,
            xform=wp.transform(
                wp.vec3(0.0, 0.0, collision_center_offset_z),
                wp.quat_identity(),
            ),
            mesh=cylinder_mesh,
            cfg=cylinder_cfg,
            label="newton_guided_cylinder_shape",
        )
    else:
        collision_center_offset_z = cylinder_collision_center_offset_z(
            args.cylinder_collision_bottom_inset_m,
            half_height,
            collision_half_height,
        )
        builder.add_shape_cylinder(
            cylinder_body,
            xform=wp.transform(
                wp.vec3(0.0, 0.0, collision_center_offset_z),
                wp.quat_identity(),
            ),
            radius=radius,
            half_height=half_height,
            cfg=cylinder_cfg,
            label="newton_guided_cylinder_shape",
        )
    model = builder.finalize(device=device)
    model.set_gravity((0.0, 0.0, -9.81))
    assign_material(model, config.material)
    solver_config = SolverImplicitMPM.Config(
        voxel_size=config.solver.voxel_size_m,
        grid_type=config.solver.grid_type,
        grid_padding=config.solver.grid_padding,
        transfer_scheme=config.solver.transfer_scheme,
        integration_scheme=config.solver.integration_scheme,
        strain_basis=config.solver.strain_basis,
        collider_basis=config.solver.collider_basis,
        velocity_basis=config.solver.velocity_basis,
        max_iterations=config.solver.max_iterations,
        tolerance=config.solver.tolerance,
        air_drag=config.solver.air_drag,
        critical_fraction=config.solver.critical_fraction,
        collider_velocity_mode="forward",
    )
    state = model.state()
    set_body_state(state, cylinder_body, center_xy, pre_settle_center_z, 0.0)
    control = None
    cylinder_collider_body = cylinder_body
    if args.guide_coupling_mode == "native_proxy":
        assert guide_joint is not None
        kamino_config = SolverKamino.Config()
        kamino_config.use_collision_detector = False
        kamino_config.use_fk_solver = False
        kamino_config.dynamics.preconditioning = True
        kamino_config.padmm.max_iterations = 120
        kamino_config.padmm.primal_tolerance = args.rigid_solver_tolerance
        kamino_config.padmm.dual_tolerance = args.rigid_solver_tolerance
        kamino_config.padmm.compl_tolerance = args.rigid_solver_tolerance
        kamino_config.padmm.rho_0 = 0.1
        kamino_config.padmm.use_acceleration = True
        kamino_config.padmm.warmstart_mode = "containers"
        solver = SolverCoupledProxy(
            model=model,
            entries=[
                SolverCoupledProxy.Entry(
                    name="kamino",
                    solver=lambda view: SolverKamino(
                        model=view,
                        config=kamino_config,
                    ),
                    bodies=[cylinder_body],
                    joints=[guide_joint],
                    substeps=args.rigid_substeps,
                ),
                SolverCoupledProxy.Entry(
                    name="mpm",
                    solver=lambda view: SolverImplicitMPM(
                        model=view,
                        config=solver_config,
                    ),
                    particles=list(range(model.particle_count)),
                    in_place=True,
                ),
            ],
            coupling=SolverCoupledProxy.Config(
                proxies=[
                    SolverCoupledProxy.Proxy(
                        source="kamino",
                        destination="mpm",
                        bodies=[cylinder_body],
                        mass_scale=1.0,
                        mode="lagged",
                        collision_pipeline=lambda _model: None,
                    )
                ],
                iterations=args.proxy_iterations,
            ),
        )
        mpm_solver = solver.solver("mpm")
        control = model.control()
        cylinder_collider_body = 0
    else:
        solver = SolverImplicitMPM(model, config=solver_config)
        mpm_solver = solver
    if args.cylinder_projection_threshold_m is not None:
        mpm_solver.setup_collider(
            collider_projection_threshold=cylinder_projection_thresholds(
                mpm_solver.collider_body_index.numpy(),
                cylinder_collider_body,
                args.cylinder_projection_threshold_m,
            )
        )
    collider_basis_degree = {"Q1": 1, "S2": 2, "S3": 3}.get(
        config.solver.collider_basis
    )
    default_activation_distance_voxels = (
        0.5 / collider_basis_degree if collider_basis_degree else None
    )
    contact_activation = {
        "implementation": "Newton package default",
        "requested_activation_distance_voxels": None,
        "newton_default_activation_distance_voxels": (
            default_activation_distance_voxels
        ),
        "containment_uses_newton_default": True,
        "signed_distance_geometry_unchanged": True,
        "project_outside_geometry_unchanged": True,
    }
    if args.cylinder_contact_activation_distance_voxels is not None:
        from newton_collider_activation import (
            install_per_collider_activation_override,
        )

        contact_activation.update(
            install_per_collider_activation_override(
                mpm_solver,
                body_index=cylinder_collider_body,
                activation_distance_voxels=(
                    args.cylinder_contact_activation_distance_voxels
                ),
            )
        )
    solver.reset(state)

    trace_rows: list[dict[str, Any]] = []
    wall_start = time.perf_counter()
    pre_settle_steps = int(round(args.pre_settle_duration_s / args.dt_s))
    required_hold_steps = int(
        math.ceil(args.pre_settle_required_duration_s / args.dt_s)
    )
    low_speed_steps = 0
    pre_settle_first_equilibrium_s = None
    pre_settle_final_speed: dict[str, float] | None = None
    for step in range(1, pre_settle_steps + 1):
        set_body_state(state, cylinder_body, center_xy, pre_settle_center_z, 0.0)
        state.clear_forces()
        solver.step(state, state, control, None, args.dt_s)
        mpm_solver.project_outside(state, state, args.dt_s)
        pre_settle_final_speed = speed_summary(state.particle_qd.numpy())
        if pre_settle_final_speed["p99_mps"] <= args.particle_speed_threshold_mps:
            low_speed_steps += 1
            if (
                low_speed_steps >= required_hold_steps
                and pre_settle_first_equilibrium_s is None
            ):
                pre_settle_first_equilibrium_s = step * args.dt_s
        else:
            low_speed_steps = 0
        if step % args.diagnostic_every == 0 or step == pre_settle_steps:
            trace_rows.append(
                {
                    "phase": "pre_settle",
                    "step": step,
                    "phase_time_s": step * args.dt_s,
                    "cylinder_center_z_m": pre_settle_center_z,
                    "cylinder_vertical_speed_mps": 0.0,
                    "cylinder_upward_impulse_ns": 0.0,
                    "cylinder_contact_nodes": 0,
                    "inside_particle_centers": 0,
                    "max_center_penetration_m": 0.0,
                    "particle_speed_p99_mps": pre_settle_final_speed["p99_mps"],
                }
            )
    if pre_settle_first_equilibrium_s is None or pre_settle_final_speed is None:
        raise RuntimeError(
            "fresh Newton state failed the cylinder-free speed hold before loading"
        )

    initial_arrays = state_arrays(state)
    local = (
        np.linalg.norm(initial_arrays["position_m"][:, :2] - np.asarray(center_xy), axis=1)
        <= radius + spacing
    )
    initial_surface_z = float(np.max(initial_arrays["position_m"][local, 2]))
    initial_center_z = initial_surface_z + float(action["start_clearance_m"]) + half_height
    initial_map, initial_supported = project_surface(
        initial_arrays["position_m"], oracle_manifest, args.max_fill_distance_m
    )
    write_particle_ply(initial_arrays["position_m"], output / "particles_initial_mpm.ply")
    write_state(output / "newton_state_initial.npz", state)

    loaded_steps = int(round(args.loaded_duration_s / args.dt_s))
    residual_steps = int(round(args.residual_duration_s / args.dt_s))
    cylinder_z = initial_center_z
    cylinder_vz = 0.0
    max_inside = 0
    max_penetration = 0.0
    max_contact_nodes = 0
    max_impulse_contact_nodes = 0
    max_upward_impulse = 0.0
    assigned_sdf_min = None
    assigned_sdf_max = None
    impulse_sdf_min = None
    impulse_sdf_max = None
    first_impulse_step = None
    first_impulse_bottom_relative_to_surface = None
    set_body_state(state, cylinder_body, center_xy, cylinder_z, cylinder_vz)
    for step in range(1, loaded_steps + 1):
        if args.guide_coupling_mode == "explicit_impulse":
            cylinder_z, cylinder_vz = set_body_state(
                state, cylinder_body, center_xy, cylinder_z, cylinder_vz
            )
        state.clear_forces()
        solver.step(state, state, control, None, args.dt_s)
        if args.guide_coupling_mode == "native_proxy":
            cylinder_z, cylinder_vz = body_vertical_state(state, cylinder_body)
        contacts = collect_cylinder_contacts(
            mpm_solver,
            state,
            cylinder_collider_body,
            center_xy,
            cylinder_z,
            radius,
            half_height,
        )
        impulse_z = float(contacts["upward_impulse_ns"])
        contact_nodes = int(contacts["assigned_nodes"])
        impulse_nodes = int(contacts["impulse_nodes"])
        mpm_solver.project_outside(state, state, args.dt_s)
        if args.guide_coupling_mode != "native_proxy":
            cylinder_z, cylinder_vz = advance_guided_body(
                cylinder_z,
                cylinder_vz,
                impulse_z,
                mass,
                args.dt_s,
                args.guided_body_position_update,
            )
        max_contact_nodes = max(max_contact_nodes, contact_nodes)
        max_impulse_contact_nodes = max(max_impulse_contact_nodes, impulse_nodes)
        max_upward_impulse = max(max_upward_impulse, impulse_z)
        for key, use_min in (
            ("assigned_sdf_min_m", True),
            ("assigned_sdf_max_m", False),
            ("impulse_sdf_min_m", True),
            ("impulse_sdf_max_m", False),
        ):
            value = contacts[key]
            if value is None:
                continue
            variable_name = key.removesuffix("_m")
            current = {
                "assigned_sdf_min": assigned_sdf_min,
                "assigned_sdf_max": assigned_sdf_max,
                "impulse_sdf_min": impulse_sdf_min,
                "impulse_sdf_max": impulse_sdf_max,
            }[variable_name]
            updated = (
                float(value)
                if current is None
                else (min(current, float(value)) if use_min else max(current, float(value)))
            )
            if variable_name == "assigned_sdf_min":
                assigned_sdf_min = updated
            elif variable_name == "assigned_sdf_max":
                assigned_sdf_max = updated
            elif variable_name == "impulse_sdf_min":
                impulse_sdf_min = updated
            else:
                impulse_sdf_max = updated
        if abs(impulse_z) > 1.0e-4 and first_impulse_step is None:
            first_impulse_step = step
            first_impulse_bottom_relative_to_surface = (
                cylinder_z - half_height - initial_surface_z
            )
        if step % args.diagnostic_every == 0 or step == loaded_steps:
            points = state.particle_q.numpy()
            penetration = cylinder_penetration(
                points, center_xy, cylinder_z, radius, half_height
            )
            max_inside = max(max_inside, int(penetration["inside_particle_centers"]))
            max_penetration = max(
                max_penetration, float(penetration["max_center_penetration_m"])
            )
            speeds = speed_summary(state.particle_qd.numpy())
            trace_rows.append(
                {
                    "phase": "loading",
                    "step": step,
                    "phase_time_s": step * args.dt_s,
                    "cylinder_center_z_m": cylinder_z,
                    "cylinder_vertical_speed_mps": cylinder_vz,
                    "cylinder_upward_impulse_ns": impulse_z,
                    "cylinder_contact_nodes": contact_nodes,
                    "cylinder_impulse_nodes": impulse_nodes,
                    "contact_assigned_sdf_min_m": contacts["assigned_sdf_min_m"],
                    "contact_assigned_sdf_max_m": contacts["assigned_sdf_max_m"],
                    "contact_impulse_sdf_min_m": contacts["impulse_sdf_min_m"],
                    "contact_impulse_sdf_max_m": contacts["impulse_sdf_max_m"],
                    "inside_particle_centers": penetration["inside_particle_centers"],
                    "max_center_penetration_m": penetration["max_center_penetration_m"],
                    "particle_speed_p99_mps": speeds["p99_mps"],
                }
            )

    if args.guide_coupling_mode == "explicit_impulse":
        cylinder_z, cylinder_vz = set_body_state(
            state, cylinder_body, center_xy, cylinder_z, cylinder_vz
        )
    loaded_body_pose = state.body_q.numpy()[cylinder_body].copy()
    loaded_body_velocity = state.body_qd.numpy()[cylinder_body].copy()
    loaded_arrays = state_arrays(state)
    loaded_speed = speed_summary(loaded_arrays["velocity_mps"])
    loaded_map, loaded_supported = project_surface(
        loaded_arrays["position_m"], oracle_manifest, args.max_fill_distance_m
    )
    loaded_penetration = cylinder_penetration(
        loaded_arrays["position_m"], center_xy, cylinder_z, radius, half_height
    )
    write_particle_ply(loaded_arrays["position_m"], output / "particles_loaded_mpm.ply")
    write_state(output / "newton_state_loaded.npz", state)
    loaded_center_z = cylinder_z
    loaded_vertical_speed = cylinder_vz

    removed_center_z = float(np.max(loaded_arrays["position_m"][:, 2])) + args.removal_height_m
    cylinder_z = removed_center_z
    cylinder_vz = 0.0
    set_body_state(state, cylinder_body, center_xy, cylinder_z, cylinder_vz)
    for step in range(1, residual_steps + 1):
        set_body_state(state, cylinder_body, center_xy, cylinder_z, 0.0)
        state.clear_forces()
        solver.step(state, state, control, None, args.dt_s)
        mpm_solver.project_outside(state, state, args.dt_s)
        if step % args.diagnostic_every == 0 or step == residual_steps:
            speeds = speed_summary(state.particle_qd.numpy())
            trace_rows.append(
                {
                    "phase": "post_removal",
                    "step": step,
                    "phase_time_s": step * args.dt_s,
                    "cylinder_center_z_m": cylinder_z,
                    "cylinder_vertical_speed_mps": 0.0,
                    "cylinder_upward_impulse_ns": 0.0,
                    "cylinder_contact_nodes": 0,
                    "inside_particle_centers": 0,
                    "max_center_penetration_m": 0.0,
                    "particle_speed_p99_mps": speeds["p99_mps"],
                }
            )
    wp.synchronize_device(device)
    wall_time = time.perf_counter() - wall_start

    residual_arrays = state_arrays(state)
    residual_speed = speed_summary(residual_arrays["velocity_mps"])
    residual_map, residual_supported = project_surface(
        residual_arrays["position_m"], oracle_manifest, args.max_fill_distance_m
    )
    write_particle_ply(residual_arrays["position_m"], output / "particles_residual_mpm.ply")
    write_state(output / "newton_state_residual.npz", state)
    valid = (
        chrono_valid
        & initial_supported
        & loaded_supported
        & residual_supported
        & np.isfinite(initial_map)
        & np.isfinite(loaded_map)
        & np.isfinite(residual_map)
    )
    np.save(output / "initial_heightmap_m.npy", initial_map)
    np.save(output / "loaded_heightmap_m.npy", loaded_map)
    np.save(output / "residual_heightmap_m.npy", residual_map)
    np.save(output / "valid_heightmap_mask.npy", valid)
    write_trace(output / "cylinder_trace.csv", trace_rows)

    finite = all(
        np.isfinite(array).all()
        for arrays in (loaded_arrays, residual_arrays)
        for array in arrays.values()
    ) and math.isfinite(loaded_center_z) and math.isfinite(loaded_vertical_speed)
    initial_match = surface_match(
        initial_map, initial_supported, chrono_initial, chrono_valid
    )
    loaded_response = response_error(
        loaded_map, initial_map, chrono_loaded, chrono_initial, valid
    )
    residual_response = response_error(
        residual_map, initial_map, chrono_residual, chrono_initial, valid
    )
    strict_penetration_passed = (
        max_inside == 0
        and int(loaded_penetration["inside_particle_centers"]) == 0
    )
    guide_error = guide_constraint_error(
        loaded_body_pose, loaded_body_velocity, center_xy
    )
    guide_constraint_passed = all(
        value <= 1.0e-6 for value in guide_error.values()
    )
    acceptance_blockers = []
    if not preparation_convergence_passed:
        acceptance_blockers.append(
            "Newton preparation timestep convergence is not demonstrated."
        )
    if not strict_penetration_passed:
        acceptance_blockers.append(
            "The strict zero particle-center penetration gate failed."
        )
    if not finite:
        acceptance_blockers.append("The coupled state contains non-finite values.")
    if not guide_constraint_passed:
        acceptance_blockers.append(
            "The cylinder violated the ideal vertical prismatic guide constraint."
        )
    mechanics_qualified = bool(
        preparation_convergence_passed
        and strict_penetration_passed
        and guide_constraint_passed
        and finite
    )
    manifest = {
        "schema_version": 1,
        "backend": "newton",
        "status": (
            "mechanics_qualified_uncalibrated"
            if mechanics_qualified
            else "diagnostic_only"
        ),
        "accepted": mechanics_qualified,
        "acceptance_eligible": preparation_convergence_passed,
        "mechanics_qualified": mechanics_qualified,
        "calibrated": False,
        "acceptance_blockers": acceptance_blockers,
        "preparation": {
            "contract_path": str(prepared_root),
            "convergence_summary": (
                str(convergence_path) if convergence_path is not None else None
            ),
            "convergence_passed": preparation_convergence_passed,
            "qualification_mode": (
                "candidate_preflight" if args.candidate_preparation else "timestep_matrix"
            ),
            "source_particles_ply": str(source_ply),
            "source_metadata_json": str(source_metadata_path),
            "mode": "fresh in-process preparation before cylinder loading",
            "newton_state_loaded": False,
            "genesis_state_loaded": False,
            "pre_settle": {
                "duration_s": pre_settle_steps * args.dt_s,
                "required_low_speed_duration_s": args.pre_settle_required_duration_s,
                "speed_threshold_mps": args.particle_speed_threshold_mps,
                "first_equilibrium_s": pre_settle_first_equilibrium_s,
                "final_speed": pre_settle_final_speed,
            },
        },
        "chrono_episode": str(args.chrono_episode.resolve()),
        "environment": {
            "python": platform.python_version(),
            "newton": newton.__version__,
            "warp": wp.__version__,
            "device": str(device),
        },
        "solver": {
            **config.raw["solver"],
            "dt_s": args.dt_s,
            "collider_velocity_mode": "forward",
            "coupling": (
                "Newton SolverCoupledProxy: Kamino prismatic rigid body to implicit MPM"
                if args.guide_coupling_mode == "native_proxy"
                else "explicit vertically constrained body update from collected MPM impulses"
            ),
            "guide_coupling_mode": args.guide_coupling_mode,
            "proxy_mode": (
                "lagged" if args.guide_coupling_mode == "native_proxy" else None
            ),
            "proxy_iterations": (
                args.proxy_iterations
                if args.guide_coupling_mode == "native_proxy"
                else None
            ),
            "rigid_solver": (
                "kamino" if args.guide_coupling_mode == "native_proxy" else None
            ),
            "rigid_substeps": (
                args.rigid_substeps
                if args.guide_coupling_mode == "native_proxy"
                else None
            ),
            "rigid_solver_tolerance": (
                args.rigid_solver_tolerance
                if args.guide_coupling_mode == "native_proxy"
                else None
            ),
        },
        "action": {
            **action,
            "initial_surface_z_m": initial_surface_z,
            "initial_center_z_m": initial_center_z,
            "loaded_duration_s": loaded_steps * args.dt_s,
            "residual_duration_s": residual_steps * args.dt_s,
            "removal_implementation": "instantaneous collider relocation above MPM domain",
            "removed_center_z_m": removed_center_z,
        },
        "cylinder": {
            "body_index": cylinder_body,
            "guide_joint_index": guide_joint,
            "friction_coefficient": args.cylinder_friction_coefficient,
            "collider_mode": args.cylinder_collider_mode,
            "collider_segments": (
                args.cylinder_collider_segments
                if args.cylinder_collider_mode == "circumscribed_mesh"
                else 32
            ),
            "analytic_radius_m": radius,
            "collision_mesh_vertex_radius_m": collision_radius,
            "collision_mesh_half_height_m": collision_half_height,
            "collision_guard_m": args.cylinder_collision_guard_m,
            "collision_bottom_inset_m": args.cylinder_collision_bottom_inset_m,
            "collision_center_offset_z_m": collision_center_offset_z,
            "projection_threshold_m": args.cylinder_projection_threshold_m,
            "guided_body_position_update": (
                "native_kamino_prismatic"
                if args.guide_coupling_mode == "native_proxy"
                else args.guided_body_position_update
            ),
            "loaded_body_pose_xyzw": loaded_body_pose.tolist(),
            "loaded_body_velocity_linear_angular": loaded_body_velocity.tolist(),
            "guide_constraint_error": guide_error,
            "guide_constraint_tolerance": 1.0e-6,
            "guide_constraint_passed": guide_constraint_passed,
            "loaded_center_z_m": loaded_center_z,
            "loaded_vertical_speed_mps": loaded_vertical_speed,
            "center_drop_m": initial_center_z - loaded_center_z,
            "sinkage_below_initial_surface_m": (
                initial_surface_z - (loaded_center_z - half_height)
            ),
            "bottom_relative_to_initial_surface_m": (
                loaded_center_z - half_height - initial_surface_z
            ),
            "loaded_particle_speed": loaded_speed,
            "max_contact_nodes": max_contact_nodes,
            "max_impulse_contact_nodes": max_impulse_contact_nodes,
            "max_upward_impulse_ns": max_upward_impulse,
        },
        "contact_activation": {
            **contact_activation,
            "distance_unit": "grid voxels",
            "voxel_size_m": config.solver.voxel_size_m,
            "first_impulse_step": first_impulse_step,
            "first_impulse_time_s": (
                first_impulse_step * args.dt_s
                if first_impulse_step is not None
                else None
            ),
            "first_impulse_threshold_ns": 1.0e-4,
            "first_impulse_analytic_bottom_relative_to_initial_surface_m": (
                first_impulse_bottom_relative_to_surface
            ),
            "assigned_node_sdf_range_m": [assigned_sdf_min, assigned_sdf_max],
            "impulse_node_sdf_range_m": [impulse_sdf_min, impulse_sdf_max],
            "sdf_sign_convention": "negative inside analytic cylinder",
        },
        "penetration": {
            "sample_every_steps": args.diagnostic_every,
            "max_inside_particle_centers": max_inside,
            "max_center_penetration_m": max_penetration,
            "loaded": loaded_penetration,
            "passed_zero_center_penetration_gate": strict_penetration_passed,
        },
        "surface": {
            "valid_cells": int(np.count_nonzero(valid)),
            "initial_match": initial_match,
            "loaded_response_error": loaded_response,
            "residual_response_error": residual_response,
            "comparison_scope": "all common valid Chrono cells; diagnostic, not calibration objective",
            "residual_particle_speed": residual_speed,
        },
        "finite": finite,
        "wall_time_s": wall_time,
        "outputs": {
            "trace": "cylinder_trace.csv",
            "initial_state": "newton_state_initial.npz",
            "loaded_state": "newton_state_loaded.npz",
            "residual_state": "newton_state_residual.npz",
            "initial_particles": "particles_initial_mpm.ply",
            "loaded_particles": "particles_loaded_mpm.ply",
            "residual_particles": "particles_residual_mpm.ply",
        },
    }
    (output / "newton_cylinder_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (output / "action.json").write_text(
        json.dumps(action, indent=2) + "\n", encoding="utf-8"
    )
    (output / "resolved_config.json").write_text(
        json.dumps(config.raw, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

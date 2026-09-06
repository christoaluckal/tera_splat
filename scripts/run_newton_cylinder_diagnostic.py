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
        "--cylinder-projection-threshold-m",
        type=float,
        default=0.0,
        help=(
            "Override allowed project_outside penetration for the cylinder only; "
            "use 0 for the strict analytic-center diagnostic."
        ),
    )
    parser.add_argument(
        "--guided-body-position-update",
        choices=("semi_implicit", "forward_consistent"),
        default="forward_consistent",
        help=(
            "Position integration for the one-DOF guide. forward_consistent uses "
            "the pre-impulse velocity, matching Newton's forward collider pose."
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
    ):
        value = float(getattr(args, name))
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"{name} must be finite and positive")
    if args.diagnostic_every <= 0:
        raise ValueError("diagnostic-every must be positive")
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


def collect_cylinder_impulse(solver, state, body_index: int) -> tuple[float, int]:
    impulses, _positions, collider_ids = solver.collect_collider_impulses(state)
    impulses_np = impulses.numpy()
    collider_ids_np = collider_ids.numpy()
    body_for_collider = solver.collider_body_index.numpy()
    valid = (collider_ids_np >= 0) & (collider_ids_np < body_for_collider.size)
    cylinder = np.zeros(valid.shape, dtype=bool)
    cylinder[valid] = body_for_collider[collider_ids_np[valid]] == body_index
    return float(np.sum(impulses_np[cylinder, 2])), int(np.count_nonzero(cylinder))


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
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
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
    convergence_path = args.preparation_convergence_summary.resolve()
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
    from newton.solvers import SolverImplicitMPM

    wp.init()
    newton.use_coord_layout_targets = True
    device = wp.get_device(args.device)
    builder = newton.ModelBuilder()
    SolverImplicitMPM.register_custom_attributes(builder)
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
    cylinder_body = builder.add_body(
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
        builder.add_shape_mesh(
            cylinder_body,
            mesh=cylinder_mesh,
            cfg=cylinder_cfg,
            label="newton_guided_cylinder_shape",
        )
    else:
        builder.add_shape_cylinder(
            cylinder_body,
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
    solver = SolverImplicitMPM(model, config=solver_config)
    if args.cylinder_projection_threshold_m is not None:
        solver.setup_collider(
            collider_projection_threshold=cylinder_projection_thresholds(
                solver.collider_body_index.numpy(),
                cylinder_body,
                args.cylinder_projection_threshold_m,
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
        solver.step(state, state, None, None, args.dt_s)
        solver.project_outside(state, state, args.dt_s)
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
    max_upward_impulse = 0.0
    for step in range(1, loaded_steps + 1):
        cylinder_z, cylinder_vz = set_body_state(
            state, cylinder_body, center_xy, cylinder_z, cylinder_vz
        )
        solver.step(state, state, None, None, args.dt_s)
        impulse_z, contact_nodes = collect_cylinder_impulse(solver, state, cylinder_body)
        solver.project_outside(state, state, args.dt_s)
        cylinder_z, cylinder_vz = advance_guided_body(
            cylinder_z,
            cylinder_vz,
            impulse_z,
            mass,
            args.dt_s,
            args.guided_body_position_update,
        )
        max_contact_nodes = max(max_contact_nodes, contact_nodes)
        max_upward_impulse = max(max_upward_impulse, impulse_z)
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
                    "inside_particle_centers": penetration["inside_particle_centers"],
                    "max_center_penetration_m": penetration["max_center_penetration_m"],
                    "particle_speed_p99_mps": speeds["p99_mps"],
                }
            )

    cylinder_z, cylinder_vz = set_body_state(
        state, cylinder_body, center_xy, cylinder_z, cylinder_vz
    )
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
        solver.step(state, state, None, None, args.dt_s)
        solver.project_outside(state, state, args.dt_s)
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
    mechanics_qualified = bool(
        preparation_convergence_passed and strict_penetration_passed and finite
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
            "convergence_summary": str(convergence_path),
            "convergence_passed": preparation_convergence_passed,
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
            "coupling": "explicit vertically constrained body update from collected MPM impulses",
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
            "projection_threshold_m": args.cylinder_projection_threshold_m,
            "guided_body_position_update": args.guided_body_position_update,
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
            "max_upward_impulse_ns": max_upward_impulse,
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

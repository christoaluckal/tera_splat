#!/usr/bin/env python3
"""Run a mass-controlled cylinder release, lift, and post-settle terrain test."""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
from pathlib import Path

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
WRITABLE_CACHE = REPO_ROOT / "outputs" / ".cache"
os.environ.setdefault("XDG_CACHE_HOME", str(WRITABLE_CACHE))
os.environ.setdefault("GS_CACHE_FILE_PATH", str(WRITABLE_CACHE / "genesis"))
os.environ.setdefault("NUMBA_CACHE_DIR", str(WRITABLE_CACHE / "numba"))
os.environ.setdefault("MPLCONFIGDIR", str(WRITABLE_CACHE / "matplotlib"))

from particle_io import load_material_config, read_particle_ply, write_particle_ply
from mpm_state_io import geostatic_state_from_points, load_mpm_state, restore_mpm_state, save_mpm_state
from run_genesis_ground_plane_solver import cuda_device_name, directory_size_bytes, make_bounds, tensor_to_numpy
from run_genesis_indenter_test import (
    DEFAULT_BASE,
    estimate_surface_z,
    get_entity_position,
    surface_displacement_metric_rows,
    write_metrics_csv,
    write_pose_csv,
)


CYLINDER_DIAMETER_M = 0.14605
CYLINDER_RADIUS_M = 0.073025
CYLINDER_HEIGHT_M = 0.0508
CYLINDER_MASS_KG = 1.5
CYLINDER_EQUIV_DENSITY_KG_M3 = 1762.522


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--initial-particles-ply", type=Path, default=DEFAULT_BASE / "particles_initial_mpm.ply")
    parser.add_argument("--initial-metadata-json", type=Path, default=DEFAULT_BASE / "ground_plane_metadata.json")
    parser.add_argument(
        "--initial-mpm-state-npz",
        type=Path,
        default=None,
        help="Complete Genesis MPM state to restore after building the identical bed scene.",
    )
    parser.add_argument(
        "--initialize-geostatic-stress",
        action="store_true",
        help="Initialize depth-varying in-situ stress through F before gravity settling; does not move particles.",
    )
    parser.add_argument(
        "--reinitialize-geostatic-stress-from-state",
        action="store_true",
        help=(
            "Restore the saved particle geometry/active mask, then replace velocity, C, F, and Jp "
            "with an analytic geostatic state for the current material config."
        ),
    )
    parser.add_argument(
        "--geostatic-stress-scale",
        type=float,
        default=1.0,
        help="Multiplier for the analytic rho*g*depth geostatic pressure field.",
    )
    parser.add_argument("--config", type=Path, default=REPO_ROOT / "configs" / "physgaussian_sand_stiff_mid.json")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "outputs" / "mass_controlled_terrain")
    parser.add_argument("--query-xy", type=float, nargs=2, default=(0.0, 0.0))
    parser.add_argument("--indenter-radius", type=float, default=CYLINDER_RADIUS_M)
    parser.add_argument("--indenter-height", type=float, default=CYLINDER_HEIGHT_M)
    parser.add_argument("--indenter-mass", type=float, default=CYLINDER_MASS_KG)
    parser.add_argument("--indenter-rho", type=float, default=CYLINDER_EQUIV_DENSITY_KG_M3)
    parser.add_argument("--first-contact-quantile", type=float, default=0.99)
    parser.add_argument("--start-clearance", type=float, default=0.0)
    parser.add_argument("--loaded-max-time", type=float, default=0.25)
    parser.add_argument(
        "--loaded-run-full-duration",
        action="store_true",
        help="Continue loading through --loaded-max-time after first equilibrium; use for fixed-time Chrono targets.",
    )
    parser.add_argument(
        "--loaded-only",
        action="store_true",
        help="End after the released-cylinder loaded settle phase; diagnostic mode with no removal or residual claim.",
    )
    parser.add_argument("--post-max-time", type=float, default=0.25)
    parser.add_argument(
        "--post-observation-times",
        type=float,
        nargs="+",
        default=None,
        help=(
            "Post-removal elapsed times at which to save particle checkpoints and diagnostics. "
            "When supplied, the post-removal phase always runs through --post-max-time instead "
            "of stopping at its first equilibrium window."
        ),
    )
    parser.add_argument("--required-duration", type=float, default=0.02)
    parser.add_argument("--cylinder-speed-threshold", type=float, default=5.0e-4)
    parser.add_argument("--particle-speed-threshold", type=float, default=5.0e-4)
    parser.add_argument("--particle-speed-percentile", type=float, default=99.0)
    parser.add_argument(
        "--diagnostic-speed-percentiles",
        type=float,
        nargs="+",
        default=(50.0, 90.0, 95.0, 99.0),
        help="Local particle-speed percentiles recorded in the settling diagnostic.",
    )
    parser.add_argument(
        "--settling-depth-window",
        type=float,
        default=0.1,
        help="Trailing loaded-phase window used for penetration-drift metrics, in seconds.",
    )
    parser.add_argument("--local-speed-radius-scale", type=float, default=2.0)
    parser.add_argument("--removal-speed", type=float, default=0.005)
    parser.add_argument("--removal-clearance", type=float, default=0.010)
    parser.add_argument(
        "--removal-mode",
        choices=("lift", "remove_body"),
        default="lift",
        help="Use Chrono-compatible instantaneous body removal or the legacy explicit lift.",
    )
    parser.add_argument(
        "--max-removal-steps",
        type=int,
        default=0,
        help="Optional safety cap for smoke tests. 0 uses the physically implied lift duration.",
    )
    parser.add_argument(
        "--pre-settle-max-time",
        type=float,
        default=0.0,
        help="Gravity-settle the MPM bed for this duration before releasing the cylinder. 0 disables pre-settling.",
    )
    parser.add_argument(
        "--pre-settle-required-duration",
        type=float,
        default=0.02,
        help="Continuous low-speed duration required to label the pre-settled bed as equilibrium.",
    )
    parser.add_argument(
        "--pre-settle-particle-speed-threshold",
        type=float,
        default=5.0e-4,
        help="All-bed p99 particle-speed threshold for pre-settling, in m/s.",
    )
    parser.add_argument(
        "--require-pre-settle",
        action="store_true",
        help="Abort before cylinder loading if the requested pre-settle phase does not reach equilibrium.",
    )
    parser.add_argument(
        "--pre-settle-run-full-duration",
        action="store_true",
        help=(
            "Continue the cylinder-free pre-settle phase through --pre-settle-max-time after "
            "its first equilibrium window. This is used to test a restored initial state for drift or rebound."
        ),
    )
    parser.add_argument(
        "--pre-settle-only",
        action="store_true",
        help="Write the contained no-cylinder settled state and exit before loading.",
    )
    parser.add_argument(
        "--containment-wall-height",
        type=float,
        default=0.0,
        help="Fixed rigid lateral-wall height above the ground plane. 0 disables lateral containment.",
    )
    parser.add_argument("--containment-wall-thickness", type=float, default=0.02)
    parser.add_argument("--backend", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--dt", type=float, default=0.0005)
    parser.add_argument("--substeps", type=int, default=10)
    parser.add_argument("--save-every", type=int, default=100)
    parser.add_argument("--n-grid", type=int, default=64)
    parser.add_argument("--grid-lim", type=float, default=None)
    parser.add_argument("--particle-size", type=float, default=0.0125)
    parser.add_argument(
        "--enable-cpic",
        action="store_true",
        help="Enable Genesis CPIC rigid--MPM coupling; recorded as a frozen solver setting.",
    )
    parser.add_argument("--indenter-friction", type=float, default=0.4)
    parser.add_argument("--indenter-softness", type=float, default=0.0)
    parser.add_argument("--indenter-restitution", type=float, default=0.0)
    parser.add_argument("--ground-coup-friction", type=float, default=0.2)
    parser.add_argument("--ground-coup-softness", type=float, default=0.0)
    parser.add_argument("--ground-coup-restitution", type=float, default=0.0)
    return parser.parse_args()


def local_particle_speed_percentiles(
    sand,
    baseline_points: np.ndarray,
    query_xy: np.ndarray,
    radius: float,
    percentiles: list[float],
) -> dict[float, float]:
    vel = tensor_to_numpy(sand.get_particles_vel())
    distance = np.linalg.norm(baseline_points[:, :2] - query_xy[None, :], axis=1)
    local = distance <= radius
    speeds = np.linalg.norm(vel[local] if np.any(local) else vel, axis=1)
    return {percentile: float(np.percentile(speeds, percentile)) for percentile in percentiles}


def entity_velocity(entity) -> tuple[float, float, float]:
    vel = entity.get_vel().detach().cpu().numpy().reshape(-1, 3)[0]
    return float(vel[0]), float(vel[1]), float(vel[2])


def write_phase_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def trailing_loaded_diagnostics(rows: list[dict], window_s: float) -> dict[str, float]:
    loaded_rows = [row for row in rows if row["phase"] == "loaded"]
    if not loaded_rows:
        return {}
    last_time = float(loaded_rows[-1]["time"])
    window_rows = [row for row in loaded_rows if float(row["time"]) >= last_time - max(window_s, 0.0)]
    depths = np.asarray([float(row["actual_depth"]) for row in window_rows], dtype=np.float64)
    diagnostics = {
        "loaded_depth_window_s": min(max(window_s, 0.0), last_time - float(loaded_rows[0]["time"])),
        "loaded_depth_drift_last_window": float(np.ptp(depths)),
        "loaded_depth_change_last_window": float(depths[-1] - depths[0]),
    }
    for key, value in window_rows[-1].items():
        if key.startswith("particle_speed_p"):
            diagnostics[f"loaded_final_{key}"] = float(value)
    return diagnostics


def add_lateral_containment(scene, gs, points: np.ndarray, ground_z: float, height_m: float, thickness_m: float, friction: float) -> None:
    if height_m <= 0.0:
        return
    if thickness_m <= 0.0:
        raise ValueError("containment wall thickness must be positive")
    xmin, ymin = (float(value) for value in points[:, :2].min(axis=0))
    xmax, ymax = (float(value) for value in points[:, :2].max(axis=0))
    zmax = float(points[:, 2].max())
    bottom = min(float(ground_z), float(points[:, 2].min()))
    height = max(float(height_m), zmax - bottom + float(height_m))
    zcenter = bottom + 0.5 * height
    material = gs.materials.Rigid(needs_coup=True, coup_friction=friction, coup_softness=0.0, coup_restitution=0.0)
    bounds = (
        ((xmin - 0.5 * thickness_m, 0.5 * (ymin + ymax), zcenter), (thickness_m, (ymax - ymin) + 2.0 * thickness_m, height)),
        ((xmax + 0.5 * thickness_m, 0.5 * (ymin + ymax), zcenter), (thickness_m, (ymax - ymin) + 2.0 * thickness_m, height)),
        ((0.5 * (xmin + xmax), ymin - 0.5 * thickness_m, zcenter), ((xmax - xmin) + 2.0 * thickness_m, thickness_m, height)),
        ((0.5 * (xmin + xmax), ymax + 0.5 * thickness_m, zcenter), ((xmax - xmin) + 2.0 * thickness_m, thickness_m, height)),
    )
    for index, (position, size) in enumerate(bounds):
        scene.add_entity(
            gs.morphs.Box(pos=position, size=size, fixed=True, visualization=False),
            material=material,
            name=f"containment_wall_{index}",
        )


def main() -> None:
    args = parse_args()
    if args.reinitialize_geostatic_stress_from_state and args.initial_mpm_state_npz is None:
        raise ValueError("--reinitialize-geostatic-stress-from-state requires --initial-mpm-state-npz")
    if args.initial_mpm_state_npz is not None and args.initialize_geostatic_stress:
        raise ValueError("Use --reinitialize-geostatic-stress-from-state with a saved state")
    total_start = time.perf_counter()
    import genesis as gs

    points = read_particle_ply(args.initial_particles_ply)
    with args.initial_metadata_json.open("r", encoding="utf-8") as f:
        metadata = json.load(f)
    config = load_material_config(args.config)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    sim_dir = args.output_dir / "simulation_ply"
    surface_count = int(metadata.get("surface_particle_count", 0))
    query_xy = np.asarray(args.query_xy, dtype=np.float32)
    backend = gs.cuda if args.backend == "cuda" else gs.cpu
    gs.init(backend=backend, precision="32", seed=0, logging_level="warning")
    grid_lim = float(args.grid_lim if args.grid_lim is not None else config.get("grid_lim", 2.0))
    lower_bound, upper_bound = make_bounds(points, metadata, grid_lim)
    gravity = tuple(float(v) for v in config.get("g", [0.0, 0.0, -9.81]))
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=args.dt, substeps=args.substeps, gravity=gravity, floor_height=lower_bound[2]),
        coupler_options=gs.options.LegacyCouplerOptions(rigid_mpm=True),
        mpm_options=gs.options.MPMOptions(
            dt=args.dt,
            gravity=gravity,
            grid_density=int(args.n_grid) / grid_lim,
            particle_size=args.particle_size,
            enable_CPIC=args.enable_cpic,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
        ),
        show_viewer=False,
    )
    ground_z = float(metadata["ground_plane_mpm"]["point"][2])
    scene.add_entity(
        gs.morphs.Plane(pos=(0.0, 0.0, ground_z), normal=(0.0, 0.0, 1.0), fixed=True, plane_size=(grid_lim * 3.0, grid_lim * 3.0)),
        material=gs.materials.Rigid(
            needs_coup=True,
            coup_friction=args.ground_coup_friction,
            coup_softness=args.ground_coup_softness,
            coup_restitution=args.ground_coup_restitution,
        ),
        name="ground_plane",
    )
    add_lateral_containment(
        scene,
        gs,
        points,
        ground_z,
        args.containment_wall_height,
        args.containment_wall_thickness,
        args.ground_coup_friction,
    )
    pre_settle_hold_z = float(points[:, 2].max()) + max(args.containment_wall_height, 0.0) + args.indenter_height + args.start_clearance + 0.05
    cylinder = scene.add_entity(
        gs.morphs.Cylinder(
            pos=(float(query_xy[0]), float(query_xy[1]), pre_settle_hold_z),
            radius=args.indenter_radius,
            height=args.indenter_height,
            fixed=False,
        ),
        material=gs.materials.Rigid(
            rho=args.indenter_rho,
            needs_coup=True,
            coup_friction=args.indenter_friction,
            coup_softness=args.indenter_softness,
            coup_restitution=args.indenter_restitution,
        ),
        name="mass_controlled_cylinder",
    )
    sand = scene.add_entity(
        gs.morphs.Nowhere(n_particles=int(points.shape[0])),
        material=gs.materials.MPM.Sand(
            E=float(config.get("E", 1e5)),
            nu=float(config.get("nu", 0.2)),
            rho=float(config.get("density", config.get("rho", 1000.0))),
            friction_angle=float(config.get("friction_angle", 45.0)),
            sampler="random",
        ),
        name="sand",
    )
    scene.build()
    sand.set_particles_pos(torch.as_tensor(points, dtype=torch.float32, device=gs.device))
    sand.set_particles_vel(torch.zeros((points.shape[0], 3), dtype=torch.float32, device=gs.device))
    sand.set_particles_active(torch.ones((points.shape[0],), dtype=torch.bool, device=gs.device))
    state_source = "positions_only"
    if args.initial_mpm_state_npz is not None:
        restored = load_mpm_state(args.initial_mpm_state_npz)
        restore_mpm_state(sand, restored, gs.device)
        state_source = f"complete_restore:{args.initial_mpm_state_npz.resolve()}"
        if args.reinitialize_geostatic_stress_from_state:
            frozen_points = restored["pos"][0]
            candidate_state = geostatic_state_from_points(
                sand,
                frozen_points,
                surface_count,
                density_kg_m3=float(config.get("density", config.get("rho", 1000.0))),
                gravity_mps2=float(np.linalg.norm(gravity)),
                youngs_modulus_pa=float(config.get("E", 1e5)),
                poisson_ratio=float(config.get("nu", 0.2)),
                stress_scale=args.geostatic_stress_scale,
            )
            candidate_state["pos"] = restored["pos"].copy()
            candidate_state["active"] = restored["active"].copy()
            restore_mpm_state(sand, candidate_state, gs.device)
            state_source = f"candidate_geostatic_from_frozen_geometry:{args.initial_mpm_state_npz.resolve()}"
    elif args.initialize_geostatic_stress:
        gravity_magnitude = float(np.linalg.norm(gravity))
        restore_mpm_state(
            sand,
            geostatic_state_from_points(
                sand,
                points,
                surface_count,
                density_kg_m3=float(config.get("density", config.get("rho", 1000.0))),
                gravity_mps2=gravity_magnitude,
                youngs_modulus_pa=float(config.get("E", 1e5)),
                poisson_ratio=float(config.get("nu", 0.2)),
                stress_scale=args.geostatic_stress_scale,
            ),
            gs.device,
        )
        state_source = "analytic_geostatic_F"
    source_points = tensor_to_numpy(sand.get_particles_pos())
    write_particle_ply(source_points, args.output_dir / "particles_unsettled_mpm.ply")

    pre_settle_reason = "disabled"
    pre_settle_steps = 0
    pre_settle_final_p99 = 0.0
    if args.pre_settle_max_time > 0.0:
        max_pre_settle_steps = max(1, int(np.ceil(args.pre_settle_max_time / args.dt)))
        required_pre_settle_steps = max(1, int(np.ceil(args.pre_settle_required_duration / args.dt)))
        stable_steps = 0
        pre_settle_reason = "timeout"
        for pre_settle_steps in range(1, max_pre_settle_steps + 1):
            cylinder.set_pos((float(query_xy[0]), float(query_xy[1]), pre_settle_hold_z), zero_velocity=True)
            scene.step(update_visualizer=False, refresh_visualizer=False)
            speeds = np.linalg.norm(tensor_to_numpy(sand.get_particles_vel()), axis=1)
            pre_settle_final_p99 = float(np.percentile(speeds, 99.0))
            if pre_settle_final_p99 <= args.pre_settle_particle_speed_threshold:
                stable_steps += 1
                if stable_steps >= required_pre_settle_steps:
                    pre_settle_reason = "equilibrium"
                    if not args.pre_settle_run_full_duration:
                        break
            else:
                stable_steps = 0
        if args.require_pre_settle and pre_settle_reason != "equilibrium":
            raise RuntimeError("Pre-settle phase timed out before cylinder loading")

    baseline_points = tensor_to_numpy(sand.get_particles_pos())
    if args.pre_settle_only:
        write_particle_ply(baseline_points, args.output_dir / "particles_initial_mpm.ply")
        write_particle_ply(baseline_points, args.output_dir / "particles_final_mpm.ply")
        state_info = save_mpm_state(sand, args.output_dir / "mpm_state.npz")
        write_metrics_csv(
            args.output_dir / "run_metrics.csv",
            [
                ("status", "pre_settle_only", ""),
                ("backend", args.backend, ""),
                ("cuda_device", cuda_device_name(), ""),
                ("particles", points.shape[0], "count"),
                ("pre_settle_termination_reason", pre_settle_reason, ""),
                ("pre_settle_steps", pre_settle_steps, "count"),
                ("pre_settle_duration", pre_settle_steps * args.dt, "seconds"),
                ("pre_settle_particle_speed_threshold", args.pre_settle_particle_speed_threshold, "meters/second"),
                ("pre_settle_final_particle_speed_p99", pre_settle_final_p99, "meters/second"),
                ("containment_wall_height", args.containment_wall_height, "meters"),
                ("containment_wall_thickness", args.containment_wall_thickness, "meters"),
                ("complete_state_restore", True, ""),
                ("state_source", state_source, ""),
                ("saved_state_particles", state_info["particles"], "count"),
                ("total_wall_seconds", time.perf_counter() - total_start, "seconds"),
            ],
        )
        with (args.output_dir / "resolved_config.json").open("w", encoding="utf-8") as file:
            json.dump({"args": vars(args), "material_config": config, "source_metadata": metadata}, file, indent=2, default=str)
        print(f"output: {args.output_dir}")
        print(f"pre_settle_termination_reason: {pre_settle_reason}")
        return
    surface_z = estimate_surface_z(baseline_points, query_xy, args.indenter_radius)
    distance = np.linalg.norm(baseline_points[:, :2] - query_xy[None, :], axis=1)
    footprint = baseline_points[distance <= max(args.indenter_radius, 1.0e-6)]
    if footprint.shape[0] > 0:
        surface_z = float(np.quantile(footprint[:, 2], args.first_contact_quantile))
    initial_center_z = surface_z + args.start_clearance + args.indenter_height * 0.5
    cylinder.set_pos((float(query_xy[0]), float(query_xy[1]), initial_center_z), zero_velocity=True)
    mass_before = float(cylinder.get_mass())
    cylinder.set_mass(float(args.indenter_mass))
    mass_after = float(cylinder.get_mass())
    mass_error = abs(mass_after - args.indenter_mass) / max(args.indenter_mass, 1.0e-12)
    if mass_error > 1.0e-3:
        raise RuntimeError(f"Cylinder mass mismatch: requested={args.indenter_mass} actual={mass_after}")

    write_particle_ply(baseline_points, sim_dir / "sim_000000.ply")
    write_particle_ply(baseline_points, args.output_dir / "particles_initial_mpm.ply")
    save_mpm_state(sand, args.output_dir / "mpm_state_initial.npz")
    pose_rows: list[dict] = []
    phase_rows: list[dict] = []
    local_speed_radius = args.indenter_radius * args.local_speed_radius_scale
    diagnostic_percentiles = sorted({*args.diagnostic_speed_percentiles, args.particle_speed_percentile})
    step = 0

    def record(phase: str, command_z: float | None = None) -> None:
        x, y, z = get_entity_position(cylinder, (float(query_xy[0]), float(query_xy[1]), initial_center_z))
        vx, vy, vz = entity_velocity(cylinder)
        particle_speeds = local_particle_speed_percentiles(
            sand,
            baseline_points,
            query_xy,
            local_speed_radius,
            diagnostic_percentiles,
        )
        row = {
            "step": step,
            "time": step * args.dt,
            "phase": phase,
            "x": x,
            "y": y,
            "z": z,
            "vx": vx,
            "vy": vy,
            "vz": vz,
            "speed": float(np.linalg.norm([vx, vy, vz])),
            "particle_speed_pctl": particle_speeds[args.particle_speed_percentile],
            "actual_depth": initial_center_z - z,
            "bottom_z": z - args.indenter_height * 0.5,
            "command_z": "" if command_z is None else command_z,
        }
        for percentile, value in particle_speeds.items():
            row[f"particle_speed_p{percentile:g}"] = value
        pose_rows.append(row)

    def maybe_save(phase: str, force: bool = False) -> None:
        if force or step % max(args.save_every, 1) == 0:
            write_particle_ply(tensor_to_numpy(sand.get_particles_pos()), sim_dir / f"sim_{step:06d}_{phase}.ply")

    def run_until_settled(
        phase: str,
        max_time: float,
        require_cylinder: bool,
        hold_cylinder_z: float | None = None,
        run_full_duration: bool = False,
    ) -> tuple[str, int]:
        nonlocal step
        required_steps = max(1, int(np.ceil(args.required_duration / args.dt)))
        max_steps = max(1, int(np.ceil(max_time / args.dt)))
        stable_steps = 0
        reached_equilibrium = False
        for local_step in range(max_steps):
            if hold_cylinder_z is not None:
                cylinder.set_pos((float(query_xy[0]), float(query_xy[1]), hold_cylinder_z), zero_velocity=True)
            scene.step(update_visualizer=False, refresh_visualizer=False)
            step += 1
            record(phase, hold_cylinder_z)
            maybe_save(phase)
            latest = pose_rows[-1]
            cylinder_ok = (not require_cylinder) or float(latest["speed"]) <= args.cylinder_speed_threshold
            particle_ok = float(latest["particle_speed_pctl"]) <= args.particle_speed_threshold
            stable_steps = stable_steps + 1 if cylinder_ok and particle_ok else 0
            if stable_steps >= required_steps:
                reached_equilibrium = True
                if not run_full_duration:
                    return "equilibrium", local_step + 1
        return ("equilibrium" if reached_equilibrium else "timeout"), max_steps

    def run_post_removal_diagnostic(max_time: float, hold_cylinder_z: float) -> tuple[str, int, float | None, list[dict]]:
        """Run the complete requested post-removal horizon and save fixed-time observations."""
        nonlocal step
        requested_times = sorted({float(value) for value in (args.post_observation_times or ())})
        if any(value <= 0.0 for value in requested_times):
            raise ValueError("--post-observation-times must contain only positive times")
        if requested_times and requested_times[-1] > max_time + 0.5 * args.dt:
            raise ValueError("--post-max-time must cover every --post-observation-times value")

        required_steps = max(1, int(np.ceil(args.required_duration / args.dt)))
        max_steps = max(1, int(np.ceil(max_time / args.dt)))
        post_start_step = step
        stable_steps = 0
        first_equilibrium_time: float | None = None
        observations: list[dict] = []
        next_observation = 0
        for _ in range(max_steps):
            cylinder.set_pos((float(query_xy[0]), float(query_xy[1]), hold_cylinder_z), zero_velocity=True)
            scene.step(update_visualizer=False, refresh_visualizer=False)
            step += 1
            record("post_removal", hold_cylinder_z)
            maybe_save("post_removal")
            latest = pose_rows[-1]
            particle_ok = float(latest["particle_speed_pctl"]) <= args.particle_speed_threshold
            stable_steps = stable_steps + 1 if particle_ok else 0
            elapsed = (step - post_start_step) * args.dt
            if first_equilibrium_time is None and stable_steps >= required_steps:
                first_equilibrium_time = elapsed
            while next_observation < len(requested_times) and elapsed + 1.0e-12 >= requested_times[next_observation]:
                requested = requested_times[next_observation]
                tag = f"{requested:.3f}s".replace(".", "p")
                checkpoint_points = tensor_to_numpy(sand.get_particles_pos())
                write_particle_ply(checkpoint_points, args.output_dir / f"particles_post_removal_{tag}_mpm.ply")
                snapshot = {
                    "requested_time_s": requested,
                    "actual_time_s": elapsed,
                    "step": step,
                    "first_equilibrium_time_s": "" if first_equilibrium_time is None else first_equilibrium_time,
                }
                for percentile in diagnostic_percentiles:
                    snapshot[f"particle_speed_p{percentile:g}"] = latest[f"particle_speed_p{percentile:g}"]
                observations.append(snapshot)
                next_observation += 1
        if next_observation != len(requested_times):
            raise RuntimeError("Post-removal diagnostic did not reach every requested observation time")
        return ("equilibrium" if first_equilibrium_time is not None else "timeout"), max_steps, first_equilibrium_time, observations

    record("initial")
    loaded_reason, loaded_steps = run_until_settled(
        "loaded",
        args.loaded_max_time,
        require_cylinder=True,
        run_full_duration=args.loaded_run_full_duration,
    )
    loaded_points = tensor_to_numpy(sand.get_particles_pos())
    write_particle_ply(loaded_points, args.output_dir / "particles_loaded_mpm.ply")
    save_mpm_state(sand, args.output_dir / "mpm_state_loaded.npz")
    if args.loaded_only:
        maybe_save("loaded_final", force=True)
        write_particle_ply(loaded_points, args.output_dir / "particles_final_mpm.ply")
        save_mpm_state(sand, args.output_dir / "mpm_state_final.npz")
        write_pose_csv(args.output_dir / "cylinder_pose.csv", pose_rows)
        write_phase_csv(args.output_dir / "loaded_settling_diagnostic.csv", [row for row in pose_rows if row["phase"] == "loaded"])
        write_phase_csv(
            args.output_dir / "phase_summary.csv",
            [{"phase": "loaded", "termination_reason": loaded_reason, "steps": loaded_steps}],
        )
        loaded_diagnostics = trailing_loaded_diagnostics(pose_rows, args.settling_depth_window)
        rows = [
            ("status", "loaded_only", ""),
            ("backend", args.backend, ""),
            ("cuda_device", cuda_device_name(), ""),
            ("particles", points.shape[0], "count"),
            ("dt", args.dt, "seconds"),
            ("enable_cpic", args.enable_cpic, ""),
            ("loaded_termination_reason", loaded_reason, ""),
            ("loaded_steps", loaded_steps, "count"),
            ("loaded_duration", loaded_steps * args.dt, "seconds"),
            ("loaded_depth", initial_center_z - float(pose_rows[-1]["z"]), "meters"),
            ("complete_state_restore", args.initial_mpm_state_npz is not None, ""),
            ("state_source", state_source, ""),
            ("removal_executed", False, ""),
            ("total_wall_seconds", time.perf_counter() - total_start, "seconds"),
        ]
        for name, value in loaded_diagnostics.items():
            rows.append((name, value, "meters" if "depth_" in name else "meters/second"))
        rows.extend(
            surface_displacement_metric_rows(
                prefix="loaded",
                baseline_points=baseline_points,
                current_points=loaded_points,
                query_xy=query_xy,
                radius=args.indenter_radius,
                surface_count=surface_count,
            )
        )
        write_metrics_csv(args.output_dir / "run_metrics.csv", rows)
        with (args.output_dir / "resolved_config.json").open("w", encoding="utf-8") as f:
            json.dump({"args": vars(args), "material_config": config, "source_metadata": metadata}, f, indent=2, default=str)
        print(f"output: {args.output_dir}")
        print(f"loaded_termination_reason: {loaded_reason}")
        print(f"loaded_depth_m: {initial_center_z - float(pose_rows[-1]['z']):.9g}")
        return
    loaded_center_z = float(pose_rows[-1]["z"])
    peak_depth = max(float(row["actual_depth"]) for row in pose_rows)
    removal_capped = False
    if args.removal_mode == "remove_body":
        # Chrono removes the body rather than sweeping it through the material.
        # Moving it outside the MPM domain before post-settle reproduces that
        # collision-free state without imparting a lift impulse to the bed.
        removed_center_z = pre_settle_hold_z
        cylinder.set_pos((float(query_xy[0]), float(query_xy[1]), removed_center_z), zero_velocity=True)
        lift_steps = 0
        phase_rows.append({"phase": "removal", "termination_reason": "remove_body", "steps": 0})
    else:
        lift_distance = max(args.removal_clearance, 0.0) + max(0.0, initial_center_z - loaded_center_z)
        lift_steps = max(1, int(np.ceil(lift_distance / max(args.removal_speed * args.dt, 1.0e-12))))
        if args.max_removal_steps > 0 and lift_steps > args.max_removal_steps:
            lift_steps = args.max_removal_steps
            removal_capped = True
        for _ in range(lift_steps):
            target_z = min(initial_center_z + args.removal_clearance, loaded_center_z + args.removal_speed * args.dt)
            loaded_center_z = target_z
            cylinder.set_pos((float(query_xy[0]), float(query_xy[1]), target_z), zero_velocity=True)
            scene.step(update_visualizer=False, refresh_visualizer=False)
            step += 1
            record("removal", target_z)
            maybe_save("removal")
            if target_z >= initial_center_z + args.removal_clearance - 1.0e-9:
                break
        removed_center_z = float(pose_rows[-1]["z"])
    if args.post_observation_times:
        post_reason, post_steps, post_first_equilibrium_time, post_observations = run_post_removal_diagnostic(
            args.post_max_time,
            removed_center_z,
        )
    else:
        post_reason, post_steps = run_until_settled(
            "post_removal",
            args.post_max_time,
            require_cylinder=False,
            hold_cylinder_z=removed_center_z,
        )
        post_first_equilibrium_time = post_steps * args.dt if post_reason == "equilibrium" else None
        post_observations = []
    maybe_save("final", force=True)
    final_points = tensor_to_numpy(sand.get_particles_pos())
    write_particle_ply(final_points, args.output_dir / "particles_final_mpm.ply")
    save_mpm_state(sand, args.output_dir / "mpm_state_final.npz")
    write_pose_csv(args.output_dir / "cylinder_pose.csv", pose_rows)
    loaded_pose_rows = [row for row in pose_rows if row["phase"] == "loaded"]
    write_phase_csv(args.output_dir / "loaded_settling_diagnostic.csv", loaded_pose_rows)
    loaded_diagnostics = trailing_loaded_diagnostics(pose_rows, args.settling_depth_window)
    phase_rows.extend(
        [
            {"phase": "loaded", "termination_reason": loaded_reason, "steps": loaded_steps},
            *([] if args.removal_mode == "remove_body" else [{"phase": "removal", "termination_reason": "capped" if removal_capped else "completed", "steps": lift_steps}]),
            {"phase": "post_removal", "termination_reason": post_reason, "steps": post_steps},
        ]
    )
    write_phase_csv(args.output_dir / "phase_summary.csv", phase_rows)
    write_phase_csv(args.output_dir / "post_removal_observations.csv", post_observations)

    rows = [
        ("status", "completed", ""),
        ("backend", args.backend, ""),
        ("cuda_device", cuda_device_name(), ""),
        ("particles", points.shape[0], "count"),
        ("surface_particles", surface_count, "count"),
        ("dt", args.dt, "seconds"),
        ("substeps", args.substeps, "count"),
        ("particle_size", args.particle_size, "meters"),
        ("enable_cpic", args.enable_cpic, ""),
        ("local_speed_radius", local_speed_radius, "meters"),
        ("settling_depth_window", args.settling_depth_window, "seconds"),
        ("query_x", float(query_xy[0]), "meters"),
        ("query_y", float(query_xy[1]), "meters"),
        ("first_contact_quantile", args.first_contact_quantile, ""),
        ("pre_settle_termination_reason", pre_settle_reason, ""),
        ("pre_settle_steps", pre_settle_steps, "count"),
        ("pre_settle_duration", pre_settle_steps * args.dt, "seconds"),
        ("pre_settle_particle_speed_threshold", args.pre_settle_particle_speed_threshold, "meters/second"),
        ("pre_settle_final_particle_speed_p99", pre_settle_final_p99, "meters/second"),
        ("containment_wall_height", args.containment_wall_height, "meters"),
        ("containment_wall_thickness", args.containment_wall_thickness, "meters"),
        ("first_contact_z", surface_z, "meters"),
        ("initial_center_z", initial_center_z, "meters"),
        ("indenter_radius", args.indenter_radius, "meters"),
        ("indenter_height", args.indenter_height, "meters"),
        ("indenter_mass_before_override", mass_before, "kg"),
        ("indenter_mass_after_override", mass_after, "kg"),
        ("loaded_termination_reason", loaded_reason, ""),
        ("loaded_steps", loaded_steps, "count"),
        ("loaded_duration", loaded_steps * args.dt, "seconds"),
        ("loaded_depth", initial_center_z - float([r for r in pose_rows if r["phase"] == "loaded"][-1]["z"]), "meters"),
        ("peak_loaded_depth", peak_depth, "meters"),
        ("removal_speed", args.removal_speed, "meters/second"),
        ("removal_mode", args.removal_mode, ""),
        ("removal_clearance", args.removal_clearance, "meters"),
        ("max_removal_steps", args.max_removal_steps, "count"),
        ("removal_capped", removal_capped, ""),
        ("post_removal_termination_reason", post_reason, ""),
        ("post_removal_steps", post_steps, "count"),
        ("post_removal_duration", post_steps * args.dt, "seconds"),
        ("post_removal_first_equilibrium_time", "" if post_first_equilibrium_time is None else post_first_equilibrium_time, "seconds"),
        ("post_removal_observation_times", "" if not args.post_observation_times else ";".join(str(value) for value in args.post_observation_times), "seconds"),
        ("final_depth", "" if args.removal_mode == "remove_body" else initial_center_z - float(pose_rows[-1]["z"]), "meters"),
        ("final_depth_meaningful", args.removal_mode != "remove_body", ""),
        ("complete_state_restore", args.initial_mpm_state_npz is not None, ""),
        ("state_source", state_source, ""),
        ("total_wall_seconds", time.perf_counter() - total_start, "seconds"),
        ("output_dir_bytes", directory_size_bytes(args.output_dir), "bytes"),
    ]
    for name, value in loaded_diagnostics.items():
        if name == "loaded_depth_window_s":
            unit = "seconds"
        elif "depth_" in name:
            unit = "meters"
        else:
            unit = "meters/second"
        rows.append((name, value, unit))
    rows.extend(
        surface_displacement_metric_rows(
            prefix="final",
            baseline_points=baseline_points,
            current_points=final_points,
            query_xy=query_xy,
            radius=args.indenter_radius,
            surface_count=surface_count,
        )
    )
    write_metrics_csv(args.output_dir / "run_metrics.csv", rows)
    with (args.output_dir / "resolved_config.json").open("w", encoding="utf-8") as f:
        json.dump({"args": vars(args), "material_config": config, "source_metadata": metadata}, f, indent=2, default=str)
    print(f"output: {args.output_dir}")
    print(f"loaded_termination_reason: {loaded_reason}")
    print(f"post_removal_termination_reason: {post_reason}")
    print(f"loaded_depth_m: {initial_center_z - float([r for r in pose_rows if r['phase'] == 'loaded'][-1]['z']):.9g}")


if __name__ == "__main__":
    main()

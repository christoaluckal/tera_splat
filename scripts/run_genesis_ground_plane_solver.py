#!/usr/bin/env python3
"""Run a Genesis MPM sand update from the same PLY-derived particles."""

from __future__ import annotations

import argparse
import csv
import os
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WRITABLE_CACHE = REPO_ROOT / "outputs" / ".cache"
os.environ.setdefault("XDG_CACHE_HOME", str(WRITABLE_CACHE))
os.environ.setdefault("GS_CACHE_FILE_PATH", str(WRITABLE_CACHE / "genesis"))
os.environ.setdefault("NUMBA_CACHE_DIR", str(WRITABLE_CACHE / "numba"))
os.environ.setdefault("MPLCONFIGDIR", str(WRITABLE_CACHE / "matplotlib"))

import numpy as np
import torch

from particle_io import build_particles, load_material_config, read_particle_ply, write_metadata, write_particle_ply
from view_iteration_7000 import DEFAULT_PLY


DEFAULT_CONFIG = REPO_ROOT / "configs" / "physgaussian_sand.json"
DEFAULT_OUTPUT = REPO_ROOT / "outputs" / "genesis_ground_plane_solver"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ply", type=Path, default=DEFAULT_PLY)
    parser.add_argument(
        "--initial-particles-ply",
        type=Path,
        default=None,
        help="Use this prebuilt XYZ particle PLY instead of rebuilding from --ply.",
    )
    parser.add_argument(
        "--initial-metadata-json",
        type=Path,
        default=None,
        help="Metadata JSON for --initial-particles-ply, including ground_plane_mpm.",
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--opacity-threshold", type=float, default=0.02)
    parser.add_argument("--axis-transform", default="opencv-to-zup")
    parser.add_argument("--max-particles", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--n-grid", type=int, default=None)
    parser.add_argument("--grid-lim", type=float, default=None)
    parser.add_argument("--padding", type=float, default=0.08)
    parser.add_argument(
        "--trim-quantile",
        type=float,
        default=0.0,
        help="Drop points outside per-axis [q, 1-q] quantiles before normalization.",
    )
    parser.add_argument(
        "--ground-quantile",
        type=float,
        default=0.0,
        help="Particle height quantile used for the ground plane. 0.0 uses the minimum height.",
    )
    parser.add_argument(
        "--subsurface-depth",
        type=float,
        default=0.2,
        help="Vertical spacing for bottom-up subsurface support layers, in source units. Use 0 to disable.",
    )
    parser.add_argument(
        "--subsurface-spacing-mpm",
        type=float,
        default=None,
        help="Override support layer spacing directly in normalized MPM units.",
    )
    parser.add_argument(
        "--subsurface-xy-jitter",
        type=float,
        default=0.45,
        help="Uniform XY jitter for subsurface particles as a fraction of support layer spacing.",
    )
    parser.add_argument(
        "--subsurface-layer-depths",
        default=None,
        help="Comma-separated source-unit depths for explicit subsurface layers, e.g. 0.05,0.1,0.15,0.2.",
    )
    parser.add_argument(
        "--subsurface-surface-height-method",
        choices=("linear", "nearest"),
        default="linear",
        help="Surface height interpolation method for subsurface grid points.",
    )
    parser.add_argument(
        "--subsurface-max-surface-distance",
        type=float,
        default=2.0,
        help="Keep subsurface grid points within this many XY spacings of a surface point.",
    )
    parser.add_argument(
        "--ground-offset-below-subsurface",
        type=float,
        default=0.01,
        help="Place ground this many source units below the selected subsurface quantile.",
    )
    parser.add_argument(
        "--ground-subsurface-quantile",
        type=float,
        default=0.01,
        help="Subsurface height quantile used for robust ground placement.",
    )
    parser.add_argument(
        "--no-surface-cap",
        dest="surface_cap",
        action="store_false",
        default=True,
        help="Disable the interpolated regular-grid surface cap.",
    )
    parser.add_argument("--surface-filter-neighbors", type=int, default=0)
    parser.add_argument("--surface-filter-quantile", type=float, default=0.9)
    parser.add_argument(
        "--surface-filter-tolerance",
        type=float,
        default=0.03,
        help="Keep original splat surface points within this source-unit distance below the local top surface.",
    )
    parser.add_argument(
        "--z-stddev-filter",
        type=float,
        default=1.0,
        help="Drop surface candidates with z > mean + N*std before subsurface fill. Use 0 to disable.",
    )
    parser.add_argument(
        "--center-radius",
        type=float,
        default=0.0,
        help="Keep only surface candidates within this aligned source-XY radius from the cloud center. Use 0 to disable.",
    )
    parser.add_argument("--steps", type=int, default=40)
    parser.add_argument("--duration", type=float, default=None)
    parser.add_argument("--dt", type=float, default=None)
    parser.add_argument(
        "--substeps",
        type=int,
        default=None,
        help="Genesis SimOptions substeps. Defaults to config substeps or 1.",
    )
    parser.add_argument("--backend", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument(
        "--gravity-scale",
        type=float,
        default=1.0,
        help="Scale config gravity. Use 0 for a stable baseline before adding contact loads.",
    )
    parser.add_argument(
        "--velocity-damping",
        type=float,
        default=None,
        help="Per-step MPM particle velocity multiplier. Values below 1 dissipate bounce.",
    )
    parser.add_argument("--particle-size", type=float, default=None)
    parser.add_argument("--ground-coup-friction", type=float, default=None)
    parser.add_argument("--ground-coup-softness", type=float, default=None)
    parser.add_argument("--ground-coup-restitution", type=float, default=None)
    parser.add_argument(
        "--metrics-interval",
        type=int,
        default=1000,
        help="Write one step timing row every N simulation steps. Use 0 to disable interval rows.",
    )
    parser.add_argument(
        "--save-every",
        type=int,
        default=1,
        help="Write one PLY frame every N simulation steps. Frame 0 and the final step are always saved.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def tensor_to_numpy(value) -> np.ndarray:
    if hasattr(value, "detach"):
        return value.detach().cpu().numpy()
    if hasattr(value, "cpu"):
        return value.cpu().numpy()
    return np.asarray(value)


def make_bounds(points: np.ndarray, metadata: dict, grid_lim: float) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    ground_z = float(metadata["ground_plane_mpm"]["point"][2])
    margin = max(grid_lim * 0.05, 0.04)
    lower = points.min(axis=0) - margin
    upper = points.max(axis=0) + margin
    lower[2] = min(ground_z, float(points[:, 2].min())) - margin
    upper[2] = max(float(upper[2]), ground_z + margin)
    return tuple(float(v) for v in lower), tuple(float(v) for v in upper)


def directory_size_bytes(path: Path) -> int:
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            total += child.stat().st_size
    return total


def write_summary_metrics(output_dir: Path, rows: list[tuple[str, object, str]]) -> None:
    with (output_dir / "run_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value", "unit"])
        writer.writerows(rows)


def write_step_metrics(output_dir: Path, rows: list[dict]) -> None:
    if not rows:
        return
    fieldnames = [
        "step",
        "elapsed_seconds",
        "interval_seconds",
        "interval_steps",
        "steps_per_second",
        "particle_steps_per_second",
    ]
    with (output_dir / "step_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def cuda_device_name() -> str:
    if not torch.cuda.is_available():
        return ""
    return torch.cuda.get_device_name(0)


def run_solver(args: argparse.Namespace, points: np.ndarray, metadata: dict, config: dict) -> dict:
    run_start = time.perf_counter()
    import genesis as gs

    backend = gs.cuda if args.backend == "cuda" else gs.cpu
    init_start = time.perf_counter()
    gs.init(backend=backend, precision="32", seed=args.seed, logging_level="warning")
    genesis_init_seconds = time.perf_counter() - init_start

    grid_lim = float(args.grid_lim if args.grid_lim is not None else config.get("grid_lim", 2.0))
    n_grid = int(args.n_grid if args.n_grid is not None else config.get("n_grid", 64))
    dt = float(args.dt if args.dt is not None else config.get("substep_dt", 2e-5))
    substeps = int(args.substeps if args.substeps is not None else config.get("substeps", 1))
    steps = int(args.steps)
    if args.duration is not None:
        steps = int(np.ceil(args.duration / dt))
        print(f"duration: {args.duration}")
        print(f"dt: {dt}")
        print(f"steps = ceil(duration / dt): {steps}")

    lower_bound, upper_bound = make_bounds(points, metadata, grid_lim)
    gravity = tuple(float(v) * float(args.gravity_scale) for v in config.get("g", [0.0, 0.0, -9.81]))
    particle_size = args.particle_size
    if particle_size is None:
        particle_size = float(config.get("particle_size", 0.01 * 64.0 / n_grid))
    velocity_damping = args.velocity_damping
    if velocity_damping is None:
        velocity_damping = float(config.get("velocity_damping", 1.0))
    velocity_damping = float(np.clip(velocity_damping, 0.0, 1.0))

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=dt, substeps=substeps, gravity=gravity, floor_height=lower_bound[2]),
        coupler_options=gs.options.LegacyCouplerOptions(rigid_mpm=True),
        mpm_options=gs.options.MPMOptions(
            dt=dt,
            gravity=gravity,
            grid_density=n_grid / grid_lim,
            particle_size=particle_size,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
        ),
        show_viewer=False,
    )
    ground_z = float(metadata["ground_plane_mpm"]["point"][2])
    plane_size = (grid_lim * 3.0, grid_lim * 3.0)
    ground_coup_friction = float(
        args.ground_coup_friction
        if args.ground_coup_friction is not None
        else config.get("ground_coup_friction", 0.2)
    )
    ground_coup_softness = float(
        args.ground_coup_softness
        if args.ground_coup_softness is not None
        else config.get("ground_coup_softness", 0.0)
    )
    ground_coup_restitution = float(
        args.ground_coup_restitution
        if args.ground_coup_restitution is not None
        else config.get("ground_coup_restitution", 0.0)
    )
    scene.add_entity(
        gs.morphs.Plane(pos=(0.0, 0.0, ground_z), normal=(0.0, 0.0, 1.0), fixed=True, plane_size=plane_size),
        material=gs.materials.Rigid(
            needs_coup=True,
            coup_friction=ground_coup_friction,
            coup_softness=ground_coup_softness,
            coup_restitution=ground_coup_restitution,
        ),
        name="extracted_ground_plane",
    )
    sand = scene.add_entity(
        gs.morphs.Nowhere(n_particles=int(points.shape[0])),
        material=gs.materials.MPM.Sand(
            E=float(config.get("E", 1e6)),
            nu=float(config.get("nu", 0.2)),
            rho=float(config.get("density", config.get("rho", 1000.0))),
            friction_angle=float(config.get("friction_angle", 45.0)),
            sampler="random",
        ),
        name="ply_sand_particles",
    )
    scene_build_start = time.perf_counter()
    scene.build()
    scene_build_seconds = time.perf_counter() - scene_build_start

    particle_upload_start = time.perf_counter()
    pos = torch.as_tensor(points, dtype=torch.float32, device=gs.device)
    vel = torch.zeros_like(pos)
    sand.set_particles_pos(pos)
    sand.set_particles_vel(vel)
    sand.set_particles_active(torch.ones((points.shape[0],), dtype=torch.bool, device=gs.device))
    particle_upload_seconds = time.perf_counter() - particle_upload_start

    sim_dir = args.output_dir / "simulation_ply"
    frame0_start = time.perf_counter()
    write_particle_ply(tensor_to_numpy(sand.get_particles_pos()), sim_dir / "sim_0000.ply")
    frame0_write_seconds = time.perf_counter() - frame0_start
    saved_frames = 1

    step_rows = []
    loop_start = time.perf_counter()
    interval_start = loop_start
    interval_step_start = 0
    for step in range(1, steps + 1):
        scene.step(update_visualizer=False, refresh_visualizer=False)
        if velocity_damping < 1.0:
            sand.set_particles_vel(sand.get_particles_vel() * velocity_damping)
        if step % max(args.save_every, 1) == 0 or step == steps:
            write_particle_ply(tensor_to_numpy(sand.get_particles_pos()), sim_dir / f"sim_{step:04d}.ply")
            saved_frames += 1
        if args.metrics_interval > 0 and (step % args.metrics_interval == 0 or step == steps):
            now = time.perf_counter()
            interval_steps = step - interval_step_start
            interval_seconds = now - interval_start
            steps_per_second = interval_steps / max(interval_seconds, 1e-12)
            step_rows.append(
                {
                    "step": step,
                    "elapsed_seconds": now - loop_start,
                    "interval_seconds": interval_seconds,
                    "interval_steps": interval_steps,
                    "steps_per_second": steps_per_second,
                    "particle_steps_per_second": steps_per_second * points.shape[0],
                }
            )
            interval_start = now
            interval_step_start = step

    simulation_loop_seconds = time.perf_counter() - loop_start
    total_solver_wall_seconds = time.perf_counter() - run_start
    write_step_metrics(args.output_dir, step_rows)
    return {
        "backend": args.backend,
        "cuda_device": cuda_device_name(),
        "particles": int(points.shape[0]),
        "surface_particles": int(metadata.get("surface_particle_count", 0)),
        "subsurface_particles": int((metadata.get("subsurface_fill") or {}).get("subsurface_particle_count", 0)),
        "steps": steps,
        "frames": saved_frames,
        "save_every": max(args.save_every, 1),
        "dt": dt,
        "substeps": substeps,
        "effective_substep_dt": dt / max(substeps, 1),
        "duration": args.duration if args.duration is not None else steps * dt,
        "n_grid": n_grid,
        "grid_lim": grid_lim,
        "particle_size": particle_size,
        "velocity_damping": velocity_damping,
        "ground_coup_friction": ground_coup_friction,
        "ground_coup_softness": ground_coup_softness,
        "ground_coup_restitution": ground_coup_restitution,
        "gravity_scale": args.gravity_scale,
        "genesis_init_seconds": genesis_init_seconds,
        "scene_build_seconds": scene_build_seconds,
        "particle_upload_seconds": particle_upload_seconds,
        "frame0_write_seconds": frame0_write_seconds,
        "simulation_loop_seconds": simulation_loop_seconds,
        "total_solver_wall_seconds": total_solver_wall_seconds,
        "average_step_seconds": simulation_loop_seconds / max(steps, 1),
        "steps_per_second": steps / max(simulation_loop_seconds, 1e-12),
        "particle_steps_per_second": (steps * points.shape[0]) / max(simulation_loop_seconds, 1e-12),
    }


def main() -> None:
    total_start = time.perf_counter()
    args = parse_args()
    particle_build_start = time.perf_counter()
    config = load_material_config(args.config)
    if args.initial_particles_ply is not None:
        if args.initial_metadata_json is None:
            raise ValueError("--initial-metadata-json is required with --initial-particles-ply")
        particles = read_particle_ply(args.initial_particles_ply)
        import json

        with args.initial_metadata_json.open("r", encoding="utf-8") as f:
            metadata = json.load(f)
    else:
        particles, metadata = build_particles(args, config)
    particle_build_seconds = time.perf_counter() - particle_build_start
    metadata["solver_backend"] = "genesis"
    metadata["genesis_options"] = {"gravity_scale": args.gravity_scale}

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_particle_ply(particles, args.output_dir / "particles_initial_mpm.ply")
    surface_count = int(metadata.get("surface_particle_count", 0))
    subsurface_count = int((metadata.get("subsurface_fill") or {}).get("subsurface_particle_count", 0))
    if surface_count > 0:
        write_particle_ply(particles[:surface_count], args.output_dir / "particles_surface_mpm.ply")
    if subsurface_count > 0:
        write_particle_ply(
            particles[surface_count : surface_count + subsurface_count],
            args.output_dir / "particles_subsurface_mpm.ply",
        )
    write_metadata(metadata, args.output_dir / "ground_plane_metadata.json")

    print(f"particles: {particles.shape[0]}")
    print(f"ground plane: {metadata['ground_plane_mpm']}")
    print(f"output: {args.output_dir}")

    if args.dry_run:
        write_summary_metrics(
            args.output_dir,
            [
                ("status", "dry_run", ""),
                ("backend", args.backend, ""),
                ("cuda_device", cuda_device_name(), ""),
                ("particles", particles.shape[0], "count"),
                ("surface_particles", metadata.get("surface_particle_count", 0), "count"),
                (
                    "subsurface_particles",
                    (metadata.get("subsurface_fill") or {}).get("subsurface_particle_count", 0),
                    "count",
                ),
                ("particle_build_seconds", particle_build_seconds, "seconds"),
                ("total_wall_seconds", time.perf_counter() - total_start, "seconds"),
                ("output_dir_bytes", directory_size_bytes(args.output_dir), "bytes"),
            ],
        )
        return

    solver_metrics = run_solver(args, particles, metadata, config)
    output_dir_bytes = directory_size_bytes(args.output_dir)
    rows = [
        ("status", "completed", ""),
        ("particle_build_seconds", particle_build_seconds, "seconds"),
        ("total_wall_seconds", time.perf_counter() - total_start, "seconds"),
        ("output_dir_bytes", output_dir_bytes, "bytes"),
    ]
    for key, value in solver_metrics.items():
        unit = ""
        if key.endswith("_seconds"):
            unit = "seconds"
        elif key in {"particles", "surface_particles", "subsurface_particles", "steps", "frames", "n_grid", "substeps"}:
            unit = "count"
        elif key in {"dt", "duration", "average_step_seconds", "effective_substep_dt"}:
            unit = "seconds"
        elif key in {"steps_per_second"}:
            unit = "steps/second"
        elif key in {"particle_steps_per_second"}:
            unit = "particle-steps/second"
        rows.append((key, value, unit))
    write_summary_metrics(args.output_dir, rows)


if __name__ == "__main__":
    main()

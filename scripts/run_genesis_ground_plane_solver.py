#!/usr/bin/env python3
"""Run a Genesis MPM sand update from the same PLY-derived particles."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WRITABLE_CACHE = REPO_ROOT / "outputs" / ".cache"
os.environ.setdefault("XDG_CACHE_HOME", str(WRITABLE_CACHE))
os.environ.setdefault("GS_CACHE_FILE_PATH", str(WRITABLE_CACHE / "genesis"))
os.environ.setdefault("NUMBA_CACHE_DIR", str(WRITABLE_CACHE / "numba"))
os.environ.setdefault("MPLCONFIGDIR", str(WRITABLE_CACHE / "matplotlib"))

import numpy as np
import torch

from particle_io import build_particles, load_material_config, write_metadata, write_particle_ply
from view_iteration_7000 import DEFAULT_PLY


DEFAULT_CONFIG = REPO_ROOT / "configs" / "physgaussian_sand.json"
DEFAULT_OUTPUT = REPO_ROOT / "outputs" / "genesis_ground_plane_solver"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ply", type=Path, default=DEFAULT_PLY)
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
    parser.add_argument("--steps", type=int, default=40)
    parser.add_argument("--duration", type=float, default=None)
    parser.add_argument("--dt", type=float, default=None)
    parser.add_argument("--backend", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument(
        "--gravity-scale",
        type=float,
        default=1.0,
        help="Scale config gravity. Use 0 for a stable baseline before adding contact loads.",
    )
    parser.add_argument("--particle-size", type=float, default=None)
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


def run_solver(args: argparse.Namespace, points: np.ndarray, metadata: dict, config: dict) -> None:
    import genesis as gs

    backend = gs.cuda if args.backend == "cuda" else gs.cpu
    gs.init(backend=backend, precision="32", seed=args.seed, logging_level="warning")

    grid_lim = float(args.grid_lim if args.grid_lim is not None else config.get("grid_lim", 2.0))
    n_grid = int(args.n_grid if args.n_grid is not None else config.get("n_grid", 64))
    dt = float(args.dt if args.dt is not None else config.get("substep_dt", 2e-5))
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

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=dt, gravity=gravity, floor_height=lower_bound[2]),
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
    scene.add_entity(
        gs.morphs.Plane(pos=(0.0, 0.0, ground_z), normal=(0.0, 0.0, 1.0), fixed=True, plane_size=plane_size),
        material=gs.materials.Rigid(),
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
    scene.build()

    pos = torch.as_tensor(points, dtype=torch.float32, device=gs.device)
    vel = torch.zeros_like(pos)
    sand.set_particles_pos(pos)
    sand.set_particles_vel(vel)
    sand.set_particles_active(torch.ones((points.shape[0],), dtype=torch.bool, device=gs.device))

    sim_dir = args.output_dir / "simulation_ply"
    write_particle_ply(tensor_to_numpy(sand.get_particles_pos()), sim_dir / "sim_0000.ply")
    for step in range(1, steps + 1):
        scene.step(update_visualizer=False, refresh_visualizer=False)
        write_particle_ply(tensor_to_numpy(sand.get_particles_pos()), sim_dir / f"sim_{step:04d}.ply")


def main() -> None:
    args = parse_args()
    config = load_material_config(args.config)
    particles, metadata = build_particles(args, config)
    metadata["solver_backend"] = "genesis"
    metadata["genesis_options"] = {"gravity_scale": args.gravity_scale}

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_particle_ply(particles, args.output_dir / "particles_initial_mpm.ply")
    write_metadata(metadata, args.output_dir / "ground_plane_metadata.json")

    print(f"particles: {particles.shape[0]}")
    print(f"ground plane: {metadata['ground_plane_mpm']}")
    print(f"output: {args.output_dir}")

    if args.dry_run:
        return

    run_solver(args, particles, metadata, config)


if __name__ == "__main__":
    main()

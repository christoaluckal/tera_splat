#!/usr/bin/env python3
"""Initialize PhysGaussian MPM particles with a fitted ground plane collider.

This is the first solver-side smoke test. It assumes all retained Gaussians are
sand, uses the same alignment path as the Viser viewer, normalizes particles
into the PhysGaussian MPM grid domain, and adds a sticky ground plane to stop
particles from falling under gravity.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

import numpy as np
import torch

from particle_io import build_particles, load_material_config, write_metadata, write_particle_ply
from view_iteration_7000 import DEFAULT_PLY


REPO_ROOT = Path(__file__).resolve().parents[2]
PHYS_GAUSSIAN_ROOT = REPO_ROOT / "PhysGaussian"
DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "configs" / "physgaussian_sand.json"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "outputs" / "ground_plane_solver"


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
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Simulation duration. When set, steps = ceil(duration / dt).",
    )
    parser.add_argument("--dt", type=float, default=None)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build particles and ground plane metadata without importing Warp.",
    )
    return parser.parse_args()


def run_solver(args: argparse.Namespace, points: np.ndarray, metadata: dict, config: dict) -> None:
    try:
        import warp as wp
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "PhysGaussian solver dependency missing: module 'warp' is not installed "
            "in this Python environment. Install warp-lang in the solver env, then rerun."
        ) from exc
    if "warp.torch" not in sys.modules:
        # PhysGaussian imports the legacy warp.torch submodule. Newer Warp builds
        # expose torch conversion helpers directly on the top-level module.
        sys.modules["warp.torch"] = wp
    if not hasattr(wp.types, "float32"):
        wp.types.float32 = wp.float32
    if not hasattr(wp.types, "array"):
        wp.types.array = wp.array

    if not torch.cuda.is_available() and args.device.startswith("cuda"):
        raise SystemExit(
            f"Requested {args.device}, but torch.cuda.is_available() is false in this environment."
        )

    sys.path.insert(0, str(PHYS_GAUSSIAN_ROOT / "mpm_solver_warp"))
    from engine_utils import save_data_at_frame
    mpm_module = importlib.import_module("mpm_solver_warp")
    warp_utils = importlib.import_module("warp_utils")

    def torch2warp_float(t, copy=False, dtype=None, dvc="cuda:0"):
        del copy, dtype, dvc
        return wp.from_torch(t.contiguous(), dtype=wp.float32)

    def torch2warp_vec3(t, copy=False, dtype=None, dvc="cuda:0"):
        del copy, dtype, dvc
        return wp.from_torch(t.contiguous(), dtype=wp.vec3)

    def torch2warp_mat33(t, copy=False, dtype=None, dvc="cuda:0"):
        del copy, dtype, dvc
        return wp.from_torch(t.contiguous(), dtype=wp.mat33)

    warp_utils.torch2warp_float = torch2warp_float
    warp_utils.torch2warp_vec3 = torch2warp_vec3
    warp_utils.torch2warp_mat33 = torch2warp_mat33
    mpm_module.torch2warp_float = torch2warp_float
    mpm_module.torch2warp_vec3 = torch2warp_vec3
    mpm_module.torch2warp_mat33 = torch2warp_mat33
    MPM_Simulator_WARP = mpm_module.MPM_Simulator_WARP

    args.output_dir.mkdir(parents=True, exist_ok=True)
    wp.config.kernel_cache_dir = str(args.output_dir / "warp_kernel_cache")
    wp.config.verify_cuda = args.device.startswith("cuda")
    wp.init()

    n_grid = int(args.n_grid if args.n_grid is not None else config.get("n_grid", 200))
    grid_lim = float(args.grid_lim if args.grid_lim is not None else config.get("grid_lim", 2.0))
    dt = float(args.dt if args.dt is not None else config.get("substep_dt", 2e-5))
    steps = int(args.steps)
    if args.duration is not None:
        steps = int(np.ceil(args.duration / dt))
        print(f"duration: {args.duration}")
        print(f"dt: {dt}")
        print(f"steps = ceil(duration / dt): {steps}")
    dx = grid_lim / n_grid
    volume = torch.full((points.shape[0],), dx**3, dtype=torch.float32, device=args.device)
    position = torch.from_numpy(points).to(device=args.device)

    solver = MPM_Simulator_WARP(points.shape[0], device=args.device)
    solver.load_initial_data_from_torch(
        position,
        volume,
        n_grid=n_grid,
        grid_lim=grid_lim,
        device=args.device,
    )
    solver.set_parameters_dict(config, device=args.device)
    solver.finalize_mu_lam(device=args.device)
    plane = metadata["ground_plane_mpm"]
    solver.add_surface_collider(
        point=plane["point"],
        normal=plane["normal"],
        surface=plane["surface"],
        friction=plane["friction"],
    )

    sim_dir = args.output_dir / "simulation_ply"
    save_data_at_frame(solver, str(sim_dir), 0, save_to_ply=True, save_to_h5=False)
    for step in range(1, steps + 1):
        solver.p2g2p(step, dt, device=args.device)
        save_data_at_frame(solver, str(sim_dir), step, save_to_ply=True, save_to_h5=False)


def main() -> None:
    args = parse_args()
    config = load_material_config(args.config)
    particles, metadata = build_particles(args, config)

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

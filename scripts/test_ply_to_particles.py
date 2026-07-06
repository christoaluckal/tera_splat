#!/usr/bin/env python3
"""Convert an EDGS/3DGS PLY into MPM particles and validate the particle set."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from particle_io import (
    build_particles,
    load_material_config,
    read_particle_ply,
    write_metadata,
    write_particle_ply,
)
from view_iteration_7000 import DEFAULT_PLY


DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "configs" / "physgaussian_sand.json"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "outputs" / "ply_particle_test"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ply", type=Path, default=DEFAULT_PLY)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--opacity-threshold", type=float, default=0.02)
    parser.add_argument("--axis-transform", default="opencv-to-zup")
    parser.add_argument("--max-particles", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=1)
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_material_config(args.config)
    particles, metadata = build_particles(args, config)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    particle_path = args.output_dir / "particles_initial_mpm.ply"
    metadata_path = args.output_dir / "ground_plane_metadata.json"
    write_particle_ply(particles, particle_path)
    write_metadata(metadata, metadata_path)

    reloaded = read_particle_ply(particle_path)
    if reloaded.shape != particles.shape:
        raise SystemExit(f"round-trip shape mismatch: wrote {particles.shape}, read {reloaded.shape}")
    max_abs_error = float(np.max(np.abs(reloaded - particles))) if particles.size else 0.0
    if max_abs_error > 1e-6:
        raise SystemExit(f"round-trip coordinate error too large: {max_abs_error}")
    if not np.isfinite(particles).all():
        raise SystemExit("particle array contains NaN or inf")

    bounds_min = particles.min(axis=0)
    bounds_max = particles.max(axis=0)
    ground_z = metadata["ground_plane_mpm"]["point"][2]
    below_ground = int(np.count_nonzero(particles[:, 2] < ground_z - 1e-5))

    print(f"particles: {particles.shape[0]}")
    print(f"bounds min: {bounds_min.tolist()}")
    print(f"bounds max: {bounds_max.tolist()}")
    print(f"ground z: {ground_z}")
    print(f"particles below ground tolerance: {below_ground}")
    print(f"round-trip max abs error: {max_abs_error}")
    print(f"particle ply: {particle_path}")
    print(f"metadata: {metadata_path}")


if __name__ == "__main__":
    main()

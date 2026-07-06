#!/usr/bin/env python3
"""Viser still viewer for one particle PLY."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import viser

from particle_io import read_particle_ply
from view_solver_animation import colors_from_height


DEFAULT_PLY = (
    Path(__file__).resolve().parents[1]
    / "outputs"
    / "genesis_cuda_10pct_2s_dt0005_min_ground"
    / "simulation_ply"
    / "sim_0000.ply"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ply", nargs="?", type=Path, default=DEFAULT_PLY)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8082)
    parser.add_argument("--point-size", type=float, default=0.003)
    parser.add_argument("--sample-fraction", type=float, default=1.0)
    parser.add_argument("--max-points", type=int, default=0)
    parser.add_argument("--seed", type=int, default=0)
    return parser.parse_args()


def select_points(points: np.ndarray, sample_fraction: float, max_points: int, seed: int) -> np.ndarray:
    if not (0.0 < sample_fraction <= 1.0):
        raise ValueError("--sample-fraction must be in (0, 1]")

    target_points = points.shape[0]
    if sample_fraction < 1.0:
        target_points = min(target_points, max(int(np.ceil(points.shape[0] * sample_fraction)), 1))
    if max_points > 0:
        target_points = min(target_points, max_points)
    if target_points >= points.shape[0]:
        return points

    rng = np.random.default_rng(seed)
    selected = np.sort(rng.choice(points.shape[0], size=target_points, replace=False))
    return points[selected]


def main() -> None:
    args = parse_args()
    points = read_particle_ply(args.ply)
    points = select_points(points, args.sample_fraction, args.max_points, args.seed)

    bounds_min = points.min(axis=0)
    bounds_max = points.max(axis=0)
    center = (bounds_min + bounds_max) / 2.0
    span = float(np.max(bounds_max - bounds_min))
    colors = colors_from_height(points, float(bounds_min[2]), float(bounds_max[2]))

    print(f"ply: {args.ply}")
    print(f"points: {points.shape[0]}")
    print(f"bounds min: {bounds_min.tolist()}")
    print(f"bounds max: {bounds_max.tolist()}")

    server = viser.ViserServer(host=args.host, port=args.port)
    server.scene.world_axes.visible = True
    server.scene.add_grid(
        "/ground_grid",
        width=span,
        height=span,
        plane="xy",
        position=(float(center[0]), float(center[1]), float(bounds_min[2])),
    )
    server.scene.add_point_cloud(
        "/particles",
        points=points,
        colors=colors,
        point_size=args.point_size,
        point_shape="circle",
    )
    print(f"Open http://localhost:{args.port}")

    while True:
        time.sleep(1.0)


if __name__ == "__main__":
    main()

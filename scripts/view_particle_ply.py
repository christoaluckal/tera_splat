#!/usr/bin/env python3
"""Still viewer for one particle PLY."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

from particle_io import read_particle_ply
from view_iteration_7000 import AXIS_TRANSFORMS, DEFAULT_PLY as DEFAULT_SPLAT_PLY, load_3dgs_ply
from view_solver_animation import colors_from_height


DEFAULT_PARTICLE_PLY = (
    Path(__file__).resolve().parents[1]
    / "outputs"
    / "genesis_cuda_10pct_2s_dt0005_min_ground"
    / "simulation_ply"
    / "sim_0000.ply"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ply", nargs="?", type=Path, default=None)
    parser.add_argument(
        "--source",
        choices=("particle", "splat"),
        default="splat",
        help="Read generated particle PLYs or original 3DGS splat PLY centers.",
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8082)
    parser.add_argument("--point-size", type=float, default=0.003)
    parser.add_argument("--sample-fraction", type=float, default=1.0)
    parser.add_argument("--max-points", type=int, default=0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--z-min", type=float, default=None, help="Keep only points with z >= this value.")
    parser.add_argument("--z-max", type=float, default=None, help="Keep only points with z <= this value.")
    parser.add_argument("--open3d", action="store_true", help="Open the filtered point cloud in an Open3D window.")
    parser.add_argument("--dry-run", action="store_true", help="Print filtered bounds/counts without opening a viewer.")
    parser.add_argument("--opacity-threshold", type=float, default=0.02)
    parser.add_argument(
        "--max-gaussians",
        type=int,
        default=300_000,
        help="Maximum splat centers to load when --source splat. Use 0 for all retained splats.",
    )
    parser.add_argument(
        "--axis-transform",
        choices=tuple(AXIS_TRANSFORMS.keys()),
        default="opencv-to-zup",
        help="Axis conversion for --source splat.",
    )
    parser.add_argument(
        "--align-ground-z",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="For --source splat, fit the dominant plane and rotate its normal onto +Z.",
    )
    return parser.parse_args()


def z_filter_mask(points: np.ndarray, z_min: float | None, z_max: float | None) -> np.ndarray:
    keep = np.ones(points.shape[0], dtype=bool)
    if z_min is not None:
        keep &= points[:, 2] >= z_min
    if z_max is not None:
        keep &= points[:, 2] <= z_max
    return keep


def select_indices(count: int, sample_fraction: float, max_points: int, seed: int) -> np.ndarray:
    if not (0.0 < sample_fraction <= 1.0):
        raise ValueError("--sample-fraction must be in (0, 1]")

    target_points = count
    if sample_fraction < 1.0:
        target_points = min(target_points, max(int(np.ceil(count * sample_fraction)), 1))
    if max_points > 0:
        target_points = min(target_points, max_points)
    if target_points >= count:
        return np.arange(count)

    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(count, size=target_points, replace=False))


def select_points(points: np.ndarray, sample_fraction: float, max_points: int, seed: int) -> np.ndarray:
    return points[select_indices(points.shape[0], sample_fraction, max_points, seed)]


def load_points(args: argparse.Namespace) -> tuple[Path, np.ndarray, np.ndarray | None]:
    if args.ply is None:
        ply = DEFAULT_SPLAT_PLY if args.source == "splat" else DEFAULT_PARTICLE_PLY
    else:
        ply = args.ply

    if args.source == "splat":
        data = load_3dgs_ply(
            ply,
            opacity_threshold=args.opacity_threshold,
            max_gaussians=args.max_gaussians,
            seed=args.seed,
            scale_multiplier=1.0,
            axis_transform=args.axis_transform,
            align_ground_z=args.align_ground_z,
        )
        colors = (data.colors * 255.0).clip(0.0, 255.0).astype(np.uint8)
        return ply, data.centers, colors

    return ply, read_particle_ply(ply), None


def print_stats(ply: Path, source: str, points: np.ndarray, original_count: int) -> tuple[np.ndarray, np.ndarray]:
    if points.shape[0] == 0:
        raise ValueError("No points remain after filtering")
    bounds_min = points.min(axis=0)
    bounds_max = points.max(axis=0)
    print(f"ply: {ply}")
    print(f"source: {source}")
    print(f"points: {points.shape[0]} / {original_count}")
    print(f"bounds min: {bounds_min.tolist()}")
    print(f"bounds max: {bounds_max.tolist()}")
    return bounds_min, bounds_max


def view_open3d(points: np.ndarray, colors: np.ndarray, title: str) -> None:
    import open3d as o3d

    point_cloud = o3d.geometry.PointCloud()
    point_cloud.points = o3d.utility.Vector3dVector(points.astype(np.float64))
    point_cloud.colors = o3d.utility.Vector3dVector((colors.astype(np.float64) / 255.0).clip(0.0, 1.0))

    frame = o3d.geometry.TriangleMesh.create_coordinate_frame(
        size=max(float(np.max(points.max(axis=0) - points.min(axis=0))) * 0.15, 0.05),
        origin=points.mean(axis=0).astype(np.float64),
    )
    o3d.visualization.draw_geometries(
        [point_cloud, frame],
        window_name=title,
        width=1280,
        height=800,
    )


def view_viser(
    points: np.ndarray,
    colors: np.ndarray,
    bounds_min: np.ndarray,
    bounds_max: np.ndarray,
    host: str,
    port: int,
    point_size: float,
) -> None:
    import viser

    center = (bounds_min + bounds_max) / 2.0
    span = float(np.max(bounds_max - bounds_min))
    server = viser.ViserServer(host=host, port=port)
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
        point_size=point_size,
        point_shape="circle",
    )
    print(f"Open http://localhost:{port}")

    while True:
        time.sleep(1.0)


def main() -> None:
    args = parse_args()
    ply, points, loaded_colors = load_points(args)
    original_count = points.shape[0]
    keep = z_filter_mask(points, args.z_min, args.z_max)
    points = points[keep]
    if loaded_colors is not None:
        loaded_colors = loaded_colors[keep]
    selected = select_indices(points.shape[0], args.sample_fraction, args.max_points, args.seed)
    points = points[selected]
    if loaded_colors is not None:
        loaded_colors = loaded_colors[selected]

    bounds_min, bounds_max = print_stats(ply, args.source, points, original_count)
    if loaded_colors is None:
        colors = colors_from_height(points, float(bounds_min[2]), float(bounds_max[2]))
    else:
        colors = loaded_colors

    if args.dry_run:
        return
    if args.open3d:
        view_open3d(points, colors, ply.name)
    else:
        view_viser(points, colors, bounds_min, bounds_max, args.host, args.port, args.point_size)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Create a subsurface PLY from a manually selected splat Z band."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from plyfile import PlyData, PlyElement

from view_iteration_7000 import AXIS_TRANSFORMS, DEFAULT_PLY, load_3dgs_ply


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ply", type=Path, default=DEFAULT_PLY)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/splat_surface_subsurface_zband"))
    parser.add_argument("--z-min", type=float, required=True, help="Keep splat centers with z >= this value.")
    parser.add_argument("--z-max", type=float, required=True, help="Keep splat centers with z <= this value.")
    parser.add_argument(
        "--box-size",
        type=float,
        default=0.0,
        help="Optional centered square XY crop size in aligned source units. Use 1.0 for a 1x1m box.",
    )
    parser.add_argument("--depth", type=float, default=0.2, help="Maximum subsurface depth below the estimated surface.")
    parser.add_argument("--xy-spacing", type=float, default=0.025, help="Regular grid spacing in source/aligned units.")
    parser.add_argument("--layer-spacing", type=float, default=0.025, help="Equal depth spacing between subsurface grids.")
    parser.add_argument(
        "--xy-jitter",
        type=float,
        default=0.45,
        help="Random XY jitter as a fraction of --xy-spacing.",
    )
    parser.add_argument(
        "--noise-scalar",
        type=float,
        default=1.0,
        help="Additional multiplier for XY layer shift and random XY jitter.",
    )
    parser.add_argument(
        "--max-surface-distance",
        type=float,
        default=0.05,
        help="Discard grid points farther than this XY distance from the selected splat surface.",
    )
    parser.add_argument(
        "--surface-neighbors",
        type=int,
        default=32,
        help="Neighbor count used to estimate local surface height for each grid point.",
    )
    parser.add_argument(
        "--surface-quantile",
        type=float,
        default=0.9,
        help="Local neighbor Z quantile used as the surface height estimate.",
    )
    parser.add_argument("--opacity-threshold", type=float, default=0.02)
    parser.add_argument("--max-gaussians", type=int, default=300_000, help="Use 0 for all retained splats.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--axis-transform",
        choices=tuple(AXIS_TRANSFORMS.keys()),
        default="opencv-to-zup",
    )
    parser.add_argument(
        "--align-ground-z",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Fit dominant plane and rotate its normal onto +Z before filtering.",
    )
    return parser.parse_args()


def write_colored_ply(points: np.ndarray, colors: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    colors_u8 = (colors * 255.0).clip(0.0, 255.0).astype(np.uint8)
    vertex = np.empty(
        points.shape[0],
        dtype=[
            ("x", "f4"),
            ("y", "f4"),
            ("z", "f4"),
            ("red", "u1"),
            ("green", "u1"),
            ("blue", "u1"),
        ],
    )
    vertex["x"] = points[:, 0].astype(np.float32)
    vertex["y"] = points[:, 1].astype(np.float32)
    vertex["z"] = points[:, 2].astype(np.float32)
    vertex["red"] = colors_u8[:, 0]
    vertex["green"] = colors_u8[:, 1]
    vertex["blue"] = colors_u8[:, 2]
    PlyData([PlyElement.describe(vertex, "vertex")], text=False).write(path)


def build_regular_grid_subsurface(
    surface: np.ndarray,
    surface_colors: np.ndarray,
    *,
    depth: float,
    xy_spacing: float,
    layer_spacing: float,
    xy_jitter_fraction: float,
    noise_scalar: float,
    max_surface_distance: float,
    surface_neighbors: int,
    surface_quantile: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, dict]:
    from scipy.spatial import cKDTree

    if xy_spacing <= 0.0:
        raise ValueError("--xy-spacing must be positive")
    if layer_spacing <= 0.0:
        raise ValueError("--layer-spacing must be positive")
    if not (0.0 <= surface_quantile <= 1.0):
        raise ValueError("--surface-quantile must be in [0, 1]")

    rng = np.random.default_rng(seed)
    xy_min = surface[:, :2].min(axis=0)
    xy_max = surface[:, :2].max(axis=0)
    xs = np.arange(xy_min[0], xy_max[0] + xy_spacing * 0.5, xy_spacing, dtype=np.float32)
    ys = np.arange(xy_min[1], xy_max[1] + xy_spacing * 0.5, xy_spacing, dtype=np.float32)
    grid_x, grid_y = np.meshgrid(xs, ys, indexing="xy")
    grid_xy = np.stack([grid_x.ravel(), grid_y.ravel()], axis=1).astype(np.float32)

    tree = cKDTree(surface[:, :2])
    nearest_distance, nearest = tree.query(grid_xy, k=1)
    if max_surface_distance > 0.0:
        keep = nearest_distance <= max_surface_distance
        grid_xy = grid_xy[keep]
        nearest = nearest[keep]
        nearest_distance = nearest_distance[keep]
    if grid_xy.shape[0] == 0:
        raise ValueError("No grid points remain after --max-surface-distance filtering")

    k = min(max(surface_neighbors, 1), surface.shape[0])
    _, neighbor_indices = tree.query(grid_xy, k=k)
    if k == 1:
        neighbor_indices = neighbor_indices[:, None]
    surface_z = np.quantile(surface[neighbor_indices, 2], surface_quantile, axis=1).astype(np.float32)

    layer_depths = np.arange(layer_spacing, depth + layer_spacing * 0.5, layer_spacing, dtype=np.float32)
    layer_depths = layer_depths[layer_depths <= depth + 1e-6]
    if layer_depths.size == 0:
        raise ValueError("No subsurface layers generated; check --depth and --layer-spacing")

    noise_scalar = max(noise_scalar, 0.0)
    jitter = max(xy_spacing * xy_jitter_fraction * noise_scalar, 0.0)
    layers: list[np.ndarray] = []
    layer_colors: list[np.ndarray] = []
    for layer_index, layer_depth in enumerate(layer_depths):
        layer_xy = grid_xy.copy()
        layer_shift = rng.uniform(
            -xy_spacing * 0.5 * noise_scalar,
            xy_spacing * 0.5 * noise_scalar,
            size=(1, 2),
        ).astype(np.float32)
        layer_xy += layer_shift
        if jitter > 0.0:
            layer_xy += rng.uniform(-jitter, jitter, size=layer_xy.shape).astype(np.float32)

        if max_surface_distance > 0.0:
            layer_nearest_distance, layer_nearest = tree.query(layer_xy, k=1)
            layer_keep = layer_nearest_distance <= max_surface_distance
            layer_xy = layer_xy[layer_keep]
            layer_surface_z = surface_z[layer_keep]
            layer_color_indices = layer_nearest[layer_keep]
        else:
            _, layer_nearest = tree.query(layer_xy, k=1)
            layer_surface_z = surface_z
            layer_color_indices = layer_nearest

        layer = np.empty((layer_xy.shape[0], 3), dtype=np.float32)
        layer[:, :2] = layer_xy
        layer[:, 2] = layer_surface_z - float(layer_depth)
        layers.append(layer)
        layer_colors.append(surface_colors[layer_color_indices])

    subsurface = np.concatenate(layers, axis=0)
    subsurface_colors = np.concatenate(layer_colors, axis=0)
    metadata = {
        "subsurface_strategy": "regular_xy_grids_equal_depth_layers",
        "xy_spacing": float(xy_spacing),
        "layer_spacing": float(layer_spacing),
        "layer_depths": layer_depths.astype(float).tolist(),
        "layer_count": int(layer_depths.shape[0]),
        "xy_jitter_fraction": float(xy_jitter_fraction),
        "noise_scalar": float(noise_scalar),
        "xy_jitter": float(jitter),
        "max_surface_distance": float(max_surface_distance),
        "surface_neighbors": int(k),
        "surface_quantile": float(surface_quantile),
        "grid_xy_count": int(grid_xy.shape[0]),
        "nearest_distance_min": float(nearest_distance.min()) if nearest_distance.size else 0.0,
        "nearest_distance_max": float(nearest_distance.max()) if nearest_distance.size else 0.0,
        "nearest_distance_mean": float(nearest_distance.mean()) if nearest_distance.size else 0.0,
        "estimated_surface_z_min": float(surface_z.min()),
        "estimated_surface_z_max": float(surface_z.max()),
    }
    return subsurface, subsurface_colors, metadata


def main() -> None:
    args = parse_args()
    if args.z_min > args.z_max:
        raise ValueError("--z-min must be <= --z-max")
    if args.depth <= 0.0:
        raise ValueError("--depth must be positive")

    data = load_3dgs_ply(
        args.ply,
        opacity_threshold=args.opacity_threshold,
        max_gaussians=args.max_gaussians,
        seed=args.seed,
        scale_multiplier=1.0,
        axis_transform=args.axis_transform,
        align_ground_z=args.align_ground_z,
    )
    keep = (data.centers[:, 2] >= args.z_min) & (data.centers[:, 2] <= args.z_max)
    box_center_xy = None
    if args.box_size > 0.0:
        zband_centers = data.centers[keep]
        if zband_centers.shape[0] == 0:
            raise ValueError("No splat centers remain after Z filtering")
        box_center_xy = zband_centers[:, :2].mean(axis=0)
        half_box = args.box_size * 0.5
        keep &= np.all(np.abs(data.centers[:, :2] - box_center_xy) <= half_box, axis=1)
    surface = data.centers[keep]
    surface_colors = data.colors[keep]
    if surface.shape[0] == 0:
        raise ValueError("No splat centers remain after Z filtering")

    subsurface, subsurface_colors, subsurface_metadata = build_regular_grid_subsurface(
        surface,
        surface_colors,
        depth=args.depth,
        xy_spacing=args.xy_spacing,
        layer_spacing=args.layer_spacing,
        xy_jitter_fraction=args.xy_jitter,
        noise_scalar=args.noise_scalar,
        max_surface_distance=args.max_surface_distance,
        surface_neighbors=args.surface_neighbors,
        surface_quantile=args.surface_quantile,
        seed=args.seed,
    )

    combined = np.concatenate([surface, subsurface], axis=0)
    combined_colors = np.concatenate([surface_colors, subsurface_colors], axis=0)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    surface_path = args.output_dir / "splat_surface_zband.ply"
    subsurface_path = args.output_dir / "regular_grid_subsurface.ply"
    combined_path = args.output_dir / "splat_surface_plus_regular_grid_subsurface.ply"
    metadata_path = args.output_dir / "metadata.json"

    write_colored_ply(surface, surface_colors, surface_path)
    write_colored_ply(subsurface, subsurface_colors, subsurface_path)
    write_colored_ply(combined, combined_colors, combined_path)

    metadata = {
        "source_ply": str(args.ply),
        "axis_transform": args.axis_transform,
        "align_ground_z": args.align_ground_z,
        "opacity_threshold": args.opacity_threshold,
        "max_gaussians": args.max_gaussians,
        "z_min": args.z_min,
        "z_max": args.z_max,
        "box_size": args.box_size,
        "box_center_xy": box_center_xy.tolist() if box_center_xy is not None else None,
        "depth": args.depth,
        "xy_spacing": args.xy_spacing,
        "layer_spacing": args.layer_spacing,
        "noise_scalar": args.noise_scalar,
        "input_splat_count": int(data.centers.shape[0]),
        "surface_count": int(surface.shape[0]),
        "subsurface_count": int(subsurface.shape[0]),
        "surface_bounds_min": surface.min(axis=0).tolist(),
        "surface_bounds_max": surface.max(axis=0).tolist(),
        "subsurface_bounds_min": subsurface.min(axis=0).tolist(),
        "subsurface_bounds_max": subsurface.max(axis=0).tolist(),
        "surface_ply": str(surface_path),
        "subsurface_ply": str(subsurface_path),
        "combined_ply": str(combined_path),
        "subsurface_generation": subsurface_metadata,
    }
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"surface points: {surface.shape[0]}")
    print(f"subsurface points: {subsurface.shape[0]}")
    print(f"surface: {surface_path}")
    print(f"subsurface: {subsurface_path}")
    print(f"combined: {combined_path}")
    print(f"metadata: {metadata_path}")


if __name__ == "__main__":
    main()

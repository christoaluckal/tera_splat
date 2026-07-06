"""Shared particle extraction and PLY I/O for terrain MPM tests."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import numpy as np

from view_iteration_7000 import load_3dgs_ply


def load_material_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_to_mpm_domain(
    points: np.ndarray,
    *,
    grid_lim: float,
    padding: float,
) -> tuple[np.ndarray, dict]:
    bounds_min = points.min(axis=0)
    bounds_max = points.max(axis=0)
    center = (bounds_min + bounds_max) / 2.0
    span = float(np.max(bounds_max - bounds_min))
    usable = grid_lim * (1.0 - 2.0 * padding)
    scale = usable / span
    offset = np.array([grid_lim * 0.5, grid_lim * 0.5, grid_lim * padding], dtype=np.float32)
    normalized = (points - center) * scale + offset
    normalized[:, 2] -= normalized[:, 2].min() - grid_lim * padding
    metadata = {
        "source_bounds_min": bounds_min.tolist(),
        "source_bounds_max": bounds_max.tolist(),
        "source_center": center.tolist(),
        "source_span": span,
        "grid_lim": grid_lim,
        "padding": padding,
        "scale_to_mpm": scale,
        "offset_after_centering": offset.tolist(),
    }
    return normalized.astype(np.float32), metadata


def build_particles(args: Namespace, config: dict) -> tuple[np.ndarray, dict]:
    grid_lim = float(args.grid_lim if args.grid_lim is not None else config.get("grid_lim", 2.0))
    ground_quantile = float(getattr(args, "ground_quantile", 0.0))
    trim_quantile = float(getattr(args, "trim_quantile", 0.0))
    data = load_3dgs_ply(
        args.ply,
        opacity_threshold=args.opacity_threshold,
        max_gaussians=args.max_particles,
        seed=args.seed,
        scale_multiplier=1.0,
        axis_transform=args.axis_transform,
        align_ground_z=True,
    )
    centers = data.centers
    trim_metadata = None
    if trim_quantile > 0.0:
        if trim_quantile >= 0.5:
            raise ValueError("--trim-quantile must be less than 0.5")
        low = np.quantile(centers, trim_quantile, axis=0)
        high = np.quantile(centers, 1.0 - trim_quantile, axis=0)
        keep = np.all((centers >= low) & (centers <= high), axis=1)
        trim_metadata = {
            "trim_quantile": trim_quantile,
            "bounds_min": low.tolist(),
            "bounds_max": high.tolist(),
            "input_count": int(centers.shape[0]),
            "kept_count": int(np.count_nonzero(keep)),
            "removed_count": int(centers.shape[0] - np.count_nonzero(keep)),
        }
        centers = centers[keep]

    points, transform_metadata = normalize_to_mpm_domain(
        centers,
        grid_lim=grid_lim,
        padding=args.padding,
    )
    ground_z = float(np.quantile(points[:, 2], ground_quantile))
    metadata = {
        "ply": str(args.ply),
        "particle_count": int(points.shape[0]),
        "axis_transform": args.axis_transform,
        "align_ground_z": True,
        "ground_normal_before_alignment": None
        if data.ground_normal is None
        else data.ground_normal.tolist(),
        "ground_alignment_matrix": None
        if data.ground_alignment is None
        else data.ground_alignment.tolist(),
        "outlier_trim": trim_metadata,
        "mpm_transform": transform_metadata,
        "ground_plane_mpm": {
            "point": [0.0, 0.0, ground_z],
            "normal": [0.0, 0.0, 1.0],
            "surface": "sticky",
            "friction": 0.0,
            "height_quantile": ground_quantile,
        },
    }
    return points, metadata


def write_particle_ply(points: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        header = f"""ply
format binary_little_endian 1.0
element vertex {points.shape[0]}
property float x
property float y
property float z
end_header
"""
        f.write(header.encode("ascii"))
        f.write(points.astype(np.float32).tobytes())


def read_particle_ply(path: Path) -> np.ndarray:
    from plyfile import PlyData

    vertex = PlyData.read(path)["vertex"].data
    return np.stack([vertex["x"], vertex["y"], vertex["z"]], axis=1).astype(np.float32)


def write_metadata(metadata: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

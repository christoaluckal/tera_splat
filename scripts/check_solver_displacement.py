#!/usr/bin/env python3
"""Report displacement statistics for solver PLY frames."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from plyfile import PlyData


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_folder", type=Path)
    return parser.parse_args()


def simulation_dir(output_folder: Path) -> Path:
    if output_folder.name == "simulation_ply":
        return output_folder
    candidate = output_folder / "simulation_ply"
    return candidate if candidate.exists() else output_folder


def read_xyz_ply(path: Path) -> np.ndarray:
    vertex = PlyData.read(path)["vertex"].data
    return np.stack([vertex["x"], vertex["y"], vertex["z"]], axis=1).astype(np.float64)


def frame_number(path: Path) -> int:
    return int(path.stem.split("_")[-1])


def main() -> None:
    args = parse_args()
    frame_paths = sorted(simulation_dir(args.output_folder).glob("sim_*.ply"), key=frame_number)
    if len(frame_paths) < 2:
        raise FileNotFoundError("Need at least two sim_*.ply frames")

    first = read_xyz_ply(frame_paths[0])
    last = read_xyz_ply(frame_paths[-1])
    if first.shape != last.shape:
        raise ValueError(f"Frame shape mismatch: {first.shape} vs {last.shape}")

    displacement = last - first
    norms = np.linalg.norm(displacement, axis=1)
    print(f"folder: {args.output_folder}")
    print(f"frames: {len(frame_paths)}")
    print(f"particles: {first.shape[0]}")
    print(f"first: {frame_paths[0].name}")
    print(f"last: {frame_paths[-1].name}")
    print(f"max_displacement: {float(norms.max())}")
    print(f"mean_displacement: {float(norms.mean())}")
    print(f"median_displacement: {float(np.median(norms))}")
    print(f"z_delta_min: {float(displacement[:, 2].min())}")
    print(f"z_delta_max: {float(displacement[:, 2].max())}")
    print(f"z_delta_mean: {float(displacement[:, 2].mean())}")
    print(f"first_bounds_min: {first.min(axis=0).tolist()}")
    print(f"first_bounds_max: {first.max(axis=0).tolist()}")
    print(f"last_bounds_min: {last.min(axis=0).tolist()}")
    print(f"last_bounds_max: {last.max(axis=0).tolist()}")


if __name__ == "__main__":
    main()

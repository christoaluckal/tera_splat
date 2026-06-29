#!/usr/bin/env python3
"""Resample sparse solver PLY frames into a denser playback sequence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from plyfile import PlyData


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_folder", type=Path)
    parser.add_argument("output_folder", type=Path)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--dt", type=float, required=True)
    return parser.parse_args()


def simulation_dir(folder: Path) -> Path:
    if folder.name == "simulation_ply":
        return folder
    candidate = folder / "simulation_ply"
    return candidate if candidate.exists() else folder


def read_xyz_ply(path: Path) -> np.ndarray:
    vertex = PlyData.read(path)["vertex"].data
    return np.stack([vertex["x"], vertex["y"], vertex["z"]], axis=1).astype(np.float32)


def write_xyz_ply(points: np.ndarray, path: Path) -> None:
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


def copy_metadata(input_folder: Path, output_folder: Path, frame_count: int, args: argparse.Namespace) -> None:
    metadata_path = input_folder / "ground_plane_metadata.json"
    if not metadata_path.exists() and input_folder.name == "simulation_ply":
        metadata_path = input_folder.parent / "ground_plane_metadata.json"
    if not metadata_path.exists():
        return

    with metadata_path.open("r", encoding="utf-8") as f:
        metadata = json.load(f)
    metadata["resampled_playback"] = {
        "source": str(input_folder),
        "duration": args.duration,
        "dt": args.dt,
        "frame_count": frame_count,
    }
    output_folder.mkdir(parents=True, exist_ok=True)
    with (output_folder / "ground_plane_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


def main() -> None:
    args = parse_args()
    if args.duration <= 0.0:
        raise ValueError("--duration must be positive")
    if args.dt <= 0.0:
        raise ValueError("--dt must be positive")

    frame_paths = sorted(simulation_dir(args.input_folder).glob("sim_*.ply"))
    if len(frame_paths) < 2:
        raise FileNotFoundError("Need at least two sim_*.ply frames to resample")

    source_frames = [read_xyz_ply(path) for path in frame_paths]
    source_count = len(source_frames)
    particle_count = source_frames[0].shape[0]
    if any(frame.shape != source_frames[0].shape for frame in source_frames):
        raise ValueError("All source frames must have the same particle shape")

    frame_count = int(np.ceil(args.duration / args.dt))
    output_sim_dir = args.output_folder / "simulation_ply"
    output_sim_dir.mkdir(parents=True, exist_ok=True)

    source_positions = np.linspace(0.0, source_count - 1, frame_count)
    for out_idx, source_pos in enumerate(source_positions):
        low = int(np.floor(source_pos))
        high = min(low + 1, source_count - 1)
        alpha = np.float32(source_pos - low)
        points = (1.0 - alpha) * source_frames[low] + alpha * source_frames[high]
        write_xyz_ply(points, output_sim_dir / f"sim_{out_idx:010d}.ply")

    copy_metadata(args.input_folder, args.output_folder, frame_count, args)
    print(f"source_frames: {source_count}")
    print(f"particles/frame: {particle_count}")
    print(f"duration: {args.duration}")
    print(f"dt: {args.dt}")
    print(f"frame_count = ceil(duration / dt): {frame_count}")
    print(f"output: {args.output_folder}")


if __name__ == "__main__":
    main()

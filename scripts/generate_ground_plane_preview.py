#!/usr/bin/env python3
"""Generate a kinematic gravity preview against the extracted ground plane.

This is a visualization/debug fallback, not an MPM solve. It starts from
`particles_initial_mpm.ply`, applies z(t) = z0 + 0.5 g t^2, and clamps particles
to the ground plane height from `ground_plane_metadata.json`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from plyfile import PlyData


DEFAULT_INPUT = Path(__file__).resolve().parents[1] / "outputs" / "ground_plane_solver_cpu_smoke2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_folder", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("output_folder", nargs="?", type=Path, default=None)
    parser.add_argument("--duration", type=float, default=2.0)
    parser.add_argument("--dt", type=float, default=0.02)
    parser.add_argument("--gravity", type=float, default=-9.8)
    return parser.parse_args()


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


def load_metadata(input_folder: Path) -> dict:
    path = input_folder / "ground_plane_metadata.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    args = parse_args()
    if args.duration <= 0.0:
        raise ValueError("--duration must be positive")
    if args.dt <= 0.0:
        raise ValueError("--dt must be positive")

    input_folder = args.input_folder
    output_folder = args.output_folder
    if output_folder is None:
        output_folder = input_folder.parent / f"{input_folder.name}_gravity_preview_2s"

    initial = read_xyz_ply(input_folder / "particles_initial_mpm.ply")
    metadata = load_metadata(input_folder)
    ground_z = float(metadata["ground_plane_mpm"]["point"][2])

    frame_count = int(np.ceil(args.duration / args.dt))
    initial = initial.copy()
    initial[:, 2] = np.maximum(initial[:, 2], ground_z)

    sim_dir = output_folder / "simulation_ply"
    for frame in range(frame_count):
        t = frame * args.dt
        points = initial.copy()
        points[:, 2] = np.maximum(points[:, 2] + 0.5 * args.gravity * t * t, ground_z)
        write_xyz_ply(points, sim_dir / f"sim_{frame:010d}.ply")

    metadata["kinematic_preview"] = {
        "source": str(input_folder),
        "duration": args.duration,
        "dt": args.dt,
        "frame_count": frame_count,
        "gravity": args.gravity,
        "ground_z": ground_z,
        "not_mpm": True,
    }
    output_folder.mkdir(parents=True, exist_ok=True)
    with (output_folder / "ground_plane_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"particles/frame: {initial.shape[0]}")
    print(f"duration: {args.duration}")
    print(f"dt: {args.dt}")
    print(f"frame_count = ceil(duration / dt): {frame_count}")
    print(f"ground_z: {ground_z}")
    print(f"output: {output_folder}")


if __name__ == "__main__":
    main()

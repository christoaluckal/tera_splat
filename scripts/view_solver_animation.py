#!/usr/bin/env python3
"""Viser playback for PhysGaussian solver particle PLY outputs.

The solver smoke test currently writes particle positions only, so this viewer
renders the frames as point splats and animates them. Pass either the solver
output folder or its `simulation_ply` subfolder.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import viser
from plyfile import PlyData


DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "outputs"
    / "ground_plane_solver_cpu_smoke"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_folder", nargs="?", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--fps", type=float, default=6.0)
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Playback duration in seconds for one full loop. Overrides --fps.",
    )
    parser.add_argument("--point-size", type=float, default=0.01)
    parser.add_argument(
        "--sample-fraction",
        type=float,
        default=1.0,
        help="Representative fixed particle fraction to display from each frame.",
    )
    parser.add_argument(
        "--max-points",
        type=int,
        default=0,
        help="Maximum particles per frame. Use 0 to display all particles.",
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load frames and print stats without starting Viser.",
    )
    return parser.parse_args()


def resolve_simulation_dir(output_folder: Path) -> Path:
    if output_folder.name == "simulation_ply":
        return output_folder
    simulation_dir = output_folder / "simulation_ply"
    if simulation_dir.exists():
        return simulation_dir
    return output_folder


def find_frame_paths(output_folder: Path) -> list[Path]:
    simulation_dir = resolve_simulation_dir(output_folder)
    paths = sorted(simulation_dir.glob("sim_*.ply"), key=frame_number)
    if not paths:
        raise FileNotFoundError(f"No sim_*.ply frames found under {simulation_dir}")
    return paths


def frame_number(path: Path) -> int:
    return int(path.stem.split("_")[-1])


def read_xyz_ply(path: Path) -> np.ndarray:
    vertex = PlyData.read(path)["vertex"].data
    return np.stack([vertex["x"], vertex["y"], vertex["z"]], axis=1).astype(np.float32)


def load_frames(
    paths: list[Path],
    max_points: int,
    sample_fraction: float,
    seed: int,
) -> list[np.ndarray]:
    first = read_xyz_ply(paths[0])
    if not (0.0 < sample_fraction <= 1.0):
        raise ValueError("--sample-fraction must be in (0, 1]")

    fraction_points = int(np.ceil(first.shape[0] * sample_fraction))
    target_points = first.shape[0]
    if sample_fraction < 1.0:
        target_points = min(target_points, max(fraction_points, 1))
    if max_points > 0:
        target_points = min(target_points, max_points)

    if target_points < first.shape[0]:
        rng = np.random.default_rng(seed)
        selected = np.sort(rng.choice(first.shape[0], size=target_points, replace=False))
    else:
        selected = None

    frames = []
    for path in paths:
        points = read_xyz_ply(path)
        if selected is not None:
            points = points[selected]
        frames.append(points)
    return frames


def load_metadata(output_folder: Path) -> dict | None:
    candidates = [
        output_folder / "ground_plane_metadata.json",
        output_folder.parent / "ground_plane_metadata.json",
    ]
    for path in candidates:
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
    return None


def colors_from_height(points: np.ndarray, z_min: float, z_max: float) -> np.ndarray:
    z = (points[:, 2] - z_min) / max(z_max - z_min, 1e-8)
    z = np.clip(z, 0.0, 1.0)
    low = np.array([194, 154, 90], dtype=np.float32)
    high = np.array([255, 230, 160], dtype=np.float32)
    return (low[None, :] * (1.0 - z[:, None]) + high[None, :] * z[:, None]).astype(np.uint8)


def main() -> None:
    args = parse_args()
    frame_paths = find_frame_paths(args.output_folder)
    frames = load_frames(frame_paths, args.max_points, args.sample_fraction, args.seed)
    stacked_bounds_min = np.min([frame.min(axis=0) for frame in frames], axis=0)
    stacked_bounds_max = np.max([frame.max(axis=0) for frame in frames], axis=0)
    z_min = float(stacked_bounds_min[2])
    z_max = float(stacked_bounds_max[2])
    metadata = load_metadata(args.output_folder)

    print(f"frames: {len(frames)}")
    print(f"points/frame: {frames[0].shape[0]}")
    print(f"sample fraction: {args.sample_fraction}")
    print(f"bounds min: {stacked_bounds_min.tolist()}")
    print(f"bounds max: {stacked_bounds_max.tolist()}")

    if args.dry_run:
        return

    server = viser.ViserServer(host=args.host, port=args.port)
    server.scene.world_axes.visible = True

    center = (stacked_bounds_min + stacked_bounds_max) / 2.0
    span = float(np.max(stacked_bounds_max - stacked_bounds_min))
    ground_z = float(stacked_bounds_min[2])
    if metadata is not None:
        ground_z = float(metadata["ground_plane_mpm"]["point"][2])

    server.scene.add_grid(
        "/ground_grid",
        width=span,
        height=span,
        plane="xy",
        position=(float(center[0]), float(center[1]), ground_z),
    )

    frame_slider = server.gui.add_slider(
        "Frame",
        min=0,
        max=len(frames) - 1,
        step=1,
        initial_value=0,
    )
    playing = server.gui.add_checkbox("Play", initial_value=True)
    initial_fps = args.fps
    if args.duration is not None:
        initial_fps = len(frames) / max(args.duration, 1e-6)
    fps = server.gui.add_number("FPS", initial_value=initial_fps, min=0.1, max=120.0, step=0.5)

    state = {"frame": 0, "handle": None}

    def show_frame(frame_index: int) -> None:
        frame_index = int(np.clip(frame_index, 0, len(frames) - 1))
        points = frames[frame_index]
        colors = colors_from_height(points, z_min, z_max)
        if state["handle"] is not None:
            state["handle"].remove()
        state["handle"] = server.scene.add_point_cloud(
            "/particles",
            points=points,
            colors=colors,
            point_size=args.point_size,
            point_shape="circle",
        )
        state["frame"] = frame_index

    @frame_slider.on_update
    def _(_) -> None:
        show_frame(int(frame_slider.value))

    show_frame(0)
    print(f"Open http://localhost:{args.port}")

    while True:
        if playing.value:
            next_frame = (state["frame"] + 1) % len(frames)
            frame_slider.value = next_frame
            show_frame(next_frame)
        time.sleep(1.0 / max(float(fps.value), 0.1))


if __name__ == "__main__":
    main()

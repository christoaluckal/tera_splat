#!/usr/bin/env python3
"""Render solver PLY frames to an MP4 without loading all frames into memory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from plyfile import PlyData

from view_solver_animation import find_frame_paths, resolve_simulation_dir


DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "outputs"
    / "genesis_cuda_10pct_2s_dt0005_min_ground"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_folder", nargs="?", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--duration", type=float, default=2.0)
    parser.add_argument("--fps", type=float, default=60.0)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--point-radius", type=int, default=2)
    parser.add_argument("--sample-fraction", type=float, default=1.0)
    parser.add_argument("--max-points", type=int, default=0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--still-frame",
        type=int,
        default=None,
        help="Render one simulation frame to an image and exit. Use 0 for the initial PLY.",
    )
    parser.add_argument(
        "--view",
        choices=("oblique", "top"),
        default="oblique",
        help="Camera projection used for the video.",
    )
    return parser.parse_args()


def read_xyz_ply(path: Path) -> np.ndarray:
    vertex = PlyData.read(path)["vertex"].data
    return np.stack([vertex["x"], vertex["y"], vertex["z"]], axis=1).astype(np.float32)


def choose_particle_indices(
    first: np.ndarray,
    *,
    sample_fraction: float,
    max_points: int,
    seed: int,
) -> np.ndarray | None:
    if not (0.0 < sample_fraction <= 1.0):
        raise ValueError("--sample-fraction must be in (0, 1]")

    target_points = first.shape[0]
    if sample_fraction < 1.0:
        target_points = min(target_points, max(int(np.ceil(first.shape[0] * sample_fraction)), 1))
    if max_points > 0:
        target_points = min(target_points, max_points)

    if target_points >= first.shape[0]:
        return None

    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(first.shape[0], size=target_points, replace=False))


def load_metadata(output_folder: Path) -> dict | None:
    candidates = [
        output_folder / "ground_plane_metadata.json",
        output_folder.parent / "ground_plane_metadata.json",
        resolve_simulation_dir(output_folder).parent / "ground_plane_metadata.json",
    ]
    for path in candidates:
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
    return None


def frame_indices(frame_count: int, duration: float, fps: float) -> np.ndarray:
    video_frames = max(int(round(duration * fps)), 1)
    return np.rint(np.linspace(0, frame_count - 1, video_frames)).astype(np.int64)


def project_points(points: np.ndarray, view: str) -> tuple[np.ndarray, np.ndarray]:
    if view == "top":
        projected = points[:, [0, 1]]
        depth = points[:, 2]
        return projected, depth

    camera_dir = np.array([0.55, -0.85, 0.55], dtype=np.float32)
    camera_dir /= np.linalg.norm(camera_dir)
    world_up = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    right = np.cross(camera_dir, world_up)
    right /= max(np.linalg.norm(right), 1e-8)
    up = np.cross(right, camera_dir)
    up /= max(np.linalg.norm(up), 1e-8)
    projected = np.stack([points @ right, points @ up], axis=1)
    depth = points @ camera_dir
    return projected, depth


def color_from_height(z: np.ndarray, z_min: float, z_max: float) -> np.ndarray:
    t = np.clip((z - z_min) / max(z_max - z_min, 1e-8), 0.0, 1.0)
    low = np.array([70, 115, 190], dtype=np.float32)
    mid = np.array([194, 154, 90], dtype=np.float32)
    high = np.array([255, 230, 160], dtype=np.float32)
    colors = np.empty((z.shape[0], 3), dtype=np.float32)
    lower = t < 0.5
    colors[lower] = low * (1.0 - 2.0 * t[lower, None]) + mid * (2.0 * t[lower, None])
    colors[~lower] = mid * (2.0 - 2.0 * t[~lower, None]) + high * (2.0 * t[~lower, None] - 1.0)
    return colors.astype(np.uint8)


def render_frame(
    points: np.ndarray,
    *,
    view: str,
    bounds_min: np.ndarray,
    bounds_max: np.ndarray,
    z_min: float,
    z_max: float,
    width: int,
    height: int,
    point_radius: int,
    ground_z: float | None,
    label: str,
) -> np.ndarray:
    image = np.full((height, width, 3), 245, dtype=np.uint8)

    bounds_corners = np.array(
        [
            [bounds_min[0], bounds_min[1], bounds_min[2]],
            [bounds_min[0], bounds_min[1], bounds_max[2]],
            [bounds_min[0], bounds_max[1], bounds_min[2]],
            [bounds_min[0], bounds_max[1], bounds_max[2]],
            [bounds_max[0], bounds_min[1], bounds_min[2]],
            [bounds_max[0], bounds_min[1], bounds_max[2]],
            [bounds_max[0], bounds_max[1], bounds_min[2]],
            [bounds_max[0], bounds_max[1], bounds_max[2]],
        ],
        dtype=np.float32,
    )
    corner_xy, _ = project_points(bounds_corners, view)
    xy, depth = project_points(points, view)
    xy_min = corner_xy.min(axis=0)
    xy_max = corner_xy.max(axis=0)
    span = np.maximum(xy_max - xy_min, 1e-8)
    margin = 0.08
    scale = min(width * (1.0 - 2.0 * margin) / span[0], height * (1.0 - 2.0 * margin) / span[1])
    pixel = np.empty_like(xy)
    pixel[:, 0] = (xy[:, 0] - xy_min[0]) * scale + width * margin
    pixel[:, 1] = height - ((xy[:, 1] - xy_min[1]) * scale + height * margin)
    pixel_i = np.rint(pixel).astype(np.int32)

    visible = (
        (pixel_i[:, 0] >= 0)
        & (pixel_i[:, 0] < width)
        & (pixel_i[:, 1] >= 0)
        & (pixel_i[:, 1] < height)
    )
    order = np.argsort(depth[visible])
    pix = pixel_i[visible][order]
    colors = color_from_height(points[visible, 2][order], z_min, z_max)
    for (x, y), color in zip(pix, colors):
        cv2.circle(image, (int(x), int(y)), point_radius, color.tolist(), thickness=-1, lineType=cv2.LINE_AA)

    if ground_z is not None:
        text = f"{label}   ground z={ground_z:.3f}"
    else:
        text = label
    cv2.putText(image, text, (24, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (30, 30, 30), 2, cv2.LINE_AA)
    return image


def main() -> None:
    args = parse_args()
    frame_paths = find_frame_paths(args.output_folder)
    selected_frames = frame_indices(len(frame_paths), args.duration, args.fps)
    output = args.output
    if output is None:
        if args.still_frame is None:
            output = args.output_folder / "solver_animation.mp4"
        else:
            output = args.output_folder / f"solver_frame_{args.still_frame:04d}.png"
    output.parent.mkdir(parents=True, exist_ok=True)

    first = read_xyz_ply(frame_paths[0])
    selected_particles = choose_particle_indices(
        first,
        sample_fraction=args.sample_fraction,
        max_points=args.max_points,
        seed=args.seed,
    )
    if selected_particles is not None:
        first = first[selected_particles]

    scan_paths = [frame_paths[int(i)] for i in np.unique(np.concatenate(([0, len(frame_paths) - 1], selected_frames)))]
    bounds_min = first.min(axis=0)
    bounds_max = first.max(axis=0)
    for path in scan_paths[1:]:
        points = read_xyz_ply(path)
        if selected_particles is not None:
            points = points[selected_particles]
        bounds_min = np.minimum(bounds_min, points.min(axis=0))
        bounds_max = np.maximum(bounds_max, points.max(axis=0))

    metadata = load_metadata(args.output_folder)
    ground_z = None
    if metadata is not None:
        ground_z = float(metadata["ground_plane_mpm"]["point"][2])

    if args.still_frame is not None:
        sim_index = int(np.clip(args.still_frame, 0, len(frame_paths) - 1))
        points = read_xyz_ply(frame_paths[sim_index])
        if selected_particles is not None:
            points = points[selected_particles]
        image = render_frame(
            points,
            view=args.view,
            bounds_min=bounds_min,
            bounds_max=bounds_max,
            z_min=float(bounds_min[2]),
            z_max=float(bounds_max[2]),
            width=args.width,
            height=args.height,
            point_radius=args.point_radius,
            ground_z=ground_z,
            label=f"frame {sim_index}/{len(frame_paths) - 1}   initial state",
        )
        if not cv2.imwrite(str(output), image):
            raise SystemExit(f"Could not write image to {output}")
        print(f"source frames: {len(frame_paths)}")
        print(f"rendered frame: {sim_index}")
        print(f"points/frame: {points.shape[0]}")
        print(f"output: {output}")
        return

    writer = cv2.VideoWriter(
        str(output),
        cv2.VideoWriter_fourcc(*"mp4v"),
        args.fps,
        (args.width, args.height),
    )
    if not writer.isOpened():
        raise SystemExit(f"Could not open video writer for {output}")

    for video_index, sim_index in enumerate(selected_frames):
        points = read_xyz_ply(frame_paths[int(sim_index)])
        if selected_particles is not None:
            points = points[selected_particles]
        label = f"frame {int(sim_index)}/{len(frame_paths) - 1}   t={video_index / args.fps:.3f}s"
        image = render_frame(
            points,
            view=args.view,
            bounds_min=bounds_min,
            bounds_max=bounds_max,
            z_min=float(bounds_min[2]),
            z_max=float(bounds_max[2]),
            width=args.width,
            height=args.height,
            point_radius=args.point_radius,
            ground_z=ground_z,
            label=label,
        )
        writer.write(image)
        if (video_index + 1) % max(int(args.fps), 1) == 0:
            print(f"rendered {video_index + 1}/{len(selected_frames)} video frames")
    writer.release()

    displayed_points = first.shape[0]
    print(f"source frames: {len(frame_paths)}")
    print(f"video frames: {len(selected_frames)}")
    print(f"points/frame: {displayed_points}")
    print(f"duration: {args.duration}")
    print(f"fps: {args.fps}")
    print(f"output: {output}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Render particle frames with a simple cylinder-indenter overlay."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import cv2
import numpy as np

from render_solver_video import (
    choose_particle_indices,
    color_from_height,
    frame_indices,
    load_metadata,
    project_points,
    read_xyz_ply,
)
from view_solver_animation import find_frame_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_folder", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--duration", type=float, default=2.0)
    parser.add_argument("--fps", type=float, default=60.0)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--point-radius", type=int, default=1)
    parser.add_argument("--sample-fraction", type=float, default=1.0)
    parser.add_argument("--max-points", type=int, default=0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--view", choices=("oblique", "top"), default="oblique")
    return parser.parse_args()


def read_pose_csv(path: Path) -> dict[int, dict[str, float]]:
    poses = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            poses[int(row["step"])] = {key: float(value) for key, value in row.items() if key != "step"}
    return poses


def step_from_frame(path: Path) -> int:
    return int(path.stem.split("_")[-1])


def cylinder_points(x: float, y: float, z: float, radius: float, height: float, n: int = 64) -> tuple[np.ndarray, np.ndarray]:
    theta = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False, dtype=np.float32)
    circle_xy = np.stack([x + radius * np.cos(theta), y + radius * np.sin(theta)], axis=1)
    bottom = np.column_stack([circle_xy, np.full(n, z - height * 0.5, dtype=np.float32)])
    top = np.column_stack([circle_xy, np.full(n, z + height * 0.5, dtype=np.float32)])
    return bottom.astype(np.float32), top.astype(np.float32)


def compute_projection_transform(
    bounds_min: np.ndarray,
    bounds_max: np.ndarray,
    *,
    view: str,
    width: int,
    height: int,
) -> tuple[np.ndarray, float, float]:
    corners = np.array(
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
    corner_xy, _ = project_points(corners, view)
    xy_min = corner_xy.min(axis=0)
    xy_max = corner_xy.max(axis=0)
    span = np.maximum(xy_max - xy_min, 1e-8)
    margin = 0.08
    scale = min(width * (1.0 - 2.0 * margin) / span[0], height * (1.0 - 2.0 * margin) / span[1])
    return xy_min, scale, margin


def world_to_pixel(points: np.ndarray, *, view: str, xy_min: np.ndarray, scale: float, margin: float, width: int, height: int) -> np.ndarray:
    xy, _ = project_points(points, view)
    pixel = np.empty_like(xy)
    pixel[:, 0] = (xy[:, 0] - xy_min[0]) * scale + width * margin
    pixel[:, 1] = height - ((xy[:, 1] - xy_min[1]) * scale + height * margin)
    return np.rint(pixel).astype(np.int32)


def draw_polyline(image: np.ndarray, points: np.ndarray, color: tuple[int, int, int], closed: bool = True) -> None:
    pts = points.reshape((-1, 1, 2))
    cv2.polylines(image, [pts], closed, color, thickness=2, lineType=cv2.LINE_AA)


def render_frame(
    points: np.ndarray,
    *,
    pose: dict[str, float] | None,
    radius: float,
    height_m: float,
    view: str,
    bounds_min: np.ndarray,
    bounds_max: np.ndarray,
    z_min: float,
    z_max: float,
    width: int,
    height: int,
    point_radius: int,
    label: str,
) -> np.ndarray:
    image = np.full((height, width, 3), 245, dtype=np.uint8)
    xy_min, scale, margin = compute_projection_transform(bounds_min, bounds_max, view=view, width=width, height=height)

    xy, depth = project_points(points, view)
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
    for (px, py), color in zip(pix, colors):
        cv2.circle(image, (int(px), int(py)), point_radius, color.tolist(), thickness=-1, lineType=cv2.LINE_AA)

    if pose is not None:
        bottom, top = cylinder_points(pose["x"], pose["y"], pose["z"], radius, height_m)
        bottom_px = world_to_pixel(bottom, view=view, xy_min=xy_min, scale=scale, margin=margin, width=width, height=height)
        top_px = world_to_pixel(top, view=view, xy_min=xy_min, scale=scale, margin=margin, width=width, height=height)
        draw_polyline(image, bottom_px, (20, 20, 220))
        draw_polyline(image, top_px, (20, 20, 220))
        for idx in range(0, bottom_px.shape[0], max(bottom_px.shape[0] // 8, 1)):
            cv2.line(image, tuple(bottom_px[idx]), tuple(top_px[idx]), (20, 20, 220), 2, cv2.LINE_AA)

    cv2.putText(image, label, (24, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (30, 30, 30), 2, cv2.LINE_AA)
    return image


def main() -> None:
    args = parse_args()
    output = args.output or args.output_folder / "indenter_animation.mp4"
    output.parent.mkdir(parents=True, exist_ok=True)
    frame_paths = find_frame_paths(args.output_folder)
    selected_frames = frame_indices(len(frame_paths), args.duration, args.fps)
    poses = read_pose_csv(args.output_folder / "indenter_pose.csv")
    metadata = load_metadata(args.output_folder) or {}
    indenter = metadata.get("indenter") or {}
    radius = float(indenter.get("radius", 0.08))
    height_m = float(indenter.get("height", 0.04))

    first = read_xyz_ply(frame_paths[0])
    selected_particles = choose_particle_indices(
        first,
        sample_fraction=args.sample_fraction,
        max_points=args.max_points,
        seed=args.seed,
    )
    if selected_particles is not None:
        first = first[selected_particles]

    bounds_min = first.min(axis=0)
    bounds_max = first.max(axis=0)
    scan_indices = np.unique(np.concatenate(([0, len(frame_paths) - 1], selected_frames)))
    for frame_idx in scan_indices[1:]:
        points = read_xyz_ply(frame_paths[int(frame_idx)])
        if selected_particles is not None:
            points = points[selected_particles]
        bounds_min = np.minimum(bounds_min, points.min(axis=0))
        bounds_max = np.maximum(bounds_max, points.max(axis=0))
    for pose in poses.values():
        bottom, top = cylinder_points(pose["x"], pose["y"], pose["z"], radius, height_m)
        bounds_min = np.minimum(bounds_min, np.minimum(bottom.min(axis=0), top.min(axis=0)))
        bounds_max = np.maximum(bounds_max, np.maximum(bottom.max(axis=0), top.max(axis=0)))

    writer = cv2.VideoWriter(
        str(output),
        cv2.VideoWriter_fourcc(*"mp4v"),
        args.fps,
        (args.width, args.height),
    )
    if not writer.isOpened():
        raise SystemExit(f"Could not open video writer for {output}")

    for video_index, sim_index in enumerate(selected_frames):
        frame_path = frame_paths[int(sim_index)]
        step = step_from_frame(frame_path)
        points = read_xyz_ply(frame_path)
        if selected_particles is not None:
            points = points[selected_particles]
        pose = poses.get(step)
        label = f"step {step}   t={video_index / args.fps:.3f}s"
        image = render_frame(
            points,
            pose=pose,
            radius=radius,
            height_m=height_m,
            view=args.view,
            bounds_min=bounds_min,
            bounds_max=bounds_max,
            z_min=float(bounds_min[2]),
            z_max=float(bounds_max[2]),
            width=args.width,
            height=args.height,
            point_radius=args.point_radius,
            label=label,
        )
        writer.write(image)
        if (video_index + 1) % max(int(args.fps), 1) == 0:
            print(f"rendered {video_index + 1}/{len(selected_frames)} video frames")
    writer.release()
    print(f"source frames: {len(frame_paths)}")
    print(f"video frames: {len(selected_frames)}")
    print(f"output: {output}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Render a Chrono cylinder episode from stored initial, loaded, and residual maps.

The cylinder trajectory is recorded in object_pose.csv. Intervening terrain frames
are linear interpolation between stored SCM states and are labeled as such.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import imageio.v2 as imageio
import matplotlib
import numpy as np
import yaml

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chrono-episode", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--duration", type=float, default=8.0)
    parser.add_argument("--fps", type=int, default=24)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.duration <= 0.0 or args.fps <= 0:
        raise ValueError("duration and fps must be positive")
    episode = args.chrono_episode.resolve()
    with (episode / "manifest.yaml").open(encoding="utf-8") as file:
        manifest = yaml.safe_load(file)
    with (episode / "action.json").open(encoding="utf-8") as file:
        action = json.load(file)
    with (episode / "object_pose.csv").open(newline="", encoding="utf-8") as file:
        poses = list(csv.DictReader(file))
    if not poses:
        raise ValueError("object_pose.csv contains no rows")
    initial = np.load(episode / "initial_heightmap_m.npy")
    loaded = np.load(episode / "loaded_heightmap_m.npy")
    residual = np.load(episode / "residual_heightmap_m.npy")
    valid = np.load(episode / "valid_heightmap_mask.npy").astype(bool)
    spec = manifest["heightmap"]
    spacing = float(spec["spacing_m"])
    x0, y0 = (float(value) for value in spec["origin_xy_m"])
    rows, cols = (int(value) for value in spec["shape"])
    xs = x0 + spacing * np.arange(cols)
    ys = y0 + spacing * np.arange(rows)
    center_row = int(np.argmin(np.abs(ys - float(action["center_xy_m"][1]))))
    extent = (x0 - 0.5 * spacing, x0 + (cols - 0.5) * spacing, y0 - 0.5 * spacing, y0 + (rows - 0.5) * spacing)
    max_down_mm = max(float(np.max((initial - state)[valid] * 1e3)) for state in (loaded, residual))
    max_down_mm = max(max_down_mm, 1e-3)
    frame_count = max(1, int(round(args.duration * args.fps)))
    loaded_frame_count = max(1, int(round(0.72 * frame_count)))
    selected_pose_indices = np.rint(np.linspace(0, len(poses) - 1, loaded_frame_count)).astype(int)
    figure, (profile_ax, dem_ax) = plt.subplots(1, 2, figsize=(12, 5.6), layout="constrained")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with imageio.get_writer(args.output, fps=args.fps, codec="libx264", quality=8) as writer:
        for index in range(frame_count):
            profile_ax.clear()
            dem_ax.clear()
            if index < loaded_frame_count:
                alpha = 0.0 if loaded_frame_count == 1 else index / (loaded_frame_count - 1)
                state = (1.0 - alpha) * initial + alpha * loaded
                pose = poses[int(selected_pose_indices[index])]
                phase_text = "loaded; SCM surface interpolated from stored states"
                show_indenter = True
            else:
                residual_count = max(frame_count - loaded_frame_count, 1)
                alpha = (index - loaded_frame_count + 1) / residual_count
                state = (1.0 - alpha) * loaded + alpha * residual
                pose = None
                phase_text = "post-removal; SCM surface interpolated from stored states"
                show_indenter = False
            profile_ax.fill_between(xs, -0.08, state[center_row], color="#b68755", alpha=0.95)
            profile_ax.plot(xs, state[center_row], color="#3b2818", linewidth=1.4)
            if show_indenter and pose is not None:
                body_x = float(pose["x_m"])
                body_z = float(pose["z_m"])
                profile_ax.add_patch(
                    Rectangle(
                        (body_x - float(action["radius_m"]), body_z - 0.5 * float(action["height_m"])),
                        2.0 * float(action["radius_m"]),
                        float(action["height_m"]),
                        facecolor="#50677e",
                        edgecolor="#1b2730",
                        linewidth=1.2,
                    )
                )
            profile_ax.axhline(0.0, color="#808080", linestyle="--", linewidth=0.8)
            profile_ax.set(xlim=(-0.18, 0.18), ylim=(-0.08, 0.10), xlabel="bed x (m)", ylabel="bed z (m)")
            profile_ax.set_aspect("equal", adjustable="box")
            profile_ax.set_title("Chrono SCM profile and indenter")
            deformation = np.ma.array((initial - state) * 1e3, mask=~valid)
            image = dem_ax.imshow(deformation, extent=extent, origin="lower", cmap="viridis", vmin=0.0, vmax=max_down_mm, interpolation="nearest")
            dem_ax.add_patch(Circle(action["center_xy_m"], action["radius_m"], fill=False, color="white", linewidth=1.1))
            dem_ax.set(xlabel="bed x (m)", ylabel="bed y (m)", aspect="equal", title="SCM downward deformation (mm)")
            figure.suptitle(f"Chrono SCM: {phase_text}")
            if not hasattr(main, "colorbar"):
                main.colorbar = figure.colorbar(image, ax=dem_ax, shrink=0.82, label="downward deformation (mm)")
            figure.canvas.draw()
            writer.append_data(np.asarray(figure.canvas.buffer_rgba())[:, :, :3])
    plt.close(figure)
    print(args.output)


if __name__ == "__main__":
    main()

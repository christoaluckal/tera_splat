#!/usr/bin/env python3
"""Render fixed-isometric Genesis initialization point clouds as a static MP4.

The output deliberately uses point sprites only: it contains no reconstructed
surface, interpolation, mesh, or camera motion.  It compares the accepted
20-mm sweep configuration against the 25-mm H0-gate failure.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from particle_io import read_particle_ply


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUCCESS = REPO_ROOT / "outputs" / "validity_experiment" / "bayesopt" / "A0_cal_full10mm_4d_clean" / "study_dooqrbdl" / "trials" / "iteration_002" / "prepared" / "metric_bed_source" / "particles_initial_mpm.ply"
DEFAULT_FAILURE = REPO_ROOT / "outputs" / "validity_experiment" / "bayesopt" / "A0_cal_full10mm_4d_proper" / "study_ulik6isa" / "trials" / "iteration_008" / "prepared" / "metric_bed_source" / "particles_initial_mpm.ply"
DEFAULT_OUTPUT = REPO_ROOT / "outputs" / "validity_experiment" / "visualizations" / "stage1_genesis_initialization_pcd_isometric.mp4"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--success-pcd", type=Path, default=DEFAULT_SUCCESS)
    parser.add_argument("--failure-pcd", type=Path, default=DEFAULT_FAILURE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seconds", type=float, default=4.0)
    parser.add_argument("--fps", type=int, default=24)
    return parser.parse_args()


def style_axis(axis, title: str) -> None:
    axis.set_title(title, fontsize=12, pad=14)
    axis.set_xlabel("x (m)")
    axis.set_ylabel("y (m)")
    axis.set_zlabel("z (m)")
    axis.set_xlim(-0.63, 0.63)
    axis.set_ylim(-0.63, 0.63)
    axis.set_zlim(-0.125, 0.025)
    axis.set_box_aspect((1.0, 1.0, 0.35))
    axis.set_proj_type("ortho")
    axis.view_init(elev=25, azim=-52)
    axis.tick_params(labelsize=8, pad=1)
    axis.xaxis.pane.fill = False
    axis.yaxis.pane.fill = False
    axis.zaxis.pane.fill = False


def plot_points(axis, points: np.ndarray, title: str) -> None:
    # Plot only particle centres.  Color encodes elevation to make individual
    # horizontal initialization layers visible without reconstructing a DEM.
    axis.scatter(
        points[:, 0], points[:, 1], points[:, 2],
        c=points[:, 2], cmap="viridis", vmin=-0.11, vmax=0.0,
        s=1.8, marker="o", linewidths=0, alpha=0.9, depthshade=False,
    )
    style_axis(axis, f"{title}\n{len(points):,} Genesis initialization particles")


def main() -> None:
    args = parse_args()
    if args.seconds <= 0 or args.fps <= 0:
        raise ValueError("--seconds and --fps must be positive")
    success = read_particle_ply(args.success_pcd.resolve())
    failure = read_particle_ply(args.failure_pcd.resolve())
    figure = plt.figure(figsize=(14, 7.5), constrained_layout=True)
    accepted_axis = figure.add_subplot(1, 2, 1, projection="3d")
    rejected_axis = figure.add_subplot(1, 2, 2, projection="3d")
    plot_points(accepted_axis, success, "Accepted configuration: 20 mm spacing, ratio 0.85")
    plot_points(rejected_axis, failure, "H0-gate failure: 25 mm spacing, ratio 0.85")
    figure.suptitle(
        "Genesis metric-bed initialization PCD — fixed isometric camera; particles only, no surface interpolation",
        fontsize=14,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    preview = args.output.with_suffix(".png")
    figure.savefig(preview, dpi=160)
    subprocess.run(
        [
            "ffmpeg", "-y", "-loop", "1", "-i", str(preview), "-t", str(args.seconds),
            "-r", str(args.fps), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(args.output),
        ],
        check=True,
    )
    print(args.output)


if __name__ == "__main__":
    main()

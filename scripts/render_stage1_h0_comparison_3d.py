#!/usr/bin/env python3
"""Render a rotating 3-D MP4 of accepted and rejected Stage-1 H0 beds.

Each row is a sweep candidate: Chrono's reference H0 is at left and the
corresponding settled Genesis bed is at right.  Heights and axes are in mm;
the z box aspect is intentionally enlarged so sub-decimetre failures remain
legible in the overview.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, FFMpegWriter

from chrono_episode_bridge import load_episode


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EPISODE = REPO_ROOT.parent / "tera_splat_sim" / "validity_experiment" / "chrono_episodes" / "A0_cal_full10mm"
DEFAULT_SUCCESS = REPO_ROOT / "outputs" / "validity_experiment" / "bayesopt" / "A0_cal_full10mm_4d_clean" / "study_dooqrbdl" / "trials" / "iteration_002"
DEFAULT_FAILURE = REPO_ROOT / "outputs" / "validity_experiment" / "bayesopt" / "A0_cal_full10mm_4d_proper" / "study_ulik6isa" / "trials" / "iteration_008"
DEFAULT_OUTPUT = REPO_ROOT / "outputs" / "validity_experiment" / "visualizations" / "stage1_h0_success_failure_comparison_3d.mp4"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chrono-episode", type=Path, default=DEFAULT_EPISODE)
    parser.add_argument("--success-trial", type=Path, default=DEFAULT_SUCCESS)
    parser.add_argument("--failure-trial", type=Path, default=DEFAULT_FAILURE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    # 60 frames retains a smooth inspection rotation while staying practical
    # on a workstation without GPU-accelerated Matplotlib rendering.
    parser.add_argument("--seconds", type=float, default=6.0)
    parser.add_argument("--fps", type=int, default=10)
    parser.add_argument("--dpi", type=int, default=100)
    return parser.parse_args()


def trial_state(trial_dir: Path) -> tuple[np.ndarray, np.ndarray, dict, dict]:
    prepared = trial_dir / "prepared"
    state = np.load(prepared / "settled_heightmap_m.npy")
    valid = np.load(prepared / "valid_heightmap_mask.npy").astype(bool)
    with (prepared / "prepared_bed_manifest.json").open(encoding="utf-8") as file:
        prepared_manifest = json.load(file)
    with (trial_dir / "candidate.json").open(encoding="utf-8") as file:
        candidate = json.load(file)
    return state, valid, prepared_manifest, candidate


def case_label(candidate: dict, prepared: dict) -> str:
    surface = prepared["surface_match"]
    state = "ACCEPTED" if prepared["accepted"] else "REJECTED"
    return (
        f"{state}: spacing={candidate['particle_spacing_m'] * 1e3:.1f} mm, "
        f"ratio={candidate['particle_size_ratio']:.2f}\n"
        f"H0 RMSE={surface['rmse_m'] * 1e3:.3f} mm | max={surface['max_abs_m'] * 1e3:.3f} mm"
    )


def surface(axis, x_m: np.ndarray, y_m: np.ndarray, height_mm: np.ndarray, valid: np.ndarray, norm) -> None:
    z = np.where(valid, height_mm, np.nan)
    axis.plot_surface(
        x_m,
        y_m,
        z,
        rstride=1,
        cstride=1,
        facecolors=plt.get_cmap("viridis")(norm(z)),
        linewidth=0,
        antialiased=False,
        shade=False,
    )


def style_axis(axis, title: str, z_min: float, z_max: float) -> None:
    axis.set_title(title, fontsize=10, pad=8)
    axis.set_xlabel("x (m)", labelpad=3)
    axis.set_ylabel("y (m)", labelpad=3)
    axis.set_zlabel("height vs Chrono median (mm)", labelpad=5)
    axis.set_xlim(-0.605, 0.605)
    axis.set_ylim(-0.605, 0.605)
    axis.set_zlim(z_min, z_max)
    # Preserve numeric z coordinates while enlarging their visual footprint.
    axis.set_box_aspect((1.0, 1.0, 0.35))
    axis.tick_params(labelsize=7, pad=0)
    axis.xaxis.pane.fill = False
    axis.yaxis.pane.fill = False
    axis.zaxis.pane.fill = False


def main() -> None:
    args = parse_args()
    if args.seconds <= 0 or args.fps <= 0:
        raise ValueError("--seconds and --fps must be positive")
    _manifest, _action, chrono_h0, chrono_valid = load_episode(args.chrono_episode.resolve())
    success_h0, success_valid, success_prepared, success_candidate = trial_state(args.success_trial.resolve())
    failure_h0, failure_valid, failure_prepared, failure_candidate = trial_state(args.failure_trial.resolve())
    if any(state.shape != chrono_h0.shape for state in (success_h0, failure_h0)):
        raise ValueError("All H0 maps must share the Chrono target grid")

    center_m = float(np.median(chrono_h0[chrono_valid]))
    x = np.linspace(-0.6, 0.6, chrono_h0.shape[1])
    y = np.linspace(-0.6, 0.6, chrono_h0.shape[0])
    x_m, y_m = np.meshgrid(x, y)
    chrono_mm = (chrono_h0 - center_m) * 1e3
    success_mm = (success_h0 - center_m) * 1e3
    failure_mm = (failure_h0 - center_m) * 1e3
    z_min = min(-10.0, float(np.nanmin(failure_mm[failure_valid])) - 5.0)
    z_max = max(10.0, float(np.nanmax(np.concatenate((chrono_mm[chrono_valid], success_mm[success_valid], failure_mm[failure_valid])))) + 5.0)
    norm = mpl.colors.Normalize(vmin=-6.0, vmax=6.0, clip=True)

    figure = plt.figure(figsize=(14, 12), constrained_layout=True)
    axes = np.array(
        [[figure.add_subplot(2, 2, 1, projection="3d"), figure.add_subplot(2, 2, 2, projection="3d")],
         [figure.add_subplot(2, 2, 3, projection="3d"), figure.add_subplot(2, 2, 4, projection="3d")]],
        dtype=object,
    )
    surface(axes[0, 0], x_m, y_m, chrono_mm, chrono_valid, norm)
    surface(axes[0, 1], x_m, y_m, success_mm, success_valid, norm)
    surface(axes[1, 0], x_m, y_m, chrono_mm, chrono_valid, norm)
    surface(axes[1, 1], x_m, y_m, failure_mm, failure_valid, norm)
    style_axis(axes[0, 0], "Chrono reference H0", z_min, z_max)
    style_axis(axes[0, 1], "Genesis settled H0\n" + case_label(success_candidate, success_prepared), z_min, z_max)
    style_axis(axes[1, 0], "Chrono reference H0", z_min, z_max)
    style_axis(axes[1, 1], "Genesis settled H0\n" + case_label(failure_candidate, failure_prepared), z_min, z_max)
    colorbar = figure.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap="viridis"), ax=axes.ravel(), shrink=0.72, pad=0.03)
    colorbar.set_label("height relative to Chrono median (mm; colors clipped at ±6 mm)")
    figure.suptitle(
        "Stage 1 H0 surface inspection — Chrono reference left, Genesis settled bed right\n"
        "Rotating view; z coordinates are physical mm, with box aspect enlarged for visibility.",
        fontsize=14,
    )

    def update(frame: int):
        azimuth = 360.0 * frame / max(1, frame_count - 1) + 20.0
        elevation = 25.0 + 8.0 * np.sin(2.0 * np.pi * frame / max(1, frame_count - 1))
        for axis in axes.ravel():
            axis.view_init(elev=elevation, azim=azimuth)
        return tuple(axes.ravel())

    frame_count = max(2, round(args.seconds * args.fps))
    animation = FuncAnimation(figure, update, frames=frame_count, interval=1000 / args.fps, blit=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    animation.save(args.output, writer=FFMpegWriter(fps=args.fps, bitrate=5000), dpi=args.dpi)
    print(args.output)


if __name__ == "__main__":
    main()

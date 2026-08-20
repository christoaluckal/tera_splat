#!/usr/bin/env python3
"""Render accepted and rejected Stage-1 H0 surfaces against the Chrono reference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from chrono_episode_bridge import load_episode


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EPISODE = REPO_ROOT.parent / "tera_splat_sim" / "validity_experiment" / "chrono_episodes" / "A0_cal_full10mm"
DEFAULT_SUCCESS = REPO_ROOT / "outputs" / "validity_experiment" / "bayesopt" / "A0_cal_full10mm_4d_clean" / "study_dooqrbdl" / "trials" / "iteration_002"
DEFAULT_FAILURE = REPO_ROOT / "outputs" / "validity_experiment" / "bayesopt" / "A0_cal_full10mm_4d_proper" / "study_ulik6isa" / "trials" / "iteration_008"
DEFAULT_OUTPUT = REPO_ROOT / "outputs" / "validity_experiment" / "visualizations" / "stage1_h0_success_failure_comparison.png"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chrono-episode", type=Path, default=DEFAULT_EPISODE)
    parser.add_argument("--success-trial", type=Path, default=DEFAULT_SUCCESS)
    parser.add_argument("--failure-trial", type=Path, default=DEFAULT_FAILURE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--display-range-mm",
        type=float,
        default=6.0,
        help="Symmetric display range around the Chrono median; values outside are visibly clipped.",
    )
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


def label(candidate: dict, prepared: dict) -> str:
    surface = prepared["surface_match"]
    state = "accepted" if prepared["accepted"] else "rejected"
    return (
        f"{state}: E={candidate['E_pa'] / 1e3:.1f} kPa, phi={candidate['phi_deg']:.1f} deg, "
        f"spacing={candidate['particle_spacing_m'] * 1e3:.1f} mm, ratio={candidate['particle_size_ratio']:.2f}\n"
        f"H0 RMSE={surface['rmse_m'] * 1e3:.3f} mm, max={surface['max_abs_m'] * 1e3:.3f} mm"
    )


def plot_pair(
    axes: tuple,
    chrono_h0: np.ndarray,
    chrono_valid: np.ndarray,
    genesis_h0: np.ndarray,
    genesis_valid: np.ndarray,
    caption: str,
    center_m: float,
    display_range_mm: float,
) -> None:
    left, right = axes
    extent = (-0.605, 0.605, -0.605, 0.605)
    chrono_display = (chrono_h0 - center_m) * 1e3
    genesis_display = (genesis_h0 - center_m) * 1e3
    chrono_display = np.where(chrono_valid, chrono_display, np.nan)
    genesis_display = np.where(genesis_valid, genesis_display, np.nan)
    common = dict(cmap="viridis", vmin=-display_range_mm, vmax=display_range_mm, origin="lower", extent=extent, interpolation="nearest")
    image = left.imshow(chrono_display, **common)
    right.imshow(genesis_display, **common)
    left.set_title("Chrono reference H0")
    right.set_title("Genesis settled H0\n" + caption)
    for axis in (left, right):
        axis.set_xlabel("bed x (m)")
        axis.set_ylabel("bed y (m)")
        axis.set_aspect("equal")
    return image


def main() -> None:
    args = parse_args()
    _manifest, _action, chrono_h0, chrono_valid = load_episode(args.chrono_episode.resolve())
    success_h0, success_valid, success_prepared, success_candidate = trial_state(args.success_trial.resolve())
    failure_h0, failure_valid, failure_prepared, failure_candidate = trial_state(args.failure_trial.resolve())
    if any(state.shape != chrono_h0.shape for state in (success_h0, failure_h0)):
        raise ValueError("All H0 maps must share the Chrono target grid")
    center_m = float(np.median(chrono_h0[chrono_valid]))
    figure, axes = plt.subplots(2, 2, figsize=(14, 13), constrained_layout=True)
    image = plot_pair(
        tuple(axes[0]), chrono_h0, chrono_valid, success_h0, success_valid,
        label(success_candidate, success_prepared), center_m, args.display_range_mm,
    )
    plot_pair(
        tuple(axes[1]), chrono_h0, chrono_valid, failure_h0, failure_valid,
        label(failure_candidate, failure_prepared), center_m, args.display_range_mm,
    )
    figure.colorbar(image, ax=axes, shrink=0.8, label="elevation relative to Chrono median (mm)")
    figure.suptitle(
        "Stage 1 prepared-bed inspection: same Chrono H0 at left, Genesis settled H0 at right\n"
        "Display is clipped to expose millimetre-scale geometry; saturated dark regions mark large downward errors.",
        fontsize=14,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=180)
    print(args.output)


if __name__ == "__main__":
    main()

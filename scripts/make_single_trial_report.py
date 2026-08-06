#!/usr/bin/env python3
"""Create a Markdown report for a normalized single-trial calibration dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRIAL = REPO_ROOT / "data" / "single_trial_real3"
DEFAULT_OUTPUT = REPO_ROOT / "outputs" / "single_trial_real3_report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trial-dir", type=Path, default=DEFAULT_TRIAL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def metric_table(stats: dict) -> str:
    rows = [
        ("valid_cells", stats["valid_cells"], "count"),
        ("valid_area_m2", stats["valid_area_m2"], "m^2"),
        ("mean_change_m", stats["mean_change_m"], "m"),
        ("median_change_m", stats["median_change_m"], "m"),
        ("p05_m", stats["p05_m"], "m"),
        ("p95_m", stats["p95_m"], "m"),
        ("cut_volume_m3", stats["cut_volume_m3"], "m^3"),
        ("fill_volume_m3", stats["fill_volume_m3"], "m^3"),
        ("net_volume_m3", stats["net_volume_m3"], "m^3"),
    ]
    text = ["| Metric | Value | Unit |", "|---|---:|---|"]
    for name, value, unit in rows:
        if isinstance(value, float):
            value_text = f"{value:.9g}"
        else:
            value_text = str(value)
        text.append(f"| `{name}` | {value_text} | {unit} |")
    return "\n".join(text)


def main() -> None:
    args = parse_args()
    processed = args.trial_dir / "processed"
    summary = load_json(processed / "preprocess_summary.json")
    noise = load_json(processed / "noise_stats.json")
    delta_npz = np.load(processed / "delta_h_real.npz")
    delta = delta_npz["delta_h"]
    valid = delta_npz["valid_mask"].astype(bool)
    finite_delta = delta[valid]

    action_text = (args.trial_dir / "action.yaml").read_text(encoding="utf-8")
    action_ready = "calibration_ready: true" in action_text

    lines = [
        "# Single-Trial real3 Calibration Report",
        "",
        "## Summary",
        "",
        f"- Trial directory: `{args.trial_dir}`",
        f"- Primary target: center 1 ft DEM at `{summary['primary_cell_size_m']}` m/cell.",
        f"- ROI bounds XY: `{summary['primary_bounds_xy_m']}` m in the RealSense `bed` frame.",
        f"- DEM shape: `{summary['primary_shape']}`.",
        f"- Valid overlap cells: `{summary['valid_cells']}`.",
        f"- Calibration rollouts ready: `{'yes' if action_ready else 'no'}`.",
        "",
        "The real-data preprocessing layer is implemented. Full Genesis parameter search is blocked until scan correction, footprint verification, and the mass-controlled Genesis runner gates are complete.",
        "",
        "## Real Deformation Target",
        "",
        metric_table(summary["primary_delta_stats"]),
        "",
        "The normalized files are:",
        "",
        "```text",
        "data/single_trial_real3/manifest.yaml",
        "data/single_trial_real3/action.yaml",
        "data/single_trial_real3/processed/S0_height.npz",
        "data/single_trial_real3/processed/S1_height.npz",
        "data/single_trial_real3/processed/delta_h_real.npz",
        "data/single_trial_real3/processed/valid_mask.npz",
        "data/single_trial_real3/processed/noise_stats.json",
        "```",
        "",
        "## Scan/Registration Noise Proxy",
        "",
        f"- ICP final RMSE: `{noise['icp_final_rmse_m']:.9g}` m.",
        f"- Direct-vs-ICP delta median abs difference: `{noise['full_direct_vs_icp_delta_abs_median_m']:.9g}` m.",
        f"- Direct-vs-ICP delta p95 abs difference: `{noise['full_direct_vs_icp_delta_abs_p95_m']:.9g}` m.",
        f"- Provisional Huber delta: `{noise['recommended_huber_delta_m']:.9g}` m.",
        "",
        "This is only a proxy. Replace it with two-view disagreement and static-border residuals before final calibration.",
        "",
        "## Distribution Diagnostics",
        "",
        f"- Minimum observed delta: `{float(np.min(finite_delta)):.9g}` m.",
        f"- Maximum observed delta: `{float(np.max(finite_delta)):.9g}` m.",
        f"- 1st percentile: `{float(np.percentile(finite_delta, 1)):.9g}` m.",
        f"- 99th percentile: `{float(np.percentile(finite_delta, 99)):.9g}` m.",
        "",
        "## Calibration Status",
        "",
        "Implemented now:",
        "",
        "- Real3 DEM normalization into the planned single-trial data contract.",
        "- Real deformation target `delta_h_real` and valid mask generation.",
        "- Provisional noise statistics.",
        "- Report generation.",
        "- Corrected cylinder action template: `0.14605 m` is diameter and `0.073025 m` is radius.",
        "",
        "Blocked before Genesis search:",
        "",
    ]
    for field in summary["blocking_fields"]:
        lines.append(f"- `{field}`")

    lines.extend(
        [
            "",
            "Once those gates pass, the next implementation step is a coarse `8 x 8` grid over:",
            "",
            "```text",
            "log10_E in [4, 7]",
            "phi_deg in [15, 45]",
            "```",
            "",
        "The forward model must use mass-controlled gravitational cylinder release, not prescribed target-depth indentation, and restore the same settled base before every candidate.",
            "",
            "## Source RealSense Artifacts",
            "",
            "```text",
            "../lamp/ros2_ws/src/realsense_splat/episodes/real3_compare_metrics_3tag/center_1ft_fine_dem/",
            "../lamp/ros2_ws/src/realsense_splat/episodes/real3_compare_metrics_3tag/real3_dem_report_3tag.json",
            "```",
            "",
        ]
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"report: {args.output}")
    print(f"calibration_ready: {action_ready}")


if __name__ == "__main__":
    main()

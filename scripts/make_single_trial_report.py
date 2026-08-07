#!/usr/bin/env python3
"""Create a Markdown report for a normalized single-trial calibration dataset."""

from __future__ import annotations

import argparse
import csv
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


def load_metric_csv(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8") as f:
        return {row["metric"]: row["value"] for row in csv.DictReader(f)}


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
    scan_correction_path = processed / "scan_correction.json"
    scan_correction = load_json(scan_correction_path) if scan_correction_path.exists() else None
    bridge_check_path = REPO_ROOT / "outputs" / "mass_controlled_bridge_checks" / "free_fall_report.json"
    bridge_check = load_json(bridge_check_path) if bridge_check_path.exists() else None
    terrain_smoke_dirs = [
        REPO_ROOT / "outputs" / "mass_controlled_bridge_checks" / "gravity_terrain_smoke_m0p75",
        REPO_ROOT / "outputs" / "mass_controlled_bridge_checks" / "gravity_terrain_smoke",
        REPO_ROOT / "outputs" / "mass_controlled_bridge_checks" / "gravity_terrain_smoke_m3p0",
    ]
    terrain_smoke_rows = []
    for smoke_dir in terrain_smoke_dirs:
        metrics_path = smoke_dir / "run_metrics.csv"
        if metrics_path.exists():
            metrics = load_metric_csv(metrics_path)
            terrain_smoke_rows.append(
                {
                    "path": smoke_dir.relative_to(REPO_ROOT).as_posix(),
                    "mass_kg": float(metrics["indenter_mass_after_override"]),
                    "sinkage_m": float(metrics["final_actual_depth"]),
                    "under_mean_dz_m": float(metrics["final_under_mean_dz"]),
                    "duration_s": float(metrics["duration"]),
                }
            )
    terrain_smoke_rows.sort(key=lambda row: row["mass_kg"])
    terrain_smoke_monotonic = (
        len(terrain_smoke_rows) == 3
        and terrain_smoke_rows[0]["sinkage_m"] < terrain_smoke_rows[1]["sinkage_m"] < terrain_smoke_rows[2]["sinkage_m"]
    )
    mass_controlled_smoke_metrics_path = (
        REPO_ROOT / "outputs" / "mass_controlled_bridge_checks" / "mass_controlled_terrain_smoke_cpu_capped" / "run_metrics.csv"
    )
    mass_controlled_smoke = load_metric_csv(mass_controlled_smoke_metrics_path) if mass_controlled_smoke_metrics_path.exists() else None
    mass_controlled_long_metrics_path = (
        REPO_ROOT / "outputs" / "mass_controlled_bridge_checks" / "mass_controlled_terrain_cuda_longer" / "run_metrics.csv"
    )
    mass_controlled_long = load_metric_csv(mass_controlled_long_metrics_path) if mass_controlled_long_metrics_path.exists() else None
    mass_controlled_loaded1s_metrics_path = (
        REPO_ROOT / "outputs" / "mass_controlled_bridge_checks" / "mass_controlled_terrain_cuda_loaded1s" / "run_metrics.csv"
    )
    mass_controlled_loaded1s = (
        load_metric_csv(mass_controlled_loaded1s_metrics_path) if mass_controlled_loaded1s_metrics_path.exists() else None
    )
    settling_diagnostic_metrics_path = (
        REPO_ROOT
        / "outputs"
        / "mass_controlled_bridge_checks"
        / "mass_controlled_terrain_cuda_settling_diagnostic_1s"
        / "run_metrics.csv"
    )
    settling_diagnostic = load_metric_csv(settling_diagnostic_metrics_path) if settling_diagnostic_metrics_path.exists() else None
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
        "The real-data preprocessing layer is implemented. Full Genesis parameter search is blocked until footprint/static-border review, final two-view noise, and the mass-controlled Genesis terrain-runner gates are complete.",
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
        "data/single_trial_real3/processed/delta_h_real_corrected.npz",
        "data/single_trial_real3/processed/valid_mask.npz",
        "data/single_trial_real3/processed/noise_stats.json",
        "data/single_trial_real3/processed/scan_correction.json",
        "data/single_trial_real3/processed/scan_correction_footprint_diagnostic.png",
        "```",
        "",
    ]
    if scan_correction is not None:
        lines.extend(
            [
                "## Static-Border Scan Correction",
                "",
                "A provisional plane bias was fit using only an assumed undeformed outer border. This closes the mechanical preprocessing step, but the static-border assumption still needs visual review before real calibration.",
                "",
                "Raw delta stats:",
                "",
                metric_table(scan_correction["raw_delta_stats"]),
                "",
                "Plane-corrected delta stats:",
                "",
                metric_table(scan_correction["plane_corrected_delta_stats"]),
                "",
                "Coverage:",
                "",
                f"- Footprint valid fraction: `{scan_correction['coverage']['footprint_valid_fraction']:.3f}`.",
                f"- Radial-region valid fraction: `{scan_correction['coverage']['radial_valid_fraction']:.3f}`.",
                f"- Static-border valid fraction: `{scan_correction['coverage']['static_valid_fraction']:.3f}`.",
                f"- First-contact height, 99th percentile in footprint: `{scan_correction['first_contact']['height_m']:.9g}` m.",
                f"- Zero-clearance cylinder center z: `{scan_correction['first_contact']['cylinder_center_z_m_for_zero_clearance']:.9g}` m.",
                f"- Diagnostic PNG: `data/single_trial_real3/processed/scan_correction_footprint_diagnostic.png`.",
                "",
            ]
        )
    if bridge_check is not None:
        lines.extend(
            [
                "## Mass-Controlled Genesis Checks",
                "",
                f"- Free-fall status: `{bridge_check['status']}`.",
                f"- Runtime mass after override: `{bridge_check['mass']['after_override_kg']:.9g}` kg.",
                f"- Fitted vertical acceleration: `{bridge_check['free_fall']['fitted_acceleration_z_mps2']:.9g}` m/s^2.",
                f"- Gravity relative error: `{bridge_check['free_fall']['relative_error']:.3g}`.",
                f"- Runtime inertia diagonal: `{bridge_check['inertia']['genesis_runtime_diag_kg_m2']}` kg m^2.",
                f"- Check artifact: `outputs/mass_controlled_bridge_checks/free_fall_report.json`.",
                "",
                "This validates a dynamic cylinder under gravity and runtime mass/inertia setup. It does not validate two-way rigid-MPM terrain contact.",
                "",
            ]
        )
    if terrain_smoke_rows:
        lines.extend(["## Short Terrain Gravity Smoke", ""])
        lines.extend(["| Mass kg | Sinkage m | Under-disk mean dz m | Duration s | Output |", "|---:|---:|---:|---:|---|"])
        for row in terrain_smoke_rows:
            lines.append(
                f"| {row['mass_kg']:.3g} | {row['sinkage_m']:.9g} | {row['under_mean_dz_m']:.9g} | {row['duration_s']:.9g} | `{row['path']}` |"
            )
        lines.extend(
            [
                "",
                f"- Short-run mass monotonicity: `{'pass' if terrain_smoke_monotonic else 'not-pass'}`.",
                "",
                "This is only a short `0.04 s` smoke using the existing gravity control path. It shows mass affects sinkage and terrain particles move, but it does not prove loaded equilibrium, removal, no-cylinder drift, or complete state restoration.",
                "",
            ]
        )
    if mass_controlled_smoke is not None:
        lines.extend(
            [
                "## Mass-Controlled Terrain Runner Smoke",
                "",
                f"- Output: `outputs/mass_controlled_bridge_checks/mass_controlled_terrain_smoke_cpu_capped`.",
                f"- Loaded termination: `{mass_controlled_smoke['loaded_termination_reason']}` after `{mass_controlled_smoke['loaded_duration']}` s.",
                f"- Loaded depth: `{float(mass_controlled_smoke['loaded_depth']):.9g}` m.",
                f"- Removal capped: `{mass_controlled_smoke['removal_capped']}`.",
                f"- Post-removal termination: `{mass_controlled_smoke['post_removal_termination_reason']}` after `{mass_controlled_smoke['post_removal_duration']}` s.",
                f"- Final depth relative to initial center: `{float(mass_controlled_smoke['final_depth']):.9g}` m.",
                "",
                "This validates the load/remove/post-settle phase machine and artifact writing. It is intentionally short and capped, so it does not close the equilibrium/removal validation gate.",
                "",
            ]
        )
    if mass_controlled_long is not None:
        lines.extend(
            [
                "## Longer CUDA Mass-Controlled Rollout",
                "",
                f"- Output: `outputs/mass_controlled_bridge_checks/mass_controlled_terrain_cuda_longer`.",
                f"- Loaded termination: `{mass_controlled_long['loaded_termination_reason']}` after `{mass_controlled_long['loaded_duration']}` s.",
                f"- Loaded depth: `{float(mass_controlled_long['loaded_depth']):.9g}` m.",
                f"- Removal capped: `{mass_controlled_long['removal_capped']}`.",
                f"- Post-removal termination: `{mass_controlled_long['post_removal_termination_reason']}` after `{mass_controlled_long['post_removal_duration']}` s.",
                f"- Final under-disk mean dz: `{float(mass_controlled_long['final_under_mean_dz']):.9g}` m.",
                f"- Total wall time: `{float(mass_controlled_long['total_wall_seconds']):.3f}` s.",
                "",
                "This proves the uncapped physical lift path runs on CUDA. Loaded equilibrium still timed out under the current `0.25 s` limit.",
                "",
            ]
        )
    if mass_controlled_loaded1s is not None:
        lines.extend(
            [
                "## Extended CUDA Loaded-Settling Check",
                "",
                f"- Output: `outputs/mass_controlled_bridge_checks/mass_controlled_terrain_cuda_loaded1s`.",
                f"- Loaded termination: `{mass_controlled_loaded1s['loaded_termination_reason']}` after `{mass_controlled_loaded1s['loaded_duration']}` s.",
                f"- Loaded depth: `{float(mass_controlled_loaded1s['loaded_depth']):.9g}` m.",
                "- Final loaded cylinder speed: `0.000292996793` m/s.",
                "- Final local p99 particle speed: `0.000672453374` m/s.",
                f"- Removal capped: `{mass_controlled_loaded1s['removal_capped']}`.",
                f"- Post-removal termination: `{mass_controlled_loaded1s['post_removal_termination_reason']}` after `{mass_controlled_loaded1s['post_removal_duration']}` s.",
                f"- Final under-disk mean dz: `{float(mass_controlled_loaded1s['final_under_mean_dz']):.9g}` m.",
                f"- Total wall time: `{float(mass_controlled_loaded1s['total_wall_seconds']):.3f}` s.",
                "",
                "The extra loaded time did not materially change penetration, but the local p99 particle-speed criterion remained above its `0.0005 m/s` threshold. The runner therefore cannot yet claim loaded equilibrium; threshold sensitivity and a settled mass-monotonicity check remain required.",
                "",
            ]
        )
    if settling_diagnostic is not None:
        lines.extend(
            [
                "## Loaded-Settling Percentile Diagnostic",
                "",
                "- Output: `outputs/mass_controlled_bridge_checks/mass_controlled_terrain_cuda_settling_diagnostic_1s`.",
                f"- Trailing depth window: `{settling_diagnostic['loaded_depth_window_s']}` s.",
                f"- Penetration drift in that window: `{float(settling_diagnostic['loaded_depth_drift_last_window']):.9g}` m.",
                f"- Final local p50/p90/p95/p99 particle speeds: `{float(settling_diagnostic['loaded_final_particle_speed_p50']):.9g}`, `{float(settling_diagnostic['loaded_final_particle_speed_p90']):.9g}`, `{float(settling_diagnostic['loaded_final_particle_speed_p95']):.9g}`, `{float(settling_diagnostic['loaded_final_particle_speed_p99']):.9g}` m/s.",
                "",
                "The p95 statistic and cylinder speed satisfy the current `0.0005 m/s` threshold in the stable-depth tail, while p99 does not. This is evidence for a threshold-sensitivity study across masses, not a basis for changing the protocol from this single run.",
                "",
            ]
        )
    lines.extend(
        [
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
        "- Static-border plane correction and footprint coverage diagnostics.",
        "- Provisional noise statistics.",
        "- Report generation.",
        "- Corrected cylinder action template: `0.14605 m` is diameter and `0.073025 m` is radius.",
        "",
        "Blocked before Genesis search:",
        "",
    ]
    )
    completed_bridge_fields = set()
    if bridge_check is not None and bridge_check.get("status") == "pass":
        completed_bridge_fields.update({"mass/inertia application check", "free-fall gravity check"})
    if mass_controlled_long is not None or mass_controlled_loaded1s is not None or settling_diagnostic is not None:
        completed_bridge_fields.add("Genesis mass-controlled action mode")
    for field in summary["blocking_fields"]:
        if field in completed_bridge_fields:
            continue
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

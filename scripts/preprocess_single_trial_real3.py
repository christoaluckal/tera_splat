#!/usr/bin/env python3
"""Normalize RealSense real3 DEM artifacts into the single-trial contract."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
PHYSICAL_ROOT = REPO_ROOT.parent
DEFAULT_SOURCE = PHYSICAL_ROOT / "lamp" / "ros2_ws" / "src" / "realsense_splat"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "single_trial_real3"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--primary-cell-size",
        choices=("0.005", "0.0025"),
        default="0.005",
        help="Center-ROI DEM resolution used as the primary calibration target.",
    )
    parser.add_argument("--copy-plys", action="store_true", help="Copy center ROI PLYs into processed/.")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def yaml_scalar(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, str):
        return value
    return json.dumps(value)


def write_manifest(path: Path, payload: dict) -> None:
    lines = []
    for key, value in payload.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for child_key, child_value in value.items():
                lines.append(f"  {child_key}: {yaml_scalar(child_value)}")
        else:
            lines.append(f"{key}: {yaml_scalar(value)}")
    write_text(path, "\n".join(lines) + "\n")


def stats_for_delta(delta: np.ndarray, cell_size: float) -> dict:
    finite = np.isfinite(delta)
    values = delta[finite]
    neg = values[values < 0.0]
    pos = values[values > 0.0]
    area = cell_size * cell_size
    return {
        "valid_cells": int(values.size),
        "valid_area_m2": float(values.size * area),
        "mean_change_m": float(np.mean(values)),
        "median_change_m": float(np.median(values)),
        "p01_m": float(np.percentile(values, 1)),
        "p05_m": float(np.percentile(values, 5)),
        "p25_m": float(np.percentile(values, 25)),
        "p75_m": float(np.percentile(values, 75)),
        "p95_m": float(np.percentile(values, 95)),
        "p99_m": float(np.percentile(values, 99)),
        "net_volume_m3": float(np.nansum(values) * area),
        "cut_volume_m3": float(np.sum(neg) * area),
        "fill_volume_m3": float(np.sum(pos) * area),
    }


def grid_centers(shape: tuple[int, int], cell_size: float, bounds_xy: list[float]) -> tuple[np.ndarray, np.ndarray]:
    x_min, _, y_min, _ = bounds_xy
    xs = x_min + (np.arange(shape[1]) + 0.5) * cell_size
    ys = y_min + (np.arange(shape[0]) + 0.5) * cell_size
    return np.meshgrid(xs, ys)


def fit_plane(xs: np.ndarray, ys: np.ndarray, values: np.ndarray, mask: np.ndarray) -> dict:
    if int(mask.sum()) < 3:
        raise ValueError("Need at least 3 valid static-border cells to fit scan-bias plane")
    design = np.column_stack([xs[mask], ys[mask], np.ones(int(mask.sum()))])
    coeff, *_ = np.linalg.lstsq(design, values[mask], rcond=None)
    a, b, c = [float(v) for v in coeff]
    plane = a * xs + b * ys + c
    residual = np.where(mask, values - plane, np.nan)
    return {
        "a": a,
        "b": b,
        "c": c,
        "plane": plane,
        "static_residual_median_m": float(np.nanmedian(residual)),
        "static_residual_mad_m": float(np.nanmedian(np.abs(residual[mask] - np.nanmedian(residual)))),
    }


def save_scan_diagnostic_png(
    path: Path,
    *,
    raw_delta: np.ndarray,
    corrected_delta: np.ndarray,
    valid_mask: np.ndarray,
    footprint_mask: np.ndarray,
    radial_mask: np.ndarray,
    static_mask: np.ndarray,
    bounds_xy: list[float],
) -> None:
    extent = [bounds_xy[0], bounds_xy[1], bounds_xy[2], bounds_xy[3]]
    vmax = float(np.nanpercentile(np.abs(raw_delta), 98))
    vmax = max(vmax, 1e-6)
    overlay = np.zeros((*valid_mask.shape, 3), dtype=np.float32)
    overlay[valid_mask] = (0.25, 0.25, 0.25)
    overlay[radial_mask] = (0.1, 0.35, 0.9)
    overlay[static_mask] = (0.1, 0.75, 0.2)
    overlay[footprint_mask] = (0.9, 0.15, 0.1)

    path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
    for ax, image, title in [
        (axes[0], raw_delta, "raw delta_h"),
        (axes[1], corrected_delta, "static-border corrected delta_h"),
    ]:
        im = ax.imshow(image, origin="lower", extent=extent, vmin=-vmax, vmax=vmax, cmap="coolwarm")
        ax.set_title(title)
        ax.set_xlabel("x [m]")
        ax.set_ylabel("y [m]")
        fig.colorbar(im, ax=ax, shrink=0.8)
    axes[2].imshow(overlay, origin="lower", extent=extent)
    axes[2].set_title("red footprint, blue radial, green static")
    axes[2].set_xlabel("x [m]")
    axes[2].set_ylabel("y [m]")
    fig.savefig(path, dpi=160)
    plt.close(fig)


def save_height_npz(path: Path, *, height: np.ndarray, cell_size: float, bounds_xy: list[float]) -> None:
    x_min, x_max, y_min, y_max = bounds_xy
    height = height.astype(np.float64)
    x_centers = x_min + (np.arange(height.shape[1]) + 0.5) * cell_size
    y_centers = y_min + (np.arange(height.shape[0]) + 0.5) * cell_size
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        height=height,
        cell_size_m=np.asarray(cell_size),
        bounds_xy_m=np.asarray(bounds_xy, dtype=np.float64),
        x_centers_m=x_centers,
        y_centers_m=y_centers,
    )


def copy_if_exists(src: Path, dst: Path) -> str | None:
    if not src.exists():
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return str(dst)


def main() -> None:
    args = parse_args()
    source_root = args.source_root.resolve()
    compare_dir = source_root / "episodes" / "real3_compare_metrics_3tag"
    center_dir = compare_dir / "center_1ft_fine_dem"
    processed = args.output_dir / "processed"

    full_report = load_json(compare_dir / "real3_dem_report_3tag.json")
    center_report = load_json(center_dir / "center_1ft_fine_dem_report.json")
    cropped_report = load_json(center_dir / "center_1ft_cropped_ply_report.json")

    cell_key = f"{args.primary_cell_size}m"
    cell_size = float(args.primary_cell_size)
    bounds_xy = center_report["roi"]["bounds_xy_m"]

    s0 = np.load(center_dir / f"before_center_1ft_dem_{cell_key}.npy")
    s1 = np.load(center_dir / f"after_center_1ft_dem_{cell_key}.npy")
    provided_delta = np.load(center_dir / f"diff_center_1ft_after_minus_before_{cell_key}.npy")
    valid_mask = np.isfinite(s0) & np.isfinite(s1) & np.isfinite(provided_delta)
    computed_delta = np.where(valid_mask, s1 - s0, np.nan)
    xs, ys = grid_centers(s0.shape, cell_size, bounds_xy)
    cylinder_center_xy = np.asarray([0.0, 0.0], dtype=np.float64)
    cylinder_radius_m = 0.073025
    distance_from_center = np.sqrt((xs - cylinder_center_xy[0]) ** 2 + (ys - cylinder_center_xy[1]) ** 2)
    footprint_mask = distance_from_center <= cylinder_radius_m
    radial_mask = (distance_from_center > cylinder_radius_m) & (distance_from_center <= 2.0 * cylinder_radius_m)
    border_width_m = max(0.025, 5.0 * cell_size)
    border_candidate_mask = (
        (xs <= bounds_xy[0] + border_width_m)
        | (xs >= bounds_xy[1] - border_width_m)
        | (ys <= bounds_xy[2] + border_width_m)
        | (ys >= bounds_xy[3] - border_width_m)
    )
    static_candidate_mask = border_candidate_mask & (distance_from_center >= cylinder_radius_m + 0.03)
    static_mask = valid_mask & static_candidate_mask
    plane_fit = fit_plane(xs, ys, computed_delta, static_mask)
    plane_bias = plane_fit["plane"]
    corrected_delta = np.where(valid_mask, computed_delta - plane_bias, np.nan)
    offset_only_c = float(np.nanmedian(computed_delta[static_mask]))
    offset_corrected_delta = np.where(valid_mask, computed_delta - offset_only_c, np.nan)
    footprint_valid = valid_mask & footprint_mask
    radial_valid = valid_mask & radial_mask
    first_contact_height_m = float(np.nanpercentile(s0[footprint_valid], 99.0))
    scan_correction = {
        "method": "static_border_plane_fit",
        "note": (
            "Plane is fit only on valid cells in an assumed undeformed outer border, excluding "
            "the cylinder footprint plus 30 mm. Verify this static-border assumption visually."
        ),
        "cylinder_center_xy_world_m": [float(cylinder_center_xy[0]), float(cylinder_center_xy[1])],
        "cylinder_radius_m": cylinder_radius_m,
        "cylinder_diameter_m": 0.14605,
        "static_border_width_m": border_width_m,
        "static_exclusion_radius_m": cylinder_radius_m + 0.03,
        "plane_bias_model": {
            "delta_h_bias_m": "a*x + b*y + c",
            "a": plane_fit["a"],
            "b": plane_fit["b"],
            "c": plane_fit["c"],
            "static_residual_median_m": plane_fit["static_residual_median_m"],
            "static_residual_mad_m": plane_fit["static_residual_mad_m"],
        },
        "offset_only_bias_m": offset_only_c,
        "coverage": {
            "footprint_total_cells": int(footprint_mask.sum()),
            "footprint_valid_cells": int(footprint_valid.sum()),
            "footprint_valid_fraction": float(footprint_valid.sum() / max(int(footprint_mask.sum()), 1)),
            "radial_total_cells": int(radial_mask.sum()),
            "radial_valid_cells": int(radial_valid.sum()),
            "radial_valid_fraction": float(radial_valid.sum() / max(int(radial_mask.sum()), 1)),
            "static_candidate_cells": int(static_candidate_mask.sum()),
            "static_valid_cells": int(static_mask.sum()),
            "static_valid_fraction": float(static_mask.sum() / max(int(static_candidate_mask.sum()), 1)),
        },
        "first_contact": {
            "surface_statistic": "percentile",
            "percentile": 99.0,
            "height_m": first_contact_height_m,
            "cylinder_center_z_m_for_zero_clearance": first_contact_height_m + 0.0508 / 2.0,
        },
        "raw_delta_stats": stats_for_delta(computed_delta, cell_size),
        "plane_corrected_delta_stats": stats_for_delta(corrected_delta, cell_size),
        "offset_corrected_delta_stats": stats_for_delta(offset_corrected_delta, cell_size),
    }

    save_height_npz(processed / "S0_height.npz", height=s0, cell_size=cell_size, bounds_xy=bounds_xy)
    save_height_npz(processed / "S1_height.npz", height=s1, cell_size=cell_size, bounds_xy=bounds_xy)
    np.savez_compressed(
        processed / "delta_h_real.npz",
        delta_h=computed_delta,
        provided_delta_h=provided_delta,
        valid_mask=valid_mask,
        cell_size_m=np.asarray(cell_size),
        bounds_xy_m=np.asarray(bounds_xy, dtype=np.float64),
    )
    np.savez_compressed(
        processed / "delta_h_real_corrected.npz",
        delta_h=corrected_delta,
        raw_delta_h=computed_delta,
        offset_corrected_delta_h=offset_corrected_delta,
        plane_bias_m=plane_bias,
        valid_mask=valid_mask,
        footprint_mask=footprint_mask,
        radial_mask=radial_mask,
        static_border_mask=static_mask,
        static_candidate_mask=static_candidate_mask,
        cell_size_m=np.asarray(cell_size),
        bounds_xy_m=np.asarray(bounds_xy, dtype=np.float64),
        x_centers_m=xs[0],
        y_centers_m=ys[:, 0],
    )
    np.savez_compressed(processed / "valid_mask.npz", valid_mask=valid_mask)
    write_json(processed / "scan_correction.json", scan_correction)
    save_scan_diagnostic_png(
        processed / "scan_correction_footprint_diagnostic.png",
        raw_delta=computed_delta,
        corrected_delta=corrected_delta,
        valid_mask=valid_mask,
        footprint_mask=footprint_mask,
        radial_mask=radial_mask,
        static_mask=static_mask,
        bounds_xy=bounds_xy,
    )

    # Include the finer DEM as a diagnostic artifact.
    fine_key = "0.0025m"
    fine_s0 = np.load(center_dir / f"before_center_1ft_dem_{fine_key}.npy")
    fine_s1 = np.load(center_dir / f"after_center_1ft_dem_{fine_key}.npy")
    fine_delta = np.load(center_dir / f"diff_center_1ft_after_minus_before_{fine_key}.npy")
    np.savez_compressed(
        processed / "center_fine_0p0025m_diagnostics.npz",
        S0_height=fine_s0,
        S1_height=fine_s1,
        delta_h=fine_delta,
        valid_mask=np.isfinite(fine_s0) & np.isfinite(fine_s1) & np.isfinite(fine_delta),
        cell_size_m=np.asarray(0.0025),
        bounds_xy_m=np.asarray(bounds_xy, dtype=np.float64),
    )

    full_s0 = np.load(compare_dir / "before_dem_3tag.npy")
    full_s1 = np.load(compare_dir / "after_dem_3tag.npy")
    full_s1_icp = np.load(compare_dir / "after_icp_aligned_dem_3tag.npy")
    full_valid = np.isfinite(full_s0) & np.isfinite(full_s1) & np.isfinite(full_s1_icp)
    direct_delta = np.where(full_valid, full_s1 - full_s0, np.nan)
    icp_delta = np.where(full_valid, full_s1_icp - full_s0, np.nan)
    registration_delta = icp_delta - direct_delta
    noise_stats = {
        "source": "derived_from_existing_real3_reports_without_two_view_recompute",
        "icp_final_rmse_m": full_report["icp"]["final_rmse_m"],
        "full_direct_vs_icp_delta_abs_median_m": float(np.nanmedian(np.abs(registration_delta))),
        "full_direct_vs_icp_delta_abs_p95_m": float(np.nanpercentile(np.abs(registration_delta), 95)),
        "recommended_huber_delta_m": float(
            max(full_report["icp"]["final_rmse_m"], np.nanpercentile(np.abs(registration_delta), 95))
        ),
        "note": (
            "This is a provisional scan/registration noise proxy. Replace with two-view disagreement and "
            "static-border residuals before final calibration."
        ),
    }
    write_json(processed / "noise_stats.json", noise_stats)

    copied_plys = {}
    if args.copy_plys:
        copied_plys["S0_fused"] = copy_if_exists(center_dir / "before_center_1ft_fused_points.ply", processed / "S0_fused.ply")
        copied_plys["S1_fused"] = copy_if_exists(center_dir / "after_center_1ft_fused_points.ply", processed / "S1_fused.ply")
        copied_plys["S1_fused_icp_aligned"] = copy_if_exists(
            center_dir / "after_icp_aligned_center_1ft_fused_points.ply",
            processed / "S1_fused_icp_aligned.ply",
        )

    manifest = {
        "trial_id": "real3_single_trial",
        "length_unit": "meter",
        "angle_unit": "degree",
        "world_frame": "bed",
        "camera_frame": "camera_color_optical_frame",
        "depth_scale_m_per_unit": 0.001,
        "height_cell_size_m": cell_size,
        "source_package": str(source_root),
        "source_compare_dir": str(compare_dir),
        "source_center_dir": str(center_dir),
        "primary_target": "center_1ft_dem",
        "calibration_ready": False,
        "roi_world": {
            "x_min": bounds_xy[0],
            "x_max": bounds_xy[1],
            "y_min": bounds_xy[2],
            "y_max": bounds_xy[3],
        },
    }
    write_manifest(args.output_dir / "manifest.yaml", manifest)

    action_text = """tool: cylinder
geometry:
  diameter_m: 0.14605
  radius_m: 0.073025
  height_m: 0.0508
rigid_body:
  mass_kg: 1.5
  equivalent_uniform_density_kg_m3: 1762.522
  inertia_model: uniform_solid_cylinder_approximation
  inertia_diagonal_kg_m2: [0.002322324, 0.002322324, 0.003999488]
contact_center_xy_world_m: [0.0, 0.0]
placement:
  mode: mass_controlled
  initial_condition: first_contact
  initial_linear_velocity_mps: [0.0, 0.0, 0.0]
  initial_angular_velocity_radps: [0.0, 0.0, 0.0]
  release_under_gravity: true
  additional_applied_force_n: [0.0, 0.0, 0.0]
first_contact:
  surface_statistic: percentile
  percentile: 99.0
  nominal_clearance_m: 0.0
loaded_settling:
  max_time_s: 5.0
  cylinder_speed_threshold_mps: 0.0005
  local_particle_speed_percentile: 99
  particle_speed_threshold_mps: 0.0005
  required_duration_s: 0.25
removal:
  mode: kinematic_lift_after_loaded_equilibrium
  upward_speed_mps: 0.005
  clearance_above_surface_m: 0.010
post_removal_settling:
  max_time_s: 5.0
  local_particle_speed_percentile: 99
  particle_speed_threshold_mps: 0.0005
  required_duration_s: 0.25
calibration_ready: false
notes:
  - 0.14605 m is cylinder diameter; radius is 0.073025 m.
  - The real trial was mass-controlled gravitational loading, not prescribed indentation depth.
  - contact_center_xy_world_m assumes the bed-frame origin is the physical bed center; verify by footprint overlay before calibration.
  - Settling/removal thresholds are fixed simulation assumptions and need sensitivity tests.
"""
    write_text(args.output_dir / "action.yaml", action_text)

    summary = {
        "trial_dir": str(args.output_dir),
        "primary_cell_size_m": cell_size,
        "primary_bounds_xy_m": bounds_xy,
        "primary_shape": list(s0.shape),
        "valid_cells": int(valid_mask.sum()),
        "provided_delta_matches_computed_nanmax_abs_m": float(np.nanmax(np.abs(provided_delta - computed_delta))),
        "primary_delta_stats": stats_for_delta(computed_delta, cell_size),
        "realsense_center_report": center_report["runs"][cell_key],
        "realsense_full_report": {
            "direct_dem": full_report["direct_dem"],
            "icp_aligned_dem": full_report["icp_aligned_dem"],
            "icp": full_report["icp"],
        },
        "noise_stats": noise_stats,
        "scan_correction": scan_correction,
        "copied_plys": copied_plys,
        "blocking_fields": [
            "two-view height exports/noise estimate",
            "Genesis mass-controlled action mode",
            "mass/inertia application check",
            "free-fall gravity check",
            "two-way rigid-MPM contact check",
            "settled/equilibrium mass monotonicity check",
            "loaded settling termination check",
            "post-removal settling termination check",
            "initial simulated S0 projection/footprint check",
            "complete MPM state restore check",
            "no-cylinder drift check",
            "synthetic 3x3 recovery check",
        ],
    }
    write_json(processed / "preprocess_summary.json", summary)
    write_json(processed / "source_center_1ft_fine_dem_report.json", center_report)
    write_json(processed / "source_center_1ft_cropped_ply_report.json", cropped_report)
    write_json(processed / "source_real3_dem_report_3tag.json", full_report)

    print(f"trial_dir: {args.output_dir}")
    print(f"primary_target: center_1ft {cell_size} m DEM")
    print(f"valid_cells: {int(valid_mask.sum())}")
    print(f"median_delta_m: {summary['primary_delta_stats']['median_change_m']}")
    print(f"corrected_median_delta_m: {scan_correction['plane_corrected_delta_stats']['median_change_m']}")
    print(f"cut_volume_m3: {summary['primary_delta_stats']['cut_volume_m3']}")
    print(f"recommended_huber_delta_m: {noise_stats['recommended_huber_delta_m']}")


if __name__ == "__main__":
    main()

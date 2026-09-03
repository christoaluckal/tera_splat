#!/usr/bin/env python3
"""Diagnose Chrono--Genesis mismatch without fitting a discrepancy network.

The report separates loaded and residual objectives, exposes their Pareto
trade-off, localizes DEM/recovery error, and summarizes Genesis MPM internal
state.  Optional sensitivity trials add the controlled resolution/timestep
matrix to the same report.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Iterable

import matplotlib.pyplot as plt
import numpy as np
import yaml


PHASES = ("loaded", "residual")
STATE_PHASES = ("initial", "loaded", "final")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chrono-episode", type=Path, required=True)
    parser.add_argument("--raw-trial", type=Path, required=True)
    parser.add_argument(
        "--study-dir",
        type=Path,
        action="append",
        default=[],
        help="Study or parent directory containing result.json files; repeat as needed.",
    )
    parser.add_argument(
        "--sensitivity-trial",
        action="append",
        default=[],
        metavar="LABEL=TRIAL_DIR",
        help="Completed numerical sensitivity trial; repeat for each matrix cell.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dpi", type=int, default=180)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: Iterable[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = rows[0].keys() if rows else ()
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(rows)


def comparison_grid(spec: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, tuple[float, float, float, float]]:
    rows, columns = (int(value) for value in spec["shape"])
    spacing = float(spec["spacing_m"])
    origin_x, origin_y = (float(value) for value in spec["origin_xy_m"])
    xs = origin_x + spacing * np.arange(columns)
    ys = origin_y + spacing * np.arange(rows)
    grid_x, grid_y = np.meshgrid(xs, ys, indexing="xy")
    extent = (
        origin_x - 0.5 * spacing,
        origin_x + (columns - 0.5) * spacing,
        origin_y - 0.5 * spacing,
        origin_y + (rows - 0.5) * spacing,
    )
    return grid_x, grid_y, extent


def pareto_indices(points: np.ndarray) -> np.ndarray:
    """Return indices not dominated for a minimization problem."""
    points = np.asarray(points, dtype=float)
    if points.ndim != 2:
        raise ValueError("points must be a two-dimensional array")
    keep = np.ones(points.shape[0], dtype=bool)
    for index, point in enumerate(points):
        dominated = np.all(points <= point, axis=1) & np.any(points < point, axis=1)
        dominated[index] = False
        keep[index] = not np.any(dominated)
    return np.flatnonzero(keep)


def result_row(path: Path, result: dict[str, Any]) -> dict[str, Any]:
    candidate = result["candidate"]
    initialization = result.get("candidate_initialization", {})
    acceptance = result.get("phase_acceptance", {})
    return {
        "result_path": str(path.resolve()),
        "valid": bool(result.get("valid", False)),
        "objective_mm": 1000.0 * float(result["objective_m"]),
        "loaded_rmse_mm": 1000.0 * float(result["loaded_rmse_m"]),
        "residual_footprint_rmse_mm": 1000.0 * float(result["residual_footprint_rmse_m"]),
        "residual_footprint_mean_signed_mm": 1000.0 * float(result["residual_footprint_mean_signed_m"]),
        "log10_E": float(candidate["log10_E"]),
        "E_pa": float(candidate.get("E_pa", 10.0 ** float(candidate["log10_E"]))),
        "phi_deg": float(candidate["phi_deg"]),
        "nu": float(candidate["nu"]),
        "particle_spacing_m": float(candidate["particle_spacing_m"]),
        "particle_size_ratio": float(candidate["particle_size_ratio"]),
        "candidate_h0_rmse_mm": 1000.0 * float(initialization.get("h0_rmse_m", float("nan"))),
        "loaded_acceptance_mode": acceptance.get("loaded", {}).get("mode", "unknown"),
    }


def collect_observations(search_roots: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_paths: set[Path] = set()
    for root in search_roots:
        root = root.resolve()
        candidates = [root / "result.json"] if (root / "result.json").is_file() else root.rglob("result.json")
        for path in candidates:
            path = path.resolve()
            if path in seen_paths:
                continue
            seen_paths.add(path)
            result = load_json(path)
            required = ("objective_m", "loaded_rmse_m", "residual_footprint_rmse_m", "candidate")
            if result.get("valid", False) and all(key in result for key in required):
                rows.append(result_row(path, result))

    # Replays of the exact same candidate are useful for repeatability but must
    # not artificially thicken the calibration Pareto set.
    best_by_candidate: dict[tuple[float, ...], dict[str, Any]] = {}
    for row in rows:
        key = tuple(
            round(float(row[name]), 12)
            for name in ("log10_E", "phi_deg", "nu", "particle_spacing_m", "particle_size_ratio")
        )
        incumbent = best_by_candidate.get(key)
        if incumbent is None or float(row["objective_mm"]) < float(incumbent["objective_mm"]):
            best_by_candidate[key] = row
    return sorted(best_by_candidate.values(), key=lambda row: float(row["objective_mm"]))


def radial_statistics(
    radius_m: np.ndarray,
    values: dict[str, np.ndarray],
    valid: np.ndarray,
    bin_width_m: float,
) -> list[dict[str, Any]]:
    maximum = float(np.max(radius_m[valid]))
    edges = np.arange(0.0, maximum + bin_width_m, bin_width_m)
    if edges.size < 2 or edges[-1] <= maximum:
        edges = np.append(edges, maximum + bin_width_m)
    rows: list[dict[str, Any]] = []
    for lower, upper in zip(edges[:-1], edges[1:]):
        mask = valid & (radius_m >= lower) & (radius_m < upper)
        count = int(np.count_nonzero(mask))
        if count == 0:
            continue
        row: dict[str, Any] = {
            "radius_lower_m": float(lower),
            "radius_upper_m": float(upper),
            "radius_center_m": float(0.5 * (lower + upper)),
            "count": count,
        }
        for name, array in values.items():
            sample = np.asarray(array)[mask]
            row[f"{name}_mean"] = float(np.mean(sample))
            row[f"{name}_rmse"] = float(np.sqrt(np.mean(sample * sample)))
            row[f"{name}_p05"] = float(np.quantile(sample, 0.05))
            row[f"{name}_median"] = float(np.median(sample))
            row[f"{name}_p95"] = float(np.quantile(sample, 0.95))
        rows.append(row)
    return rows


def load_response_data(chrono_dir: Path, bridge_dir: Path) -> dict[str, Any]:
    chrono_manifest = yaml.safe_load((chrono_dir / "manifest.yaml").read_text(encoding="utf-8"))
    genesis_manifest = load_json(bridge_dir / "manifest.json")
    if chrono_manifest["heightmap"] != genesis_manifest["heightmap"]:
        raise ValueError("Chrono and Genesis manifests use different comparison grids")
    action = load_json(chrono_dir / "action.json")
    grid_x, grid_y, extent = comparison_grid(chrono_manifest["heightmap"])
    valid = np.load(chrono_dir / "valid_heightmap_mask.npy").astype(bool)
    valid &= np.load(bridge_dir / "valid_heightmap_mask.npy").astype(bool)
    center_x, center_y = (float(value) for value in action["center_xy_m"])
    radius = np.hypot(grid_x - center_x, grid_y - center_y)
    footprint = radius <= float(action["radius_m"])
    chrono_initial = np.load(chrono_dir / "initial_heightmap_m.npy")
    genesis_initial = np.load(bridge_dir / "initial_heightmap_m.npy")
    phases: dict[str, dict[str, np.ndarray]] = {}
    for phase in PHASES:
        chrono = 1000.0 * (np.load(chrono_dir / f"{phase}_heightmap_m.npy") - chrono_initial)
        genesis = 1000.0 * (np.load(bridge_dir / f"{phase}_heightmap_m.npy") - genesis_initial)
        phases[phase] = {"chrono_mm": chrono, "genesis_mm": genesis, "error_mm": genesis - chrono}
    phases["recovery"] = {
        "chrono_mm": phases["residual"]["chrono_mm"] - phases["loaded"]["chrono_mm"],
        "genesis_mm": phases["residual"]["genesis_mm"] - phases["loaded"]["genesis_mm"],
    }
    phases["recovery"]["error_mm"] = phases["recovery"]["genesis_mm"] - phases["recovery"]["chrono_mm"]
    return {
        "manifest": chrono_manifest,
        "action": action,
        "grid_x": grid_x,
        "grid_y": grid_y,
        "extent": extent,
        "valid": valid,
        "footprint": footprint,
        "radius_m": radius,
        "phases": phases,
    }


def response_summary(data: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    valid = data["valid"]
    footprint = data["footprint"]
    spacing = float(data["manifest"]["heightmap"]["spacing_m"])
    radial_rows: list[dict[str, Any]] = []
    for phase in (*PHASES, "recovery"):
        phase_rows = radial_statistics(
            data["radius_m"],
            {
                "chrono_response_mm": data["phases"][phase]["chrono_mm"],
                "genesis_response_mm": data["phases"][phase]["genesis_mm"],
                "error_mm": data["phases"][phase]["error_mm"],
            },
            valid,
            spacing,
        )
        for row in phase_rows:
            row["phase"] = phase
            row["inside_action_radius"] = bool(float(row["radius_center_m"]) <= float(data["action"]["radius_m"]))
        radial_rows.extend(phase_rows)

    center_x, center_y = (float(value) for value in data["action"]["center_xy_m"])
    xs = data["grid_x"][0, :]
    ys = data["grid_y"][:, 0]
    row_index = int(np.argmin(np.abs(ys - center_y)))
    column_index = int(np.argmin(np.abs(xs - center_x)))
    cross_rows: list[dict[str, Any]] = []
    for phase in (*PHASES, "recovery"):
        phase_data = data["phases"][phase]
        for axis, coordinates, indexer in (
            ("x", xs, (row_index, slice(None))),
            ("y", ys, (slice(None), column_index)),
        ):
            line_valid = valid[indexer]
            for index in np.flatnonzero(line_valid):
                cross_rows.append(
                    {
                        "phase": phase,
                        "axis": axis,
                        "coordinate_m": float(coordinates[index]),
                        "chrono_response_mm": float(phase_data["chrono_mm"][indexer][index]),
                        "genesis_response_mm": float(phase_data["genesis_mm"][indexer][index]),
                        "error_mm": float(phase_data["error_mm"][indexer][index]),
                    }
                )

    metric_rows: list[dict[str, Any]] = []
    for phase in (*PHASES, "recovery"):
        mask = valid & footprint if phase in ("residual", "recovery") else valid
        error = data["phases"][phase]["error_mm"][mask]
        metric_rows.append(
            {
                "phase": phase,
                "scope": "action_footprint" if phase in ("residual", "recovery") else "common_support",
                "cells": int(error.size),
                "rmse_mm": float(np.sqrt(np.mean(error * error))),
                "mae_mm": float(np.mean(np.abs(error))),
                "mean_signed_mm": float(np.mean(error)),
                "p05_signed_mm": float(np.quantile(error, 0.05)),
                "p95_signed_mm": float(np.quantile(error, 0.95)),
            }
        )
    return radial_rows, cross_rows, metric_rows


def render_spatial_diagnosis(path: Path, data: dict[str, Any], radial_rows: list[dict[str, Any]]) -> None:
    figure, axes = plt.subplots(2, 3, figsize=(16, 9), layout="constrained")
    errors = [data["phases"][phase]["error_mm"][data["valid"]] for phase in (*PHASES, "recovery")]
    limit = max(float(np.quantile(np.abs(np.concatenate(errors)), 0.995)), 1.0)
    image = None
    for column, phase in enumerate((*PHASES, "recovery")):
        image = axes[0, column].imshow(
            np.ma.array(data["phases"][phase]["error_mm"], mask=~data["valid"]),
            extent=data["extent"],
            origin="lower",
            cmap="RdBu_r",
            vmin=-limit,
            vmax=limit,
            interpolation="nearest",
        )
        axes[0, column].set_title(f"{phase.capitalize()} error\nGenesis − Chrono")
        axes[0, column].set_aspect("equal")
        axes[0, column].set_xlabel("bed x (m)")
        axes[0, column].set_ylabel("bed y (m)")
    figure.colorbar(image, ax=list(axes[0, :]), label="response error (mm)", shrink=0.8)

    for column, phase in enumerate((*PHASES, "recovery")):
        selected = [row for row in radial_rows if row["phase"] == phase]
        radius = np.asarray([row["radius_center_m"] for row in selected])
        axes[1, column].plot(radius, [row["chrono_response_mm_mean"] for row in selected], label="Chrono")
        axes[1, column].plot(radius, [row["genesis_response_mm_mean"] for row in selected], label="Genesis")
        axes[1, column].axvline(float(data["action"]["radius_m"]), color="black", linestyle="--", linewidth=1)
        axes[1, column].set_title(f"{phase.capitalize()} radial mean")
        axes[1, column].set_xlabel("radius from action center (m)")
        axes[1, column].set_ylabel("surface response (mm)")
        axes[1, column].grid(alpha=0.25)
        axes[1, column].legend()
    figure.suptitle("Chrono–Genesis spatial and recovery mismatch", fontsize=14)
    figure.savefig(path, dpi=180, facecolor="white")
    plt.close(figure)


def state_arrays(path: Path) -> dict[str, np.ndarray]:
    with np.load(path) as archive:
        arrays = {name: np.asarray(archive[name]) for name in ("pos", "F", "Jp", "active")}
    for name, array in arrays.items():
        if array.ndim >= 1 and array.shape[0] == 1:
            arrays[name] = array[0]
    arrays["active"] = arrays["active"].astype(bool).reshape(-1)
    arrays["Jp"] = arrays["Jp"].reshape(-1)
    return arrays


def quantile_columns(prefix: str, values: np.ndarray) -> dict[str, float]:
    return {
        f"{prefix}_mean": float(np.mean(values)),
        f"{prefix}_p01": float(np.quantile(values, 0.01)),
        f"{prefix}_median": float(np.median(values)),
        f"{prefix}_p95": float(np.quantile(values, 0.95)),
        f"{prefix}_p99": float(np.quantile(values, 0.99)),
        f"{prefix}_max": float(np.max(values)),
    }


def hidden_state_summary(raw_dir: Path, action: dict[str, Any], spacing_m: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    states = {phase: state_arrays(raw_dir / f"mpm_state_{phase}.npz") for phase in STATE_PHASES}
    particle_count = states["initial"]["pos"].shape[0]
    if any(state["pos"].shape[0] != particle_count for state in states.values()):
        raise ValueError("MPM particle identities are not consistent across state snapshots")
    initial = states["initial"]
    center_x, center_y = (float(value) for value in action["center_xy_m"])
    radius = np.hypot(initial["pos"][:, 0] - center_x, initial["pos"][:, 1] - center_y)
    summary_rows: list[dict[str, Any]] = []
    radial_rows: list[dict[str, Any]] = []
    for phase, state in states.items():
        active = initial["active"] & state["active"]
        displacement_mm = 1000.0 * (state["pos"] - initial["pos"])
        det_f = np.linalg.det(state["F"])
        delta_jp = state["Jp"] - initial["Jp"]
        delta_det_f = det_f - np.linalg.det(initial["F"])
        row: dict[str, Any] = {
            "phase": phase,
            "active_particles": int(np.count_nonzero(active)),
            "jp_nonzero_particles": int(np.count_nonzero(active & (np.abs(state["Jp"]) > 1.0e-12))),
            "delta_jp_nonzero_particles": int(np.count_nonzero(active & (np.abs(delta_jp) > 1.0e-12))),
        }
        row.update(quantile_columns("jp", state["Jp"][active]))
        row.update(quantile_columns("delta_jp", delta_jp[active]))
        row.update(quantile_columns("det_f", det_f[active]))
        row.update(quantile_columns("delta_det_f", delta_det_f[active]))
        row.update(quantile_columns("displacement_mm", np.linalg.norm(displacement_mm[active], axis=1)))
        row.update(quantile_columns("vertical_displacement_mm", displacement_mm[active, 2]))
        summary_rows.append(row)

        phase_radial = radial_statistics(
            radius,
            {
                "jp": state["Jp"],
                "delta_jp": delta_jp,
                "det_f": det_f,
                "delta_det_f": delta_det_f,
                "vertical_displacement_mm": displacement_mm[:, 2],
            },
            active,
            spacing_m,
        )
        for radial in phase_radial:
            radial["phase"] = phase
            radial["inside_action_radius"] = bool(float(radial["radius_center_m"]) <= float(action["radius_m"]))
        radial_rows.extend(phase_radial)
    return summary_rows, radial_rows


def render_hidden_state(path: Path, rows: list[dict[str, Any]], action_radius_m: float) -> None:
    figure, axes = plt.subplots(2, 2, figsize=(12, 8), layout="constrained")
    plot_specs = (
        ("delta_jp_p95", "95th percentile ΔJp"),
        ("delta_det_f_median", "median Δdet(F)"),
        ("vertical_displacement_mm_mean", "mean vertical displacement (mm)"),
        ("vertical_displacement_mm_p05", "5th percentile vertical displacement (mm)"),
    )
    for axis, (column, title) in zip(axes.flat, plot_specs):
        for phase in STATE_PHASES:
            selected = [row for row in rows if row["phase"] == phase]
            axis.plot(
                [row["radius_center_m"] for row in selected],
                [row[column] for row in selected],
                label=phase,
            )
        axis.axvline(action_radius_m, color="black", linestyle="--", linewidth=1)
        axis.set_title(title)
        axis.set_xlabel("initial radius from action center (m)")
        axis.grid(alpha=0.25)
        axis.legend()
    figure.suptitle("Genesis MPM internal-state localization", fontsize=14)
    figure.savefig(path, dpi=180, facecolor="white")
    plt.close(figure)


def render_pareto(path: Path, observations: list[dict[str, Any]], front_indices: np.ndarray) -> None:
    points = np.asarray([[row["loaded_rmse_mm"], row["residual_footprint_rmse_mm"]] for row in observations])
    front = points[front_indices]
    order = np.argsort(front[:, 0])
    figure, axis = plt.subplots(figsize=(7.5, 6), layout="constrained")
    axis.scatter(points[:, 0], points[:, 1], color="0.55", label="valid unique candidates")
    axis.plot(front[order, 0], front[order, 1], "o-", color="tab:red", label="nondominated front")
    axis.set_xlabel("loaded RMSE (mm; lower is better)")
    axis.set_ylabel("residual footprint RMSE (mm; lower is better)")
    axis.set_title("Loaded–residual objective trade-off")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.savefig(path, dpi=180, facecolor="white")
    plt.close(figure)


def parse_labelled_trial(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise ValueError(f"Expected LABEL=TRIAL_DIR, got: {value}")
    label, path = value.split("=", 1)
    if not label:
        raise ValueError("Sensitivity label cannot be empty")
    return label, Path(path).resolve()


def sensitivity_rows(specifications: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for specification in specifications:
        label, trial = parse_labelled_trial(specification)
        result = load_json(trial / "result.json")
        manifest = load_json(trial / "bridge" / "manifest.json")
        runtime = manifest["genesis_runtime"]
        row = result_row(trial / "result.json", result)
        row.update(
            {
                "label": label,
                "n_grid": int(runtime["n_grid"]),
                "dt_s": float(runtime["dt_s"]),
                "prepared_state_dt_s": float(runtime.get("prepared_state_dt_s", runtime["dt_s"])),
                "diagnostic_dt_override": bool(runtime.get("diagnostic_dt_override", False)),
                "particle_size_m": float(runtime["particle_size_m"]),
            }
        )
        rows.append(row)
    return sorted(rows, key=lambda row: (int(row["n_grid"]), float(row["dt_s"])), reverse=False)


def sensitivity_effects(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Report pairwise movement while holding one discretization axis fixed."""
    effects: list[dict[str, Any]] = []
    by_grid: dict[int, list[dict[str, Any]]] = {}
    by_dt: dict[float, list[dict[str, Any]]] = {}
    for row in rows:
        by_grid.setdefault(int(row["n_grid"]), []).append(row)
        by_dt.setdefault(float(row["dt_s"]), []).append(row)

    def append_effect(kind: str, fixed_value: float | int, source: dict[str, Any], target: dict[str, Any]) -> None:
        effects.append(
            {
                "comparison": kind,
                "fixed_n_grid": fixed_value if kind == "timestep" else "",
                "fixed_dt_s": fixed_value if kind == "resolution" else "",
                "from_label": source["label"],
                "to_label": target["label"],
                "loaded_rmse_delta_mm": float(target["loaded_rmse_mm"]) - float(source["loaded_rmse_mm"]),
                "residual_footprint_rmse_delta_mm": (
                    float(target["residual_footprint_rmse_mm"])
                    - float(source["residual_footprint_rmse_mm"])
                ),
                "objective_delta_mm": float(target["objective_mm"]) - float(source["objective_mm"]),
                "candidate_h0_rmse_delta_mm": (
                    float(target["candidate_h0_rmse_mm"]) - float(source["candidate_h0_rmse_mm"])
                ),
            }
        )

    for n_grid, group in sorted(by_grid.items()):
        if len(group) >= 2:
            ordered = sorted(group, key=lambda row: float(row["dt_s"]), reverse=True)
            for source, target in zip(ordered[:-1], ordered[1:]):
                append_effect("timestep", n_grid, source, target)
    for dt_s, group in sorted(by_dt.items(), reverse=True):
        if len(group) >= 2:
            ordered = sorted(group, key=lambda row: int(row["n_grid"]))
            append_effect("resolution", dt_s, ordered[0], ordered[-1])
    return effects


def convergence_estimates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Estimate three-level timestep behavior for each fixed grid.

    These are end-to-end estimates: changing timestep also changes preparation
    and candidate relaxation.  They diagnose pipeline convergence and must not
    be presented as a formal integrator order study.
    """
    estimates: list[dict[str, Any]] = []
    metrics = ("loaded_rmse_mm", "residual_footprint_rmse_mm", "objective_mm")
    grids = sorted({int(row["n_grid"]) for row in rows})
    for n_grid in grids:
        group = sorted(
            (row for row in rows if int(row["n_grid"]) == n_grid),
            key=lambda row: float(row["dt_s"]),
            reverse=True,
        )
        for coarse, middle, fine in zip(group[:-2], group[1:-1], group[2:]):
            ratio_1 = float(coarse["dt_s"]) / float(middle["dt_s"])
            ratio_2 = float(middle["dt_s"]) / float(fine["dt_s"])
            if not (np.isclose(ratio_1, ratio_2) and ratio_1 > 1.0):
                continue
            end_to_end_levels = all(
                np.isclose(float(row["dt_s"]), float(row.get("prepared_state_dt_s", row["dt_s"])))
                for row in (coarse, middle, fine)
            )
            for metric in metrics:
                coarse_delta = float(middle[metric]) - float(coarse[metric])
                fine_delta = float(fine[metric]) - float(middle[metric])
                same_direction = bool(coarse_delta * fine_delta > 0.0)
                decreasing_change = bool(abs(fine_delta) < abs(coarse_delta))
                change_ratio = float("inf") if fine_delta == 0.0 else abs(coarse_delta / fine_delta)
                observed_order = (
                    float(np.log(change_ratio) / np.log(ratio_1))
                    if end_to_end_levels and np.isfinite(change_ratio) and change_ratio > 0.0
                    else float("nan")
                )
                extrapolated = float("nan")
                if same_direction and observed_order > 0.0:
                    denominator = ratio_1**observed_order - 1.0
                    if denominator > 0.0:
                        extrapolated = float(fine[metric]) + fine_delta / denominator
                estimates.append(
                    {
                        "n_grid": n_grid,
                        "metric": metric,
                        "coarse_dt_s": float(coarse["dt_s"]),
                        "middle_dt_s": float(middle["dt_s"]),
                        "fine_dt_s": float(fine["dt_s"]),
                        "coarse_to_middle_delta": coarse_delta,
                        "middle_to_fine_delta": fine_delta,
                        "absolute_change_ratio": change_ratio,
                        "observed_order": observed_order,
                        "same_direction": same_direction,
                        "decreasing_change": decreasing_change,
                        "eligible_for_end_to_end_order": end_to_end_levels,
                        "extrapolated_zero_dt_value": extrapolated,
                        "scope": (
                            "end_to_end_preparation_and_rollout"
                            if end_to_end_levels
                            else "mixed: finest level reuses an accepted coarser-timestep prepared state"
                        ),
                    }
                )
    return estimates


def render_sensitivity(path: Path, rows: list[dict[str, Any]]) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.7), layout="constrained")
    labels = [row["label"] for row in rows]
    positions = np.arange(len(rows))
    axes[0].bar(positions - 0.18, [row["loaded_rmse_mm"] for row in rows], 0.36, label="loaded")
    axes[0].bar(positions + 0.18, [row["residual_footprint_rmse_mm"] for row in rows], 0.36, label="residual footprint")
    axes[0].set_xticks(positions, labels, rotation=25, ha="right")
    axes[0].set_ylabel("RMSE (mm)")
    axes[0].set_title("Absolute score by numerical configuration")
    axes[0].legend()
    for row in rows:
        axes[1].scatter(row["loaded_rmse_mm"], row["residual_footprint_rmse_mm"], s=70, label=row["label"])
    axes[1].set_xlabel("loaded RMSE (mm)")
    axes[1].set_ylabel("residual footprint RMSE (mm)")
    axes[1].set_title("Numerical movement in objective space")
    axes[1].grid(alpha=0.25)
    axes[1].legend(fontsize=8)
    figure.savefig(path, dpi=180, facecolor="white")
    plt.close(figure)


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    if output_dir.exists():
        raise SystemExit(f"Refusing to overwrite existing output directory: {output_dir}")
    if args.dpi <= 0:
        raise ValueError("--dpi must be positive")
    chrono_dir = args.chrono_episode.resolve()
    raw_trial = args.raw_trial.resolve()
    bridge_dir = raw_trial / "bridge"

    observations = collect_observations([path.resolve() for path in args.study_dir] + [raw_trial])
    if not observations:
        raise ValueError("No valid result.json observations were found")
    points = np.asarray([[row["loaded_rmse_mm"], row["residual_footprint_rmse_mm"]] for row in observations])
    front_indices = pareto_indices(points)
    for index, row in enumerate(observations):
        row["pareto_nondominated"] = bool(index in set(front_indices.tolist()))
    front_rows = sorted((observations[index] for index in front_indices), key=lambda row: row["loaded_rmse_mm"])

    response = load_response_data(chrono_dir, bridge_dir)
    radial_rows, cross_rows, metric_rows = response_summary(response)
    state_summary_rows, state_radial_rows = hidden_state_summary(
        bridge_dir / "genesis_raw",
        response["action"],
        float(response["manifest"]["heightmap"]["spacing_m"]),
    )
    numerical_rows = sensitivity_rows(args.sensitivity_trial)
    numerical_effects = sensitivity_effects(numerical_rows)
    convergence_rows = convergence_estimates(numerical_rows)

    output_dir.mkdir(parents=True)
    write_csv(output_dir / "pareto_observations.csv", observations)
    write_csv(output_dir / "pareto_front.csv", front_rows)
    write_csv(output_dir / "spatial_radial_profiles.csv", radial_rows)
    write_csv(output_dir / "spatial_center_cross_sections.csv", cross_rows)
    write_csv(output_dir / "spatial_error_summary.csv", metric_rows)
    write_csv(output_dir / "hidden_state_summary.csv", state_summary_rows)
    write_csv(output_dir / "hidden_state_radial_profiles.csv", state_radial_rows)
    render_pareto(output_dir / "pareto_front.png", observations, front_indices)
    render_spatial_diagnosis(output_dir / "spatial_recovery_diagnosis.png", response, radial_rows)
    render_hidden_state(
        output_dir / "hidden_state_profiles.png",
        state_radial_rows,
        float(response["action"]["radius_m"]),
    )
    if numerical_rows:
        write_csv(output_dir / "numerical_sensitivity.csv", numerical_rows)
        write_csv(output_dir / "numerical_pairwise_effects.csv", numerical_effects)
        if convergence_rows:
            write_csv(output_dir / "numerical_convergence_estimates.csv", convergence_rows)
        render_sensitivity(output_dir / "numerical_sensitivity.png", numerical_rows)

    metric_lookup = {row["phase"]: row for row in metric_rows}
    raw_result = load_json(raw_trial / "result.json")
    report = {
        "schema_version": 1,
        "method": "post-hoc multi-objective, spatial/recovery, and internal-state diagnosis; no learned network",
        "chrono_episode": str(chrono_dir),
        "raw_trial": str(raw_trial),
        "observation_count_unique_valid": len(observations),
        "pareto_front_count": len(front_rows),
        "pareto_front": [
            {
                key: row[key]
                for key in ("loaded_rmse_mm", "residual_footprint_rmse_mm", "E_pa", "phi_deg", "nu", "result_path")
            }
            for row in front_rows
        ],
        "raw_incumbent": {
            "objective_mm": 1000.0 * float(raw_result["objective_m"]),
            "loaded_rmse_mm": 1000.0 * float(raw_result["loaded_rmse_m"]),
            "residual_footprint_rmse_mm": 1000.0 * float(raw_result["residual_footprint_rmse_m"]),
        },
        "spatial_error": metric_lookup,
        "internal_state": {row["phase"]: row for row in state_summary_rows},
        "numerical_sensitivity": numerical_rows,
        "numerical_pairwise_effects": numerical_effects,
        "numerical_convergence_estimates": convergence_rows,
        "numerical_convergence_status": (
            "not_demonstrated: two levels expose sensitivity but cannot establish an asymptotic convergence rate"
            if numerical_rows
            else "not_evaluated"
        ),
        "model_form_status": (
            "suggestive_but_not_isolated_from_end_to_end_numerical_sensitivity"
            if numerical_rows
            else "pending_controlled_numerical_matrix"
        ),
        "interpretation_guardrail": (
            "A persistent loaded/residual trade-off plus localized plastic/recovery mismatch supports a model-form "
            "diagnosis only if the controlled numerical matrix is small relative to the residual mismatch."
        ),
    }
    (output_dir / "diagnosis.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(output_dir)


if __name__ == "__main__":
    main()

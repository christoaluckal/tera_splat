#!/usr/bin/env python3
"""Recompute the 2026-09-06 Newton/Genesis cylinder A/B report."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEWTON = REPO / "outputs/validity_experiment/newton/response_convergence_native_proxy_20260906/dt0p5ms"
GENESIS_MATCHED = REPO / "outputs/validity_experiment/backend_ab_20260906/genesis_newton_smoke_material_dt0p5ms"
GENESIS_INCUMBENT = (
    REPO
    / "outputs/validity_experiment/bayesopt"
    / "A0_oracle_guided_offset_5mm_gate6mm_5mm_n128_incumbent_raw_20260830"
    / "study_ykep3esa/trials/iteration_000/bridge"
)
NEWTON_REVERSE_PREP = (
    REPO
    / "outputs/validity_experiment/backend_ab_20260906"
    / "newton_genesis_incumbent_preparation/dt0p5ms_2s"
)


def metrics(error: np.ndarray, mask: np.ndarray) -> dict[str, float | int]:
    values = error[mask]
    return {
        "cells": int(values.size),
        "rmse_mm": float(np.sqrt(np.mean(values * values)) * 1.0e3),
        "mae_mm": float(np.mean(np.abs(values)) * 1.0e3),
        "mean_mm": float(np.mean(values) * 1.0e3),
        "max_abs_mm": float(np.max(np.abs(values)) * 1.0e3),
    }


def read_metric(path: Path, name: str) -> float:
    with path.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            if row["metric"] == name:
                return float(row["value"])
    raise KeyError(f"{name} not found in {path}")


def stage_time(root: Path) -> float:
    return sum(
        read_metric(root / relative, "total_wall_seconds")
        for relative in (
            "candidate_prepare_raw/run_metrics.csv",
            "candidate_initial_hold_raw/run_metrics.csv",
            "genesis_raw/run_metrics.csv",
        )
    )


def load_case(
    name: str,
    backend: str,
    root: Path,
    chrono: dict[str, np.ndarray],
    footprint: np.ndarray,
) -> dict:
    initial = np.load(root / "initial_heightmap_m.npy")
    loaded = np.load(root / "loaded_heightmap_m.npy")
    residual = np.load(root / "residual_heightmap_m.npy")
    valid = np.load(root / "valid_heightmap_mask.npy").astype(bool)
    valid &= chrono["valid"]
    valid &= np.isfinite(initial) & np.isfinite(loaded) & np.isfinite(residual)
    loaded_response = loaded - initial
    residual_response = residual - initial
    loaded_error = loaded_response - (chrono["loaded"] - chrono["initial"])
    residual_error = residual_response - (chrono["residual"] - chrono["initial"])
    result = {
        "name": name,
        "backend": backend,
        "root": str(root.resolve()),
        "valid_cells": int(np.count_nonzero(valid)),
        "initial": metrics(initial - chrono["initial"], valid),
        "loaded_all": metrics(loaded_error, valid),
        "loaded_footprint": metrics(loaded_error, valid & footprint),
        "residual_all": metrics(residual_error, valid),
        "residual_footprint": metrics(residual_error, valid & footprint),
        "loaded_response_footprint": metrics(loaded_response, valid & footprint),
        "residual_response_footprint": metrics(residual_response, valid & footprint),
        "_valid": valid,
        "_loaded_response": loaded_response,
        "_residual_response": residual_response,
        "_loaded_error": loaded_error,
        "_residual_error": residual_error,
    }
    result["objective_mm"] = (
        result["loaded_all"]["rmse_mm"]
        + 0.5 * result["residual_footprint"]["rmse_mm"]
    )
    return result


def public_case(case: dict) -> dict:
    return {key: value for key, value in case.items() if not key.startswith("_")}


def compare(left: dict, right: dict, footprint: np.ndarray) -> dict:
    valid = left["_valid"] & right["_valid"]
    return {
        "left": left["name"],
        "right": right["name"],
        "cells": int(np.count_nonzero(valid)),
        "loaded_response_delta_all": metrics(
            left["_loaded_response"] - right["_loaded_response"], valid
        ),
        "loaded_response_delta_footprint": metrics(
            left["_loaded_response"] - right["_loaded_response"], valid & footprint
        ),
        "residual_response_delta_all": metrics(
            left["_residual_response"] - right["_residual_response"], valid
        ),
        "residual_response_delta_footprint": metrics(
            left["_residual_response"] - right["_residual_response"], valid & footprint
        ),
    }


def add_circle(axis: plt.Axes) -> None:
    axis.add_patch(plt.Circle((0.0, 0.005), 0.073025, fill=False, color="black", linewidth=0.8))


def response_figure(cases: list[dict], chrono: dict[str, np.ndarray], extent: tuple[float, ...]) -> None:
    target = {
        "name": "Chrono target",
        "_loaded_response": chrono["loaded"] - chrono["initial"],
        "_residual_response": chrono["residual"] - chrono["initial"],
    }
    columns = [target, *cases]
    fig, axes = plt.subplots(2, len(columns), figsize=(4.0 * len(columns), 7.2), constrained_layout=True)
    image = None
    for row, (key, label) in enumerate((("_loaded_response", "Loaded response"), ("_residual_response", "Residual response"))):
        for column, case in enumerate(columns):
            image = axes[row, column].imshow(
                case[key] * 1.0e3,
                origin="lower",
                extent=extent,
                cmap="viridis",
                vmin=-35.0,
                vmax=5.0,
            )
            add_circle(axes[row, column])
            axes[row, column].set_title(case["name"])
            if column == 0:
                axes[row, column].set_ylabel(f"{label}\ny (m)")
            axes[row, column].set_xlabel("x (m)")
    fig.colorbar(image, ax=axes, label="surface change (mm)", shrink=0.85)
    fig.savefig(HERE / "response_maps.png", dpi=170)
    plt.close(fig)


def error_figure(cases: list[dict], extent: tuple[float, ...]) -> None:
    fig, axes = plt.subplots(2, len(cases), figsize=(4.2 * len(cases), 7.2), constrained_layout=True)
    image = None
    for row, (key, label) in enumerate((("_loaded_error", "Loaded error"), ("_residual_error", "Residual error"))):
        for column, case in enumerate(cases):
            image = axes[row, column].imshow(
                case[key] * 1.0e3,
                origin="lower",
                extent=extent,
                cmap="coolwarm",
                vmin=-25.0,
                vmax=25.0,
            )
            add_circle(axes[row, column])
            axes[row, column].set_title(case["name"])
            if column == 0:
                axes[row, column].set_ylabel(f"{label}\ny (m)")
            axes[row, column].set_xlabel("x (m)")
    fig.colorbar(image, ax=axes, label="simulation - Chrono (mm)", shrink=0.85)
    fig.savefig(HERE / "error_maps.png", dpi=170)
    plt.close(fig)


def main() -> None:
    manifest = json.loads((GENESIS_MATCHED / "manifest.json").read_text(encoding="utf-8"))
    oracle_root = Path(manifest["source_chrono_episode"])
    chrono = {
        key: np.load(oracle_root / f"{key}_heightmap_m.npy")
        for key in ("initial", "loaded", "residual")
    }
    chrono["valid"] = np.load(oracle_root / "valid_heightmap_mask.npy").astype(bool)
    origin_x, origin_y = manifest["heightmap"]["origin_xy_m"]
    spacing = float(manifest["heightmap"]["spacing_m"])
    rows, columns = chrono["initial"].shape
    x = origin_x + spacing * np.arange(columns)
    y = origin_y + spacing * np.arange(rows)
    xx, yy = np.meshgrid(x, y)
    footprint = xx * xx + (yy - 0.005) ** 2 <= 0.073025**2
    extent = (
        origin_x - spacing / 2,
        origin_x + spacing * (columns - 0.5),
        origin_y - spacing / 2,
        origin_y + spacing * (rows - 0.5),
    )

    newton = load_case("Newton 100 kPa", "newton", NEWTON, chrono, footprint)
    genesis_matched = load_case("Genesis 100 kPa", "genesis", GENESIS_MATCHED, chrono, footprint)
    genesis_incumbent = load_case("Genesis incumbent", "genesis", GENESIS_INCUMBENT, chrono, footprint)
    cases = [newton, genesis_matched, genesis_incumbent]

    newton_manifest = json.loads((NEWTON / "newton_cylinder_manifest.json").read_text(encoding="utf-8"))
    reverse_manifest = json.loads((NEWTON_REVERSE_PREP / "newton_prepared_bed_manifest.json").read_text(encoding="utf-8"))
    summary = {
        "schema_version": 1,
        "experiment": "newton_genesis_backend_ab",
        "status": "completed_with_reverse_crossover_rejected_at_preparation",
        "contract": {
            "chrono_episode": str(oracle_root.resolve()),
            "timestep_s": 0.0005,
            "particle_spacing_m": 0.005,
            "voxel_or_grid_cell_m": 0.015625,
            "loaded_time_s": 3.595,
            "residual_time_s": 0.25,
            "valid_cells": 14161,
            "footprint_cells": int(np.count_nonzero(footprint & chrono["valid"])),
            "objective": "loaded all-cell RMSE + 0.5 * residual footprint RMSE",
        },
        "matched_material": {
            "young_modulus_pa": 100000.0,
            "poisson_ratio": 0.2,
            "density_kg_m3": 1000.0,
            "newton_friction_coefficient": 0.68,
            "genesis_friction_angle_deg": 34.2157021324374,
            "qualification": "nominal scalar match only; constitutive laws, transfer, preparation, and contact discretization differ",
            "objective_winner": "newton",
            "newton_objective_mm": newton["objective_mm"],
            "genesis_objective_mm": genesis_matched["objective_mm"],
            "newton_stage_wall_s": float(newton_manifest["wall_time_s"]),
            "genesis_stage_wall_s": stage_time(GENESIS_MATCHED),
            "genesis_external_process_wall_s": 315.83,
        },
        "current_pipeline": {
            "objective_winner": "genesis_incumbent",
            "genesis_incumbent_objective_mm": genesis_incumbent["objective_mm"],
            "newton_uncalibrated_objective_mm": newton["objective_mm"],
            "genesis_incumbent_stage_wall_s": stage_time(GENESIS_INCUMBENT),
        },
        "reverse_crossover": {
            "requested_material": "Genesis incumbent in Newton",
            "accepted": bool(reverse_manifest["accepted"]),
            "settled_h0_rmse_mm": float(reverse_manifest["surface_match"]["settled"]["rmse_m"] * 1.0e3),
            "settled_h0_max_abs_mm": float(reverse_manifest["surface_match"]["settled"]["max_abs_m"] * 1.0e3),
            "h0_rmse_gate_mm": float(reverse_manifest["surface_match"]["acceptance_rmse_m"] * 1.0e3),
            "h0_max_abs_gate_mm": float(reverse_manifest["surface_match"]["acceptance_max_abs_m"] * 1.0e3),
            "interpretation": "rejected before cylinder contact; direct Genesis parameter transfer is not admissible",
        },
        "cases": [public_case(case) for case in cases],
        "comparisons": [
            compare(newton, genesis_matched, footprint),
            compare(newton, genesis_incumbent, footprint),
        ],
        "conclusion": "Newton wins the matched 100 kPa map objective and numerical-stability evidence; calibrated Genesis wins current absolute Chrono fit. Newton requires backend-specific calibration after collider-support diagnosis.",
    }
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    fields = [
        "name", "backend", "objective_mm", "h0_rmse_mm", "loaded_all_rmse_mm",
        "loaded_footprint_rmse_mm", "residual_all_rmse_mm", "residual_footprint_rmse_mm",
        "loaded_footprint_mean_response_mm", "residual_footprint_mean_response_mm",
    ]
    with (HERE / "cases.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for case in cases:
            writer.writerow({
                "name": case["name"],
                "backend": case["backend"],
                "objective_mm": case["objective_mm"],
                "h0_rmse_mm": case["initial"]["rmse_mm"],
                "loaded_all_rmse_mm": case["loaded_all"]["rmse_mm"],
                "loaded_footprint_rmse_mm": case["loaded_footprint"]["rmse_mm"],
                "residual_all_rmse_mm": case["residual_all"]["rmse_mm"],
                "residual_footprint_rmse_mm": case["residual_footprint"]["rmse_mm"],
                "loaded_footprint_mean_response_mm": case["loaded_response_footprint"]["mean_mm"],
                "residual_footprint_mean_response_mm": case["residual_response_footprint"]["mean_mm"],
            })

    response_figure(cases, chrono, extent)
    error_figure(cases, extent)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

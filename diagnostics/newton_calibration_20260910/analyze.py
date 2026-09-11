#!/usr/bin/env python3
"""Recompute the first corrected-Newton stiffness calibration diagnostic."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
BASE_ANALYZER = REPO / "diagnostics/backend_ab_20260906/analyze.py"
BASELINE = (
    REPO
    / "outputs/validity_experiment/newton/collider_support_inset_20260908"
    / "full_strict_kamino/inset9p375mm_dt0p5ms"
)
CANDIDATE = (
    REPO
    / "outputs/validity_experiment/newton/calibration_20260910"
    / "e25k/response/dt0p5ms"
)
PREPARATION = (
    REPO
    / "outputs/validity_experiment/newton/calibration_20260910"
    / "e25k/preparation/analysis/summary.json"
)


def load_base_analyzer():
    spec = importlib.util.spec_from_file_location("backend_ab_20260906", BASE_ANALYZER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {BASE_ANALYZER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    analyzer = load_base_analyzer()
    matched_manifest = json.loads(
        (analyzer.GENESIS_MATCHED / "manifest.json").read_text(encoding="utf-8")
    )
    oracle_root = Path(matched_manifest["source_chrono_episode"])
    chrono = {
        key: np.load(oracle_root / f"{key}_heightmap_m.npy")
        for key in ("initial", "loaded", "residual")
    }
    chrono["valid"] = np.load(oracle_root / "valid_heightmap_mask.npy").astype(bool)
    origin_x, origin_y = matched_manifest["heightmap"]["origin_xy_m"]
    spacing = float(matched_manifest["heightmap"]["spacing_m"])
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
    baseline = analyzer.load_case(
        "Newton 100 kPa qualified", "newton", BASELINE, chrono, footprint
    )
    candidate = analyzer.load_case(
        "Newton 25 kPa rejected", "newton", CANDIDATE, chrono, footprint
    )
    candidate_manifest = json.loads(
        (CANDIDATE / "newton_cylinder_manifest.json").read_text(encoding="utf-8")
    )
    preparation = json.loads(PREPARATION.read_text(encoding="utf-8"))
    cases = [baseline, candidate]
    analyzer.HERE = HERE
    analyzer.response_figure(cases, chrono, extent)
    analyzer.error_figure(cases, extent)
    summary = {
        "schema_version": 1,
        "experiment": "corrected_newton_stiffness_screen",
        "status": "candidate_rejected",
        "frozen_settings": {
            "timestep_s": 0.0005,
            "collision_bottom_inset_m": 0.009375,
            "rigid_solver_tolerance": 1.0e-6,
        },
        "preparation_consistency_passed": preparation["consistency_passed"],
        "cases": [analyzer.public_case(case) for case in cases],
        "candidate_mechanics": {
            "accepted": candidate_manifest["accepted"],
            "acceptance_blockers": candidate_manifest["acceptance_blockers"],
            "max_inside_particle_centers": candidate_manifest["penetration"][
                "max_inside_particle_centers"
            ],
            "max_center_penetration_mm": 1.0e3
            * candidate_manifest["penetration"]["max_center_penetration_m"],
            "guide_constraint_error": candidate_manifest["cylinder"][
                "guide_constraint_error"
            ],
        },
        "interpretation": (
            "Lower stiffness improves the DEM-only objective but exploits the "
            "uncollided analytic slice created by the raised proxy. Stop material "
            "calibration until support is corrected without shrinking collision coverage."
        ),
    }
    with (HERE / "cases.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=("name", "objective_mm", "loaded_rmse_mm", "residual_footprint_rmse_mm"),
        )
        writer.writeheader()
        for case in cases:
            writer.writerow(
                {
                    "name": case["name"],
                    "objective_mm": case["objective_mm"],
                    "loaded_rmse_mm": case["loaded_all"]["rmse_mm"],
                    "residual_footprint_rmse_mm": case["residual_footprint"]["rmse_mm"],
                }
            )
    (HERE / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

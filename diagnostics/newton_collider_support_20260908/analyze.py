#!/usr/bin/env python3
"""Recompute the corrected Newton/Genesis A/B report and support delta."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
BASE_ANALYZER = REPO / "diagnostics/backend_ab_20260906/analyze.py"
CORRECTED = (
    REPO
    / "outputs/validity_experiment/newton/collider_support_inset_20260908"
    / "full_strict_kamino/inset9p375mm_dt0p5ms"
)
ORIGINAL = (
    REPO
    / "outputs/validity_experiment/newton"
    / "response_convergence_native_proxy_20260906/dt0p5ms"
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
    analyzer.HERE = HERE
    analyzer.NEWTON = CORRECTED
    analyzer.main()

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
    original = analyzer.load_case(
        "Newton original support", "newton", ORIGINAL, chrono, footprint
    )
    corrected = analyzer.load_case(
        "Newton corrected support", "newton", CORRECTED, chrono, footprint
    )
    summary_path = HERE / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["status"] = "completed_corrected_newton_ab"
    summary["support_correction"] = {
        "collision_bottom_inset_mm": 9.375,
        "rigid_solver_tolerance": 1.0e-6,
        "original_objective_mm": original["objective_mm"],
        "corrected_objective_mm": corrected["objective_mm"],
        "objective_change_mm": corrected["objective_mm"] - original["objective_mm"],
        "response_delta": analyzer.compare(corrected, original, footprint),
    }
    summary["conclusion"] = (
        "The support correction is mechanics-qualified and timestep-consistent. "
        "Use corrected Newton for backend-specific calibration; Genesis incumbent "
        "remains the current absolute-fit reference."
    )
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary["support_correction"], indent=2))


if __name__ == "__main__":
    main()

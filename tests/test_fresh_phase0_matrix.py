#!/usr/bin/env python3
"""Tests for progressive fresh Phase 0 matrix selection and local metrics."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "fresh_phase0_matrix",
    REPO_ROOT / "scripts" / "run_fresh_phase0_matrix.py",
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FreshPhase0MatrixTest(unittest.TestCase):
    def setUp(self) -> None:
        self.path = REPO_ROOT / "configs" / "static_proxy_hierarchical_v3_20261017.json"
        self.contract = MODULE.fresh.load_contract(self.path)
        self.cases = MODULE.fresh.cases(self.contract)

    def test_spatial_rungs_cover_five_positions_and_full_covers_matrix(self) -> None:
        rungs = MODULE.rung_cases(self.cases)
        for name in ("spatial31", "spatial46", "spatial61"):
            self.assertEqual(len(rungs[name]), 5)
        self.assertEqual(len(rungs["full"]), 15)
        self.assertEqual(set(rungs["full"]), {case["case_id"] for case in self.cases})

    def test_spatial31_preserves_whole_position_split(self) -> None:
        selected = MODULE.select_cases(self.cases, "spatial31", [])
        partitions = [
            MODULE.split_for_case(self.contract, case["case_id"])
            for case in selected
        ]
        self.assertEqual(partitions.count("train"), 3)
        self.assertEqual(partitions.count("validation"), 1)
        self.assertEqual(partitions.count("test"), 1)

    def test_explicit_case_selection_overrides_rung(self) -> None:
        selected = MODULE.select_cases(
            self.cases, "spatial31", ["yminus100_f046n"]
        )
        self.assertEqual([case["case_id"] for case in selected], ["yminus100_f046n"])

    def test_error_metrics_report_skill_against_no_deformation(self) -> None:
        target = np.asarray([0.0, -2.0], dtype=np.float64)
        baseline = np.asarray([0.0, 0.0], dtype=np.float64)
        prediction = np.asarray([0.0, -1.0], dtype=np.float64)
        result = MODULE.error_metrics(prediction, target, baseline)
        self.assertAlmostEqual(result["mse_skill_vs_no_deformation"], 0.75)
        self.assertAlmostEqual(result["rmse_m"], np.sqrt(0.5))


if __name__ == "__main__":
    unittest.main()

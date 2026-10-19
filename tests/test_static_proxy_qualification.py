#!/usr/bin/env python3
"""Unit tests for the static 35 mm proxy qualification contract."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "static_proxy_qualification",
    REPO_ROOT / "scripts" / "run_static_proxy_qualification.py",
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class StaticProxyQualificationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = MODULE.load_contract(
            REPO_ROOT / "configs" / "static_proxy_35mm_qualification.json"
        )
        self.cases = MODULE.build_cases(self.contract)

    def test_contract_is_static_35mm_and_excludes_dynamic_loads(self) -> None:
        action = self.contract["action"]
        self.assertEqual(action["load_mode"], "static_gravity_equivalent_mass")
        self.assertTrue(action["dynamic_loads_excluded"])
        self.assertAlmostEqual(action["radius_m"], 0.035)

    def test_matrix_crosses_five_positions_and_two_admitted_loads(self) -> None:
        self.assertEqual(len(self.cases), 10)
        self.assertEqual(len({case.position_label for case in self.cases}), 5)
        self.assertEqual(len({case.normal_force_n for case in self.cases}), 2)
        self.assertEqual(len({case.case_id for case in self.cases}), 10)

    def test_static_loads_stop_below_rejected_two_support_boundary(self) -> None:
        masses = sorted({case.equivalent_mass_kg for case in self.cases})
        forces = sorted({case.normal_force_n for case in self.cases})
        self.assertEqual(masses, [3.125, 4.6875])
        self.assertAlmostEqual(forces[0], 30.65625)
        self.assertAlmostEqual(forces[-1], 45.984375)
        excluded = self.contract["excluded_boundary_actions"]
        self.assertEqual(len(excluded), 1)
        self.assertAlmostEqual(excluded[0]["normal_force_n"], 61.3125)
        self.assertEqual(excluded[0]["loaded_inside_particle_centers"], 38)

    def test_pressure_is_force_over_foot_area(self) -> None:
        case = self.cases[0]
        expected = case.normal_force_n / (MODULE.math.pi * 0.035**2)
        self.assertAlmostEqual(case.nominal_pressure_pa, expected)

    def test_high_load_spatial_anchor_exists(self) -> None:
        anchor = self.contract["response_convergence"]["anchor_case_id"]
        self.assertIn(anchor, {case.case_id for case in self.cases})
        selected_dt = self.contract["newton"]["selected_dt_s"]
        self.assertIn(selected_dt, self.contract["response_convergence"]["timesteps_s"])

    def test_low_load_center_case_is_the_expansion_sentinel(self) -> None:
        sentinel = self.contract["newton"]["sentinel_case_id"]
        self.assertEqual(sentinel, "center_f031n")
        self.assertIn(sentinel, {case.case_id for case in self.cases})

    def test_episode_split_is_prospective_complete_and_position_held_out(self) -> None:
        assignments = MODULE.validate_episode_split(self.contract, self.cases)
        self.assertEqual(len(assignments), 10)
        self.assertEqual(
            {case.position_label for case in self.cases if assignments[case.case_id] == "train"},
            {"center", "xplus100", "xminus100"},
        )
        self.assertEqual(
            {case.position_label for case in self.cases if assignments[case.case_id] == "validation"},
            {"yplus100"},
        )
        self.assertEqual(
            {case.position_label for case in self.cases if assignments[case.case_id] == "test"},
            {"yminus100"},
        )

    def test_bounded_overlap_can_admit_coarse_prior_without_strict_claim(self) -> None:
        manifest = {
            "mechanics_qualified": False,
            "finite": True,
            "preparation": {"convergence_passed": True},
            "cylinder": {"guide_constraint_passed": True},
            "penetration": {
                "max_inside_particle_centers": 20,
                "max_center_penetration_m": 4.5e-6,
                "loaded": {
                    "inside_particle_centers": 0,
                    "max_center_penetration_m": 0.0,
                },
            },
            "surface": {
                "valid_cells": 14161,
                "initial_match": {"valid_fraction": 1.0},
            },
        }
        prepared = {"selection": {"particle_count": 307461}}
        result = MODULE.evaluate_coarse_prior_admission(
            manifest, prepared, self.contract["coarse_prior_admission"]
        )
        self.assertTrue(result["admissible"])
        self.assertFalse(result["strict_mechanics_qualified"])
        self.assertFalse(result["strict_mechanics_claim_permitted"])

    def test_coarse_prior_rejects_overlap_beyond_declared_depth(self) -> None:
        manifest = {
            "mechanics_qualified": False,
            "finite": True,
            "preparation": {"convergence_passed": True},
            "cylinder": {"guide_constraint_passed": True},
            "penetration": {
                "max_inside_particle_centers": 1,
                "max_center_penetration_m": 1.1e-5,
                "loaded": {
                    "inside_particle_centers": 0,
                    "max_center_penetration_m": 0.0,
                },
            },
            "surface": {
                "valid_cells": 14161,
                "initial_match": {"valid_fraction": 1.0},
            },
        }
        prepared = {"selection": {"particle_count": 307461}}
        result = MODULE.evaluate_coarse_prior_admission(
            manifest, prepared, self.contract["coarse_prior_admission"]
        )
        self.assertFalse(result["admissible"])
        self.assertFalse(result["checks"]["transient_penetration_depth"])

    def test_coarse_prior_rejects_affected_fraction_beyond_frozen_limit(self) -> None:
        manifest = {
            "mechanics_qualified": False,
            "finite": True,
            "preparation": {"convergence_passed": True},
            "cylinder": {"guide_constraint_passed": True},
            "penetration": {
                "max_inside_particle_centers": 62,
                "max_center_penetration_m": 5.0e-6,
                "loaded": {
                    "inside_particle_centers": 0,
                    "max_center_penetration_m": 0.0,
                },
            },
            "surface": {
                "valid_cells": 14161,
                "initial_match": {"valid_fraction": 1.0},
            },
        }
        prepared = {"selection": {"particle_count": 307461}}
        result = MODULE.evaluate_coarse_prior_admission(
            manifest, prepared, self.contract["coarse_prior_admission"]
        )
        self.assertFalse(result["admissible"])
        self.assertFalse(result["checks"]["transient_inside_particle_fraction"])


if __name__ == "__main__":
    unittest.main()

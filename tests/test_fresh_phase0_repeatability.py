#!/usr/bin/env python3
"""Tests for the fresh-only hierarchical Phase 0 contract."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "fresh_phase0_repeatability",
    REPO_ROOT / "scripts" / "run_fresh_phase0_repeatability.py",
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FreshPhase0RepeatabilityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.path = REPO_ROOT / "configs" / "static_proxy_hierarchical_v3_20261017.json"
        self.contract = MODULE.load_contract(self.path)
        self.cases = MODULE.cases(self.contract)

    def test_contract_forbids_prior_output_reuse(self) -> None:
        reuse = self.contract["reuse_policy"]
        self.assertFalse(reuse["prior_experiment_outputs_admissible"])
        self.assertTrue(reuse["require_fresh_chrono_h0"])
        self.assertTrue(reuse["require_fresh_metric_particle_bed_from_chrono_h0"])
        self.assertTrue(reuse["require_fresh_newton_preparation_per_response"])
        self.assertNotIn("particles_ply", self.contract["newton"])
        self.assertNotIn("metadata_json", self.contract["newton"])

    def test_fresh_matrix_restores_three_loads_and_fifteen_actions(self) -> None:
        self.assertEqual(len(self.cases), 15)
        self.assertEqual(len({case["position_label"] for case in self.cases}), 5)
        self.assertEqual(len({case["normal_force_n"] for case in self.cases}), 3)
        MODULE.validate_split(self.contract, self.cases)

    def test_variation_is_characterized_without_bitwise_gate(self) -> None:
        repeatability = self.contract["repeatability"]
        self.assertFalse(repeatability["required_before_matrix"])
        self.assertEqual(repeatability["sequential_repeats"], 2)
        self.assertFalse(repeatability["reuse_repeat_as_training_data"])
        self.assertTrue(repeatability["chrono"]["report_heightmap_variation"])
        self.assertTrue(repeatability["newton"]["report_surface_and_particle_variation"])
        self.assertFalse(
            self.contract["hierarchical_admission"]["level_0_provenance"]
            ["bitwise_repeatability_required"]
        )

    def test_overlap_is_classified_but_geometry_is_primary(self) -> None:
        policy = self.contract["hierarchical_admission"]
        interaction = policy["level_2_interaction_artifact"]
        geometry = policy["level_3_geometric_utility"]
        self.assertTrue(interaction["loaded_overlap_may_be_labeled_artifact"])
        self.assertEqual(geometry["primary_masks"], ["footprint", "local_2r"])
        self.assertEqual(geometry["baseline"], "no_deformation")
        self.assertEqual(geometry["min_loaded_footprint_mse_skill"], 0.0)

    def test_array_comparison_reports_small_nonzero_variation_as_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.npy"
            second = root / "second.npy"
            np.save(first, np.asarray([1.0, 2.0], dtype=np.float32))
            np.save(second, np.asarray([1.0, 2.0], dtype=np.float32))
            self.assertTrue(MODULE.compare_arrays(first, second)["exact"])
            np.save(second, np.asarray([1.0, 2.0 + 1.0e-6], dtype=np.float32))
            comparison = MODULE.compare_arrays(first, second)
            self.assertFalse(comparison["exact"])
            self.assertTrue(comparison["compatible"])
            self.assertGreater(comparison["rmse_difference"], 0.0)


if __name__ == "__main__":
    unittest.main()

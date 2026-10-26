#!/usr/bin/env python3
"""Tests for the Phase 1 locked-evaluation contract and pure metrics."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "evaluate_phase1_bed_state.py"
spec = importlib.util.spec_from_file_location("evaluate_phase1_bed_state", SCRIPT_PATH)
assert spec and spec.loader
evaluation = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = evaluation
spec.loader.exec_module(evaluation)


class Phase1EvaluationTests(unittest.TestCase):
    def test_config_locks_test_groups_and_episode_bootstrap(self) -> None:
        config = evaluation.load_evaluation_config(evaluation.DEFAULT_CONFIG)
        self.assertEqual(config["membership"]["test"], 24)
        self.assertEqual(sum(config["membership"]["required_holdout_groups"].values()), 24)
        self.assertTrue(config["membership"]["selection_must_precede_unlock"])
        self.assertTrue(config["metrics"]["episode_is_resampling_unit"])
        self.assertFalse(
            config["sensitivity"]["use_for_training_normalization_calibration_or_selection"]
        )

    def test_test_episode_selection_rechecks_lock_groups_and_surfaces(self) -> None:
        config = evaluation.load_evaluation_config(evaluation.DEFAULT_CONFIG)
        groups = []
        for name, count in config["membership"]["required_holdout_groups"].items():
            groups.extend([name] * count)
        seeds = config["membership"]["required_surface_seeds"]
        episodes = [
            {
                "episode_id": f"test_{index:02d}",
                "split": "test",
                "holdout_group": group,
                "initial_surface_seed": seeds[index % len(seeds)],
                "input_sha256": f"sha-{index}",
                "target_access": "locked",
            }
            for index, group in enumerate(groups)
        ]
        plan = {
            "episodes": {"test": episodes},
            "test_lock_sha256": evaluation.canonical_sha256(
                [
                    {"episode_id": item["episode_id"], "input_sha256": item["input_sha256"]}
                    for item in episodes
                ]
            ),
        }
        selected = evaluation.selected_test_episodes(config, plan)
        self.assertEqual(len(selected), 24)
        plan["episodes"]["test"][0]["target_access"] = "open"
        with self.assertRaisesRegex(ValueError, "lock is invalid"):
            evaluation.selected_test_episodes(config, plan)

    def test_parameter_shuffle_is_deterministic_derangement(self) -> None:
        identities = [f"episode_{index:02d}" for index in range(24)]
        first = evaluation.parameter_shuffle_mapping(identities, 17)
        second = evaluation.parameter_shuffle_mapping(reversed(identities), 17)
        self.assertEqual(first, second)
        self.assertEqual(set(first), set(identities))
        self.assertEqual(set(first.values()), set(identities))
        self.assertTrue(all(source != target for source, target in first.items()))

    def test_matched_sensitivity_contract_requires_rectangle_and_common_action(self) -> None:
        config = evaluation.load_evaluation_config(evaluation.DEFAULT_CONFIG)
        combinations = [
            (640000.0, 24.0),
            (640000.0, 32.0),
            (960000.0, 24.0),
            (960000.0, 32.0),
            (800000.0, 28.0),
        ]
        cases = [
            {
                "case_id": f"case_{index}",
                "initial_surface_seed": 1101,
                "center_xy_m": [0.0, 0.0],
                "normal_force_n": 45.984375,
                "bekker_kphi": kphi,
                "mohr_friction_deg": friction,
            }
            for index, (kphi, friction) in enumerate(combinations)
        ]
        self.assertEqual(
            len(evaluation.matched_sensitivity_cases(config, {"material_cases": cases})),
            5,
        )
        cases[0]["normal_force_n"] = 31.0
        with self.assertRaisesRegex(ValueError, "not action matched"):
            evaluation.matched_sensitivity_cases(config, {"material_cases": cases})

    def test_surface_metrics_report_geometry_and_error(self) -> None:
        initial = np.zeros((3, 3), dtype=np.float64)
        target = np.zeros((3, 3), dtype=np.float64)
        target[1, 1] = -0.01
        prediction = np.zeros((3, 3), dtype=np.float64)
        prediction[1, 1] = -0.008
        mask = np.ones((3, 3), dtype=bool)
        x, y = np.meshgrid(np.arange(3) - 1, np.arange(3) - 1)
        metrics = evaluation.surface_metrics(
            prediction,
            target,
            initial,
            mask,
            grid_spacing_m=0.005,
            deformation_threshold_m=0.0005,
            relative_x_m=x,
            relative_y_m=y,
        )
        self.assertAlmostEqual(metrics["rmse_m"], 0.002 / 3.0)
        self.assertEqual(metrics["peak_depression_m"], 0.008)
        self.assertEqual(metrics["target_peak_depression_m"], 0.01)
        self.assertAlmostEqual(metrics["deformation_centroid_x_m"], 0.0)
        self.assertAlmostEqual(metrics["deformation_centroid_y_m"], 0.0)

    def test_bootstrap_resamples_whole_episode_values_deterministically(self) -> None:
        values = [1.0, 2.0, 3.0, 4.0]
        first = evaluation.bootstrap_interval(
            values, resamples=500, confidence=0.95, seed=9
        )
        second = evaluation.bootstrap_interval(
            values, resamples=500, confidence=0.95, seed=9
        )
        self.assertEqual(first, second)
        self.assertEqual(first["episode_count"], 4)
        self.assertEqual(first["estimate"], 2.5)
        self.assertLessEqual(first["lower"], first["estimate"])
        self.assertGreaterEqual(first["upper"], first["estimate"])

    def test_prerequisite_gate_refuses_absent_selection(self) -> None:
        config = evaluation.load_evaluation_config(evaluation.DEFAULT_CONFIG)
        with tempfile.TemporaryDirectory() as directory:
            modified = json.loads(json.dumps(config))
            modified["selection_summary"] = str(Path(directory) / "absent.json")
            with self.assertRaisesRegex(RuntimeError, "prerequisites are absent"):
                evaluation.require_prerequisites(modified)


if __name__ == "__main__":
    unittest.main()

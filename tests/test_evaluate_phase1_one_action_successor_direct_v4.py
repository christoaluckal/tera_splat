#!/usr/bin/env python3
"""Pure tests for the direct-v4 protected report gates."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "evaluate_phase1_one_action_successor_direct_v4.py"
CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_direct_v4.json"


def load_module():
    spec = importlib.util.spec_from_file_location("direct_v4_report", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


reporter = load_module()


def passing_rows():
    tree = {
        checkpoint: {region: 0.001 for region in reporter.REGIONS}
        for checkpoint in reporter.CHECKPOINTS
    }
    raw = {
        checkpoint: {region: 0.002 for region in reporter.REGIONS}
        for checkpoint in reporter.CHECKPOINTS
    }
    zero = {
        checkpoint: {region: 0.003 for region in reporter.REGIONS}
        for checkpoint in reporter.CHECKPOINTS
    }
    control = {
        checkpoint: {region: 0.0011 for region in reporter.REGIONS}
        for checkpoint in reporter.CHECKPOINTS
    }
    coverage = {
        checkpoint: {region: 0.9 for region in reporter.REGIONS}
        for checkpoint in reporter.CHECKPOINTS
    }
    return [
        {
            "episode_id": f"episode_{index:03d}",
            "holdout_group": "fresh_joint_confirmation",
            "rmse_m": {"D1": tree, "raw_newton": raw, "no_deformation": zero},
            "parameter_controls": {
                "kphi_shuffled": control,
                "kphi_constant_reference": control,
            },
            "coverage_fraction": coverage,
        }
        for index in range(24)
    ]


class DirectV4ReportTests(unittest.TestCase):
    def test_all_frozen_gates_can_pass(self) -> None:
        config = reporter.planner.load_config(CONFIG)
        payload = {
            "episodes": passing_rows(),
            "protected_sensitivity": {
                "direction_fraction": 1.0,
                "eligible_comparisons": 24,
            },
        }
        result = reporter.aggregate_report(config, payload)
        self.assertTrue(result["phase1_goal_achieved"])
        self.assertEqual(result["failed_hypothesis_checks"], [])

    def test_sensitivity_is_mandatory(self) -> None:
        config = reporter.planner.load_config(CONFIG)
        payload = {
            "episodes": passing_rows(),
            "protected_sensitivity": {
                "direction_fraction": 1.0,
                "eligible_comparisons": 23,
            },
        }
        result = reporter.aggregate_report(config, payload)
        self.assertFalse(result["phase1_goal_achieved"])
        self.assertIn("protected_sensitivity_direction", result["failed_hypothesis_checks"])


if __name__ == "__main__":
    unittest.main()

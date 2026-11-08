#!/usr/bin/env python3
"""Pure tests for direct-v3 validation semantics."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "validate_phase1_one_action_successor_direct_v3.py"
CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_direct_v3.json"


def load_module():
    spec = importlib.util.spec_from_file_location("successor_direct_v3", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


direct_v3 = load_module()


class DirectV3Tests(unittest.TestCase):
    def test_config_preserves_v2_failure_and_fresh_confirmation(self) -> None:
        config = direct_v3.load_config(CONFIG)
        self.assertIn("failed_direct_v2_validation", config["antecedent"])
        self.assertTrue(
            config["confirmation_protocol"]["revealed_v1_test_is_not_confirmation"]
        )

    def test_paired_control_statistic_passes_coherent_synthetic_effect(self) -> None:
        config = direct_v3.load_config(CONFIG)
        rows = []
        for index in range(16):
            tree = {
                checkpoint: {region: 0.001 for region in direct_v3.v2.REGIONS}
                for checkpoint in direct_v3.v2.CHECKPOINTS
            }
            raw = {
                checkpoint: {region: 0.004 for region in direct_v3.v2.REGIONS}
                for checkpoint in direct_v3.v2.CHECKPOINTS
            }
            control = {
                checkpoint: {region: 0.002 for region in direct_v3.v2.REGIONS}
                for checkpoint in direct_v3.v2.CHECKPOINTS
            }
            rows.append(
                {
                    "episode_id": f"validation_{index:03d}",
                    "rmse_m": {"D1": tree, "raw_newton": raw, "no_deformation": raw},
                    "parameter_controls": {
                        "kphi_shuffled": control,
                        "kphi_constant_reference": control,
                    },
                }
            )
        result = direct_v3.aggregate(config, rows)
        self.assertTrue(result["passed"])
        for control in result["parameter_controls"].values():
            self.assertGreater(control["loaded"]["paired_mean_relative_rmse_increase"], 0.02)


if __name__ == "__main__":
    unittest.main()

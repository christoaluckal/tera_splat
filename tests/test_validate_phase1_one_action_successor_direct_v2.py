#!/usr/bin/env python3
"""Pure tests for the prospective direct-v2 validation adapter."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "validate_phase1_one_action_successor_direct_v2.py"
CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_direct_v2.json"


def load_module():
    spec = importlib.util.spec_from_file_location("successor_direct_v2", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


direct_v2 = load_module()


class DirectV2Tests(unittest.TestCase):
    def test_config_freezes_fresh_confirmation_and_local_controls(self) -> None:
        config = direct_v2.load_config(CONFIG)
        protocol = config["confirmation_protocol"]
        self.assertTrue(protocol["fresh_surface_seeds_required"])
        self.assertTrue(protocol["revealed_v1_test_is_not_confirmation"])
        self.assertEqual(protocol["accuracy_regions"], ["footprint", "twice_radius"])
        self.assertEqual(protocol["parameter_control_regions"], ["footprint"])

    def test_reference_differenced_surface_formula(self) -> None:
        initial = np.zeros((2, 2), dtype=np.float32)
        primary = np.ones((2, 2, 2), dtype=np.float32) * 2.0
        reference = np.ones((2, 2, 2), dtype=np.float32) * 0.5
        result = direct_v2.d1_surface(
            initial, primary, reference, gain=1.0, scale=1.0
        )
        np.testing.assert_allclose(result, 3.5)

    def test_aggregate_requires_full_accuracy_and_local_controls(self) -> None:
        config = direct_v2.load_config(CONFIG)
        rows = []
        for index in range(16):
            tree = {
                checkpoint: {region: 0.001 for region in direct_v2.REGIONS}
                for checkpoint in direct_v2.CHECKPOINTS
            }
            raw = {
                checkpoint: {region: 0.004 for region in direct_v2.REGIONS}
                for checkpoint in direct_v2.CHECKPOINTS
            }
            control = {
                checkpoint: {region: 0.002 for region in direct_v2.REGIONS}
                for checkpoint in direct_v2.CHECKPOINTS
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
        result = direct_v2.aggregate(config, rows)
        self.assertTrue(result["passed"])
        self.assertEqual(len(result["checks"]), 20)


if __name__ == "__main__":
    unittest.main()

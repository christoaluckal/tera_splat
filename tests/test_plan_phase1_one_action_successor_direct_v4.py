#!/usr/bin/env python3
"""Pure tests for direct-v4 fresh confirmation planning."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "plan_phase1_one_action_successor_direct_v4.py"
CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_direct_v4.json"


def load_module():
    spec = importlib.util.spec_from_file_location("successor_direct_v4_plan", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


planner = load_module()


class DirectV4PlanTests(unittest.TestCase):
    def test_fresh_membership_is_unique_and_outside_original_94(self) -> None:
        config = planner.load_config(CONFIG)
        contract = planner.original.load_contract(
            planner.require_source(config, "domain_contract")
        )
        test = planner.make_test_episodes(config, contract)
        sensitivity = planner.make_sensitivity_episodes(config, contract)
        planner.validate_episodes(config, contract, test, sensitivity)
        self.assertEqual((len(test), len(sensitivity)), (24, 6))
        self.assertEqual(len({row["input_sha256"] for row in test + sensitivity}), 30)
        self.assertTrue(all(row["target_access"] == "locked" for row in test + sensitivity))

    def test_plan_requires_lock_before_authoritative_validation(self) -> None:
        config = planner.load_config(CONFIG)
        self.assertTrue(
            config["confirmation_protocol"][
                "target_lock_required_before_authoritative_validation"
            ]
        )
        self.assertTrue(config["validation"]["must_run_after_confirmation_plan_freeze"])


if __name__ == "__main__":
    unittest.main()

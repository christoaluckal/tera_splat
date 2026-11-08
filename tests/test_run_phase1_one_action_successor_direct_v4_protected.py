#!/usr/bin/env python3
"""Focused tests for the direct-v4 protected runtime."""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "run_phase1_one_action_successor_direct_v4_protected.py"
CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_direct_v4.json"


def load_module():
    spec = importlib.util.spec_from_file_location("direct_v4_protected", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runtime = load_module()


class DirectV4ProtectedRuntimeTests(unittest.TestCase):
    def test_runtime_uses_fresh_roots_and_two_workers(self) -> None:
        config = runtime.planner.load_config(CONFIG)
        adapted = runtime.runtime_config(config)
        self.assertEqual(adapted["execution"]["workers"], 2)
        self.assertIn("phase1_one_action_successor_direct_v4", adapted["execution"]["output_root"])
        self.assertTrue(adapted["execution"]["surface_root"].endswith("surface_qualification/surfaces"))

    def test_protected_membership_is_exact(self) -> None:
        config = runtime.planner.load_config(CONFIG)
        path = runtime.planner.repo_path(config["execution"]["confirmation_plan"])
        plan = json.loads(path.read_text(encoding="utf-8"))
        rows = runtime.protected_episodes(plan)
        self.assertEqual(len(rows), 30)
        self.assertEqual(sum(row["split"] == "test" for row in rows), 24)
        self.assertEqual(sum(row["split"] == "protected_sensitivity" for row in rows), 6)

    def test_protected_tensor_check_replaces_smoke_sentinel(self) -> None:
        checks = {"no_test_target": False, "finite": True}
        updated = runtime.protected_tensor_checks(checks, True)
        self.assertNotIn("no_test_target", updated)
        self.assertEqual(
            updated,
            {"finite": True, "protected_target_opened_after_joint_unlock": True},
        )


if __name__ == "__main__":
    unittest.main()

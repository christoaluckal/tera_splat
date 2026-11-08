#!/usr/bin/env python3
"""Focused tests for the direct-v4 one-time joint unlock."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "unlock_phase1_one_action_successor_direct_v4.py"
CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_direct_v4.json"


def load_module():
    spec = importlib.util.spec_from_file_location("direct_v4_unlock", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


unlock = load_module()


class DirectV4UnlockTests(unittest.TestCase):
    def test_expected_marker_binds_every_prerequisite(self) -> None:
        config_path = CONFIG.resolve()
        config = unlock.planner.load_config(config_path)
        marker = unlock.expected_marker(config_path, config)
        self.assertEqual(marker["counts"], {"test": 24, "protected_sensitivity": 6})
        self.assertFalse(marker["targets_opened"])
        self.assertEqual(marker["status"], unlock.STATUS)
        self.assertEqual(len(marker["test_lock_sha256"]), 64)
        self.assertEqual(len(marker["sensitivity_lock_sha256"]), 64)
        self.assertEqual(len(marker["surface_qualification_summary_sha256"]), 64)

    def test_protected_targets_are_absent_before_unlock(self) -> None:
        config = unlock.planner.load_config(CONFIG)
        unlock.assert_targets_absent(config)


if __name__ == "__main__":
    unittest.main()

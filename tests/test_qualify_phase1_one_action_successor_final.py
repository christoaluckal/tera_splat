#!/usr/bin/env python3
"""Focused tests for successor final-result qualification."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "qualify_phase1_one_action_successor_final.py"
CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_final_qualification_v1.json"


def load_module():
    spec = importlib.util.spec_from_file_location("successor_final_qualification", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


qualification = load_module()


class FinalQualificationTests(unittest.TestCase):
    def test_config_binds_complete_artifact_set(self) -> None:
        config = qualification.load_config(CONFIG)
        self.assertEqual(len(config["required_artifacts"]), 6)
        self.assertIn("final_report", config["required_artifacts"])
        self.assertIn("original_failed_protected_summary", config["required_artifacts"])

    def test_current_result_qualifies_as_failed(self) -> None:
        config = qualification.load_config(CONFIG)
        result = qualification.qualify(CONFIG, config)
        self.assertEqual(result["status"], "qualified_failed_result")
        self.assertFalse(result["scientific_result"]["phase1_goal_achieved"])
        self.assertTrue(all(result["checks"].values()))


if __name__ == "__main__":
    unittest.main()

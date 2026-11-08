#!/usr/bin/env python3
"""Focused tests for protected post-unlock admission recovery."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "recover_phase1_one_action_successor_protected_admission_v3.py"
CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_protected_admission_recovery_v3.json"


def load_module():
    spec = importlib.util.spec_from_file_location("protected_admission_recovery", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


recovery = load_module()


class ProtectedAdmissionRecoveryTests(unittest.TestCase):
    def test_config_is_artifact_only_and_preserves_qualification(self) -> None:
        config = recovery.load_config(CONFIG)
        self.assertTrue(config["semantics"]["artifact_only"])
        self.assertFalse(config["semantics"]["simulator_rerun_performed"])
        self.assertFalse(config["semantics"]["tensor_array_replacement_performed"])
        self.assertTrue(config["semantics"]["preserve_serial_execution_identity_qualification"])

    def test_false_checks_identifies_only_failed_sentinel(self) -> None:
        row = {"tensor_manifest": {"checks": {"no_test_target": False, "finite": True}}}
        self.assertEqual(recovery.false_checks(row), ["no_test_target"])


if __name__ == "__main__":
    unittest.main()

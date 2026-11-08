#!/usr/bin/env python3
"""Focused tests for the prospective protected Newton recovery."""

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
SCRIPT = SCRIPT_DIR / "recover_phase1_one_action_successor_protected_v1.py"
CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_protected_recovery_v1.json"


def load_module():
    spec = importlib.util.spec_from_file_location("protected_recovery", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


recovery = load_module()


class ProtectedRecoveryTests(unittest.TestCase):
    def test_config_freezes_missing_only_two_process_recovery(self) -> None:
        config = recovery.load_config(CONFIG)
        self.assertEqual(config["execution"]["workers"], 2)
        self.assertTrue(config["semantics"]["preserve_failed_attempt"])
        self.assertTrue(config["semantics"]["generate_only_missing_official_response"])
        self.assertFalse(config["semantics"]["replace_completed_official_response"])
        self.assertFalse(config["semantics"]["allow_additional_retry_without_new_plan"])

    def test_config_refuses_weakened_semantics(self) -> None:
        value = json.loads(CONFIG.read_text(encoding="utf-8"))
        value["semantics"]["replace_completed_official_response"] = True
        with self.assertRaisesRegex(ValueError, "may not be replaced"):
            # Exercise validation without creating an alternate repository config.
            original = recovery.json.loads
            recovery.json.loads = lambda _text: value
            try:
                recovery.load_config(CONFIG)
            finally:
                recovery.json.loads = original

    def test_manifest_checks_fail_closed(self) -> None:
        self.assertEqual(
            recovery.manifest_checks(Path("/definitely/missing/manifest.json")),
            {"exists": False, "finite": False, "guide": False, "preparation": False},
        )


if __name__ == "__main__":
    unittest.main()

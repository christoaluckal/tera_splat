#!/usr/bin/env python3
"""Focused tests for the qualified serial protected recovery."""

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
SCRIPT = SCRIPT_DIR / "recover_phase1_one_action_successor_protected_v2.py"
CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_protected_recovery_v2.json"


def load_module():
    spec = importlib.util.spec_from_file_location("protected_recovery_v2", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


recovery = load_module()


class ProtectedRecoveryV2Tests(unittest.TestCase):
    def test_config_freezes_qualified_serial_missing_only_retry(self) -> None:
        config = recovery.load_config(CONFIG)
        self.assertEqual(config["execution"]["workers"], 1)
        self.assertTrue(config["semantics"]["serial_retry_is_execution_identity_qualification"])
        self.assertFalse(config["semantics"]["may_claim_clean_two_worker_identity"])
        self.assertFalse(config["semantics"]["replace_completed_official_response"])

    def test_config_refuses_clean_two_worker_claim(self) -> None:
        value = json.loads(CONFIG.read_text(encoding="utf-8"))
        value["semantics"]["may_claim_clean_two_worker_identity"] = True
        original = recovery.json.loads
        recovery.json.loads = lambda _text: value
        try:
            with self.assertRaisesRegex(ValueError, "requires may_claim_clean_two_worker_identity=false"):
                recovery.load_config(CONFIG)
        finally:
            recovery.json.loads = original


if __name__ == "__main__":
    unittest.main()

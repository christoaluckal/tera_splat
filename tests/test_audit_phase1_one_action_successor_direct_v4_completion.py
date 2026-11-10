#!/usr/bin/env python3
"""Focused tests for the direct-v4 Phase 1 completion audit."""

from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "audit_phase1_one_action_successor_direct_v4_completion.py"
CONFIG = (
    REPO_ROOT
    / "configs"
    / "phase1_one_action_successor_direct_v4_completion_audit_v1.json"
)


def load_module():
    spec = importlib.util.spec_from_file_location("direct_v4_completion_audit", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


audit = load_module()


class DirectV4CompletionAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = audit.load_config(CONFIG)
        self.payloads, self.identities = audit.evidence_payloads(self.config)

    def checks(self, payloads):
        return audit.completion_checks(
            self.config,
            payloads,
            self.identities,
            continuation_revalidated=True,
            prediction_artifacts_revalidated=True,
            qualification_recomputed=True,
        )

    def test_bound_completion_evidence_passes_pure_checks(self) -> None:
        self.assertTrue(all(self.checks(self.payloads).values()))

    def test_report_failure_cannot_complete_phase1(self) -> None:
        payloads = copy.deepcopy(self.payloads)
        payloads["final_report"]["phase1_goal_achieved"] = False
        checks = self.checks(payloads)
        self.assertFalse(checks["report_passed_coherently"])

    def test_missing_hypothesis_gate_cannot_complete_phase1(self) -> None:
        payloads = copy.deepcopy(self.payloads)
        payloads["final_report"]["hypothesis_checks"].pop(
            "protected_sensitivity_direction"
        )
        checks = self.checks(payloads)
        self.assertFalse(checks["exact_25_hypothesis_checks_passed"])


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Focused tests for the direct-v4 prediction/report revision bridge."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "run_phase1_one_action_successor_direct_v4_reporting_rebind.py"
CONFIG = (
    REPO_ROOT
    / "configs"
    / "phase1_one_action_successor_direct_v4_reporting_rebind_v1.json"
)


def load_module():
    spec = importlib.util.spec_from_file_location("direct_v4_reporting_rebind", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


continuation = load_module()


class DirectV4ReportingRebindTests(unittest.TestCase):
    def test_config_permits_only_prediction_and_report(self) -> None:
        config = continuation.load_config(CONFIG)
        self.assertEqual(config["execution"]["allowed_stages"], ["predict", "report"])
        self.assertTrue(config["semantics"]["reuse_frozen_revision_only_proof"])
        self.assertFalse(
            config["semantics"]["permit_protected_runtime_or_tensor_change"]
        )
        self.assertFalse(
            config["semantics"]["permit_model_threshold_or_claim_boundary_change"]
        )

    def test_bound_admission_and_qualification_plans_exist(self) -> None:
        config = continuation.load_config(CONFIG)
        self.assertTrue(
            continuation.required_file(config, "protected_dataset_summary").is_file()
        )
        self.assertTrue(
            continuation.required_file(config, "final_qualification_plan").is_file()
        )

    def test_non_reporting_stage_is_rejected_before_delegation(self) -> None:
        config = continuation.load_config(CONFIG)
        with self.assertRaisesRegex(ValueError, "does not permit stage"):
            continuation.run_stage(CONFIG, config, "analyze")

    def test_reporting_stage_restores_loader_and_argv(self) -> None:
        config = continuation.load_config(CONFIG)
        direct_path = REPO_ROOT / "configs" / "phase1_one_action_successor_direct_v4.json"
        recovery_config = {"recovery_id": "test"}
        rebound = {"status": "frozen"}
        original_loader = continuation.reporter.protected.load_execution_plan
        original_argv = list(sys.argv)
        observed = {}

        def fake_reporter_main() -> None:
            observed["argv"] = list(sys.argv)
            observed["plan"] = continuation.reporter.protected.load_execution_plan(
                direct_path, {"branch_id": "test"}
            )

        with (
            mock.patch.object(continuation, "load_plan"),
            mock.patch.object(
                continuation, "required_file", return_value=CONFIG
            ),
            mock.patch.object(
                continuation.recovery, "load_config", return_value=recovery_config
            ),
            mock.patch.object(
                continuation.recovery,
                "direct_config_path",
                return_value=direct_path,
            ),
            mock.patch.object(
                continuation.recovery,
                "rebound_execution_plan",
                return_value=rebound,
            ) as rebound_loader,
            mock.patch.object(
                continuation.reporter, "main", side_effect=fake_reporter_main
            ),
        ):
            continuation.run_stage(CONFIG, config, "predict")

        self.assertEqual(observed["argv"][-3:], ["--config", str(direct_path), "--stage", "predict"][-3:])
        self.assertEqual(observed["plan"], rebound)
        rebound_loader.assert_called_once()
        self.assertIs(
            continuation.reporter.protected.load_execution_plan, original_loader
        )
        self.assertEqual(sys.argv, original_argv)


if __name__ == "__main__":
    unittest.main()

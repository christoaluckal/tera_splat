#!/usr/bin/env python3
"""Pure tests for the prospective direct-v4 final qualification."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "qualify_phase1_one_action_successor_direct_v4_final.py"
CONFIG = (
    REPO_ROOT
    / "configs"
    / "phase1_one_action_successor_direct_v4_final_qualification_v1.json"
)


def load_module():
    spec = importlib.util.spec_from_file_location("direct_v4_final_qualification", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


qualification = load_module()


def artifacts(config, passed=True):
    checks = {f"check_{index:02d}": True for index in range(25)}
    if not passed:
        checks["check_24"] = False
    prediction_artifacts = {
        f"member_{index:03d}": {
            "summary_sha256": "a" * 64,
            "archive_sha256": "b" * 64,
        }
        for index in range(30)
    }
    dataset_artifacts = {"member_000:target": "c" * 64}
    report = {
        "status": "passed" if passed else "failed",
        "phase1_goal_achieved": passed,
        "supported_claim_permitted": passed,
        "claim_route": (
            "learned_one_action_direct_surrogate"
            if passed
            else "no_positive_successor_claim"
        ),
        "candidate": config["required_candidate"],
        "claim_boundary": config["requirements"]["claim_boundary"],
        "hypothesis_checks": checks,
        "failed_hypothesis_checks": [] if passed else ["check_24"],
        "prediction_results_sha256": "prediction",
        "protected_dataset_summary_sha256": "dataset",
        "reporting_plan_sha256": config["frozen_inputs"]["reporting_plan"][
            "sha256"
        ],
        "protected_execution_plan_sha256": config["frozen_inputs"][
            "protected_execution_plan"
        ]["sha256"],
        "prediction_artifact_sha256": prediction_artifacts,
        "dataset_artifact_sha256": dataset_artifacts,
    }
    prediction = {
        "status": "protected_predictions_complete",
        "candidate": config["required_candidate"],
        "episodes": [{"episode_id": f"test_{index:03d}"} for index in range(24)],
        "prediction_artifacts": prediction_artifacts,
        "reporting_plan_sha256": config["frozen_inputs"]["reporting_plan"][
            "sha256"
        ],
        "protected_dataset_summary_sha256": "dataset",
        "protected_execution_plan_sha256": config["frozen_inputs"][
            "protected_execution_plan"
        ]["sha256"],
        "dataset_artifact_sha256": dataset_artifacts,
    }
    protected = {
        "status": "passed",
        "prediction_permitted": True,
        "counts": {"total": 30, "test": 24, "protected_sensitivity": 6},
        "checks": {"all_complete": True, "all_admitted": True},
        "protected_execution_plan_sha256": config["frozen_inputs"][
            "protected_execution_plan"
        ]["sha256"],
        "protected_open_sha256": config["frozen_inputs"]["protected_open_marker"][
            "sha256"
        ],
        "artifact_sha256": dataset_artifacts,
    }
    return {
        "final_report": report,
        "prediction_results": prediction,
        "protected_dataset_summary": protected,
    }


class DirectV4FinalQualificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = qualification.load_config(CONFIG)
        self.original_load_json = qualification.load_json
        recovery_path = qualification.repo_path(
            self.config["frozen_inputs"]["revision_rebind_plan"]["path"]
        )

        def fake_load_json(path):
            if Path(path).resolve() == recovery_path:
                return {
                    "changed_execution_identity_keys": ["repository_revisions"],
                    "protected_episode_count": 30,
                    "downstream_artifacts_absent_at_freeze": True,
                    "prediction_permitted": False,
                }
            return self.original_load_json(path)

        qualification.load_json = fake_load_json

    def tearDown(self) -> None:
        qualification.load_json = self.original_load_json

    def test_config_is_outcome_neutral_and_prospective(self) -> None:
        self.assertTrue(
            self.config["semantics"]["accept_coherent_pass_or_failure"]
        )
        self.assertFalse(
            self.config["semantics"][
                "permit_target_inspection_before_qualification_plan_freeze"
            ]
        )
        self.assertEqual(self.config["requirements"]["hypothesis_check_count"], 25)

    def test_coherent_pass_qualifies(self) -> None:
        payloads = artifacts(self.config, passed=True)
        checks = qualification.qualification_checks(
            self.config,
            payloads,
            {"prediction_results": "prediction", "protected_dataset_summary": "dataset"},
        )
        self.assertTrue(all(checks.values()))

    def test_coherent_failure_qualifies_without_claim(self) -> None:
        payloads = artifacts(self.config, passed=False)
        checks = qualification.qualification_checks(
            self.config,
            payloads,
            {"prediction_results": "prediction", "protected_dataset_summary": "dataset"},
        )
        self.assertTrue(all(checks.values()))
        self.assertFalse(payloads["final_report"]["phase1_goal_achieved"])

    def test_incoherent_failure_is_rejected(self) -> None:
        payloads = artifacts(self.config, passed=False)
        payloads["final_report"]["failed_hypothesis_checks"] = []
        checks = qualification.qualification_checks(
            self.config,
            payloads,
            {"prediction_results": "prediction", "protected_dataset_summary": "dataset"},
        )
        self.assertFalse(checks["failed_check_list_exact"])


if __name__ == "__main__":
    unittest.main()

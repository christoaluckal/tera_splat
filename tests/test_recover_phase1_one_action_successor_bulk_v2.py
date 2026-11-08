#!/usr/bin/env python3
"""Focused tests for the artifact-preserving successor bulk recovery."""

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
SCRIPT = SCRIPT_DIR / "recover_phase1_one_action_successor_bulk_v2.py"
CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_bulk_recovery_v2.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


RECOVERY = load_module("phase1_successor_bulk_recovery_v2", SCRIPT)


def admitted_episode(episode_id: str = "episode_ok") -> dict:
    return {
        "episode_id": episode_id,
        "complete": True,
        "admitted": True,
        "numerical_checks": {
            "chrono_accepted": True,
            "preparation_accepted": True,
            "guide": True,
        },
        "interaction_artifact_checks": {
            "within_gross_depth": True,
            "within_gross_affected_fraction": True,
        },
        "tensor_manifest": {
            "checks": {
                "all_expected_shapes": True,
                "all_finite": True,
            }
        },
    }


class SuccessorBulkRecoveryTests(unittest.TestCase):
    def test_config_uses_independently_prospective_component_contract(self) -> None:
        config = RECOVERY.load_config(CONFIG)
        self.assertEqual(
            config["guide_contract"], RECOVERY.EXPECTED_GUIDE_TOLERANCES
        )
        self.assertTrue(
            config["guide_contract_precedent"][
                "selected_before_successor_bulk_failure_was_observed"
            ]
        )
        self.assertTrue(all(config["policy"].values()))

    def test_component_contract_recovers_only_horizontal_speed_margin(self) -> None:
        manifest = {
            "cylinder": {
                "guide_constraint_error": {
                    "horizontal_position_error_m": 2.0e-9,
                    "horizontal_speed_mps": 1.3220210438912167e-6,
                    "angular_speed_radps": 7.0e-7,
                    "orientation_quaternion_error": 2.0e-9,
                },
                "guide_constraint_passed": False,
            }
        }
        result = RECOVERY.evaluate_guide(
            manifest, RECOVERY.EXPECTED_GUIDE_TOLERANCES
        )
        self.assertTrue(result["passed"])
        self.assertFalse(result["legacy_manifest_passed"])
        self.assertTrue(all(result["component_checks"].values()))

    def test_component_contract_remains_fail_closed_for_other_components(self) -> None:
        manifest = {
            "cylinder": {
                "guide_constraint_error": {
                    "horizontal_position_error_m": 1.1e-6,
                    "horizontal_speed_mps": 1.0e-7,
                    "angular_speed_radps": 1.0e-7,
                    "orientation_quaternion_error": 1.0e-9,
                },
                "guide_constraint_passed": False,
            }
        }
        result = RECOVERY.evaluate_guide(
            manifest, RECOVERY.EXPECTED_GUIDE_TOLERANCES
        )
        self.assertFalse(result["passed"])
        self.assertFalse(
            result["component_checks"]["horizontal_position_error_m"]
        )

    def test_expected_legacy_failure_shape_rejects_extra_failures(self) -> None:
        config = {
            "expected_legacy_failure_ids": ["episode_bad"],
            "expected_legacy_failed_episode_checks": ["guide"],
        }
        bad = admitted_episode("episode_bad")
        bad["admitted"] = False
        bad["numerical_checks"]["guide"] = False
        summary = {
            "episodes": {
                "episode_ok": admitted_episode(),
                "episode_bad": bad,
            }
        }
        RECOVERY.require_expected_legacy_failure(config, summary)
        changed = copy.deepcopy(summary)
        changed["episodes"]["episode_bad"]["tensor_manifest"]["checks"][
            "all_finite"
        ] = False
        with self.assertRaisesRegex(RuntimeError, "failure checks changed"):
            RECOVERY.require_expected_legacy_failure(config, changed)


if __name__ == "__main__":
    unittest.main()

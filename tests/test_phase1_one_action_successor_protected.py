#!/usr/bin/env python3
"""Tests for the selection-gated successor protected-data bridge."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "run_phase1_one_action_successor_protected.py"
CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_evaluation_v1.json"
DATASET_PLAN = (
    REPO_ROOT
    / "outputs"
    / "validity_experiment"
    / "newton"
    / "phase1_one_action_successor_contract_v1"
    / "dataset_plan.json"
)


def load_module():
    spec = importlib.util.spec_from_file_location("successor_protected", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


protected = load_module()


def config() -> dict:
    return protected.evaluation.load_config(CONFIG)


def plan() -> dict:
    dataset = json.loads(DATASET_PLAN.read_text(encoding="utf-8"))
    selected = protected.evaluation.selected_membership(config(), dataset)
    return {
        "episodes": selected,
        "episode_ids": {
            split: [item["episode_id"] for item in rows]
            for split, rows in selected.items()
        },
        "selection_summary_sha256": "selection",
        "test_lock_sha256": protected.evaluation.EXPECTED_TEST_LOCK_SHA256,
        "sensitivity_lock_sha256": protected.evaluation.EXPECTED_SENSITIVITY_LOCK_SHA256,
    }


class SuccessorProtectedTests(unittest.TestCase):
    def test_runtime_reuses_proven_schema_and_routes_shared_output_roots(self) -> None:
        cfg = config()
        runtime = protected.runtime_config(cfg)
        self.assertEqual(
            runtime["dataset_id"], "phase1_one_action_successor_protected_v1"
        )
        self.assertEqual(
            runtime["execution"]["output_root"],
            cfg["execution"]["dataset_output_root"],
        )
        self.assertEqual(
            runtime["execution"]["chrono_output_root"],
            cfg["execution"]["chrono_output_root"],
        )
        self.assertEqual(runtime["execution"]["workers"], 2)
        self.assertEqual(runtime["tensor_schema"]["global_parameter_vector"], ["bekker_kphi"])
        self.assertIn("plastic_jacobian", runtime["tensor_schema"]["excluded_fields"])

    def test_protected_membership_is_exactly_24_test_plus_6_sensitivity(self) -> None:
        episodes = protected.protected_episodes(plan())
        self.assertEqual(len(episodes), 30)
        self.assertEqual(sum(item["split"] == "test" for item in episodes), 24)
        self.assertEqual(
            sum(item["split"] == "protected_sensitivity" for item in episodes),
            6,
        )
        changed = plan()
        changed["episodes"]["test"].pop()
        with self.assertRaisesRegex(ValueError, "30 unique"):
            protected.protected_episodes(changed)

    def test_episode_subset_refuses_unknown_identity(self) -> None:
        episodes = protected.protected_episodes(plan())
        selected = protected.choose_episodes(
            episodes, [episodes[0]["episode_id"]]
        )
        self.assertEqual(len(selected), 1)
        with self.assertRaisesRegex(ValueError, "unknown protected"):
            protected.choose_episodes(episodes, ["not-in-plan"])

    def test_runtime_plan_rebinds_proven_bed_helpers_to_evaluation_plan(self) -> None:
        cfg = config()
        frozen = plan()
        runtime_plan = protected.configure_runtime_plan(cfg, frozen)
        self.assertEqual(len(runtime_plan["episodes"]), 30)
        self.assertEqual(
            protected.smoke.base.plan_path({}),
            protected.evaluation.plan_path(cfg),
        )

    def test_summary_requires_all_30_admitted_before_prediction(self) -> None:
        cfg = config()
        frozen = plan()
        runtime_plan = protected.configure_runtime_plan(cfg, frozen)
        runtime = protected.runtime_config(cfg)
        rows = [
            {
                "episode_id": item["episode_id"],
                "split": item["split"],
                "complete": True,
                "admitted": True,
            }
            for item in runtime_plan["episodes"]
        ]
        by_id = {item["episode_id"]: item for item in rows}
        with tempfile.TemporaryDirectory() as directory:
            cfg["execution"]["output_root"] = str(Path(directory) / "evaluation")
            protected.evaluation.write_json(
                protected.evaluation.plan_path(cfg), frozen
            )
            protected.evaluation.write_json(
                protected.evaluation.opened_path(cfg), {"targets_opened": True}
            )
            with (
                mock.patch.object(
                    protected.smoke.base,
                    "analyze_episode",
                    side_effect=lambda _runtime, _contract, item: by_id[item["episode_id"]],
                ),
                mock.patch.object(
                    protected.evaluation,
                    "require_opened",
                    return_value={"targets_opened": True},
                ),
                mock.patch.object(
                    protected.evaluation,
                    "protected_artifact_identity",
                    return_value={"artifact": "sha"},
                ),
            ):
                result = protected.summarize(
                    cfg, runtime, {}, frozen, runtime_plan
                )
                self.assertEqual(result["status"], "passed")
                self.assertTrue(result["prediction_permitted"])
                by_id[rows[0]["episode_id"]]["admitted"] = False
                result = protected.summarize(
                    cfg, runtime, {}, frozen, runtime_plan
                )
                self.assertEqual(result["status"], "failed_or_incomplete")
                self.assertFalse(result["prediction_permitted"])


if __name__ == "__main__":
    unittest.main()

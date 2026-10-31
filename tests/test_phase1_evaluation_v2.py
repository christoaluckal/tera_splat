#!/usr/bin/env python3
"""Focused tests for the prospective Phase 1 v2 recovery contract."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative_path: str):
    path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


evaluation = load_module(
    "phase1_evaluation_v2_runtime", "scripts/evaluate_phase1_bed_state.py"
)
planner = load_module(
    "phase1_evaluation_v2_planner", "scripts/plan_phase1_evaluation_v2.py"
)
dataset = sys.modules["run_phase1_dataset"]


class Phase1EvaluationV2Tests(unittest.TestCase):
    def test_config_freezes_recovery_guide_and_execution_identity(self) -> None:
        config = evaluation.load_evaluation_config(
            REPO_ROOT / "configs" / "phase1_evaluation_v2.json"
        )
        self.assertEqual(config["evaluation_id"], "phase1_bed_state_evaluation_v2")
        self.assertEqual(config["execution"]["newton_workers"], 2)
        self.assertEqual(
            config["guide_tolerances"]["horizontal_speed_mps"], 5.0e-6
        )
        self.assertTrue(
            config["recovery_v2"]["reuse_selected_models_without_refit"]
        )
        self.assertEqual(
            config["recovery_v2"]["selection_summary_sha256"],
            "bc2b77f3ca66b2a9eaffac681e6180dc12c4ad200db37909624924d7850e8b79",
        )

    def test_new_manifest_is_unique_disjoint_and_group_complete(self) -> None:
        config = planner.load_config(planner.DEFAULT_CONFIG)
        contract = planner.contract_screen.load_contract(
            planner.repo_path(config["phase1_contract"])
        )
        v1_plan = json.loads(
            planner.repo_path(
                "outputs/validity_experiment/newton/phase1_bed_state_v1/dataset_plan.json"
            ).read_text(encoding="utf-8")
        )
        episodes = planner.build_episodes(contract, v1_plan)
        audit = planner.build_overlap_audit(episodes, v1_plan)
        self.assertEqual(len(episodes), 24)
        self.assertTrue(audit["passed"], audit)
        self.assertEqual(
            Counter(item["holdout_group"] for item in episodes),
            Counter(config["membership"]["required_holdout_groups"]),
        )
        self.assertEqual(
            {int(item["initial_surface_seed"]) for item in episodes},
            {1101, 1102, 1103, 1104, 3102},
        )
        manifest = {
            "episodes": {"test": episodes},
            "test_lock_sha256": planner.contract_screen.canonical_sha256(
                [
                    {
                        "episode_id": item["episode_id"],
                        "input_sha256": item["input_sha256"],
                    }
                    for item in episodes
                ]
            ),
        }
        selected = evaluation.selected_test_episodes(config, manifest)
        self.assertEqual(selected, episodes)

    def test_component_guide_contract_is_prospective_and_dimensional(self) -> None:
        v1 = evaluation.load_evaluation_config(evaluation.DEFAULT_CONFIG)
        v2 = evaluation.load_evaluation_config(
            REPO_ROOT / "configs" / "phase1_evaluation_v2.json"
        )
        manifest = {
            "cylinder": {
                "guide_constraint_error": {
                    "horizontal_position_error_m": 2.0e-7,
                    "horizontal_speed_mps": 2.0e-6,
                    "angular_speed_radps": 2.0e-7,
                    "orientation_quaternion_error": 2.0e-7,
                },
                "guide_constraint_tolerance": 1.0e-6,
                "guide_constraint_passed": False,
            }
        }
        self.assertFalse(evaluation.evaluate_guide_contract(v1, manifest)["passed"])
        result = evaluation.evaluate_guide_contract(v2, manifest)
        self.assertTrue(result["passed"])
        self.assertFalse(result["legacy_manifest_passed"])
        manifest["cylinder"]["guide_constraint_error"][
            "horizontal_position_error_m"
        ] = 2.0e-6
        self.assertFalse(evaluation.evaluate_guide_contract(v2, manifest)["passed"])

    def test_v2_reserved_surface_override_does_not_change_v1_routing(self) -> None:
        contract = evaluation.load_contract(
            REPO_ROOT / "configs" / "phase1_bed_state_v1.json"
        )
        v1 = evaluation.load_evaluation_config(evaluation.DEFAULT_CONFIG)
        v2 = evaluation.load_evaluation_config(
            REPO_ROOT / "configs" / "phase1_evaluation_v2.json"
        )
        self.assertEqual(
            dataset.surface_input_root(v1, contract, 3101),
            dataset.screening.surface_dir(contract, 3101),
        )
        self.assertEqual(
            dataset.surface_input_root(v2, contract, 1101),
            dataset.screening.surface_dir(contract, 1101),
        )
        self.assertEqual(
            dataset.surface_input_root(v2, contract, 3102),
            planner.repo_path(v2["surface_qualification"]["root"])
            / "surface_3102",
        )

    def test_target_absence_guard_detects_new_v2_episode_artifacts(self) -> None:
        config = planner.load_config(planner.DEFAULT_CONFIG)
        with tempfile.TemporaryDirectory() as directory:
            modified = json.loads(json.dumps(config))
            root = Path(directory)
            modified["execution"]["output_root"] = str(root / "evaluation")
            modified["execution"]["chrono_output_root"] = str(root / "chrono")
            manifest = {
                "episodes": {
                    "test": [{"episode_id": "p1_v2_test_unseen-position_000"}]
                }
            }
            planner.assert_targets_absent(modified, manifest)
            artifact = (
                Path(modified["execution"]["output_root"])
                / "episodes"
                / "p1_v2_test_unseen-position_000"
            )
            artifact.mkdir(parents=True)
            with self.assertRaisesRegex(RuntimeError, "already exist"):
                planner.assert_targets_absent(modified, manifest)


if __name__ == "__main__":
    unittest.main()

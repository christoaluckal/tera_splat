#!/usr/bin/env python3
"""Tests for the target-free Phase 1 one-action successor plan."""

from __future__ import annotations

import copy
import importlib.util
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "plan_phase1_one_action_successor.py"
SPEC = importlib.util.spec_from_file_location("phase1_successor_plan", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class Phase1OneActionSuccessorPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract_path = REPO_ROOT / "configs" / "phase1_one_action_successor_contract_v1.json"
        self.contract = MODULE.load_contract(self.contract_path)
        self.plan = MODULE.build_plan(self.contract_path, self.contract)

    def test_plan_is_deterministic_target_free_and_has_declared_counts(self) -> None:
        repeated = MODULE.build_plan(self.contract_path, self.contract)
        self.assertEqual(self.plan["episode_manifest_sha256"], repeated["episode_manifest_sha256"])
        self.assertEqual(self.plan["test_lock_sha256"], repeated["test_lock_sha256"])
        self.assertEqual(self.plan["sensitivity_lock_sha256"], repeated["sensitivity_lock_sha256"])
        self.assertEqual(self.plan["counts"], {"train": 48, "validation": 16, "test": 24, "protected_sensitivity": 6})
        self.assertTrue(self.plan["target_free"])
        serialized = json.dumps(self.plan["episodes"])
        for forbidden in ("loaded_heightmap", "post_unload_heightmap", "chrono_target", "target_path"):
            self.assertNotIn(forbidden, serialized)

    def test_all_94_inputs_are_unique_and_inside_the_screened_domain(self) -> None:
        episodes = [item for split in self.plan["episodes"].values() for item in split]
        self.assertEqual(len(episodes), 94)
        self.assertEqual(len({item["episode_id"] for item in episodes}), 94)
        self.assertEqual(len({item["input_sha256"] for item in episodes}), 94)
        for item in episodes:
            physical = {
                key: value
                for key, value in item.items()
                if key not in {
                    "episode_id",
                    "split",
                    "holdout_group",
                    "input_sha256",
                    "target_access",
                }
            }
            self.assertEqual(item["input_sha256"], MODULE.canonical_sha256(physical))
        for item in episodes:
            self.assertLessEqual(math.hypot(*item["center_xy_m"]), 0.1 + 1.0e-12)
            self.assertGreaterEqual(item["normal_force_n"], 30.65625)
            self.assertLessEqual(item["normal_force_n"], 45.984375)
            self.assertGreaterEqual(item["soil_parameters"]["bekker_kphi"], 1500000.0)
            self.assertLessEqual(item["soil_parameters"]["bekker_kphi"], 2000000.0)
            self.assertEqual(item["soil_parameters"]["mohr_friction_deg"], 30.0)
            self.assertEqual(item["soil_parameters"]["bekker_kc"], 0.0)

    def test_surface_partitions_and_test_groups_are_disjoint_and_present(self) -> None:
        groups = self.contract["initial_surface_domain"]["surface_seeds"]
        train, validation, test = set(groups["train"]), set(groups["validation_reserved"]), set(groups["test_reserved"])
        self.assertFalse(train & validation)
        self.assertFalse(train & test)
        self.assertFalse(validation & test)
        self.assertEqual({item["initial_surface_seed"] for item in self.plan["episodes"]["train"]}, train)
        self.assertTrue(validation.issubset({item["initial_surface_seed"] for item in self.plan["episodes"]["validation"]}))
        self.assertTrue(test.issubset({item["initial_surface_seed"] for item in self.plan["episodes"]["test"]}))
        counts: dict[str, int] = {}
        for item in self.plan["episodes"]["test"]:
            counts[item["holdout_group"]] = counts.get(item["holdout_group"], 0) + 1
            self.assertEqual(item["target_access"], "locked")
        self.assertEqual(counts, self.contract["dataset"]["test_group_counts"])

    def test_protected_sensitivity_is_a_locked_matched_two_by_three_sweep(self) -> None:
        values = self.plan["episodes"]["protected_sensitivity"]
        self.assertEqual(len(values), 6)
        self.assertEqual(len({(item["initial_surface_seed"], tuple(item["center_xy_m"]), item["radius_m"]) for item in values}), 1)
        self.assertEqual({item["normal_force_n"] for item in values}, {30.65625, 45.984375})
        self.assertEqual({item["soil_parameters"]["bekker_kphi"] for item in values}, {1500000.0, 1750000.0, 2000000.0})
        self.assertTrue(all(item["target_access"] == "locked" for item in values))
        expected = MODULE.canonical_sha256([{"episode_id": item["episode_id"], "input_sha256": item["input_sha256"]} for item in values])
        self.assertEqual(self.plan["sensitivity_lock_sha256"], expected)

    def test_smoke_reuses_declared_train_validation_members_and_preserves_protection(self) -> None:
        smoke = self.plan["smoke_membership"]
        self.assertEqual(len(smoke["train"]), 8)
        self.assertEqual(len(smoke["validation"]), 4)
        train_ids = {item["episode_id"] for item in self.plan["episodes"]["train"]}
        validation_ids = {item["episode_id"] for item in self.plan["episodes"]["validation"]}
        self.assertTrue(set(smoke["train"]).issubset(train_ids))
        self.assertTrue(set(smoke["validation"]).issubset(validation_ids))
        self.assertTrue(self.plan["permissions"]["smoke_train_validation_target_generation"])
        self.assertFalse(self.plan["permissions"]["remaining_train_validation_target_generation"])
        self.assertFalse(self.plan["permissions"]["test_or_protected_sensitivity_target_generation"])
        self.assertFalse(self.plan["permissions"]["training"])

    def test_contract_rejects_domain_or_model_scope_expansion(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["chrono"]["soil_parameters"]["varied"]["mohr_friction_deg"] = {"minimum": 25.0, "maximum": 31.0}
        with self.assertRaisesRegex(ValueError, "vary only"):
            MODULE.validate_contract(self.contract_path, changed)
        changed = copy.deepcopy(self.contract)
        changed["tensor_schema"]["excluded_inputs"].remove("plastic_jacobian")
        with self.assertRaisesRegex(ValueError, "Plastic|plastic"):
            MODULE.validate_contract(self.contract_path, changed)
        changed = copy.deepcopy(self.contract)
        changed["permissions_after_dataset_plan_freeze"]["training"] = True
        with self.assertRaisesRegex(ValueError, "permissions"):
            MODULE.validate_contract(self.contract_path, changed)

    def test_frozen_plan_refuses_incompatible_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dataset_plan.json"
            MODULE.write_plan(path, self.plan)
            MODULE.write_plan(path, self.plan)
            changed = copy.deepcopy(self.plan)
            changed["test_lock_sha256"] = "0" * 64
            with self.assertRaisesRegex(RuntimeError, "different frozen plan"):
                MODULE.write_plan(path, changed)


if __name__ == "__main__":
    unittest.main()

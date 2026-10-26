#!/usr/bin/env python3
"""Tests for the prospective Phase 1 contract and target-free dataset plan."""

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
SCRIPT = REPO_ROOT / "scripts" / "run_phase1_contract_screen.py"
SPEC = importlib.util.spec_from_file_location("phase1_contract_screen", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class Phase1ContractScreenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract_path = REPO_ROOT / "configs" / "phase1_bed_state_v1.json"
        self.contract = MODULE.load_contract(self.contract_path)
        self.plan = MODULE.build_plan(self.contract_path, self.contract)

    def test_plan_is_deterministic_and_has_locked_counts(self) -> None:
        repeated = MODULE.build_plan(self.contract_path, self.contract)
        self.assertEqual(self.plan["episode_manifest_sha256"], repeated["episode_manifest_sha256"])
        self.assertEqual(self.plan["test_lock_sha256"], repeated["test_lock_sha256"])
        self.assertEqual(
            self.plan["counts"],
            {"train": 48, "validation": 16, "test": 24},
        )
        self.assertTrue(self.plan["target_free"])
        self.assertFalse(self.plan["screening"]["bulk_dataset_permitted"])

    def test_every_episode_is_unique_and_inside_the_domain(self) -> None:
        episodes = [
            episode
            for split in ("train", "validation", "test")
            for episode in self.plan["episodes"][split]
        ]
        self.assertEqual(len(episodes), 88)
        self.assertEqual(len({value["episode_id"] for value in episodes}), 88)
        self.assertEqual(len({value["input_sha256"] for value in episodes}), 88)
        for episode in episodes:
            x, y = episode["center_xy_m"]
            self.assertLessEqual(math.hypot(x, y), 0.1 + 1.0e-12)
            self.assertGreaterEqual(episode["normal_force_n"], 30.65625)
            self.assertLessEqual(episode["normal_force_n"], 45.984375)
            self.assertGreaterEqual(
                episode["soil_parameters"]["bekker_kphi"], 640000.0
            )
            self.assertLessEqual(
                episode["soil_parameters"]["bekker_kphi"], 960000.0
            )
            self.assertGreaterEqual(
                episode["soil_parameters"]["mohr_friction_deg"], 24.0
            )
            self.assertLessEqual(
                episode["soil_parameters"]["mohr_friction_deg"], 32.0
            )

    def test_test_groups_and_targets_are_protected(self) -> None:
        counts: dict[str, int] = {}
        for episode in self.plan["episodes"]["test"]:
            group = episode["holdout_group"]
            counts[group] = counts.get(group, 0) + 1
            self.assertEqual(episode["target_access"], "locked")
        self.assertEqual(counts, self.contract["dataset"]["test_group_counts"])
        self.assertEqual(
            self.plan["test_lock_sha256"],
            MODULE.canonical_sha256(
                [
                    {
                        "episode_id": episode["episode_id"],
                        "input_sha256": episode["input_sha256"],
                    }
                    for episode in self.plan["episodes"]["test"]
                ]
            ),
        )
        serialized = json.dumps(self.plan["episodes"])
        for forbidden in (
            "loaded_heightmap",
            "post_unload_heightmap",
            "chrono_target",
            "target_path",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_surface_seed_partitions_are_present_and_disjoint(self) -> None:
        groups = self.contract["initial_surface_domain"]["surface_seeds"]
        train = set(groups["train"])
        validation = set(groups["validation_reserved"])
        test = set(groups["test_reserved"])
        self.assertFalse(train & validation)
        self.assertFalse(train & test)
        self.assertFalse(validation & test)
        self.assertEqual(
            {episode["initial_surface_seed"] for episode in self.plan["episodes"]["train"]},
            train,
        )
        self.assertTrue(
            validation.issubset(
                {
                    episode["initial_surface_seed"]
                    for episode in self.plan["episodes"]["validation"]
                }
            )
        )
        self.assertTrue(
            test.issubset(
                {
                    episode["initial_surface_seed"]
                    for episode in self.plan["episodes"]["test"]
                }
            )
        )

    def test_screening_contains_material_corners_center_and_all_surfaces(self) -> None:
        material = self.plan["screening"]["material_cases"]
        self.assertEqual(len(material), 5)
        self.assertEqual(
            {
                (case["bekker_kphi"], case["mohr_friction_deg"])
                for case in material
            },
            {
                (640000.0, 24.0),
                (640000.0, 32.0),
                (960000.0, 24.0),
                (960000.0, 32.0),
                (800000.0, 28.0),
            },
        )
        self.assertEqual(len(self.plan["screening"]["surface_cases"]), 6)

    def test_contract_rejects_relaxed_split_and_surface_guards(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["dataset"]["counts"]["test"] = 23
        with self.assertRaisesRegex(ValueError, "48/16/24"):
            MODULE.validate_contract(self.contract_path, modified)
        modified = copy.deepcopy(self.contract)
        modified["initial_surface_domain"]["surface_seeds"]["test_reserved"] = [1101]
        with self.assertRaisesRegex(ValueError, "disjoint"):
            MODULE.validate_contract(self.contract_path, modified)

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

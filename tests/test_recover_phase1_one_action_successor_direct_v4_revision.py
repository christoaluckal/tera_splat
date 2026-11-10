#!/usr/bin/env python3
"""Focused tests for the direct-v4 repository-revision rebind."""

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
SCRIPT = SCRIPT_DIR / "recover_phase1_one_action_successor_direct_v4_revision.py"
CONFIG = (
    REPO_ROOT
    / "configs"
    / "phase1_one_action_successor_direct_v4_revision_rebind_v1.json"
)


def load_module():
    spec = importlib.util.spec_from_file_location("direct_v4_revision_rebind", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


recovery = load_module()


class DirectV4RevisionRebindTests(unittest.TestCase):
    def test_config_allows_only_revision_rebind_after_chrono(self) -> None:
        config = recovery.load_config(CONFIG)
        self.assertEqual(config["execution"]["workers"], 2)
        self.assertNotIn("chrono", config["execution"]["allowed_stages"])
        self.assertTrue(config["semantics"]["forbid_chrono_rerun"])
        self.assertFalse(config["semantics"]["permit_target_inspection_before_prediction"])
        self.assertFalse(config["semantics"]["permit_threshold_or_model_change"])
        self.assertFalse(config["semantics"]["permit_positive_claim"])

    def test_revision_only_validator_rejects_any_other_change(self) -> None:
        config = recovery.load_config(CONFIG)
        frozen = {
            key: f"same-{key}" for key in recovery.protected.STABLE_PLAN_KEYS
        }
        frozen["repository_revisions"] = config["repository_revisions"]["frozen"]
        current = dict(frozen)
        current["repository_revisions"] = config["repository_revisions"]["rebound"]
        recovery.validate_revision_only_difference(frozen, current, config)
        current["source_sha256"] = {"changed": "true"}
        with self.assertRaisesRegex(RuntimeError, "not revision-only"):
            recovery.validate_revision_only_difference(frozen, current, config)

    def test_config_refuses_target_inspection_permission(self) -> None:
        value = json.loads(CONFIG.read_text(encoding="utf-8"))
        value["semantics"]["permit_target_inspection_before_prediction"] = True
        original = recovery.json.loads
        recovery.json.loads = lambda _text: value
        try:
            with self.assertRaisesRegex(
                ValueError,
                "requires permit_target_inspection_before_prediction=false",
            ):
                recovery.load_config(CONFIG)
        finally:
            recovery.json.loads = original

    def test_downstream_absence_covers_partial_directories_and_logs(self) -> None:
        original = recovery.planner.repo_path
        recovery.planner.repo_path = lambda value: Path("/audit") / str(value)
        try:
            paths = recovery.downstream_paths(
                {
                    "execution": {
                        "dataset_output_root": "dataset",
                        "output_root": "output",
                    }
                },
                {
                    "surface_seeds": [5101],
                    "episodes": [{"episode_id": "protected_000"}],
                },
            )
        finally:
            recovery.planner.repo_path = original
        expected = {
            Path("/audit/dataset/newton_priors"),
            Path("/audit/dataset/episodes/protected_000/newton_response"),
            Path("/audit/dataset/episodes/protected_000/tensors"),
            Path("/audit/dataset/episodes/protected_000/logs/newton_response.log"),
        }
        self.assertTrue(expected.issubset(set(paths)))

    def test_chrono_acceptance_requires_all_30_members(self) -> None:
        episodes = [{"episode_id": f"protected_{index:03d}"} for index in range(30)]
        original_context = recovery.protected.context
        original_result = recovery.protected.smoke.chrono_result
        recovery.protected.context = lambda *_args: ({}, {}, {}, {})
        recovery.protected.smoke.chrono_result = lambda _runtime, _contract, episode: {
            "complete": True,
            "accepted": episode["episode_id"] != "protected_029",
            "checks": {"identity": True},
            "loaded_time_s": 0.349,
            "valid_cells": 1,
        }
        try:
            with self.assertRaisesRegex(RuntimeError, "protected_029"):
                recovery.chrono_acceptance(Path("direct.json"), {}, {"episodes": episodes})
        finally:
            recovery.protected.context = original_context
            recovery.protected.smoke.chrono_result = original_result


if __name__ == "__main__":
    unittest.main()

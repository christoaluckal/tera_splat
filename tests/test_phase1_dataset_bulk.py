#!/usr/bin/env python3
"""Focused tests for the locked Phase 1 train/validation bulk route."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_phase1_dataset_bulk.py"
CONFIG_PATH = REPO_ROOT / "configs" / "phase1_dataset_bulk_v1.json"
DATASET_PLAN_PATH = (
    REPO_ROOT
    / "outputs"
    / "validity_experiment"
    / "newton"
    / "phase1_bed_state_v1"
    / "dataset_plan.json"
)

spec = importlib.util.spec_from_file_location("run_phase1_dataset_bulk", SCRIPT_PATH)
assert spec and spec.loader
bulk = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bulk
spec.loader.exec_module(bulk)


def config() -> dict:
    return bulk.load_bulk_config(CONFIG_PATH)


def frozen_plan() -> dict:
    return json.loads(DATASET_PLAN_PATH.read_text(encoding="utf-8"))


def test_bulk_membership_is_all_train_validation_and_no_test() -> None:
    cfg = config()
    episodes = bulk.selected_episodes(cfg, frozen_plan())
    assert len(episodes) == 64
    assert sum(item["split"] == "train" for item in episodes) == 48
    assert sum(item["split"] == "validation" for item in episodes) == 16
    assert not any(item["split"] == "test" for item in episodes)
    assert all(item["target_access"] != "locked" for item in episodes)
    assert {item["initial_surface_seed"] for item in episodes} == {
        1101,
        1102,
        1103,
        1104,
        2101,
    }


def test_bulk_config_cannot_request_or_unlock_test_targets(tmp_path: Path) -> None:
    cfg = config()
    assert cfg["membership"]["test"] == 0
    assert "prohibited" in cfg["membership"]["test_policy"]

    invalid = copy.deepcopy(cfg)
    invalid["membership"]["test"] = 24
    path = tmp_path / "invalid_bulk.json"
    path.write_text(json.dumps(invalid), encoding="utf-8")
    with pytest.raises(ValueError, match="test target generation is prohibited"):
        bulk.load_bulk_config(path)


def test_bulk_selection_matches_frozen_manifest_and_lock() -> None:
    plan = frozen_plan()
    episodes = bulk.selected_episodes(config(), plan)
    assert bulk.canonical_sha256(plan["episodes"]) == plan["episode_manifest_sha256"]
    assert bulk.canonical_sha256(episodes) != plan["episode_manifest_sha256"]
    assert plan["test_lock_sha256"] == bulk.canonical_sha256(
        [
            {
                "episode_id": item["episode_id"],
                "input_sha256": item["input_sha256"],
            }
            for item in plan["episodes"]["test"]
        ]
    )


def test_bulk_requires_passing_frozen_smoke_summary() -> None:
    evidence = bulk.require_prerequisites(config())
    assert evidence["smoke"]["status"] == "passed"
    assert evidence["smoke"]["full_dataset_permitted"] is True
    assert evidence["smoke"]["counts"] == {
        "total": 12,
        "train": 8,
        "validation": 4,
        "test": 0,
    }


def test_bulk_tensor_contract_matches_smoke_contract() -> None:
    cfg = config()
    smoke_cfg = bulk.smoke.load_smoke_config(bulk.smoke.DEFAULT_SMOKE_CONFIG)
    bulk_prior = dict(cfg["newton_prior"])
    smoke_prior = dict(smoke_cfg["newton_prior"])
    assert "bulk campaign" in bulk_prior.pop("preparation_reuse_scope")
    smoke_prior.pop("preparation_reuse_scope")
    assert bulk_prior == smoke_prior
    assert cfg["tensor_schema"] == smoke_cfg["tensor_schema"]
    assert cfg["bulk_exit"]["minimum_target_action_rms_m"] == smoke_cfg[
        "smoke_exit"
    ]["minimum_target_action_rms_m"]
    assert cfg["bulk_exit"]["maximum_uncompressed_tensor_bytes_per_episode"] == smoke_cfg[
        "smoke_exit"
    ]["maximum_uncompressed_tensor_bytes_per_episode"]


def test_choose_episodes_rejects_test_identity() -> None:
    plan = {
        "episodes": bulk.selected_episodes(config(), frozen_plan()),
    }
    with pytest.raises(ValueError, match="unknown bulk episodes"):
        bulk.choose_episodes(plan, ["p1_test_unseen-position_000"])

#!/usr/bin/env python3
"""Focused tests for the smoke-gated successor train/validation bulk route."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "run_phase1_one_action_successor_bulk.py"
CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_bulk_v1.json"
DATASET_PLAN = (
    REPO_ROOT
    / "outputs"
    / "validity_experiment"
    / "newton"
    / "phase1_one_action_successor_contract_v1"
    / "dataset_plan.json"
)
SMOKE_PLAN = (
    REPO_ROOT
    / "outputs"
    / "validity_experiment"
    / "newton"
    / "phase1_one_action_successor_contract_v1"
    / "dataset_smoke_v1"
    / "smoke_plan.json"
)
SPEC = importlib.util.spec_from_file_location("phase1_successor_bulk", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def config() -> dict:
    return MODULE.load_config(CONFIG)


def dataset_plan() -> dict:
    return json.loads(DATASET_PLAN.read_text(encoding="utf-8"))


def smoke_plan() -> dict:
    return json.loads(SMOKE_PLAN.read_text(encoding="utf-8"))


def test_full_membership_reuses_twelve_and_generates_only_remaining_fifty_two() -> None:
    cfg = config()
    episodes = MODULE.selected_episodes(cfg, dataset_plan())
    reused, remaining = MODULE.split_smoke_and_remaining(cfg, episodes, smoke_plan())
    assert len(episodes) == 64
    assert len(reused) == 12
    assert len(remaining) == 52
    assert sum(item["split"] == "train" for item in reused) == 8
    assert sum(item["split"] == "validation" for item in reused) == 4
    assert sum(item["split"] == "train" for item in remaining) == 40
    assert sum(item["split"] == "validation" for item in remaining) == 12
    assert {item["initial_surface_seed"] for item in episodes} == {
        4101,
        4102,
        4103,
        4104,
        4201,
    }


def test_config_preserves_both_protected_boundaries_and_shared_smoke_root() -> None:
    cfg = config()
    smoke_cfg = MODULE.smoke.load_config(
        MODULE.fresh.repo_path(cfg["prerequisites"]["smoke_config"])
    )
    assert cfg["membership"]["test"] == 0
    assert cfg["membership"]["protected_sensitivity"] == 0
    assert cfg["execution"]["output_root"] == smoke_cfg["execution"]["output_root"]
    assert cfg["execution"]["chrono_output_root"] == smoke_cfg["execution"]["chrono_output_root"]
    assert cfg["reuse_policy"]["smoke_response_regeneration_prohibited"] is True


def test_config_refuses_any_protected_membership(tmp_path: Path) -> None:
    changed = copy.deepcopy(config())
    changed.pop("smoke_exit")
    changed["membership"]["test"] = 1
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError, match="membership changed"):
        MODULE.load_config(path)


def test_dataset_plan_recomputes_test_and_sensitivity_locks() -> None:
    _path, plan = MODULE.load_dataset_plan(config())
    assert len(plan["episodes"]["test"]) == 24
    assert len(plan["episodes"]["protected_sensitivity"]) == 6
    assert all(
        item["target_access"] == "locked"
        for split in ("test", "protected_sensitivity")
        for item in plan["episodes"][split]
    )


def test_episode_selector_refuses_smoke_regeneration_and_protected_identity() -> None:
    cfg = config()
    episodes = MODULE.selected_episodes(cfg, dataset_plan())
    reused, remaining = MODULE.split_smoke_and_remaining(cfg, episodes, smoke_plan())
    plan = {
        "remaining_episodes": remaining,
        "reused_smoke_episode_ids": [item["episode_id"] for item in reused],
    }
    with pytest.raises(ValueError, match="regeneration is prohibited"):
        MODULE.choose_remaining(plan, [reused[0]["episode_id"]])
    with pytest.raises(ValueError, match="unknown or protected"):
        MODULE.choose_remaining(
            plan,
            [dataset_plan()["episodes"]["test"][0]["episode_id"]],
        )


def test_bulk_planning_refuses_absent_smoke_summary(tmp_path: Path) -> None:
    cfg = config()
    cfg["prerequisites"]["smoke_summary"] = str(tmp_path / "missing_summary.json")
    with pytest.raises(RuntimeError, match="smoke gate is incomplete"):
        MODULE.require_smoke_pass(cfg)


def test_tensor_schema_matches_smoke_and_retains_only_kphi() -> None:
    cfg = config()
    smoke_cfg = MODULE.smoke.load_config(
        MODULE.fresh.repo_path(cfg["prerequisites"]["smoke_config"])
    )
    assert cfg["tensor_schema"] == smoke_cfg["tensor_schema"]
    assert cfg["tensor_schema"]["global_parameter_vector"] == ["bekker_kphi"]
    assert "plastic_jacobian" in cfg["tensor_schema"]["excluded_fields"]


def test_source_manifest_resolves_without_opening_runtime_targets() -> None:
    cfg = config()
    successor_path, _successor, operations_path, runtime = MODULE.smoke.merged_contract(cfg)
    sources = MODULE.source_paths(CONFIG, cfg, successor_path, operations_path, runtime)
    assert sources
    assert all(path.is_file() for path in sources.values())


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))

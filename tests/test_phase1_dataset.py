#!/usr/bin/env python3
"""Focused tests for the prospective Phase 1 smoke dataset contract."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_phase1_dataset.py"
CONFIG_PATH = REPO_ROOT / "configs" / "phase1_dataset_smoke_v1.json"
DATASET_PLAN_PATH = (
    REPO_ROOT
    / "outputs"
    / "validity_experiment"
    / "newton"
    / "phase1_bed_state_v1"
    / "dataset_plan.json"
)

spec = importlib.util.spec_from_file_location("run_phase1_dataset", SCRIPT_PATH)
assert spec and spec.loader
dataset = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dataset
spec.loader.exec_module(dataset)


def config() -> dict:
    return dataset.load_smoke_config(CONFIG_PATH)


def frozen_plan() -> dict:
    return json.loads(DATASET_PLAN_PATH.read_text(encoding="utf-8"))


def test_smoke_membership_is_exactly_eight_train_four_validation() -> None:
    cfg = config()
    episodes = dataset.selected_episodes(cfg, frozen_plan())
    assert len(episodes) == 12
    assert sum(item["split"] == "train" for item in episodes) == 8
    assert sum(item["split"] == "validation" for item in episodes) == 4
    assert not any(item["split"] == "test" for item in episodes)
    assert {item["initial_surface_seed"] for item in episodes} == {
        1101,
        1102,
        1103,
        1104,
        2101,
    }


def test_smoke_never_opens_locked_test_targets(tmp_path: Path) -> None:
    cfg = config()
    assert cfg["membership"]["test"] == []
    episodes = dataset.selected_episodes(cfg, frozen_plan())
    assert all(item["target_access"] != "locked" for item in episodes)

    invalid = copy.deepcopy(cfg)
    invalid["membership"]["test"] = ["p1_test_unseen-position_000"]
    path = tmp_path / "invalid_smoke.json"
    path.write_text(json.dumps(invalid), encoding="utf-8")
    with pytest.raises(ValueError, match="must not open test targets"):
        dataset.load_smoke_config(path)


def test_tensor_contract_admits_only_qualified_mechanics() -> None:
    cfg = config()
    prerequisites = cfg["prerequisites"]
    schema = cfg["tensor_schema"]
    assert prerequisites["qualified_nonkinematic_families"] == [
        "stress",
        "elastic",
    ]
    assert prerequisites["excluded_nonkinematic_families"] == ["plastic"]
    assert "plastic_jacobian" in schema["excluded_fields"]
    assert not any(
        "plastic" in field for field in schema["qualified_h2_fields_per_checkpoint"]
    )
    assert {
        "column_particle_count",
        "column_mass_kg",
        "column_mean_action_velocity_mps",
        "contact_node_count",
        "contact_normal_impulse_ns",
        "column_mean_stress_mean_pa",
        "column_mean_stress_von_mises_pa",
        "column_mean_elastic_jacobian",
        "column_mean_elastic_isochoric_shear",
    } == set(schema["qualified_h2_fields_per_checkpoint"])


def test_targets_are_structurally_separate_from_model_inputs() -> None:
    schema = config()["tensor_schema"]
    assert schema["target_arrays_are_never_model_inputs"] is True
    assert set(schema["targets"]).isdisjoint(schema["core_spatial_inputs"])
    assert set(schema["targets"]).isdisjoint(
        schema["qualified_h2_fields_per_checkpoint"]
    )


def test_box_mean_is_fixed_edge_padded_three_by_three() -> None:
    values = np.arange(9, dtype=np.float64).reshape(3, 3)
    actual = dataset.box_mean_2d(values, 3)
    expected = np.asarray(
        [
            [12.0 / 9.0, 18.0 / 9.0, 24.0 / 9.0],
            [30.0 / 9.0, 36.0 / 9.0, 42.0 / 9.0],
            [48.0 / 9.0, 54.0 / 9.0, 60.0 / 9.0],
        ]
    )
    np.testing.assert_allclose(actual, expected)
    with pytest.raises(ValueError):
        dataset.box_mean_2d(values, 2)


def test_prerequisite_machine_decisions_match_smoke_contract() -> None:
    cfg = config()
    evidence = dataset.require_prerequisites(cfg)
    assert evidence["physical"]["status"] == "passed"
    assert evidence["physical"]["bulk_dataset_permitted"] is True
    assert evidence["latent"]["status"] == "passed"
    assert evidence["latent"]["qualified_nonkinematic_families"] == [
        "stress",
        "elastic",
    ]


def test_fixed_time_prior_cannot_be_target_timed() -> None:
    prior = config()["newton_prior"]
    assert prior["observation_time_mode"] == "independent_fixed"
    assert prior["loaded_duration_s"] == 0.35
    assert prior["post_unload_duration_s"] == 0.25
    assert prior["chrono_target_time_must_not_control_newton_rollout"] is True
    assert prior["strict_mechanics_claim_permitted"] is False

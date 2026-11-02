#!/usr/bin/env python3
"""Focused tests for the prospective successor smoke runner."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "run_phase1_one_action_successor_smoke.py"
CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_smoke_v1.json"
DATASET_PLAN = REPO_ROOT / "outputs" / "validity_experiment" / "newton" / "phase1_one_action_successor_contract_v1" / "dataset_plan.json"
SPEC = importlib.util.spec_from_file_location("phase1_successor_smoke", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def config() -> dict:
    return MODULE.load_config(CONFIG)


def dataset_plan() -> dict:
    return json.loads(DATASET_PLAN.read_text(encoding="utf-8"))


def test_membership_is_exactly_authorized_eight_train_four_validation() -> None:
    cfg = config()
    episodes = MODULE.selected_episodes(cfg, dataset_plan())
    assert len(episodes) == 12
    assert sum(item["split"] == "train" for item in episodes) == 8
    assert sum(item["split"] == "validation" for item in episodes) == 4
    assert {item["initial_surface_seed"] for item in episodes} == {4101, 4102, 4103, 4104}
    assert not cfg["membership"]["test"]
    assert not cfg["membership"]["protected_sensitivity"]
    assert all(item["target_access"] != "locked" for item in episodes)


def test_config_refuses_any_protected_member(tmp_path: Path) -> None:
    changed = copy.deepcopy(config())
    changed["membership"]["test"] = [dataset_plan()["episodes"]["test"][0]["episode_id"]]
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError, match="cannot open protected"):
        MODULE.load_config(path)


def test_runtime_contract_keeps_screened_soil_and_frozen_newton() -> None:
    cfg = config()
    _successor_path, successor, _operations_path, runtime = MODULE.merged_contract(cfg)
    assert set(runtime["chrono"]["soil_parameters"]["varied"]) == {"bekker_kphi"}
    assert runtime["chrono"]["soil_parameters"] == successor["chrono"]["soil_parameters"]
    assert runtime["newton"]["young_modulus_pa"] == 100000.0
    assert runtime["newton"]["selected_dt_s"] == 0.00025
    assert runtime["newton"]["voxel_size_m"] == 0.0078125


def test_chrono_command_binds_every_fixed_soil_parameter() -> None:
    cfg = config()
    _successor_path, _successor, _operations_path, runtime = MODULE.merged_contract(cfg)
    episode = MODULE.selected_episodes(cfg, dataset_plan())[0]
    command = MODULE.chrono_command(cfg, runtime, episode)
    for option in (
        "--bekker-kphi",
        "--bekker-kc",
        "--bekker-n",
        "--mohr-cohesion-pa",
        "--mohr-friction-deg",
        "--janosi-shear-m",
        "--elastic-k-pa-per-m",
        "--damping-r-pa-s-per-m",
        "--vertical-guide",
    ):
        assert option in command


def test_tensor_parameter_adapter_retains_only_kphi(tmp_path: Path) -> None:
    path = tmp_path / "model_inputs.npz"
    np.savez_compressed(path, soil_parameters=np.asarray([1.5e6, 30.0], dtype=np.float32), field=np.ones((2, 2), dtype=np.float32))
    MODULE.adapt_model_inputs(path, 1.75e6)
    with np.load(path, allow_pickle=False) as archive:
        np.testing.assert_array_equal(archive["soil_parameters"], np.asarray([1.75e6], dtype=np.float32))
        np.testing.assert_array_equal(archive["field"], np.ones((2, 2), dtype=np.float32))


def test_tensor_schema_separates_robotics_stress_and_elastic_and_excludes_plastic() -> None:
    schema = config()["tensor_schema"]
    assert schema["global_parameter_vector"] == ["bekker_kphi"]
    assert set(schema["robotics_facing_fields_per_checkpoint"]) == {
        "column_particle_count",
        "column_mass_kg",
        "column_mean_action_velocity_mps",
        "contact_node_count",
        "contact_normal_impulse_ns",
    }
    assert set(schema["optional_stress_fields_per_checkpoint"]) == {"column_mean_stress_mean_pa", "column_mean_stress_von_mises_pa"}
    assert set(schema["optional_elastic_fields_per_checkpoint"]) == {"column_mean_elastic_jacobian", "column_mean_elastic_isochoric_shear"}
    assert "plastic_jacobian" in schema["excluded_fields"]
    assert set(schema["targets"]).isdisjoint(schema["core_spatial_inputs"])


def test_prerequisites_are_hash_bound_and_permit_only_smoke() -> None:
    cfg = config()
    successor_path, _successor, _operations_path, _runtime = MODULE.merged_contract(cfg)
    evidence = MODULE.require_prerequisites(cfg, successor_path)
    assert evidence["directional"]["screen_passed"] is True
    assert evidence["surface"]["all_six_surfaces_qualified"] is True
    assert evidence["surface"]["smoke_target_generation_permitted"] is True
    assert evidence["latent"]["qualified_nonkinematic_families"] == ["stress", "elastic"]


def test_source_manifest_resolves_every_frozen_runtime_source() -> None:
    cfg = config()
    successor_path, _successor, operations_path, runtime = MODULE.merged_contract(cfg)
    sources = MODULE.source_paths(CONFIG, cfg, successor_path, operations_path, runtime)
    assert sources
    assert all(path.is_file() for path in sources.values())


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))

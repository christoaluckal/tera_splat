#!/usr/bin/env python3
"""Freeze the Phase 1 v2 target-free test manifest and qualify surface 3102."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

import phase1_surface
import run_fresh_phase0_repeatability as fresh
import run_phase1_contract_screen as contract_screen


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "phase1_evaluation_v2.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--stage", choices=("manifest", "surface", "verify"), default="manifest"
    )
    return parser.parse_args()


def repo_path(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (REPO_ROOT / path).resolve()


def load_config(path: Path) -> dict[str, Any]:
    value = json.loads(path.resolve().read_text(encoding="utf-8"))
    if value.get("evaluation_id") != "phase1_bed_state_evaluation_v2":
        raise ValueError("unexpected v2 evaluation identity")
    if value.get("status") != "prospective_recovery_before_target_generation":
        raise ValueError("v2 recovery contract must be prospective")
    recovery = value["recovery_v2"]
    if not bool(recovery["reuse_selected_models_without_refit"]):
        raise ValueError("v2 may not refit or reselect models")
    if not bool(
        recovery["v1_test_observations_must_not_affect_training_selection_or_calibration"]
    ):
        raise ValueError("v1 test observations must remain excluded from model choices")
    if int(value["surface_qualification"]["reserved_seed"]) != 3102:
        raise ValueError("v2 reserved surface seed changed")
    return value


def _copy_values(episode: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "center_xy_m": [float(value) for value in episode["center_xy_m"]],
        "normal_force_n": float(episode["normal_force_n"]),
        "bekker_kphi": float(episode["soil_parameters"]["bekker_kphi"]),
        "mohr_friction_deg": float(
            episode["soil_parameters"]["mohr_friction_deg"]
        ),
    }


def _episode(
    contract: dict[str, Any],
    ordinal: int,
    values: dict[str, Any],
    surface_seed: int,
    holdout_group: str,
) -> dict[str, Any]:
    result = contract_screen.make_episode(
        contract,
        "test",
        ordinal,
        values,
        surface_seed,
        holdout_group,
    )
    result["episode_id"] = (
        f"p1_v2_test_{holdout_group.replace('_', '-')}_{ordinal:03d}"
    )
    return result


def build_episodes(
    contract: dict[str, Any], v1_plan: Mapping[str, Any]
) -> list[dict[str, Any]]:
    train = [dict(item) for item in v1_plan["episodes"]["train"]]
    train_seeds = [
        int(value)
        for value in contract["initial_surface_domain"]["surface_seeds"]["train"]
    ]
    reserved_seed = 3102
    action = contract["action_domain"]
    force_bounds = (
        float(action["normal_force_n"]["minimum"]),
        float(action["normal_force_n"]["maximum"]),
    )
    varied = contract["chrono"]["soil_parameters"]["varied"]
    kphi_bounds = (
        float(varied["bekker_kphi"]["minimum"]),
        float(varied["bekker_kphi"]["maximum"]),
    )
    friction_bounds = (
        float(varied["mohr_friction_deg"]["minimum"]),
        float(varied["mohr_friction_deg"]["maximum"]),
    )
    episodes: list[dict[str, Any]] = []
    ordinal = 0

    for index in range(5):
        values = contract_screen.continuous_sample(contract, 4001 + index)
        reference = _copy_values(train[20 + index])
        values.update(
            normal_force_n=reference["normal_force_n"],
            bekker_kphi=reference["bekker_kphi"],
            mohr_friction_deg=reference["mohr_friction_deg"],
        )
        episodes.append(
            _episode(
                contract,
                ordinal,
                values,
                train_seeds[index % len(train_seeds)],
                "unseen_position",
            )
        )
        ordinal += 1

    for index in range(5):
        values = _copy_values(train[25 + index])
        fraction = (2.0 * index + 1.0) / 10.0
        values["normal_force_n"] = contract_screen.scale(fraction, force_bounds)
        episodes.append(
            _episode(
                contract,
                ordinal,
                values,
                train_seeds[index % len(train_seeds)],
                "unseen_force",
            )
        )
        ordinal += 1

    for index in range(5):
        values = _copy_values(train[30 + index])
        fraction = (2.0 * index + 1.0) / 10.0
        values["bekker_kphi"] = contract_screen.scale(fraction, kphi_bounds)
        values["mohr_friction_deg"] = contract_screen.scale(
            1.0 - fraction, friction_bounds
        )
        episodes.append(
            _episode(
                contract,
                ordinal,
                values,
                train_seeds[index % len(train_seeds)],
                "unseen_material_combination",
            )
        )
        ordinal += 1

    for index in range(4):
        episodes.append(
            _episode(
                contract,
                ordinal,
                _copy_values(train[35 + index]),
                reserved_seed,
                "unseen_initial_surface",
            )
        )
        ordinal += 1

    for index in range(5):
        episodes.append(
            _episode(
                contract,
                ordinal,
                contract_screen.continuous_sample(contract, 5001 + index),
                reserved_seed,
                "joint_combination",
            )
        )
        ordinal += 1
    return episodes


def physical_signature(episode: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        int(episode["initial_surface_seed"]),
        *(float(value) for value in episode["center_xy_m"]),
        float(episode["normal_force_n"]),
        float(episode["radius_m"]),
        float(episode["soil_parameters"]["bekker_kphi"]),
        float(episode["soil_parameters"]["mohr_friction_deg"]),
    )


def build_overlap_audit(
    episodes: Sequence[Mapping[str, Any]], v1_plan: Mapping[str, Any]
) -> dict[str, Any]:
    old = [
        episode
        for split in ("train", "validation", "test")
        for episode in v1_plan["episodes"][split]
    ]
    signatures = [physical_signature(item) for item in episodes]
    old_signatures = {physical_signature(item) for item in old}
    train_validation = [
        episode
        for split in ("train", "validation")
        for episode in v1_plan["episodes"][split]
    ]
    old_centers = {
        tuple(float(value) for value in item["center_xy_m"])
        for item in train_validation
    }
    old_forces = {float(item["normal_force_n"]) for item in train_validation}
    old_materials = {
        (
            float(item["soil_parameters"]["bekker_kphi"]),
            float(item["soil_parameters"]["mohr_friction_deg"]),
        )
        for item in train_validation
    }
    position_cases = [
        item for item in episodes if item["holdout_group"] == "unseen_position"
    ]
    force_cases = [
        item for item in episodes if item["holdout_group"] == "unseen_force"
    ]
    material_cases = [
        item
        for item in episodes
        if item["holdout_group"] == "unseen_material_combination"
    ]
    checks = {
        "episode_count": len(episodes) == 24,
        "episode_ids_unique": len({item["episode_id"] for item in episodes}) == 24,
        "physical_inputs_unique": len(set(signatures)) == 24,
        "no_physical_overlap_with_v1_88": not bool(set(signatures) & old_signatures),
        "unseen_position_centers_absent_from_train_validation": all(
            tuple(float(value) for value in item["center_xy_m"]) not in old_centers
            for item in position_cases
        ),
        "unseen_force_values_absent_from_train_validation": all(
            float(item["normal_force_n"]) not in old_forces for item in force_cases
        ),
        "unseen_material_pairs_absent_from_train_validation": all(
            (
                float(item["soil_parameters"]["bekker_kphi"]),
                float(item["soil_parameters"]["mohr_friction_deg"]),
            )
            not in old_materials
            for item in material_cases
        ),
        "reserved_surface_absent_from_v1": 3102
        not in {int(item["initial_surface_seed"]) for item in old},
    }
    return {"checks": checks, "passed": all(checks.values())}


def build_manifest(
    config_path: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    contract_path = repo_path(config["phase1_contract"])
    contract = contract_screen.load_contract(contract_path)
    recovery = config["recovery_v2"]
    v1_plan_path = repo_path(recovery["v1_evaluation_plan"])
    v1_plan = json.loads(v1_plan_path.read_text(encoding="utf-8"))
    if fresh.sha256_file(v1_plan_path) != recovery["v1_evaluation_plan_sha256"]:
        raise RuntimeError("v1 evaluation plan changed")
    original_plan_path = repo_path(
        "outputs/validity_experiment/newton/phase1_bed_state_v1/dataset_plan.json"
    )
    original_plan = json.loads(original_plan_path.read_text(encoding="utf-8"))
    if (
        original_plan["episode_manifest_sha256"]
        != contract_screen.canonical_sha256(original_plan["episodes"])
    ):
        raise RuntimeError("v1 88-input manifest changed")
    episodes = build_episodes(contract, original_plan)
    audit = build_overlap_audit(episodes, original_plan)
    if not audit["passed"]:
        failed = sorted(name for name, passed in audit["checks"].items() if not passed)
        raise RuntimeError(f"v2 overlap audit failed: {failed}")
    groups = Counter(item["holdout_group"] for item in episodes)
    expected_groups = {
        name: int(count)
        for name, count in config["membership"]["required_holdout_groups"].items()
    }
    if dict(groups) != expected_groups:
        raise RuntimeError("v2 holdout groups changed")
    seeds = sorted({int(item["initial_surface_seed"]) for item in episodes})
    if seeds != sorted(int(value) for value in config["membership"]["required_surface_seeds"]):
        raise RuntimeError("v2 surface coverage changed")
    test_identity = [
        {"episode_id": item["episode_id"], "input_sha256": item["input_sha256"]}
        for item in episodes
    ]
    source_paths = {
        "config": config_path.resolve(),
        "planner": Path(__file__).resolve(),
        "evaluator": REPO_ROOT / "scripts" / "evaluate_phase1_bed_state.py",
        "evaluator_tests": REPO_ROOT / "tests" / "test_evaluate_phase1_bed_state.py",
        "v2_tests": REPO_ROOT / "tests" / "test_phase1_evaluation_v2.py",
        "surface_generator": REPO_ROOT / "scripts" / "phase1_surface.py",
    }
    missing = [str(path) for path in source_paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing v2 sources: {missing}")
    return {
        "schema_version": 1,
        "evaluation_id": config["evaluation_id"],
        "status": "target_free_test_manifest_frozen",
        "authority": config["authority"],
        "target_free": True,
        "contract_sha256": fresh.sha256_file(contract_path),
        "source_sha256": {
            name: fresh.sha256_file(path) for name, path in source_paths.items()
        },
        "v1_88_episode_manifest_sha256": original_plan["episode_manifest_sha256"],
        "v1_evaluation_plan_sha256": fresh.sha256_file(v1_plan_path),
        "selection_summary_sha256": recovery["selection_summary_sha256"],
        "episodes": {"test": episodes},
        "counts": {"train": 0, "validation": 0, "test": 24},
        "test_lock_sha256": contract_screen.canonical_sha256(test_identity),
        "episode_manifest_sha256": contract_screen.canonical_sha256(
            {"test": episodes}
        ),
        "overlap_audit": audit,
        "generation_gate": (
            "surface 3102 qualification and frozen evaluator plan must pass before "
            "the explicit v2 unlock may create any target"
        ),
    }


def manifest_path(config: Mapping[str, Any]) -> Path:
    return repo_path(config["dataset_plan"])


def write_manifest(path: Path, manifest: Mapping[str, Any]) -> None:
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        stable = (
            "contract_sha256",
            "source_sha256",
            "episode_manifest_sha256",
            "test_lock_sha256",
            "selection_summary_sha256",
        )
        changed = [name for name in stable if existing.get(name) != manifest.get(name)]
        if changed:
            raise RuntimeError(f"refusing to replace frozen v2 manifest: {changed}")
        return
    fresh.write_json(path, manifest)


def load_frozen_manifest(
    config_path: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    path = manifest_path(config)
    if not path.is_file():
        raise RuntimeError("v2 target-free manifest is absent")
    existing = json.loads(path.read_text(encoding="utf-8"))
    current = build_manifest(config_path, config)
    stable = (
        "contract_sha256",
        "source_sha256",
        "episode_manifest_sha256",
        "test_lock_sha256",
        "selection_summary_sha256",
        "overlap_audit",
    )
    changed = [name for name in stable if existing.get(name) != current.get(name)]
    if changed:
        raise RuntimeError(f"frozen v2 manifest identity changed: {changed}")
    return existing


def qualify_surface(
    config_path: Path, config: Mapping[str, Any], manifest: Mapping[str, Any]
) -> dict[str, Any]:
    contract = contract_screen.load_contract(repo_path(config["phase1_contract"]))
    surface_contract = config["surface_qualification"]
    seed = int(surface_contract["reserved_seed"])
    root = repo_path(surface_contract["root"]) / f"surface_{seed}"
    heightmap_path = root / "initial_heightmap_m.npy"
    generator_path = root / "generator_summary.json"
    native_dir = root / "chrono_scm_roundtrip"
    if not root.exists():
        heightmap, generated = phase1_surface.generate_surface(
            seed, phase1_surface.limits_from_contract(contract)
        )
        root.mkdir(parents=True, exist_ok=False)
        np.save(heightmap_path, heightmap)
        fresh.write_json(generator_path, generated)
    else:
        if not heightmap_path.is_file() or not generator_path.is_file():
            raise RuntimeError("refusing incomplete v2 surface directory")
        heightmap = np.load(heightmap_path, allow_pickle=False)
        generated = json.loads(generator_path.read_text(encoding="utf-8"))
        if (
            phase1_surface.array_sha256(heightmap)
            != generated["metrics"]["array_sha256"]
        ):
            raise RuntimeError("stored v2 surface identity changed")
    if not (native_dir / "summary.json").is_file():
        if native_dir.exists():
            raise RuntimeError("refusing incomplete v2 SCM round-trip directory")
        chrono = contract["chrono"]
        varied = chrono["soil_parameters"]["varied"]
        command = [
            *(str(value) for value in chrono["command"]),
            str(repo_path(chrono["repo"]) / "check_scm_initial_heightmap.py"),
            "--heightmap-npy",
            str(heightmap_path),
            "--output-dir",
            str(native_dir),
            "--scm-grid-spacing-m",
            str(chrono["scm_grid_spacing_m"]),
            "--scm-pit-size-m",
            *(str(value) for value in chrono["scm_pit_size_m"]),
            "--bekker-kphi",
            str(varied["bekker_kphi"]["reference"]),
            "--mohr-friction-deg",
            str(varied["mohr_friction_deg"]["reference"]),
            "--maximum-roundtrip-error-m",
            str(surface_contract["maximum_scm_roundtrip_error_m"]),
        ]
        fresh.run_logged(
            command,
            root / "chrono_scm_roundtrip.log",
            repo_path(chrono["repo"]),
            chrono["thread_environment"],
        )
    native = json.loads((native_dir / "summary.json").read_text(encoding="utf-8"))
    checks = {
        "generator": bool(generated["qualified"]),
        "native_scm": native["status"] == "passed" and all(native["checks"].values()),
        "identity": native["requested_array_sha256"]
        == generated["metrics"]["array_sha256"],
        "target_free_manifest": manifest.get("target_free") is True,
        "reserved_seed": seed == 3102,
    }
    result = {
        "schema_version": 1,
        "evaluation_id": config["evaluation_id"],
        "seed": seed,
        "partition": "v2_test_reserved",
        "qualified": all(checks.values()),
        "checks": checks,
        "target_free_manifest_sha256": fresh.sha256_file(manifest_path(config)),
        "config_sha256": fresh.sha256_file(config_path),
        "planner_sha256": fresh.sha256_file(Path(__file__).resolve()),
        "generator": generated,
        "chrono_scm_roundtrip": native,
    }
    fresh.write_json(root / "qualification_summary.json", result)
    return result


def assert_targets_absent(
    config: Mapping[str, Any], manifest: Mapping[str, Any]
) -> None:
    output = repo_path(config["execution"]["output_root"])
    chrono = repo_path(config["execution"]["chrono_output_root"])
    present = []
    for episode in manifest["episodes"]["test"]:
        for path in (
            output / "episodes" / episode["episode_id"],
            chrono / episode["episode_id"],
        ):
            if path.exists():
                present.append(str(path))
    for marker in ("evaluation_plan.json", "test_unlock.json", "test_targets_opened.json"):
        if (output / marker).exists():
            present.append(str(output / marker))
    if present:
        raise RuntimeError(f"v2 target or unlock artifacts already exist: {present}")


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = load_config(config_path)
    if args.stage == "manifest":
        manifest = build_manifest(config_path, config)
        assert_targets_absent(config, manifest)
        write_manifest(manifest_path(config), manifest)
        print(
            json.dumps(
                {
                    "status": manifest["status"],
                    "test": manifest["counts"]["test"],
                    "test_lock_sha256": manifest["test_lock_sha256"],
                    "overlap_audit": manifest["overlap_audit"],
                },
                indent=2,
            )
        )
        return
    manifest = load_frozen_manifest(config_path, config)
    assert_targets_absent(config, manifest)
    if args.stage == "surface":
        result = qualify_surface(config_path, config, manifest)
        print(json.dumps(result, indent=2))
        if not result["qualified"]:
            raise SystemExit(2)
        return
    summary = repo_path(config["surface_qualification"]["summary"])
    if not summary.is_file():
        raise RuntimeError("v2 surface qualification is absent")
    qualification = json.loads(summary.read_text(encoding="utf-8"))
    checks = {
        "manifest_identity": manifest["episode_manifest_sha256"]
        == contract_screen.canonical_sha256(manifest["episodes"]),
        "test_lock_identity": manifest["test_lock_sha256"]
        == contract_screen.canonical_sha256(
            [
                {
                    "episode_id": item["episode_id"],
                    "input_sha256": item["input_sha256"],
                }
                for item in manifest["episodes"]["test"]
            ]
        ),
        "overlap_audit": bool(manifest["overlap_audit"]["passed"]),
        "surface_qualified": bool(qualification["qualified"]),
        "targets_absent": True,
    }
    print(json.dumps({"checks": checks, "passed": all(checks.values())}, indent=2))
    if not all(checks.values()):
        raise SystemExit(2)


if __name__ == "__main__":
    main()

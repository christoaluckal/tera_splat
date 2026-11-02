#!/usr/bin/env python3
"""Validate and freeze the target-free Phase 1 one-action successor plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = REPO_ROOT / "configs" / "phase1_one_action_successor_contract_v1.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def repo_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (REPO_ROOT / path).resolve()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def closed_range(spec: dict[str, Any], label: str) -> tuple[float, float]:
    minimum, maximum = float(spec["minimum"]), float(spec["maximum"])
    if not math.isfinite(minimum) or not math.isfinite(maximum) or minimum >= maximum:
        raise ValueError(f"{label} must be a finite increasing range")
    return minimum, maximum


def validate_antecedent(contract: dict[str, Any]) -> None:
    antecedent = contract["antecedent_screen"]
    for key, hash_key in (
        ("recovery_plan", "recovery_plan_sha256"),
        ("directional_analysis_plan", "directional_analysis_plan_sha256"),
        ("directional_analysis_summary", "directional_analysis_summary_sha256"),
    ):
        path = repo_path(antecedent[key])
        if not path.is_file() or sha256_file(path) != antecedent[hash_key]:
            raise RuntimeError(f"antecedent screen identity changed: {key}")
    summary = json.loads(repo_path(antecedent["directional_analysis_summary"]).read_text(encoding="utf-8"))
    if summary.get("status") != antecedent["required_status"] or summary.get("screen_passed") is not True:
        raise RuntimeError("antecedent directional screen is not passed")
    if antecedent.get("screen_artifacts_excluded_from_training_selection_and_protected_accuracy") is not True:
        raise ValueError("screen artifacts must remain excluded from learning and protected accuracy")


def validate_contract(contract_path: Path, contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != 1:
        raise ValueError("successor contract schema_version must be 1")
    if contract.get("contract_id") != "phase1_one_action_successor_contract_v1":
        raise ValueError("unexpected successor contract identity")
    if contract.get("status") != "frozen_before_target_generation":
        raise ValueError("successor contract must be frozen before targets")
    if contract.get("authority") != "docs/newton/phase1.md":
        raise ValueError("successor contract lost Phase 1 authority")
    validate_antecedent(contract)

    action = contract["action_domain"]
    if action["proxy_shape"] != "vertically_guided_cylinder" or not math.isclose(float(action["radius_m"]), 0.035):
        raise ValueError("successor action must retain the 35 mm guided cylinder")
    if not all(bool(action[key]) for key in ("dynamic_loads_excluded", "tangential_motion_excluded", "rotation_excluded")):
        raise ValueError("dynamic, tangential, and rotational actions must remain excluded")
    if action["center_domain"]["shape"] != "closed_disk" or not math.isclose(float(action["center_domain"]["max_radius_m"]), 0.1):
        raise ValueError("successor position domain changed")
    if closed_range(action["normal_force_n"], "normal_force_n") != (30.65625, 45.984375):
        raise ValueError("successor force bounds changed")

    varied = contract["chrono"]["soil_parameters"]["varied"]
    if set(varied) != {"bekker_kphi"}:
        raise ValueError("successor must vary only bekker_kphi")
    if closed_range(varied["bekker_kphi"], "bekker_kphi") != (1500000.0, 2000000.0):
        raise ValueError("screened Kphi bounds changed")
    fixed = contract["chrono"]["soil_parameters"]["fixed"]
    expected_fixed = {
        "bekker_kc": 0.0,
        "bekker_n": 1.1,
        "mohr_cohesion_pa": 0.0,
        "mohr_friction_deg": 30.0,
        "janosi_shear_m": 0.01,
        "elastic_k_pa_per_m": 200000000.0,
        "damping_r_pa_s_per_m": 30000.0,
    }
    if {key: float(value) for key, value in fixed.items()} != expected_fixed:
        raise ValueError("screened fixed soil parameters changed")

    surface = contract["initial_surface_domain"]
    groups = surface["surface_seeds"]
    train = [int(value) for value in groups["train"]]
    validation = [int(value) for value in groups["validation_reserved"]]
    test = [int(value) for value in groups["test_reserved"]]
    if len(train) != 4 or len(validation) != 1 or len(test) != 1:
        raise ValueError("successor requires 4/1/1 surface-seed partitions")
    if len(set(train + validation + test)) != 6:
        raise ValueError("surface-seed partitions must be disjoint")
    if not bool(surface["history_free"]):
        raise ValueError("successor initial surfaces must be history-free")

    dataset = contract["dataset"]
    if dataset["counts"] != {"train": 48, "validation": 16, "test": 24, "protected_sensitivity": 6}:
        raise ValueError("successor split must remain 48/16/24 plus six sensitivity cases")
    if sum(int(value) for value in dataset["test_group_counts"].values()) != 24:
        raise ValueError("test holdout groups must sum to 24")
    if len(dataset["halton_bases"]) != 4 or len(set(dataset["halton_bases"])) != 4:
        raise ValueError("successor four-dimensional design needs four distinct bases")
    if not all(bool(dataset[key]) for key in ("whole_episode_split_required", "target_free_plan_required", "freeze_plan_before_target_generation", "test_and_sensitivity_targets_locked_until_after_model_selection")):
        raise ValueError("successor leakage guards must all be enabled")
    sensitivity = dataset["protected_sensitivity_design"]
    if len(sensitivity["normal_force_points_n"]) * len(sensitivity["bekker_kphi_points"]) != 6:
        raise ValueError("protected sensitivity suite must contain six matched cases")
    if not bool(sensitivity["excluded_from_fitting_normalization_calibration_and_model_selection"]):
        raise ValueError("sensitivity targets must be excluded from all model development")

    models = contract["model_contract"]
    if models["selection_pool"] != ["D0", "R0", "R1"]:
        raise ValueError("successor selection pool changed")
    if models["optional_ablation_pool"] != ["R2S", "R2E"]:
        raise ValueError("successor optional ablations changed")
    if not (100000 <= int(models["parameter_count_minimum"]) <= int(models["parameter_count_maximum"]) <= 1000000):
        raise ValueError("successor model capacity is outside the declared range")
    excluded = set(contract["tensor_schema"]["excluded_inputs"])
    if "plastic_jacobian" not in excluded:
        raise ValueError("plastic state must remain excluded")
    permissions = contract["permissions_after_dataset_plan_freeze"]
    if permissions != {
        "surface_qualification": True,
        "smoke_train_validation_target_generation": True,
        "remaining_train_validation_target_generation": False,
        "test_or_protected_sensitivity_target_generation": False,
        "training": False,
    }:
        raise ValueError("post-plan permissions changed")
    if contract_path.resolve() != DEFAULT_CONTRACT.resolve() and contract["authority"] != "docs/newton/phase1.md":
        raise ValueError("alternate contract lost its authority")


def load_contract(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    contract = json.loads(resolved.read_text(encoding="utf-8"))
    validate_contract(resolved, contract)
    return contract


def halton(index: int, base: int) -> float:
    if index <= 0 or base <= 1:
        raise ValueError("Halton index and base must be positive")
    fraction, result, value = 1.0, 0.0, int(index)
    while value:
        fraction /= base
        result += fraction * (value % base)
        value //= base
    return result


def scale(value: float, bounds: tuple[float, float]) -> float:
    return bounds[0] + float(value) * (bounds[1] - bounds[0])


def continuous_sample(contract: dict[str, Any], index: int) -> dict[str, Any]:
    dataset = contract["dataset"]
    offset = int(dataset["design_seed"]) % 10000
    unit = [halton(offset + index, int(base)) for base in dataset["halton_bases"]]
    center = contract["action_domain"]["center_domain"]
    origin = [float(value) for value in center["origin_xy_m"]]
    radius = float(center["max_radius_m"]) * math.sqrt(unit[0])
    angle = 2.0 * math.pi * unit[1]
    return {
        "center_xy_m": [origin[0] + radius * math.cos(angle), origin[1] + radius * math.sin(angle)],
        "normal_force_n": scale(unit[2], closed_range(contract["action_domain"]["normal_force_n"], "force")),
        "bekker_kphi": scale(unit[3], closed_range(contract["chrono"]["soil_parameters"]["varied"]["bekker_kphi"], "Kphi")),
    }


def make_episode(contract: dict[str, Any], split: str, ordinal: int, values: dict[str, Any], surface_seed: int, holdout_group: str) -> dict[str, Any]:
    action = contract["action_domain"]
    force = float(values["normal_force_n"])
    fixed = {key: float(value) for key, value in contract["chrono"]["soil_parameters"]["fixed"].items()}
    payload = {
        "initial_surface_id": f"surface_{int(surface_seed)}",
        "initial_surface_seed": int(surface_seed),
        "center_xy_m": [float(value) for value in values["center_xy_m"]],
        "normal_force_n": force,
        "equivalent_mass_kg": force / float(action["gravity_mps2"]),
        "radius_m": float(action["radius_m"]),
        "height_m": float(action["height_m"]),
        "soil_parameters": {**fixed, "bekker_kphi": float(values["bekker_kphi"])},
        "checkpoints": ["loaded", "post_unload"],
    }
    episode_id = f"p1s_{split}_{holdout_group.replace('_', '-')}_{ordinal:03d}"
    return {
        "episode_id": episode_id,
        "split": split,
        "holdout_group": holdout_group,
        **payload,
        "input_sha256": canonical_sha256(payload),
        "target_access": "locked" if split in ("test", "protected_sensitivity") else "unavailable_at_plan_time",
    }


def copy_values(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "center_xy_m": list(episode["center_xy_m"]),
        "normal_force_n": float(episode["normal_force_n"]),
        "bekker_kphi": float(episode["soil_parameters"]["bekker_kphi"]),
    }


def build_train(contract: dict[str, Any]) -> list[dict[str, Any]]:
    seeds = [int(value) for value in contract["initial_surface_domain"]["surface_seeds"]["train"]]
    return [make_episode(contract, "train", index, continuous_sample(contract, 1 + index), seeds[index % len(seeds)], "joint_design") for index in range(48)]


def build_validation(contract: dict[str, Any]) -> list[dict[str, Any]]:
    groups = contract["initial_surface_domain"]["surface_seeds"]
    train_seeds = [int(value) for value in groups["train"]]
    reserved = int(groups["validation_reserved"][0])
    result = []
    for index in range(16):
        unseen_surface = index >= 8
        result.append(make_episode(contract, "validation", index, continuous_sample(contract, 1001 + index), reserved if unseen_surface else train_seeds[index % len(train_seeds)], "unseen_initial_surface" if unseen_surface else "joint_design"))
    return result


def build_test(contract: dict[str, Any], train: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = contract["dataset"]["test_group_counts"]
    train_seeds = [int(value) for value in contract["initial_surface_domain"]["surface_seeds"]["train"]]
    test_seed = int(contract["initial_surface_domain"]["surface_seeds"]["test_reserved"][0])
    force_bounds = closed_range(contract["action_domain"]["normal_force_n"], "force")
    kphi_bounds = closed_range(contract["chrono"]["soil_parameters"]["varied"]["bekker_kphi"], "Kphi")
    result: list[dict[str, Any]] = []

    for index in range(int(groups["unseen_position"])):
        values = continuous_sample(contract, 2001 + index)
        reference = copy_values(train[index])
        values.update(normal_force_n=reference["normal_force_n"], bekker_kphi=reference["bekker_kphi"])
        result.append(make_episode(contract, "test", len(result), values, train_seeds[index % len(train_seeds)], "unseen_position"))
    for index in range(int(groups["unseen_force"])):
        values = copy_values(train[5 + index])
        values["normal_force_n"] = scale((index + 1) / 6.0, force_bounds)
        result.append(make_episode(contract, "test", len(result), values, train_seeds[index % len(train_seeds)], "unseen_force"))
    for index in range(int(groups["unseen_kphi"])):
        values = copy_values(train[10 + index])
        values["bekker_kphi"] = scale((index + 1) / 6.0, kphi_bounds)
        result.append(make_episode(contract, "test", len(result), values, train_seeds[index % len(train_seeds)], "unseen_kphi"))
    for index in range(int(groups["unseen_initial_surface"])):
        result.append(make_episode(contract, "test", len(result), copy_values(train[15 + index]), test_seed, "unseen_initial_surface"))
    for index in range(int(groups["joint_combination"])):
        result.append(make_episode(contract, "test", len(result), continuous_sample(contract, 3001 + index), test_seed, "joint_combination"))
    return result


def build_sensitivity(contract: dict[str, Any]) -> list[dict[str, Any]]:
    spec = contract["dataset"]["protected_sensitivity_design"]
    result = []
    for force in spec["normal_force_points_n"]:
        for kphi in spec["bekker_kphi_points"]:
            values = {"center_xy_m": spec["center_xy_m"], "normal_force_n": force, "bekker_kphi": kphi}
            result.append(make_episode(contract, "protected_sensitivity", len(result), values, int(spec["initial_surface_seed"]), "matched_kphi_sweep"))
    return result


def validate_plan(contract: dict[str, Any], plan: dict[str, Any]) -> None:
    expected = contract["dataset"]["counts"]
    for split in ("train", "validation", "test", "protected_sensitivity"):
        if len(plan["episodes"][split]) != int(expected[split]):
            raise ValueError(f"{split} count differs from contract")
    episodes = [episode for split in ("train", "validation", "test", "protected_sensitivity") for episode in plan["episodes"][split]]
    if len({item["episode_id"] for item in episodes}) != len(episodes) or len({item["input_sha256"] for item in episodes}) != len(episodes):
        raise ValueError("successor episode ids and inputs must be unique")
    origin = contract["action_domain"]["center_domain"]["origin_xy_m"]
    max_radius = float(contract["action_domain"]["center_domain"]["max_radius_m"])
    force_bounds = closed_range(contract["action_domain"]["normal_force_n"], "force")
    kphi_bounds = closed_range(contract["chrono"]["soil_parameters"]["varied"]["bekker_kphi"], "Kphi")
    for episode in episodes:
        x, y = episode["center_xy_m"]
        if math.hypot(float(x) - float(origin[0]), float(y) - float(origin[1])) > max_radius + 1.0e-12:
            raise ValueError(f"out-of-domain position: {episode['episode_id']}")
        if not force_bounds[0] <= float(episode["normal_force_n"]) <= force_bounds[1]:
            raise ValueError(f"out-of-domain force: {episode['episode_id']}")
        if not kphi_bounds[0] <= float(episode["soil_parameters"]["bekker_kphi"]) <= kphi_bounds[1]:
            raise ValueError(f"out-of-domain Kphi: {episode['episode_id']}")
        if episode["split"] in ("test", "protected_sensitivity") and episode["target_access"] != "locked":
            raise ValueError("protected target is not locked")
    actual_groups: dict[str, int] = {}
    for episode in plan["episodes"]["test"]:
        group = episode["holdout_group"]
        actual_groups[group] = actual_groups.get(group, 0) + 1
    if actual_groups != {key: int(value) for key, value in contract["dataset"]["test_group_counts"].items()}:
        raise ValueError("test holdout counts changed")
    sensitivity = plan["episodes"]["protected_sensitivity"]
    shared = {(item["initial_surface_seed"], tuple(item["center_xy_m"]), item["radius_m"]) for item in sensitivity}
    if len(shared) != 1 or len({item["normal_force_n"] for item in sensitivity}) != 2 or len({item["soil_parameters"]["bekker_kphi"] for item in sensitivity}) != 3:
        raise ValueError("protected sensitivity suite is not a matched 2x3 sweep")
    serialized = json.dumps(plan["episodes"], sort_keys=True)
    for forbidden in ("loaded_heightmap", "post_unload_heightmap", "chrono_target", "target_path"):
        if forbidden in serialized:
            raise ValueError(f"target-free plan contains forbidden key: {forbidden}")
    for split, key in (("test", "test_lock_sha256"), ("protected_sensitivity", "sensitivity_lock_sha256")):
        expected_lock = canonical_sha256([{"episode_id": item["episode_id"], "input_sha256": item["input_sha256"]} for item in plan["episodes"][split]])
        if plan[key] != expected_lock:
            raise ValueError(f"{split} identity lock changed")


def git_output(arguments: list[str]) -> str:
    result = subprocess.run(["git", *arguments], cwd=REPO_ROOT, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return result.stdout.strip()


def build_plan(contract_path: Path, contract: dict[str, Any]) -> dict[str, Any]:
    train = build_train(contract)
    validation = build_validation(contract)
    test = build_test(contract, train)
    sensitivity = build_sensitivity(contract)
    episodes = {"train": train, "validation": validation, "test": test, "protected_sensitivity": sensitivity}
    smoke = contract["dataset"]["smoke_membership"]
    plan = {
        "schema_version": 1,
        "identity": "phase1_one_action_successor_dataset_plan_v1",
        "status": "target_free_plan_frozen",
        "authority": contract["authority"],
        "contract": str(contract_path.resolve().relative_to(REPO_ROOT)),
        "contract_sha256": sha256_file(contract_path.resolve()),
        "planner": str(Path(__file__).resolve().relative_to(REPO_ROOT)),
        "planner_sha256": sha256_file(Path(__file__).resolve()),
        "repository": {"revision": git_output(["rev-parse", "HEAD"]), "branch": git_output(["branch", "--show-current"]), "status_short": git_output(["status", "--short"]).splitlines()},
        "target_free": True,
        "antecedent_screen": {
            "status": contract["antecedent_screen"]["required_status"],
            "directional_analysis_summary_sha256": contract["antecedent_screen"]["directional_analysis_summary_sha256"],
        },
        "episodes": episodes,
        "counts": {key: len(value) for key, value in episodes.items()},
        "smoke_membership": {
            "train": [train[int(index)]["episode_id"] for index in smoke["train_ordinals"]],
            "validation": [validation[int(index)]["episode_id"] for index in smoke["validation_ordinals"]],
        },
        "episode_manifest_sha256": canonical_sha256(episodes),
        "test_lock_sha256": canonical_sha256([{"episode_id": item["episode_id"], "input_sha256": item["input_sha256"]} for item in test]),
        "sensitivity_lock_sha256": canonical_sha256([{"episode_id": item["episode_id"], "input_sha256": item["input_sha256"]} for item in sensitivity]),
        "permissions": contract["permissions_after_dataset_plan_freeze"],
    }
    validate_plan(contract, plan)
    return plan


def default_output(contract: dict[str, Any]) -> Path:
    return REPO_ROOT / "outputs" / "validity_experiment" / "newton" / contract["contract_id"] / "dataset_plan.json"


def write_plan(path: Path, plan: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(plan, indent=2, sort_keys=False) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != encoded:
            raise RuntimeError(f"refusing to replace a different frozen plan: {path}")
        return
    path.write_text(encoded, encoding="utf-8")


def main() -> None:
    args = parse_args()
    contract_path = args.contract.resolve()
    contract = load_contract(contract_path)
    plan = build_plan(contract_path, contract)
    output = args.output.resolve() if args.output else default_output(contract)
    if not args.check_only:
        write_plan(output, plan)
    print(json.dumps({
        "contract": str(contract_path),
        "contract_sha256": plan["contract_sha256"],
        "planner_sha256": plan["planner_sha256"],
        "output": None if args.check_only else str(output),
        "counts": plan["counts"],
        "episode_manifest_sha256": plan["episode_manifest_sha256"],
        "test_lock_sha256": plan["test_lock_sha256"],
        "sensitivity_lock_sha256": plan["sensitivity_lock_sha256"],
        "permissions": plan["permissions"],
    }, indent=2))


if __name__ == "__main__":
    main()

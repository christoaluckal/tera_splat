#!/usr/bin/env python3
"""Validate the Phase 1 contract and freeze its target-free episode plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = REPO_ROOT / "configs" / "phase1_bed_state_v1.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate and summarize without writing dataset_plan.json.",
    )
    return parser.parse_args()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return sha256_bytes(encoded)


def repo_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (REPO_ROOT / path).resolve()


def _finite_number(value: Any, label: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _closed_range(spec: dict[str, Any], label: str) -> tuple[float, float]:
    minimum = _finite_number(spec["minimum"], f"{label}.minimum")
    maximum = _finite_number(spec["maximum"], f"{label}.maximum")
    if not minimum < maximum:
        raise ValueError(f"{label} must have minimum < maximum")
    return minimum, maximum


def validate_contract(contract_path: Path, contract: dict[str, Any]) -> None:
    if int(contract.get("schema_version", -1)) != 1:
        raise ValueError("Phase 1 contract schema_version must be 1")
    if contract.get("phase_id") != "phase1_bed_state_v1":
        raise ValueError("unexpected Phase 1 contract identity")
    if contract.get("status") != "frozen_pre_screening":
        raise ValueError("Phase 1 contract must be frozen before screening")

    inheritance = contract["inheritance"]
    if not all(
        bool(inheritance[key])
        for key in (
            "phase0_cases_are_immutable",
            "phase0_models_are_immutable",
            "phase0_61n_targets_are_protected",
        )
    ):
        raise ValueError("Phase 0 cases, models, and 61 N targets must remain protected")
    for key in ("phase0_contract", "phase0_completion_report"):
        if not repo_path(inheritance[key]).is_file():
            raise FileNotFoundError(f"missing inherited source: {inheritance[key]}")

    action = contract["action_domain"]
    if action["proxy_shape"] != "vertically_guided_cylinder":
        raise ValueError("Phase 1 requires the frozen vertical cylinder")
    if not math.isclose(float(action["radius_m"]), 0.035):
        raise ValueError("Phase 1 radius must remain 35 mm")
    if action["center_domain"]["shape"] != "closed_disk":
        raise ValueError("Phase 1 action center must use a closed disk")
    if not math.isclose(float(action["center_domain"]["max_radius_m"]), 0.1):
        raise ValueError("Phase 1 position radius must remain 0.10 m")
    force_min, force_max = _closed_range(action["normal_force_n"], "normal_force_n")
    if not math.isclose(force_min, 30.65625) or not math.isclose(force_max, 45.984375):
        raise ValueError("Phase 1 force bounds differ from the authority")
    if not all(
        bool(action[key])
        for key in (
            "dynamic_loads_excluded",
            "tangential_motion_excluded",
            "rotation_excluded",
        )
    ):
        raise ValueError("dynamic, tangential, and rotational actions must be excluded")

    surface = contract["initial_surface_domain"]
    if not bool(surface["history_free"]):
        raise ValueError("Phase 1 initial surfaces must be history-free")
    if float(surface["relief_limit_m"]) > 0.005:
        raise ValueError("initial relief exceeds the Phase 1 bound")
    if float(surface["maximum_local_slope_deg"]) > 10.0:
        raise ValueError("initial slope exceeds the Phase 1 bound")
    if float(surface["minimum_correlation_length_m"]) < 0.05:
        raise ValueError("initial correlation length is below the Phase 1 bound")
    seed_groups = surface["surface_seeds"]
    train_seeds = [int(value) for value in seed_groups["train"]]
    validation_seeds = [int(value) for value in seed_groups["validation_reserved"]]
    test_seeds = [int(value) for value in seed_groups["test_reserved"]]
    if len(train_seeds) < 4 or len(validation_seeds) + len(test_seeds) < 2:
        raise ValueError("Phase 1 requires four training and two reserved surface seeds")
    flattened = train_seeds + validation_seeds + test_seeds
    if len(flattened) != len(set(flattened)):
        raise ValueError("surface seed partitions must be disjoint")

    varied = contract["chrono"]["soil_parameters"]["varied"]
    if set(varied) != {"bekker_kphi", "mohr_friction_deg"}:
        raise ValueError("Phase 1 must vary exactly the two declared SCM parameters")
    kphi_min, kphi_max = _closed_range(varied["bekker_kphi"], "bekker_kphi")
    friction_min, friction_max = _closed_range(
        varied["mohr_friction_deg"], "mohr_friction_deg"
    )
    expected_points = {
        (kphi_min, friction_min),
        (kphi_min, friction_max),
        (kphi_max, friction_min),
        (kphi_max, friction_max),
        (
            float(varied["bekker_kphi"]["reference"]),
            float(varied["mohr_friction_deg"]["reference"]),
        ),
    }
    actual_points = {
        (float(point["bekker_kphi"]), float(point["mohr_friction_deg"]))
        for point in contract["screening"]["material_box_points"]
    }
    if actual_points != expected_points:
        raise ValueError("screening must contain all four material corners and center")
    if not bool(contract["screening"]["bulk_dataset_blocked_until_pass"]):
        raise ValueError("bulk data generation must remain blocked until screening passes")

    dataset = contract["dataset"]
    if dataset["counts"] != {"train": 48, "validation": 16, "test": 24}:
        raise ValueError("Phase 1 split must remain 48/16/24")
    if sum(int(value) for value in dataset["test_group_counts"].values()) != 24:
        raise ValueError("test group counts must sum to 24")
    if not all(
        bool(dataset[key])
        for key in (
            "whole_episode_split_required",
            "target_free_plan_required",
            "freeze_plan_before_target_generation",
            "test_targets_locked_until_final_evaluation",
        )
    ):
        raise ValueError("Phase 1 split and target locks must all be enabled")
    bases = [int(value) for value in dataset["halton_bases"]]
    if len(bases) != 5 or len(set(bases)) != 5 or min(bases) < 2:
        raise ValueError("the five-dimensional design needs five distinct bases")
    if not (100000 <= int(contract["model_contract"]["parameter_count_minimum"])):
        raise ValueError("model capacity floor is below the Phase 1 contract")
    if int(contract["model_contract"]["parameter_count_maximum"]) > 1000000:
        raise ValueError("model capacity cap exceeds the Phase 1 contract")
    if contract_path.resolve() != DEFAULT_CONTRACT.resolve():
        # Alternate paths are supported in tests, but the contract still owns its identity.
        if contract.get("authority") != "docs/newton/phase1.md":
            raise ValueError("alternate contract lost the Phase 1 authority")


def load_contract(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    contract = json.loads(resolved.read_text(encoding="utf-8"))
    validate_contract(resolved, contract)
    return contract


def halton(index: int, base: int) -> float:
    if index <= 0 or base <= 1:
        raise ValueError("Halton index and base must be positive")
    fraction = 1.0
    result = 0.0
    value = int(index)
    while value:
        fraction /= base
        result += fraction * (value % base)
        value //= base
    return result


def scale(unit_value: float, bounds: tuple[float, float]) -> float:
    return bounds[0] + float(unit_value) * (bounds[1] - bounds[0])


def continuous_sample(contract: dict[str, Any], index: int) -> dict[str, Any]:
    bases = [int(value) for value in contract["dataset"]["halton_bases"]]
    offset = int(contract["dataset"]["design_seed"]) % 10000
    values = [halton(offset + index, base) for base in bases]
    action = contract["action_domain"]
    origin = [float(value) for value in action["center_domain"]["origin_xy_m"]]
    radius = float(action["center_domain"]["max_radius_m"]) * math.sqrt(values[0])
    angle = 2.0 * math.pi * values[1]
    varied = contract["chrono"]["soil_parameters"]["varied"]
    return {
        "center_xy_m": [
            origin[0] + radius * math.cos(angle),
            origin[1] + radius * math.sin(angle),
        ],
        "normal_force_n": scale(
            values[2], _closed_range(action["normal_force_n"], "normal_force_n")
        ),
        "bekker_kphi": scale(
            values[3], _closed_range(varied["bekker_kphi"], "bekker_kphi")
        ),
        "mohr_friction_deg": scale(
            values[4],
            _closed_range(varied["mohr_friction_deg"], "mohr_friction_deg"),
        ),
    }


def make_episode(
    contract: dict[str, Any],
    split: str,
    ordinal: int,
    values: dict[str, Any],
    surface_seed: int,
    holdout_group: str,
) -> dict[str, Any]:
    action = contract["action_domain"]
    radius_m = float(action["radius_m"])
    normal_force_n = float(values["normal_force_n"])
    payload = {
        "split": split,
        "holdout_group": holdout_group,
        "initial_surface_id": f"surface_{int(surface_seed)}",
        "initial_surface_seed": int(surface_seed),
        "center_xy_m": [float(value) for value in values["center_xy_m"]],
        "normal_force_n": normal_force_n,
        "equivalent_mass_kg": normal_force_n / float(action["gravity_mps2"]),
        "radius_m": radius_m,
        "nominal_pressure_pa": normal_force_n / (math.pi * radius_m * radius_m),
        "soil_parameters": {
            "bekker_kphi": float(values["bekker_kphi"]),
            "mohr_friction_deg": float(values["mohr_friction_deg"]),
        },
        "checkpoints": ["loaded", "post_unload"],
    }
    group_label = holdout_group.replace("_", "-")
    episode_id = f"p1_{split}_{group_label}_{ordinal:03d}"
    return {
        "episode_id": episode_id,
        **payload,
        "input_sha256": canonical_sha256(payload),
        "target_access": "locked" if split == "test" else "unavailable_at_plan_time",
    }


def build_train(contract: dict[str, Any]) -> list[dict[str, Any]]:
    count = int(contract["dataset"]["counts"]["train"])
    seeds = [int(value) for value in contract["initial_surface_domain"]["surface_seeds"]["train"]]
    return [
        make_episode(
            contract,
            "train",
            index,
            continuous_sample(contract, 1 + index),
            seeds[index % len(seeds)],
            "joint_design",
        )
        for index in range(count)
    ]


def build_validation(contract: dict[str, Any]) -> list[dict[str, Any]]:
    count = int(contract["dataset"]["counts"]["validation"])
    seed_groups = contract["initial_surface_domain"]["surface_seeds"]
    train_seeds = [int(value) for value in seed_groups["train"]]
    reserved = [int(value) for value in seed_groups["validation_reserved"]]
    result = []
    for index in range(count):
        surface_seed = (
            train_seeds[index % len(train_seeds)]
            if index < count // 2
            else reserved[index % len(reserved)]
        )
        group = "joint_design" if index < count // 2 else "unseen_initial_surface"
        result.append(
            make_episode(
                contract,
                "validation",
                index,
                continuous_sample(contract, 1001 + index),
                surface_seed,
                group,
            )
        )
    return result


def _copy_values(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "center_xy_m": list(episode["center_xy_m"]),
        "normal_force_n": float(episode["normal_force_n"]),
        "bekker_kphi": float(episode["soil_parameters"]["bekker_kphi"]),
        "mohr_friction_deg": float(
            episode["soil_parameters"]["mohr_friction_deg"]
        ),
    }


def build_test(
    contract: dict[str, Any], train: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    groups = contract["dataset"]["test_group_counts"]
    surface_groups = contract["initial_surface_domain"]["surface_seeds"]
    train_seeds = [int(value) for value in surface_groups["train"]]
    test_seed = int(surface_groups["test_reserved"][0])
    force_bounds = _closed_range(contract["action_domain"]["normal_force_n"], "force")
    varied = contract["chrono"]["soil_parameters"]["varied"]
    kphi_bounds = _closed_range(varied["bekker_kphi"], "bekker_kphi")
    friction_bounds = _closed_range(
        varied["mohr_friction_deg"], "mohr_friction_deg"
    )
    result: list[dict[str, Any]] = []
    ordinal = 0

    for index in range(int(groups["unseen_position"])):
        values = continuous_sample(contract, 2001 + index)
        reference = _copy_values(train[index])
        values.update(
            normal_force_n=reference["normal_force_n"],
            bekker_kphi=reference["bekker_kphi"],
            mohr_friction_deg=reference["mohr_friction_deg"],
        )
        result.append(
            make_episode(
                contract,
                "test",
                ordinal,
                values,
                train_seeds[index % len(train_seeds)],
                "unseen_position",
            )
        )
        ordinal += 1

    force_count = int(groups["unseen_force"])
    for index in range(force_count):
        values = _copy_values(train[5 + index])
        values["normal_force_n"] = scale(
            (index + 1) / (force_count + 1), force_bounds
        )
        result.append(
            make_episode(
                contract,
                "test",
                ordinal,
                values,
                train_seeds[index % len(train_seeds)],
                "unseen_force",
            )
        )
        ordinal += 1

    material_count = int(groups["unseen_material_combination"])
    for index in range(material_count):
        values = _copy_values(train[10 + index])
        fraction = (index + 1) / (material_count + 1)
        values["bekker_kphi"] = scale(fraction, kphi_bounds)
        values["mohr_friction_deg"] = scale(1.0 - fraction, friction_bounds)
        result.append(
            make_episode(
                contract,
                "test",
                ordinal,
                values,
                train_seeds[index % len(train_seeds)],
                "unseen_material_combination",
            )
        )
        ordinal += 1

    for index in range(int(groups["unseen_initial_surface"])):
        values = _copy_values(train[15 + index])
        result.append(
            make_episode(
                contract,
                "test",
                ordinal,
                values,
                test_seed,
                "unseen_initial_surface",
            )
        )
        ordinal += 1

    for index in range(int(groups["joint_combination"])):
        result.append(
            make_episode(
                contract,
                "test",
                ordinal,
                continuous_sample(contract, 3001 + index),
                test_seed,
                "joint_combination",
            )
        )
        ordinal += 1
    return result


def screening_cases(contract: dict[str, Any]) -> list[dict[str, Any]]:
    action = contract["screening"]["material_action"]
    result = []
    for point in contract["screening"]["material_box_points"]:
        payload = {
            "center_xy_m": [float(value) for value in action["center_xy_m"]],
            "normal_force_n": float(action["normal_force_n"]),
            "initial_surface_seed": int(action["initial_surface_seed"]),
            "bekker_kphi": float(point["bekker_kphi"]),
            "mohr_friction_deg": float(point["mohr_friction_deg"]),
        }
        result.append(
            {
                "case_id": f"screen_material_{point['label']}",
                **payload,
                "input_sha256": canonical_sha256(payload),
                "required_before_bulk_dataset": True,
            }
        )
    return result


def surface_qualification_cases(contract: dict[str, Any]) -> list[dict[str, Any]]:
    seed_groups = contract["initial_surface_domain"]["surface_seeds"]
    result = []
    for partition, values in seed_groups.items():
        for seed in values:
            payload = {
                "partition": partition,
                "initial_surface_seed": int(seed),
                "generator": contract["initial_surface_domain"]["generator"],
                "bounds": {
                    "relief_limit_m": contract["initial_surface_domain"]["relief_limit_m"],
                    "maximum_local_slope_deg": contract["initial_surface_domain"]["maximum_local_slope_deg"],
                    "minimum_correlation_length_m": contract["initial_surface_domain"]["minimum_correlation_length_m"],
                },
            }
            result.append(
                {
                    "case_id": f"screen_surface_{int(seed)}",
                    **payload,
                    "input_sha256": canonical_sha256(payload),
                    "required_before_bulk_dataset": True,
                }
            )
    return result


def validate_plan(contract: dict[str, Any], plan: dict[str, Any]) -> None:
    counts = contract["dataset"]["counts"]
    for split in ("train", "validation", "test"):
        if len(plan["episodes"][split]) != int(counts[split]):
            raise ValueError(f"{split} plan count does not match the contract")
    episodes = [
        episode
        for split in ("train", "validation", "test")
        for episode in plan["episodes"][split]
    ]
    ids = [str(episode["episode_id"]) for episode in episodes]
    signatures = [str(episode["input_sha256"]) for episode in episodes]
    if len(ids) != len(set(ids)):
        raise ValueError("episode ids are not unique")
    if len(signatures) != len(set(signatures)):
        raise ValueError("episode inputs are not unique")

    action = contract["action_domain"]
    origin = [float(value) for value in action["center_domain"]["origin_xy_m"]]
    max_radius = float(action["center_domain"]["max_radius_m"])
    force_bounds = _closed_range(action["normal_force_n"], "normal_force_n")
    varied = contract["chrono"]["soil_parameters"]["varied"]
    kphi_bounds = _closed_range(varied["bekker_kphi"], "bekker_kphi")
    friction_bounds = _closed_range(
        varied["mohr_friction_deg"], "mohr_friction_deg"
    )
    for episode in episodes:
        x, y = [float(value) for value in episode["center_xy_m"]]
        if math.hypot(x - origin[0], y - origin[1]) > max_radius + 1.0e-12:
            raise ValueError(f"episode outside position domain: {episode['episode_id']}")
        values = (
            (float(episode["normal_force_n"]), force_bounds, "force"),
            (
                float(episode["soil_parameters"]["bekker_kphi"]),
                kphi_bounds,
                "bekker_kphi",
            ),
            (
                float(episode["soil_parameters"]["mohr_friction_deg"]),
                friction_bounds,
                "friction",
            ),
        )
        for value, bounds, label in values:
            if value < bounds[0] - 1.0e-12 or value > bounds[1] + 1.0e-12:
                raise ValueError(
                    f"{episode['episode_id']} has out-of-domain {label}"
                )
    actual_groups: dict[str, int] = {}
    for episode in plan["episodes"]["test"]:
        group = str(episode["holdout_group"])
        actual_groups[group] = actual_groups.get(group, 0) + 1
        if episode["target_access"] != "locked":
            raise ValueError("every test target must be locked")
    expected_groups = {
        str(key): int(value)
        for key, value in contract["dataset"]["test_group_counts"].items()
    }
    if actual_groups != expected_groups:
        raise ValueError("test holdout groups do not match the contract")

    train_seeds = set(
        int(value)
        for value in contract["initial_surface_domain"]["surface_seeds"]["train"]
    )
    validation_reserved = set(
        int(value)
        for value in contract["initial_surface_domain"]["surface_seeds"][
            "validation_reserved"
        ]
    )
    test_reserved = set(
        int(value)
        for value in contract["initial_surface_domain"]["surface_seeds"][
            "test_reserved"
        ]
    )
    if {int(value["initial_surface_seed"]) for value in plan["episodes"]["train"]} != train_seeds:
        raise ValueError("training episodes do not cover every training surface seed")
    if not validation_reserved.issubset(
        {int(value["initial_surface_seed"]) for value in plan["episodes"]["validation"]}
    ):
        raise ValueError("validation reserved surface is absent")
    if not test_reserved.issubset(
        {int(value["initial_surface_seed"]) for value in plan["episodes"]["test"]}
    ):
        raise ValueError("test reserved surface is absent")

    expected_lock = canonical_sha256(
        [
            {
                "episode_id": episode["episode_id"],
                "input_sha256": episode["input_sha256"],
            }
            for episode in plan["episodes"]["test"]
        ]
    )
    if plan["test_lock_sha256"] != expected_lock:
        raise ValueError("test identity lock does not match the test episodes")


def git_output(arguments: list[str]) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return result.stdout.strip()


def build_plan(contract_path: Path, contract: dict[str, Any]) -> dict[str, Any]:
    train = build_train(contract)
    validation = build_validation(contract)
    test = build_test(contract, train)
    test_identity = [
        {"episode_id": episode["episode_id"], "input_sha256": episode["input_sha256"]}
        for episode in test
    ]
    plan = {
        "schema_version": 1,
        "phase_id": contract["phase_id"],
        "status": "target_free_plan_frozen",
        "authority": contract["authority"],
        "contract": str(contract_path.resolve().relative_to(REPO_ROOT)),
        "contract_sha256": sha256_file(contract_path.resolve()),
        "planner": str(Path(__file__).resolve().relative_to(REPO_ROOT)),
        "planner_sha256": sha256_file(Path(__file__).resolve()),
        "repository": {
            "revision": git_output(["rev-parse", "HEAD"]),
            "branch": git_output(["branch", "--show-current"]),
            "status_short": git_output(["status", "--short"]).splitlines(),
        },
        "target_free": True,
        "screening": {
            "status": "not_started",
            "material_cases": screening_cases(contract),
            "surface_cases": surface_qualification_cases(contract),
            "bulk_dataset_permitted": False,
        },
        "episodes": {
            "train": train,
            "validation": validation,
            "test": test,
        },
        "counts": {key: len(value) for key, value in {
            "train": train,
            "validation": validation,
            "test": test,
        }.items()},
        "test_lock_sha256": canonical_sha256(test_identity),
        "episode_manifest_sha256": canonical_sha256(
            {"train": train, "validation": validation, "test": test}
        ),
        "generation_gate": (
            "screening.material_cases and screening.surface_cases must all pass "
            "before any bulk episode target is generated"
        ),
    }
    validate_plan(contract, plan)
    return plan


def write_plan(path: Path, plan: dict[str, Any]) -> None:
    path = path.resolve()
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        stable_keys = (
            "contract_sha256",
            "planner_sha256",
            "episode_manifest_sha256",
            "test_lock_sha256",
        )
        if any(existing.get(key) != plan.get(key) for key in stable_keys):
            raise RuntimeError(f"refusing to replace a different frozen plan: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def summary(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "phase_id": plan["phase_id"],
        "status": plan["status"],
        "counts": plan["counts"],
        "material_screening_cases": len(plan["screening"]["material_cases"]),
        "surface_screening_cases": len(plan["screening"]["surface_cases"]),
        "episode_manifest_sha256": plan["episode_manifest_sha256"],
        "test_lock_sha256": plan["test_lock_sha256"],
        "bulk_dataset_permitted": plan["screening"]["bulk_dataset_permitted"],
    }


def main() -> None:
    args = parse_args()
    contract_path = args.contract.resolve()
    contract = load_contract(contract_path)
    plan = build_plan(contract_path, contract)
    if not args.check_only:
        output = (
            args.output.resolve()
            if args.output is not None
            else repo_path(contract["dataset"]["plan_path"])
        )
        write_plan(output, plan)
    print(json.dumps(summary(plan), indent=2))


if __name__ == "__main__":
    main()

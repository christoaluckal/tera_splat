#!/usr/bin/env python3
"""Continue the successor dataset from a passing smoke set without opening protected targets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_fresh_phase0_repeatability as fresh
import run_phase1_one_action_successor_smoke as smoke


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_bulk_v1.json"
EXPECTED_DATASET_PLAN_SHA256 = "b326a96bbbcd82e863984eef016e0d320c479f5ec1b7ff937ec4da031d1070ef"
EXPECTED_TEST_LOCK_SHA256 = "0390d46bfd5860b08518f3b99ab116084f24138939c04435f29582c3feedf713"
EXPECTED_SENSITIVITY_LOCK_SHA256 = "a003ec52f2fb43c94d5d760e06a924c3b49809a0ddf415a6abbb718ff18a4139"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--stage",
        choices=("plan", "chrono", "bed", "newton", "analyze", "all"),
        default="plan",
    )
    parser.add_argument("--episode", action="append", default=[])
    parser.add_argument("--workers", type=int)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def sha256(path: Path) -> str:
    return fresh.sha256_file(path)


def load_config(path: Path) -> dict[str, Any]:
    config = load_json(path.resolve())
    if config.get("schema_version") != 1:
        raise ValueError("successor bulk config schema_version must be 1")
    if config.get("dataset_id") != "phase1_one_action_successor_bulk_v1":
        raise ValueError("unexpected successor bulk identity")
    if config.get("status") != "prepared_smoke_gate_locked":
        raise ValueError("successor bulk must remain smoke-gate locked before planning")
    membership = config["membership"]
    expected = {
        "full_train": 48,
        "full_validation": 16,
        "reused_smoke_train": 8,
        "reused_smoke_validation": 4,
        "new_train": 40,
        "new_validation": 12,
        "test": 0,
        "protected_sensitivity": 0,
    }
    actual = {name: int(membership[name]) for name in expected}
    if actual != expected:
        raise ValueError(f"successor bulk membership changed: {actual}")
    if not all(config["reuse_policy"].values()):
        raise ValueError("successor bulk smoke-reuse policy changed")
    prior = config["newton_prior"]
    if prior["observation_time_mode"] != "independent_fixed":
        raise ValueError("successor bulk Newton timing changed")
    if not prior["chrono_target_time_must_not_control_newton_rollout"]:
        raise ValueError("Chrono target time cannot control the Newton rollout")
    schema = config["tensor_schema"]
    if schema["global_parameter_vector"] != ["bekker_kphi"]:
        raise ValueError("successor bulk must condition on Kphi alone")
    if "plastic_jacobian" not in schema["excluded_fields"]:
        raise ValueError("successor bulk plastic exclusion changed")
    if not schema["target_arrays_are_never_model_inputs"]:
        raise ValueError("successor bulk input/target separation changed")
    if int(config["execution"]["workers"]) != 2:
        raise ValueError("successor bulk requires the qualified two-worker identity")
    config["smoke_exit"] = dict(config["bulk_exit"])
    return config


def output_root(config: Mapping[str, Any]) -> Path:
    return fresh.repo_path(config["execution"]["output_root"])


def chrono_root(config: Mapping[str, Any]) -> Path:
    return fresh.repo_path(config["execution"]["chrono_output_root"])


def bulk_plan_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "bulk_plan.json"


def bulk_summary_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "bulk_summary.json"


# The proven base builder records the active plan hash in newly created bed
# metadata. Existing smoke beds keep their smoke-plan provenance; the reserved
# validation bed created by this runner binds the bulk plan instead.
smoke.base.plan_path = bulk_plan_path


def load_dataset_plan(config: Mapping[str, Any]) -> tuple[Path, dict[str, Any]]:
    path = fresh.repo_path(config["dataset_plan"])
    if not path.is_file() or sha256(path) != EXPECTED_DATASET_PLAN_SHA256:
        raise RuntimeError("frozen successor dataset plan changed")
    plan = load_json(path)
    if plan.get("test_lock_sha256") != EXPECTED_TEST_LOCK_SHA256:
        raise RuntimeError("successor test lock changed")
    if plan.get("sensitivity_lock_sha256") != EXPECTED_SENSITIVITY_LOCK_SHA256:
        raise RuntimeError("successor sensitivity lock changed")
    if smoke.base.canonical_sha256(plan["episodes"]) != plan["episode_manifest_sha256"]:
        raise RuntimeError("successor episode manifest changed")
    for split, key in (
        ("test", "test_lock_sha256"),
        ("protected_sensitivity", "sensitivity_lock_sha256"),
    ):
        expected = smoke.base.canonical_sha256(
            [
                {"episode_id": item["episode_id"], "input_sha256": item["input_sha256"]}
                for item in plan["episodes"][split]
            ]
        )
        if plan[key] != expected:
            raise RuntimeError(f"successor {split} lock payload changed")
    return path, plan


def selected_episodes(config: Mapping[str, Any], dataset_plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    episodes = [
        dict(item)
        for split in ("train", "validation")
        for item in dataset_plan["episodes"][split]
    ]
    membership = config["membership"]
    counts = {
        "train": sum(item["split"] == "train" for item in episodes),
        "validation": sum(item["split"] == "validation" for item in episodes),
    }
    if counts != {
        "train": int(membership["full_train"]),
        "validation": int(membership["full_validation"]),
    }:
        raise ValueError(f"successor bulk split counts changed: {counts}")
    if any(item["target_access"] == "locked" for item in episodes):
        raise ValueError("successor bulk crossed a protected target lock")
    expected_seeds = sorted(int(value) for value in config["bulk_exit"]["required_surface_seeds"])
    actual_seeds = sorted({int(item["initial_surface_seed"]) for item in episodes})
    if actual_seeds != expected_seeds:
        raise ValueError(f"successor bulk surface coverage changed: {actual_seeds}")
    return episodes


def protected_episodes(dataset_plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(item)
        for split in ("test", "protected_sensitivity")
        for item in dataset_plan["episodes"][split]
    ]


def assert_protected_targets_absent(config: Mapping[str, Any], dataset_plan: Mapping[str, Any]) -> None:
    present: list[str] = []
    for episode in protected_episodes(dataset_plan):
        episode_id = episode["episode_id"]
        for path in (
            chrono_root(config) / episode_id,
            output_root(config) / "episodes" / episode_id,
        ):
            if path.exists():
                present.append(str(path))
    if present:
        raise RuntimeError(f"protected successor target artifacts are present: {present}")


def require_smoke_pass(config: Mapping[str, Any]) -> dict[str, Any]:
    prerequisites = config["prerequisites"]
    smoke_config_path = fresh.repo_path(prerequisites["smoke_config"])
    smoke_plan_path = fresh.repo_path(prerequisites["smoke_plan"])
    smoke_summary_path = fresh.repo_path(prerequisites["smoke_summary"])
    if not smoke_config_path.is_file() or sha256(smoke_config_path) != prerequisites["smoke_config_sha256"]:
        raise RuntimeError("frozen successor smoke config changed")
    if not smoke_plan_path.is_file() or sha256(smoke_plan_path) != prerequisites["smoke_plan_sha256"]:
        raise RuntimeError("frozen successor smoke plan changed")
    smoke_plan = load_json(smoke_plan_path)
    if smoke_plan.get("status") != "frozen_before_first_target":
        raise RuntimeError("successor smoke plan is not frozen")
    if smoke_plan.get("counts") != {
        "train": 8,
        "validation": 4,
        "test": 0,
        "protected_sensitivity": 0,
    }:
        raise RuntimeError("successor smoke membership changed")
    if not smoke_summary_path.is_file():
        raise RuntimeError("successor smoke gate is incomplete; bulk planning remains locked")
    summary = load_json(smoke_summary_path)
    if summary.get("status") != prerequisites["required_smoke_status"]:
        raise RuntimeError("successor smoke gate did not pass")
    if summary.get("remaining_train_validation_permitted") is not True:
        raise RuntimeError("successor smoke does not permit remaining train/validation targets")
    if summary.get("test_or_protected_sensitivity_permitted") is not False:
        raise RuntimeError("successor smoke protected-target permission changed")
    if summary.get("identity", {}).get("smoke_plan_sha256") != prerequisites["smoke_plan_sha256"]:
        raise RuntimeError("successor smoke summary is not bound to the frozen smoke plan")
    expected_ids = {item["episode_id"] for item in smoke_plan["episodes"]}
    actual_ids = set(summary.get("episodes", {}))
    if actual_ids != expected_ids:
        raise RuntimeError("successor smoke summary membership changed")
    if not all(
        item.get("complete") is True and item.get("admitted") is True
        for item in summary["episodes"].values()
    ):
        raise RuntimeError("successor smoke members are not all admitted")
    for path_key, hash_key, required_status in (
        ("surface_qualification_summary", "surface_qualification_summary_sha256", "required_surface_status"),
        ("latent_summary", "latent_summary_sha256", "required_latent_status"),
    ):
        path = fresh.repo_path(prerequisites[path_key])
        if not path.is_file() or sha256(path) != prerequisites[hash_key]:
            raise RuntimeError(f"successor bulk prerequisite changed: {path_key}")
        if load_json(path).get("status") != prerequisites[required_status]:
            raise RuntimeError(f"successor bulk prerequisite did not pass: {path_key}")
    return {"plan": smoke_plan, "summary": summary, "summary_path": smoke_summary_path}


def split_smoke_and_remaining(
    config: Mapping[str, Any],
    episodes: list[dict[str, Any]],
    smoke_plan: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_id = {item["episode_id"]: item for item in episodes}
    reused: list[dict[str, Any]] = []
    for frozen in smoke_plan["episodes"]:
        episode_id = frozen["episode_id"]
        if episode_id not in by_id or by_id[episode_id]["input_sha256"] != frozen["input_sha256"]:
            raise RuntimeError(f"smoke member is not the same bulk input: {episode_id}")
        reused.append(by_id[episode_id])
    reused_ids = {item["episode_id"] for item in reused}
    remaining = [item for item in episodes if item["episode_id"] not in reused_ids]
    membership = config["membership"]
    reused_counts = {
        "train": sum(item["split"] == "train" for item in reused),
        "validation": sum(item["split"] == "validation" for item in reused),
    }
    remaining_counts = {
        "train": sum(item["split"] == "train" for item in remaining),
        "validation": sum(item["split"] == "validation" for item in remaining),
    }
    if reused_counts != {
        "train": int(membership["reused_smoke_train"]),
        "validation": int(membership["reused_smoke_validation"]),
    }:
        raise RuntimeError(f"successor smoke reuse counts changed: {reused_counts}")
    if remaining_counts != {
        "train": int(membership["new_train"]),
        "validation": int(membership["new_validation"]),
    }:
        raise RuntimeError(f"successor remaining counts changed: {remaining_counts}")
    return reused, remaining


def reused_artifact_paths(config: Mapping[str, Any], reused: list[dict[str, Any]]) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for episode in reused:
        episode_id = episode["episode_id"]
        local = smoke.base.episode_root(config, episode_id)
        response = smoke.base.response_root(config, episode_id)
        chrono = smoke.base.chrono_episode(config, episode_id)
        members = {
            "episode_summary": local / "episode_summary.json",
            "tensor_manifest": local / "tensors" / "tensor_manifest.json",
            "model_inputs": local / "tensors" / "model_inputs.npz",
            "targets": local / "tensors" / "targets.npz",
            "newton_manifest": response / "newton_cylinder_manifest.json",
            "chrono_manifest": chrono / "manifest.yaml",
        }
        for label, path in members.items():
            if not path.is_file():
                raise RuntimeError(f"missing admitted smoke artifact: {path}")
            paths[f"{episode_id}:{label}"] = path
    return paths


def source_paths(
    config_path: Path,
    config: Mapping[str, Any],
    successor_path: Path,
    operations_path: Path,
    contract: Mapping[str, Any],
) -> dict[str, Path]:
    smoke_config_path = fresh.repo_path(config["prerequisites"]["smoke_config"])
    smoke_config = smoke.load_config(smoke_config_path)
    shared = smoke.source_paths(
        smoke_config_path,
        smoke_config,
        successor_path,
        operations_path,
        contract,
    )
    return {
        "bulk_config": config_path.resolve(),
        "bulk_runner": Path(__file__).resolve(),
        "bulk_tests": REPO_ROOT / "tests" / "test_phase1_one_action_successor_bulk.py",
        **{f"shared_{name}": path for name, path in shared.items()},
    }


def build_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    successor_path, successor, operations_path, contract = smoke.merged_contract(config)
    smoke_evidence = require_smoke_pass(config)
    dataset_path, dataset = load_dataset_plan(config)
    if dataset.get("contract_sha256") != sha256(successor_path):
        raise RuntimeError("successor plan and contract binding changed")
    if dataset.get("permissions") != successor["permissions_after_dataset_plan_freeze"]:
        raise RuntimeError("successor dataset-plan permissions changed")
    assert_protected_targets_absent(config, dataset)
    episodes = selected_episodes(config, dataset)
    reused, remaining = split_smoke_and_remaining(config, episodes, smoke_evidence["plan"])
    reused_paths = reused_artifact_paths(config, reused)
    sources = source_paths(config_path, config, successor_path, operations_path, contract)
    missing_sources = [str(path) for path in sources.values() if not path.is_file()]
    if missing_sources:
        raise FileNotFoundError(f"missing successor bulk sources: {missing_sources}")
    inputs = {
        "dataset_plan": dataset_path,
        "smoke_plan": fresh.repo_path(config["prerequisites"]["smoke_plan"]),
        "smoke_summary": smoke_evidence["summary_path"],
        "surface_qualification_summary": fresh.repo_path(config["prerequisites"]["surface_qualification_summary"]),
        "latent_summary": fresh.repo_path(config["prerequisites"]["latent_summary"]),
    }
    for seed in sorted({int(item["initial_surface_seed"]) for item in episodes}):
        root = fresh.repo_path(config["execution"]["surface_root"]) / f"surface_{seed}"
        for label, filename in (
            ("heightmap", "initial_heightmap_m.npy"),
            ("qualification", "qualification_summary.json"),
        ):
            path = root / filename
            if not path.is_file():
                raise FileNotFoundError(f"missing qualified successor surface: {path}")
            inputs[f"surface_{seed}:{label}"] = path
    return {
        "schema_version": 1,
        "dataset_id": config["dataset_id"],
        "status": "frozen_after_smoke_pass_before_first_remaining_target",
        "config_sha256": sha256(config_path),
        "successor_contract_sha256": sha256(successor_path),
        "operations_contract_sha256": sha256(operations_path),
        "dataset_plan_sha256": sha256(dataset_path),
        "episode_manifest_sha256": dataset["episode_manifest_sha256"],
        "test_lock_sha256": dataset["test_lock_sha256"],
        "sensitivity_lock_sha256": dataset["sensitivity_lock_sha256"],
        "full_train_validation_manifest_sha256": smoke.base.canonical_sha256(episodes),
        "reused_smoke_manifest_sha256": smoke.base.canonical_sha256(reused),
        "remaining_manifest_sha256": smoke.base.canonical_sha256(remaining),
        "source_sha256": {name: sha256(path) for name, path in sources.items()},
        "input_sha256": {name: sha256(path) for name, path in inputs.items()},
        "reused_smoke_artifact_sha256": {name: sha256(path) for name, path in reused_paths.items()},
        "environment": smoke.base.environment_probe(config, contract),
        "repository_revisions": {
            "tera_splat": fresh.command_output(["git", "rev-parse", "HEAD"], REPO_ROOT),
            "tera_splat_sim": fresh.command_output(
                ["git", "rev-parse", "HEAD"], fresh.repo_path(contract["chrono"]["repo"])
            ),
        },
        "episodes": episodes,
        "reused_smoke_episode_ids": [item["episode_id"] for item in reused],
        "remaining_episodes": remaining,
        "counts": {
            "total": 64,
            "train": 48,
            "validation": 16,
            "reused_smoke": 12,
            "remaining": 52,
            "test": 0,
            "protected_sensitivity": 0,
        },
        "surface_seeds": sorted({int(item["initial_surface_seed"]) for item in episodes}),
        "qualified_optional_families": config["prerequisites"]["qualified_optional_families"],
        "excluded_families": config["prerequisites"]["excluded_families"],
        "newton_prior": config["newton_prior"],
        "tensor_schema": config["tensor_schema"],
        "worker_count": int(config["execution"]["workers"]),
        "training_permitted": False,
        "test_or_protected_sensitivity_permitted": False,
    }


def stable_plan_keys() -> tuple[str, ...]:
    return (
        "config_sha256",
        "successor_contract_sha256",
        "operations_contract_sha256",
        "dataset_plan_sha256",
        "episode_manifest_sha256",
        "test_lock_sha256",
        "sensitivity_lock_sha256",
        "full_train_validation_manifest_sha256",
        "reused_smoke_manifest_sha256",
        "remaining_manifest_sha256",
        "source_sha256",
        "input_sha256",
        "reused_smoke_artifact_sha256",
        "environment",
        "episodes",
        "remaining_episodes",
        "tensor_schema",
        "worker_count",
    )


def write_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    plan = build_plan(config_path, config)
    path = bulk_plan_path(config)
    if path.exists():
        existing = load_json(path)
        changed = [key for key in stable_plan_keys() if existing.get(key) != plan.get(key)]
        if changed:
            raise RuntimeError(f"refusing changed successor bulk plan: {changed}")
        return existing
    fresh.write_json(path, plan)
    return plan


def load_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    path = bulk_plan_path(config)
    if not path.is_file():
        raise RuntimeError("successor bulk plan is absent; run --stage plan after smoke passes")
    frozen = load_json(path)
    current = build_plan(config_path, config)
    changed = [key for key in stable_plan_keys() if frozen.get(key) != current.get(key)]
    if changed:
        raise RuntimeError(f"successor bulk identity changed: {changed}")
    return frozen


def choose_remaining(plan: Mapping[str, Any], requested: list[str]) -> list[dict[str, Any]]:
    remaining = list(plan["remaining_episodes"])
    by_id = {item["episode_id"]: item for item in remaining}
    reused = set(plan["reused_smoke_episode_ids"])
    reused_requested = sorted(set(requested) & reused)
    if reused_requested:
        raise ValueError(f"smoke response regeneration is prohibited: {reused_requested}")
    unknown = sorted(set(requested) - set(by_id))
    if unknown:
        raise ValueError(f"unknown or protected successor bulk episodes: {unknown}")
    return [by_id[name] for name in requested] if requested else remaining


def verify_reused_artifacts(config: Mapping[str, Any], plan: Mapping[str, Any]) -> bool:
    by_id = {item["episode_id"]: item for item in plan["episodes"]}
    reused = [by_id[name] for name in plan["reused_smoke_episode_ids"]]
    paths = reused_artifact_paths(config, reused)
    current = {name: sha256(path) for name, path in paths.items()}
    return current == plan["reused_smoke_artifact_sha256"]


def summarize(config: Mapping[str, Any], contract: Mapping[str, Any], plan: Mapping[str, Any]) -> dict[str, Any]:
    _dataset_path, dataset = load_dataset_plan(config)
    assert_protected_targets_absent(config, dataset)
    episodes = [smoke.base.analyze_episode(config, contract, item) for item in plan["episodes"]]
    counts = {
        "total": len(episodes),
        "train": sum(item["split"] == "train" for item in episodes),
        "validation": sum(item["split"] == "validation" for item in episodes),
        "test": sum(item["split"] == "test" for item in episodes),
        "protected_sensitivity": 0,
    }
    exit_contract = config["bulk_exit"]
    checks = {
        "episode_count": counts["total"] == int(exit_contract["required_episode_count"]),
        "train_count": counts["train"] == int(exit_contract["required_train_count"]),
        "validation_count": counts["validation"] == int(exit_contract["required_validation_count"]),
        "test_and_sensitivity_targets_unopened": counts["test"] == 0,
        "all_complete": all(item["complete"] for item in episodes),
        "all_admitted": all(item["admitted"] for item in episodes),
        "surface_coverage": sorted(plan["surface_seeds"])
        == sorted(int(value) for value in exit_contract["required_surface_seeds"]),
        "reused_smoke_artifacts_unchanged": verify_reused_artifacts(config, plan),
    }
    passed = all(checks.values())
    summary = {
        "schema_version": 1,
        "dataset_id": config["dataset_id"],
        "status": "passed" if passed else "failed_or_incomplete",
        "training_plan_freeze_permitted": passed,
        "test_or_protected_sensitivity_permitted": False,
        "counts": counts,
        "checks": checks,
        "identity": {
            "bulk_plan_sha256": sha256(bulk_plan_path(config)),
            "full_train_validation_manifest_sha256": plan["full_train_validation_manifest_sha256"],
            "test_lock_sha256": plan["test_lock_sha256"],
            "sensitivity_lock_sha256": plan["sensitivity_lock_sha256"],
        },
        "episodes": {item["episode_id"]: item for item in episodes},
    }
    fresh.write_json(bulk_summary_path(config), summary)
    return summary


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = load_config(config_path)
    workers = int(args.workers or config["execution"]["workers"])
    if workers != int(config["execution"]["workers"]):
        raise ValueError("worker count differs from frozen successor bulk identity")
    if args.stage == "plan":
        plan = write_plan(config_path, config)
        print(
            json.dumps(
                {
                    "plan": str(bulk_plan_path(config)),
                    "sha256": sha256(bulk_plan_path(config)),
                    "counts": plan["counts"],
                    "smoke_targets_reused": 12,
                    "new_targets_permitted": 52,
                    "protected_targets_opened": False,
                },
                indent=2,
            )
        )
        return
    plan = load_plan(config_path, config)
    _successor_path, _successor, _operations_path, contract = smoke.merged_contract(config)
    episodes = choose_remaining(plan, args.episode)
    if args.stage in ("chrono", "all"):
        smoke.run_parallel("chrono", episodes, workers, lambda item: smoke.run_chrono(config, contract, item))
    seeds = sorted({int(item["initial_surface_seed"]) for item in episodes})
    if args.stage in ("bed", "all"):
        smoke.run_parallel("bed", seeds, workers, lambda seed: smoke.base.build_bed(config, contract, plan, seed))
    if args.stage in ("newton", "all"):
        smoke.run_parallel("preparation", seeds, workers, lambda seed: smoke.base.prepare_prior(config, contract, plan, seed))
        smoke.run_parallel("response", episodes, workers, lambda item: smoke.base.run_newton(config, contract, plan, item))
    if args.stage in ("analyze", "all"):
        for episode in episodes:
            smoke.base.analyze_episode(config, contract, episode)
    summary = summarize(config, contract, plan)
    print(
        json.dumps(
            {
                "status": summary["status"],
                "training_plan_freeze_permitted": summary["training_plan_freeze_permitted"],
                "test_or_protected_sensitivity_permitted": False,
                "counts": summary["counts"],
                "checks": summary["checks"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

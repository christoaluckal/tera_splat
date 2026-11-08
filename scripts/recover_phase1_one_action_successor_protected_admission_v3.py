#!/usr/bin/env python3
"""Recover protected admission from a post-unlock smoke-sentinel mismatch."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import evaluate_phase1_one_action_successor as evaluation
import recover_phase1_one_action_successor_protected_v1 as recovery_v1
import run_fresh_phase0_repeatability as fresh


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_protected_admission_recovery_v3.json"
EXPECTED_ID = "phase1_one_action_successor_protected_admission_recovery_v3"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--stage", choices=("plan", "run", "all"), default="plan")
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    value = json.loads(path.resolve().read_text(encoding="utf-8"))
    if value.get("schema_version") != 1 or value.get("recovery_id") != EXPECTED_ID:
        raise ValueError("unexpected protected admission-recovery identity")
    semantics = value.get("semantics", {})
    required_true = (
        "artifact_only",
        "preserve_failed_analysis",
        "require_exact_24_test_only_false_no_test_target",
        "replace_smoke_sentinel_with_joint_unlock_check",
        "preserve_serial_execution_identity_qualification",
        "prediction_requires_recovered_30_member_admission",
    )
    if not all(semantics.get(name) is True for name in required_true):
        raise ValueError("protected admission-recovery semantics weakened")
    if semantics.get("simulator_rerun_performed") is not False:
        raise ValueError("admission recovery may not rerun a simulator")
    if semantics.get("tensor_array_replacement_performed") is not False:
        raise ValueError("admission recovery may not replace tensor arrays")
    return value


def output_root(config: Mapping[str, Any]) -> Path:
    return fresh.repo_path(config["output_root"])


def plan_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "recovery_plan.json"


def summary_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "recovery_summary.json"


def required_file(config: Mapping[str, Any], key: str, sha_key: str) -> Path:
    path = fresh.repo_path(config[key])
    if not path.is_file() or evaluation.sha256_file(path) != config[sha_key]:
        raise RuntimeError(f"required {key} identity changed")
    return path


def context(config: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    eval_path = fresh.repo_path(config["evaluation_config"])
    eval_config = evaluation.load_config(eval_path)
    plan = evaluation.load_plan(eval_path, eval_config)
    evaluation.require_opened(eval_config, plan)
    if evaluation.sha256_file(evaluation.plan_path(eval_config)) != config["required_evaluation_plan_sha256"]:
        raise RuntimeError("evaluation plan identity changed")
    if evaluation.sha256_file(evaluation.opened_path(eval_config)) != config["required_open_marker_sha256"]:
        raise RuntimeError("protected open marker identity changed")
    return eval_config, plan


def artifact_hashes(eval_config: Mapping[str, Any], plan: Mapping[str, Any]) -> dict[str, str]:
    paths = evaluation.protected_artifact_paths(eval_config, plan)
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise RuntimeError(f"protected artifacts are incomplete: {missing}")
    return {name: evaluation.sha256_file(path) for name, path in sorted(paths.items())}


def false_checks(row: Mapping[str, Any]) -> list[str]:
    return sorted(name for name, passed in row["tensor_manifest"]["checks"].items() if passed is not True)


def validate_failed_analysis(summary: Mapping[str, Any]) -> None:
    if summary.get("status") != "failed_or_incomplete" or summary.get("prediction_permitted") is not False:
        raise RuntimeError("protected analysis is not the required failed state")
    episodes = summary.get("episodes", {})
    if len(episodes) != 30:
        raise RuntimeError("failed protected analysis membership changed")
    failed = [row for row in episodes.values() if row.get("admitted") is not True]
    if len(failed) != 24 or Counter(str(row["split"]) for row in failed) != {"test": 24}:
        raise RuntimeError("protected analysis does not fail exactly 24 test members")
    for row in failed:
        if not all(row["numerical_checks"].values()) or not all(row["interaction_artifact_checks"].values()):
            raise RuntimeError("a failed test member has a scientific admission failure")
        if false_checks(row) != ["no_test_target"]:
            raise RuntimeError("test admission has a failure beyond the smoke-only sentinel")
    for row in episodes.values():
        if row["split"] == "protected_sensitivity" and row.get("admitted") is not True:
            raise RuntimeError("protected sensitivity member is not admitted")


def build_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    eval_config, plan = context(config)
    failed_path = required_file(config, "failed_protected_summary", "required_failed_protected_summary_sha256")
    serial_path = required_file(config, "serial_recovery_summary", "required_serial_recovery_summary_sha256")
    failed = json.loads(failed_path.read_text(encoding="utf-8"))
    serial = json.loads(serial_path.read_text(encoding="utf-8"))
    validate_failed_analysis(failed)
    if serial.get("status") != "passed_with_execution_identity_qualification":
        raise RuntimeError("serial Newton recovery has not passed with its qualification")
    payload = {
        "schema_version": 1,
        "recovery_id": EXPECTED_ID,
        "status": "frozen_before_artifact_only_reanalysis",
        "config_sha256": evaluation.sha256_file(config_path.resolve()),
        "evaluation_plan_sha256": evaluation.sha256_file(evaluation.plan_path(eval_config)),
        "protected_open_sha256": evaluation.sha256_file(evaluation.opened_path(eval_config)),
        "failed_protected_summary_sha256": evaluation.sha256_file(failed_path),
        "serial_recovery_summary_sha256": evaluation.sha256_file(serial_path),
        "protected_artifact_sha256_before": artifact_hashes(eval_config, plan),
        "semantics": dict(config["semantics"]),
        "source_sha256": {
            "admission_recovery_runner": evaluation.sha256_file(Path(__file__).resolve()),
            "evaluator": evaluation.sha256_file(Path(evaluation.__file__)),
        },
    }
    output_root(config).mkdir(parents=True, exist_ok=True)
    evaluation.write_json(plan_path(config), payload)
    return payload


def load_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    path = plan_path(config)
    if not path.is_file():
        raise RuntimeError("freeze protected admission-recovery plan before runtime")
    plan = json.loads(path.read_text(encoding="utf-8"))
    if plan.get("recovery_id") != EXPECTED_ID or plan.get("status") != "frozen_before_artifact_only_reanalysis":
        raise RuntimeError("protected admission-recovery plan identity changed")
    if plan.get("config_sha256") != evaluation.sha256_file(config_path.resolve()):
        raise RuntimeError("protected admission-recovery config changed after freeze")
    sources = {
        "admission_recovery_runner": evaluation.sha256_file(Path(__file__).resolve()),
        "evaluator": evaluation.sha256_file(Path(evaluation.__file__)),
    }
    if plan.get("source_sha256") != sources:
        raise RuntimeError("protected admission-recovery sources changed after freeze")
    return plan


def episode_paths(eval_config: Mapping[str, Any], evaluation_plan: Mapping[str, Any]) -> dict[str, tuple[Path, Path]]:
    root = evaluation.repo_path(eval_config["execution"]["dataset_output_root"]) / "episodes"
    return {
        str(item["episode_id"]): (
            root / str(item["episode_id"]) / "episode_summary.json",
            root / str(item["episode_id"]) / "tensors" / "tensor_manifest.json",
        )
        for split in ("test", "protected_sensitivity")
        for item in evaluation_plan["episodes"][split]
    }


def run(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    frozen = load_plan(config_path, config)
    eval_config, evaluation_plan = context(config)
    failed_path = required_file(config, "failed_protected_summary", "required_failed_protected_summary_sha256")
    failed = json.loads(failed_path.read_text(encoding="utf-8"))
    validate_failed_analysis(failed)
    if artifact_hashes(eval_config, evaluation_plan) != frozen["protected_artifact_sha256_before"]:
        raise RuntimeError("protected artifacts changed after admission-recovery freeze")
    archive = output_root(config) / "original_failed_analysis"
    if archive.exists():
        raise RuntimeError("protected admission recovery already ran")
    archive.mkdir(parents=True)
    shutil.copy2(failed_path, archive / "protected_dataset_summary.json")
    paths = episode_paths(eval_config, evaluation_plan)
    for episode_id, (episode_summary, tensor_manifest) in paths.items():
        destination = archive / episode_id
        destination.mkdir(parents=True)
        shutil.copy2(episode_summary, destination / "episode_summary.json")
        shutil.copy2(tensor_manifest, destination / "tensor_manifest.json")

    rows: list[dict[str, Any]] = []
    for split in ("test", "protected_sensitivity"):
        for item in evaluation_plan["episodes"][split]:
            episode_id = str(item["episode_id"])
            episode_summary_path, tensor_manifest_path = paths[episode_id]
            row = json.loads(episode_summary_path.read_text(encoding="utf-8"))
            manifest = json.loads(tensor_manifest_path.read_text(encoding="utf-8"))
            if split == "test":
                if false_checks(row) != ["no_test_target"]:
                    raise RuntimeError(f"unexpected test tensor checks for {episode_id}")
                checks = dict(manifest["checks"])
                checks.pop("no_test_target")
                checks["protected_target_opened_after_joint_unlock"] = True
                manifest["checks"] = checks
                evaluation.write_json(tensor_manifest_path, manifest)
                row["tensor_manifest"] = manifest
                row["admitted"] = all(row["numerical_checks"].values()) and all(row["interaction_artifact_checks"].values()) and all(checks.values())
                row["analysis_recovery_id"] = EXPECTED_ID
                evaluation.write_json(episode_summary_path, row)
            rows.append(row)

    counts = Counter(str(row["split"]) for row in rows)
    test_groups = Counter(str(item["holdout_group"]) for item in evaluation_plan["episodes"]["test"])
    checks = {
        "episode_count": len(rows) == 30,
        "test_count": counts == {"test": 24, "protected_sensitivity": 6},
        "all_complete": all(row.get("complete") is True for row in rows),
        "all_admitted": all(row.get("admitted") is True for row in rows),
        "test_holdout_groups": dict(test_groups) == eval_config["membership"]["test_holdout_groups"],
        "protected_open_identity": evaluation.require_opened(eval_config, evaluation_plan).get("targets_opened") is True,
        "simulator_rerun_performed": False,
        "tensor_array_replacement_performed": False,
        "failed_analysis_preserved": (archive / "protected_dataset_summary.json").is_file(),
        "serial_execution_identity_qualification_preserved": True,
    }
    passed = all(value is True for name, value in checks.items() if name not in {"simulator_rerun_performed", "tensor_array_replacement_performed"}) and checks["simulator_rerun_performed"] is False and checks["tensor_array_replacement_performed"] is False
    artifact_after = evaluation.protected_artifact_identity(eval_config, evaluation_plan) if passed else {}
    recovered = {
        "schema_version": 1,
        "status": "passed" if passed else "failed_or_incomplete",
        "evaluation_plan_sha256": evaluation.sha256_file(evaluation.plan_path(eval_config)),
        "protected_open_sha256": evaluation.sha256_file(evaluation.opened_path(eval_config)),
        "counts": {"total": len(rows), "test": counts.get("test", 0), "protected_sensitivity": counts.get("protected_sensitivity", 0)},
        "checks": checks,
        "prediction_permitted": passed,
        "episodes": {str(row["episode_id"]): row for row in rows},
        "artifact_sha256": artifact_after,
        "analysis_recovery_id": EXPECTED_ID,
        "analysis_recovery_plan_sha256": evaluation.sha256_file(plan_path(config)),
        "original_failed_summary_sha256": frozen["failed_protected_summary_sha256"],
        "serial_recovery_summary_sha256": frozen["serial_recovery_summary_sha256"],
        "execution_identity_qualification": "member 019 is a serial retry after two preserved dual-process failures",
    }
    evaluation.write_json(failed_path, recovered)
    result = {
        "schema_version": 1,
        "recovery_id": EXPECTED_ID,
        "status": "passed" if passed else "failed",
        "recovery_plan_sha256": evaluation.sha256_file(plan_path(config)),
        "checks": checks,
        "protected_dataset_summary_sha256": evaluation.sha256_file(failed_path),
        "protected_artifact_sha256_after": artifact_after,
        "prediction_permitted": passed,
        "execution_identity_qualification": recovered["execution_identity_qualification"],
    }
    evaluation.write_json(summary_path(config), result)
    return result


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = load_config(config_path)
    if args.stage == "plan":
        result = build_plan(config_path, config)
    else:
        if args.stage == "all" and not plan_path(config).is_file():
            build_plan(config_path, config)
        result = run(config_path, config)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

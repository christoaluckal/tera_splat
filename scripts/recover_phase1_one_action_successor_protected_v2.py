#!/usr/bin/env python3
"""Prospectively perform one serial retry after two dual-process failures."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import evaluate_phase1_one_action_successor as evaluation
import recover_phase1_one_action_successor_protected_v1 as v1
import run_fresh_phase0_repeatability as fresh


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_protected_recovery_v2.json"
EXPECTED_ID = "phase1_one_action_successor_protected_recovery_v2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--stage", choices=("plan", "run", "analyze", "all"), default="plan")
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    value = json.loads(path.resolve().read_text(encoding="utf-8"))
    if value.get("schema_version") != 1 or value.get("recovery_id") != EXPECTED_ID:
        raise ValueError("unexpected protected serial-recovery identity")
    semantics = value.get("semantics", {})
    required_true = (
        "preserve_both_failed_attempts",
        "generate_only_missing_official_response",
        "serial_retry_is_execution_identity_qualification",
        "prediction_requires_original_30_member_admission",
    )
    if not all(semantics.get(name) is True for name in required_true):
        raise ValueError("protected serial-recovery semantics weakened")
    for name in (
        "replace_completed_official_response",
        "may_claim_clean_two_worker_identity",
        "allow_additional_retry_without_new_plan",
    ):
        if semantics.get(name) is not False:
            raise ValueError(f"protected serial-recovery requires {name}=false")
    if int(value["execution"]["workers"]) != 1:
        raise ValueError("protected serial recovery requires exactly one worker")
    return value


def output_root(config: Mapping[str, Any]) -> Path:
    return fresh.repo_path(config["execution"]["output_root"])


def plan_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "recovery_plan.json"


def summary_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "recovery_summary.json"


def required_file(config: Mapping[str, Any], key: str, sha_key: str) -> Path:
    path = fresh.repo_path(config[key])
    if not path.is_file() or evaluation.sha256_file(path) != config[sha_key]:
        raise RuntimeError(f"required {key} identity changed")
    return path


def file_identities(paths: list[Path], base: Path) -> dict[str, str]:
    return {str(path.relative_to(base)): evaluation.sha256_file(path) for path in sorted(paths)}


def build_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    previous_plan_path = required_file(config, "previous_recovery_plan", "required_previous_recovery_plan_sha256")
    previous_summary_path = required_file(config, "previous_recovery_summary", "required_previous_recovery_summary_sha256")
    previous_plan = json.loads(previous_plan_path.read_text(encoding="utf-8"))
    previous_summary = json.loads(previous_summary_path.read_text(encoding="utf-8"))
    if previous_summary.get("status") != "failed" or previous_summary.get("checks", {}).get("official_retry") is not False:
        raise RuntimeError("v1 recovery failure is not established")
    if previous_summary.get("checks", {}).get("companion_retry") is not True:
        raise RuntimeError("v1 companion did not pass")
    eval_config, runtime, runtime_plan, _contract, episodes = v1.context(config)
    failed_id = str(config["failed_episode_id"])
    manifest = v1.response_dir(runtime, failed_id) / "newton_cylinder_manifest.json"
    if manifest.exists():
        raise RuntimeError("failed official response already has a manifest")
    root = v1.episode_dir(runtime, failed_id)
    paths = v1.failed_files(runtime, failed_id)
    log = root / "logs" / "newton_response.log"
    if not log.is_file() or evaluation.sha256_file(log) != config["failed_log_sha256"]:
        raise RuntimeError("second failed response log identity changed")
    attempt_1 = root / "failed_attempts" / "attempt_1_nonfinite_plastic_jacobian"
    if not attempt_1.is_dir():
        raise RuntimeError("first failed attempt archive is absent")
    episode_ids = [str(item["episode_id"]) for item in runtime_plan["episodes"]]
    completed = v1.completed_manifest_identities(runtime, episode_ids)
    if completed != previous_plan["completed_official_manifest_sha256"]:
        raise RuntimeError("completed official manifests changed after v1 recovery plan")
    payload = {
        "schema_version": 1,
        "recovery_id": EXPECTED_ID,
        "status": "frozen_before_serial_retry",
        "config_sha256": evaluation.sha256_file(config_path.resolve()),
        "evaluation_plan_sha256": evaluation.sha256_file(evaluation.plan_path(eval_config)),
        "protected_open_sha256": evaluation.sha256_file(evaluation.opened_path(eval_config)),
        "previous_recovery_plan_sha256": evaluation.sha256_file(previous_plan_path),
        "previous_recovery_summary_sha256": evaluation.sha256_file(previous_summary_path),
        "failed_episode_id": failed_id,
        "attempt_1_archive_sha256": file_identities([p for p in attempt_1.rglob("*") if p.is_file()], attempt_1),
        "attempt_2_sha256": file_identities(paths, root),
        "completed_official_manifest_sha256": completed,
        "execution": dict(config["execution"]),
        "semantics": dict(config["semantics"]),
        "source_sha256": {
            "serial_recovery_runner": evaluation.sha256_file(Path(__file__).resolve()),
            "v1_recovery_runner": evaluation.sha256_file(Path(v1.__file__)),
            "newton_runner": evaluation.sha256_file(SCRIPT_DIR / "run_newton_cylinder_diagnostic.py"),
        },
        "episode_input": episodes[failed_id],
    }
    output_root(config).mkdir(parents=True, exist_ok=True)
    evaluation.write_json(plan_path(config), payload)
    return payload


def load_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    path = plan_path(config)
    if not path.is_file():
        raise RuntimeError("freeze protected serial-recovery plan before runtime")
    plan = json.loads(path.read_text(encoding="utf-8"))
    if plan.get("recovery_id") != EXPECTED_ID or plan.get("status") != "frozen_before_serial_retry":
        raise RuntimeError("protected serial-recovery plan identity changed")
    if plan.get("config_sha256") != evaluation.sha256_file(config_path.resolve()):
        raise RuntimeError("protected serial-recovery config changed after freeze")
    current_sources = {
        "serial_recovery_runner": evaluation.sha256_file(Path(__file__).resolve()),
        "v1_recovery_runner": evaluation.sha256_file(Path(v1.__file__)),
        "newton_runner": evaluation.sha256_file(SCRIPT_DIR / "run_newton_cylinder_diagnostic.py"),
    }
    if plan.get("source_sha256") != current_sources:
        raise RuntimeError("protected serial-recovery sources changed after freeze")
    return plan


def archive_attempt_2(config: Mapping[str, Any], runtime: Mapping[str, Any], plan: Mapping[str, Any]) -> Path:
    failed_id = str(config["failed_episode_id"])
    root = v1.episode_dir(runtime, failed_id)
    archive = root / str(config["execution"]["failed_attempt_archive"])
    if archive.exists():
        raise RuntimeError("second-attempt archive already exists; another retry is prohibited")
    if file_identities(v1.failed_files(runtime, failed_id), root) != plan["attempt_2_sha256"]:
        raise RuntimeError("second failed attempt changed after plan freeze")
    archive.mkdir(parents=True)
    shutil.move(str(v1.response_dir(runtime, failed_id)), str(archive / "newton_response"))
    shutil.move(str(root / "logs" / "newton_response.log"), str(archive / "newton_response.log"))
    return archive


def run(config_path: Path, config: Mapping[str, Any]) -> None:
    plan = load_plan(config_path, config)
    _eval_config, runtime, runtime_plan, contract, episodes = v1.context(config)
    failed_id = str(config["failed_episode_id"])
    if v1.completed_manifest_identities(runtime, list(plan["completed_official_manifest_sha256"])) != plan["completed_official_manifest_sha256"]:
        raise RuntimeError("completed official manifests changed after serial-recovery freeze")
    archive_attempt_2(config, runtime, plan)
    output = v1.response_dir(runtime, failed_id)
    command = v1.newton_command(runtime, contract, runtime_plan, episodes[failed_id], output)
    fresh.run_logged(command, v1.episode_dir(runtime, failed_id) / "logs" / "newton_response.log", REPO_ROOT)


def archive_matches(archive: Path, expected: Mapping[str, str]) -> bool:
    if not archive.is_dir():
        return False
    current = file_identities([p for p in archive.rglob("*") if p.is_file()], archive)
    normalized = {
        ("newton_response.log" if name == "logs/newton_response.log" else name): sha
        for name, sha in expected.items()
    }
    return current == normalized


def analyze(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    plan = load_plan(config_path, config)
    _eval_config, runtime, runtime_plan, _contract, _episodes = v1.context(config)
    failed_id = str(config["failed_episode_id"])
    root = v1.episode_dir(runtime, failed_id)
    official = v1.response_dir(runtime, failed_id) / "newton_cylinder_manifest.json"
    checks = {
        "attempt_1_preserved": file_identities(
            [p for p in (root / "failed_attempts" / "attempt_1_nonfinite_plastic_jacobian").rglob("*") if p.is_file()],
            root / "failed_attempts" / "attempt_1_nonfinite_plastic_jacobian",
        ) == plan["attempt_1_archive_sha256"],
        "attempt_2_preserved": archive_matches(root / str(config["execution"]["failed_attempt_archive"]), plan["attempt_2_sha256"]),
        "completed_official_manifests_unchanged": v1.completed_manifest_identities(runtime, list(plan["completed_official_manifest_sha256"])) == plan["completed_official_manifest_sha256"],
        "official_serial_retry": all(v1.manifest_checks(official).values()),
        "official_manifest_count": len(v1.completed_manifest_identities(runtime, [str(item["episode_id"]) for item in runtime_plan["episodes"]])) == 30,
        "serial_identity_qualification_preserved": config["semantics"]["serial_retry_is_execution_identity_qualification"] is True and config["semantics"]["may_claim_clean_two_worker_identity"] is False,
    }
    passed = all(checks.values())
    result = {
        "schema_version": 1,
        "recovery_id": EXPECTED_ID,
        "status": "passed_with_execution_identity_qualification" if passed else "failed",
        "recovery_plan_sha256": evaluation.sha256_file(plan_path(config)),
        "checks": checks,
        "official_retry_manifest_sha256": evaluation.sha256_file(official) if official.is_file() else None,
        "prediction_permitted": False,
        "execution_identity_qualification": "member 019 is a serial retry after two preserved dual-process failures",
        "next_gate": "original_30_member_protected_admission",
    }
    evaluation.write_json(summary_path(config), result)
    return result


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = load_config(config_path)
    if args.stage == "plan":
        result = build_plan(config_path, config)
    elif args.stage == "run":
        run(config_path, config)
        result = {"status": "runtime_complete", "prediction_permitted": False}
    elif args.stage == "analyze":
        result = analyze(config_path, config)
    else:
        if not plan_path(config).is_file():
            build_plan(config_path, config)
        run(config_path, config)
        result = analyze(config_path, config)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

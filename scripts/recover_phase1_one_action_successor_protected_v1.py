#!/usr/bin/env python3
"""Prospectively recover the one missing protected Newton response.

The plan is frozen after the original failure and before any retry.  It binds
the failed attempt and all 29 completed official manifests.  Runtime archives
the failed attempt, then launches the missing official response and a separate
companion response concurrently so the frozen two-process execution identity
is retained without replacing a completed evaluation artifact.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Mapping


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import evaluate_phase1_one_action_successor as evaluation
import run_fresh_phase0_repeatability as fresh
import run_phase1_one_action_successor_protected as protected


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = (
    REPO_ROOT
    / "configs"
    / "phase1_one_action_successor_protected_recovery_v1.json"
)
EXPECTED_ID = "phase1_one_action_successor_protected_recovery_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--stage", choices=("plan", "run", "analyze", "all"), default="plan")
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    value = json.loads(path.resolve().read_text(encoding="utf-8"))
    if value.get("schema_version") != 1 or value.get("recovery_id") != EXPECTED_ID:
        raise ValueError("unexpected protected recovery identity")
    semantics = value.get("semantics", {})
    required_true = (
        "preserve_failed_attempt",
        "generate_only_missing_official_response",
        "companion_is_recovery_evidence_not_evaluation_membership",
        "require_two_concurrent_processes",
        "prediction_requires_original_30_member_admission",
    )
    if not all(semantics.get(name) is True for name in required_true):
        raise ValueError("protected recovery semantics weakened")
    if semantics.get("replace_completed_official_response") is not False:
        raise ValueError("completed official responses may not be replaced")
    if semantics.get("allow_additional_retry_without_new_plan") is not False:
        raise ValueError("additional retries require a new plan")
    if int(value["execution"]["workers"]) != 2:
        raise ValueError("protected recovery requires two workers")
    return value


def output_root(config: Mapping[str, Any]) -> Path:
    return fresh.repo_path(config["execution"]["output_root"])


def plan_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "recovery_plan.json"


def summary_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "recovery_summary.json"


def load_evaluation(config: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    path = fresh.repo_path(config["evaluation_config"])
    eval_config = evaluation.load_config(path)
    plan = evaluation.load_plan(path, eval_config)
    evaluation.require_opened(eval_config, plan)
    if evaluation.sha256_file(evaluation.plan_path(eval_config)) != config["required_evaluation_plan_sha256"]:
        raise RuntimeError("evaluation plan identity changed")
    if evaluation.sha256_file(evaluation.opened_path(eval_config)) != config["required_open_marker_sha256"]:
        raise RuntimeError("protected open-marker identity changed")
    return eval_config, plan


def context(config: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, dict[str, Any]]]:
    eval_config, plan = load_evaluation(config)
    runtime = protected.runtime_config(eval_config)
    runtime_plan = protected.configure_runtime_plan(eval_config, plan)
    _successor_path, _successor, _operations_path, contract = protected.smoke.merged_contract(runtime)
    episodes = {str(item["episode_id"]): item for item in runtime_plan["episodes"]}
    required = {str(config["failed_episode_id"]), str(config["companion_episode_id"])}
    if not required <= set(episodes):
        raise RuntimeError("recovery episodes are outside frozen protected membership")
    return eval_config, runtime, runtime_plan, contract, episodes


def response_dir(runtime: Mapping[str, Any], episode_id: str) -> Path:
    return protected.smoke.base.response_root(runtime, episode_id)


def episode_dir(runtime: Mapping[str, Any], episode_id: str) -> Path:
    return protected.smoke.base.episode_root(runtime, episode_id)


def failed_files(runtime: Mapping[str, Any], episode_id: str) -> list[Path]:
    root = episode_dir(runtime, episode_id)
    response = response_dir(runtime, episode_id)
    paths = [root / "logs" / "newton_response.log"]
    if response.is_dir():
        paths.extend(sorted(path for path in response.rglob("*") if path.is_file()))
    return paths


def file_identities(paths: list[Path], base: Path) -> dict[str, str]:
    return {
        str(path.relative_to(base)): evaluation.sha256_file(path)
        for path in sorted(paths)
    }


def completed_manifest_identities(runtime: Mapping[str, Any], episode_ids: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for episode_id in episode_ids:
        manifest = response_dir(runtime, episode_id) / "newton_cylinder_manifest.json"
        if manifest.is_file():
            result[episode_id] = evaluation.sha256_file(manifest)
    return result


def build_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    eval_config, runtime, runtime_plan, _contract, episodes = context(config)
    failed_id = str(config["failed_episode_id"])
    failed_response = response_dir(runtime, failed_id)
    failed_manifest = failed_response / "newton_cylinder_manifest.json"
    if failed_manifest.exists():
        raise RuntimeError("failed official response already has a manifest")
    paths = failed_files(runtime, failed_id)
    log_path = episode_dir(runtime, failed_id) / "logs" / "newton_response.log"
    if not log_path.is_file() or evaluation.sha256_file(log_path) != config["failed_log_sha256"]:
        raise RuntimeError("failed response log identity changed")
    if len(paths) < 2:
        raise RuntimeError("failed attempt evidence is incomplete")
    episode_ids = [str(item["episode_id"]) for item in runtime_plan["episodes"]]
    completed = completed_manifest_identities(runtime, episode_ids)
    if len(completed) != 29 or failed_id in completed:
        raise RuntimeError("recovery plan requires exactly 29 completed official manifests")
    payload = {
        "schema_version": 1,
        "recovery_id": EXPECTED_ID,
        "status": "frozen_before_retry",
        "config_sha256": evaluation.sha256_file(config_path.resolve()),
        "evaluation_plan_sha256": evaluation.sha256_file(evaluation.plan_path(eval_config)),
        "protected_open_sha256": evaluation.sha256_file(evaluation.opened_path(eval_config)),
        "failed_episode_id": failed_id,
        "companion_episode_id": str(config["companion_episode_id"]),
        "failed_attempt_sha256": file_identities(paths, episode_dir(runtime, failed_id)),
        "completed_official_manifest_sha256": completed,
        "completed_official_count": len(completed),
        "execution": dict(config["execution"]),
        "semantics": dict(config["semantics"]),
        "source_sha256": {
            "recovery_runner": evaluation.sha256_file(Path(__file__).resolve()),
            "protected_runner": evaluation.sha256_file(Path(protected.__file__)),
            "dataset_runner": evaluation.sha256_file(Path(protected.smoke.base.__file__)),
            "newton_runner": evaluation.sha256_file(SCRIPT_DIR / "run_newton_cylinder_diagnostic.py"),
        },
        "episode_inputs": {
            name: episodes[name] for name in (failed_id, str(config["companion_episode_id"]))
        },
    }
    output_root(config).mkdir(parents=True, exist_ok=True)
    evaluation.write_json(plan_path(config), payload)
    return payload


def load_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    path = plan_path(config)
    if not path.is_file():
        raise RuntimeError("freeze protected recovery plan before runtime")
    plan = json.loads(path.read_text(encoding="utf-8"))
    if plan.get("recovery_id") != EXPECTED_ID or plan.get("status") != "frozen_before_retry":
        raise RuntimeError("protected recovery plan identity changed")
    if plan.get("config_sha256") != evaluation.sha256_file(config_path.resolve()):
        raise RuntimeError("protected recovery config changed after freeze")
    current_sources = {
        "recovery_runner": evaluation.sha256_file(Path(__file__).resolve()),
        "protected_runner": evaluation.sha256_file(Path(protected.__file__)),
        "dataset_runner": evaluation.sha256_file(Path(protected.smoke.base.__file__)),
        "newton_runner": evaluation.sha256_file(SCRIPT_DIR / "run_newton_cylinder_diagnostic.py"),
    }
    if plan.get("source_sha256") != current_sources:
        raise RuntimeError("protected recovery sources changed after freeze")
    return plan


def newton_command(runtime: Mapping[str, Any], contract: Mapping[str, Any], runtime_plan: Mapping[str, Any], episode: Mapping[str, Any], output: Path) -> list[str]:
    preparation = protected.smoke.base.prepare_prior(
        runtime, contract, runtime_plan, int(episode["initial_surface_seed"])
    )
    newton = contract["newton"]
    prior = runtime["newton_prior"]
    return [
        str(Path(runtime["execution"]["newton_python"]).resolve()),
        str(SCRIPT_DIR / "run_newton_cylinder_diagnostic.py"),
        "--config", str(fresh.repo_path(newton["base_config"])),
        "--prepared-dir", str(preparation),
        "--candidate-preparation",
        "--chrono-episode", str(protected.smoke.base.chrono_episode(runtime, episode["episode_id"])),
        "--output-dir", str(output),
        "--device", str(runtime["execution"]["device"]),
        "--dt-s", str(newton["selected_dt_s"]),
        "--pre-settle-duration-s", str(newton["pre_settle_duration_s"]),
        "--pre-settle-required-duration-s", str(newton["pre_settle_required_duration_s"]),
        "--particle-speed-threshold-mps", str(newton["particle_speed_threshold_mps"]),
        "--observation-time-mode", str(prior["observation_time_mode"]),
        "--loaded-duration-s", str(prior["loaded_duration_s"]),
        "--residual-duration-s", str(prior["post_unload_duration_s"]),
        "--proxy-iterations", str(newton["proxy_iterations"]),
        "--rigid-substeps", str(newton["rigid_substeps"]),
        "--cylinder-friction-coefficient", str(newton["cylinder_friction_coefficient"]),
        "--cylinder-collider-mode", str(newton["collider_mode"]),
        "--cylinder-collider-segments", str(newton["collider_segments"]),
        "--cylinder-collision-guard-m", str(newton["collision_guard_m"]),
        "--cylinder-collision-bottom-inset-m", "0",
        "--cylinder-projection-threshold-m", str(newton["projection_threshold_m"]),
    ]


def archive_failed_attempt(config: Mapping[str, Any], runtime: Mapping[str, Any], plan: Mapping[str, Any]) -> Path:
    failed_id = str(config["failed_episode_id"])
    root = episode_dir(runtime, failed_id)
    archive = root / str(config["execution"]["failed_attempt_archive"])
    if archive.exists():
        raise RuntimeError("failed-attempt archive already exists; additional retry is prohibited")
    archive.mkdir(parents=True)
    response = response_dir(runtime, failed_id)
    log = root / "logs" / "newton_response.log"
    current = file_identities(failed_files(runtime, failed_id), root)
    if current != plan["failed_attempt_sha256"]:
        raise RuntimeError("failed attempt changed after recovery-plan freeze")
    shutil.move(str(response), str(archive / "newton_response"))
    shutil.move(str(log), str(archive / "newton_response.log"))
    return archive


def run_recovery(config_path: Path, config: Mapping[str, Any]) -> None:
    plan = load_plan(config_path, config)
    _eval_config, runtime, runtime_plan, contract, episodes = context(config)
    failed_id = str(config["failed_episode_id"])
    companion_id = str(config["companion_episode_id"])
    current_completed = completed_manifest_identities(runtime, list(plan["completed_official_manifest_sha256"]))
    if current_completed != plan["completed_official_manifest_sha256"]:
        raise RuntimeError("a completed official manifest changed after recovery-plan freeze")
    archive_failed_attempt(config, runtime, plan)
    official_output = response_dir(runtime, failed_id)
    companion_root = output_root(config) / "companion" / companion_id
    if official_output.exists() or companion_root.exists():
        raise RuntimeError("recovery output exists before the one permitted attempt")
    commands = [
        (
            newton_command(runtime, contract, runtime_plan, episodes[failed_id], official_output),
            episode_dir(runtime, failed_id) / "logs" / "newton_response.log",
        ),
        (
            newton_command(runtime, contract, runtime_plan, episodes[companion_id], companion_root),
            output_root(config) / "logs" / "companion_newton_response.log",
        ),
    ]
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(fresh.run_logged, command, log, REPO_ROOT)
            for command, log in commands
        ]
        for future in futures:
            future.result()


def manifest_checks(path: Path) -> dict[str, bool]:
    if not path.is_file():
        return {"exists": False, "finite": False, "guide": False, "preparation": False}
    value = json.loads(path.read_text(encoding="utf-8"))
    return {
        "exists": True,
        "finite": value.get("finite") is True,
        "guide": value.get("cylinder", {}).get("guide_constraint_passed") is True,
        "preparation": value.get("preparation", {}).get("convergence_passed") is True,
    }


def analyze(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    plan = load_plan(config_path, config)
    _eval_config, runtime, runtime_plan, _contract, _episodes = context(config)
    failed_id = str(config["failed_episode_id"])
    companion_id = str(config["companion_episode_id"])
    archive = episode_dir(runtime, failed_id) / str(config["execution"]["failed_attempt_archive"])
    official_manifest = response_dir(runtime, failed_id) / "newton_cylinder_manifest.json"
    companion_manifest = output_root(config) / "companion" / companion_id / "newton_cylinder_manifest.json"
    completed_unchanged = completed_manifest_identities(runtime, list(plan["completed_official_manifest_sha256"])) == plan["completed_official_manifest_sha256"]
    archived = file_identities(
        sorted(path for path in archive.rglob("*") if path.is_file()), archive
    ) if archive.is_dir() else {}
    # The archived response retains its directory name; only the log moves out
    # of the episode's logs directory into the attempt archive.
    normalized_archived = dict(archived)
    expected_archive = {
        ("newton_response.log" if name == "logs/newton_response.log" else name): sha
        for name, sha in plan["failed_attempt_sha256"].items()
    }
    checks = {
        "failed_attempt_preserved": normalized_archived == expected_archive,
        "completed_official_manifests_unchanged": completed_unchanged,
        "official_retry": all(manifest_checks(official_manifest).values()),
        "companion_retry": all(manifest_checks(companion_manifest).values()),
        "official_manifest_count": len(
            completed_manifest_identities(
                runtime,
                [str(item["episode_id"]) for item in runtime_plan["episodes"]],
            )
        ) == 30,
        "companion_excluded_from_evaluation_membership": companion_manifest.parent.parent.parent != protected.smoke.base.output_root(runtime),
    }
    passed = all(checks.values())
    result = {
        "schema_version": 1,
        "recovery_id": EXPECTED_ID,
        "status": "passed" if passed else "failed",
        "recovery_plan_sha256": evaluation.sha256_file(plan_path(config)),
        "checks": checks,
        "official_retry_manifest_sha256": evaluation.sha256_file(official_manifest) if official_manifest.is_file() else None,
        "companion_manifest_sha256": evaluation.sha256_file(companion_manifest) if companion_manifest.is_file() else None,
        "prediction_permitted": False,
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
        run_recovery(config_path, config)
        result = {"status": "runtime_complete", "prediction_permitted": False}
    elif args.stage == "analyze":
        result = analyze(config_path, config)
    else:
        if not plan_path(config).is_file():
            build_plan(config_path, config)
        run_recovery(config_path, config)
        result = analyze(config_path, config)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

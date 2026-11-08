#!/usr/bin/env python3
"""Re-evaluate the failed successor bulk guide check without rerunning simulators."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Mapping

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_fresh_phase0_repeatability as fresh
import run_phase1_one_action_successor_bulk as bulk


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = (
    REPO_ROOT / "configs" / "phase1_one_action_successor_bulk_recovery_v2.json"
)
GUIDE_COMPONENTS = (
    "horizontal_position_error_m",
    "horizontal_speed_mps",
    "angular_speed_radps",
    "orientation_quaternion_error",
)
EXPECTED_GUIDE_TOLERANCES = {
    "horizontal_position_error_m": 1.0e-6,
    "horizontal_speed_mps": 5.0e-6,
    "angular_speed_radps": 1.0e-6,
    "orientation_quaternion_error": 1.0e-6,
}
EXPECTED_LEGACY_CHECKS = {
    "episode_count": True,
    "train_count": True,
    "validation_count": True,
    "test_and_sensitivity_targets_unopened": True,
    "all_complete": True,
    "all_admitted": False,
    "surface_coverage": True,
    "reused_smoke_artifacts_unchanged": True,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--stage", choices=("plan", "analyze"), default="plan")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_config(path: Path) -> dict[str, Any]:
    config = load_json(path.resolve())
    if config.get("schema_version") != 1:
        raise ValueError("successor bulk recovery schema_version must be 1")
    if config.get("recovery_id") != "phase1_one_action_successor_bulk_recovery_v2":
        raise ValueError("unexpected successor bulk recovery identity")
    if config.get("status") != "prepared_after_v1_bulk_failure_before_training":
        raise ValueError("successor bulk recovery status changed")
    tolerances = {
        name: float(value) for name, value in config["guide_contract"].items()
    }
    if tolerances != EXPECTED_GUIDE_TOLERANCES:
        raise ValueError("component-specific guide contract changed")
    policy = config["policy"]
    if not all(policy.values()):
        raise ValueError("successor recovery fail-closed policy changed")
    if config["expected_counts"] != {
        "total": 64,
        "train": 48,
        "validation": 16,
        "test": 0,
        "protected_sensitivity": 0,
    }:
        raise ValueError("successor recovery counts changed")
    return config


def plan_path(config: Mapping[str, Any]) -> Path:
    return fresh.repo_path(config["output"]["plan"])


def summary_path(config: Mapping[str, Any]) -> Path:
    return fresh.repo_path(config["output"]["summary"])


def load_legacy_inputs(
    config: Mapping[str, Any],
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    bulk_config_path = fresh.repo_path(config["legacy_bulk_config"])
    bulk_config = bulk.load_config(bulk_config_path)
    legacy_plan_path = fresh.repo_path(config["legacy_bulk_plan"])
    legacy_summary_path = fresh.repo_path(config["legacy_bulk_summary"])
    expected = (
        (legacy_plan_path, config["legacy_bulk_plan_sha256"], "bulk plan"),
        (legacy_summary_path, config["legacy_bulk_summary_sha256"], "bulk summary"),
    )
    for path, digest, label in expected:
        if not path.is_file() or fresh.sha256_file(path) != digest:
            raise RuntimeError(f"frozen legacy {label} changed")
    legacy_plan = load_json(legacy_plan_path)
    legacy_summary = load_json(legacy_summary_path)
    if legacy_summary.get("status") != config["expected_legacy_status"]:
        raise RuntimeError("legacy successor bulk status changed")
    if legacy_summary.get("counts") != config["expected_counts"]:
        raise RuntimeError("legacy successor bulk counts changed")
    if legacy_summary.get("checks") != EXPECTED_LEGACY_CHECKS:
        raise RuntimeError("legacy successor bulk failure shape changed")
    if legacy_summary.get("training_plan_freeze_permitted") is not False:
        raise RuntimeError("legacy successor bulk unexpectedly permits training")
    if legacy_summary.get("test_or_protected_sensitivity_permitted") is not False:
        raise RuntimeError("legacy successor bulk protected permission changed")
    _dataset_path, dataset_plan = bulk.load_dataset_plan(bulk_config)
    bulk.assert_protected_targets_absent(bulk_config, dataset_plan)
    return bulk_config_path, bulk_config, {
        "plan": legacy_plan,
        "summary": legacy_summary,
    }


def legacy_failure_ids(summary: Mapping[str, Any]) -> list[str]:
    return sorted(
        episode_id
        for episode_id, episode in summary["episodes"].items()
        if episode.get("admitted") is not True
    )


def failed_checks(episode: Mapping[str, Any]) -> list[str]:
    failures = [
        name
        for name, passed in episode["numerical_checks"].items()
        if passed is not True
    ]
    failures.extend(
        f"interaction:{name}"
        for name, passed in episode["interaction_artifact_checks"].items()
        if passed is not True
    )
    failures.extend(
        f"tensor:{name}"
        for name, passed in episode["tensor_manifest"]["checks"].items()
        if passed is not True
    )
    return failures


def require_expected_legacy_failure(
    config: Mapping[str, Any], summary: Mapping[str, Any]
) -> None:
    expected_ids = sorted(config["expected_legacy_failure_ids"])
    if legacy_failure_ids(summary) != expected_ids:
        raise RuntimeError("legacy successor bulk failure membership changed")
    expected_checks = sorted(config["expected_legacy_failed_episode_checks"])
    for episode_id, episode in summary["episodes"].items():
        failures = sorted(failed_checks(episode))
        if episode_id in expected_ids:
            if failures != expected_checks:
                raise RuntimeError(
                    f"legacy failure checks changed for {episode_id}: {failures}"
                )
        elif failures:
            raise RuntimeError(
                f"unexpected failed legacy checks for {episode_id}: {failures}"
            )


def artifact_paths(
    bulk_config: Mapping[str, Any], legacy_summary: Mapping[str, Any]
) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for episode_id in sorted(legacy_summary["episodes"]):
        local = bulk.output_root(bulk_config) / "episodes" / episode_id
        response = local / "newton_response"
        chrono = bulk.chrono_root(bulk_config) / episode_id
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
                raise RuntimeError(f"missing recovery-bound artifact: {path}")
            paths[f"{episode_id}:{label}"] = path
    return paths


def source_paths(config: Mapping[str, Any]) -> dict[str, Path]:
    paths = {
        name: fresh.repo_path(value)
        for name, value in config["source_files"].items()
    }
    precedent = config["guide_contract_precedent"]
    paths["guide_precedent_config"] = fresh.repo_path(
        precedent["prospective_config"]
    )
    paths["guide_qualification_summary"] = fresh.repo_path(
        precedent["full_duration_qualification"]
    )
    for name, path in paths.items():
        if not path.is_file():
            raise RuntimeError(f"missing recovery source {name}: {path}")
    return paths


def require_guide_precedent(config: Mapping[str, Any]) -> None:
    precedent = config["guide_contract_precedent"]
    for key, hash_key in (
        ("prospective_config", "prospective_config_sha256"),
        ("full_duration_qualification", "full_duration_qualification_sha256"),
    ):
        path = fresh.repo_path(precedent[key])
        if fresh.sha256_file(path) != precedent[hash_key]:
            raise RuntimeError(f"guide precedent changed: {key}")
    qualification = load_json(
        fresh.repo_path(precedent["full_duration_qualification"])
    )
    if qualification.get("status") != precedent["required_qualification_status"]:
        raise RuntimeError("full-duration guide qualification did not pass")
    if precedent.get("selected_before_successor_bulk_failure_was_observed") is not True:
        raise RuntimeError("guide contract is not independently prospective")


def build_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    _bulk_config_path, bulk_config, legacy = load_legacy_inputs(config)
    legacy_summary = legacy["summary"]
    require_expected_legacy_failure(config, legacy_summary)
    require_guide_precedent(config)
    artifacts = artifact_paths(bulk_config, legacy_summary)
    sources = source_paths(config)
    return {
        "schema_version": 1,
        "recovery_id": config["recovery_id"],
        "status": "frozen_before_component_guide_reanalysis",
        "config_sha256": fresh.sha256_file(config_path.resolve()),
        "legacy_bulk_plan_sha256": config["legacy_bulk_plan_sha256"],
        "legacy_bulk_summary_sha256": config["legacy_bulk_summary_sha256"],
        "expected_legacy_failure_ids": list(
            config["expected_legacy_failure_ids"]
        ),
        "guide_contract": dict(config["guide_contract"]),
        "guide_contract_precedent": dict(config["guide_contract_precedent"]),
        "artifact_sha256": {
            name: fresh.sha256_file(path) for name, path in artifacts.items()
        },
        "source_sha256": {
            name: fresh.sha256_file(path) for name, path in sources.items()
        },
        "test_lock_sha256": legacy["plan"]["test_lock_sha256"],
        "sensitivity_lock_sha256": legacy["plan"]["sensitivity_lock_sha256"],
        "full_train_validation_manifest_sha256": legacy["plan"][
            "full_train_validation_manifest_sha256"
        ],
        "simulator_rerun_permitted": False,
        "artifact_replacement_permitted": False,
        "protected_targets_opened": False,
    }


def write_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    plan = build_plan(config_path, config)
    path = plan_path(config)
    if path.exists():
        existing = load_json(path)
        if existing != plan:
            raise RuntimeError("refusing changed successor bulk recovery plan")
        return existing
    fresh.write_json(path, plan)
    return plan


def load_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    path = plan_path(config)
    if not path.is_file():
        raise RuntimeError("freeze the successor bulk recovery plan first")
    frozen = load_json(path)
    if frozen != build_plan(config_path, config):
        raise RuntimeError("successor bulk recovery identity or artifacts changed")
    return frozen


def evaluate_guide(
    manifest: Mapping[str, Any], tolerances: Mapping[str, Any]
) -> dict[str, Any]:
    observed = manifest["cylinder"]["guide_constraint_error"]
    component_checks = {
        name: abs(float(observed[name])) <= float(tolerances[name])
        for name in GUIDE_COMPONENTS
    }
    return {
        "contract": "component_specific_preprotected_reanalysis_v2",
        "observed": {name: float(observed[name]) for name in GUIDE_COMPONENTS},
        "tolerances": {
            name: float(tolerances[name]) for name in GUIDE_COMPONENTS
        },
        "component_checks": component_checks,
        "passed": all(component_checks.values()),
        "legacy_manifest_passed": bool(
            manifest["cylinder"]["guide_constraint_passed"]
        ),
    }


def recover_episode(
    bulk_config: Mapping[str, Any],
    episode: Mapping[str, Any],
    tolerances: Mapping[str, Any],
) -> dict[str, Any]:
    episode_id = str(episode["episode_id"])
    manifest_path = (
        bulk.output_root(bulk_config)
        / "episodes"
        / episode_id
        / "newton_response"
        / "newton_cylinder_manifest.json"
    )
    manifest = load_json(manifest_path)
    guide = evaluate_guide(manifest, tolerances)
    result = copy.deepcopy(dict(episode))
    result["legacy_admitted"] = bool(episode["admitted"])
    result["legacy_numerical_checks"] = dict(episode["numerical_checks"])
    result["guide_contract"] = guide
    result["numerical_checks"]["guide"] = bool(guide["passed"])
    result["admitted"] = bool(
        all(result["numerical_checks"].values())
        and all(result["interaction_artifact_checks"].values())
        and all(result["tensor_manifest"]["checks"].values())
    )
    return result


def summarize(
    config_path: Path, config: Mapping[str, Any], plan: Mapping[str, Any]
) -> dict[str, Any]:
    _bulk_config_path, bulk_config, legacy = load_legacy_inputs(config)
    legacy_summary = legacy["summary"]
    require_expected_legacy_failure(config, legacy_summary)
    episodes = {
        episode_id: recover_episode(
            bulk_config, episode, config["guide_contract"]
        )
        for episode_id, episode in legacy_summary["episodes"].items()
    }
    current_artifacts = {
        name: fresh.sha256_file(path)
        for name, path in artifact_paths(bulk_config, legacy_summary).items()
    }
    checks = {
        "legacy_failure_shape_preserved": True,
        "legacy_summary_unchanged": fresh.sha256_file(
            fresh.repo_path(config["legacy_bulk_summary"])
        )
        == config["legacy_bulk_summary_sha256"],
        "all_artifacts_match_frozen_recovery_plan": current_artifacts
        == plan["artifact_sha256"],
        "all_complete": all(item["complete"] for item in episodes.values()),
        "all_component_guide_checks_pass": all(
            item["guide_contract"]["passed"] for item in episodes.values()
        ),
        "all_admitted": all(item["admitted"] for item in episodes.values()),
        "test_and_sensitivity_targets_unopened": True,
        "simulator_rerun_performed": False,
        "artifact_replacement_performed": False,
    }
    passed = all(
        value is True
        for name, value in checks.items()
        if name not in {
            "simulator_rerun_performed",
            "artifact_replacement_performed",
        }
    ) and not checks["simulator_rerun_performed"] and not checks[
        "artifact_replacement_performed"
    ]
    summary = {
        "schema_version": 1,
        "recovery_id": config["recovery_id"],
        "status": "passed" if passed else "failed_or_incomplete",
        "training_plan_freeze_permitted": passed,
        "test_or_protected_sensitivity_permitted": False,
        "counts": dict(config["expected_counts"]),
        "checks": checks,
        "identity": {
            "recovery_plan_sha256": fresh.sha256_file(plan_path(config)),
            "legacy_bulk_plan_sha256": config["legacy_bulk_plan_sha256"],
            "legacy_bulk_summary_sha256": config[
                "legacy_bulk_summary_sha256"
            ],
            "full_train_validation_manifest_sha256": plan[
                "full_train_validation_manifest_sha256"
            ],
            "test_lock_sha256": plan["test_lock_sha256"],
            "sensitivity_lock_sha256": plan["sensitivity_lock_sha256"],
        },
        "reanalysis": {
            "guide_contract": dict(config["guide_contract"]),
            "legacy_failure_ids": legacy_failure_ids(legacy_summary),
            "recovered_ids": sorted(
                episode_id
                for episode_id, item in episodes.items()
                if not item["legacy_admitted"] and item["admitted"]
            ),
            "simulator_outputs_reused_unchanged": True,
            "protected_targets_opened": False,
        },
        "episodes": episodes,
    }
    path = summary_path(config)
    if path.exists():
        existing = load_json(path)
        if existing != summary:
            raise RuntimeError("refusing to replace a different recovery summary")
        return existing
    fresh.write_json(path, summary)
    return summary


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = load_config(config_path)
    if args.stage == "plan":
        plan = write_plan(config_path, config)
        print(
            json.dumps(
                {
                    "plan": str(plan_path(config)),
                    "sha256": fresh.sha256_file(plan_path(config)),
                    "legacy_failure_ids": plan["expected_legacy_failure_ids"],
                    "simulator_rerun_permitted": False,
                    "protected_targets_opened": False,
                },
                indent=2,
            )
        )
        return
    plan = load_plan(config_path, config)
    summary = summarize(config_path, config, plan)
    print(
        json.dumps(
            {
                "summary": str(summary_path(config)),
                "sha256": fresh.sha256_file(summary_path(config)),
                "status": summary["status"],
                "training_plan_freeze_permitted": summary[
                    "training_plan_freeze_permitted"
                ],
                "recovered_ids": summary["reanalysis"]["recovered_ids"],
                "protected_targets_opened": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Prospectively qualify the direct-v4 protected report and its provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = (
    REPO_ROOT
    / "configs"
    / "phase1_one_action_successor_direct_v4_final_qualification_v1.json"
)
EXPECTED_ID = "phase1_one_action_successor_direct_v4_final_qualification_v1"
TEST_PATH = (
    REPO_ROOT
    / "tests"
    / "test_qualify_phase1_one_action_successor_direct_v4_final.py"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--stage", choices=("plan", "qualify"), default="plan")
    return parser.parse_args()


def repo_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (REPO_ROOT / path).resolve()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def load_config(path: Path) -> dict[str, Any]:
    config = load_json(path.resolve())
    if config.get("schema_version") != 1 or config.get("qualification_id") != EXPECTED_ID:
        raise ValueError("unexpected direct-v4 final qualification identity")
    if config.get("status") != (
        "prospective_before_protected_admission_prediction_or_final_report"
    ):
        raise ValueError("direct-v4 final qualification was not declared prospectively")
    expected_inputs = {
        "direct_v4_config",
        "confirmation_plan",
        "validation_summary",
        "protected_execution_plan",
        "protected_open_marker",
        "reporting_plan",
        "revision_rebind_plan",
    }
    if set(config.get("frozen_inputs", {})) != expected_inputs:
        raise ValueError("direct-v4 final qualification input set changed")
    semantics = config.get("semantics", {})
    for name in (
        "accept_coherent_pass_or_failure",
        "phase1_goal_achieved_must_equal_report",
        "require_all_25_precommitted_checks_for_success",
        "require_30_of_30_protected_admission",
        "require_complete_prediction_artifact_binding",
        "preserve_revision_only_execution_qualification",
    ):
        if semantics.get(name) is not True:
            raise ValueError(f"required final qualification semantic changed: {name}")
    for name in (
        "permit_target_inspection_before_qualification_plan_freeze",
        "permit_model_threshold_or_claim_boundary_change",
    ):
        if semantics.get(name) is not False:
            raise ValueError(f"forbidden final qualification semantic changed: {name}")
    if int(config["requirements"]["hypothesis_check_count"]) != 25:
        raise ValueError("direct-v4 final qualification requires exactly 25 checks")
    return config


def execution_path(config: Mapping[str, Any], name: str) -> Path:
    return repo_path(config["execution"][name])


def source_identities() -> dict[str, str]:
    return {
        "qualifier": sha256_file(Path(__file__).resolve()),
        "qualifier_tests": sha256_file(TEST_PATH),
    }


def frozen_input_identities(config: Mapping[str, Any]) -> dict[str, str]:
    identities: dict[str, str] = {}
    for name, expected in sorted(config["frozen_inputs"].items()):
        path = repo_path(expected["path"])
        if not path.is_file() or sha256_file(path) != expected["sha256"]:
            raise RuntimeError(f"frozen final qualification input changed: {name}")
        identities[name] = expected["sha256"]
    return identities


def plan_payload(
    config_path: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    for name in (
        "protected_dataset_summary",
        "prediction_results",
        "final_report",
        "qualification_output",
    ):
        if execution_path(config, name).exists():
            raise RuntimeError(
                f"direct-v4 qualification plan must precede output: {name}"
            )
    return {
        "schema_version": 1,
        "qualification_id": EXPECTED_ID,
        "status": (
            "frozen_before_protected_admission_prediction_or_final_report"
        ),
        "config_sha256": sha256_file(config_path.resolve()),
        "source_sha256": source_identities(),
        "frozen_input_sha256": frozen_input_identities(config),
        "required_candidate": dict(config["required_candidate"]),
        "requirements": dict(config["requirements"]),
        "semantics": dict(config["semantics"]),
        "target_values_inspected_before_freeze": False,
        "outcome_known_before_freeze": False,
    }


def write_plan(
    config_path: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    current = plan_payload(config_path, config)
    path = execution_path(config, "qualification_plan")
    if path.is_file():
        existing = load_json(path)
        if existing != current:
            raise RuntimeError("refusing changed direct-v4 final qualification plan")
        return existing
    write_json(path, current)
    return current


def load_plan(
    config_path: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    path = execution_path(config, "qualification_plan")
    if not path.is_file():
        raise RuntimeError("freeze the direct-v4 final qualification plan first")
    plan = load_json(path)
    expected = {
        "schema_version": 1,
        "qualification_id": EXPECTED_ID,
        "status": "frozen_before_protected_admission_prediction_or_final_report",
        "config_sha256": sha256_file(config_path.resolve()),
        "source_sha256": source_identities(),
        "frozen_input_sha256": frozen_input_identities(config),
        "required_candidate": dict(config["required_candidate"]),
        "requirements": dict(config["requirements"]),
        "semantics": dict(config["semantics"]),
        "target_values_inspected_before_freeze": False,
        "outcome_known_before_freeze": False,
    }
    if plan != expected:
        raise RuntimeError("direct-v4 final qualification plan identity changed")
    return plan


def artifact_payloads(
    config: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    paths = {
        "protected_dataset_summary": execution_path(
            config, "protected_dataset_summary"
        ),
        "prediction_results": execution_path(config, "prediction_results"),
        "final_report": execution_path(config, "final_report"),
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise RuntimeError(f"direct-v4 final artifacts are absent: {missing}")
    return (
        {name: load_json(path) for name, path in paths.items()},
        {name: sha256_file(path) for name, path in paths.items()},
    )


def qualification_checks(
    config: Mapping[str, Any],
    artifacts: Mapping[str, Mapping[str, Any]],
    artifact_sha256: Mapping[str, str],
) -> dict[str, bool]:
    requirements = config["requirements"]
    report = artifacts["final_report"]
    prediction = artifacts["prediction_results"]
    protected = artifacts["protected_dataset_summary"]
    recovery = load_json(
        repo_path(config["frozen_inputs"]["revision_rebind_plan"]["path"])
    )
    hypothesis = report.get("hypothesis_checks", {})
    failed = sorted(name for name, value in hypothesis.items() if value is not True)
    report_passed = report.get("status") == requirements["passing_status"]
    coherent_outcome = (
        report_passed
        and report.get("phase1_goal_achieved") is True
        and report.get("supported_claim_permitted") is True
        and report.get("claim_route") == requirements["passing_claim_route"]
        and failed == []
    ) or (
        report.get("status") == requirements["failing_status"]
        and report.get("phase1_goal_achieved") is False
        and report.get("supported_claim_permitted") is False
        and report.get("claim_route") == requirements["failing_claim_route"]
        and bool(failed)
    )
    counts = protected.get("counts", {})
    dataset_checks = protected.get("checks", {})
    prediction_episodes = prediction.get("episodes", [])
    prediction_artifacts = prediction.get("prediction_artifacts", {})
    complete_prediction_artifacts = (
        len(prediction_artifacts) == int(requirements["protected_episode_count"])
        and all(
            set(identity) == {"summary_sha256", "archive_sha256"}
            and all(
                isinstance(value, str) and len(value) == 64
                for value in identity.values()
            )
            for identity in prediction_artifacts.values()
        )
    )
    return {
        "qualification_plan_preceded_outcome": True,
        "candidate_unchanged": report.get("candidate")
        == config["required_candidate"],
        "claim_boundary_unchanged": report.get("claim_boundary")
        == requirements["claim_boundary"],
        "exact_25_hypothesis_checks": len(hypothesis)
        == int(requirements["hypothesis_check_count"]),
        "failed_check_list_exact": report.get("failed_hypothesis_checks") == failed,
        "report_outcome_coherent": coherent_outcome,
        "protected_dataset_passed": protected.get("status") == "passed"
        and protected.get("prediction_permitted") is True
        and protected.get("protected_execution_plan_sha256")
        == config["frozen_inputs"]["protected_execution_plan"]["sha256"]
        and protected.get("protected_open_sha256")
        == config["frozen_inputs"]["protected_open_marker"]["sha256"]
        and counts
        == {
            "total": int(requirements["protected_episode_count"]),
            "test": int(requirements["test_episode_count"]),
            "protected_sensitivity": int(
                requirements["protected_sensitivity_episode_count"]
            ),
        }
        and bool(dataset_checks)
        and all(value is True for value in dataset_checks.values()),
        "prediction_complete": prediction.get("status")
        == "protected_predictions_complete"
        and prediction.get("candidate") == config["required_candidate"]
        and len(prediction_episodes) == int(requirements["test_episode_count"])
        and complete_prediction_artifacts,
        "report_artifact_links": report.get("prediction_results_sha256")
        == artifact_sha256["prediction_results"]
        and report.get("protected_dataset_summary_sha256")
        == artifact_sha256["protected_dataset_summary"]
        and report.get("reporting_plan_sha256")
        == config["frozen_inputs"]["reporting_plan"]["sha256"]
        and report.get("protected_execution_plan_sha256")
        == config["frozen_inputs"]["protected_execution_plan"]["sha256"]
        and report.get("prediction_artifact_sha256") == prediction_artifacts
        and report.get("dataset_artifact_sha256")
        == protected.get("artifact_sha256"),
        "prediction_artifact_links": prediction.get("reporting_plan_sha256")
        == config["frozen_inputs"]["reporting_plan"]["sha256"]
        and prediction.get("protected_dataset_summary_sha256")
        == artifact_sha256["protected_dataset_summary"]
        and prediction.get("protected_execution_plan_sha256")
        == config["frozen_inputs"]["protected_execution_plan"]["sha256"]
        and prediction.get("dataset_artifact_sha256")
        == protected.get("artifact_sha256"),
        "revision_only_qualification_preserved": recovery.get(
            "changed_execution_identity_keys"
        )
        == ["repository_revisions"]
        and recovery.get("protected_episode_count")
        == int(requirements["protected_episode_count"])
        and recovery.get("downstream_artifacts_absent_at_freeze") is True
        and recovery.get("prediction_permitted") is False,
    }


def qualify(
    config_path: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    plan = load_plan(config_path, config)
    artifacts, identities = artifact_payloads(config)
    checks = qualification_checks(config, artifacts, identities)
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise RuntimeError(f"direct-v4 final qualification failed: {failed}")
    report = artifacts["final_report"]
    achieved = report["phase1_goal_achieved"] is True
    result = {
        "schema_version": 1,
        "qualification_id": EXPECTED_ID,
        "status": "qualified_passed_result" if achieved else "qualified_failed_result",
        "qualification_plan_sha256": sha256_file(
            execution_path(config, "qualification_plan")
        ),
        "config_sha256": plan["config_sha256"],
        "artifact_sha256": dict(identities),
        "checks": checks,
        "scientific_result": {
            "status": report["status"],
            "phase1_goal_achieved": achieved,
            "supported_claim_permitted": report["supported_claim_permitted"],
            "claim_route": report["claim_route"],
            "failed_hypothesis_checks": report["failed_hypothesis_checks"],
        },
        "claim_boundary": report["claim_boundary"],
        "next_gate": (
            "phase1_completion_audit"
            if achieved
            else "freeze_a_new_prospective_branch_before_using_protected_evidence"
        ),
    }
    destination = execution_path(config, "qualification_output")
    if destination.is_file():
        existing = load_json(destination)
        if existing != result:
            raise RuntimeError("refusing changed direct-v4 final qualification")
        return existing
    write_json(destination, result)
    return result


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = load_config(config_path)
    if args.stage == "plan":
        result = write_plan(config_path, config)
        output = {
            "plan": str(execution_path(config, "qualification_plan")),
            "sha256": sha256_file(execution_path(config, "qualification_plan")),
            "status": result["status"],
            "outcome_known_before_freeze": False,
        }
    else:
        result = qualify(config_path, config)
        output = {
            "status": result["status"],
            "phase1_goal_achieved": result["scientific_result"][
                "phase1_goal_achieved"
            ],
            "claim_route": result["scientific_result"]["claim_route"],
        }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run frozen direct-v4 prediction/reporting through the qualified revision rebind."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import evaluate_phase1_one_action_successor_direct_v4 as reporter
import recover_phase1_one_action_successor_direct_v4_revision as recovery


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = (
    REPO_ROOT
    / "configs"
    / "phase1_one_action_successor_direct_v4_reporting_rebind_v1.json"
)
EXPECTED_ID = "phase1_one_action_successor_direct_v4_reporting_rebind_v1"
TEST_PATH = (
    REPO_ROOT
    / "tests"
    / "test_run_phase1_one_action_successor_direct_v4_reporting_rebind.py"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--stage", choices=("plan", "predict", "report"), default="plan")
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
    if config.get("schema_version") != 1 or config.get("continuation_id") != EXPECTED_ID:
        raise ValueError("unexpected direct-v4 reporting-rebind identity")
    if config.get("status") != (
        "prospective_after_protected_admission_before_prediction_or_report"
    ):
        raise ValueError("direct-v4 reporting rebind was not declared prospectively")
    if config.get("execution", {}).get("allowed_stages") != ["predict", "report"]:
        raise ValueError("direct-v4 reporting rebind permits only predict/report")
    semantics = config.get("semantics", {})
    for name in (
        "reuse_frozen_revision_only_proof",
        "require_30_of_30_protected_admission",
        "require_prediction_permitted",
        "preserve_frozen_reporter_sources_thresholds_and_candidate",
        "preserve_final_qualification_plan",
    ):
        if semantics.get(name) is not True:
            raise ValueError(f"required reporting-rebind semantic changed: {name}")
    for name in (
        "permit_protected_runtime_or_tensor_change",
        "permit_model_threshold_or_claim_boundary_change",
        "permit_positive_claim_before_25_gate_report",
    ):
        if semantics.get(name) is not False:
            raise ValueError(f"forbidden reporting-rebind semantic changed: {name}")
    return config


def required_file(config: Mapping[str, Any], name: str) -> Path:
    identity = config[name]
    path = repo_path(identity["path"])
    if not path.is_file() or sha256_file(path) != identity["sha256"]:
        raise RuntimeError(f"required reporting-rebind artifact changed: {name}")
    return path


def output_root(config: Mapping[str, Any]) -> Path:
    return repo_path(config["execution"]["output_root"])


def plan_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "continuation_plan.json"


def source_identities() -> dict[str, str]:
    return {
        "reporting_rebind_runner": sha256_file(Path(__file__).resolve()),
        "reporting_rebind_tests": sha256_file(TEST_PATH),
        "frozen_reporter": sha256_file(Path(reporter.__file__).resolve()),
        "frozen_revision_recovery": sha256_file(Path(recovery.__file__).resolve()),
    }


def validated_context(
    config: Mapping[str, Any],
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    recovery_config_path = required_file(config, "recovery_config")
    recovery_config = recovery.load_config(recovery_config_path)
    recovery.load_plan(recovery_config_path, recovery_config)
    direct_path = recovery.direct_config_path(recovery_config)
    direct_config = recovery.planner.load_config(direct_path)
    frozen = recovery.load_json(recovery.protected_plan_path(recovery_config))
    current = recovery.protected.build_execution_plan(
        direct_path, direct_config, False
    )
    recovery.validate_revision_only_difference(frozen, current, recovery_config)
    summary = load_json(required_file(config, "protected_dataset_summary"))
    if (
        summary.get("status") != "passed"
        or summary.get("prediction_permitted") is not True
        or summary.get("counts")
        != {"total": 30, "test": 24, "protected_sensitivity": 6}
        or not all(value is True for value in summary.get("checks", {}).values())
    ):
        raise RuntimeError("passing 30/30 protected admission is required")
    qualification_plan = load_json(required_file(config, "final_qualification_plan"))
    if (
        qualification_plan.get("status")
        != "frozen_before_protected_admission_prediction_or_final_report"
        or qualification_plan.get("outcome_known_before_freeze") is not False
    ):
        raise RuntimeError("prospective final qualification plan changed")
    required_file(config, "recovery_plan")
    required_file(config, "reporting_plan")
    return direct_path, direct_config, recovery_config


def plan_payload(
    config_path: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    direct_path, _direct_config, recovery_config = validated_context(config)
    for path in (
        reporter.prediction_path(reporter.planner.load_config(direct_path)),
        reporter.report_path(reporter.planner.load_config(direct_path)),
    ):
        if path.exists():
            raise RuntimeError(
                "direct-v4 reporting continuation must freeze before prediction/report"
            )
    return {
        "schema_version": 1,
        "continuation_id": EXPECTED_ID,
        "status": "frozen_after_admission_before_prediction_or_report",
        "config_sha256": sha256_file(config_path.resolve()),
        "source_sha256": source_identities(),
        "required_artifact_sha256": {
            name: config[name]["sha256"]
            for name in (
                "recovery_config",
                "recovery_plan",
                "reporting_plan",
                "protected_dataset_summary",
                "final_qualification_plan",
            )
        },
        "direct_v4_config_sha256": sha256_file(direct_path),
        "repository_revisions": dict(recovery_config["repository_revisions"]),
        "changed_execution_identity_keys": ["repository_revisions"],
        "protected_admission_count": 30,
        "prediction_permitted": True,
        "allowed_stages": list(config["execution"]["allowed_stages"]),
        "semantics": dict(config["semantics"]),
        "prediction_or_report_existed_at_freeze": False,
    }


def write_plan(
    config_path: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    current = plan_payload(config_path, config)
    path = plan_path(config)
    if path.is_file():
        existing = load_json(path)
        if existing != current:
            raise RuntimeError("refusing changed direct-v4 reporting-rebind plan")
        return existing
    write_json(path, current)
    return current


def load_plan(
    config_path: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    path = plan_path(config)
    if not path.is_file():
        raise RuntimeError("freeze the direct-v4 reporting-rebind plan first")
    plan = load_json(path)
    direct_path, _direct_config, recovery_config = validated_context(config)
    expected = {
        "schema_version": 1,
        "continuation_id": EXPECTED_ID,
        "status": "frozen_after_admission_before_prediction_or_report",
        "config_sha256": sha256_file(config_path.resolve()),
        "source_sha256": source_identities(),
        "required_artifact_sha256": {
            name: config[name]["sha256"]
            for name in (
                "recovery_config",
                "recovery_plan",
                "reporting_plan",
                "protected_dataset_summary",
                "final_qualification_plan",
            )
        },
        "direct_v4_config_sha256": sha256_file(direct_path),
        "repository_revisions": dict(recovery_config["repository_revisions"]),
        "changed_execution_identity_keys": ["repository_revisions"],
        "protected_admission_count": 30,
        "prediction_permitted": True,
        "allowed_stages": list(config["execution"]["allowed_stages"]),
        "semantics": dict(config["semantics"]),
        "prediction_or_report_existed_at_freeze": False,
    }
    if plan != expected:
        raise RuntimeError("direct-v4 reporting-rebind plan identity changed")
    return plan


def run_stage(
    config_path: Path, config: Mapping[str, Any], stage: str
) -> None:
    if stage not in config["execution"]["allowed_stages"]:
        raise ValueError(f"reporting rebind does not permit stage: {stage}")
    load_plan(config_path, config)
    recovery_config_path = required_file(config, "recovery_config")
    recovery_config = recovery.load_config(recovery_config_path)
    direct_path = recovery.direct_config_path(recovery_config)
    original_loader = reporter.protected.load_execution_plan
    original_argv = list(sys.argv)
    reporter.protected.load_execution_plan = (
        lambda requested_path, requested_config: recovery.rebound_execution_plan(
            recovery_config_path,
            recovery_config,
            requested_path,
            requested_config,
        )
    )
    sys.argv = [
        str(Path(reporter.__file__).resolve()),
        "--config",
        str(direct_path),
        "--stage",
        stage,
    ]
    try:
        reporter.main()
    finally:
        sys.argv = original_argv
        reporter.protected.load_execution_plan = original_loader


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = load_config(config_path)
    if args.stage == "plan":
        result = write_plan(config_path, config)
        output = {
            "plan": str(plan_path(config)),
            "sha256": sha256_file(plan_path(config)),
            "status": result["status"],
            "prediction_or_report_existed_at_freeze": False,
        }
        print(json.dumps(output, indent=2, sort_keys=True))
        return
    run_stage(config_path, config, args.stage)


if __name__ == "__main__":
    main()

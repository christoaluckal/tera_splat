#!/usr/bin/env python3
"""Bind the frozen successor report to its execution and admission qualifications."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_final_qualification_v1.json"
EXPECTED_ID = "phase1_one_action_successor_final_qualification_v1"
MODELS = {"D0", "R0", "R1", "R2S", "R2E"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
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
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_config(path: Path) -> dict[str, Any]:
    config = load_json(path.resolve())
    if config.get("schema_version") != 1 or config.get("qualification_id") != EXPECTED_ID:
        raise ValueError("unexpected final qualification identity")
    required = config.get("required_artifacts", {})
    expected = {
        "final_report",
        "prediction_results",
        "protected_dataset_summary",
        "serial_recovery_summary",
        "admission_recovery_summary",
        "original_failed_protected_summary",
    }
    if set(required) != expected:
        raise ValueError("final qualification artifact set changed")
    return config


def require_artifacts(config: Mapping[str, Any]) -> dict[str, tuple[Path, dict[str, Any]]]:
    loaded: dict[str, tuple[Path, dict[str, Any]]] = {}
    for name, identity in config["required_artifacts"].items():
        path = repo_path(identity["path"])
        if not path.is_file() or sha256_file(path) != identity["sha256"]:
            raise RuntimeError(f"required artifact identity changed: {name}")
        loaded[name] = (path, load_json(path))
    return loaded


def qualify(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    artifacts = require_artifacts(config)
    report = artifacts["final_report"][1]
    prediction = artifacts["prediction_results"][1]
    protected = artifacts["protected_dataset_summary"][1]
    serial = artifacts["serial_recovery_summary"][1]
    admission = artifacts["admission_recovery_summary"][1]
    failed = artifacts["original_failed_protected_summary"][1]

    model_pass = report.get("model_pass", {})
    checks = {
        "report_failed_closed": report.get("status") == "failed",
        "no_supported_claim": report.get("supported_claim_permitted") is False
        and report.get("claim_route") == "no_positive_successor_claim",
        "all_declared_models_fail": set(model_pass) == MODELS
        and all(value is False for value in model_pass.values()),
        "no_passing_correction": report.get("passing_correction_models") == [],
        "no_newton_added_value": report.get("newton_added_value_models") == [],
        "claim_boundary_unchanged": report.get("claim_boundary")
        == config["required_claim_boundary"],
        "prediction_complete": prediction.get("status")
        == "protected_predictions_complete",
        "protected_admission_passed": protected.get("status") == "passed"
        and protected.get("prediction_permitted") is True,
        "serial_qualification_preserved": serial.get("status")
        == "passed_with_execution_identity_qualification"
        and serial.get("execution_identity_qualification")
        == config["execution_identity_qualification"],
        "artifact_only_admission_preserved": admission.get("status") == "passed"
        and admission.get("checks", {}).get("simulator_rerun_performed") is False
        and admission.get("checks", {}).get("tensor_array_replacement_performed")
        is False,
        "original_failed_analysis_preserved": failed.get("status")
        == "failed_or_incomplete"
        and failed.get("prediction_permitted") is False,
    }
    if not all(checks.values()):
        failed_checks = [name for name, passed in checks.items() if not passed]
        raise RuntimeError(f"final qualification failed: {failed_checks}")

    result = {
        "schema_version": 1,
        "qualification_id": EXPECTED_ID,
        "status": "qualified_failed_result",
        "config_sha256": sha256_file(config_path.resolve()),
        "artifact_sha256": {
            name: config["required_artifacts"][name]["sha256"]
            for name in sorted(config["required_artifacts"])
        },
        "checks": checks,
        "scientific_result": {
            "status": "failed",
            "phase1_goal_achieved": False,
            "supported_claim_permitted": False,
            "claim_route": "no_positive_successor_claim",
            "model_pass": model_pass,
            "failed_hypothesis_check_count": len(
                report.get("failed_hypothesis_checks", [])
            ),
        },
        "execution_identity_qualification": config[
            "execution_identity_qualification"
        ],
        "analysis_qualification": config["analysis_qualification"],
        "claim_boundary": config["required_claim_boundary"],
        "next_gate": "freeze_a_new_prospective_model_or_protocol_branch_before_using_test_evidence",
    }
    write_json(repo_path(config["output"]), result)
    return result


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    result = qualify(config_path, load_config(config_path))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

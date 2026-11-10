#!/usr/bin/env python3
"""Audit the qualified direct-v4 result against the Phase 1 completion contract."""

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
import qualify_phase1_one_action_successor_direct_v4_final as qualifier
import run_phase1_one_action_successor_direct_v4_reporting_rebind as continuation


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = (
    REPO_ROOT
    / "configs"
    / "phase1_one_action_successor_direct_v4_completion_audit_v1.json"
)
EXPECTED_ID = "phase1_one_action_successor_direct_v4_completion_audit_v1"
TEST_PATH = (
    REPO_ROOT
    / "tests"
    / "test_audit_phase1_one_action_successor_direct_v4_completion.py"
)


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
    if config.get("schema_version") != 1 or config.get("audit_id") != EXPECTED_ID:
        raise ValueError("unexpected direct-v4 completion-audit identity")
    if config.get("status") != (
        "retrospective_evidence_binding_after_qualified_protected_result"
    ):
        raise ValueError("completion audit must be retrospective evidence binding")
    if set(config.get("evidence", {})) != {
        "reporting_continuation_plan",
        "final_qualification_plan",
        "protected_dataset_summary",
        "prediction_results",
        "final_report",
        "final_qualification",
    }:
        raise ValueError("completion-audit evidence set changed")
    requirements = config.get("requirements", {})
    if (
        len(requirements.get("required_hypothesis_checks", [])) != 25
        or len(set(requirements.get("required_hypothesis_checks", []))) != 25
        or len(requirements.get("qualification_checks", [])) != 11
    ):
        raise ValueError("completion-audit required check identity changed")
    semantics = config.get("semantics", {})
    for name in (
        "audit_only_no_new_scientific_gate",
        "require_revalidation_of_every_prediction_artifact",
        "require_recomputation_of_qualification_checks",
        "preserve_direct_surrogate_claim_boundary",
    ):
        if semantics.get(name) is not True:
            raise ValueError(f"required completion-audit semantic changed: {name}")
    for name in (
        "permit_newton_added_value_claim",
        "permit_sequential_or_sim_to_real_claim",
    ):
        if semantics.get(name) is not False:
            raise ValueError(f"forbidden completion-audit semantic changed: {name}")
    return config


def evidence_payloads(
    config: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    payloads: dict[str, dict[str, Any]] = {}
    identities: dict[str, str] = {}
    for name, expected in sorted(config["evidence"].items()):
        path = repo_path(expected["path"])
        identity = sha256_file(path) if path.is_file() else ""
        if identity != expected["sha256"]:
            raise RuntimeError(f"completion-audit evidence changed: {name}")
        payloads[name] = load_json(path)
        identities[name] = identity
    return payloads, identities


def completion_checks(
    config: Mapping[str, Any],
    payloads: Mapping[str, Mapping[str, Any]],
    identities: Mapping[str, str],
    *,
    continuation_revalidated: bool,
    prediction_artifacts_revalidated: bool,
    qualification_recomputed: bool,
) -> dict[str, bool]:
    requirements = config["requirements"]
    continuation_plan = payloads["reporting_continuation_plan"]
    qualification_plan = payloads["final_qualification_plan"]
    protected = payloads["protected_dataset_summary"]
    prediction = payloads["prediction_results"]
    report = payloads["final_report"]
    qualification = payloads["final_qualification"]
    hypothesis = report.get("hypothesis_checks", {})
    qualification_checks = qualification.get("checks", {})
    expected_hypothesis = set(requirements["required_hypothesis_checks"])
    expected_qualification = set(requirements["qualification_checks"])
    candidate = report.get("candidate", {})
    return {
        "reporting_continuation_preceded_outcome": (
            continuation_plan.get("status")
            == "frozen_after_admission_before_prediction_or_report"
            and continuation_plan.get("prediction_or_report_existed_at_freeze")
            is False
            and continuation_plan.get("required_artifact_sha256", {}).get(
                "final_qualification_plan"
            )
            == identities["final_qualification_plan"]
            and continuation_plan.get("required_artifact_sha256", {}).get(
                "protected_dataset_summary"
            )
            == identities["protected_dataset_summary"]
        ),
        "final_qualification_plan_preceded_outcome": (
            qualification_plan.get("status")
            == "frozen_before_protected_admission_prediction_or_final_report"
            and qualification_plan.get("outcome_known_before_freeze") is False
        ),
        "protected_dataset_complete": (
            protected.get("status") == "passed"
            and protected.get("prediction_permitted") is True
            and protected.get("counts")
            == {
                "total": int(requirements["protected_episode_count"]),
                "test": int(requirements["test_episode_count"]),
                "protected_sensitivity": int(
                    requirements["protected_sensitivity_episode_count"]
                ),
            }
            and bool(protected.get("checks"))
            and all(value is True for value in protected["checks"].values())
        ),
        "prediction_complete_and_bound": (
            prediction.get("status") == "protected_predictions_complete"
            and len(prediction.get("episodes", []))
            == int(requirements["test_episode_count"])
            and len(prediction.get("prediction_artifacts", {}))
            == int(requirements["protected_episode_count"])
            and prediction.get("protected_dataset_summary_sha256")
            == identities["protected_dataset_summary"]
            and prediction.get("reporting_plan_sha256")
            == requirements["reporting_plan_sha256"]
            and prediction.get("protected_execution_plan_sha256")
            == requirements["protected_execution_plan_sha256"]
        ),
        "protected_sensitivity_passed": (
            prediction.get("protected_sensitivity", {}).get(
                "eligible_comparisons"
            )
            == 24
            and prediction.get("protected_sensitivity", {}).get(
                "direction_fraction"
            )
            == 1.0
        ),
        "exact_25_hypothesis_checks_passed": (
            set(hypothesis) == expected_hypothesis
            and len(hypothesis) == int(requirements["hypothesis_check_count"])
            and all(value is True for value in hypothesis.values())
            and report.get("failed_hypothesis_checks") == []
        ),
        "report_passed_coherently": (
            report.get("status") == "passed"
            and report.get("phase1_goal_achieved") is True
            and report.get("supported_claim_permitted") is True
            and report.get("claim_route") == requirements["claim_route"]
            and report.get("claim_boundary") == requirements["claim_boundary"]
        ),
        "candidate_is_fixed_parameter_conditioned_direct_model": (
            candidate.get("name") == "D1"
            and candidate.get("base_model") == "D0_seed_20261102"
            and candidate.get("family")
            == "frozen_D0_reference_differenced_kphi_sensitivity_wrapper"
            and candidate.get("no_fitting_or_gradient_updates") is True
        ),
        "report_artifact_links_exact": (
            report.get("prediction_results_sha256")
            == identities["prediction_results"]
            and report.get("protected_dataset_summary_sha256")
            == identities["protected_dataset_summary"]
            and report.get("reporting_plan_sha256")
            == requirements["reporting_plan_sha256"]
            and report.get("protected_execution_plan_sha256")
            == requirements["protected_execution_plan_sha256"]
        ),
        "qualification_passed_all_checks": (
            qualification.get("status") == "qualified_passed_result"
            and set(qualification_checks) == expected_qualification
            and all(value is True for value in qualification_checks.values())
            and qualification.get("qualification_plan_sha256")
            == identities["final_qualification_plan"]
            and qualification.get("artifact_sha256")
            == {
                "protected_dataset_summary": identities[
                    "protected_dataset_summary"
                ],
                "prediction_results": identities["prediction_results"],
                "final_report": identities["final_report"],
            }
            and qualification.get("scientific_result", {}).get(
                "phase1_goal_achieved"
            )
            is True
        ),
        "reporting_continuation_revalidated": continuation_revalidated,
        "every_prediction_artifact_revalidated": prediction_artifacts_revalidated,
        "qualification_checks_recomputed": qualification_recomputed,
    }


def build_audit(
    config_path: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    payloads, identities = evidence_payloads(config)

    continuation_config_path = continuation.DEFAULT_CONFIG.resolve()
    continuation_config = continuation.load_config(continuation_config_path)
    continuation.load_plan(continuation_config_path, continuation_config)

    direct_path, direct_config, recovery_config = continuation.validated_context(
        continuation_config
    )
    recovery_config_path = continuation.required_file(
        continuation_config, "recovery_config"
    )
    execution_plan = continuation.recovery.rebound_execution_plan(
        recovery_config_path,
        recovery_config,
        direct_path,
        direct_config,
    )
    reporter.validate_prediction_artifacts(
        direct_config, execution_plan, payloads["prediction_results"]
    )

    qualifier_config_path = qualifier.DEFAULT_CONFIG.resolve()
    qualifier_config = qualifier.load_config(qualifier_config_path)
    qualifier.load_plan(qualifier_config_path, qualifier_config)
    qualification_inputs = {
        "protected_dataset_summary": payloads["protected_dataset_summary"],
        "prediction_results": payloads["prediction_results"],
        "final_report": payloads["final_report"],
    }
    recomputed = qualifier.qualification_checks(
        qualifier_config,
        qualification_inputs,
        {
            "protected_dataset_summary": identities["protected_dataset_summary"],
            "prediction_results": identities["prediction_results"],
            "final_report": identities["final_report"],
        },
    )
    checks = completion_checks(
        config,
        payloads,
        identities,
        continuation_revalidated=True,
        prediction_artifacts_revalidated=True,
        qualification_recomputed=bool(recomputed)
        and all(value is True for value in recomputed.values()),
    )
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise RuntimeError(f"Phase 1 completion audit failed: {failed}")
    return {
        "schema_version": 1,
        "audit_id": EXPECTED_ID,
        "status": "passed",
        "phase1_goal_achieved": True,
        "claim_route": config["requirements"]["claim_route"],
        "claim_boundary": config["requirements"]["claim_boundary"],
        "config_sha256": sha256_file(config_path),
        "source_sha256": {
            "auditor": sha256_file(Path(__file__).resolve()),
            "auditor_tests": sha256_file(TEST_PATH),
        },
        "evidence_sha256": dict(identities),
        "checks": checks,
        "scientific_summary": {
            "hypothesis_checks_passed": 25,
            "hypothesis_checks_failed": 0,
            "protected_test_episodes": 24,
            "protected_sensitivity_episodes": 6,
            "protected_sensitivity_direction_fraction": 1.0,
            "candidate": payloads["final_report"]["candidate"],
            "accuracy": payloads["final_report"]["accuracy"],
            "parameter_controls": payloads["final_report"][
                "parameter_controls"
            ],
            "uncertainty_coverage": payloads["final_report"][
                "uncertainty_coverage"
            ],
        },
    }


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = load_config(config_path)
    result = build_audit(config_path, config)
    destination = repo_path(config["execution"]["output"])
    if destination.is_file():
        existing = load_json(destination)
        if existing != result:
            raise RuntimeError("refusing changed Phase 1 completion audit")
    else:
        write_json(destination, result)
    print(
        json.dumps(
            {
                "audit": str(destination),
                "sha256": sha256_file(destination),
                "status": result["status"],
                "phase1_goal_achieved": result["phase1_goal_achieved"],
                "claim_route": result["claim_route"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

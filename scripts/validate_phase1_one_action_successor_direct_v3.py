#!/usr/bin/env python3
"""Validate direct-v3 with one coherent paired parameter-control statistic."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import evaluate_phase1_one_action_successor as evaluation
import validate_phase1_one_action_successor_direct_v2 as v2


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_direct_v3.json"
EXPECTED_ID = "phase1_one_action_successor_direct_v3"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.resolve().read_text(encoding="utf-8"))
    if config.get("schema_version") != 1 or config.get("branch_id") != EXPECTED_ID:
        raise ValueError("unexpected direct-v3 branch identity")
    candidate = config.get("candidate", {})
    if (
        candidate.get("name") != "D1"
        or candidate.get("base_model") != "D0_seed_20261102"
        or candidate.get("sensitivity_gain") != 1.0
        or candidate.get("initial_residual_scale") != 1.0
        or candidate.get("reference_kphi_normalized") != 0.0
        or candidate.get("no_fitting_or_gradient_updates") is not True
    ):
        raise ValueError("direct-v3 candidate definition changed")
    protocol = config.get("confirmation_protocol", {})
    if protocol.get("accuracy_regions") != list(v2.REGIONS):
        raise ValueError("direct-v3 full-region accuracy contract changed")
    if protocol.get("parameter_control_regions") != ["footprint"]:
        raise ValueError("direct-v3 parameter-control locality changed")
    if protocol.get("parameter_control_metric") != (
        "paired_mean_rmse_increase_relative_to_mean_candidate_rmse"
    ):
        raise ValueError("direct-v3 parameter-control statistic changed")
    if protocol.get("revealed_v1_test_is_not_confirmation") is not True:
        raise ValueError("revealed v1 test boundary weakened")
    return config


def require_sources(config: Mapping[str, Any]) -> None:
    v2.require_sources(config)
    path = v2.repo_path(config["antecedent"]["failed_direct_v2_validation"])
    v2.require_file(
        path,
        str(config["antecedent"]["failed_direct_v2_validation_sha256"]),
        "failed_direct_v2_validation",
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != "validation_failed" or payload.get("passed") is not False:
        raise RuntimeError("direct-v2 validation failure is not preserved")


def aggregate(config: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    compatibility = copy.deepcopy(config)
    compatibility["success_thresholds"]["parameter_control_minimum_degradation"] = float(
        config["success_thresholds"][
            "parameter_control_paired_mean_relative_degradation_minimum"
        ]
    )
    result = v2.aggregate(compatibility, rows)
    checks = dict(result["checks"])
    controls: dict[str, Any] = {}
    ordered = sorted(rows, key=lambda row: str(row["episode_id"]))
    validation = config["validation"]
    threshold = float(
        config["success_thresholds"][
            "parameter_control_paired_mean_relative_degradation_minimum"
        ]
    )
    for control_index, control in enumerate(
        ("kphi_shuffled", "kphi_constant_reference")
    ):
        controls[control] = {}
        for checkpoint_index, checkpoint in enumerate(v2.CHECKPOINTS):
            model = np.asarray(
                [row["rmse_m"]["D1"][checkpoint]["footprint"] for row in ordered]
            )
            degraded = np.asarray(
                [
                    row["parameter_controls"][control][checkpoint]["footprint"]
                    for row in ordered
                ]
            )
            difference = degraded - model
            relative = float(np.mean(difference) / np.mean(model))
            interval = evaluation.bootstrap_interval(
                difference,
                statistic=np.mean,
                resamples=int(validation["bootstrap_resamples"]),
                confidence=float(validation["bootstrap_confidence"]),
                seed=int(validation["bootstrap_seed"])
                + 100 * control_index
                + checkpoint_index,
            )
            controls[control][checkpoint] = {
                "paired_mean_relative_rmse_increase": relative,
                "control_minus_model_rmse_m": interval,
            }
            checks[f"parameter_control:{control}:{checkpoint}:footprint"] = (
                relative >= threshold and float(interval["lower"]) > 0.0
            )
    result["checks"] = checks
    result["passed"] = all(checks.values())
    result["parameter_controls"] = controls
    return result


def validate(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    require_sources(config)
    rows, auxiliary = v2.validation_rows(config)
    result = aggregate(config, rows)
    payload = {
        "schema_version": 1,
        "branch_id": EXPECTED_ID,
        "status": "validation_passed_fresh_confirmation_plan_permitted"
        if result["passed"]
        else "validation_failed",
        "config_sha256": evaluation.sha256_file(config_path.resolve()),
        "validation_episode_ids": sorted(str(row["episode_id"]) for row in rows),
        "v1_test_episode_count_used": 0,
        "candidate": dict(config["candidate"]),
        **result,
        **auxiliary,
    }
    output = v2.repo_path(config["validation"]["output"])
    if output.is_file():
        existing = json.loads(output.read_text(encoding="utf-8"))
        if existing != payload:
            raise RuntimeError("refusing to replace a different direct-v3 validation")
        return existing
    evaluation.write_json(output, payload)
    return payload


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    payload = validate(config_path, load_config(config_path))
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

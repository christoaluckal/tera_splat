#!/usr/bin/env python3
"""Run authoritative direct-v4 validation after confirmation-lock freeze."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import evaluate_phase1_one_action_successor as evaluation
import plan_phase1_one_action_successor_direct_v4 as planner
import validate_phase1_one_action_successor_direct_v2 as v2
import validate_phase1_one_action_successor_direct_v3 as v3


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = planner.DEFAULT_CONFIG
EXPECTED_ID = planner.EXPECTED_ID


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    return parser.parse_args()


def require_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    path = planner.repo_path(config["execution"]["confirmation_plan"])
    if not path.is_file():
        raise RuntimeError("freeze direct-v4 confirmation identities before validation")
    plan = json.loads(path.read_text(encoding="utf-8"))
    if plan.get("status") != "target_free_confirmation_plan_frozen_before_authoritative_validation":
        raise RuntimeError("direct-v4 confirmation plan state changed")
    if plan.get("config_sha256") != evaluation.sha256_file(config_path.resolve()):
        raise RuntimeError("direct-v4 config changed after confirmation-plan freeze")
    sources = planner.source_paths(config_path)
    current = {name: evaluation.sha256_file(path) for name, path in sorted(sources.items())}
    if plan.get("source_sha256") != current:
        raise RuntimeError("direct-v4 sources changed after confirmation-plan freeze")
    if plan.get("targets_opened") is not False or plan.get("authoritative_validation_complete") is not False:
        raise RuntimeError("direct-v4 plan is not in its pre-validation locked state")
    dataset_root = planner.repo_path(config["execution"]["dataset_output_root"])
    chrono_root = planner.repo_path(config["execution"]["chrono_output_root"])
    if (dataset_root / "episodes").exists() or chrono_root.exists():
        raise RuntimeError("direct-v4 targets opened before authoritative validation")
    return plan


def require_antecedents(config: Mapping[str, Any]) -> None:
    v3.require_sources(config)
    path = planner.repo_path(config["antecedent"]["direct_v3_preflight_validation"])
    v2.require_file(
        path,
        str(config["antecedent"]["direct_v3_preflight_validation_sha256"]),
        "direct_v3_preflight_validation",
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != "validation_passed_fresh_confirmation_plan_permitted":
        raise RuntimeError("direct-v3 preflight validation is not preserved")
    if config["antecedent"].get(
        "direct_v3_preflight_only_because_confirmation_lock_followed_validation"
    ) is not True:
        raise RuntimeError("direct-v3 ordering qualification was removed")


def validate(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    plan = require_plan(config_path, config)
    require_antecedents(config)
    rows, auxiliary = v2.validation_rows(config)
    result = v3.aggregate(config, rows)
    payload = {
        "schema_version": 1,
        "branch_id": EXPECTED_ID,
        "status": "authoritative_validation_passed_confirmation_unlock_permitted"
        if result["passed"]
        else "authoritative_validation_failed",
        "confirmation_plan_sha256": evaluation.sha256_file(
            planner.repo_path(config["execution"]["confirmation_plan"])
        ),
        "test_lock_sha256": plan["test_lock_sha256"],
        "sensitivity_lock_sha256": plan["sensitivity_lock_sha256"],
        "confirmation_targets_opened": False,
        "validation_episode_ids": sorted(str(row["episode_id"]) for row in rows),
        "v1_test_episode_count_used": 0,
        "candidate": dict(config["candidate"]),
        **result,
        **auxiliary,
    }
    output = planner.repo_path(config["validation"]["output"])
    if output.is_file():
        existing = json.loads(output.read_text(encoding="utf-8"))
        if existing != payload:
            raise RuntimeError("refusing to replace a different direct-v4 validation")
        return existing
    evaluation.write_json(output, payload)
    return payload


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = planner.load_config(config_path)
    payload = validate(config_path, config)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Qualify direct-v4 fresh surfaces without opening confirmation targets."""

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
import qualify_phase1_one_action_successor_surfaces as base
import run_fresh_phase0_repeatability as fresh


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = planner.DEFAULT_CONFIG
IDENTITY = "phase1_one_action_successor_direct_v4_surface_qualification"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--stage", choices=("plan", "qualify", "analyze", "all"), default="plan"
    )
    parser.add_argument("--seed", type=int, action="append", default=[])
    return parser.parse_args()


def output_root(config: Mapping[str, Any]) -> Path:
    return planner.repo_path(config["execution"]["output_root"]) / "surface_qualification"


def plan_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "qualification_plan.json"


def summary_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "qualification_summary.json"


def load_context(
    config_path: Path, config: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], Path]:
    confirmation_path = planner.repo_path(config["execution"]["confirmation_plan"])
    if not confirmation_path.is_file():
        raise RuntimeError("direct-v4 confirmation plan is absent")
    confirmation = json.loads(confirmation_path.read_text(encoding="utf-8"))
    if confirmation.get("status") != (
        "target_free_confirmation_plan_frozen_before_authoritative_validation"
    ):
        raise RuntimeError("direct-v4 confirmation plan state changed")
    if confirmation.get("config_sha256") != evaluation.sha256_file(
        config_path.resolve()
    ):
        raise RuntimeError("direct-v4 config changed after confirmation freeze")
    validation_path = planner.repo_path(config["validation"]["output"])
    if not validation_path.is_file():
        raise RuntimeError("direct-v4 authoritative validation is absent")
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    if validation.get("status") != (
        "authoritative_validation_passed_confirmation_unlock_permitted"
    ) or validation.get("confirmation_targets_opened") is not False:
        raise RuntimeError("direct-v4 authoritative validation has not passed closed")
    contract_path = planner.require_source(config, "domain_contract")
    contract = planner.original.load_contract(contract_path)
    dataset_root = planner.repo_path(config["execution"]["dataset_output_root"])
    chrono_root = planner.repo_path(config["execution"]["chrono_output_root"])
    if (dataset_root / "episodes").exists() or chrono_root.exists():
        raise RuntimeError("direct-v4 targets opened before surface qualification")
    return contract, confirmation, validation_path


def cases(config: Mapping[str, Any], confirmation: Mapping[str, Any]) -> list[dict[str, Any]]:
    by_seed: dict[int, str] = {}
    for split in ("test", "protected_sensitivity"):
        for episode in confirmation["episodes"][split]:
            seed = int(episode["initial_surface_seed"])
            partition = "fresh_test" if split == "test" else "fresh_sensitivity"
            if seed in by_seed and by_seed[seed] != partition:
                raise RuntimeError("direct-v4 surface seed crosses partitions")
            by_seed[seed] = partition
    expected = set(int(value) for value in config["confirmation_design"]["test_surface_seeds"])
    expected.add(int(config["confirmation_design"]["sensitivity_surface_seed"]))
    if set(by_seed) != expected:
        raise RuntimeError("direct-v4 confirmation surface membership changed")
    domain = json.loads(
        planner.require_source(config, "domain_contract").read_text(encoding="utf-8")
    )["initial_surface_domain"]
    bounds = {
        "relief_limit_m": domain["relief_limit_m"],
        "maximum_local_slope_deg": domain["maximum_local_slope_deg"],
        "minimum_correlation_length_m": domain["minimum_correlation_length_m"],
    }
    result = []
    for seed, partition in sorted(by_seed.items()):
        payload = {
            "partition": partition,
            "initial_surface_seed": seed,
            "generator": domain["generator"],
            "bounds": bounds,
        }
        result.append(
            {
                "case_id": f"direct_v4_surface_{seed}",
                **payload,
                "input_sha256": base.canonical_sha256(payload),
            }
        )
    return result


def source_paths(contract: Mapping[str, Any]) -> dict[str, Path]:
    paths = base.source_paths(dict(contract))
    paths["qualifier"] = Path(__file__).resolve()
    paths["base_qualifier"] = Path(base.__file__).resolve()
    paths["focused_tests"] = (
        REPO_ROOT
        / "tests"
        / "test_qualify_phase1_one_action_successor_direct_v4_surfaces.py"
    )
    return paths


def build_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    contract, confirmation, validation_path = load_context(config_path, config)
    sources = source_paths(contract)
    missing = [str(path) for path in sources.values() if not path.is_file()]
    if missing:
        raise RuntimeError(f"direct-v4 surface source set is incomplete: {missing}")
    return {
        "schema_version": 1,
        "identity": IDENTITY,
        "status": "frozen_before_surface_runtime",
        "config_sha256": evaluation.sha256_file(config_path.resolve()),
        "confirmation_plan_sha256": evaluation.sha256_file(
            planner.repo_path(config["execution"]["confirmation_plan"])
        ),
        "authoritative_validation_sha256": evaluation.sha256_file(validation_path),
        "test_lock_sha256": confirmation["test_lock_sha256"],
        "sensitivity_lock_sha256": confirmation["sensitivity_lock_sha256"],
        "source_sha256": {
            name: evaluation.sha256_file(path) for name, path in sorted(sources.items())
        },
        "environment": base.environment(contract),
        "cases": cases(config, confirmation),
        "maximum_scm_roundtrip_error_m": base.MAXIMUM_ROUNDTRIP_ERROR_M,
        "target_generation_permitted": False,
    }


def write_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    payload = build_plan(config_path, config)
    path = plan_path(config)
    if path.is_file():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != payload:
            raise RuntimeError("refusing changed direct-v4 surface plan")
        return existing
    evaluation.write_json(path, payload)
    return payload


def load_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    path = plan_path(config)
    if not path.is_file():
        raise RuntimeError("freeze direct-v4 surface plan before runtime")
    frozen = json.loads(path.read_text(encoding="utf-8"))
    if frozen != build_plan(config_path, config):
        raise RuntimeError("direct-v4 surface qualification identity changed")
    return frozen


def surface_root(config: Mapping[str, Any], seed: int) -> Path:
    return output_root(config) / "surfaces" / f"surface_{int(seed)}"


def qualify(
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    plan: Mapping[str, Any],
    case: Mapping[str, Any],
) -> dict[str, Any]:
    original_root = base.OUTPUT_ROOT
    try:
        base.OUTPUT_ROOT = output_root(config)
        return base.qualify(dict(contract), dict(plan), dict(case))
    finally:
        base.OUTPUT_ROOT = original_root


def summarize(config: Mapping[str, Any], plan: Mapping[str, Any]) -> dict[str, Any]:
    results = []
    for case in plan["cases"]:
        path = surface_root(config, int(case["initial_surface_seed"])) / "qualification_summary.json"
        results.append(
            json.loads(path.read_text(encoding="utf-8"))
            if path.is_file()
            else {
                "case_id": case["case_id"],
                "seed": case["initial_surface_seed"],
                "qualified": False,
            }
        )
    passed = len(results) == 6 and all(item.get("qualified") is True for item in results)
    payload = {
        "schema_version": 1,
        "identity": IDENTITY,
        "status": "passed" if passed else "failed_or_incomplete",
        "all_six_surfaces_qualified": passed,
        "joint_unlock_permitted": passed,
        "targets_opened": False,
        "qualification_plan_sha256": evaluation.sha256_file(plan_path(config)),
        "surfaces": {str(item["seed"]): item for item in results},
    }
    evaluation.write_json(summary_path(config), payload)
    return payload


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = planner.load_config(config_path)
    if args.stage == "plan":
        payload = write_plan(config_path, config)
        print(
            json.dumps(
                {
                    "plan": str(plan_path(config)),
                    "sha256": evaluation.sha256_file(plan_path(config)),
                    "cases": len(payload["cases"]),
                },
                indent=2,
            )
        )
        return
    plan = load_plan(config_path, config)
    contract, _confirmation, _validation = load_context(config_path, config)
    selected = [
        case
        for case in plan["cases"]
        if not args.seed or int(case["initial_surface_seed"]) in set(args.seed)
    ]
    if args.seed and len(selected) != len(set(args.seed)):
        raise ValueError("unknown or duplicate direct-v4 surface seed")
    if args.stage in ("qualify", "all"):
        for case in selected:
            result = qualify(config, contract, plan, case)
            print(json.dumps({"seed": result["seed"], "qualified": result["qualified"]}), flush=True)
    if args.stage in ("analyze", "all"):
        result = summarize(config, plan)
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "all_six_surfaces_qualified": result["all_six_surfaces_qualified"],
                    "joint_unlock_permitted": result["joint_unlock_permitted"],
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()

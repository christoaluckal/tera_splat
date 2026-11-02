#!/usr/bin/env python3
"""Generate the jointly unlocked successor test and sensitivity episodes."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import evaluate_phase1_one_action_successor as evaluation
import run_fresh_phase0_repeatability as fresh
import run_phase1_one_action_successor_smoke as smoke


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = evaluation.DEFAULT_CONFIG
SMOKE_CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_smoke_v1.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--stage",
        choices=("chrono", "bed", "newton", "analyze", "all"),
        default="chrono",
    )
    parser.add_argument("--episode", action="append", default=[])
    parser.add_argument("--workers", type=int)
    return parser.parse_args()


def runtime_config(config: Mapping[str, Any]) -> dict[str, Any]:
    runtime = smoke.load_config(SMOKE_CONFIG)
    runtime = copy.deepcopy(runtime)
    runtime["dataset_id"] = "phase1_one_action_successor_protected_v1"
    runtime["status"] = "selection_gated_protected_runtime"
    runtime["dataset_plan"] = str(evaluation.repo_path(config["dataset_plan"]))
    runtime["membership"] = {
        "train": [],
        "validation": [],
        "test": [],
        "protected_sensitivity": [],
    }
    runtime["execution"]["output_root"] = config["execution"]["dataset_output_root"]
    runtime["execution"]["chrono_output_root"] = config["execution"]["chrono_output_root"]
    runtime["execution"]["workers"] = 2
    return runtime


def protected_episodes(plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    result = [
        dict(item)
        for split in ("test", "protected_sensitivity")
        for item in plan["episodes"][split]
    ]
    if len(result) != 30 or len({item["episode_id"] for item in result}) != 30:
        raise ValueError("protected runtime requires 30 unique episodes")
    if Counter(item["split"] for item in result) != {
        "test": 24,
        "protected_sensitivity": 6,
    }:
        raise ValueError("protected runtime split membership changed")
    return result


def choose_episodes(
    episodes: Sequence[Mapping[str, Any]], requested: Sequence[str]
) -> list[dict[str, Any]]:
    by_id = {str(item["episode_id"]): dict(item) for item in episodes}
    unknown = sorted(set(requested) - set(by_id))
    if unknown:
        raise ValueError(f"unknown protected successor episodes: {unknown}")
    return [by_id[name] for name in requested] if requested else list(by_id.values())


def configure_runtime_plan(
    config: Mapping[str, Any], plan: Mapping[str, Any]
) -> dict[str, Any]:
    episodes = protected_episodes(plan)
    runtime_plan = dict(plan)
    runtime_plan["episodes"] = episodes
    # The proven bed/preparation helpers bind their metadata to this path.
    smoke.base.plan_path = lambda _runtime_config: evaluation.plan_path(config)
    return runtime_plan


def summary_path(config: Mapping[str, Any]) -> Path:
    return evaluation.output_root(config) / "protected_dataset_summary.json"


def summarize(
    config: Mapping[str, Any],
    runtime: Mapping[str, Any],
    contract: Mapping[str, Any],
    evaluation_plan: Mapping[str, Any],
    runtime_plan: Mapping[str, Any],
) -> dict[str, Any]:
    rows = [
        smoke.base.analyze_episode(runtime, contract, item)
        for item in runtime_plan["episodes"]
    ]
    counts = Counter(str(item["split"]) for item in rows)
    test_groups = Counter(
        str(item["holdout_group"])
        for item in evaluation_plan["episodes"]["test"]
    )
    checks = {
        "episode_count": len(rows) == 30,
        "test_count": counts == {"test": 24, "protected_sensitivity": 6},
        "all_complete": all(item.get("complete") is True for item in rows),
        "all_admitted": all(item.get("admitted") is True for item in rows),
        "test_holdout_groups": dict(test_groups)
        == config["membership"]["test_holdout_groups"],
        "protected_open_identity": evaluation.require_opened(
            config, evaluation_plan
        ).get("targets_opened")
        is True,
    }
    passed = all(checks.values())
    result = {
        "schema_version": 1,
        "status": "passed" if passed else "failed_or_incomplete",
        "evaluation_plan_sha256": evaluation.sha256_file(
            evaluation.plan_path(config)
        ),
        "protected_open_sha256": evaluation.sha256_file(
            evaluation.opened_path(config)
        ),
        "counts": {
            "total": len(rows),
            "test": counts.get("test", 0),
            "protected_sensitivity": counts.get("protected_sensitivity", 0),
        },
        "checks": checks,
        "prediction_permitted": passed,
        "episodes": {str(item["episode_id"]): item for item in rows},
        "artifact_sha256": (
            evaluation.protected_artifact_identity(config, evaluation_plan)
            if passed
            else {}
        ),
    }
    evaluation.write_json(summary_path(config), result)
    return result


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = evaluation.load_config(config_path)
    plan = evaluation.load_plan(config_path, config)
    evaluation.require_unlocked(config, plan)
    runtime = runtime_config(config)
    workers = int(args.workers or runtime["execution"]["workers"])
    if workers != 2:
        raise ValueError("protected successor runtime requires the qualified two workers")
    runtime_plan = configure_runtime_plan(config, plan)
    episodes = choose_episodes(runtime_plan["episodes"], args.episode)
    _successor_path, _successor, _operations_path, contract = smoke.merged_contract(
        runtime
    )
    if args.stage in ("chrono", "all"):
        evaluation.mark_protected_opened(config, plan)
        smoke.run_parallel(
            "protected chrono",
            episodes,
            workers,
            lambda item: smoke.run_chrono(runtime, contract, item),
        )
    else:
        evaluation.require_opened(config, plan)
    seeds = sorted({int(item["initial_surface_seed"]) for item in episodes})
    if args.stage in ("bed", "all"):
        smoke.run_parallel(
            "protected bed",
            seeds,
            workers,
            lambda seed: smoke.base.build_bed(
                runtime, contract, runtime_plan, seed
            ),
        )
    if args.stage in ("newton", "all"):
        smoke.run_parallel(
            "protected preparation",
            seeds,
            workers,
            lambda seed: smoke.base.prepare_prior(
                runtime, contract, runtime_plan, seed
            ),
        )
        smoke.run_parallel(
            "protected response",
            episodes,
            workers,
            lambda item: smoke.base.run_newton(
                runtime, contract, runtime_plan, item
            ),
        )
    if args.stage in ("analyze", "all"):
        result = summarize(config, runtime, contract, plan, runtime_plan)
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "prediction_permitted": result["prediction_permitted"],
                    "counts": result["counts"],
                    "checks": result["checks"],
                },
                indent=2,
            )
        )
        return
    print(
        json.dumps(
            {
                "stage": args.stage,
                "requested": len(episodes),
                "protected_targets_opened": evaluation.opened_path(config).is_file(),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

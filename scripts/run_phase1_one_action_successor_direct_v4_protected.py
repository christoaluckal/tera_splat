#!/usr/bin/env python3
"""Generate and admit the jointly unlocked direct-v4 confirmation set."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import evaluate_phase1_one_action_successor as evaluation
import plan_phase1_one_action_successor_direct_v4 as planner
import run_fresh_phase0_repeatability as fresh
import run_phase1_one_action_successor_smoke as smoke
import unlock_phase1_one_action_successor_direct_v4 as unlock


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = planner.DEFAULT_CONFIG
SMOKE_CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_smoke_v1.json"
TEST_PATH = REPO_ROOT / "tests" / "test_run_phase1_one_action_successor_direct_v4_protected.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--stage",
        choices=("plan", "chrono", "bed", "newton", "analyze", "all"),
        default="plan",
    )
    parser.add_argument("--episode", action="append", default=[])
    parser.add_argument("--workers", type=int)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def runtime_config(config: Mapping[str, Any]) -> dict[str, Any]:
    runtime = copy.deepcopy(smoke.load_config(SMOKE_CONFIG))
    runtime["dataset_id"] = "phase1_one_action_successor_direct_v4_protected"
    runtime["status"] = "jointly_unlocked_protected_runtime"
    runtime["dataset_plan"] = config["execution"]["confirmation_plan"]
    runtime["membership"] = {
        "train": [],
        "validation": [],
        "test": [],
        "protected_sensitivity": [],
    }
    output = planner.repo_path(config["execution"]["output_root"])
    runtime["prerequisites"]["surface_qualification_plan"] = str(
        output / "surface_qualification" / "qualification_plan.json"
    )
    runtime["prerequisites"]["surface_qualification_summary"] = str(
        output / "surface_qualification" / "qualification_summary.json"
    )
    runtime["execution"]["output_root"] = config["execution"]["dataset_output_root"]
    runtime["execution"]["chrono_output_root"] = config["execution"]["chrono_output_root"]
    runtime["execution"]["surface_root"] = str(
        output / "surface_qualification" / "surfaces"
    )
    runtime["execution"]["workers"] = 2
    return runtime


def execution_plan_path(config: Mapping[str, Any]) -> Path:
    return planner.repo_path(config["execution"]["output_root"]) / "protected_execution_plan.json"


def summary_path(config: Mapping[str, Any]) -> Path:
    return planner.repo_path(config["execution"]["output_root"]) / "protected_dataset_summary.json"


def protected_episodes(plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = [
        dict(item)
        for split in ("test", "protected_sensitivity")
        for item in plan["episodes"][split]
    ]
    counts = Counter(str(item["split"]) for item in rows)
    if len(rows) != 30 or len({str(item["episode_id"]) for item in rows}) != 30:
        raise RuntimeError("direct-v4 runtime requires 30 unique episodes")
    if counts != {"test": 24, "protected_sensitivity": 6}:
        raise RuntimeError("direct-v4 protected split membership changed")
    if any(item.get("target_access") != "locked" for item in rows):
        raise RuntimeError("direct-v4 protected target lock changed")
    return rows


def choose_episodes(
    episodes: Sequence[Mapping[str, Any]], requested: Sequence[str]
) -> list[dict[str, Any]]:
    by_id = {str(item["episode_id"]): dict(item) for item in episodes}
    unknown = sorted(set(requested) - set(by_id))
    if unknown:
        raise ValueError(f"unknown direct-v4 protected episodes: {unknown}")
    return [by_id[name] for name in requested] if requested else list(by_id.values())


def context(
    config_path: Path, config: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    joint = unlock.require_unlocked(config_path, config)
    confirmation_path, confirmation = unlock.validate_confirmation(config_path, config)
    runtime = runtime_config(config)
    _successor_path, successor, _operations_path, contract = smoke.merged_contract(runtime)
    if confirmation_path != planner.repo_path(config["execution"]["confirmation_plan"]):
        raise RuntimeError("direct-v4 confirmation path changed")
    return runtime, successor, contract, {"joint": joint, "plan": confirmation}


def prerequisite_paths(runtime: Mapping[str, Any]) -> dict[str, Path]:
    prerequisite = runtime["prerequisites"]
    return {
        "directional_summary": planner.repo_path(prerequisite["directional_summary"]),
        "latent_summary": planner.repo_path(prerequisite["latent_summary"]),
        "surface_qualification_plan": Path(
            prerequisite["surface_qualification_plan"]
        ).resolve(),
        "surface_qualification_summary": Path(
            prerequisite["surface_qualification_summary"]
        ).resolve(),
    }


def validate_prerequisites(runtime: Mapping[str, Any]) -> dict[str, Path]:
    paths = prerequisite_paths(runtime)
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise RuntimeError(f"direct-v4 runtime prerequisites are absent: {missing}")
    prerequisite = runtime["prerequisites"]
    directional = load_json(paths["directional_summary"])
    latent = load_json(paths["latent_summary"])
    surface = load_json(paths["surface_qualification_summary"])
    if evaluation.sha256_file(paths["directional_summary"]) != prerequisite[
        "directional_summary_sha256"
    ] or directional.get("status") != prerequisite["required_directional_status"]:
        raise RuntimeError("direct-v4 directional prerequisite changed")
    if evaluation.sha256_file(paths["latent_summary"]) != prerequisite[
        "latent_summary_sha256"
    ] or latent.get("status") != prerequisite["required_latent_status"]:
        raise RuntimeError("direct-v4 latent prerequisite changed")
    if sorted(latent.get("qualified_nonkinematic_families", [])) != sorted(
        prerequisite["qualified_optional_families"]
    ):
        raise RuntimeError("direct-v4 latent field qualification changed")
    if surface.get("status") != "passed" or surface.get(
        "joint_unlock_permitted"
    ) is not True:
        raise RuntimeError("direct-v4 surface prerequisite changed")
    return paths


def source_paths(
    config_path: Path,
    runtime: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Path]:
    successor_path = planner.repo_path(runtime["successor_contract"])
    operations_path = planner.repo_path(runtime["operations_contract"])
    paths = smoke.source_paths(
        SMOKE_CONFIG, runtime, successor_path, operations_path, contract
    )
    paths.update(
        {
            "direct_v4_config": config_path,
            "direct_v4_protected_runner": Path(__file__).resolve(),
            "direct_v4_protected_tests": TEST_PATH,
            "direct_v4_unlocker": Path(unlock.__file__).resolve(),
        }
    )
    return paths


def input_paths(
    config: Mapping[str, Any],
    runtime: Mapping[str, Any],
    episodes: Sequence[Mapping[str, Any]],
) -> dict[str, Path]:
    paths = {
        "confirmation_plan": planner.repo_path(config["execution"]["confirmation_plan"]),
        "joint_unlock": unlock.unlock_path(config),
        **validate_prerequisites(runtime),
        "phase0_admission_contract": REPO_ROOT
        / "configs"
        / "static_proxy_hierarchical_v3_20261017.json",
    }
    surface_root = planner.repo_path(runtime["execution"]["surface_root"])
    for seed in sorted({int(item["initial_surface_seed"]) for item in episodes}):
        root = surface_root / f"surface_{seed}"
        paths[f"surface_{seed}:heightmap"] = root / "initial_heightmap_m.npy"
        paths[f"surface_{seed}:qualification"] = root / "qualification_summary.json"
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise RuntimeError(f"direct-v4 runtime inputs are absent: {missing}")
    return paths


def build_execution_plan(
    config_path: Path, config: Mapping[str, Any], require_targets_absent: bool
) -> dict[str, Any]:
    runtime, _successor, contract, records = context(config_path, config)
    if require_targets_absent:
        unlock.assert_targets_absent(config)
    confirmation = records["plan"]
    episodes = protected_episodes(confirmation)
    sources = source_paths(config_path, runtime, contract)
    inputs = input_paths(config, runtime, episodes)
    missing = [str(path) for path in sources.values() if not path.is_file()]
    if missing:
        raise RuntimeError(f"direct-v4 runtime sources are absent: {missing}")
    return {
        "schema_version": 1,
        "branch_id": config["branch_id"],
        "status": "protected_execution_frozen_before_first_target",
        "config_sha256": evaluation.sha256_file(config_path),
        "confirmation_plan_sha256": evaluation.sha256_file(
            planner.repo_path(config["execution"]["confirmation_plan"])
        ),
        "joint_unlock_sha256": evaluation.sha256_file(unlock.unlock_path(config)),
        "source_sha256": {
            name: evaluation.sha256_file(path) for name, path in sorted(sources.items())
        },
        "input_sha256": {
            name: evaluation.sha256_file(path) for name, path in sorted(inputs.items())
        },
        "environment": smoke.base.environment_probe(runtime, contract),
        "repository_revisions": {
            "tera_splat": fresh.command_output(["git", "rev-parse", "HEAD"], REPO_ROOT),
            "tera_splat_sim": fresh.command_output(
                ["git", "rev-parse", "HEAD"], planner.repo_path(contract["chrono"]["repo"])
            ),
        },
        "episodes": episodes,
        "counts": {"test": 24, "protected_sensitivity": 6},
        "surface_seeds": list(range(5101, 5107)),
        "episode_manifest_sha256": confirmation["episode_manifest_sha256"],
        "test_lock_sha256": confirmation["test_lock_sha256"],
        "sensitivity_lock_sha256": confirmation["sensitivity_lock_sha256"],
        "worker_count": 2,
        "targets_opened": False,
    }


STABLE_PLAN_KEYS = (
    "config_sha256",
    "confirmation_plan_sha256",
    "joint_unlock_sha256",
    "source_sha256",
    "input_sha256",
    "environment",
    "repository_revisions",
    "episodes",
    "counts",
    "surface_seeds",
    "episode_manifest_sha256",
    "test_lock_sha256",
    "sensitivity_lock_sha256",
    "worker_count",
    "targets_opened",
)


def write_execution_plan(
    config_path: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    current = build_execution_plan(config_path, config, True)
    path = execution_plan_path(config)
    if path.is_file():
        frozen = load_json(path)
        if any(frozen.get(key) != current.get(key) for key in STABLE_PLAN_KEYS):
            raise RuntimeError("refusing changed direct-v4 protected execution plan")
        return frozen
    evaluation.write_json(path, current)
    return current


def load_execution_plan(
    config_path: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    path = execution_plan_path(config)
    if not path.is_file():
        raise RuntimeError("freeze the direct-v4 protected execution plan first")
    frozen = load_json(path)
    current = build_execution_plan(config_path, config, False)
    changed = [
        key for key in STABLE_PLAN_KEYS if frozen.get(key) != current.get(key)
    ]
    if changed:
        raise RuntimeError(f"direct-v4 protected execution identity changed: {changed}")
    return frozen


def expected_open_marker(
    config: Mapping[str, Any], plan: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "branch_id": config["branch_id"],
        "status": "direct_v4_test_and_sensitivity_targets_opened_once",
        "protected_execution_plan_sha256": evaluation.sha256_file(
            execution_plan_path(config)
        ),
        "joint_unlock_sha256": evaluation.sha256_file(unlock.unlock_path(config)),
        "episode_manifest_sha256": plan["episode_manifest_sha256"],
        "test_lock_sha256": plan["test_lock_sha256"],
        "sensitivity_lock_sha256": plan["sensitivity_lock_sha256"],
        "counts": {"test": 24, "protected_sensitivity": 6},
        "targets_opened": True,
    }


def mark_opened(
    config_path: Path, config: Mapping[str, Any], plan: Mapping[str, Any]
) -> dict[str, Any]:
    unlock.require_unlocked(config_path, config)
    marker = expected_open_marker(config, plan)
    path = unlock.opened_path(config)
    if path.is_file():
        existing = load_json(path)
        if existing != marker:
            raise RuntimeError("direct-v4 protected open identity changed")
        return existing
    unlock.assert_targets_absent(config)
    evaluation.write_json(path, marker)
    return marker


def require_opened(
    config_path: Path, config: Mapping[str, Any], plan: Mapping[str, Any]
) -> dict[str, Any]:
    unlock.require_unlocked(config_path, config)
    path = unlock.opened_path(config)
    if not path.is_file():
        raise RuntimeError("direct-v4 protected targets have not been opened")
    marker = load_json(path)
    if marker != expected_open_marker(config, plan):
        raise RuntimeError("direct-v4 protected open marker changed")
    return marker


def protected_tensor_checks(
    checks: Mapping[str, Any], protected_opened: bool
) -> dict[str, Any]:
    updated = dict(checks)
    updated.pop("no_test_target", None)
    updated["protected_target_opened_after_joint_unlock"] = protected_opened
    return updated


def configure_runtime_helpers(
    config_path: Path, config: Mapping[str, Any], plan: Mapping[str, Any]
) -> None:
    smoke.base.plan_path = lambda _runtime: execution_plan_path(config)

    def export_tensors(
        runtime: Mapping[str, Any],
        contract: Mapping[str, Any],
        episode: Mapping[str, Any],
    ) -> dict[str, Any]:
        manifest = smoke.export_tensors(runtime, contract, episode)
        opened = require_opened(config_path, config, plan).get("targets_opened") is True
        manifest["checks"] = protected_tensor_checks(manifest["checks"], opened)
        tensor_path = (
            smoke.base.episode_root(runtime, str(episode["episode_id"]))
            / "tensors"
            / "tensor_manifest.json"
        )
        evaluation.write_json(tensor_path, manifest)
        return manifest

    smoke.base.export_tensors = export_tensors


def run_parallel(
    label: str, items: Sequence[Any], workers: int, function: Callable[[Any], Any]
) -> None:
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for item in items:
            name = str(item["episode_id"]) if isinstance(item, dict) else str(item)
            print(f"{label} start {name}", flush=True)
            futures[executor.submit(function, item)] = name
        for future in as_completed(futures):
            future.result()
            print(f"{label} complete {futures[future]}", flush=True)


def artifact_paths(
    config: Mapping[str, Any], plan: Mapping[str, Any]
) -> dict[str, Path]:
    local = planner.repo_path(config["execution"]["dataset_output_root"])
    chrono = planner.repo_path(config["execution"]["chrono_output_root"])
    result: dict[str, Path] = {}
    for item in plan["episodes"]:
        episode_id = str(item["episode_id"])
        root = local / "episodes" / episode_id
        members = {
            "episode_summary": root / "episode_summary.json",
            "tensor_manifest": root / "tensors" / "tensor_manifest.json",
            "model_inputs": root / "tensors" / "model_inputs.npz",
            "targets": root / "tensors" / "targets.npz",
            "newton_manifest": root / "newton_response" / "newton_cylinder_manifest.json",
            "chrono_manifest": chrono / episode_id / "manifest.yaml",
        }
        result.update({f"{episode_id}:{name}": path for name, path in members.items()})
    return result


def summarize(
    config_path: Path,
    config: Mapping[str, Any],
    runtime: Mapping[str, Any],
    contract: Mapping[str, Any],
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    require_opened(config_path, config, plan)
    rows = [
        smoke.base.analyze_episode(runtime, contract, item)
        for item in plan["episodes"]
    ]
    counts = Counter(str(item["split"]) for item in rows)
    expected_groups = {"fresh_joint_confirmation": 24, "matched_kphi_sweep": 6}
    groups = Counter(str(item["holdout_group"]) for item in plan["episodes"])
    checks = {
        "episode_count": len(rows) == 30,
        "split_counts": counts == {"test": 24, "protected_sensitivity": 6},
        "holdout_groups": dict(groups) == expected_groups,
        "all_complete": all(item.get("complete") is True for item in rows),
        "all_admitted": all(item.get("admitted") is True for item in rows),
        "protected_open_identity": True,
    }
    passed = all(checks.values())
    artifacts = artifact_paths(config, plan)
    missing = [str(path) for path in artifacts.values() if not path.is_file()]
    if passed and missing:
        raise RuntimeError(f"direct-v4 protected artifacts are incomplete: {missing}")
    result = {
        "schema_version": 1,
        "branch_id": config["branch_id"],
        "status": "passed" if passed else "failed_or_incomplete",
        "protected_execution_plan_sha256": evaluation.sha256_file(
            execution_plan_path(config)
        ),
        "joint_unlock_sha256": evaluation.sha256_file(unlock.unlock_path(config)),
        "protected_open_sha256": evaluation.sha256_file(unlock.opened_path(config)),
        "counts": {
            "total": len(rows),
            "test": counts.get("test", 0),
            "protected_sensitivity": counts.get("protected_sensitivity", 0),
        },
        "checks": checks,
        "prediction_permitted": passed,
        "episodes": {str(item["episode_id"]): item for item in rows},
        "artifact_sha256": (
            {
                name: evaluation.sha256_file(path)
                for name, path in sorted(artifacts.items())
            }
            if passed
            else {}
        ),
    }
    evaluation.write_json(summary_path(config), result)
    return result


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = planner.load_config(config_path)
    if args.stage == "plan":
        plan = write_execution_plan(config_path, config)
        print(
            json.dumps(
                {
                    "plan": str(execution_plan_path(config)),
                    "sha256": evaluation.sha256_file(execution_plan_path(config)),
                    "counts": plan["counts"],
                    "targets_opened": False,
                },
                indent=2,
            )
        )
        return
    plan = load_execution_plan(config_path, config)
    runtime, _successor, contract, _records = context(config_path, config)
    workers = int(args.workers or plan["worker_count"])
    if workers != 2:
        raise ValueError("direct-v4 protected runtime requires two workers")
    configure_runtime_helpers(config_path, config, plan)
    episodes = choose_episodes(plan["episodes"], args.episode)
    if args.stage in ("chrono", "all"):
        mark_opened(config_path, config, plan)
        run_parallel(
            "direct-v4 protected chrono",
            episodes,
            workers,
            lambda item: smoke.run_chrono(runtime, contract, item),
        )
    else:
        require_opened(config_path, config, plan)
    seeds = sorted({int(item["initial_surface_seed"]) for item in episodes})
    if args.stage in ("bed", "all"):
        run_parallel(
            "direct-v4 protected bed",
            seeds,
            workers,
            lambda seed: smoke.base.build_bed(runtime, contract, plan, seed),
        )
    if args.stage in ("newton", "all"):
        run_parallel(
            "direct-v4 protected preparation",
            seeds,
            workers,
            lambda seed: smoke.base.prepare_prior(runtime, contract, plan, seed),
        )
        run_parallel(
            "direct-v4 protected response",
            episodes,
            workers,
            lambda item: smoke.base.run_newton(runtime, contract, plan, item),
        )
    if args.stage in ("analyze", "all"):
        result = summarize(config_path, config, runtime, contract, plan)
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
                "protected_targets_opened": unlock.opened_path(config).is_file(),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

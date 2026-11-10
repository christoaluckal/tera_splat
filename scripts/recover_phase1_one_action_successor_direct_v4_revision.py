#!/usr/bin/env python3
"""Rebind only the committed repository revision for direct-v4 continuation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import evaluate_phase1_one_action_successor as evaluation
import plan_phase1_one_action_successor_direct_v4 as planner
import run_fresh_phase0_repeatability as fresh
import run_phase1_one_action_successor_direct_v4_protected as protected


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = (
    REPO_ROOT
    / "configs"
    / "phase1_one_action_successor_direct_v4_revision_rebind_v1.json"
)
EXPECTED_ID = "phase1_one_action_successor_direct_v4_revision_rebind_v1"
TEST_PATH = (
    REPO_ROOT
    / "tests"
    / "test_recover_phase1_one_action_successor_direct_v4_revision.py"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--stage", choices=("plan", "bed", "newton", "analyze", "all"), default="plan"
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.resolve().read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_config(path: Path) -> dict[str, Any]:
    value = load_json(path)
    if value.get("schema_version") != 1 or value.get("recovery_id") != EXPECTED_ID:
        raise ValueError("unexpected direct-v4 revision-rebind identity")
    if value.get("status") != "prospective_before_bed_newton_tensor_prediction_or_scoring":
        raise ValueError("revision rebind was not frozen prospectively")
    semantics = value.get("semantics", {})
    required_true = (
        "allow_only_repository_revision_rebind",
        "require_all_non_revision_execution_keys_identical",
        "require_all_30_chrono_manifests_complete_before_freeze",
        "bind_every_completed_chrono_file_before_downstream_runtime",
        "require_downstream_artifacts_absent_before_freeze",
        "forbid_chrono_rerun",
        "preserve_frozen_protected_plan",
        "preserve_frozen_open_marker",
    )
    if not all(semantics.get(name) is True for name in required_true):
        raise ValueError("revision-rebind preservation semantics weakened")
    for name in (
        "permit_target_inspection_before_prediction",
        "permit_threshold_or_model_change",
        "permit_positive_claim",
    ):
        if semantics.get(name) is not False:
            raise ValueError(f"revision rebind requires {name}=false")
    execution = value.get("execution", {})
    if int(execution.get("workers", 0)) != 2:
        raise ValueError("revision rebind requires the frozen two-worker identity")
    if execution.get("allowed_stages") != ["bed", "newton", "analyze", "all"]:
        raise ValueError("revision rebind stage permissions changed")
    return value


def output_root(config: Mapping[str, Any]) -> Path:
    return fresh.repo_path(config["execution"]["output_root"])


def plan_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "recovery_plan.json"


def required_file(
    config: Mapping[str, Any], path_key: str, sha_key: str
) -> Path:
    path = fresh.repo_path(config[path_key])
    if not path.is_file() or evaluation.sha256_file(path) != config[sha_key]:
        raise RuntimeError(f"required {path_key} identity changed")
    return path


def direct_config_path(config: Mapping[str, Any]) -> Path:
    return required_file(
        config, "direct_v4_config", "required_direct_v4_config_sha256"
    )


def protected_plan_path(config: Mapping[str, Any]) -> Path:
    return required_file(
        config,
        "protected_execution_plan",
        "required_protected_execution_plan_sha256",
    )


def open_marker_path(config: Mapping[str, Any]) -> Path:
    return required_file(
        config,
        "protected_open_marker",
        "required_protected_open_marker_sha256",
    )


def repository_revisions(direct_config: Mapping[str, Any]) -> dict[str, str]:
    contract_path = planner.repo_path(
        load_json(planner.repo_path(direct_config["frozen_sources"]["domain_contract"]))[
            "chrono"
        ]["repo"]
    )
    return {
        "tera_splat": fresh.command_output(["git", "rev-parse", "HEAD"], REPO_ROOT),
        "tera_splat_sim": fresh.command_output(
            ["git", "rev-parse", "HEAD"], contract_path
        ),
    }


def stable_differences(
    frozen: Mapping[str, Any], current: Mapping[str, Any]
) -> list[str]:
    return [
        key
        for key in protected.STABLE_PLAN_KEYS
        if frozen.get(key) != current.get(key)
    ]


def validate_revision_only_difference(
    frozen: Mapping[str, Any],
    current: Mapping[str, Any],
    config: Mapping[str, Any],
) -> None:
    changed = stable_differences(frozen, current)
    if changed != ["repository_revisions"]:
        raise RuntimeError(
            f"direct-v4 continuation is not revision-only: {changed}"
        )
    revisions = config["repository_revisions"]
    if frozen.get("repository_revisions") != revisions["frozen"]:
        raise RuntimeError("frozen protected repository revisions changed")
    if current.get("repository_revisions") != revisions["rebound"]:
        raise RuntimeError("rebound repository revisions changed")


def file_identities(paths: Sequence[Path], base: Path) -> dict[str, str]:
    return {
        str(path.relative_to(base)): evaluation.sha256_file(path)
        for path in sorted(paths)
    }


def chrono_identities(
    direct_config: Mapping[str, Any], frozen_plan: Mapping[str, Any]
) -> dict[str, str]:
    root = planner.repo_path(direct_config["execution"]["chrono_output_root"])
    files: list[Path] = []
    for episode in frozen_plan["episodes"]:
        episode_root = root / str(episode["episode_id"])
        manifest = episode_root / "manifest.yaml"
        if not manifest.is_file():
            raise RuntimeError(f"completed Chrono manifest absent: {manifest}")
        episode_files = [path for path in episode_root.rglob("*") if path.is_file()]
        if not episode_files:
            raise RuntimeError(f"completed Chrono payload absent: {episode_root}")
        files.extend(episode_files)
    return file_identities(files, root)


def chrono_acceptance(
    direct_path: Path,
    direct_config: Mapping[str, Any],
    frozen_plan: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    runtime, _successor, contract, _records = protected.context(
        direct_path, direct_config
    )
    results: dict[str, dict[str, Any]] = {}
    for episode in frozen_plan["episodes"]:
        episode_id = str(episode["episode_id"])
        result = protected.smoke.chrono_result(runtime, contract, episode)
        if result.get("complete") is not True or result.get("accepted") is not True:
            raise RuntimeError(f"completed Chrono episode rejected: {episode_id}")
        results[episode_id] = {
            "complete": True,
            "accepted": True,
            "checks": dict(result.get("checks", {})),
            "loaded_time_s": float(result["loaded_time_s"]),
            "valid_cells": int(result["valid_cells"]),
        }
    if len(results) != 30:
        raise RuntimeError("exactly 30 accepted Chrono episodes are required")
    return results


def downstream_paths(
    direct_config: Mapping[str, Any], frozen_plan: Mapping[str, Any]
) -> list[Path]:
    dataset = planner.repo_path(direct_config["execution"]["dataset_output_root"])
    paths: list[Path] = [
        dataset / "newton_priors",
        planner.repo_path(direct_config["execution"]["output_root"])
        / "protected_dataset_summary.json",
        planner.repo_path(direct_config["execution"]["output_root"])
        / "protected_prediction_results.json",
        planner.repo_path(direct_config["execution"]["output_root"])
        / "final_evaluation_report.json",
    ]
    for seed in frozen_plan["surface_seeds"]:
        prior = dataset / "newton_priors" / f"surface_{int(seed)}"
        paths.extend(
            [
                prior / "metric_bed" / "particles_initial_mpm.ply",
                prior / "metric_bed" / "ground_plane_metadata.json",
                prior / "preparation" / "newton_prepared_bed_manifest.json",
            ]
        )
    for episode in frozen_plan["episodes"]:
        root = dataset / "episodes" / str(episode["episode_id"])
        paths.extend(
            [
                root / "newton_response",
                root / "tensors",
                root / "newton_response" / "newton_cylinder_manifest.json",
                root / "tensors" / "tensor_manifest.json",
                root / "tensors" / "model_inputs.npz",
                root / "tensors" / "targets.npz",
                root / "logs" / "newton_response.log",
                root / "episode_summary.json",
                root / "predictions",
            ]
        )
    return paths


def source_identities() -> dict[str, str]:
    return {
        "revision_rebind_runner": evaluation.sha256_file(Path(__file__).resolve()),
        "revision_rebind_tests": evaluation.sha256_file(TEST_PATH),
        "frozen_protected_runner": evaluation.sha256_file(Path(protected.__file__).resolve()),
    }


def build_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    direct_path = direct_config_path(config)
    direct_config = planner.load_config(direct_path)
    frozen_path = protected_plan_path(config)
    frozen_plan = load_json(frozen_path)
    current_plan = protected.build_execution_plan(direct_path, direct_config, False)
    validate_revision_only_difference(frozen_plan, current_plan, config)
    marker_path = open_marker_path(config)
    marker = load_json(marker_path)
    if marker.get("targets_opened") is not True:
        raise RuntimeError("protected targets were not opened by the frozen runtime")
    identities = chrono_identities(direct_config, frozen_plan)
    if len(frozen_plan["episodes"]) != 30 or not identities:
        raise RuntimeError("exactly 30 completed Chrono episodes are required")
    acceptance = chrono_acceptance(direct_path, direct_config, frozen_plan)
    present = [
        str(path)
        for path in downstream_paths(direct_config, frozen_plan)
        if path.exists()
    ]
    if present:
        raise RuntimeError(f"downstream artifacts existed before revision rebind: {present}")
    payload = {
        "schema_version": 1,
        "recovery_id": EXPECTED_ID,
        "status": "frozen_after_chrono_before_bed_newton_tensor_prediction_or_scoring",
        "config_sha256": evaluation.sha256_file(config_path.resolve()),
        "direct_v4_config_sha256": evaluation.sha256_file(direct_path),
        "protected_execution_plan_sha256": evaluation.sha256_file(frozen_path),
        "protected_open_marker_sha256": evaluation.sha256_file(marker_path),
        "changed_execution_identity_keys": stable_differences(frozen_plan, current_plan),
        "repository_revisions": config["repository_revisions"],
        "protected_episode_count": len(frozen_plan["episodes"]),
        "chrono_artifact_sha256": identities,
        "chrono_acceptance": acceptance,
        "downstream_artifacts_absent_at_freeze": True,
        "source_sha256": source_identities(),
        "execution": dict(config["execution"]),
        "semantics": dict(config["semantics"]),
        "prediction_permitted": False,
    }
    output_root(config).mkdir(parents=True, exist_ok=True)
    evaluation.write_json(plan_path(config), payload)
    return payload


def load_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    path = plan_path(config)
    if not path.is_file():
        raise RuntimeError("freeze the direct-v4 revision-rebind plan first")
    plan = load_json(path)
    if plan.get("recovery_id") != EXPECTED_ID or plan.get("status") != (
        "frozen_after_chrono_before_bed_newton_tensor_prediction_or_scoring"
    ):
        raise RuntimeError("direct-v4 revision-rebind plan identity changed")
    if plan.get("config_sha256") != evaluation.sha256_file(config_path.resolve()):
        raise RuntimeError("direct-v4 revision-rebind config changed after freeze")
    if plan.get("source_sha256") != source_identities():
        raise RuntimeError("direct-v4 revision-rebind sources changed after freeze")
    direct_path = direct_config_path(config)
    direct_config = planner.load_config(direct_path)
    frozen_plan = load_json(protected_plan_path(config))
    current_plan = protected.build_execution_plan(direct_path, direct_config, False)
    validate_revision_only_difference(frozen_plan, current_plan, config)
    if plan.get("chrono_artifact_sha256") != chrono_identities(
        direct_config, frozen_plan
    ):
        raise RuntimeError("completed Chrono artifacts changed after revision rebind")
    if plan.get("chrono_acceptance") != chrono_acceptance(
        direct_path, direct_config, frozen_plan
    ):
        raise RuntimeError("completed Chrono acceptance changed after revision rebind")
    return plan


def rebound_execution_plan(
    config_path: Path,
    config: Mapping[str, Any],
    requested_config_path: Path,
    requested_direct_config: Mapping[str, Any],
) -> dict[str, Any]:
    load_plan(config_path, config)
    expected_path = direct_config_path(config).resolve()
    if requested_config_path.resolve() != expected_path:
        raise RuntimeError("revision rebind requested an unknown direct-v4 config")
    frozen = load_json(protected_plan_path(config))
    current = protected.build_execution_plan(
        requested_config_path, requested_direct_config, False
    )
    validate_revision_only_difference(frozen, current, config)
    return frozen


def run_stage(config_path: Path, config: Mapping[str, Any], stage: str) -> None:
    if stage not in config["execution"]["allowed_stages"]:
        raise ValueError(f"revision rebind does not permit stage: {stage}")
    load_plan(config_path, config)
    direct_path = direct_config_path(config)
    original_loader = protected.load_execution_plan
    original_argv = list(sys.argv)
    protected.load_execution_plan = (
        lambda requested_path, requested_config: rebound_execution_plan(
            config_path,
            config,
            requested_path,
            requested_config,
        )
    )
    sys.argv = [
        str(Path(protected.__file__).resolve()),
        "--config",
        str(direct_path),
        "--stage",
        stage,
    ]
    try:
        protected.main()
    finally:
        sys.argv = original_argv
        protected.load_execution_plan = original_loader


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = load_config(config_path)
    if args.stage == "plan":
        result = build_plan(config_path, config)
        print(
            json.dumps(
                {
                    "plan": str(plan_path(config)),
                    "sha256": evaluation.sha256_file(plan_path(config)),
                    "changed_execution_identity_keys": result[
                        "changed_execution_identity_keys"
                    ],
                    "protected_episode_count": result["protected_episode_count"],
                    "prediction_permitted": False,
                },
                indent=2,
            )
        )
        return
    run_stage(config_path, config, args.stage)


if __name__ == "__main__":
    main()

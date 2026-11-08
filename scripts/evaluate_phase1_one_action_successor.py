#!/usr/bin/env python3
"""Freeze and score the selection-gated Phase 1 successor evaluation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = (
    REPO_ROOT / "configs" / "phase1_one_action_successor_evaluation_v1.json"
)
LEARNED_MODELS = ("D0", "R0", "R1", "R2S", "R2E")
CORE_MODELS = ("D0", "R0", "R1")
OPTIONAL_MODELS = ("R2S", "R2E")
CORRECTION_MODELS = ("R0", "R1")
BASELINES = ("no_deformation", "raw_newton")
EXPECTED_TEST_LOCK_SHA256 = (
    "0390d46bfd5860b08518f3b99ab116084f24138939c04435f29582c3feedf713"
)
EXPECTED_SENSITIVITY_LOCK_SHA256 = (
    "a003ec52f2fb43c94d5d760e06a924c3b49809a0ddf415a6abbb718ff18a4139"
)
EXPECTED_BULK_RECOVERY_ID = "phase1_one_action_successor_bulk_recovery_v2"
EXPECTED_LEGACY_BULK_SUMMARY_SHA256 = (
    "f80c9f018758438ecac0300cfc35c51e828af08a3268ba5fc791a2501f748955"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--stage", choices=("plan", "unlock", "open", "report"), default="plan"
    )
    parser.add_argument("--results", type=Path)
    return parser.parse_args()


def repo_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (REPO_ROOT / path).resolve()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_config(path: Path) -> dict[str, Any]:
    value = load_json(path.resolve())
    if value.get("schema_version") != 1:
        raise ValueError("successor evaluation schema_version must be 1")
    if value.get("evaluation_id") != "phase1_one_action_successor_evaluation_v1":
        raise ValueError("unexpected successor evaluation identity")
    if value.get("status") != "prepared_selection_gate_locked":
        raise ValueError("successor evaluation must remain selection-gate locked")
    models = value["models"]
    if tuple(models["learned"]) != LEARNED_MODELS:
        raise ValueError("successor learned-model ladder changed")
    if tuple(models["core_selection_pool"]) != CORE_MODELS:
        raise ValueError("successor core selection pool changed")
    if tuple(models["optional_ablation_pool"]) != OPTIONAL_MODELS:
        raise ValueError("successor optional ablation pool changed")
    if tuple(models["baselines"]) != BASELINES:
        raise ValueError("successor evaluation baselines changed")
    membership = value["membership"]
    if int(membership["test"]) != 24 or int(membership["protected_sensitivity"]) != 6:
        raise ValueError("successor protected membership counts changed")
    if sum(int(v) for v in membership["test_holdout_groups"].values()) != 24:
        raise ValueError("successor test holdout counts must sum to 24")
    if not all(
        bool(membership[name])
        for name in (
            "test_and_sensitivity_must_remain_locked_until_selection",
            "single_joint_unlock_marker",
            "open_once",
        )
    ):
        raise ValueError("successor protected-target governance changed")
    metrics = value["metrics"]
    if tuple(metrics["checkpoints"]) != ("loaded", "post_unload"):
        raise ValueError("successor evaluation checkpoints changed")
    if tuple(metrics["primary_regions"]) != ("footprint", "twice_radius"):
        raise ValueError("successor primary regions changed")
    if not metrics["episode_is_resampling_unit"]:
        raise ValueError("bootstrap unit must remain the whole episode")
    if int(metrics["bootstrap_resamples"]) < 1000:
        raise ValueError("successor bootstrap contract is too small")
    controls = value["parameter_controls"]
    if tuple(controls["controls"]) != (
        "kphi_shuffled",
        "kphi_constant_reference",
    ) or int(controls["shuffle_seed"]) != 20261101:
        raise ValueError("successor parameter-control identity changed")
    protected = value["protected_use"]
    if tuple(protected["directional_quantities"]) != (
        "peak_depression_m",
        "mean_depression_m",
        "displaced_volume_m3",
    ):
        raise ValueError("successor sensitivity quantities changed")
    if protected["directional_edges"] != "adjacent_kphi_pairs_within_each_force":
        raise ValueError("successor sensitivity edges changed")
    if int(protected["required_eligible_comparisons_per_model"]) != 24:
        raise ValueError("successor sensitivity comparison count changed")
    if value["execution"]["device"] != "cuda:0":
        raise ValueError("successor evaluation device changed")
    required = value["required_identity"]
    if required["test_lock_sha256"] != EXPECTED_TEST_LOCK_SHA256:
        raise ValueError("configured test lock changed")
    if required["sensitivity_lock_sha256"] != EXPECTED_SENSITIVITY_LOCK_SHA256:
        raise ValueError("configured sensitivity lock changed")
    if (
        required.get("legacy_bulk_summary_sha256")
        != EXPECTED_LEGACY_BULK_SUMMARY_SHA256
    ):
        raise ValueError("configured legacy bulk failure identity changed")
    if value.get("required_bulk_recovery_id") != EXPECTED_BULK_RECOVERY_ID:
        raise ValueError("configured bulk recovery identity changed")
    return value


def output_root(config: Mapping[str, Any]) -> Path:
    return repo_path(config["execution"]["output_root"])


def plan_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "evaluation_plan.json"


def unlock_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "protected_unlock.json"


def opened_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "protected_targets_opened.json"


def selected_membership(
    config: Mapping[str, Any], dataset_plan: Mapping[str, Any]
) -> dict[str, list[dict[str, Any]]]:
    required = config["required_identity"]
    for key in (
        "contract_sha256",
        "episode_manifest_sha256",
        "test_lock_sha256",
        "sensitivity_lock_sha256",
    ):
        if dataset_plan.get(key) != required[key]:
            raise ValueError(f"successor dataset identity changed: {key}")
    selected = {
        split: [dict(item) for item in dataset_plan.get("episodes", {}).get(split, [])]
        for split in ("test", "protected_sensitivity")
    }
    if len(selected["test"]) != int(config["membership"]["test"]):
        raise ValueError("successor test membership count changed")
    if len(selected["protected_sensitivity"]) != int(
        config["membership"]["protected_sensitivity"]
    ):
        raise ValueError("successor sensitivity membership count changed")
    all_rows = selected["test"] + selected["protected_sensitivity"]
    ids = [str(item["episode_id"]) for item in all_rows]
    if len(ids) != len(set(ids)):
        raise ValueError("protected episode identities must be unique")
    for item in all_rows:
        if item.get("split") not in selected or item.get("target_access") != "locked":
            raise ValueError("successor protected membership lock is invalid")
    groups = Counter(str(item["holdout_group"]) for item in selected["test"])
    if dict(groups) != config["membership"]["test_holdout_groups"]:
        raise ValueError("successor test holdout membership changed")
    sensitivity = selected["protected_sensitivity"]
    if {int(item["initial_surface_seed"]) for item in sensitivity} != {4301}:
        raise ValueError("protected sensitivity surface changed")
    if {str(item["holdout_group"]) for item in sensitivity} != {"matched_kphi_sweep"}:
        raise ValueError("protected sensitivity design changed")
    combinations = {
        (float(item["normal_force_n"]), float(item["soil_parameters"]["bekker_kphi"]))
        for item in sensitivity
    }
    expected = {
        (force, kphi)
        for force in (30.65625, 45.984375)
        for kphi in (1500000.0, 1750000.0, 2000000.0)
    }
    if combinations != expected:
        raise ValueError("protected sensitivity force/kphi grid changed")
    return selected


def protected_paths(
    config: Mapping[str, Any], membership: Mapping[str, Sequence[Mapping[str, Any]]]
) -> list[Path]:
    local_root = repo_path(config["execution"]["dataset_output_root"]) / "episodes"
    chrono_root = repo_path(config["execution"]["chrono_output_root"])
    return [
        root / str(item["episode_id"])
        for items in membership.values()
        for item in items
        for root in (local_root, chrono_root)
    ]


def assert_protected_targets_absent(
    config: Mapping[str, Any], membership: Mapping[str, Sequence[Mapping[str, Any]]]
) -> None:
    present = [str(path) for path in protected_paths(config, membership) if path.exists()]
    if present:
        raise RuntimeError(f"protected target artifacts exist before unlock: {present}")


def prerequisite_paths(config: Mapping[str, Any]) -> dict[str, Path]:
    return {
        "contract": repo_path(config["successor_contract"]),
        "dataset_plan": repo_path(config["dataset_plan"]),
        "bulk_summary": repo_path(config["bulk_summary"]),
        "training_config": repo_path(config["training_config"]),
        "training_plan": repo_path(config["training_plan"]),
        "normalization": repo_path(config["normalization"]),
        "selection_summary": repo_path(config["selection_summary"]),
    }


def selected_artifacts(
    config: Mapping[str, Any], selection: Mapping[str, Any]
) -> dict[str, dict[str, Any]]:
    training_config = load_json(repo_path(config["training_config"]))
    model_root = repo_path(training_config["execution"]["output_root"]) / "models"
    artifacts: dict[str, dict[str, Any]] = {}
    for variant in LEARNED_MODELS:
        card = selection["selected"][variant]
        seed = int(card["seed"])
        root = model_root / variant / f"seed_{seed}"
        paths = {
            "model_card": root / "model_card.json",
            "checkpoint": root / "model.pt",
            "history": root / "history.json",
        }
        missing = [str(path) for path in paths.values() if not path.is_file()]
        if missing:
            raise RuntimeError(f"selected successor artifacts are absent: {missing}")
        stored = load_json(paths["model_card"])
        if stored != card or stored.get("variant") != variant or int(stored["seed"]) != seed:
            raise RuntimeError(f"selected {variant} model-card identity changed")
        if stored.get("model_sha256") != sha256_file(paths["checkpoint"]):
            raise RuntimeError(f"selected {variant} checkpoint identity changed")
        if stored.get("history_sha256") != sha256_file(paths["history"]):
            raise RuntimeError(f"selected {variant} history identity changed")
        if bool(stored.get("test_targets_opened")):
            raise RuntimeError(f"selected {variant} reports protected contamination")
        artifacts[variant] = {
            "seed": seed,
            "model_card_sha256": sha256_file(paths["model_card"]),
            "checkpoint_sha256": sha256_file(paths["checkpoint"]),
            "history_sha256": sha256_file(paths["history"]),
        }
    return artifacts


def require_prerequisites(
    config: Mapping[str, Any], *, require_protected_absent: bool = True
) -> dict[str, Any]:
    paths = prerequisite_paths(config)
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise RuntimeError(f"successor evaluation prerequisites are absent: {missing}")
    if sha256_file(paths["contract"]) != config["required_identity"]["contract_sha256"]:
        raise RuntimeError("frozen successor contract identity changed")
    dataset_plan = load_json(paths["dataset_plan"])
    membership = selected_membership(config, dataset_plan)
    bulk = load_json(paths["bulk_summary"])
    expected_counts = {
        "total": 64,
        "train": 48,
        "validation": 16,
        "test": 0,
        "protected_sensitivity": 0,
    }
    if bulk.get("status") != "passed" or bulk.get("counts") != expected_counts:
        raise RuntimeError("admitted successor train/validation bulk is required")
    if bulk.get("recovery_id") != EXPECTED_BULK_RECOVERY_ID:
        raise RuntimeError("successor bulk recovery identity changed")
    if bulk.get("training_plan_freeze_permitted") is not True:
        raise RuntimeError("successor bulk does not permit model training")
    if bulk.get("test_or_protected_sensitivity_permitted") is not False:
        raise RuntimeError("successor bulk reports an opened protected boundary")
    if not bulk.get("checks", {}).get("test_and_sensitivity_targets_unopened"):
        raise RuntimeError("successor bulk protected-target lock is not intact")
    recovery_checks = bulk.get("checks", {})
    required_recovery_checks = (
        "legacy_failure_shape_preserved",
        "legacy_summary_unchanged",
        "all_artifacts_match_frozen_recovery_plan",
        "all_complete",
        "all_component_guide_checks_pass",
        "all_admitted",
    )
    if not all(
        recovery_checks.get(name) is True for name in required_recovery_checks
    ):
        raise RuntimeError("successor bulk recovery checks have not all passed")
    if recovery_checks.get("simulator_rerun_performed") is not False:
        raise RuntimeError("successor bulk recovery reran a simulator")
    if recovery_checks.get("artifact_replacement_performed") is not False:
        raise RuntimeError("successor bulk recovery replaced frozen artifacts")
    bulk_identity = bulk.get("identity", {})
    if (
        bulk_identity.get("legacy_bulk_summary_sha256")
        != EXPECTED_LEGACY_BULK_SUMMARY_SHA256
    ):
        raise RuntimeError("successor legacy bulk failure identity changed")
    reanalysis = bulk.get("reanalysis", {})
    if reanalysis.get("recovered_ids") != ["p1s_train_joint-design_019"]:
        raise RuntimeError("successor bulk recovery membership changed")
    if reanalysis.get("simulator_outputs_reused_unchanged") is not True:
        raise RuntimeError("successor bulk recovery did not preserve outputs")
    if reanalysis.get("protected_targets_opened") is not False:
        raise RuntimeError("successor bulk recovery opened protected targets")
    training_plan = load_json(paths["training_plan"])
    normalization = load_json(paths["normalization"])
    selection = load_json(paths["selection_summary"])
    if selection.get("status") != "models_selected_before_protected_unlock":
        raise RuntimeError("successor validation selection is incomplete")
    if selection.get("evaluation_plan_freeze_permitted") is not True:
        raise RuntimeError("successor selection does not permit evaluation freeze")
    if selection.get("test_targets_opened") or selection.get(
        "protected_sensitivity_targets_opened"
    ):
        raise RuntimeError("successor selection reports protected contamination")
    if tuple(selection.get("selection_pool", ())) != CORE_MODELS:
        raise RuntimeError("successor selection pool identity changed")
    if tuple(selection.get("optional_ablation_pool", ())) != OPTIONAL_MODELS:
        raise RuntimeError("successor optional ablation identity changed")
    if set(selection.get("selected", {})) != set(LEARNED_MODELS):
        raise RuntimeError("successor selection must bind all five learned variants")
    if set(selection.get("uncertainty_calibration", {})) != set(LEARNED_MODELS):
        raise RuntimeError("successor uncertainty calibration is incomplete")
    if selection.get("training_plan_sha256") != sha256_file(paths["training_plan"]):
        raise RuntimeError("successor selection references a different training plan")
    if selection.get("normalization_file_sha256") != sha256_file(paths["normalization"]):
        raise RuntimeError("successor selection references different normalization")
    artifacts = selected_artifacts(config, selection)
    if require_protected_absent:
        assert_protected_targets_absent(config, membership)
    return {
        "paths": paths,
        "dataset_plan": dataset_plan,
        "membership": membership,
        "bulk": bulk,
        "training_plan": training_plan,
        "normalization": normalization,
        "selection": selection,
        "selected_artifacts": artifacts,
    }


def source_paths(config_path: Path) -> dict[str, Path]:
    return {
        "evaluation_config": config_path.resolve(),
        "bulk_recovery_config": REPO_ROOT
        / "configs"
        / "phase1_one_action_successor_bulk_recovery_v2.json",
        "bulk_recovery_runner": REPO_ROOT
        / "scripts"
        / "recover_phase1_one_action_successor_bulk_v2.py",
        "bulk_recovery_tests": REPO_ROOT
        / "tests"
        / "test_recover_phase1_one_action_successor_bulk_v2.py",
        "successor_evaluator": Path(__file__).resolve(),
        "successor_evaluator_tests": REPO_ROOT
        / "tests"
        / "test_phase1_one_action_successor_evaluation.py",
        "protected_dataset_runner": REPO_ROOT
        / "scripts"
        / "run_phase1_one_action_successor_protected.py",
        "protected_dataset_tests": REPO_ROOT
        / "tests"
        / "test_phase1_one_action_successor_protected.py",
        "protected_predictor": REPO_ROOT
        / "scripts"
        / "predict_phase1_one_action_successor.py",
        "protected_predictor_tests": REPO_ROOT
        / "tests"
        / "test_predict_phase1_one_action_successor.py",
        "successor_trainer": REPO_ROOT / "scripts" / "train_phase1_one_action_successor.py",
        "successor_model": REPO_ROOT / "scripts" / "phase1_one_action_successor_model.py",
        "historical_evaluator": REPO_ROOT / "scripts" / "evaluate_phase1_bed_state.py",
    }


def build_plan(
    config_path: Path,
    config: Mapping[str, Any],
    *,
    require_protected_absent: bool = True,
) -> dict[str, Any]:
    prerequisite = require_prerequisites(
        config, require_protected_absent=require_protected_absent
    )
    membership = prerequisite["membership"]
    sources = source_paths(config_path)
    missing = [str(path) for path in sources.values() if not path.is_file()]
    if missing:
        raise RuntimeError(f"successor evaluation sources are absent: {missing}")
    paths = prerequisite["paths"]
    return {
        "schema_version": 1,
        "status": "frozen_after_validation_selection_before_first_protected_target",
        "evaluation_id": config["evaluation_id"],
        "config_sha256": sha256_file(config_path.resolve()),
        "source_sha256": {name: sha256_file(path) for name, path in sources.items()},
        "input_sha256": {name: sha256_file(path) for name, path in paths.items()},
        "selection_summary_sha256": sha256_file(paths["selection_summary"]),
        "training_plan_sha256": sha256_file(paths["training_plan"]),
        "normalization_sha256": sha256_file(paths["normalization"]),
        "selected_model_artifacts": prerequisite["selected_artifacts"],
        "uncertainty_calibration": prerequisite["selection"]["uncertainty_calibration"],
        "episodes": membership,
        "episode_ids": {
            split: [str(item["episode_id"]) for item in rows]
            for split, rows in membership.items()
        },
        "counts": {split: len(rows) for split, rows in membership.items()},
        "test_holdout_groups": dict(
            Counter(str(item["holdout_group"]) for item in membership["test"])
        ),
        "test_lock_sha256": config["required_identity"]["test_lock_sha256"],
        "sensitivity_lock_sha256": config["required_identity"]["sensitivity_lock_sha256"],
        "metrics": config["metrics"],
        "parameter_controls": config["parameter_controls"],
        "success_thresholds": config["success_thresholds"],
        "claim_routing": config["claim_routing"],
        "protected_targets_opened": False,
    }


STABLE_PLAN_KEYS = (
    "config_sha256",
    "source_sha256",
    "input_sha256",
    "selection_summary_sha256",
    "training_plan_sha256",
    "normalization_sha256",
    "selected_model_artifacts",
    "uncertainty_calibration",
    "episodes",
    "episode_ids",
    "counts",
    "test_holdout_groups",
    "test_lock_sha256",
    "sensitivity_lock_sha256",
    "metrics",
    "parameter_controls",
    "success_thresholds",
    "claim_routing",
    "protected_targets_opened",
)


def write_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    if unlock_path(config).exists() or opened_path(config).exists():
        raise RuntimeError("protected unlock/open marker exists before evaluation plan")
    value = build_plan(config_path, config)
    path = plan_path(config)
    if path.exists():
        existing = load_json(path)
        changed = [key for key in STABLE_PLAN_KEYS if existing.get(key) != value.get(key)]
        if changed:
            raise RuntimeError(f"refusing to replace a different evaluation plan: {changed}")
        return existing
    write_json(path, value)
    return value


def load_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    path = plan_path(config)
    if not path.is_file():
        raise RuntimeError("successor evaluation plan is absent; run selection-gated plan first")
    existing = load_json(path)
    current = build_plan(
        config_path, config, require_protected_absent=False
    )
    changed = [key for key in STABLE_PLAN_KEYS if existing.get(key) != current.get(key)]
    if changed:
        raise RuntimeError(f"locked successor evaluation identity changed: {changed}")
    return existing


def unlock_protected(config: Mapping[str, Any], plan: Mapping[str, Any]) -> dict[str, Any]:
    if opened_path(config).exists():
        raise RuntimeError("protected targets have already been opened")
    assert_protected_targets_absent(config, plan["episodes"])
    marker = {
        "schema_version": 1,
        "status": "test_and_sensitivity_generation_unlocked_after_model_selection",
        "evaluation_plan_sha256": sha256_file(plan_path(config)),
        "selection_summary_sha256": plan["selection_summary_sha256"],
        "test_lock_sha256": plan["test_lock_sha256"],
        "sensitivity_lock_sha256": plan["sensitivity_lock_sha256"],
        "test_target_count": 24,
        "protected_sensitivity_target_count": 6,
        "targets_opened": False,
    }
    path = unlock_path(config)
    if path.exists():
        existing = load_json(path)
        if existing != marker:
            raise RuntimeError("protected unlock marker identity changed")
        return existing
    write_json(path, marker)
    return marker


def require_unlocked(
    config: Mapping[str, Any], plan: Mapping[str, Any]
) -> dict[str, Any]:
    path = unlock_path(config)
    if not path.is_file():
        raise RuntimeError("protected generation remains locked")
    marker = load_json(path)
    expected = {
        "evaluation_plan_sha256": sha256_file(plan_path(config)),
        "selection_summary_sha256": plan["selection_summary_sha256"],
        "test_lock_sha256": plan["test_lock_sha256"],
        "sensitivity_lock_sha256": plan["sensitivity_lock_sha256"],
    }
    if any(marker.get(key) != value for key, value in expected.items()):
        raise RuntimeError("protected unlock marker references a different identity")
    if marker.get("status") != (
        "test_and_sensitivity_generation_unlocked_after_model_selection"
    ):
        raise RuntimeError("protected unlock marker status changed")
    return marker


def protected_artifact_paths(
    config: Mapping[str, Any], plan: Mapping[str, Any]
) -> dict[str, Path]:
    local_root = repo_path(config["execution"]["dataset_output_root"]) / "episodes"
    chrono_root = repo_path(config["execution"]["chrono_output_root"])
    paths: dict[str, Path] = {}
    for split in ("test", "protected_sensitivity"):
        for item in plan["episodes"][split]:
            episode_id = str(item["episode_id"])
            episode_root = local_root / episode_id
            members = {
                "episode_summary": episode_root / "episode_summary.json",
                "tensor_manifest": episode_root / "tensors" / "tensor_manifest.json",
                "model_inputs": episode_root / "tensors" / "model_inputs.npz",
                "targets": episode_root / "tensors" / "targets.npz",
                "newton_manifest": episode_root
                / "newton_response"
                / "newton_cylinder_manifest.json",
                "chrono_manifest": chrono_root / episode_id / "manifest.yaml",
            }
            paths.update(
                {
                    f"{split}:{episode_id}:{label}": path
                    for label, path in members.items()
                }
            )
    return paths


def mark_protected_opened(
    config: Mapping[str, Any], plan: Mapping[str, Any]
) -> dict[str, Any]:
    require_unlocked(config, plan)
    marker = {
        "schema_version": 1,
        "status": "test_and_sensitivity_targets_opened_once",
        "evaluation_plan_sha256": sha256_file(plan_path(config)),
        "unlock_sha256": sha256_file(unlock_path(config)),
        "selection_summary_sha256": plan["selection_summary_sha256"],
        "test_lock_sha256": plan["test_lock_sha256"],
        "sensitivity_lock_sha256": plan["sensitivity_lock_sha256"],
        "counts": {"test": 24, "protected_sensitivity": 6},
        "targets_opened": True,
    }
    path = opened_path(config)
    if path.exists():
        existing = load_json(path)
        if existing != marker:
            raise RuntimeError("protected open marker identity changed")
        return existing
    assert_protected_targets_absent(config, plan["episodes"])
    write_json(path, marker)
    return marker


def require_opened(
    config: Mapping[str, Any], plan: Mapping[str, Any]
) -> dict[str, Any]:
    require_unlocked(config, plan)
    path = opened_path(config)
    if not path.is_file():
        raise RuntimeError("protected targets have not been recorded as opened")
    marker = load_json(path)
    if marker.get("evaluation_plan_sha256") != sha256_file(plan_path(config)):
        raise RuntimeError("protected open marker references a different plan")
    if marker.get("unlock_sha256") != sha256_file(unlock_path(config)):
        raise RuntimeError("protected open marker references a different unlock event")
    if marker.get("selection_summary_sha256") != plan["selection_summary_sha256"]:
        raise RuntimeError("protected open marker references different selected models")
    if marker.get("targets_opened") is not True:
        raise RuntimeError("protected open marker does not record target opening")
    return marker


def protected_artifact_identity(
    config: Mapping[str, Any], plan: Mapping[str, Any]
) -> dict[str, str]:
    require_opened(config, plan)
    artifacts = protected_artifact_paths(config, plan)
    missing = [str(path) for path in artifacts.values() if not path.is_file()]
    if missing:
        raise RuntimeError(f"protected target artifacts are incomplete: {missing}")
    for split in ("test", "protected_sensitivity"):
        for item in plan["episodes"][split]:
            summary_path = (
                repo_path(config["execution"]["dataset_output_root"])
                / "episodes"
                / str(item["episode_id"])
                / "episode_summary.json"
            )
            summary = load_json(summary_path)
            if summary.get("complete") is not True or summary.get("admitted") is not True:
                raise RuntimeError(
                    f"protected episode is not complete and admitted: {item['episode_id']}"
                )
    return {name: sha256_file(path) for name, path in sorted(artifacts.items())}


def sensitivity_from_prediction_summaries(
    config: Mapping[str, Any], summaries: Sequence[Mapping[str, Any]]
) -> dict[str, dict[str, float | int]]:
    if len(summaries) != 6:
        raise RuntimeError("sensitivity prediction summary count changed")
    by_force: dict[float, list[Mapping[str, Any]]] = {}
    for summary in summaries:
        by_force.setdefault(float(summary["normal_force_n"]), []).append(summary)
    if sorted(len(rows) for rows in by_force.values()) != [3, 3]:
        raise RuntimeError("sensitivity prediction force grouping changed")
    quantities = tuple(config["protected_use"]["directional_quantities"])
    floors = config["protected_use"]["minimum_target_change"]
    matches = {model: 0 for model in LEARNED_MODELS}
    eligible = {model: 0 for model in LEARNED_MODELS}
    for rows in by_force.values():
        ordered = sorted(rows, key=lambda item: float(item["bekker_kphi"]))
        if len({float(item["bekker_kphi"]) for item in ordered}) != 3:
            raise RuntimeError("sensitivity prediction kphi grouping changed")
        for low, high in zip(ordered[:-1], ordered[1:]):
            low_values = low["directional_quantities"]
            high_values = high["directional_quantities"]
            for checkpoint in config["metrics"]["checkpoints"]:
                for quantity in quantities:
                    target_delta = float(high_values["target"][checkpoint][quantity]) - float(
                        low_values["target"][checkpoint][quantity]
                    )
                    if abs(target_delta) < float(floors[quantity]):
                        continue
                    for model in LEARNED_MODELS:
                        prediction_delta = float(
                            high_values["predictions"][model][checkpoint][quantity]
                        ) - float(
                            low_values["predictions"][model][checkpoint][quantity]
                        )
                        if not math.isfinite(prediction_delta):
                            raise RuntimeError("nonfinite sensitivity prediction quantity")
                        eligible[model] += 1
                        matches[model] += int(
                            np.sign(prediction_delta) == np.sign(target_delta)
                        )
    return {
        model: {
            "direction_fraction": (
                float(matches[model] / eligible[model])
                if eligible[model]
                else math.nan
            ),
            "eligible_comparisons": eligible[model],
        }
        for model in LEARNED_MODELS
    }


def prediction_artifact_identity(
    config: Mapping[str, Any],
    plan: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> dict[str, dict[str, str]]:
    expected_ids = {
        str(item["episode_id"])
        for split in ("test", "protected_sensitivity")
        for item in plan["episodes"][split]
    }
    declared = payload.get("prediction_artifacts", {})
    if set(declared) != expected_ids:
        raise RuntimeError("prediction artifact membership changed")
    test_ids = set(plan["episode_ids"]["test"])
    payload_rows = {
        str(item["episode_id"]): item for item in payload.get("episodes", [])
    }
    if set(payload_rows) != test_ids:
        raise RuntimeError("prediction payload test-row membership changed")
    root = repo_path(config["execution"]["dataset_output_root"]) / "episodes"
    current: dict[str, dict[str, str]] = {}
    sensitivity_summaries: list[dict[str, Any]] = []
    for episode_id in sorted(expected_ids):
        prediction_root = root / episode_id / "predictions"
        if episode_id in test_ids:
            summary = prediction_root / "successor_prediction_summary.json"
            archive = prediction_root / "successor_predictions.npz"
        else:
            summary = prediction_root / "successor_sensitivity_prediction_summary.json"
            archive = prediction_root / "successor_sensitivity_predictions.npz"
        if not summary.is_file() or not archive.is_file():
            raise RuntimeError(f"prediction artifacts are incomplete: {episode_id}")
        current[episode_id] = {
            "summary_sha256": sha256_file(summary),
            "archive_sha256": sha256_file(archive),
        }
        if current[episode_id] != declared[episode_id]:
            raise RuntimeError(f"prediction artifact identity changed: {episode_id}")
        summary_value = load_json(summary)
        if summary_value.get("evaluation_plan_sha256") != payload.get(
            "evaluation_plan_sha256"
        ):
            raise RuntimeError(f"prediction summary plan identity changed: {episode_id}")
        if summary_value.get("prediction_archive_sha256") != current[episode_id][
            "archive_sha256"
        ]:
            raise RuntimeError(f"prediction summary archive identity changed: {episode_id}")
        if episode_id in test_ids:
            reconstructed = {
                key: value
                for key, value in summary_value.items()
                if key
                not in ("evaluation_plan_sha256", "prediction_archive_sha256")
            }
            if reconstructed != payload_rows[episode_id]:
                raise RuntimeError(f"prediction payload row changed: {episode_id}")
        else:
            if summary_value.get(
                "used_for_training_normalization_calibration_or_selection"
            ) is not False:
                raise RuntimeError("protected sensitivity use boundary changed")
            sensitivity_summaries.append(summary_value)
    recomputed_sensitivity = sensitivity_from_prediction_summaries(
        config, sensitivity_summaries
    )
    if recomputed_sensitivity != payload.get("protected_sensitivity"):
        raise RuntimeError("protected sensitivity payload changed")
    return current


def bootstrap_interval(
    values: Sequence[float],
    *,
    statistic: Callable[[np.ndarray], float] = np.median,
    resamples: int,
    confidence: float,
    seed: int,
) -> dict[str, float | int]:
    data = np.asarray(values, dtype=np.float64)
    if data.ndim != 1 or data.size < 2 or not np.isfinite(data).all():
        raise ValueError("bootstrap requires at least two finite episode values")
    if resamples <= 0 or not 0.0 < confidence < 1.0:
        raise ValueError("invalid bootstrap contract")
    rng = np.random.default_rng(seed)
    sampled = data[rng.integers(0, data.size, size=(resamples, data.size))]
    estimates = np.asarray([statistic(row) for row in sampled], dtype=np.float64)
    alpha = (1.0 - confidence) / 2.0
    return {
        "estimate": float(statistic(data)),
        "lower": float(np.quantile(estimates, alpha)),
        "upper": float(np.quantile(estimates, 1.0 - alpha)),
        "episode_count": int(data.size),
    }


def paired_difference(
    candidate: Sequence[float],
    comparator: Sequence[float],
    config: Mapping[str, Any],
    seed_offset: int,
) -> dict[str, float | int]:
    first = np.asarray(candidate, dtype=np.float64)
    second = np.asarray(comparator, dtype=np.float64)
    if first.shape != second.shape:
        raise ValueError("paired metric arrays must have identical shapes")
    return bootstrap_interval(
        second - first,
        resamples=int(config["metrics"]["bootstrap_resamples"]),
        confidence=float(config["metrics"]["bootstrap_confidence"]),
        seed=int(config["metrics"]["bootstrap_seed"]) + seed_offset,
    )


def aggregate_results(
    config: Mapping[str, Any], plan: Mapping[str, Any], payload: Mapping[str, Any]
) -> dict[str, Any]:
    if payload.get("status") != "protected_predictions_complete":
        raise ValueError("successor protected predictions are incomplete")
    expected_plan_sha = sha256_file(plan_path(config))
    if payload.get("evaluation_plan_sha256") != expected_plan_sha:
        raise ValueError("prediction payload references a different evaluation plan")
    rows = [dict(item) for item in payload.get("episodes", [])]
    expected_ids = set(plan["episode_ids"]["test"])
    by_id = {str(item["episode_id"]): item for item in rows}
    if len(rows) != 24 or set(by_id) != expected_ids:
        raise ValueError("locked successor report requires the exact 24 test episodes")
    expected_group = {
        str(item["episode_id"]): str(item["holdout_group"])
        for item in plan["episodes"]["test"]
    }
    if any(str(item.get("holdout_group")) != expected_group[episode_id] for episode_id, item in by_id.items()):
        raise ValueError("test holdout group identity changed")
    checkpoints = tuple(config["metrics"]["checkpoints"])
    regions = tuple(config["metrics"]["primary_regions"])
    predictors = (*BASELINES, *LEARNED_MODELS)

    def values(
        predictor: str, checkpoint: str, region: str, group: str | None = None
    ) -> np.ndarray:
        selected = sorted(by_id.values(), key=lambda item: str(item["episode_id"]))
        if group is not None:
            selected = [item for item in selected if item["holdout_group"] == group]
        result = np.asarray(
            [item["rmse_m"][predictor][checkpoint][region] for item in selected],
            dtype=np.float64,
        )
        if result.size < 2 or not np.isfinite(result).all() or np.any(result < 0.0):
            raise ValueError("RMSE arrays must contain finite nonnegative episode values")
        return result

    for predictor in predictors:
        for checkpoint in checkpoints:
            for region in regions:
                values(predictor, checkpoint, region)

    thresholds = config["success_thresholds"]
    checks: dict[str, bool] = {}
    details: dict[str, Any] = {}
    candidate_checks: dict[str, list[bool]] = {name: [] for name in LEARNED_MODELS}
    for model_index, model in enumerate(LEARNED_MODELS):
        details[model] = {}
        for phase_index, checkpoint in enumerate(checkpoints):
            for region_index, region in enumerate(regions):
                model_values = values(model, checkpoint, region)
                raw = values("raw_newton", checkpoint, region)
                zero = values("no_deformation", checkpoint, region)
                median = float(np.median(model_values))
                raw_median = float(np.median(raw))
                reduction = 1.0 - median / raw_median if raw_median > 0.0 else -math.inf
                improvement = float(np.mean((model_values < raw) & (model_values < zero)))
                tolerance = np.maximum(
                    float(thresholds["maximum_regression_relative"]) * raw,
                    float(thresholds["maximum_regression_absolute_m"]),
                )
                no_bad_tail = bool(np.all(model_values <= raw + tolerance))
                key = f"{checkpoint}:{region}"
                interval = paired_difference(
                    model_values,
                    raw,
                    config,
                    1000 * model_index + 10 * phase_index + region_index,
                )
                local = {
                    "median_rmse_m": median,
                    "median_reduction_vs_raw_newton": reduction,
                    "episode_improvement_fraction_vs_raw_and_no_deformation": improvement,
                    "no_episode_exceeds_raw_newton_regression_tolerance": no_bad_tail,
                    "raw_newton_minus_model_rmse_m": interval,
                }
                details[model][key] = local
                gates = {
                    f"{model}:absolute:{key}": median
                    <= float(thresholds["maximum_median_rmse_m"]),
                    f"{model}:raw_reduction:{key}": reduction
                    >= float(thresholds["median_rmse_reduction_vs_raw_newton_minimum"]),
                    f"{model}:episode_fraction:{key}": improvement
                    >= float(thresholds["episode_improvement_fraction_minimum"]),
                    f"{model}:failure_tail:{key}": no_bad_tail,
                }
                checks.update(gates)
                candidate_checks[model].extend(gates.values())

    control_details: dict[str, Any] = {}
    controls = tuple(config["parameter_controls"]["controls"])
    for model_index, model in enumerate(LEARNED_MODELS):
        control_details[model] = {}
        for control_index, control in enumerate(controls):
            control_details[model][control] = {}
            for phase_index, checkpoint in enumerate(checkpoints):
                for region_index, region in enumerate(regions):
                    base_values = values(model, checkpoint, region)
                    ordered = sorted(by_id.values(), key=lambda item: str(item["episode_id"]))
                    degraded = np.asarray(
                        [
                            item["parameter_controls"][model][control][checkpoint][region]
                            for item in ordered
                        ],
                        dtype=np.float64,
                    )
                    if degraded.shape != base_values.shape or not np.isfinite(degraded).all():
                        raise ValueError("parameter-control arrays must be finite and episode matched")
                    denominator = float(np.median(base_values))
                    relative = (
                        float(np.median(degraded)) / denominator - 1.0
                        if denominator > 0.0
                        else -math.inf
                    )
                    interval = paired_difference(
                        base_values,
                        degraded,
                        config,
                        10000 + 1000 * model_index + 100 * control_index + 10 * phase_index + region_index,
                    )
                    key = f"{checkpoint}:{region}"
                    control_details[model][control][key] = {
                        "relative_median_rmse_increase": relative,
                        "control_minus_model_rmse_m": interval,
                    }
                    passed = (
                        relative >= float(config["parameter_controls"]["minimum_degradation"])
                        and float(interval["lower"]) > 0.0
                    )
                    checks[f"{model}:parameter_control:{control}:{key}"] = passed
                    candidate_checks[model].append(passed)

    coverage_details: dict[str, Any] = {}
    lower, upper = (float(v) for v in thresholds["accepted_interval_coverage_range"])
    for model_index, model in enumerate(LEARNED_MODELS):
        coverage_details[model] = {}
        for phase_index, checkpoint in enumerate(checkpoints):
            for region_index, region in enumerate(regions):
                ordered = sorted(by_id.values(), key=lambda item: str(item["episode_id"]))
                episode_coverage = [
                    float(item["coverage_fraction"][model][checkpoint][region])
                    for item in ordered
                ]
                interval = bootstrap_interval(
                    episode_coverage,
                    statistic=np.mean,
                    resamples=int(config["metrics"]["bootstrap_resamples"]),
                    confidence=float(config["metrics"]["bootstrap_confidence"]),
                    seed=int(config["metrics"]["bootstrap_seed"])
                    + 20000
                    + 100 * model_index
                    + 10 * phase_index
                    + region_index,
                )
                key = f"{checkpoint}:{region}"
                coverage_details[model][key] = interval
                passed = lower <= float(interval["estimate"]) <= upper
                checks[f"{model}:coverage:{key}"] = passed
                candidate_checks[model].append(passed)

    sensitivity = payload.get("protected_sensitivity", {})
    sensitivity_details: dict[str, Any] = {}
    for model in LEARNED_MODELS:
        item = dict(sensitivity.get(model, {}))
        fraction = float(item.get("direction_fraction", math.nan))
        count = int(item.get("eligible_comparisons", 0))
        passed = (
            math.isfinite(fraction)
            and count
            == int(config["protected_use"]["required_eligible_comparisons_per_model"])
            and fraction
            >= float(thresholds["protected_sensitivity_direction_fraction_minimum"])
        )
        sensitivity_details[model] = {
            "direction_fraction": fraction,
            "eligible_comparisons": count,
        }
        checks[f"{model}:protected_sensitivity_direction"] = passed
        candidate_checks[model].append(passed)

    model_pass = {model: all(candidate_checks[model]) for model in LEARNED_MODELS}
    added_value: dict[str, Any] = {}
    for model_index, model in enumerate(CORRECTION_MODELS):
        added_value[model] = {}
        passes = True
        for phase_index, checkpoint in enumerate(checkpoints):
            for region_index, region in enumerate(regions):
                candidate = values(model, checkpoint, region, "joint_combination")
                direct = values("D0", checkpoint, region, "joint_combination")
                margin = 1.0 - float(np.median(candidate)) / float(np.median(direct))
                interval = paired_difference(
                    candidate,
                    direct,
                    config,
                    30000 + 100 * model_index + 10 * phase_index + region_index,
                )
                passed = (
                    margin
                    >= float(thresholds["newton_added_value_joint_relative_margin_minimum"])
                    and float(interval["lower"]) > 0.0
                )
                key = f"{checkpoint}:{region}"
                added_value[model][key] = {
                    "relative_margin_vs_D0": margin,
                    "D0_minus_model_rmse_m": interval,
                    "passed": passed,
                }
                checks[f"{model}:newton_added_value:{key}"] = passed
                passes &= passed
        passes = passes and model_pass[model]
        added_value[model]["candidate_model_pass"] = model_pass[model]
        added_value[model]["passed"] = passes

    optional_value: dict[str, Any] = {}
    for model_index, model in enumerate(OPTIONAL_MODELS):
        optional_value[model] = {}
        passes = True
        for phase_index, checkpoint in enumerate(checkpoints):
            for region_index, region in enumerate(regions):
                candidate = values(model, checkpoint, region)
                robotics = values("R1", checkpoint, region)
                margin = 1.0 - float(np.median(candidate)) / float(np.median(robotics))
                interval = paired_difference(
                    candidate,
                    robotics,
                    config,
                    40000 + 100 * model_index + 10 * phase_index + region_index,
                )
                tolerance = np.maximum(
                    float(thresholds["maximum_regression_relative"]) * robotics,
                    float(thresholds["maximum_regression_absolute_m"]),
                )
                no_bad_tail = bool(np.all(candidate <= robotics + tolerance))
                passed = (
                    margin >= float(thresholds["optional_field_value_relative_margin_minimum"])
                    and float(interval["lower"]) > 0.0
                    and no_bad_tail
                )
                key = f"{checkpoint}:{region}"
                optional_value[model][key] = {
                    "relative_margin_vs_R1": margin,
                    "R1_minus_model_rmse_m": interval,
                    "no_worse_failure_tail": no_bad_tail,
                    "passed": passed,
                }
                checks[f"{model}:optional_field_value:{key}"] = passed
                passes &= passed
        passes = passes and model_pass[model]
        optional_value[model]["candidate_model_pass"] = model_pass[model]
        optional_value[model]["passed"] = passes

    passing_corrections = [model for model in CORRECTION_MODELS if model_pass[model]]
    added_corrections = [
        model for model in passing_corrections if bool(added_value[model]["passed"])
    ]
    if added_corrections:
        claim = config["claim_routing"]["R0_or_R1_passes_and_beats_D0"]
    elif passing_corrections:
        claim = config["claim_routing"]["R0_or_R1_passes_without_beating_D0"]
    elif model_pass["D0"]:
        claim = config["claim_routing"]["D0_passes"]
    else:
        claim = config["claim_routing"]["no_core_model_passes"]
    return {
        "schema_version": 1,
        "status": "passed" if claim != "no_positive_successor_claim" else "failed",
        "supported_claim_permitted": claim != "no_positive_successor_claim",
        "evaluation_id": config["evaluation_id"],
        "evaluation_plan_sha256": expected_plan_sha,
        "claim_route": claim,
        "passing_correction_models": passing_corrections,
        "newton_added_value_models": added_corrections,
        "model_pass": model_pass,
        "hypothesis_checks": checks,
        "failed_hypothesis_checks": sorted(
            name for name, passed in checks.items() if not passed
        ),
        "accuracy": details,
        "parameter_controls": control_details,
        "uncertainty_coverage": coverage_details,
        "protected_sensitivity": sensitivity_details,
        "newton_added_value": added_value,
        "optional_field_value": optional_value,
        "claim_boundary": (
            "The result concerns one held-out vertical action in the frozen synthetic "
            "domain; it does not establish sequential rollout, planner benefit, "
            "constitutive validation, named-soil calibration, or sim-to-real transfer."
        ),
    }


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = load_config(config_path)
    if args.stage == "plan":
        plan = write_plan(config_path, config)
        print(json.dumps({"plan": str(plan_path(config)), "counts": plan["counts"], "protected_targets_opened": False}, indent=2))
        return
    plan = load_plan(config_path, config)
    if args.stage == "unlock":
        marker = unlock_protected(config, plan)
        print(json.dumps(marker, indent=2))
        return
    if args.stage == "open":
        marker = mark_protected_opened(config, plan)
        print(json.dumps({"status": marker["status"], "counts": marker["counts"]}, indent=2))
        return
    if args.results is None:
        raise ValueError("--results is required for the report stage")
    artifact_identity = protected_artifact_identity(config, plan)
    payload = load_json(args.results.resolve())
    prediction_identity = prediction_artifact_identity(config, plan, payload)
    report = aggregate_results(config, plan, payload)
    report["prediction_results_sha256"] = sha256_file(args.results.resolve())
    report["protected_artifact_sha256"] = artifact_identity
    report["prediction_artifact_sha256"] = prediction_identity
    write_json(output_root(config) / "final_evaluation_report.json", report)
    print(json.dumps({"status": report["status"], "claim_route": report["claim_route"]}, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Freeze, predict, and score the direct-v4 protected confirmation."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import evaluate_phase1_one_action_successor as evaluation
import plan_phase1_one_action_successor_direct_v4 as planner
import predict_phase1_one_action_successor as prediction
import run_phase1_one_action_successor_direct_v4_protected as protected
import unlock_phase1_one_action_successor_direct_v4 as unlock
import validate_phase1_one_action_successor_direct_v2 as v2
import validate_phase1_one_action_successor_direct_v3 as v3


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = planner.DEFAULT_CONFIG
TEST_PATH = REPO_ROOT / "tests" / "test_evaluate_phase1_one_action_successor_direct_v4.py"
LEGACY_EVALUATION_CONFIG = (
    REPO_ROOT / "configs" / "phase1_one_action_successor_evaluation_v1.json"
)
CHECKPOINTS = ("loaded", "post_unload")
REGIONS = ("footprint", "twice_radius")
DIRECTIONAL_QUANTITIES = (
    "peak_depression_m",
    "mean_depression_m",
    "displaced_volume_m3",
)
MINIMUM_TARGET_CHANGE = {
    "peak_depression_m": 1.0e-9,
    "mean_depression_m": 1.0e-9,
    "displaced_volume_m3": 1.0e-12,
}
REQUIRED_ELIGIBLE_COMPARISONS = 24


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--stage", choices=("plan", "predict", "report"), default="plan")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def output_root(config: Mapping[str, Any]) -> Path:
    return planner.repo_path(config["execution"]["output_root"])


def reporting_plan_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "reporting_plan.json"


def prediction_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "protected_prediction_results.json"


def report_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "final_evaluation_report.json"


def source_paths(config_path: Path) -> dict[str, Path]:
    return {
        "config": config_path,
        "reporter": Path(__file__).resolve(),
        "reporter_tests": TEST_PATH,
        "direct_v2_validator": Path(v2.__file__).resolve(),
        "direct_v3_aggregator": Path(v3.__file__).resolve(),
        "prediction_helpers": Path(prediction.__file__).resolve(),
        "evaluation_helpers": Path(evaluation.__file__).resolve(),
        "trainer": SCRIPT_DIR / "train_phase1_one_action_successor.py",
    }


def input_paths(config: Mapping[str, Any]) -> dict[str, Path]:
    return {
        "confirmation_plan": planner.repo_path(config["execution"]["confirmation_plan"]),
        "authoritative_validation": planner.repo_path(config["validation"]["output"]),
        "joint_unlock": unlock.unlock_path(config),
        "protected_open": unlock.opened_path(config),
        "protected_execution_plan": protected.execution_plan_path(config),
        "training_plan": planner.repo_path(config["frozen_sources"]["training_plan"]),
        "normalization": planner.repo_path(config["frozen_sources"]["normalization"]),
        "selection": planner.repo_path(config["frozen_sources"]["selection"]),
        "d0_checkpoint": planner.repo_path(config["frozen_sources"]["d0_checkpoint"]),
    }


def completed_target_count(config: Mapping[str, Any]) -> int:
    chrono_root = planner.repo_path(config["execution"]["chrono_output_root"])
    dataset_root = planner.repo_path(config["execution"]["dataset_output_root"])
    chrono = len(list(chrono_root.glob("*/manifest.yaml"))) if chrono_root.exists() else 0
    tensors = (
        len(list((dataset_root / "episodes").glob("*/tensors/targets.npz")))
        if (dataset_root / "episodes").exists()
        else 0
    )
    return max(chrono, tensors)


def build_reporting_plan(
    config_path: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    execution_plan = protected.load_execution_plan(config_path, config)
    open_marker = protected.require_opened(config_path, config, execution_plan)
    if prediction_path(config).exists() or report_path(config).exists():
        raise RuntimeError("direct-v4 reporting outputs exist before protocol freeze")
    dataset_root = planner.repo_path(config["execution"]["dataset_output_root"])
    if (dataset_root / "episodes").exists() and list(
        (dataset_root / "episodes").glob("*/tensors/targets.npz")
    ):
        raise RuntimeError("freeze direct-v4 reporting before tensor target export")
    sources = source_paths(config_path)
    inputs = input_paths(config)
    missing = [str(path) for path in (*sources.values(), *inputs.values()) if not path.is_file()]
    if missing:
        raise RuntimeError(f"direct-v4 reporting identity is incomplete: {missing}")
    return {
        "schema_version": 1,
        "branch_id": config["branch_id"],
        "status": (
            "reporting_implementation_frozen_after_open_before_target_inspection_"
            "tensor_export_prediction_or_scoring"
        ),
        "source_sha256": {
            name: evaluation.sha256_file(path) for name, path in sorted(sources.items())
        },
        "input_sha256": {
            name: evaluation.sha256_file(path) for name, path in sorted(inputs.items())
        },
        "protected_execution_plan_sha256": evaluation.sha256_file(
            protected.execution_plan_path(config)
        ),
        "protected_open_sha256": evaluation.sha256_file(unlock.opened_path(config)),
        "test_lock_sha256": execution_plan["test_lock_sha256"],
        "sensitivity_lock_sha256": execution_plan["sensitivity_lock_sha256"],
        "counts": dict(execution_plan["counts"]),
        "candidate": dict(config["candidate"]),
        "confirmation_protocol": dict(config["confirmation_protocol"]),
        "success_thresholds": dict(config["success_thresholds"]),
        "protected_sensitivity_definition": {
            "directional_quantities": list(DIRECTIONAL_QUANTITIES),
            "minimum_target_change": dict(MINIMUM_TARGET_CHANGE),
            "required_eligible_comparisons": REQUIRED_ELIGIBLE_COMPARISONS,
        },
        "completed_chrono_targets_at_freeze": completed_target_count(config),
        "scientific_thresholds_precommitted_before_unlock": True,
        "target_values_inspected_before_freeze": False,
        "targets_opened": open_marker["targets_opened"],
        "prediction_complete": False,
    }


STABLE_PLAN_KEYS = (
    "source_sha256",
    "input_sha256",
    "protected_execution_plan_sha256",
    "protected_open_sha256",
    "test_lock_sha256",
    "sensitivity_lock_sha256",
    "counts",
    "candidate",
    "confirmation_protocol",
    "success_thresholds",
    "protected_sensitivity_definition",
    "completed_chrono_targets_at_freeze",
    "scientific_thresholds_precommitted_before_unlock",
    "target_values_inspected_before_freeze",
    "targets_opened",
    "prediction_complete",
)


def write_reporting_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    current = build_reporting_plan(config_path, config)
    path = reporting_plan_path(config)
    if path.is_file():
        frozen = load_json(path)
        if any(frozen.get(key) != current.get(key) for key in STABLE_PLAN_KEYS):
            raise RuntimeError("refusing changed direct-v4 reporting plan")
        return frozen
    evaluation.write_json(path, current)
    return current


def load_reporting_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    path = reporting_plan_path(config)
    if not path.is_file():
        raise RuntimeError("freeze the direct-v4 reporting protocol first")
    frozen = load_json(path)
    sources = source_paths(config_path)
    inputs = input_paths(config)
    current_sources = {
        name: evaluation.sha256_file(source) for name, source in sorted(sources.items())
    }
    current_inputs = {
        name: evaluation.sha256_file(source) for name, source in sorted(inputs.items())
    }
    if frozen.get("source_sha256") != current_sources:
        raise RuntimeError("direct-v4 reporting sources changed after freeze")
    if frozen.get("input_sha256") != current_inputs:
        raise RuntimeError("direct-v4 reporting inputs changed after freeze")
    return frozen


def dataset_context(
    config_path: Path, config: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    plan = protected.load_execution_plan(config_path, config)
    protected.require_opened(config_path, config, plan)
    summary = load_json(protected.summary_path(config))
    if summary.get("status") != "passed" or summary.get("prediction_permitted") is not True:
        raise RuntimeError("passing direct-v4 protected dataset is required")
    if summary.get("protected_execution_plan_sha256") != evaluation.sha256_file(
        protected.execution_plan_path(config)
    ):
        raise RuntimeError("direct-v4 protected dataset plan identity changed")
    return plan, summary


def episode_tensor_paths(config: Mapping[str, Any], episode_id: str) -> tuple[Path, Path]:
    root = (
        planner.repo_path(config["execution"]["dataset_output_root"])
        / "episodes"
        / episode_id
        / "tensors"
    )
    return root / "model_inputs.npz", root / "targets.npz"


def d1_prediction(
    runtime: tuple[Any, Any, dict[str, Any], Mapping[str, Any], Mapping[str, Any], Any],
    inputs: Mapping[str, np.ndarray],
    candidate: Mapping[str, Any],
    *,
    primary_kphi: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    torch, trainer, networks, normalization, _selection, device = runtime
    arrays = prediction.inference_arrays(trainer, inputs, normalization)
    condition = np.array(arrays["global_condition"], copy=True)
    if primary_kphi is not None:
        condition[3] = float(primary_kphi)
    primary, deviation = prediction.infer_network(
        torch, networks["D0"], arrays, normalization, device, global_condition=condition
    )
    reference_condition = np.array(arrays["global_condition"], copy=True)
    reference_condition[3] = float(candidate["reference_kphi_normalized"])
    reference, _ = prediction.infer_network(
        torch,
        networks["D0"],
        arrays,
        normalization,
        device,
        global_condition=reference_condition,
    )
    surface = v2.d1_surface(
        np.asarray(inputs["initial_height_m"], dtype=np.float32),
        primary,
        reference,
        gain=float(candidate["sensitivity_gain"]),
        scale=float(candidate["initial_residual_scale"]),
    )
    return surface, deviation


def coverage_tree(
    surface: np.ndarray,
    deviation: np.ndarray,
    target: np.ndarray,
    inputs: Mapping[str, np.ndarray],
    calibration: Mapping[str, Any],
) -> dict[str, dict[str, float]]:
    masks = prediction.metric_masks(inputs)
    return {
        checkpoint: {
            region: float(
                np.mean(
                    np.abs(surface[index][mask] - target[index][mask])
                    <= float(calibration[checkpoint]) * deviation[index][mask]
                )
            )
            for region, mask in masks.items()
        }
        for index, checkpoint in enumerate(CHECKPOINTS)
    }


def sensitivity_summary(
    episodes: Sequence[Mapping[str, Any]],
    inputs_by_id: Mapping[str, Mapping[str, np.ndarray]],
    targets_by_id: Mapping[str, np.ndarray],
    predictions_by_id: Mapping[str, np.ndarray],
) -> dict[str, float | int]:
    by_force: dict[float, list[Mapping[str, Any]]] = {}
    for episode in episodes:
        by_force.setdefault(float(episode["normal_force_n"]), []).append(episode)
    if sorted(len(rows) for rows in by_force.values()) != [3, 3]:
        raise RuntimeError("direct-v4 sensitivity grid changed")
    eligible = 0
    matches = 0
    for rows in by_force.values():
        ordered = sorted(rows, key=lambda item: float(item["soil_parameters"]["bekker_kphi"]))
        for low, high in zip(ordered[:-1], ordered[1:]):
            low_id, high_id = str(low["episode_id"]), str(high["episode_id"])
            for index, _checkpoint in enumerate(CHECKPOINTS):
                low_mask = prediction.metric_masks(inputs_by_id[low_id])["footprint"]
                high_mask = prediction.metric_masks(inputs_by_id[high_id])["footprint"]
                target_low = prediction.surface_quantities(
                    inputs_by_id[low_id]["initial_height_m"], targets_by_id[low_id][index], low_mask
                )
                target_high = prediction.surface_quantities(
                    inputs_by_id[high_id]["initial_height_m"], targets_by_id[high_id][index], high_mask
                )
                predicted_low = prediction.surface_quantities(
                    inputs_by_id[low_id]["initial_height_m"], predictions_by_id[low_id][index], low_mask
                )
                predicted_high = prediction.surface_quantities(
                    inputs_by_id[high_id]["initial_height_m"], predictions_by_id[high_id][index], high_mask
                )
                for quantity in DIRECTIONAL_QUANTITIES:
                    target_delta = target_high[quantity] - target_low[quantity]
                    if abs(target_delta) < MINIMUM_TARGET_CHANGE[quantity]:
                        continue
                    predicted_delta = predicted_high[quantity] - predicted_low[quantity]
                    eligible += 1
                    matches += int(np.sign(predicted_delta) == np.sign(target_delta))
    return {
        "direction_fraction": float(matches / eligible) if eligible else math.nan,
        "eligible_comparisons": eligible,
    }


def predict(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    reporting = load_reporting_plan(config_path, config)
    execution_plan, dataset_summary = dataset_context(config_path, config)
    destination = prediction_path(config)
    if destination.is_file():
        existing = load_json(destination)
        validate_prediction_artifacts(config, execution_plan, existing)
        return existing
    episodes = [dict(item) for item in execution_plan["episodes"]]
    test = [item for item in episodes if item["split"] == "test"]
    sensitivity = [item for item in episodes if item["split"] == "protected_sensitivity"]
    all_ids = [str(item["episode_id"]) for item in episodes]
    inputs_by_id: dict[str, dict[str, np.ndarray]] = {}
    targets_by_id: dict[str, np.ndarray] = {}
    for episode_id in all_ids:
        input_path, target_path = episode_tensor_paths(config, episode_id)
        inputs_by_id[episode_id] = prediction.load_npz(input_path)
        targets_by_id[episode_id] = prediction.target_surfaces(prediction.load_npz(target_path))
    legacy_config = evaluation.load_config(LEGACY_EVALUATION_CONFIG)
    legacy_plan = evaluation.load_plan(LEGACY_EVALUATION_CONFIG, legacy_config)
    inference = prediction.load_selected_runtime(legacy_config, legacy_plan)
    validation = load_json(planner.repo_path(config["validation"]["output"]))
    candidate = config["candidate"]
    test_ids = [str(item["episode_id"]) for item in test]
    shuffle = prediction.parameter_shuffle_mapping(test_ids, int(config["validation"]["shuffle_seed"]))
    rows: list[dict[str, Any]] = []
    artifacts: dict[str, dict[str, str]] = {}
    for episode in test:
        episode_id = str(episode["episode_id"])
        inputs = inputs_by_id[episode_id]
        target = targets_by_id[episode_id]
        arrays = prediction.inference_arrays(inference[1], inputs, inference[3])
        donor_arrays = prediction.inference_arrays(
            inference[1], inputs_by_id[shuffle[episode_id]], inference[3]
        )
        surface, deviation = d1_prediction(inference, inputs, candidate)
        reference, _ = d1_prediction(
            inference,
            inputs,
            candidate,
            primary_kphi=float(candidate["reference_kphi_normalized"]),
        )
        shuffled, _ = d1_prediction(
            inference,
            inputs,
            candidate,
            primary_kphi=float(donor_arrays["global_condition"][3]),
        )
        initial = np.asarray(inputs["initial_height_m"], dtype=np.float32)
        row = {
            "episode_id": episode_id,
            "holdout_group": episode["holdout_group"],
            "rmse_m": {
                "D1": prediction.rmse_tree(surface, target, inputs),
                "raw_newton": prediction.rmse_tree(arrays["hybrid"], target, inputs),
                "no_deformation": prediction.rmse_tree(np.stack((initial, initial)), target, inputs),
            },
            "parameter_controls": {
                "kphi_shuffled": prediction.rmse_tree(shuffled, target, inputs),
                "kphi_constant_reference": prediction.rmse_tree(reference, target, inputs),
            },
            "coverage_fraction": coverage_tree(
                surface,
                deviation,
                target,
                inputs,
                validation["calibration_multiplier"],
            ),
        }
        root = (
            planner.repo_path(config["execution"]["dataset_output_root"])
            / "episodes"
            / episode_id
            / "predictions"
        )
        root.mkdir(parents=True, exist_ok=False)
        archive = root / "direct_v4_predictions.npz"
        np.savez_compressed(
            archive,
            prediction_D1=surface,
            deviation_D1=deviation,
            control_kphi_shuffled=shuffled,
            control_kphi_constant_reference=reference,
        )
        summary_path = root / "direct_v4_prediction_summary.json"
        summary = {
            **row,
            "reporting_plan_sha256": evaluation.sha256_file(reporting_plan_path(config)),
            "prediction_archive_sha256": evaluation.sha256_file(archive),
        }
        evaluation.write_json(summary_path, summary)
        artifacts[episode_id] = {
            "summary_sha256": evaluation.sha256_file(summary_path),
            "archive_sha256": evaluation.sha256_file(archive),
        }
        rows.append(row)
    sensitivity_predictions: dict[str, np.ndarray] = {}
    for episode in sensitivity:
        episode_id = str(episode["episode_id"])
        surface, _deviation = d1_prediction(inference, inputs_by_id[episode_id], candidate)
        sensitivity_predictions[episode_id] = surface
        root = (
            planner.repo_path(config["execution"]["dataset_output_root"])
            / "episodes"
            / episode_id
            / "predictions"
        )
        root.mkdir(parents=True, exist_ok=False)
        archive = root / "direct_v4_sensitivity_predictions.npz"
        np.savez_compressed(archive, prediction_D1=surface)
        summary_path = root / "direct_v4_sensitivity_prediction_summary.json"
        summary = {
            "episode_id": episode_id,
            "normal_force_n": float(episode["normal_force_n"]),
            "bekker_kphi": float(episode["soil_parameters"]["bekker_kphi"]),
            "used_for_training_normalization_calibration_or_selection": False,
            "reporting_plan_sha256": evaluation.sha256_file(reporting_plan_path(config)),
            "prediction_archive_sha256": evaluation.sha256_file(archive),
        }
        evaluation.write_json(summary_path, summary)
        artifacts[episode_id] = {
            "summary_sha256": evaluation.sha256_file(summary_path),
            "archive_sha256": evaluation.sha256_file(archive),
        }
    sensitivity_result = sensitivity_summary(
        sensitivity, inputs_by_id, targets_by_id, sensitivity_predictions
    )
    payload = {
        "schema_version": 1,
        "branch_id": config["branch_id"],
        "status": "protected_predictions_complete",
        "reporting_plan_sha256": evaluation.sha256_file(reporting_plan_path(config)),
        "protected_execution_plan_sha256": evaluation.sha256_file(
            protected.execution_plan_path(config)
        ),
        "protected_dataset_summary_sha256": evaluation.sha256_file(
            protected.summary_path(config)
        ),
        "candidate": dict(candidate),
        "parameter_shuffle_mapping": shuffle,
        "parameter_shuffle_mapping_sha256": evaluation.canonical_sha256(shuffle),
        "episodes": rows,
        "protected_sensitivity": sensitivity_result,
        "prediction_artifacts": artifacts,
        "dataset_artifact_sha256": dataset_summary["artifact_sha256"],
        "reporting_protocol": reporting["confirmation_protocol"],
    }
    evaluation.write_json(destination, payload)
    return payload


def validate_prediction_artifacts(
    config: Mapping[str, Any], plan: Mapping[str, Any], payload: Mapping[str, Any]
) -> dict[str, dict[str, str]]:
    expected = {str(item["episode_id"]) for item in plan["episodes"]}
    declared = payload.get("prediction_artifacts", {})
    if set(declared) != expected:
        raise RuntimeError("direct-v4 prediction artifact membership changed")
    test_ids = {str(item["episode_id"]) for item in plan["episodes"] if item["split"] == "test"}
    rows = {str(item["episode_id"]): item for item in payload.get("episodes", [])}
    if set(rows) != test_ids:
        raise RuntimeError("direct-v4 prediction row membership changed")
    root = planner.repo_path(config["execution"]["dataset_output_root"]) / "episodes"
    current: dict[str, dict[str, str]] = {}
    for episode_id in sorted(expected):
        prediction_root = root / episode_id / "predictions"
        if episode_id in test_ids:
            summary_path = prediction_root / "direct_v4_prediction_summary.json"
            archive = prediction_root / "direct_v4_predictions.npz"
        else:
            summary_path = prediction_root / "direct_v4_sensitivity_prediction_summary.json"
            archive = prediction_root / "direct_v4_sensitivity_predictions.npz"
        current[episode_id] = {
            "summary_sha256": evaluation.sha256_file(summary_path),
            "archive_sha256": evaluation.sha256_file(archive),
        }
        if current[episode_id] != declared[episode_id]:
            raise RuntimeError(f"direct-v4 prediction artifact changed: {episode_id}")
        summary = load_json(summary_path)
        if summary.get("prediction_archive_sha256") != current[episode_id]["archive_sha256"]:
            raise RuntimeError(f"direct-v4 prediction archive changed: {episode_id}")
        if episode_id in test_ids:
            reconstructed = {
                key: value
                for key, value in summary.items()
                if key not in ("reporting_plan_sha256", "prediction_archive_sha256")
            }
            if reconstructed != rows[episode_id]:
                raise RuntimeError(f"direct-v4 prediction payload changed: {episode_id}")
    return current


def aggregate_report(config: Mapping[str, Any], payload: Mapping[str, Any]) -> dict[str, Any]:
    rows = list(payload.get("episodes", []))
    if len(rows) != 24 or len({str(row["episode_id"]) for row in rows}) != 24:
        raise RuntimeError("direct-v4 report requires exactly 24 test rows")
    result = v3.aggregate(config, rows)
    checks = dict(result["checks"])
    coverage: dict[str, Any] = {}
    lower, upper = (float(value) for value in config["success_thresholds"]["accepted_interval_coverage_range"])
    ordered = sorted(rows, key=lambda row: str(row["episode_id"]))
    for checkpoint_index, checkpoint in enumerate(CHECKPOINTS):
        for region_index, region in enumerate(REGIONS):
            values = [float(row["coverage_fraction"][checkpoint][region]) for row in ordered]
            interval = evaluation.bootstrap_interval(
                values,
                statistic=np.mean,
                resamples=int(config["validation"]["bootstrap_resamples"]),
                confidence=float(config["validation"]["bootstrap_confidence"]),
                seed=int(config["validation"]["bootstrap_seed"]) + 20000 + 10 * checkpoint_index + region_index,
            )
            key = f"{checkpoint}:{region}"
            coverage[key] = interval
            checks[f"coverage:{key}"] = lower <= float(interval["estimate"]) <= upper
    sensitivity = dict(payload.get("protected_sensitivity", {}))
    sensitivity_passed = (
        int(sensitivity.get("eligible_comparisons", 0)) == REQUIRED_ELIGIBLE_COMPARISONS
        and math.isfinite(float(sensitivity.get("direction_fraction", math.nan)))
        and float(sensitivity["direction_fraction"])
        >= float(config["success_thresholds"]["protected_sensitivity_direction_fraction_minimum"])
    )
    checks["protected_sensitivity_direction"] = sensitivity_passed
    passed = all(checks.values())
    return {
        "schema_version": 1,
        "branch_id": config["branch_id"],
        "status": "passed" if passed else "failed",
        "phase1_goal_achieved": passed,
        "supported_claim_permitted": passed,
        "claim_route": "learned_one_action_direct_surrogate" if passed else "no_positive_successor_claim",
        "candidate": dict(config["candidate"]),
        "hypothesis_checks": checks,
        "failed_hypothesis_checks": sorted(name for name, value in checks.items() if not value),
        "accuracy": result["accuracy"],
        "parameter_controls": result["parameter_controls"],
        "uncertainty_coverage": coverage,
        "protected_sensitivity": sensitivity,
        "claim_boundary": (
            "The result concerns one held-out vertical action in the frozen synthetic "
            "domain; it does not establish sequential rollout, planner benefit, "
            "constitutive validation, named-soil calibration, or sim-to-real transfer."
        ),
    }


def report(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    load_reporting_plan(config_path, config)
    execution_plan, dataset_summary = dataset_context(config_path, config)
    payload = load_json(prediction_path(config))
    identity = validate_prediction_artifacts(config, execution_plan, payload)
    result = aggregate_report(config, payload)
    result.update(
        {
            "reporting_plan_sha256": evaluation.sha256_file(reporting_plan_path(config)),
            "prediction_results_sha256": evaluation.sha256_file(prediction_path(config)),
            "protected_dataset_summary_sha256": evaluation.sha256_file(protected.summary_path(config)),
            "protected_execution_plan_sha256": evaluation.sha256_file(protected.execution_plan_path(config)),
            "prediction_artifact_sha256": identity,
            "dataset_artifact_sha256": dataset_summary["artifact_sha256"],
        }
    )
    destination = report_path(config)
    if destination.is_file():
        existing = load_json(destination)
        if existing != result:
            raise RuntimeError("refusing changed direct-v4 final report")
        return existing
    evaluation.write_json(destination, result)
    return result


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = planner.load_config(config_path)
    if args.stage == "plan":
        value = write_reporting_plan(config_path, config)
        output = {
            "plan": str(reporting_plan_path(config)),
            "sha256": evaluation.sha256_file(reporting_plan_path(config)),
            "status": value["status"],
            "completed_chrono_targets_at_freeze": value[
                "completed_chrono_targets_at_freeze"
            ],
        }
    elif args.stage == "predict":
        value = predict(config_path, config)
        output = {
            "status": value["status"],
            "test_episodes": len(value["episodes"]),
            "protected_sensitivity": value["protected_sensitivity"],
        }
    else:
        value = report(config_path, config)
        output = {
            "status": value["status"],
            "phase1_goal_achieved": value["phase1_goal_achieved"],
            "claim_route": value["claim_route"],
            "failed_hypothesis_checks": value["failed_hypothesis_checks"],
        }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

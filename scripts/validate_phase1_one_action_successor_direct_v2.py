#!/usr/bin/env python3
"""Validate the fixed D1 wrapper on the original validation split only."""

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
import predict_phase1_one_action_successor as prediction


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_direct_v2.json"
EVALUATION_CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_evaluation_v1.json"
EXPECTED_ID = "phase1_one_action_successor_direct_v2"
CHECKPOINTS = ("loaded", "post_unload")
REGIONS = ("footprint", "twice_radius")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    return parser.parse_args()


def repo_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (REPO_ROOT / path).resolve()


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.resolve().read_text(encoding="utf-8"))
    if config.get("schema_version") != 1 or config.get("branch_id") != EXPECTED_ID:
        raise ValueError("unexpected direct-v2 branch identity")
    candidate = config.get("candidate", {})
    if (
        candidate.get("name") != "D1"
        or candidate.get("base_model") != "D0_seed_20261102"
        or candidate.get("sensitivity_gain") != 1.0
        or candidate.get("initial_residual_scale") != 1.0
        or candidate.get("reference_kphi_normalized") != 0.0
        or candidate.get("no_fitting_or_gradient_updates") is not True
    ):
        raise ValueError("direct-v2 candidate definition changed")
    protocol = config.get("confirmation_protocol", {})
    if protocol.get("accuracy_regions") != list(REGIONS):
        raise ValueError("direct-v2 full-region accuracy contract changed")
    if protocol.get("parameter_control_regions") != ["footprint"]:
        raise ValueError("direct-v2 parameter-control locality changed")
    if protocol.get("revealed_v1_test_is_not_confirmation") is not True:
        raise ValueError("revealed v1 test boundary weakened")
    return config


def require_file(path: Path, expected_sha256: str, name: str) -> Path:
    if not path.is_file() or evaluation.sha256_file(path) != expected_sha256:
        raise RuntimeError(f"required direct-v2 source changed: {name}")
    return path


def require_sources(config: Mapping[str, Any]) -> None:
    for name in ("training_plan", "normalization", "selection", "d0_checkpoint"):
        require_file(
            repo_path(config["frozen_sources"][name]),
            str(config["frozen_sources"][f"{name}_sha256"]),
            name,
        )
    require_file(
        repo_path(config["antecedent"]["failed_report"]),
        str(config["antecedent"]["failed_report_sha256"]),
        "failed_report",
    )
    require_file(
        repo_path(config["antecedent"]["qualification"]),
        str(config["antecedent"]["qualification_sha256"]),
        "qualification",
    )


def d1_surface(
    initial: np.ndarray,
    primary: np.ndarray,
    reference: np.ndarray,
    *,
    gain: float,
    scale: float,
) -> np.ndarray:
    initial_two = np.stack((initial, initial)).astype(np.float32)
    result = initial_two + scale * (
        primary + gain * (primary - reference) - initial_two
    )
    if result.shape != primary.shape or not np.isfinite(result).all():
        raise ValueError("D1 surface is not finite shape-matched [2,H,W]")
    return result.astype(np.float32)


def bootstrap_interval(
    values: Sequence[float], *, resamples: int, confidence: float, seed: int
) -> dict[str, float | int]:
    return evaluation.bootstrap_interval(
        values,
        statistic=np.mean,
        resamples=resamples,
        confidence=confidence,
        seed=seed,
    )


def validation_rows(config: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    eval_config = evaluation.load_config(EVALUATION_CONFIG)
    eval_plan = evaluation.load_plan(EVALUATION_CONFIG, eval_config)
    runtime = prediction.load_selected_runtime(eval_config, eval_plan)
    torch, trainer, networks, normalization, _selection, device = runtime
    training_plan = json.loads(
        repo_path(config["frozen_sources"]["training_plan"]).read_text(encoding="utf-8")
    )
    episode_ids = list(training_plan["validation_episode_ids"])
    if len(episode_ids) != 16 or any("test" in episode_id for episode_id in episode_ids):
        raise RuntimeError("direct-v2 validation membership changed")
    shuffle = prediction.parameter_shuffle_mapping(
        episode_ids, int(config["validation"]["shuffle_seed"])
    )
    dataset_root = evaluation.repo_path(eval_config["execution"]["dataset_output_root"])
    inputs_by_id = {
        episode_id: prediction.load_npz(
            dataset_root / "episodes" / episode_id / "tensors" / "model_inputs.npz"
        )
        for episode_id in episode_ids
    }
    targets_by_id = {
        episode_id: prediction.target_surfaces(
            prediction.load_npz(
                dataset_root / "episodes" / episode_id / "tensors" / "targets.npz"
            )
        )
        for episode_id in episode_ids
    }
    network = networks["D0"]
    candidate = config["candidate"]
    rows: list[dict[str, Any]] = []
    calibration_errors = {checkpoint: [] for checkpoint in CHECKPOINTS}
    calibration_deviations = {checkpoint: [] for checkpoint in CHECKPOINTS}
    for episode_id in episode_ids:
        inputs = inputs_by_id[episode_id]
        arrays = prediction.inference_arrays(trainer, inputs, normalization)
        donor_arrays = prediction.inference_arrays(
            trainer, inputs_by_id[shuffle[episode_id]], normalization
        )
        primary, deviation = prediction.infer_network(
            torch, network, arrays, normalization, device
        )
        reference_condition = np.array(arrays["global_condition"], copy=True)
        reference_condition[3] = float(candidate["reference_kphi_normalized"])
        reference, _ = prediction.infer_network(
            torch,
            network,
            arrays,
            normalization,
            device,
            global_condition=reference_condition,
        )
        shuffled_condition = np.array(arrays["global_condition"], copy=True)
        shuffled_condition[3] = donor_arrays["global_condition"][3]
        shuffled, _ = prediction.infer_network(
            torch,
            network,
            arrays,
            normalization,
            device,
            global_condition=shuffled_condition,
        )
        initial = np.asarray(inputs["initial_height_m"], dtype=np.float32)
        gain = float(candidate["sensitivity_gain"])
        scale = float(candidate["initial_residual_scale"])
        d1 = d1_surface(initial, primary, reference, gain=gain, scale=scale)
        d1_reference = d1_surface(
            initial, reference, reference, gain=gain, scale=scale
        )
        d1_shuffled = d1_surface(
            initial, shuffled, reference, gain=gain, scale=scale
        )
        target = targets_by_id[episode_id]
        raw = arrays["hybrid"]
        zero = np.stack((initial, initial))
        masks = prediction.metric_masks(inputs)
        for index, checkpoint in enumerate(CHECKPOINTS):
            mask = masks["twice_radius"]
            calibration_errors[checkpoint].extend(
                np.abs(d1[index][mask] - target[index][mask]).astype(float).tolist()
            )
            calibration_deviations[checkpoint].extend(
                deviation[index][mask].astype(float).tolist()
            )
        rows.append(
            {
                "episode_id": episode_id,
                "rmse_m": {
                    "D1": prediction.rmse_tree(d1, target, inputs),
                    "raw_newton": prediction.rmse_tree(raw, target, inputs),
                    "no_deformation": prediction.rmse_tree(zero, target, inputs),
                },
                "parameter_controls": {
                    "kphi_shuffled": prediction.rmse_tree(
                        d1_shuffled, target, inputs
                    ),
                    "kphi_constant_reference": prediction.rmse_tree(
                        d1_reference, target, inputs
                    ),
                },
            }
        )
    calibration = {
        checkpoint: trainer.conformal_multiplier(
            np.asarray(calibration_errors[checkpoint]),
            np.asarray(calibration_deviations[checkpoint]),
            float(config["success_thresholds"]["nominal_interval_coverage"]),
        )
        for checkpoint in CHECKPOINTS
    }
    return rows, {"shuffle_mapping": shuffle, "calibration_multiplier": calibration}


def aggregate(config: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    thresholds = config["success_thresholds"]
    validation = config["validation"]
    ordered = sorted(rows, key=lambda row: str(row["episode_id"]))
    checks: dict[str, bool] = {}
    accuracy: dict[str, Any] = {}
    for checkpoint in CHECKPOINTS:
        for region in REGIONS:
            key = f"{checkpoint}:{region}"
            model = np.asarray([row["rmse_m"]["D1"][checkpoint][region] for row in ordered])
            raw = np.asarray([row["rmse_m"]["raw_newton"][checkpoint][region] for row in ordered])
            zero = np.asarray([row["rmse_m"]["no_deformation"][checkpoint][region] for row in ordered])
            median = float(np.median(model))
            reduction = 1.0 - median / float(np.median(raw))
            improvement = float(np.mean((model < raw) & (model < zero)))
            tolerance = np.maximum(
                float(thresholds["maximum_regression_relative"]) * raw,
                float(thresholds["maximum_regression_absolute_m"]),
            )
            no_bad_tail = bool(np.all(model <= raw + tolerance))
            accuracy[key] = {
                "median_rmse_m": median,
                "median_reduction_vs_raw_newton": reduction,
                "episode_improvement_fraction_vs_raw_and_no_deformation": improvement,
                "no_episode_exceeds_raw_newton_regression_tolerance": no_bad_tail,
            }
            checks[f"absolute:{key}"] = median <= float(thresholds["maximum_median_rmse_m"])
            checks[f"raw_reduction:{key}"] = reduction >= float(thresholds["median_rmse_reduction_vs_raw_newton_minimum"])
            checks[f"episode_fraction:{key}"] = improvement >= float(thresholds["episode_improvement_fraction_minimum"])
            checks[f"failure_tail:{key}"] = no_bad_tail

    controls: dict[str, Any] = {}
    for control_index, control in enumerate(("kphi_shuffled", "kphi_constant_reference")):
        controls[control] = {}
        for checkpoint_index, checkpoint in enumerate(CHECKPOINTS):
            model = np.asarray([row["rmse_m"]["D1"][checkpoint]["footprint"] for row in ordered])
            degraded = np.asarray([row["parameter_controls"][control][checkpoint]["footprint"] for row in ordered])
            relative = float(np.median(degraded)) / float(np.median(model)) - 1.0
            interval = evaluation.bootstrap_interval(
                degraded - model,
                statistic=np.mean,
                resamples=int(validation["bootstrap_resamples"]),
                confidence=float(validation["bootstrap_confidence"]),
                seed=int(validation["bootstrap_seed"]) + 100 * control_index + checkpoint_index,
            )
            controls[control][checkpoint] = {
                "relative_median_rmse_increase": relative,
                "control_minus_model_rmse_m": interval,
            }
            checks[f"parameter_control:{control}:{checkpoint}:footprint"] = (
                relative >= float(thresholds["parameter_control_minimum_degradation"])
                and float(interval["lower"]) > 0.0
            )
    return {
        "checks": checks,
        "passed": all(checks.values()),
        "accuracy": accuracy,
        "parameter_controls": controls,
    }


def validate(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    require_sources(config)
    rows, auxiliary = validation_rows(config)
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
    output = repo_path(config["validation"]["output"])
    if output.is_file():
        existing = json.loads(output.read_text(encoding="utf-8"))
        if existing != payload:
            raise RuntimeError("refusing to replace a different direct-v2 validation")
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

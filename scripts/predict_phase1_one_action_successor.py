#!/usr/bin/env python3
"""Run the selected successor ladder on the admitted protected tensor set."""

from __future__ import annotations

import argparse
import importlib
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


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = evaluation.DEFAULT_CONFIG
CHECKPOINTS = ("loaded", "post_unload")
REGIONS = ("footprint", "twice_radius")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    return parser.parse_args()


def load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as archive:
        return {name: np.array(archive[name], copy=True) for name in archive.files}


def episode_tensor_paths(
    config: Mapping[str, Any], episode_id: str
) -> tuple[Path, Path]:
    root = (
        evaluation.repo_path(config["execution"]["dataset_output_root"])
        / "episodes"
        / episode_id
        / "tensors"
    )
    return root / "model_inputs.npz", root / "targets.npz"


def parameter_shuffle_mapping(
    episode_ids: Sequence[str], seed: int
) -> dict[str, str]:
    identities = sorted(str(value) for value in episode_ids)
    if len(identities) < 2 or len(set(identities)) != len(identities):
        raise ValueError("parameter shuffle requires unique episode identities")
    rng = np.random.default_rng(seed)
    for _ in range(10_000):
        donors = list(rng.permutation(identities))
        if all(source != donor for source, donor in zip(identities, donors)):
            return dict(zip(identities, donors))
    raise RuntimeError("failed to construct deterministic parameter derangement")


def metric_masks(inputs: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
    valid = np.asarray(inputs["valid_support"], dtype=bool)
    footprint = np.asarray(inputs["action_footprint"], dtype=bool) & valid
    twice_radius = (
        np.asarray(inputs["action_signed_distance_m"], dtype=np.float64) <= 0.035
    ) & valid
    if not np.any(footprint) or not np.any(twice_radius):
        raise ValueError("successor metric regions must be nonempty")
    return {"footprint": footprint, "twice_radius": twice_radius}


def target_surfaces(targets: Mapping[str, np.ndarray]) -> np.ndarray:
    result = np.stack(
        (
            np.asarray(targets["chrono_loaded_height_m"], dtype=np.float32),
            np.asarray(targets["chrono_post_unload_height_m"], dtype=np.float32),
        )
    )
    if result.ndim != 3 or not np.isfinite(result).all():
        raise ValueError("protected target surfaces must be finite [2,H,W]")
    return result


def rmse_tree(
    prediction: np.ndarray,
    target: np.ndarray,
    inputs: Mapping[str, np.ndarray],
) -> dict[str, dict[str, float]]:
    values = np.asarray(prediction, dtype=np.float64)
    truth = np.asarray(target, dtype=np.float64)
    if values.shape != truth.shape or values.shape[0] != 2:
        raise ValueError("prediction and target surfaces must be shape matched [2,H,W]")
    masks = metric_masks(inputs)
    return {
        checkpoint: {
            region: float(
                np.sqrt(np.mean((values[index][mask] - truth[index][mask]) ** 2))
            )
            for region, mask in masks.items()
        }
        for index, checkpoint in enumerate(CHECKPOINTS)
    }


def coverage_tree(
    prediction: np.ndarray,
    deviation: np.ndarray,
    target: np.ndarray,
    inputs: Mapping[str, np.ndarray],
    calibration: Mapping[str, Any],
) -> dict[str, dict[str, float]]:
    masks = metric_masks(inputs)
    multipliers = (
        float(calibration["loaded_multiplier"]),
        float(calibration["post_unload_multiplier"]),
    )
    return {
        checkpoint: {
            region: float(
                np.mean(
                    np.abs(prediction[index][mask] - target[index][mask])
                    <= multipliers[index] * deviation[index][mask]
                )
            )
            for region, mask in masks.items()
        }
        for index, checkpoint in enumerate(CHECKPOINTS)
    }


def inference_arrays(
    trainer: Any,
    inputs: Mapping[str, np.ndarray],
    normalization: Mapping[str, Any],
) -> dict[str, np.ndarray]:
    spatial = trainer.normalized_spatial_arrays(inputs, normalization)
    global_raw = trainer.global_vector(inputs).astype(np.float32)
    global_mean = np.asarray(normalization["global_mean"], dtype=np.float32)
    global_std = np.asarray(normalization["global_std"], dtype=np.float32)
    initial = np.asarray(inputs["initial_height_m"], dtype=np.float32)
    hybrid = np.stack(
        (
            initial
            + np.asarray(inputs["newton_loaded_displacement_m"], dtype=np.float32),
            initial
            + np.asarray(
                inputs["newton_post_unload_displacement_m"], dtype=np.float32
            ),
        )
    )
    valid = np.asarray(inputs["valid_support"], dtype=bool)
    taper = trainer.boundary_taper(
        valid, int(normalization["boundary_taper_width_cells"])
    )
    return {
        "spatial": spatial,
        "global_raw": global_raw,
        "global_condition": (global_raw - global_mean) / global_std,
        "initial": initial,
        "hybrid": hybrid,
        "taper": taper,
    }


def infer_network(
    torch: Any,
    network: Any,
    arrays: Mapping[str, np.ndarray],
    normalization: Mapping[str, Any],
    device: Any,
    *,
    global_condition: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    condition = np.asarray(
        arrays["global_condition"]
        if global_condition is None
        else global_condition,
        dtype=np.float32,
    )
    base = (
        np.stack((arrays["initial"], arrays["initial"]))
        if network.base_state == "initial"
        else arrays["hybrid"]
    )
    with torch.no_grad():
        result = network(
            torch.from_numpy(np.asarray(arrays["spatial"], dtype=np.float32))[None].to(device),
            torch.from_numpy(condition)[None].to(device),
            torch.from_numpy(np.asarray(base, dtype=np.float32))[None].to(device),
            torch.tensor(
                normalization["correction_scale_m"],
                dtype=torch.float32,
                device=device,
            ),
            torch.from_numpy(np.asarray(arrays["taper"], dtype=np.float32))[None, None].to(device),
        )
    prediction = result["height_m"][0].detach().cpu().numpy().astype(np.float32)
    deviation = (
        torch.exp(0.5 * result["log_variance_m2"])[0]
        .detach()
        .cpu()
        .numpy()
        .astype(np.float32)
    )
    return prediction, deviation


def load_selected_runtime(
    config: Mapping[str, Any], plan: Mapping[str, Any]
) -> tuple[Any, Any, dict[str, Any], Mapping[str, Any], Mapping[str, Any], Any]:
    torch = importlib.import_module("torch")
    trainer = importlib.import_module("train_phase1_one_action_successor")
    training_config = trainer.load_config(evaluation.repo_path(config["training_config"]))
    normalization = json.loads(
        evaluation.repo_path(config["normalization"]).read_text(encoding="utf-8")
    )
    selection = json.loads(
        evaluation.repo_path(config["selection_summary"]).read_text(encoding="utf-8")
    )
    device = torch.device(config["execution"]["device"])
    model_root = evaluation.repo_path(config["selection_summary"]).parent / "models"
    networks: dict[str, Any] = {}
    for variant in evaluation.LEARNED_MODELS:
        selected = plan["selected_model_artifacts"][variant]
        checkpoint_path = model_root / variant / f"seed_{int(selected['seed'])}" / "model.pt"
        if evaluation.sha256_file(checkpoint_path) != selected["checkpoint_sha256"]:
            raise RuntimeError(f"selected successor checkpoint changed: {variant}")
        network = trainer.base.instantiate_network(training_config, variant, device)
        checkpoint = torch.load(checkpoint_path, map_location=device)
        if checkpoint.get("variant") != variant:
            raise RuntimeError(f"successor checkpoint variant changed: {variant}")
        network.load_state_dict(checkpoint["state_dict"], strict=True)
        network.eval()
        networks[variant] = network
    return torch, trainer, networks, normalization, selection, device


def prediction_set(
    runtime: tuple[Any, Any, dict[str, Any], Mapping[str, Any], Mapping[str, Any], Any],
    inputs: Mapping[str, np.ndarray],
    *,
    control_conditions: Mapping[str, np.ndarray] | None = None,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    torch, trainer, networks, normalization, _selection, device = runtime
    arrays = inference_arrays(trainer, inputs, normalization)
    predictions: dict[str, np.ndarray] = {}
    deviations: dict[str, np.ndarray] = {}
    for variant, network in networks.items():
        prediction, deviation = infer_network(
            torch,
            network,
            arrays,
            normalization,
            device,
            global_condition=(
                None if control_conditions is None else control_conditions[variant]
            ),
        )
        predictions[variant] = prediction
        deviations[variant] = deviation
    return predictions, deviations


def surface_quantities(
    initial: np.ndarray, surface: np.ndarray, footprint: np.ndarray
) -> dict[str, float]:
    depression = np.maximum(
        np.asarray(initial, dtype=np.float64) - np.asarray(surface, dtype=np.float64),
        0.0,
    )[footprint]
    return {
        "peak_depression_m": float(np.max(depression)),
        "mean_depression_m": float(np.mean(depression)),
        "displaced_volume_m3": float(np.sum(depression) * 0.005**2),
    }


def sensitivity_direction_summary(
    config: Mapping[str, Any],
    episodes: Sequence[Mapping[str, Any]],
    inputs_by_id: Mapping[str, Mapping[str, np.ndarray]],
    targets_by_id: Mapping[str, np.ndarray],
    predictions_by_id: Mapping[str, Mapping[str, np.ndarray]],
) -> dict[str, dict[str, float | int]]:
    by_force: dict[float, list[Mapping[str, Any]]] = {}
    for episode in episodes:
        by_force.setdefault(float(episode["normal_force_n"]), []).append(episode)
    if sorted(len(rows) for rows in by_force.values()) != [3, 3]:
        raise ValueError("protected sensitivity must contain two three-point force sweeps")
    quantities = tuple(config["protected_use"]["directional_quantities"])
    floors = config["protected_use"]["minimum_target_change"]
    matches = {model: 0 for model in evaluation.LEARNED_MODELS}
    eligible = {model: 0 for model in evaluation.LEARNED_MODELS}
    for rows in by_force.values():
        ordered = sorted(rows, key=lambda item: float(item["soil_parameters"]["bekker_kphi"]))
        for low, high in zip(ordered[:-1], ordered[1:]):
            low_id, high_id = str(low["episode_id"]), str(high["episode_id"])
            for phase_index, _checkpoint in enumerate(CHECKPOINTS):
                input_low = inputs_by_id[low_id]
                input_high = inputs_by_id[high_id]
                mask_low = metric_masks(input_low)["footprint"]
                mask_high = metric_masks(input_high)["footprint"]
                target_low = surface_quantities(
                    input_low["initial_height_m"], targets_by_id[low_id][phase_index], mask_low
                )
                target_high = surface_quantities(
                    input_high["initial_height_m"], targets_by_id[high_id][phase_index], mask_high
                )
                for model in evaluation.LEARNED_MODELS:
                    pred_low = surface_quantities(
                        input_low["initial_height_m"], predictions_by_id[low_id][model][phase_index], mask_low
                    )
                    pred_high = surface_quantities(
                        input_high["initial_height_m"], predictions_by_id[high_id][model][phase_index], mask_high
                    )
                    for quantity in quantities:
                        target_delta = target_high[quantity] - target_low[quantity]
                        if abs(target_delta) < float(floors[quantity]):
                            continue
                        prediction_delta = pred_high[quantity] - pred_low[quantity]
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
        for model in evaluation.LEARNED_MODELS
    }


def predict(config: Mapping[str, Any], plan: Mapping[str, Any]) -> dict[str, Any]:
    evaluation.protected_artifact_identity(config, plan)
    destination = evaluation.output_root(config) / "protected_prediction_results.json"
    if destination.is_file():
        existing = json.loads(destination.read_text(encoding="utf-8"))
        if existing.get("status") != "protected_predictions_complete" or existing.get(
            "evaluation_plan_sha256"
        ) != evaluation.sha256_file(evaluation.plan_path(config)):
            raise RuntimeError("existing protected prediction payload identity changed")
        evaluation.prediction_artifact_identity(config, plan, existing)
        return existing
    dataset_summary_path = evaluation.output_root(config) / "protected_dataset_summary.json"
    if not dataset_summary_path.is_file():
        raise RuntimeError("passing protected dataset summary is required before prediction")
    dataset_summary = json.loads(dataset_summary_path.read_text(encoding="utf-8"))
    if dataset_summary.get("status") != "passed" or dataset_summary.get(
        "prediction_permitted"
    ) is not True:
        raise RuntimeError("protected dataset does not permit prediction")
    if dataset_summary.get("evaluation_plan_sha256") != evaluation.sha256_file(
        evaluation.plan_path(config)
    ):
        raise RuntimeError("protected dataset references a different evaluation plan")
    all_episodes = {
        str(item["episode_id"]): dict(item)
        for split in ("test", "protected_sensitivity")
        for item in plan["episodes"][split]
    }
    dataset_root = evaluation.repo_path(config["execution"]["dataset_output_root"])
    for episode_id in all_episodes:
        root = dataset_root / "episodes" / episode_id / "predictions"
        names = (
            ("successor_prediction_summary.json", "successor_predictions.npz")
            if episode_id in set(plan["episode_ids"]["test"])
            else (
                "successor_sensitivity_prediction_summary.json",
                "successor_sensitivity_predictions.npz",
            )
        )
        if any((root / name).exists() for name in names):
            raise RuntimeError(
                f"incomplete protected prediction output exists: {episode_id}"
            )
    inputs_by_id: dict[str, dict[str, np.ndarray]] = {}
    targets_by_id: dict[str, np.ndarray] = {}
    for episode_id in all_episodes:
        input_path, target_path = episode_tensor_paths(config, episode_id)
        inputs_by_id[episode_id] = load_npz(input_path)
        targets_by_id[episode_id] = target_surfaces(load_npz(target_path))
    runtime = load_selected_runtime(config, plan)
    _torch, trainer, _networks, normalization, selection, _device = runtime
    test_ids = list(plan["episode_ids"]["test"])
    shuffle = parameter_shuffle_mapping(
        test_ids, int(config["parameter_controls"]["shuffle_seed"])
    )
    rows: list[dict[str, Any]] = []
    prediction_artifacts: dict[str, Any] = {}
    for episode_id in test_ids:
        inputs = inputs_by_id[episode_id]
        target = targets_by_id[episode_id]
        predictions, deviations = prediction_set(runtime, inputs)
        base_arrays = inference_arrays(trainer, inputs, normalization)
        donor_arrays = inference_arrays(
            trainer, inputs_by_id[shuffle[episode_id]], normalization
        )
        controls: dict[str, dict[str, dict[str, dict[str, float]]]] = {}
        control_predictions: dict[str, np.ndarray] = {}
        for control in ("kphi_shuffled", "kphi_constant_reference"):
            conditions = {}
            for model in evaluation.LEARNED_MODELS:
                condition = np.array(base_arrays["global_condition"], copy=True)
                condition[3] = (
                    donor_arrays["global_condition"][3]
                    if control == "kphi_shuffled"
                    else 0.0
                )
                conditions[model] = condition
            predicted, _deviation = prediction_set(
                runtime, inputs, control_conditions=conditions
            )
            for model in evaluation.LEARNED_MODELS:
                controls.setdefault(model, {})[control] = rmse_tree(
                    predicted[model], target, inputs
                )
                control_predictions[f"{model}_{control}"] = predicted[model]
        initial = np.asarray(inputs["initial_height_m"], dtype=np.float32)
        baselines = {
            "no_deformation": np.stack((initial, initial)),
            "raw_newton": base_arrays["hybrid"],
        }
        row = {
            "episode_id": episode_id,
            "holdout_group": all_episodes[episode_id]["holdout_group"],
            "rmse_m": {
                **{
                    name: rmse_tree(surface, target, inputs)
                    for name, surface in baselines.items()
                },
                **{
                    model: rmse_tree(predictions[model], target, inputs)
                    for model in evaluation.LEARNED_MODELS
                },
            },
            "parameter_controls": controls,
            "coverage_fraction": {
                model: coverage_tree(
                    predictions[model],
                    deviations[model],
                    target,
                    inputs,
                    selection["uncertainty_calibration"][model],
                )
                for model in evaluation.LEARNED_MODELS
            },
        }
        root = (
            evaluation.repo_path(config["execution"]["dataset_output_root"])
            / "episodes"
            / episode_id
            / "predictions"
        )
        archive = root / "successor_predictions.npz"
        root.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            archive,
            **{f"prediction_{name}": value for name, value in predictions.items()},
            **{f"deviation_{name}": value for name, value in deviations.items()},
            **{f"control_{name}": value for name, value in control_predictions.items()},
        )
        summary_path = root / "successor_prediction_summary.json"
        summary = {
            **row,
            "evaluation_plan_sha256": evaluation.sha256_file(
                evaluation.plan_path(config)
            ),
            "prediction_archive_sha256": evaluation.sha256_file(archive),
        }
        evaluation.write_json(summary_path, summary)
        prediction_artifacts[episode_id] = {
            "summary_sha256": evaluation.sha256_file(summary_path),
            "archive_sha256": evaluation.sha256_file(archive),
        }
        rows.append(row)
    sensitivity_predictions: dict[str, dict[str, np.ndarray]] = {}
    for episode in plan["episodes"]["protected_sensitivity"]:
        episode_id = str(episode["episode_id"])
        sensitivity_predictions[episode_id], _deviation = prediction_set(
            runtime, inputs_by_id[episode_id]
        )
        root = (
            evaluation.repo_path(config["execution"]["dataset_output_root"])
            / "episodes"
            / episode_id
            / "predictions"
        )
        root.mkdir(parents=True, exist_ok=True)
        archive = root / "successor_sensitivity_predictions.npz"
        np.savez_compressed(
            archive,
            **{
                f"prediction_{model}": surface
                for model, surface in sensitivity_predictions[episode_id].items()
            },
        )
        summary_path = root / "successor_sensitivity_prediction_summary.json"
        sensitivity_inputs = inputs_by_id[episode_id]
        sensitivity_target = targets_by_id[episode_id]
        footprint = metric_masks(sensitivity_inputs)["footprint"]
        summary = {
            "episode_id": episode_id,
            "normal_force_n": float(episode["normal_force_n"]),
            "bekker_kphi": float(episode["soil_parameters"]["bekker_kphi"]),
            "evaluation_plan_sha256": evaluation.sha256_file(
                evaluation.plan_path(config)
            ),
            "prediction_archive_sha256": evaluation.sha256_file(archive),
            "used_for_training_normalization_calibration_or_selection": False,
            "directional_quantities": {
                "target": {
                    checkpoint: surface_quantities(
                        sensitivity_inputs["initial_height_m"],
                        sensitivity_target[index],
                        footprint,
                    )
                    for index, checkpoint in enumerate(CHECKPOINTS)
                },
                "predictions": {
                    model: {
                        checkpoint: surface_quantities(
                            sensitivity_inputs["initial_height_m"],
                            surface[index],
                            footprint,
                        )
                        for index, checkpoint in enumerate(CHECKPOINTS)
                    }
                    for model, surface in sensitivity_predictions[episode_id].items()
                },
            },
        }
        evaluation.write_json(summary_path, summary)
        prediction_artifacts[episode_id] = {
            "summary_sha256": evaluation.sha256_file(summary_path),
            "archive_sha256": evaluation.sha256_file(archive),
        }
    sensitivity = sensitivity_direction_summary(
        config,
        plan["episodes"]["protected_sensitivity"],
        inputs_by_id,
        targets_by_id,
        sensitivity_predictions,
    )
    payload = {
        "schema_version": 1,
        "status": "protected_predictions_complete",
        "evaluation_plan_sha256": evaluation.sha256_file(
            evaluation.plan_path(config)
        ),
        "protected_dataset_summary_sha256": evaluation.sha256_file(
            dataset_summary_path
        ),
        "parameter_shuffle_mapping": shuffle,
        "parameter_shuffle_mapping_sha256": evaluation.canonical_sha256(shuffle),
        "episodes": rows,
        "protected_sensitivity": sensitivity,
        "prediction_artifacts": prediction_artifacts,
    }
    evaluation.write_json(destination, payload)
    return payload


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = evaluation.load_config(config_path)
    plan = evaluation.load_plan(config_path, config)
    evaluation.require_opened(config, plan)
    payload = predict(config, plan)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "test_episodes": len(payload["episodes"]),
                "protected_sensitivity": payload["protected_sensitivity"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

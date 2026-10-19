#!/usr/bin/env python3
"""Train and evaluate the first fresh Phase 0 particle residual pilot.

The model is intentionally small.  It learns a bounded, action-aligned vertical
displacement field from Chrono-observable geometry, then lifts that field onto
the saved Newton particles with a depth taper.  Validation and test actions are
never used to fit or select the model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from scipy.spatial import cKDTree

from particle_io import write_particle_ply


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX_ROOT = (
    REPO_ROOT
    / "outputs/validity_experiment/newton/static_proxy_hierarchical_v3_20261017/matrix"
)
MODEL_ID = "phase0_action_aligned_particle_mlp_v1_20261018"
FEATURE_NAMES = (
    "foot_relative_x_over_radius",
    "foot_relative_y_over_radius",
    "radial_distance_over_radius",
    "signed_foot_distance_over_radius",
    "phase_loaded_minus1_post_unload_plus1",
    "newton_response_m",
    "initial_alignment_error_m",
    "normal_force_over_30p65625n",
)
PHASES = ("loaded", "residual")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix-root", type=Path, default=DEFAULT_MATRIX_ROOT)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--stage", choices=("train", "evaluate", "all"), default="all")
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--hidden-width", type=int, default=24)
    parser.add_argument("--epochs", type=int, default=3000)
    parser.add_argument("--learning-rate", type=float, default=0.01)
    parser.add_argument("--l2", type=float, default=1.0e-5)
    parser.add_argument("--max-correction-m", type=float, default=0.05)
    parser.add_argument("--particle-depth-scale-m", type=float, default=0.02)
    parser.add_argument("--seed", type=int, default=20261018)
    return parser.parse_args()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_plan(matrix_root: Path) -> dict[str, Any]:
    path = matrix_root / "matrix_plan.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing frozen matrix plan: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def case_by_id(plan: dict[str, Any], case_id: str) -> dict[str, Any]:
    for case in plan["cases"]:
        if case["case_id"] == case_id:
            return case
    raise KeyError(case_id)


def split_for_case(plan: dict[str, Any], case_id: str) -> str:
    for split, ids in plan["episode_split"].items():
        if case_id in ids:
            return split
    raise KeyError(f"No split declared for {case_id}")


def spatial_case_ids(plan: dict[str, Any]) -> list[str]:
    return list(plan["rungs"]["spatial31"])


def require_case(matrix_root: Path, case_id: str) -> dict[str, Any]:
    summary_path = matrix_root / "cases" / case_id / "case_summary.json"
    if not summary_path.is_file():
        raise RuntimeError(f"Fresh case is incomplete: {case_id}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if not summary.get("complete") or not summary.get("pipeline_usable"):
        raise RuntimeError(f"Fresh case is not pipeline-usable: {case_id}")
    return summary


def case_paths(matrix_root: Path, case_id: str) -> tuple[Path, Path]:
    summary = require_case(matrix_root, case_id)
    return Path(summary["artifacts"]["chrono_episode"]), Path(
        summary["artifacts"]["newton_response"]
    )


def load_case_fields(
    matrix_root: Path, plan: dict[str, Any], case_id: str, phase: str
) -> dict[str, Any]:
    case = case_by_id(plan, case_id)
    chrono_dir, response_dir = case_paths(matrix_root, case_id)
    manifest = yaml.safe_load((chrono_dir / "manifest.yaml").read_text(encoding="utf-8"))
    initial_name = manifest["states"]["initial"]
    target_name = manifest["states"][phase]
    chrono_initial = np.load(chrono_dir / initial_name, allow_pickle=False).astype(np.float64)
    target = np.load(chrono_dir / target_name, allow_pickle=False).astype(np.float64)
    newton_initial = np.load(
        response_dir / "initial_heightmap_m.npy", allow_pickle=False
    ).astype(np.float64)
    prior = np.load(
        response_dir / f"{phase}_heightmap_m.npy", allow_pickle=False
    ).astype(np.float64)
    mask_name = str(manifest["heightmap"]["valid_mask"]).split(";", 1)[0].strip()
    valid = np.load(chrono_dir / mask_name, allow_pickle=False).astype(bool)
    valid &= np.load(
        response_dir / "valid_heightmap_mask.npy", allow_pickle=False
    ).astype(bool)
    rows, columns = target.shape
    spacing = float(manifest["heightmap"]["spacing_m"])
    origin_x, origin_y = (float(value) for value in manifest["heightmap"]["origin_xy_m"])
    grid_x, grid_y = np.meshgrid(
        origin_x + np.arange(columns) * spacing,
        origin_y + np.arange(rows) * spacing,
    )
    center_x, center_y = (float(value) for value in case["center_xy_m"])
    radius = float(case["radius_m"])
    dx = (grid_x - center_x) / radius
    dy = (grid_y - center_y) / radius
    radial = np.sqrt(np.square(dx) + np.square(dy))
    local = radial <= 2.0 + 1.0e-12
    phase_value = -1.0 if phase == "loaded" else 1.0
    force = float(case["normal_force_n"]) / 30.65625
    features = np.stack(
        (
            dx,
            dy,
            radial,
            radial - 1.0,
            np.full_like(dx, phase_value),
            prior - newton_initial,
            chrono_initial - newton_initial,
            np.full_like(dx, force),
        ),
        axis=-1,
    )
    finite = (
        valid
        & local
        & np.isfinite(chrono_initial)
        & np.isfinite(target)
        & np.isfinite(newton_initial)
        & np.isfinite(prior)
        & np.all(np.isfinite(features), axis=-1)
    )
    taper = radial_taper(radial)
    return {
        "case": case,
        "phase": phase,
        "chrono_dir": chrono_dir,
        "response_dir": response_dir,
        "manifest": manifest,
        "chrono_initial": chrono_initial,
        "target": target,
        "newton_initial": newton_initial,
        "prior": prior,
        "valid": valid,
        "features": features,
        "local": local,
        "finite_local": finite,
        "taper": taper,
        "grid_x": grid_x,
        "grid_y": grid_y,
        "spacing": spacing,
        "radius": radius,
        "radial": radial,
    }


def radial_taper(radial_over_radius: np.ndarray) -> np.ndarray:
    result = np.zeros_like(radial_over_radius, dtype=np.float64)
    result[radial_over_radius <= 1.5] = 1.0
    transition = (radial_over_radius > 1.5) & (radial_over_radius < 2.0)
    fraction = (radial_over_radius[transition] - 1.5) / 0.5
    result[transition] = 0.5 * (1.0 + np.cos(np.pi * fraction))
    return result


def training_arrays(
    matrix_root: Path, plan: dict[str, Any], train_ids: list[str]
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    xs: list[np.ndarray] = []
    ys: list[np.ndarray] = []
    tapers: list[np.ndarray] = []
    weights: list[np.ndarray] = []
    for case_id in train_ids:
        for phase in PHASES:
            fields = load_case_fields(matrix_root, plan, case_id, phase)
            mask = fields["finite_local"]
            xs.append(fields["features"][mask])
            ys.append((fields["target"] - fields["prior"])[mask])
            tapers.append(fields["taper"][mask])
            weights.append(np.where(fields["radial"][mask] <= 1.0, 2.0, 1.0))
    return (
        np.concatenate(xs),
        np.concatenate(ys),
        np.concatenate(tapers),
        np.concatenate(weights),
    )


def initialize_model(
    features: np.ndarray,
    hidden_width: int,
    max_correction_m: float,
    seed: int,
) -> dict[str, np.ndarray]:
    mean = np.mean(features, axis=0)
    std = np.std(features, axis=0)
    std[std < 1.0e-8] = 1.0
    rng = np.random.default_rng(seed)
    return {
        "feature_mean": mean,
        "feature_std": std,
        "w1": rng.normal(0.0, 1.0 / np.sqrt(features.shape[1]), (features.shape[1], hidden_width)),
        "b1": np.zeros(hidden_width, dtype=np.float64),
        "w2": np.zeros((hidden_width, 1), dtype=np.float64),
        "b2": np.zeros(1, dtype=np.float64),
        "max_correction_m": np.asarray(max_correction_m, dtype=np.float64),
    }


def predict(model: dict[str, np.ndarray], features: np.ndarray, taper: np.ndarray) -> np.ndarray:
    normalized = (features - model["feature_mean"]) / model["feature_std"]
    hidden = np.tanh(normalized @ model["w1"] + model["b1"])
    bounded = np.tanh(hidden @ model["w2"] + model["b2"]).reshape(-1)
    return float(model["max_correction_m"]) * taper * bounded


def fit_model(
    features: np.ndarray,
    targets_m: np.ndarray,
    taper: np.ndarray,
    sample_weight: np.ndarray,
    *,
    hidden_width: int,
    epochs: int,
    learning_rate: float,
    l2: float,
    max_correction_m: float,
    seed: int,
) -> tuple[dict[str, np.ndarray], list[dict[str, float]]]:
    model = initialize_model(features, hidden_width, max_correction_m, seed)
    x = (features - model["feature_mean"]) / model["feature_std"]
    target = targets_m / max_correction_m
    weight = sample_weight / np.mean(sample_weight)
    parameters = ("w1", "b1", "w2", "b2")
    first = {name: np.zeros_like(model[name]) for name in parameters}
    second = {name: np.zeros_like(model[name]) for name in parameters}
    history: list[dict[str, float]] = []
    beta1, beta2 = 0.9, 0.999
    for epoch in range(1, epochs + 1):
        hidden = np.tanh(x @ model["w1"] + model["b1"])
        raw = hidden @ model["w2"] + model["b2"]
        bounded = np.tanh(raw).reshape(-1)
        prediction = taper * bounded
        error = prediction - target
        data_loss = float(np.mean(weight * np.square(error)))
        reg_loss = l2 * float(np.sum(np.square(model["w1"])) + np.sum(np.square(model["w2"])))
        output_grad = (
            2.0
            * weight
            * error
            / features.shape[0]
            * taper
            * (1.0 - np.square(bounded))
        )[:, None]
        gradients = {
            "w2": hidden.T @ output_grad + 2.0 * l2 * model["w2"],
            "b2": np.sum(output_grad, axis=0),
        }
        hidden_grad = (output_grad @ model["w2"].T) * (1.0 - np.square(hidden))
        gradients["w1"] = x.T @ hidden_grad + 2.0 * l2 * model["w1"]
        gradients["b1"] = np.sum(hidden_grad, axis=0)
        for name in parameters:
            first[name] = beta1 * first[name] + (1.0 - beta1) * gradients[name]
            second[name] = beta2 * second[name] + (1.0 - beta2) * np.square(gradients[name])
            first_hat = first[name] / (1.0 - beta1**epoch)
            second_hat = second[name] / (1.0 - beta2**epoch)
            model[name] -= learning_rate * first_hat / (np.sqrt(second_hat) + 1.0e-8)
        if epoch == 1 or epoch % 100 == 0 or epoch == epochs:
            history.append(
                {
                    "epoch": epoch,
                    "normalized_data_mse": data_loss,
                    "regularization": reg_loss,
                    "rmse_m": float(np.sqrt(np.mean(np.square(max_correction_m * error)))),
                }
            )
    return model, history


def save_model(path: Path, model: dict[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        schema_version=np.asarray(1, dtype=np.int64),
        model_id=np.asarray(MODEL_ID),
        feature_names=np.asarray(FEATURE_NAMES),
        **model,
    )


def load_model(path: Path) -> dict[str, np.ndarray]:
    archive = np.load(path, allow_pickle=False)
    if str(archive["model_id"]) != MODEL_ID:
        raise RuntimeError(f"Unexpected model id in {path}")
    return {name: archive[name] for name in ("feature_mean", "feature_std", "w1", "b1", "w2", "b2", "max_correction_m")}


def error_metrics(prediction: np.ndarray, target: np.ndarray, baseline: np.ndarray) -> dict[str, Any]:
    error = prediction - target
    baseline_error = baseline - target
    mse = float(np.mean(np.square(error)))
    baseline_mse = float(np.mean(np.square(baseline_error)))
    absolute = np.abs(error)
    return {
        "rmse_m": float(np.sqrt(mse)),
        "mae_m": float(np.mean(absolute)),
        "max_abs_m": float(np.max(absolute)),
        "p95_abs_m": float(np.quantile(absolute, 0.95)),
        "signed_mean_m": float(np.mean(error)),
        "mse_skill_vs_no_deformation": (
            float(1.0 - mse / baseline_mse) if baseline_mse > 0.0 else None
        ),
    }


def project_surface(
    points: np.ndarray,
    manifest: dict[str, Any],
    max_fill_distance_m: float,
) -> tuple[np.ndarray, np.ndarray]:
    info = manifest["heightmap"]
    rows, columns = (int(value) for value in info["shape"])
    spacing = float(info["spacing_m"])
    origin_x, origin_y = (float(value) for value in info["origin_xy_m"])
    columns_for_particle = np.rint((points[:, 0] - origin_x) / spacing).astype(int)
    rows_for_particle = np.rint((points[:, 1] - origin_y) / spacing).astype(int)
    in_bounds = (
        (columns_for_particle >= 0)
        & (columns_for_particle < columns)
        & (rows_for_particle >= 0)
        & (rows_for_particle < rows)
    )
    heightmap = np.full((rows, columns), -np.inf, dtype=np.float64)
    np.maximum.at(
        heightmap,
        (rows_for_particle[in_bounds], columns_for_particle[in_bounds]),
        points[in_bounds, 2],
    )
    heightmap[~np.isfinite(heightmap)] = np.nan
    observed = np.isfinite(heightmap)
    if not np.any(observed):
        return heightmap, observed
    xs = origin_x + np.arange(columns) * spacing
    ys = origin_y + np.arange(rows) * spacing
    observed_rows, observed_columns = np.nonzero(observed)
    tree = cKDTree(np.column_stack((xs[observed_columns], ys[observed_rows])))
    grid_x, grid_y = np.meshgrid(xs, ys)
    distances, nearest = tree.query(np.column_stack((grid_x.ravel(), grid_y.ravel())))
    supported = distances.reshape(rows, columns) <= max_fill_distance_m
    missing = ~observed & supported
    heightmap[missing] = heightmap[observed][nearest.reshape(rows, columns)[missing]]
    return heightmap, observed | supported


def lift_to_particles(
    positions: np.ndarray,
    surface: np.ndarray,
    correction: np.ndarray,
    manifest: dict[str, Any],
    depth_scale_m: float,
) -> tuple[np.ndarray, np.ndarray]:
    info = manifest["heightmap"]
    spacing = float(info["spacing_m"])
    origin_x, origin_y = (float(value) for value in info["origin_xy_m"])
    rows, columns = surface.shape
    columns_for_particle = np.rint((positions[:, 0] - origin_x) / spacing).astype(int)
    rows_for_particle = np.rint((positions[:, 1] - origin_y) / spacing).astype(int)
    in_bounds = (
        (columns_for_particle >= 0)
        & (columns_for_particle < columns)
        & (rows_for_particle >= 0)
        & (rows_for_particle < rows)
    )
    displacement = np.zeros(positions.shape[0], dtype=np.float64)
    rows_in = rows_for_particle[in_bounds]
    columns_in = columns_for_particle[in_bounds]
    local_surface = surface[rows_in, columns_in]
    local_correction = correction[rows_in, columns_in]
    valid = np.isfinite(local_surface) & np.isfinite(local_correction)
    indices = np.flatnonzero(in_bounds)[valid]
    depth = np.maximum(local_surface[valid] - positions[indices, 2], 0.0)
    weights = np.exp(-depth / depth_scale_m)
    weights[depth > 6.0 * depth_scale_m] = 0.0
    displacement[indices] = local_correction[valid] * weights
    corrected = np.asarray(positions, dtype=np.float64).copy()
    corrected[:, 2] += displacement
    return corrected.astype(np.float32), displacement.astype(np.float32)


def write_corrected_state(
    source_path: Path,
    output_path: Path,
    corrected_positions: np.ndarray,
    displacement_z: np.ndarray,
) -> None:
    source = np.load(source_path, allow_pickle=False)
    arrays = {name: source[name] for name in source.files if name not in {"schema_version", "backend", "position_m"}}
    np.savez_compressed(
        output_path,
        schema_version=np.asarray(1, dtype=np.int64),
        backend=np.asarray("newton_plus_learned_residual"),
        residual_model_id=np.asarray(MODEL_ID),
        position_m=corrected_positions,
        position_correction_m=np.column_stack(
            (
                np.zeros_like(displacement_z),
                np.zeros_like(displacement_z),
                displacement_z,
            )
        ),
        **arrays,
    )


def phase_metrics(fields: dict[str, Any], prediction: np.ndarray) -> dict[str, Any]:
    radius_mask = {
        "footprint": fields["radial"] <= 1.0 + 1.0e-12,
        "local_2r": fields["radial"] <= 2.0 + 1.0e-12,
    }
    result: dict[str, Any] = {}
    for name, region in radius_mask.items():
        mask = (
            fields["valid"]
            & region
            & np.isfinite(prediction)
            & np.isfinite(fields["target"])
            & np.isfinite(fields["chrono_initial"])
        )
        result[name] = {
            "cells": int(np.count_nonzero(mask)),
            **error_metrics(
                prediction[mask], fields["target"][mask], fields["chrono_initial"][mask]
            ),
        }
    return result


def evaluate_case(
    matrix_root: Path,
    output_dir: Path,
    plan: dict[str, Any],
    model: dict[str, np.ndarray],
    case_id: str,
    depth_scale_m: float,
) -> dict[str, Any]:
    case_output = output_dir / "cases" / case_id
    case_output.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "case_id": case_id,
        "split": split_for_case(plan, case_id),
        "model_fitted_on_case": split_for_case(plan, case_id) == "train",
        "phases": {},
    }
    for phase in PHASES:
        fields = load_case_fields(matrix_root, plan, case_id, phase)
        flat_features = fields["features"].reshape(-1, len(FEATURE_NAMES))
        flat_taper = fields["taper"].reshape(-1)
        correction = predict(model, flat_features, flat_taper).reshape(fields["target"].shape)
        correction[~fields["valid"]] = 0.0
        field_corrected = fields["prior"] + correction
        state_path = fields["response_dir"] / f"newton_state_{phase}.npz"
        state = np.load(state_path, allow_pickle=False)
        corrected_positions, displacement_z = lift_to_particles(
            state["position_m"],
            fields["prior"],
            correction,
            fields["manifest"],
            depth_scale_m,
        )
        particle_map, particle_supported = project_surface(
            corrected_positions, fields["manifest"], 1.51 * fields["spacing"]
        )
        particle_map[~particle_supported] = np.nan
        np.save(case_output / f"predicted_correction_{phase}_m.npy", correction.astype(np.float32))
        np.save(case_output / f"field_corrected_{phase}_heightmap_m.npy", field_corrected.astype(np.float32))
        np.save(case_output / f"particle_corrected_{phase}_heightmap_m.npy", particle_map.astype(np.float32))
        write_corrected_state(
            state_path,
            case_output / f"corrected_state_{phase}.npz",
            corrected_positions,
            displacement_z,
        )
        write_particle_ply(
            corrected_positions,
            case_output / f"particles_corrected_{phase}_mpm.ply",
        )
        raw_metrics = phase_metrics(fields, fields["prior"])
        field_metrics = phase_metrics(fields, field_corrected)
        particle_metrics = phase_metrics(fields, particle_map)
        checks: dict[str, Any] = {}
        for region in ("footprint", "local_2r"):
            raw_rmse = raw_metrics[region]["rmse_m"]
            corrected_rmse = particle_metrics[region]["rmse_m"]
            corrected_skill = particle_metrics[region]["mse_skill_vs_no_deformation"]
            checks[region] = {
                "improves_raw_newton": corrected_rmse < raw_rmse,
                "improves_no_deformation": corrected_skill is not None and corrected_skill > 0.0,
                "rmse_change_m": corrected_rmse - raw_rmse,
            }
        result["phases"][phase] = {
            "raw_newton": raw_metrics,
            "direct_field_correction": field_metrics,
            "particle_lift_correction": particle_metrics,
            "checks": checks,
            "particle_count": int(corrected_positions.shape[0]),
            "max_abs_particle_displacement_m": float(np.max(np.abs(displacement_z))),
        }
    result["all_local_checks_pass"] = all(
        checks["improves_raw_newton"] and checks["improves_no_deformation"]
        for phase in result["phases"].values()
        for checks in phase["checks"].values()
    )
    write_json(case_output / "evaluation_summary.json", result)
    return result


def train(args: argparse.Namespace, matrix_root: Path, output_dir: Path, plan: dict[str, Any]) -> None:
    train_ids = [
        case_id
        for case_id in spatial_case_ids(plan)
        if split_for_case(plan, case_id) == "train"
    ]
    if len(train_ids) != 3:
        raise RuntimeError(f"Expected three spatial31 training actions, got {train_ids}")
    holdout_ids = [
        case_id
        for case_id in spatial_case_ids(plan)
        if split_for_case(plan, case_id) in {"validation", "test"}
    ]
    generated_holdouts = [
        case_id
        for case_id in holdout_ids
        if (matrix_root / "cases" / case_id / "case_summary.json").is_file()
    ]
    if generated_holdouts:
        raise RuntimeError(
            "Refusing to fit after held-out action generation: "
            + ", ".join(generated_holdouts)
        )
    for case_id in train_ids:
        require_case(matrix_root, case_id)
    features, targets, taper, weight = training_arrays(matrix_root, plan, train_ids)
    model, history = fit_model(
        features,
        targets,
        taper,
        weight,
        hidden_width=args.hidden_width,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        l2=args.l2,
        max_correction_m=args.max_correction_m,
        seed=args.seed,
    )
    model_path = output_dir / "model.npz"
    save_model(model_path, model)
    source_files: list[Path] = [matrix_root / "matrix_plan.json"]
    for case_id in train_ids:
        chrono_dir, response_dir = case_paths(matrix_root, case_id)
        source_files.extend(
            [
                chrono_dir / "manifest.yaml",
                chrono_dir / "initial_heightmap_m.npy",
                chrono_dir / "loaded_heightmap_m.npy",
                chrono_dir / "residual_heightmap_m.npy",
                response_dir / "initial_heightmap_m.npy",
                response_dir / "loaded_heightmap_m.npy",
                response_dir / "residual_heightmap_m.npy",
            ]
        )
    write_json(
        output_dir / "training_summary.json",
        {
            "schema_version": 1,
            "model_id": MODEL_ID,
            "status": "trained_without_validation_or_test_access",
            "train_case_ids": train_ids,
            "validation_or_test_used_for_fit_or_selection": False,
            "held_out_case_ids_absent_at_fit": holdout_ids,
            "feature_names": list(FEATURE_NAMES),
            "latent_feature_status": (
                "excluded_from v1: current fresh states export zero stress and velocity "
                "gradient plus identity strain/transform; retain for a later informative-state ablation"
            ),
            "architecture": {
                "type": "one_hidden_layer_tanh_mlp",
                "hidden_width": args.hidden_width,
                "zero_initialized_output_layer": True,
                "bounded_vertical_correction_m": args.max_correction_m,
                "support": "action-aligned 2r crop with cosine taper from 1.5r to 2r",
                "particle_lift_depth_scale_m": args.particle_depth_scale_m,
            },
            "optimization": {
                "epochs": args.epochs,
                "learning_rate": args.learning_rate,
                "l2": args.l2,
                "seed": args.seed,
                "selection": "fixed before held-out action generation; no holdout tuning",
            },
            "training_samples": int(features.shape[0]),
            "history": history,
            "model_sha256": sha256(model_path),
            "learner_source_sha256": sha256(Path(__file__).resolve()),
            "source_sha256": {str(path.resolve()): sha256(path) for path in source_files},
        },
    )


def evaluate(args: argparse.Namespace, matrix_root: Path, output_dir: Path, plan: dict[str, Any]) -> None:
    model_path = output_dir / "model.npz"
    if not model_path.is_file():
        raise RuntimeError("Train the frozen residual pilot before evaluation")
    model = load_model(model_path)
    requested = args.case or spatial_case_ids(plan)
    results = []
    for case_id in requested:
        if case_id not in spatial_case_ids(plan):
            raise ValueError(f"Case is outside the frozen spatial31 rung: {case_id}")
        results.append(
            evaluate_case(
                matrix_root,
                output_dir,
                plan,
                model,
                case_id,
                args.particle_depth_scale_m,
            )
        )
    held_out = [result for result in results if result["split"] in {"validation", "test"}]
    write_json(
        output_dir / "evaluation_summary.json",
        {
            "schema_version": 1,
            "model_id": MODEL_ID,
            "evaluated_case_ids": [result["case_id"] for result in results],
            "held_out_case_ids": [result["case_id"] for result in held_out],
            "held_out_residual_exit_demonstrated": (
                len(held_out) == 2 and all(result["all_local_checks_pass"] for result in held_out)
            ),
            "cases": {result["case_id"]: result for result in results},
        },
    )


def main() -> None:
    args = parse_args()
    matrix_root = args.matrix_root.resolve()
    output_dir = (args.output_dir or matrix_root / "residual_pilot_v1").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    plan = load_plan(matrix_root)
    if args.stage in {"train", "all"}:
        train(args, matrix_root, output_dir, plan)
    if args.stage in {"evaluate", "all"}:
        evaluate(args, matrix_root, output_dir, plan)


if __name__ == "__main__":
    main()

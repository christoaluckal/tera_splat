#!/usr/bin/env python3
"""Freeze, train, and select the Phase 1 B3/H0/H1/H2 U-Net ladder."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import random
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from phase1_bed_state_model import (
    GLOBAL_FEATURES,
    MODEL_VARIANTS,
    SPATIAL_CHANNELS,
    Phase1BedStateUNet,
    VARIANT_CONTRACTS,
    parameter_count,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "phase1_training_v1.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--stage", choices=("plan", "train", "select"), default="plan")
    parser.add_argument("--model", choices=(*MODEL_VARIANTS, "all"), default="all")
    parser.add_argument("--seed", type=int, action="append", default=[])
    return parser.parse_args()


def repo_path(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (REPO_ROOT / path).resolve()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def serialized_json_sha256(value: Any) -> str:
    """Hash the exact UTF-8 representation emitted by write_json."""
    payload = (json.dumps(value, indent=2) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_config(path: Path) -> dict[str, Any]:
    value = json.loads(path.resolve().read_text(encoding="utf-8"))
    if value.get("schema_version") != 1:
        raise ValueError("training config schema_version must be 1")
    if value.get("training_id") != "phase1_bed_state_training_v1":
        raise ValueError("unexpected Phase 1 training identity")
    if tuple(value["models"]) != MODEL_VARIANTS:
        raise ValueError("training model ladder must be exactly B3/H0/H1/H2")
    model = value["model"]
    if model["channel_multipliers"] != [1, 2, 4]:
        raise ValueError("Phase 1 requires exactly three U-Net resolution levels")
    if not bool(model["fixed_capacity_across_variants"]):
        raise ValueError("model variants must retain identical capacity")
    seeds = [int(item) for item in value["optimization"]["training_seeds"]]
    if len(seeds) < 3 or len(seeds) != len(set(seeds)):
        raise ValueError("at least three unique training seeds are required")
    if value["normalization"]["fit_split"] != "train":
        raise ValueError("normalization must be fit on train only")
    if not bool(value["controls"]["model_selection_before_test_unlock"]):
        raise ValueError("model selection must precede test unlock")
    calibration = value["uncertainty_calibration"]
    if calibration["fit_split"] != "validation":
        raise ValueError("uncertainty calibration must use validation only")
    if calibration["region"] != "twice_radius":
        raise ValueError("uncertainty calibration region must be twice_radius")
    if calibration["quantile_method"] != "higher":
        raise ValueError("uncertainty calibration quantile method changed")
    nominal = float(calibration["nominal_coverage"])
    if not 0.0 < nominal < 1.0:
        raise ValueError("uncertainty nominal coverage must lie in (0,1)")
    lift = value["particle_lift"]
    if lift["method"] != "columnwise_linear_depth_taper":
        raise ValueError("unexpected Phase 1 particle-lift method")
    if float(lift["cutoff_depth_m"]) <= 0.0:
        raise ValueError("particle-lift cutoff depth must be positive")
    if float(lift["surface_reproduction_tolerance_m"]) <= 0.0:
        raise ValueError("particle-lift surface tolerance must be positive")
    if not bool(lift["require_every_valid_cell_observed"]):
        raise ValueError("every valid surface cell must have particle support")
    if not bool(lift["preserve_particles_outside_valid_support"]):
        raise ValueError("particles outside valid support must be preserved")
    return value


def output_root(config: Mapping[str, Any]) -> Path:
    return repo_path(config["execution"]["output_root"])


def plan_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "training_plan.json"


def normalization_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "normalization.json"


def selection_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "selection_summary.json"


def bulk_root(config: Mapping[str, Any]) -> Path:
    bulk = json.loads(repo_path(config["bulk_config"]).read_text(encoding="utf-8"))
    return repo_path(bulk["execution"]["output_root"])


def tensor_root(config: Mapping[str, Any], episode_id: str) -> Path:
    return bulk_root(config) / "episodes" / episode_id / "tensors"


def source_paths(config_path: Path) -> dict[str, Path]:
    return {
        "training_config": config_path.resolve(),
        "trainer": Path(__file__).resolve(),
        "model": SCRIPT_DIR / "phase1_bed_state_model.py",
        "model_tests": REPO_ROOT / "tests" / "test_phase1_bed_state_model.py",
        "training_tests": REPO_ROOT / "tests" / "test_train_phase1_bed_state.py",
        "particle_lift": SCRIPT_DIR / "phase1_particle_lift.py",
        "particle_lift_tests": REPO_ROOT / "tests" / "test_phase1_particle_lift.py",
    }


def require_bulk_summary(config: Mapping[str, Any]) -> dict[str, Any]:
    path = repo_path(config["bulk_summary"])
    if not path.is_file():
        raise RuntimeError("bulk summary is absent; the 64-target dataset is not admitted")
    summary = json.loads(path.read_text(encoding="utf-8"))
    if summary.get("status") != config["required_bulk_status"]:
        raise RuntimeError("bulk train/validation summary has not passed")
    if bool(summary.get("training_dataset_ready")) is not bool(
        config["required_training_dataset_ready"]
    ):
        raise RuntimeError("bulk dataset is not ready for training")
    if summary.get("counts") != {
        "total": 64,
        "train": 48,
        "validation": 16,
        "test": 0,
    }:
        raise RuntimeError("bulk summary counts changed")
    if not bool(summary.get("checks", {}).get("test_targets_unopened")):
        raise RuntimeError("test target lock is not intact")
    if not all(item.get("admitted") for item in summary["episodes"].values()):
        raise RuntimeError("every train/validation episode must be admitted")
    return summary


def episode_records(summary: Mapping[str, Any], split: str) -> list[dict[str, Any]]:
    return sorted(
        [dict(item) for item in summary["episodes"].values() if item["split"] == split],
        key=lambda item: item["episode_id"],
    )


def boundary_taper(valid: np.ndarray, width_cells: int) -> np.ndarray:
    mask = np.asarray(valid, dtype=bool)
    if mask.ndim != 2 or width_cells <= 0:
        raise ValueError("boundary taper requires a 2D mask and positive width")
    current = mask.copy()
    taper = np.zeros(mask.shape, dtype=np.float64)
    for _ in range(width_cells):
        taper += current.astype(np.float64) / float(width_cells)
        padded = np.pad(current, 1, mode="constant", constant_values=False)
        current = (
            padded[1:-1, 1:-1]
            & padded[:-2, 1:-1]
            & padded[2:, 1:-1]
            & padded[1:-1, :-2]
            & padded[1:-1, 2:]
        )
    return taper.astype(np.float32)


def _episode_arrays(config: Mapping[str, Any], record: Mapping[str, Any]):
    root = tensor_root(config, record["episode_id"])
    with np.load(root / "model_inputs.npz", allow_pickle=False) as archive:
        inputs = {name: np.array(archive[name], copy=True) for name in archive.files}
    with np.load(root / "targets.npz", allow_pickle=False) as archive:
        targets = {name: np.array(archive[name], copy=True) for name in archive.files}
    return inputs, targets


def global_vector(inputs: Mapping[str, np.ndarray]) -> np.ndarray:
    action = np.asarray(inputs["action_phase"], dtype=np.float64)
    soil = np.asarray(inputs["soil_parameters"], dtype=np.float64)
    if action.shape != (2, 4) or soil.shape != (2,):
        raise ValueError("unexpected Phase 1 global tensor shape")
    if not np.allclose(action[0, :3], action[1, :3]):
        raise ValueError("loaded/post action identity changed")
    return np.asarray([*action[0, :3], *soil], dtype=np.float64)


def fit_normalization(
    config: Mapping[str, Any], train_records: Iterable[Mapping[str, Any]]
) -> dict[str, Any]:
    records = list(train_records)
    if len(records) != 48 or any(item["split"] != "train" for item in records):
        raise ValueError("normalization requires exactly the 48 training episodes")
    spatial_sum = np.zeros(len(SPATIAL_CHANNELS), dtype=np.float64)
    spatial_square = np.zeros(len(SPATIAL_CHANNELS), dtype=np.float64)
    spatial_count = np.zeros(len(SPATIAL_CHANNELS), dtype=np.int64)
    globals_: list[np.ndarray] = []
    correction_values: list[list[np.ndarray]] = [[], []]
    direct_values: list[list[np.ndarray]] = [[], []]
    for record in records:
        inputs, targets = _episode_arrays(config, record)
        valid = np.asarray(inputs["valid_support"], dtype=bool)
        for index, name in enumerate(SPATIAL_CHANNELS):
            values = np.asarray(inputs[name], dtype=np.float64)[valid]
            if not np.isfinite(values).all():
                raise ValueError(f"nonfinite training channel: {record['episode_id']}:{name}")
            spatial_sum[index] += float(values.sum())
            spatial_square[index] += float(np.dot(values, values))
            spatial_count[index] += values.size
        globals_.append(global_vector(inputs))
        initial = np.asarray(inputs["initial_height_m"], dtype=np.float64)
        hybrid = (
            initial + np.asarray(inputs["newton_loaded_displacement_m"], dtype=np.float64),
            initial
            + np.asarray(inputs["newton_post_unload_displacement_m"], dtype=np.float64),
        )
        target = (
            np.asarray(targets["chrono_loaded_height_m"], dtype=np.float64),
            np.asarray(targets["chrono_post_unload_height_m"], dtype=np.float64),
        )
        for checkpoint in range(2):
            correction_values[checkpoint].append(np.abs(target[checkpoint][valid] - hybrid[checkpoint][valid]))
            direct_values[checkpoint].append(np.abs(target[checkpoint][valid] - initial[valid]))
    minimum_std = float(config["normalization"]["minimum_std"])
    spatial_mean = spatial_sum / spatial_count
    spatial_variance = np.maximum(spatial_square / spatial_count - spatial_mean**2, 0.0)
    spatial_std = np.maximum(np.sqrt(spatial_variance), minimum_std)
    passthrough_channels = ("valid_support", "action_footprint")
    for name in passthrough_channels:
        index = SPATIAL_CHANNELS.index(name)
        spatial_mean[index] = 0.0
        spatial_std[index] = 1.0
    global_array = np.stack(globals_)
    global_mean = global_array.mean(axis=0)
    global_std = np.maximum(global_array.std(axis=0), minimum_std)
    quantile = float(config["normalization"]["correction_scale_quantile"])
    minimum_scale = float(config["normalization"]["correction_scale_minimum_m"])
    scales = []
    for checkpoint in range(2):
        hybrid_q = float(np.quantile(np.concatenate(correction_values[checkpoint]), quantile))
        direct_q = float(np.quantile(np.concatenate(direct_values[checkpoint]), quantile))
        scales.append(max(hybrid_q, direct_q, minimum_scale))
    return {
        "schema_version": 1,
        "fit_split": "train",
        "fit_episode_ids": [item["episode_id"] for item in records],
        "spatial_channels": list(SPATIAL_CHANNELS),
        "spatial_mean": spatial_mean.tolist(),
        "spatial_std": spatial_std.tolist(),
        "spatial_count": spatial_count.tolist(),
        "passthrough_spatial_channels": list(passthrough_channels),
        "global_features": list(GLOBAL_FEATURES),
        "global_mean": global_mean.tolist(),
        "global_std": global_std.tolist(),
        "correction_scale_m": scales,
        "correction_scale_quantile": quantile,
        "boundary_taper_width_cells": int(
            config["normalization"]["boundary_taper_width_cells"]
        ),
    }


def environment_probe(config: Mapping[str, Any]) -> dict[str, Any]:
    if not torch.cuda.is_available():
        raise RuntimeError("Phase 1 training requires CUDA")
    device = torch.device(config["execution"]["device"])
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "torch": torch.__version__,
        "cuda_runtime": torch.version.cuda,
        "cuda_available": True,
        "device": str(device),
        "gpu_name": torch.cuda.get_device_name(device),
        "gpu_capability": list(torch.cuda.get_device_capability(device)),
    }


def build_plan(config_path: Path, config: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    summary = require_bulk_summary(config)
    train = episode_records(summary, "train")
    validation = episode_records(summary, "validation")
    normalization = fit_normalization(config, train)
    sources = source_paths(config_path)
    missing = [str(path) for path in sources.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing training sources: {missing}")
    tensor_hashes: dict[str, Any] = {}
    for record in (*train, *validation):
        root = tensor_root(config, record["episode_id"])
        manifest_path = root / "tensor_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["sha256"]["model_inputs"] != sha256_file(root / "model_inputs.npz"):
            raise RuntimeError("model-input tensor hash changed")
        if manifest["sha256"]["targets"] != sha256_file(root / "targets.npz"):
            raise RuntimeError("target tensor hash changed")
        tensor_hashes[record["episode_id"]] = {
            "split": record["split"],
            "input_sha256": record["input_sha256"],
            "tensor_manifest_sha256": sha256_file(manifest_path),
            **manifest["sha256"],
        }
    model_cfg = config["model"]
    counts = {
        variant: parameter_count(
            Phase1BedStateUNet(
                variant,
                base_channels=int(model_cfg["base_channels"]),
                blocks_per_scale=int(model_cfg["residual_blocks_per_scale"]),
                initial_variance_m2=float(model_cfg["initial_variance_m2"]),
                variance_floor_m2=float(model_cfg["variance_floor_m2"]),
            )
        )
        for variant in MODEL_VARIANTS
    }
    if len(set(counts.values())) != 1:
        raise RuntimeError("model ladder capacity changed across variants")
    count = next(iter(counts.values()))
    if not int(model_cfg["parameter_count_minimum"]) <= count <= int(
        model_cfg["parameter_count_maximum"]
    ):
        raise RuntimeError("U-Net parameter count is outside the Phase 1 contract")
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, check=True, text=True, capture_output=True
    ).stdout.strip()
    plan = {
        "schema_version": 1,
        "training_id": config["training_id"],
        "status": "frozen_before_first_fit",
        "config_sha256": sha256_file(config_path),
        "bulk_summary_sha256": sha256_file(repo_path(config["bulk_summary"])),
        "bulk_identity": summary["identity"],
        "source_sha256": {name: sha256_file(path) for name, path in sources.items()},
        "tensor_sha256": tensor_hashes,
        "normalization_payload_sha256": canonical_sha256(normalization),
        "normalization_file_sha256": serialized_json_sha256(normalization),
        "train_episode_ids": [item["episode_id"] for item in train],
        "validation_episode_ids": [item["episode_id"] for item in validation],
        "test_episode_ids": [],
        "test_targets_opened": False,
        "model_parameter_counts": counts,
        "model_variants": {
            name: {
                "spatial_channels": list(VARIANT_CONTRACTS[name].spatial_channels),
                "global_features": list(VARIANT_CONTRACTS[name].global_features),
                "base_state": VARIANT_CONTRACTS[name].base_state,
            }
            for name in MODEL_VARIANTS
        },
        "training_seeds": [int(item) for item in config["optimization"]["training_seeds"]],
        "environment": environment_probe(config),
        "repository_revision": revision,
    }
    return plan, normalization


STABLE_PLAN_KEYS = (
    "config_sha256",
    "bulk_summary_sha256",
    "bulk_identity",
    "source_sha256",
    "tensor_sha256",
    "normalization_payload_sha256",
    "normalization_file_sha256",
    "train_episode_ids",
    "validation_episode_ids",
    "test_episode_ids",
    "test_targets_opened",
    "model_parameter_counts",
    "model_variants",
    "training_seeds",
    "environment",
)


def write_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    plan, normalization = build_plan(config_path, config)
    if normalization_path(config).exists():
        existing_normalization = json.loads(normalization_path(config).read_text(encoding="utf-8"))
        if existing_normalization != normalization:
            raise RuntimeError("refusing to replace different training normalization")
    else:
        write_json(normalization_path(config), normalization)
    if sha256_file(normalization_path(config)) != plan["normalization_file_sha256"]:
        raise RuntimeError("written training-normalization file hash changed")
    path = plan_path(config)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        changed = [key for key in STABLE_PLAN_KEYS if existing.get(key) != plan.get(key)]
        if changed:
            raise RuntimeError(f"refusing to replace a different training plan: {changed}")
        return existing
    write_json(path, plan)
    return plan


def load_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    if not plan_path(config).is_file():
        raise RuntimeError("training plan is absent; run --stage plan after bulk admission")
    existing = json.loads(plan_path(config).read_text(encoding="utf-8"))
    current, normalization = build_plan(config_path, config)
    changed = [key for key in STABLE_PLAN_KEYS if existing.get(key) != current.get(key)]
    if changed:
        raise RuntimeError(f"training plan identity changed: {changed}")
    if canonical_sha256(normalization) != existing["normalization_payload_sha256"]:
        raise RuntimeError("training normalization payload changed")
    if sha256_file(normalization_path(config)) != existing["normalization_file_sha256"]:
        raise RuntimeError("training normalization file changed")
    return existing


NO_ACTION_RETAINED_SPATIAL_CHANNELS = (
    "initial_height_m",
    "valid_support",
    "action_relative_x_m",
    "action_relative_y_m",
    "action_signed_distance_m",
)


def normalized_spatial_arrays(
    inputs: Mapping[str, np.ndarray],
    normalization: Mapping[str, Any],
    *,
    no_action: bool = False,
) -> np.ndarray:
    """Normalize one episode, optionally representing a physical zero-force action."""
    means = np.asarray(normalization["spatial_mean"], dtype=np.float32)
    stds = np.asarray(normalization["spatial_std"], dtype=np.float32)
    if means.shape != (len(SPATIAL_CHANNELS),) or stds.shape != means.shape:
        raise ValueError("normalization does not match Phase 1 spatial channels")
    reference = np.asarray(inputs["initial_height_m"], dtype=np.float32)
    retained = set(NO_ACTION_RETAINED_SPATIAL_CHANNELS)
    arrays = []
    for channel, name in enumerate(SPATIAL_CHANNELS):
        values = np.asarray(inputs[name], dtype=np.float32)
        if values.shape != reference.shape:
            raise ValueError(f"spatial channel shape changed: {name}")
        if no_action and name not in retained:
            values = np.zeros_like(reference)
        arrays.append((values - means[channel]) / stds[channel])
    result = np.stack(arrays)
    if not np.isfinite(result).all():
        raise ValueError("normalized spatial inputs contain nonfinite values")
    return result


class Phase1TensorDataset(Dataset):
    def __init__(
        self,
        config: Mapping[str, Any],
        episode_ids: list[str],
        normalization: Mapping[str, Any],
    ):
        self.config = config
        self.episode_ids = list(episode_ids)
        self.normalization = normalization

    def __len__(self) -> int:
        return len(self.episode_ids)

    def __getitem__(self, index: int) -> dict[str, Any]:
        episode_id = self.episode_ids[index]
        record = {"episode_id": episode_id}
        inputs, targets = _episode_arrays(self.config, record)
        spatial = normalized_spatial_arrays(inputs, self.normalization)
        no_action_spatial = normalized_spatial_arrays(
            inputs, self.normalization, no_action=True
        )
        global_raw = global_vector(inputs).astype(np.float32)
        global_mean = np.asarray(self.normalization["global_mean"], dtype=np.float32)
        global_std = np.asarray(self.normalization["global_std"], dtype=np.float32)
        no_action_global_raw = global_raw.copy()
        no_action_global_raw[2] = 0.0
        initial = np.asarray(inputs["initial_height_m"], dtype=np.float32)
        hybrid_base = np.stack(
            (
                initial + np.asarray(inputs["newton_loaded_displacement_m"], dtype=np.float32),
                initial + np.asarray(inputs["newton_post_unload_displacement_m"], dtype=np.float32),
            )
        )
        target = np.stack(
            (
                np.asarray(targets["chrono_loaded_height_m"], dtype=np.float32),
                np.asarray(targets["chrono_post_unload_height_m"], dtype=np.float32),
            )
        )
        valid = np.asarray(inputs["valid_support"], dtype=bool)
        footprint = np.asarray(inputs["action_footprint"], dtype=bool) & valid
        twice_radius = (
            np.asarray(inputs["action_signed_distance_m"], dtype=np.float32) <= 0.035
        ) & valid
        taper = boundary_taper(
            valid, int(self.normalization["boundary_taper_width_cells"])
        )
        return {
            "episode_id": episode_id,
            "spatial": torch.from_numpy(spatial),
            "no_action_spatial": torch.from_numpy(no_action_spatial),
            "global_condition": torch.from_numpy((global_raw - global_mean) / global_std),
            "global_raw": torch.from_numpy(global_raw),
            "no_action_global_condition": torch.from_numpy(
                (no_action_global_raw - global_mean) / global_std
            ),
            "initial": torch.from_numpy(initial[None]),
            "hybrid_base": torch.from_numpy(hybrid_base),
            "target": torch.from_numpy(target),
            "valid": torch.from_numpy(valid[None]),
            "footprint": torch.from_numpy(footprint[None]),
            "twice_radius": torch.from_numpy(twice_radius[None]),
            "taper": torch.from_numpy(taper[None]),
            "relative_x": torch.from_numpy(np.asarray(inputs["action_relative_x_m"], dtype=np.float32)[None]),
            "relative_y": torch.from_numpy(np.asarray(inputs["action_relative_y_m"], dtype=np.float32)[None]),
        }


def masked_mean(values: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    expanded = mask.expand_as(values).to(dtype=values.dtype)
    return (values * expanded).sum() / expanded.sum().clamp_min(1.0)


def robust_error(prediction: torch.Tensor, target: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    return masked_mean(nn.functional.smooth_l1_loss(prediction, target, reduction="none", beta=0.001), mask)


def characteristic_losses(
    prediction: torch.Tensor,
    target: torch.Tensor,
    initial: torch.Tensor,
    footprint: torch.Tensor,
    valid: torch.Tensor,
    relative_x: torch.Tensor,
    relative_y: torch.Tensor,
    grid_spacing_m: float = 0.005,
) -> dict[str, torch.Tensor]:
    pred_dep = initial - prediction
    target_dep = initial - target
    fp = footprint.expand_as(pred_dep)
    support = valid.expand_as(pred_dep)
    large_negative = torch.full_like(pred_dep, -1.0e6)
    pred_peak = torch.where(fp, pred_dep, large_negative).flatten(2).amax(dim=2)
    target_peak = torch.where(fp, target_dep, large_negative).flatten(2).amax(dim=2)
    peak = (pred_peak - target_peak).abs().mean()
    mean_footprint = (
        masked_mean(pred_dep, fp) - masked_mean(target_dep, fp)
    ).abs()
    cell_area = grid_spacing_m * grid_spacing_m
    pred_volume = (torch.relu(pred_dep) * support).flatten(2).sum(dim=2) * cell_area
    target_volume = (torch.relu(target_dep) * support).flatten(2).sum(dim=2) * cell_area
    volume = (pred_volume - target_volume).abs().mean()
    threshold = 0.0005
    pred_weight = torch.sigmoid((pred_dep.abs() - threshold) / 0.0001) * support
    target_weight = torch.sigmoid((target_dep.abs() - threshold) / 0.0001) * support
    footprint_loss = (
        pred_weight.flatten(2).mean(dim=2) - target_weight.flatten(2).mean(dim=2)
    ).abs().mean()
    x = relative_x.expand_as(pred_dep)
    y = relative_y.expand_as(pred_dep)
    pred_sum = pred_weight.flatten(2).sum(dim=2).clamp_min(1.0e-8)
    target_sum = target_weight.flatten(2).sum(dim=2).clamp_min(1.0e-8)
    pred_cx = (pred_weight * x).flatten(2).sum(dim=2) / pred_sum
    pred_cy = (pred_weight * y).flatten(2).sum(dim=2) / pred_sum
    target_cx = (target_weight * x).flatten(2).sum(dim=2) / target_sum
    target_cy = (target_weight * y).flatten(2).sum(dim=2) / target_sum
    centroid = torch.sqrt((pred_cx - target_cx) ** 2 + (pred_cy - target_cy) ** 2 + 1.0e-12).mean()
    pred_recovery = masked_mean(pred_dep[:, :1] - pred_dep[:, 1:], footprint)
    target_recovery = masked_mean(target_dep[:, :1] - target_dep[:, 1:], footprint)
    return {
        "peak_depression": peak,
        "mean_footprint_depression": mean_footprint,
        "displaced_volume": volume,
        "deformation_footprint": footprint_loss,
        "deformation_centroid": centroid,
        "recovery": (pred_recovery - target_recovery).abs(),
    }


def phase1_loss(
    model: Phase1BedStateUNet,
    result: Mapping[str, torch.Tensor],
    batch: Mapping[str, torch.Tensor],
    weights: Mapping[str, float],
    correction_scale: torch.Tensor,
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    prediction = result["height_m"]
    target = batch["target"]
    valid = batch["valid"]
    footprint = batch["footprint"]
    twice = batch["twice_radius"]
    error = prediction - target
    parts = {
        "robust_footprint": robust_error(prediction, target, footprint),
        "robust_twice_radius": robust_error(prediction, target, twice),
        "robust_valid_bed": robust_error(prediction, target, valid),
        "heteroscedastic_nll": masked_mean(
            0.5 * (result["log_variance_m2"] + error.square() * torch.exp(-result["log_variance_m2"])),
            twice,
        ),
        **characteristic_losses(
            prediction,
            target,
            batch["initial"],
            footprint,
            valid,
            batch["relative_x"],
            batch["relative_y"],
        ),
        "residual_magnitude": masked_mean(result["correction_m"].square(), valid),
        "spatial_smoothness": (
            result["correction_m"][:, :, 1:, :].sub(result["correction_m"][:, :, :-1, :]).abs().mean()
            + result["correction_m"][:, :, :, 1:].sub(result["correction_m"][:, :, :, :-1]).abs().mean()
        ),
        "boundary_taper": masked_mean(
            result["correction_m"].square(), 1.0 - batch["taper"]
        ),
    }
    no_action_spatial = batch["no_action_spatial"]
    no_action_global = batch["no_action_global_condition"]
    no_action_base = batch["initial"].repeat(1, 2, 1, 1)
    no_action = model(
        no_action_spatial,
        no_action_global,
        no_action_base,
        correction_scale,
        batch["taper"],
    )
    parts["no_action_identity"] = masked_mean(
        no_action["correction_m"].square(), valid
    )
    # Particle lifting is a deterministic hard constraint applied after surface
    # inference: only particle z is corrected and every other archived field is
    # copied bit-for-bit. These zero losses make the structural constraints
    # explicit in every training record without pretending to supervise absent
    # Chrono particle correspondence.
    parts["particle_surface_reproduction"] = prediction.new_zeros(())
    parts["particle_state_preservation"] = prediction.new_zeros(())
    total = sum(parts[name] * float(weights[name]) for name in weights)
    return total, parts


def move_batch(batch: Mapping[str, Any], device: torch.device) -> dict[str, Any]:
    return {
        name: value.to(device, non_blocking=True) if isinstance(value, torch.Tensor) else value
        for name, value in batch.items()
    }


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed % (2**32))
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=False)


def validation_metric(
    model: Phase1BedStateUNet,
    loader: DataLoader,
    correction_scale: torch.Tensor,
    device: torch.device,
) -> float:
    model.eval()
    values: list[float] = []
    with torch.no_grad():
        for raw_batch in loader:
            batch = move_batch(raw_batch, device)
            base = (
                batch["initial"].repeat(1, 2, 1, 1)
                if model.base_state == "initial"
                else batch["hybrid_base"]
            )
            result = model(
                batch["spatial"], batch["global_condition"], base, correction_scale, batch["taper"]
            )
            squared = (result["height_m"] - batch["target"]).square()
            mask = batch["twice_radius"].expand_as(squared)
            numerator = (squared * mask).flatten(2).sum(dim=2)
            denominator = mask.flatten(2).sum(dim=2).clamp_min(1)
            values.extend(torch.sqrt(numerator / denominator).mean(dim=1).cpu().tolist())
    return float(np.mean(values))


def conformal_multiplier(
    absolute_errors: np.ndarray,
    standard_deviations: np.ndarray,
    nominal_coverage: float,
) -> float:
    errors = np.asarray(absolute_errors, dtype=np.float64)
    deviations = np.asarray(standard_deviations, dtype=np.float64)
    coverage = float(nominal_coverage)
    if errors.shape != deviations.shape or errors.size == 0:
        raise ValueError("calibration arrays must be nonempty and shape matched")
    if not np.isfinite(errors).all() or not np.isfinite(deviations).all():
        raise ValueError("calibration arrays must be finite")
    if np.any(errors < 0.0) or np.any(deviations <= 0.0):
        raise ValueError("calibration errors must be nonnegative and deviations positive")
    if not 0.0 < coverage < 1.0:
        raise ValueError("nominal coverage must lie in (0,1)")
    scores = errors / deviations
    return float(np.quantile(scores, coverage, method="higher"))


def instantiate_network(
    config: Mapping[str, Any], variant: str, device: torch.device
) -> Phase1BedStateUNet:
    model_cfg = config["model"]
    return Phase1BedStateUNet(
        variant,
        base_channels=int(model_cfg["base_channels"]),
        blocks_per_scale=int(model_cfg["residual_blocks_per_scale"]),
        initial_variance_m2=float(model_cfg["initial_variance_m2"]),
        variance_floor_m2=float(model_cfg["variance_floor_m2"]),
    ).to(device)


def validate_model_card(
    config: Mapping[str, Any],
    plan: Mapping[str, Any],
    card: Mapping[str, Any],
    variant: str,
    seed: int,
) -> Path:
    if card.get("variant") != variant or int(card.get("seed", -1)) != int(seed):
        raise RuntimeError("model-card identity changed")
    if bool(card.get("test_targets_opened")):
        raise RuntimeError("test target contamination detected")
    if card.get("training_plan_sha256") != sha256_file(plan_path(config)):
        raise RuntimeError("model card references a different training plan")
    if card.get("normalization_payload_sha256") != plan[
        "normalization_payload_sha256"
    ]:
        raise RuntimeError("model card normalization payload changed")
    if card.get("normalization_file_sha256") != sha256_file(
        normalization_path(config)
    ):
        raise RuntimeError("model card normalization file changed")
    if int(card.get("parameter_count", -1)) != int(
        plan["model_parameter_counts"][variant]
    ):
        raise RuntimeError("model-card parameter count changed")
    destination = model_output_dir(config, variant, int(seed))
    checkpoint = destination / "model.pt"
    history = destination / "history.json"
    if not checkpoint.is_file() or not history.is_file():
        raise RuntimeError("model checkpoint or history is missing")
    if card.get("model_sha256") != sha256_file(checkpoint):
        raise RuntimeError("model checkpoint hash changed")
    if card.get("history_sha256") != sha256_file(history):
        raise RuntimeError("training history hash changed")
    return checkpoint


def calibrate_selected_model(
    config: Mapping[str, Any],
    plan: Mapping[str, Any],
    card: Mapping[str, Any],
) -> dict[str, Any]:
    variant = str(card["variant"])
    seed = int(card["seed"])
    checkpoint_path = validate_model_card(config, plan, card, variant, seed)
    normalization = json.loads(normalization_path(config).read_text(encoding="utf-8"))
    validation_data = Phase1TensorDataset(
        config, plan["validation_episode_ids"], normalization
    )
    loader = DataLoader(
        validation_data,
        batch_size=int(config["optimization"]["batch_size"]),
        shuffle=False,
        num_workers=0,
    )
    device = torch.device(config["execution"]["device"])
    network = instantiate_network(config, variant, device)
    checkpoint = torch.load(checkpoint_path, map_location=device)
    network.load_state_dict(checkpoint["state_dict"], strict=True)
    network.eval()
    scale = torch.tensor(normalization["correction_scale_m"], device=device)
    phase_errors: list[list[np.ndarray]] = [[], []]
    phase_deviations: list[list[np.ndarray]] = [[], []]
    with torch.no_grad():
        for raw_batch in loader:
            batch = move_batch(raw_batch, device)
            base = (
                batch["initial"].repeat(1, 2, 1, 1)
                if network.base_state == "initial"
                else batch["hybrid_base"]
            )
            result = network(
                batch["spatial"],
                batch["global_condition"],
                base,
                scale,
                batch["taper"],
            )
            absolute = (result["height_m"] - batch["target"]).abs()
            deviation = torch.exp(0.5 * result["log_variance_m2"])
            mask = batch["twice_radius"].expand_as(absolute)
            for phase in range(2):
                selected = mask[:, phase]
                phase_errors[phase].append(
                    absolute[:, phase][selected].detach().cpu().numpy()
                )
                phase_deviations[phase].append(
                    deviation[:, phase][selected].detach().cpu().numpy()
                )
    nominal = float(config["uncertainty_calibration"]["nominal_coverage"])
    multipliers = [
        conformal_multiplier(
            np.concatenate(phase_errors[phase]),
            np.concatenate(phase_deviations[phase]),
            nominal,
        )
        for phase in range(2)
    ]
    return {
        "fit_split": "validation",
        "fit_episode_ids": list(plan["validation_episode_ids"]),
        "method": config["uncertainty_calibration"]["method"],
        "region": config["uncertainty_calibration"]["region"],
        "nominal_coverage": nominal,
        "quantile_method": "higher",
        "loaded_multiplier": multipliers[0],
        "post_unload_multiplier": multipliers[1],
        "test_targets_opened": False,
    }


def model_output_dir(config: Mapping[str, Any], variant: str, seed: int) -> Path:
    return output_root(config) / "models" / variant / f"seed_{seed}"


def train_one(
    config: Mapping[str, Any], plan: Mapping[str, Any], variant: str, seed: int
) -> dict[str, Any]:
    destination = model_output_dir(config, variant, seed)
    card_path = destination / "model_card.json"
    if card_path.is_file():
        return json.loads(card_path.read_text(encoding="utf-8"))
    if destination.exists():
        raise RuntimeError(f"refusing incomplete training output: {destination}")
    destination.mkdir(parents=True)
    seed_everything(seed)
    normalization = json.loads(normalization_path(config).read_text(encoding="utf-8"))
    train_data = Phase1TensorDataset(config, plan["train_episode_ids"], normalization)
    validation_data = Phase1TensorDataset(config, plan["validation_episode_ids"], normalization)
    generator = torch.Generator().manual_seed(seed)
    batch_size = int(config["optimization"]["batch_size"])
    train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True, generator=generator, num_workers=0)
    validation_loader = DataLoader(validation_data, batch_size=batch_size, shuffle=False, num_workers=0)
    device = torch.device(config["execution"]["device"])
    network = instantiate_network(config, variant, device)
    optimizer = torch.optim.AdamW(
        network.parameters(),
        lr=float(config["optimization"]["learning_rate"]),
        weight_decay=float(config["optimization"]["weight_decay"]),
    )
    use_amp = bool(config["optimization"]["mixed_precision"])
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)
    correction_scale = torch.tensor(normalization["correction_scale_m"], device=device)
    best = math.inf
    best_epoch = -1
    epochs_without_improvement = 0
    history: list[dict[str, Any]] = []
    checkpoint = destination / "model.pt"
    for epoch in range(int(config["optimization"]["maximum_epochs"])):
        network.train()
        totals: list[float] = []
        for raw_batch in train_loader:
            batch = move_batch(raw_batch, device)
            base = (
                batch["initial"].repeat(1, 2, 1, 1)
                if network.base_state == "initial"
                else batch["hybrid_base"]
            )
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast("cuda", enabled=use_amp):
                result = network(
                    batch["spatial"], batch["global_condition"], base, correction_scale, batch["taper"]
                )
                loss, _parts = phase1_loss(
                    network, result, batch, config["loss_weights"], correction_scale
                )
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            nn.utils.clip_grad_norm_(
                network.parameters(), float(config["optimization"]["gradient_clip_norm"])
            )
            scaler.step(optimizer)
            scaler.update()
            totals.append(float(loss.detach().cpu()))
        validation = validation_metric(network, validation_loader, correction_scale, device)
        history.append(
            {"epoch": epoch, "train_loss": float(np.mean(totals)), "validation_metric_m": validation}
        )
        if validation < best:
            best = validation
            best_epoch = epoch
            epochs_without_improvement = 0
            torch.save(
                {
                    "variant": variant,
                    "seed": seed,
                    "state_dict": network.state_dict(),
                    "normalization_payload_sha256": plan[
                        "normalization_payload_sha256"
                    ],
                    "normalization_file_sha256": plan["normalization_file_sha256"],
                    "training_plan_sha256": sha256_file(plan_path(config)),
                },
                checkpoint,
            )
        else:
            epochs_without_improvement += 1
        write_json(destination / "history.json", history)
        if epochs_without_improvement >= int(config["optimization"]["early_stopping_patience"]):
            break
    card = {
        "schema_version": 1,
        "variant": variant,
        "seed": seed,
        "parameter_count": parameter_count(network),
        "base_state": network.base_state,
        "active_spatial_channels": list(VARIANT_CONTRACTS[variant].spatial_channels),
        "active_global_features": list(VARIANT_CONTRACTS[variant].global_features),
        "training_plan_sha256": sha256_file(plan_path(config)),
        "normalization_payload_sha256": plan["normalization_payload_sha256"],
        "normalization_file_sha256": sha256_file(normalization_path(config)),
        "model_sha256": sha256_file(checkpoint),
        "history_sha256": sha256_file(destination / "history.json"),
        "best_epoch": best_epoch,
        "best_validation_metric_m": best,
        "epochs_run": len(history),
        "test_targets_opened": False,
    }
    write_json(card_path, card)
    return card


def select_models(config: Mapping[str, Any], plan: Mapping[str, Any]) -> dict[str, Any]:
    cards: dict[str, list[dict[str, Any]]] = {}
    for variant in MODEL_VARIANTS:
        cards[variant] = []
        for seed in plan["training_seeds"]:
            path = model_output_dir(config, variant, int(seed)) / "model_card.json"
            if not path.is_file():
                raise RuntimeError(f"missing model card before selection: {path}")
            card = json.loads(path.read_text(encoding="utf-8"))
            validate_model_card(config, plan, card, variant, int(seed))
            cards[variant].append(card)
    selected = {
        variant: min(values, key=lambda item: item["best_validation_metric_m"])
        for variant, values in cards.items()
    }
    calibration = {
        variant: calibrate_selected_model(config, plan, card)
        for variant, card in selected.items()
    }
    summary = {
        "schema_version": 1,
        "status": "models_selected_before_test_unlock",
        "training_plan_sha256": sha256_file(plan_path(config)),
        "normalization_payload_sha256": plan["normalization_payload_sha256"],
        "normalization_file_sha256": sha256_file(normalization_path(config)),
        "selection_metric": config["optimization"]["selection_metric"],
        "selected": selected,
        "uncertainty_calibration": calibration,
        "all_model_cards": cards,
        "test_targets_opened": False,
        "locked_evaluation_permitted": True,
    }
    if selection_path(config).exists():
        existing = json.loads(selection_path(config).read_text(encoding="utf-8"))
        if existing != summary:
            raise RuntimeError("refusing to replace a different model selection")
        return existing
    write_json(selection_path(config), summary)
    return summary


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = load_config(config_path)
    if args.stage == "plan":
        plan = write_plan(config_path, config)
        print(json.dumps({"plan": str(plan_path(config)), "parameter_counts": plan["model_parameter_counts"], "test_targets_opened": False}, indent=2))
        return
    plan = load_plan(config_path, config)
    if args.stage == "train":
        variants = MODEL_VARIANTS if args.model == "all" else (args.model,)
        requested_seeds = args.seed or plan["training_seeds"]
        unknown = sorted(set(requested_seeds) - set(plan["training_seeds"]))
        if unknown:
            raise ValueError(f"training seeds are outside the frozen plan: {unknown}")
        results = [train_one(config, plan, variant, int(seed)) for variant in variants for seed in requested_seeds]
        print(json.dumps({"models_completed": len(results), "test_targets_opened": False}, indent=2))
        return
    summary = select_models(config, plan)
    print(json.dumps({"status": summary["status"], "selected": {name: card["seed"] for name, card in summary["selected"].items()}, "locked_evaluation_permitted": True}, indent=2))


if __name__ == "__main__":
    main()

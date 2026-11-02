#!/usr/bin/env python3
"""Freeze, fit, and select the smoke/bulk-gated Phase 1 successor model ladder."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import train_phase1_bed_state as base
from phase1_one_action_successor_model import (
    GLOBAL_FEATURES,
    MODEL_VARIANTS,
    OPTIONAL_ABLATION_VARIANTS,
    SELECTION_VARIANTS,
    SPATIAL_CHANNELS,
    SuccessorBedStateUNet,
    VARIANT_CONTRACTS,
    parameter_count,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = (
    REPO_ROOT / "configs" / "phase1_one_action_successor_training_v1.json"
)
EXPECTED_TEST_LOCK_SHA256 = (
    "0390d46bfd5860b08518f3b99ab116084f24138939c04435f29582c3feedf713"
)
EXPECTED_SENSITIVITY_LOCK_SHA256 = (
    "a003ec52f2fb43c94d5d760e06a924c3b49809a0ddf415a6abbb718ff18a4139"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--stage", choices=("plan", "train", "select"), default="plan")
    parser.add_argument("--model", choices=(*MODEL_VARIANTS, "all"), default="all")
    parser.add_argument("--seed", type=int, action="append", default=[])
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.resolve().read_text(encoding="utf-8"))
    if config.get("schema_version") != 1:
        raise ValueError("successor training config schema_version must be 1")
    if config.get("training_id") != "phase1_one_action_successor_training_v1":
        raise ValueError("unexpected successor training identity")
    if config.get("status") != "prepared_bulk_gate_locked":
        raise ValueError("successor training must remain bulk-gate locked before planning")
    if tuple(config["models"]) != MODEL_VARIANTS:
        raise ValueError("successor model ladder changed")
    if tuple(config["selection_pool"]) != SELECTION_VARIANTS:
        raise ValueError("successor core selection pool changed")
    if tuple(config["optional_ablation_pool"]) != OPTIONAL_ABLATION_VARIANTS:
        raise ValueError("successor optional ablation pool changed")
    model = config["model"]
    if model["channel_multipliers"] != [1, 2, 4]:
        raise ValueError("successor requires exactly three U-Net resolution levels")
    if not model["fixed_capacity_across_variants"]:
        raise ValueError("successor variants must retain identical capacity")
    inputs = config["input_contract"]
    if tuple(inputs["global_features"]) != GLOBAL_FEATURES:
        raise ValueError("successor global feature contract changed")
    if int(inputs["soil_parameter_count"]) != 1:
        raise ValueError("successor must use exactly one soil parameter")
    if not inputs["fixed_friction_is_not_a_model_feature"]:
        raise ValueError("fixed friction cannot become a successor model feature")
    if not inputs["plastic_state_excluded"] or not inputs["target_arrays_are_never_inputs"]:
        raise ValueError("successor leakage or plastic exclusion changed")
    seeds = [int(value) for value in config["optimization"]["training_seeds"]]
    if len(seeds) < 3 or len(seeds) != len(set(seeds)):
        raise ValueError("at least three unique successor training seeds are required")
    if config["normalization"]["fit_split"] != "train":
        raise ValueError("successor normalization must be fit on train only")
    if config["uncertainty_calibration"]["fit_split"] != "validation":
        raise ValueError("successor uncertainty calibration must use validation only")
    if not config["controls"]["model_selection_before_test_or_sensitivity_unlock"]:
        raise ValueError("successor selection must precede every protected unlock")
    lift = config["particle_lift"]
    if lift["method"] != "columnwise_linear_depth_taper":
        raise ValueError("unexpected successor particle-lift method")
    if float(lift["cutoff_depth_m"]) <= 0 or float(
        lift["surface_reproduction_tolerance_m"]
    ) <= 0:
        raise ValueError("successor particle-lift bounds must be positive")
    return config


def global_vector(inputs: Mapping[str, np.ndarray]) -> np.ndarray:
    action = np.asarray(inputs["action_phase"], dtype=np.float64)
    soil = np.asarray(inputs["soil_parameters"], dtype=np.float64)
    if action.shape != (2, 4) or soil.shape != (1,):
        raise ValueError("unexpected successor global tensor shape")
    if not np.allclose(action[0, :3], action[1, :3]):
        raise ValueError("loaded/post action identity changed")
    return np.asarray([*action[0, :3], soil[0]], dtype=np.float64)


def require_bulk_summary(config: Mapping[str, Any]) -> dict[str, Any]:
    path = base.repo_path(config["bulk_summary"])
    if not path.is_file():
        raise RuntimeError(
            "successor bulk summary is absent; training-plan freeze remains locked"
        )
    summary = json.loads(path.read_text(encoding="utf-8"))
    if summary.get("status") != config["required_bulk_status"]:
        raise RuntimeError("successor bulk train/validation summary has not passed")
    if summary.get("training_plan_freeze_permitted") is not True:
        raise RuntimeError("successor bulk does not permit training-plan freeze")
    if summary.get("test_or_protected_sensitivity_permitted") is not False:
        raise RuntimeError("successor bulk protected-target permission changed")
    if summary.get("counts") != {
        "total": 64,
        "train": 48,
        "validation": 16,
        "test": 0,
        "protected_sensitivity": 0,
    }:
        raise RuntimeError("successor bulk summary counts changed")
    checks = summary.get("checks", {})
    if not checks.get("test_and_sensitivity_targets_unopened"):
        raise RuntimeError("successor protected target locks are not intact")
    identity = summary.get("identity", {})
    if identity.get("test_lock_sha256") != EXPECTED_TEST_LOCK_SHA256:
        raise RuntimeError("successor test lock changed before training")
    if identity.get("sensitivity_lock_sha256") != EXPECTED_SENSITIVITY_LOCK_SHA256:
        raise RuntimeError("successor sensitivity lock changed before training")
    if len(summary.get("episodes", {})) != 64 or not all(
        item.get("complete") is True and item.get("admitted") is True
        for item in summary["episodes"].values()
    ):
        raise RuntimeError("all 64 successor train/validation episodes must be admitted")
    return summary


def source_paths(config_path: Path) -> dict[str, Path]:
    return {
        "training_config": config_path.resolve(),
        "successor_trainer": Path(__file__).resolve(),
        "successor_model": SCRIPT_DIR / "phase1_one_action_successor_model.py",
        "successor_tests": REPO_ROOT
        / "tests"
        / "test_phase1_one_action_successor_training.py",
        "base_trainer": SCRIPT_DIR / "train_phase1_bed_state.py",
        "base_model": SCRIPT_DIR / "phase1_bed_state_model.py",
        "particle_lift": SCRIPT_DIR / "phase1_particle_lift.py",
        "particle_lift_tests": REPO_ROOT / "tests" / "test_phase1_particle_lift.py",
    }


# The proven trainer resolves these names at call time. Rebinding them here
# keeps its normalization, loss, fitting, and calibration machinery while the
# successor receives an isolated model ladder and four-feature global vector.
base.GLOBAL_FEATURES = GLOBAL_FEATURES
base.MODEL_VARIANTS = MODEL_VARIANTS
base.SPATIAL_CHANNELS = SPATIAL_CHANNELS
base.Phase1BedStateUNet = SuccessorBedStateUNet
base.VARIANT_CONTRACTS = VARIANT_CONTRACTS
base.parameter_count = parameter_count
base.global_vector = global_vector
base.require_bulk_summary = require_bulk_summary
base.source_paths = source_paths


# Re-export the proven pure helpers under the successor module for focused
# tests and future locked evaluation reuse.
boundary_taper = base.boundary_taper
normalized_spatial_arrays = base.normalized_spatial_arrays
conformal_multiplier = base.conformal_multiplier
phase1_loss = base.phase1_loss
Phase1TensorDataset = base.Phase1TensorDataset
plan_path = base.plan_path
normalization_path = base.normalization_path
selection_path = base.selection_path
build_plan = base.build_plan
write_plan = base.write_plan
load_plan = base.load_plan
train_one = base.train_one


def select_models(
    config: Mapping[str, Any], plan: Mapping[str, Any]
) -> dict[str, Any]:
    cards: dict[str, list[dict[str, Any]]] = {}
    for variant in MODEL_VARIANTS:
        cards[variant] = []
        for seed in plan["training_seeds"]:
            path = base.model_output_dir(config, variant, int(seed)) / "model_card.json"
            if not path.is_file():
                raise RuntimeError(f"missing model card before selection: {path}")
            card = json.loads(path.read_text(encoding="utf-8"))
            base.validate_model_card(config, plan, card, variant, int(seed))
            cards[variant].append(card)
    selected = {
        variant: min(values, key=lambda item: item["best_validation_metric_m"])
        for variant, values in cards.items()
    }
    calibration = {
        variant: base.calibrate_selected_model(config, plan, card)
        for variant, card in selected.items()
    }
    summary = {
        "schema_version": 1,
        "status": "models_selected_before_protected_unlock",
        "training_plan_sha256": base.sha256_file(plan_path(config)),
        "normalization_payload_sha256": plan["normalization_payload_sha256"],
        "normalization_file_sha256": base.sha256_file(normalization_path(config)),
        "selection_metric": config["optimization"]["selection_metric"],
        "selection_pool": list(SELECTION_VARIANTS),
        "optional_ablation_pool": list(OPTIONAL_ABLATION_VARIANTS),
        "selected": selected,
        "uncertainty_calibration": calibration,
        "all_model_cards": cards,
        "test_targets_opened": False,
        "protected_sensitivity_targets_opened": False,
        "evaluation_plan_freeze_permitted": True,
    }
    path = selection_path(config)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != summary:
            raise RuntimeError("refusing to replace a different successor selection")
        return existing
    base.write_json(path, summary)
    return summary


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = load_config(config_path)
    if args.stage == "plan":
        plan = write_plan(config_path, config)
        print(
            json.dumps(
                {
                    "plan": str(plan_path(config)),
                    "parameter_counts": plan["model_parameter_counts"],
                    "selection_pool": list(SELECTION_VARIANTS),
                    "optional_ablation_pool": list(OPTIONAL_ABLATION_VARIANTS),
                    "protected_targets_opened": False,
                },
                indent=2,
            )
        )
        return
    plan = load_plan(config_path, config)
    if args.stage == "train":
        variants = MODEL_VARIANTS if args.model == "all" else (args.model,)
        requested_seeds = args.seed or plan["training_seeds"]
        unknown = sorted(set(requested_seeds) - set(plan["training_seeds"]))
        if unknown:
            raise ValueError(f"training seeds are outside the frozen plan: {unknown}")
        results = [
            train_one(config, plan, variant, int(seed))
            for variant in variants
            for seed in requested_seeds
        ]
        print(
            json.dumps(
                {
                    "models_completed": len(results),
                    "protected_targets_opened": False,
                },
                indent=2,
            )
        )
        return
    summary = select_models(config, plan)
    print(
        json.dumps(
            {
                "status": summary["status"],
                "selected_seed_per_variant": {
                    name: card["seed"] for name, card in summary["selected"].items()
                },
                "selection_pool": list(SELECTION_VARIANTS),
                "optional_ablation_pool": list(OPTIONAL_ABLATION_VARIANTS),
                "evaluation_plan_freeze_permitted": True,
                "protected_targets_opened": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

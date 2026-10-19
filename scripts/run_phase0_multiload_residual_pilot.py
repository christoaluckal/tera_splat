#!/usr/bin/env python3
"""Freeze, fit, and evaluate the separate 31 N + 46 N residual pilot.

This wrapper deliberately leaves the successful single-load v1 source and
artifacts unchanged.  It reuses the tested geometry/particle implementation,
but owns a distinct model id, output root, provenance record, and pre-holdout
fit lock.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

import run_phase0_residual_pilot as base


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX_ROOT = (
    REPO_ROOT
    / "outputs/validity_experiment/newton/static_proxy_hierarchical_v3_20261017/matrix"
)
MODEL_ID = "phase0_action_aligned_particle_mlp_v2_multiload_20261018"
TRAIN_RUNG_NAMES = ("spatial31", "spatial46")
EVALUATION_RUNG = "spatial46"
FUTURE_PROTECTED_RUNG = "spatial61"

# Base functions use this module global when serializing models and corrected
# states.  Rebinding it changes only this process; the v1 source is untouched.
base.MODEL_ID = MODEL_ID


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


def training_case_ids(plan: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for rung_name in TRAIN_RUNG_NAMES:
        result.extend(
            case_id
            for case_id in plan["rungs"][rung_name]
            if base.split_for_case(plan, case_id) == "train"
        )
    return result


def evaluation_case_ids(plan: dict[str, Any]) -> list[str]:
    return [
        case_id
        for case_id in plan["rungs"][EVALUATION_RUNG]
        if base.split_for_case(plan, case_id) in {"validation", "test"}
    ]


def protected_case_ids(plan: dict[str, Any]) -> list[str]:
    return evaluation_case_ids(plan) + list(plan["rungs"][FUTURE_PROTECTED_RUNG])


def source_files_for_case(matrix_root: Path, case_id: str) -> list[Path]:
    chrono_dir, response_dir = base.case_paths(matrix_root, case_id)
    return [
        chrono_dir / "manifest.yaml",
        chrono_dir / "initial_heightmap_m.npy",
        chrono_dir / "loaded_heightmap_m.npy",
        chrono_dir / "residual_heightmap_m.npy",
        response_dir / "initial_heightmap_m.npy",
        response_dir / "loaded_heightmap_m.npy",
        response_dir / "residual_heightmap_m.npy",
    ]


def train(
    args: argparse.Namespace,
    matrix_root: Path,
    output_dir: Path,
    plan: dict[str, Any],
) -> None:
    train_ids = training_case_ids(plan)
    if len(train_ids) != 6:
        raise RuntimeError(f"Expected six 31 N + 46 N training actions, got {train_ids}")
    generated_protected = [
        case_id
        for case_id in protected_case_ids(plan)
        if (matrix_root / "cases" / case_id / "case_summary.json").is_file()
    ]
    if generated_protected:
        raise RuntimeError(
            "Refusing to fit v2 after protected holdout/future-load generation: "
            + ", ".join(generated_protected)
        )
    for case_id in train_ids:
        base.require_case(matrix_root, case_id)
    features, targets, taper, weight = base.training_arrays(matrix_root, plan, train_ids)
    model, history = base.fit_model(
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
    base.save_model(model_path, model)
    source_files = [matrix_root / "matrix_plan.json"]
    for case_id in train_ids:
        source_files.extend(source_files_for_case(matrix_root, case_id))
    base.write_json(
        output_dir / "training_summary.json",
        {
            "schema_version": 1,
            "model_id": MODEL_ID,
            "status": "trained_on_31n_and_46n_without_46n_holdout_or_61n_access",
            "train_case_ids": train_ids,
            "loads_n": sorted(
                {float(base.case_by_id(plan, case_id)["normal_force_n"]) for case_id in train_ids}
            ),
            "validation_or_test_used_for_fit_or_selection": False,
            "protected_case_ids_absent_at_fit": protected_case_ids(plan),
            "feature_names": list(base.FEATURE_NAMES),
            "latent_feature_status": (
                "excluded: current fresh 31 N states export zero/identity latent arrays; "
                "v2 isolates load coverage rather than silently consuming placeholders"
            ),
            "architecture": {
                "type": "one_hidden_layer_tanh_mlp",
                "hidden_width": args.hidden_width,
                "zero_initialized_output_layer": True,
                "bounded_vertical_correction_m": args.max_correction_m,
                "support": "action-aligned 2r crop with cosine taper from 1.5r to 2r",
                "particle_lift_depth_scale_m": args.particle_depth_scale_m,
                "difference_from_v1": "training includes force-varying 31 N and 46 N actions",
            },
            "optimization": {
                "epochs": args.epochs,
                "learning_rate": args.learning_rate,
                "l2": args.l2,
                "seed": args.seed,
                "selection": "same fixed hyperparameters as v1; no 46 N holdout or 61 N tuning",
            },
            "training_samples": int(features.shape[0]),
            "history": history,
            "model_sha256": base.sha256(model_path),
            "learner_source_sha256": base.sha256(Path(__file__).resolve()),
            "base_v1_source_sha256": base.sha256(Path(base.__file__).resolve()),
            "source_sha256": {str(path.resolve()): base.sha256(path) for path in source_files},
        },
    )


def evaluate(
    args: argparse.Namespace,
    matrix_root: Path,
    output_dir: Path,
    plan: dict[str, Any],
) -> None:
    model_path = output_dir / "model.npz"
    if not model_path.is_file():
        raise RuntimeError("Train and freeze the multi-load v2 model before evaluation")
    model = base.load_model(model_path)
    allowed = set(plan["rungs"][EVALUATION_RUNG])
    requested = args.case or evaluation_case_ids(plan)
    results = []
    for case_id in requested:
        if case_id not in allowed:
            raise ValueError(f"Case is outside the frozen 46 N evaluation rung: {case_id}")
        results.append(
            base.evaluate_case(
                matrix_root,
                output_dir,
                plan,
                model,
                case_id,
                args.particle_depth_scale_m,
            )
        )
    held_out = [result for result in results if result["split"] in {"validation", "test"}]
    base.write_json(
        output_dir / "evaluation_summary.json",
        {
            "schema_version": 1,
            "model_id": MODEL_ID,
            "evaluated_case_ids": [result["case_id"] for result in results],
            "held_out_case_ids": [result["case_id"] for result in held_out],
            "multiload_held_out_residual_exit_demonstrated": (
                len(held_out) == 2 and all(result["all_local_checks_pass"] for result in held_out)
            ),
            "cases": {result["case_id"]: result for result in results},
        },
    )


def main() -> None:
    args = parse_args()
    matrix_root = args.matrix_root.resolve()
    output_dir = (args.output_dir or matrix_root / "residual_pilot_v2_multiload").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    plan = base.load_plan(matrix_root)
    if args.stage in {"train", "all"}:
        train(args, matrix_root, output_dir, plan)
    if args.stage in {"evaluate", "all"}:
        evaluate(args, matrix_root, output_dir, plan)


if __name__ == "__main__":
    main()

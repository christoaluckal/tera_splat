#!/usr/bin/env python3
"""Freeze and execute the one-shot Phase 1 locked evaluation."""

from __future__ import annotations

import argparse
import concurrent.futures
import importlib
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_fresh_phase0_repeatability as fresh
import run_phase1_dataset as dataset
from chrono_episode_bridge import load_episode
from phase1_metric_bed import write_common_base_metric_bed
from run_phase1_contract_screen import canonical_sha256, load_contract


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "phase1_evaluation_v1.json"
REQUIRED_MODELS = ("B3", "H0", "H1", "H2")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--stage",
        choices=("plan", "unlock", "chrono", "bed", "newton", "admit", "predict", "report"),
        default="plan",
    )
    parser.add_argument("--episode", action="append", default=[])
    return parser.parse_args()


def repo_path(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (REPO_ROOT / path).resolve()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def load_evaluation_config(path: Path) -> dict[str, Any]:
    value = json.loads(path.resolve().read_text(encoding="utf-8"))
    if value.get("schema_version") != 1:
        raise ValueError("evaluation config schema_version must be 1")
    evaluation_id = value.get("evaluation_id")
    if evaluation_id not in {
        "phase1_bed_state_evaluation_v1",
        "phase1_bed_state_evaluation_v2",
    }:
        raise ValueError("unexpected Phase 1 evaluation identity")
    membership = value["membership"]
    if int(membership["test"]) != 24:
        raise ValueError("locked evaluation must contain exactly 24 test episodes")
    if sum(int(count) for count in membership["required_holdout_groups"].values()) != 24:
        raise ValueError("test holdout-group counts must sum to 24")
    if not bool(membership["selection_must_precede_unlock"]):
        raise ValueError("model selection must precede test unlock")
    metrics = value["metrics"]
    if not bool(metrics["episode_is_resampling_unit"]):
        raise ValueError("bootstrap resampling unit must be whole episodes")
    if metrics["regions"] != ["footprint", "twice_radius", "valid_bed"]:
        raise ValueError("evaluation regions changed")
    controls = value["parameter_controls"]
    if controls["shuffle_algorithm"] != (
        "seeded_derangement_of_test_episode_soil_vectors"
    ):
        raise ValueError("parameter shuffle algorithm changed")
    if controls["constant_parameters"] != "train_mean_normalized_to_zero":
        raise ValueError("constant-parameter control changed")
    if not bool(controls["require_paired_bootstrap_lower_bound_above_zero"]):
        raise ValueError("parameter controls require a positive paired-bootstrap bound")
    if any(
        float(controls[name]) < 0.0
        for name in (
            "minimum_shuffle_degradation_m",
            "minimum_constant_degradation_m",
        )
    ):
        raise ValueError("parameter-control degradation thresholds must be nonnegative")
    sensitivity = value["sensitivity"]
    prohibited = bool(sensitivity["use_for_training_normalization_calibration_or_selection"])
    if prohibited or not bool(sensitivity["use_only_for_directional_parameter_sensitivity"]):
        raise ValueError("matched sensitivity cases must remain evaluation-only")
    if sensitivity["quantities"] != [
        "loaded_peak_sinkage_m",
        "loaded_displaced_volume_m3",
        "peak_recovery_m",
    ]:
        raise ValueError("matched sensitivity quantities changed")
    if any(
        float(value) != 0.0
        for value in sensitivity["chrono_repeatability_floor"].values()
    ):
        raise ValueError("Chrono repeatability floor must reflect exact repeats")
    if float(sensitivity["maximum_center_bilinear_deviation_fraction"]) <= 0.0:
        raise ValueError("sensitivity smoothness threshold must be positive")
    dataset = value["test_dataset"]
    if int(dataset["required_episode_count"]) != 24 or int(dataset["required_test_count"]) != 24:
        raise ValueError("test dataset exit counts changed")
    guide_tolerances = value.get("guide_tolerances")
    if evaluation_id == "phase1_bed_state_evaluation_v2":
        required_guide_components = {
            "horizontal_position_error_m",
            "horizontal_speed_mps",
            "angular_speed_radps",
            "orientation_quaternion_error",
        }
        if set(guide_tolerances or {}) != required_guide_components:
            raise ValueError("v2 requires all component-specific guide tolerances")
        if any(float(limit) <= 0.0 for limit in guide_tolerances.values()):
            raise ValueError("guide tolerances must be positive")
        if not math.isclose(
            float(guide_tolerances["horizontal_speed_mps"]),
            5.0e-6,
            rel_tol=0.0,
            abs_tol=0.0,
        ):
            raise ValueError("v2 horizontal-speed tolerance changed")
        if any(
            not math.isclose(
                float(guide_tolerances[name]), 1.0e-6, rel_tol=0.0, abs_tol=0.0
            )
            for name in required_guide_components - {"horizontal_speed_mps"}
        ):
            raise ValueError("v2 non-speed guide tolerances changed")
        if int(value["execution"].get("newton_workers", 0)) != 2:
            raise ValueError("v2 execution identity requires exactly two Newton workers")
        recovery = value.get("recovery_v2", {})
        if recovery.get("source_evaluation_id") != "phase1_bed_state_evaluation_v1":
            raise ValueError("v2 must preserve the failed v1 evaluation as its source")
        if not bool(recovery.get("reuse_selected_models_without_refit")):
            raise ValueError("v2 must reuse the selected v1 models without refitting")
    # Generic Phase 1 tensor helpers read these keys.  The alias exists only in
    # memory and does not weaken their original no-test contract.
    value["newton_prior"] = dict(dataset["newton_prior"])
    value["smoke_exit"] = {
        **dataset,
        "required_train_count": 0,
        "required_validation_count": 0,
        "required_surface_seeds": list(membership["required_surface_seeds"]),
    }
    return value


def output_root(config: Mapping[str, Any]) -> Path:
    return repo_path(config["execution"]["output_root"])


def chrono_root(config: Mapping[str, Any]) -> Path:
    return repo_path(config["execution"]["chrono_output_root"])


def plan_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "evaluation_plan.json"


def unlock_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "test_unlock.json"


def opened_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "test_targets_opened.json"


def prerequisite_paths(config: Mapping[str, Any]) -> dict[str, Path]:
    sensitivity = config["sensitivity"]
    result = {
        "phase1_contract": repo_path(config["phase1_contract"]),
        "dataset_plan": repo_path(config["dataset_plan"]),
        "bulk_summary": repo_path(config["bulk_summary"]),
        "training_config": repo_path(config["training_config"]),
        "training_plan": repo_path(config["training_plan"]),
        "normalization": repo_path(config["normalization"]),
        "selection_summary": repo_path(config["selection_summary"]),
        "phase0_model": repo_path(config["phase0_model"]),
        "phase0_training_summary": repo_path(
            config["phase0_training_summary"]
        ),
        "sensitivity_screening_plan": repo_path(sensitivity["screening_plan"]),
        "sensitivity_screening_summary": repo_path(sensitivity["screening_summary"]),
        "sensitivity_pairing_summary": repo_path(sensitivity["pairing_summary"]),
        "chrono_repeatability_summary": repo_path(
            sensitivity["chrono_repeatability_summary"]
        ),
    }
    recovery = config.get("recovery_v2")
    if recovery:
        result.update(
            {
                "v1_evaluation_plan": repo_path(recovery["v1_evaluation_plan"]),
                "v1_failed_dataset_summary": repo_path(
                    recovery["v1_failed_dataset_summary"]
                ),
                "v2_surface_qualification": repo_path(
                    config["surface_qualification"]["summary"]
                ),
            }
        )
    return result


def selected_test_episodes(
    config: Mapping[str, Any], dataset_plan: Mapping[str, Any]
) -> list[dict[str, Any]]:
    episodes = [dict(item) for item in dataset_plan["episodes"]["test"]]
    if len(episodes) != int(config["membership"]["test"]):
        raise ValueError("frozen test episode count changed")
    if any(item.get("split") != "test" or item.get("target_access") != "locked" for item in episodes):
        raise ValueError("test identity lock is invalid")
    expected_lock = canonical_sha256(
        [
            {"episode_id": item["episode_id"], "input_sha256": item["input_sha256"]}
            for item in episodes
        ]
    )
    if dataset_plan.get("test_lock_sha256") != expected_lock:
        raise ValueError("test identity hash changed")
    groups = Counter(item["holdout_group"] for item in episodes)
    expected_groups = {
        name: int(count)
        for name, count in config["membership"]["required_holdout_groups"].items()
    }
    if dict(groups) != expected_groups:
        raise ValueError(f"test holdout groups changed: {dict(groups)}")
    seeds = sorted({int(item["initial_surface_seed"]) for item in episodes})
    if seeds != sorted(int(value) for value in config["membership"]["required_surface_seeds"]):
        raise ValueError(f"test surface coverage changed: {seeds}")
    return episodes


def parameter_shuffle_mapping(
    episode_ids: Sequence[str], seed: int
) -> dict[str, str]:
    identities = sorted(str(value) for value in episode_ids)
    if len(identities) < 2 or len(set(identities)) != len(identities):
        raise ValueError("parameter shuffle requires unique episode identities")
    rng = np.random.default_rng(int(seed))
    indices = np.arange(len(identities))
    for _ in range(1000):
        shuffled = rng.permutation(indices)
        if np.all(shuffled != indices):
            return {
                identities[index]: identities[int(shuffled[index])]
                for index in indices
            }
    raise RuntimeError("failed to construct deterministic parameter derangement")


def assert_test_targets_absent(
    config: Mapping[str, Any], episodes: Sequence[Mapping[str, Any]]
) -> None:
    present = []
    for episode in episodes:
        episode_id = str(episode["episode_id"])
        for path in (
            chrono_root(config) / episode_id,
            output_root(config) / "episodes" / episode_id,
        ):
            if path.exists():
                present.append(str(path))
    if present:
        raise RuntimeError(f"test target artifacts exist before unlock: {present}")


def source_paths(
    config_path: Path,
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Path]:
    shared = dataset.source_paths(config_path, config, contract)
    result = {
        "evaluation_config": config_path.resolve(),
        "evaluator": Path(__file__).resolve(),
        "evaluator_tests": REPO_ROOT / "tests" / "test_evaluate_phase1_bed_state.py",
        "model": SCRIPT_DIR / "phase1_bed_state_model.py",
        "trainer": SCRIPT_DIR / "train_phase1_bed_state.py",
        "particle_lift": SCRIPT_DIR / "phase1_particle_lift.py",
        "dataset_runtime": SCRIPT_DIR / "run_phase1_dataset.py",
        "bulk_runtime": SCRIPT_DIR / "run_phase1_dataset_bulk.py",
        **{f"shared_{name}": path for name, path in shared.items()},
    }
    for name, value in config.get("additional_locked_sources", {}).items():
        result[f"additional_{name}"] = repo_path(value)
    return result


def require_prerequisites(config: Mapping[str, Any]) -> dict[str, Any]:
    paths = prerequisite_paths(config)
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise RuntimeError(f"locked evaluation prerequisites are absent: {missing}")
    bulk = json.loads(paths["bulk_summary"].read_text(encoding="utf-8"))
    if bulk.get("status") != "passed" or not bool(bulk.get("training_dataset_ready")):
        raise RuntimeError("admitted train/validation dataset is required")
    if not bool(bulk.get("checks", {}).get("test_targets_unopened")):
        raise RuntimeError("bulk summary reports an opened test boundary")
    training_plan = json.loads(paths["training_plan"].read_text(encoding="utf-8"))
    if bool(training_plan.get("test_targets_opened")):
        raise RuntimeError("training plan reports test contamination")
    selection = json.loads(paths["selection_summary"].read_text(encoding="utf-8"))
    if selection.get("status") != "models_selected_before_test_unlock":
        raise RuntimeError("validation model selection is incomplete")
    if not bool(selection.get("locked_evaluation_permitted")) or bool(
        selection.get("test_targets_opened")
    ):
        raise RuntimeError("selection summary does not permit locked evaluation")
    if set(selection.get("selected", {})) != set(REQUIRED_MODELS):
        raise RuntimeError("selection summary does not contain B3/H0/H1/H2")
    if set(selection.get("uncertainty_calibration", {})) != set(REQUIRED_MODELS):
        raise RuntimeError("validation uncertainty calibration is incomplete")
    recovery = config.get("recovery_v2")
    if recovery:
        if (
            fresh.sha256_file(paths["selection_summary"])
            != recovery["selection_summary_sha256"]
        ):
            raise RuntimeError("v2 selected-model identity differs from frozen v1")
        if (
            fresh.sha256_file(paths["v1_evaluation_plan"])
            != recovery["v1_evaluation_plan_sha256"]
        ):
            raise RuntimeError("v1 evaluation-plan evidence changed")
        if (
            fresh.sha256_file(paths["v1_failed_dataset_summary"])
            != recovery["v1_failed_dataset_summary_sha256"]
        ):
            raise RuntimeError("v1 failed admission evidence changed")
        failed_v1 = json.loads(
            paths["v1_failed_dataset_summary"].read_text(encoding="utf-8")
        )
        if failed_v1.get("status") != "failed_or_incomplete" or bool(
            failed_v1.get("prediction_permitted")
        ):
            raise RuntimeError("v2 recovery requires the preserved fail-closed v1 result")
        surface = json.loads(
            paths["v2_surface_qualification"].read_text(encoding="utf-8")
        )
        expected_seed = int(config["surface_qualification"]["reserved_seed"])
        if int(surface.get("seed", -1)) != expected_seed or not bool(
            surface.get("qualified")
        ):
            raise RuntimeError("reserved v2 surface is not qualified")
    if (
        fresh.sha256_file(paths["phase0_model"])
        != config["phase0_model_sha256"]
    ):
        raise RuntimeError("frozen Phase 0 model identity changed")
    if (
        fresh.sha256_file(paths["phase0_training_summary"])
        != config["phase0_training_summary_sha256"]
    ):
        raise RuntimeError("frozen Phase 0 training record changed")
    pairing = json.loads(
        paths["sensitivity_pairing_summary"].read_text(encoding="utf-8")
    )
    if pairing.get("status") != "passed" or not bool(
        pairing.get("all_five_pairings_admitted")
    ):
        raise RuntimeError("matched sensitivity pairings are not admitted")
    repeatability = json.loads(
        paths["chrono_repeatability_summary"].read_text(encoding="utf-8")
    )
    if not bool(
        repeatability.get("chrono", {}).get("bitwise_identical")
    ):
        raise RuntimeError(
            "zero Chrono sensitivity floor lacks exact-repeat evidence"
        )
    return {"bulk": bulk, "training_plan": training_plan, "selection": selection}


def matched_sensitivity_cases(
    config: Mapping[str, Any], screening_plan: Mapping[str, Any]
) -> list[dict[str, Any]]:
    cases = [dict(item) for item in screening_plan.get("material_cases", [])]
    if len(cases) != 5:
        raise ValueError("matched sensitivity suite must contain five material cases")
    identities = {
        (
            int(item["initial_surface_seed"]),
            tuple(float(x) for x in item["center_xy_m"]),
            float(item["normal_force_n"]),
        )
        for item in cases
    }
    if len(identities) != 1:
        raise ValueError("sensitivity material cases are not action matched")
    combinations = {
        (float(item["bekker_kphi"]), float(item["mohr_friction_deg"]))
        for item in cases
    }
    expected = {
        (640000.0, 24.0),
        (640000.0, 32.0),
        (960000.0, 24.0),
        (960000.0, 32.0),
        (800000.0, 28.0),
    }
    if combinations != expected:
        raise ValueError("sensitivity material rectangle changed")
    return cases


def validate_inference_domain(
    contract: Mapping[str, Any], episode: Mapping[str, Any]
) -> None:
    action = contract["action_domain"]
    center = np.asarray(episode["center_xy_m"], dtype=np.float64)
    if center.shape != (2,) or not np.isfinite(center).all():
        raise ValueError("action center must be a finite xy pair")
    origin = np.asarray(
        action["center_domain"]["origin_xy_m"], dtype=np.float64
    )
    if float(np.linalg.norm(center - origin)) > float(
        action["center_domain"]["max_radius_m"]
    ) + 1.0e-12:
        raise ValueError("action center is outside the Phase 1 domain")
    if not math.isclose(
        float(episode["radius_m"]),
        float(action["radius_m"]),
        rel_tol=0.0,
        abs_tol=1.0e-12,
    ):
        raise ValueError("cylinder radius is outside the Phase 1 domain")
    force = float(episode["normal_force_n"])
    force_bounds = action["normal_force_n"]
    if not float(force_bounds["minimum"]) <= force <= float(
        force_bounds["maximum"]
    ):
        raise ValueError("normal force is outside the Phase 1 domain")
    soil = episode.get("soil_parameters")
    if soil is None:
        soil = {
            "bekker_kphi": episode["bekker_kphi"],
            "mohr_friction_deg": episode["mohr_friction_deg"],
        }
    varied = contract["chrono"]["soil_parameters"]["varied"]
    for name in ("bekker_kphi", "mohr_friction_deg"):
        value = float(soil[name])
        if not float(varied[name]["minimum"]) <= value <= float(
            varied[name]["maximum"]
        ):
            raise ValueError(
                f"{name} is outside the Phase 1 domain"
            )


def build_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    prerequisites = require_prerequisites(config)
    paths = prerequisite_paths(config)
    dataset_plan = json.loads(paths["dataset_plan"].read_text(encoding="utf-8"))
    contract_path = paths["phase1_contract"]
    contract = load_contract(contract_path)
    if dataset_plan.get("contract_sha256") != fresh.sha256_file(contract_path):
        raise RuntimeError("dataset plan no longer matches the Phase 1 contract")
    if canonical_sha256(dataset_plan["episodes"]) != dataset_plan["episode_manifest_sha256"]:
        raise RuntimeError("frozen 88-episode manifest changed")
    episodes = selected_test_episodes(config, dataset_plan)
    for episode in episodes:
        validate_inference_domain(contract, episode)
    screening_plan = json.loads(
        paths["sensitivity_screening_plan"].read_text(encoding="utf-8")
    )
    sensitivity_cases = matched_sensitivity_cases(config, screening_plan)
    surface_input_sha256: dict[str, str] = {}
    for seed in sorted({int(item["initial_surface_seed"]) for item in episodes}):
        root = dataset.surface_input_root(config, contract, seed)
        for label, filename in (
            ("heightmap", "initial_heightmap_m.npy"),
            ("generator", "generator_summary.json"),
            ("qualification", "qualification_summary.json"),
        ):
            path = root / filename
            if not path.is_file():
                raise FileNotFoundError(f"missing qualified evaluation surface: {path}")
            surface_input_sha256[f"surface_{seed}:{label}"] = fresh.sha256_file(path)
        qualification = json.loads(
            (root / "qualification_summary.json").read_text(encoding="utf-8")
        )
        if not bool(qualification.get("qualified")):
            raise RuntimeError(f"evaluation surface {seed} is not qualified")
    sources = source_paths(config_path, config, contract)
    missing_sources = [str(path) for path in sources.values() if not path.is_file()]
    if missing_sources:
        raise FileNotFoundError(f"missing locked evaluation sources: {missing_sources}")
    selection = prerequisites["selection"]
    selected_artifacts: dict[str, Any] = {}
    training_root = repo_path(config["selection_summary"]).parent
    for variant, card in selection["selected"].items():
        seed = int(card["seed"])
        root = training_root / "models" / variant / f"seed_{seed}"
        selected_artifacts[variant] = {
            "seed": seed,
            "model_card_sha256": fresh.sha256_file(root / "model_card.json"),
            "checkpoint_sha256": fresh.sha256_file(root / "model.pt"),
            "history_sha256": fresh.sha256_file(root / "history.json"),
        }
    shuffle = parameter_shuffle_mapping(
        [item["episode_id"] for item in episodes],
        int(config["parameter_controls"]["shuffle_seed"]),
    )
    return {
        "schema_version": 1,
        "evaluation_id": config["evaluation_id"],
        "status": "frozen_after_validation_selection_before_first_test_target",
        "config_sha256": fresh.sha256_file(config_path),
        "source_sha256": {name: fresh.sha256_file(path) for name, path in sources.items()},
        "input_sha256": {name: fresh.sha256_file(path) for name, path in paths.items()},
        "surface_input_sha256": surface_input_sha256,
        "episode_manifest_sha256": dataset_plan["episode_manifest_sha256"],
        "test_lock_sha256": dataset_plan["test_lock_sha256"],
        "selected_test_manifest_sha256": canonical_sha256(episodes),
        "selection_summary_sha256": fresh.sha256_file(paths["selection_summary"]),
        "selected_model_artifacts": selected_artifacts,
        "uncertainty_calibration": selection["uncertainty_calibration"],
        "episodes": episodes,
        "counts": {"train": 0, "validation": 0, "test": 24},
        "holdout_groups": dict(Counter(item["holdout_group"] for item in episodes)),
        "surface_seeds": sorted({int(item["initial_surface_seed"]) for item in episodes}),
        "parameter_shuffle_mapping": shuffle,
        "parameter_shuffle_mapping_sha256": canonical_sha256(shuffle),
        "matched_sensitivity_cases": sensitivity_cases,
        "matched_sensitivity_manifest_sha256": canonical_sha256(sensitivity_cases),
        "test_targets_opened": False,
    }


STABLE_PLAN_KEYS = (
    "config_sha256",
    "source_sha256",
    "input_sha256",
    "surface_input_sha256",
    "episode_manifest_sha256",
    "test_lock_sha256",
    "selected_test_manifest_sha256",
    "selection_summary_sha256",
    "selected_model_artifacts",
    "uncertainty_calibration",
    "episodes",
    "parameter_shuffle_mapping",
    "matched_sensitivity_cases",
    "test_targets_opened",
)


def write_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    dataset_plan = json.loads(repo_path(config["dataset_plan"]).read_text(encoding="utf-8"))
    episodes = selected_test_episodes(config, dataset_plan)
    assert_test_targets_absent(config, episodes)
    if unlock_path(config).exists() or opened_path(config).exists():
        raise RuntimeError("test unlock/open marker exists before evaluation plan")
    plan = build_plan(config_path, config)
    path = plan_path(config)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        changed = [key for key in STABLE_PLAN_KEYS if existing.get(key) != plan.get(key)]
        if changed:
            raise RuntimeError(f"refusing to replace a different evaluation plan: {changed}")
        return existing
    write_json(path, plan)
    return plan


def load_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    path = plan_path(config)
    if not path.is_file():
        raise RuntimeError("evaluation plan is absent; selection-gated plan must run first")
    existing = json.loads(path.read_text(encoding="utf-8"))
    current = build_plan(config_path, config)
    changed = [key for key in STABLE_PLAN_KEYS if existing.get(key) != current.get(key)]
    if changed:
        raise RuntimeError(f"locked evaluation identity changed: {changed}")
    return existing


def unlock_test(config: Mapping[str, Any], plan: Mapping[str, Any]) -> dict[str, Any]:
    if opened_path(config).exists():
        raise RuntimeError("test targets have already been opened")
    assert_test_targets_absent(config, plan["episodes"])
    marker = {
        "schema_version": 1,
        "status": "test_generation_unlocked_after_model_selection",
        "evaluation_plan_sha256": fresh.sha256_file(plan_path(config)),
        "selection_summary_sha256": plan["selection_summary_sha256"],
        "selected_test_manifest_sha256": plan["selected_test_manifest_sha256"],
        "test_lock_sha256": plan["test_lock_sha256"],
        "target_count": 24,
        "targets_opened": False,
    }
    path = unlock_path(config)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != marker:
            raise RuntimeError("test unlock marker identity changed")
        return existing
    write_json(path, marker)
    return marker


def require_unlocked(config: Mapping[str, Any], plan: Mapping[str, Any]) -> dict[str, Any]:
    if not unlock_path(config).is_file():
        raise RuntimeError("test generation is locked; run the explicit unlock stage")
    marker = json.loads(unlock_path(config).read_text(encoding="utf-8"))
    if marker.get("evaluation_plan_sha256") != fresh.sha256_file(plan_path(config)):
        raise RuntimeError("test unlock marker references a different evaluation plan")
    if marker.get("selection_summary_sha256") != plan["selection_summary_sha256"]:
        raise RuntimeError("test unlock marker references different selected models")
    return marker


def choose_episodes(
    plan: Mapping[str, Any], requested: Sequence[str]
) -> list[dict[str, Any]]:
    episodes = [dict(item) for item in plan["episodes"]]
    by_id = {item["episode_id"]: item for item in episodes}
    unknown = sorted(set(requested) - set(by_id))
    if unknown:
        raise ValueError(f"unknown locked test episodes: {unknown}")
    return [by_id[item] for item in requested] if requested else episodes


def mark_targets_opened(
    config: Mapping[str, Any], plan: Mapping[str, Any]
) -> dict[str, Any]:
    require_unlocked(config, plan)
    marker = {
        "schema_version": 1,
        "status": "test_targets_opened_once",
        "evaluation_plan_sha256": fresh.sha256_file(plan_path(config)),
        "test_unlock_sha256": fresh.sha256_file(unlock_path(config)),
        "selection_summary_sha256": plan["selection_summary_sha256"],
        "selected_test_manifest_sha256": plan["selected_test_manifest_sha256"],
        "test_lock_sha256": plan["test_lock_sha256"],
        "target_count": 24,
        "targets_opened": True,
    }
    path = opened_path(config)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != marker:
            raise RuntimeError("test-open marker identity changed")
        return existing
    assert_test_targets_absent(config, plan["episodes"])
    write_json(path, marker)
    return marker


def require_opened(config: Mapping[str, Any], plan: Mapping[str, Any]) -> dict[str, Any]:
    if not opened_path(config).is_file():
        raise RuntimeError("test targets are not open; the Chrono stage must run first")
    marker = json.loads(opened_path(config).read_text(encoding="utf-8"))
    if marker.get("evaluation_plan_sha256") != fresh.sha256_file(plan_path(config)):
        raise RuntimeError("test-open marker references a different evaluation plan")
    if marker.get("test_unlock_sha256") != fresh.sha256_file(unlock_path(config)):
        raise RuntimeError("test-open marker references a different unlock event")
    if marker.get("selection_summary_sha256") != plan["selection_summary_sha256"]:
        raise RuntimeError("test-open marker references different selected models")
    return marker


def reference_episode_for_seed(
    plan: Mapping[str, Any], surface_seed: int
) -> dict[str, Any]:
    return next(
        dict(item)
        for item in plan["episodes"]
        if int(item["initial_surface_seed"]) == int(surface_seed)
    )


def build_test_bed(
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    plan: Mapping[str, Any],
    surface_seed: int,
) -> Path:
    root = dataset.prior_root(config, surface_seed)
    output = root / "metric_bed"
    expected = output / "particles_initial_mpm.ply", output / "ground_plane_metadata.json"
    if all(path.is_file() for path in expected):
        return output
    if output.exists():
        raise RuntimeError(f"refusing incomplete locked-test metric bed: {output}")
    episode = reference_episode_for_seed(plan, surface_seed)
    if not dataset.chrono_result(config, contract, episode).get("accepted"):
        raise RuntimeError("accepted locked-test Chrono episode required before bed build")
    chrono_dir = dataset.chrono_episode(config, episode["episode_id"])
    manifest, _action, initial, _valid = load_episode(chrono_dir)
    builder_contract = json.loads(
        repo_path(config["newton_prior"]["builder_contract"]).read_text(encoding="utf-8")
    )
    builder = builder_contract["builder"]
    metadata = write_common_base_metric_bed(
        output,
        initial,
        manifest,
        bed_depth_m=float(builder["nominal_bed_depth_m"]),
        particle_spacing_m=float(builder["particle_spacing_m"]),
        minimum_top_gap_fraction=float(builder["minimum_top_gap_fraction"]),
    )
    metadata["provenance"] = {
        "evaluation_plan_sha256": fresh.sha256_file(plan_path(config)),
        "test_unlock_sha256": fresh.sha256_file(unlock_path(config)),
        "test_open_sha256": fresh.sha256_file(opened_path(config)),
        "surface_seed": int(surface_seed),
        "reference_episode_id": episode["episode_id"],
        "reference_chrono_initial_sha256": fresh.sha256_file(
            chrono_dir / manifest["states"]["initial"]
        ),
        "loaded_or_post_unload_target_consumed": False,
    }
    write_json(output / "ground_plane_metadata.json", metadata)
    return output


def prepare_test_prior(
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    plan: Mapping[str, Any],
    surface_seed: int,
) -> Path:
    bed = build_test_bed(config, contract, plan, surface_seed)
    root = dataset.prior_root(config, surface_seed)
    preparation = root / "preparation"
    manifest_path = preparation / "newton_prepared_bed_manifest.json"
    if manifest_path.is_file():
        prepared = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not bool(prepared.get("accepted")):
            raise RuntimeError(f"existing test preparation rejected for surface {surface_seed}")
        return preparation
    if preparation.exists():
        raise RuntimeError(f"refusing incomplete locked-test preparation: {preparation}")
    episode = reference_episode_for_seed(plan, surface_seed)
    newton = contract["newton"]
    fresh.run_logged(
        [
            str(Path(config["execution"]["newton_python"]).resolve()),
            str(SCRIPT_DIR / "run_newton_prepared_bed.py"),
            "--config",
            str(repo_path(newton["base_config"])),
            "--particles-ply",
            str(bed / "particles_initial_mpm.ply"),
            "--metadata-json",
            str(bed / "ground_plane_metadata.json"),
            "--chrono-episode",
            str(dataset.chrono_episode(config, episode["episode_id"])),
            "--output-dir",
            str(preparation),
            "--device",
            str(config["execution"]["device"]),
            "--dt-s",
            str(newton["selected_dt_s"]),
            "--duration-s",
            str(newton["pre_settle_duration_s"]),
            "--required-duration-s",
            str(newton["pre_settle_required_duration_s"]),
            "--particle-speed-threshold-mps",
            str(newton["particle_speed_threshold_mps"]),
            "--center-crop-half-width-m",
            "0",
            "--speed-check-every",
            "1",
            "--qualification-run",
        ],
        root / "logs" / "newton_preparation.log",
        REPO_ROOT,
    )
    prepared = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not bool(prepared.get("accepted")):
        raise RuntimeError(f"test preparation rejected for surface {surface_seed}")
    return preparation


def run_test_newton(
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    plan: Mapping[str, Any],
    episode: Mapping[str, Any],
) -> Path:
    preparation = prepare_test_prior(
        config, contract, plan, int(episode["initial_surface_seed"])
    )
    response = dataset.response_root(config, episode["episode_id"])
    manifest_path = response / "newton_cylinder_manifest.json"
    if manifest_path.is_file():
        return response
    if response.exists():
        raise RuntimeError(f"refusing incomplete locked-test response: {response}")
    newton = contract["newton"]
    prior = config["newton_prior"]
    fresh.run_logged(
        [
            str(Path(config["execution"]["newton_python"]).resolve()),
            str(SCRIPT_DIR / "run_newton_cylinder_diagnostic.py"),
            "--config",
            str(repo_path(newton["base_config"])),
            "--prepared-dir",
            str(preparation),
            "--candidate-preparation",
            "--chrono-episode",
            str(dataset.chrono_episode(config, episode["episode_id"])),
            "--output-dir",
            str(response),
            "--device",
            str(config["execution"]["device"]),
            "--dt-s",
            str(newton["selected_dt_s"]),
            "--pre-settle-duration-s",
            str(newton["pre_settle_duration_s"]),
            "--pre-settle-required-duration-s",
            str(newton["pre_settle_required_duration_s"]),
            "--particle-speed-threshold-mps",
            str(newton["particle_speed_threshold_mps"]),
            "--observation-time-mode",
            str(prior["observation_time_mode"]),
            "--loaded-duration-s",
            str(prior["loaded_duration_s"]),
            "--residual-duration-s",
            str(prior["post_unload_duration_s"]),
            "--proxy-iterations",
            str(newton["proxy_iterations"]),
            "--rigid-substeps",
            str(newton["rigid_substeps"]),
            "--cylinder-friction-coefficient",
            str(newton["cylinder_friction_coefficient"]),
            "--cylinder-collider-mode",
            str(newton["collider_mode"]),
            "--cylinder-collider-segments",
            str(newton["collider_segments"]),
            "--cylinder-collision-guard-m",
            str(newton["collision_guard_m"]),
            "--cylinder-collision-bottom-inset-m",
            "0",
            "--cylinder-projection-threshold-m",
            str(newton["projection_threshold_m"]),
        ],
        dataset.episode_root(config, episode["episode_id"])
        / "logs"
        / "newton_response.log",
        REPO_ROOT,
    )
    return response


GUIDE_COMPONENTS = (
    "horizontal_position_error_m",
    "horizontal_speed_mps",
    "angular_speed_radps",
    "orientation_quaternion_error",
)


def evaluate_guide_contract(
    config: Mapping[str, Any], manifest: Mapping[str, Any]
) -> dict[str, Any]:
    cylinder = manifest["cylinder"]
    observed = cylinder["guide_constraint_error"]
    declared = config.get("guide_tolerances")
    if declared is None:
        tolerance = float(cylinder["guide_constraint_tolerance"])
        tolerances = {name: tolerance for name in GUIDE_COMPONENTS}
        checks = {
            name: abs(float(observed[name])) <= tolerance
            for name in GUIDE_COMPONENTS
        }
        passed = bool(cylinder["guide_constraint_passed"]) and all(checks.values())
        contract = "legacy_single_tolerance_and_manifest_boolean"
    else:
        tolerances = {name: float(declared[name]) for name in GUIDE_COMPONENTS}
        checks = {
            name: abs(float(observed[name])) <= tolerances[name]
            for name in GUIDE_COMPONENTS
        }
        passed = all(checks.values())
        contract = "prospective_component_specific_v2"
    return {
        "contract": contract,
        "passed": passed,
        "observed": {name: float(observed[name]) for name in GUIDE_COMPONENTS},
        "tolerances": tolerances,
        "checks": checks,
        "legacy_manifest_passed": bool(cylinder["guide_constraint_passed"]),
    }


def analyze_test_episode(
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    plan: Mapping[str, Any],
    episode: Mapping[str, Any],
) -> dict[str, Any]:
    episode_id = str(episode["episode_id"])
    chrono = dataset.chrono_result(config, contract, episode)
    preparation_path = (
        dataset.prior_root(config, int(episode["initial_surface_seed"]))
        / "preparation"
        / "newton_prepared_bed_manifest.json"
    )
    response = dataset.response_root(config, episode_id)
    response_path = response / "newton_cylinder_manifest.json"
    if not chrono.get("complete") or not preparation_path.is_file() or not response_path.is_file():
        return {
            "episode_id": episode_id,
            "split": "test",
            "holdout_group": episode["holdout_group"],
            "complete": False,
            "admitted": False,
        }
    prepared = json.loads(preparation_path.read_text(encoding="utf-8"))
    manifest = json.loads(response_path.read_text(encoding="utf-8"))
    metadata = json.loads(
        (
            dataset.prior_root(config, int(episode["initial_surface_seed"]))
            / "metric_bed"
            / "ground_plane_metadata.json"
        ).read_text(encoding="utf-8")
    )
    policy = dataset.admission_policy(contract)
    level_1 = policy["level_1_numerical_integrity"]
    level_2 = policy["level_2_interaction_artifact"]
    penetration = manifest["penetration"]
    particle_count = int(metadata["particle_count"])
    inside = int(penetration["max_inside_particle_centers"])
    spacing = float(contract["newton"]["metric_bed_source"]["particle_spacing_m"])
    timing = manifest.get("observation_timing_s", {})
    guide = evaluate_guide_contract(config, manifest)
    numerical = {
        "chrono_accepted": bool(chrono["accepted"]),
        "preparation_accepted": bool(prepared.get("accepted")),
        "preparation_converged": bool(manifest["preparation"]["convergence_passed"]),
        "finite": bool(manifest["finite"]),
        "guide": bool(guide["passed"]),
        "surface_cells": int(manifest["surface"]["valid_cells"])
        >= int(level_1["min_surface_valid_cells"]),
        "initial_support": float(manifest["surface"]["initial_match"]["valid_fraction"])
        >= float(level_1["min_initial_surface_valid_fraction"]),
        "independent_fixed_timing": timing.get("mode") == "independent_fixed"
        and timing.get("chrono_target_time_controls_newton") is False,
        "loaded_duration": math.isclose(
            float(timing.get("newton_loaded", -1.0)),
            float(config["newton_prior"]["loaded_duration_s"]),
            abs_tol=1.0e-12,
        ),
        "post_unload_duration": math.isclose(
            float(timing.get("newton_residual", -1.0)),
            float(config["newton_prior"]["post_unload_duration_s"]),
            abs_tol=1.0e-12,
        ),
        "state_schema_v2": int(manifest.get("state_archive", {}).get("schema_version", 0))
        == 2,
    }
    gross_depth = spacing * float(level_2["gross_penetration_fraction_of_particle_spacing"])
    interaction = {
        "within_gross_depth": float(penetration["max_center_penetration_m"])
        <= gross_depth,
        "within_gross_affected_fraction": float(inside / particle_count)
        <= float(level_2["gross_inside_particle_fraction"]),
    }
    tensor_manifest = dataset.export_tensors(config, contract, episode)
    tensor_checks = {
        name: bool(value)
        for name, value in tensor_manifest["checks"].items()
        if name != "no_test_target"
    }
    tensor_checks.update(
        {
            "test_access_authorized": opened_path(config).is_file(),
            "test_split_confirmed": episode["split"] == "test",
            "frozen_test_identity": episode["target_access"] == "locked",
            "original_no_test_guard_triggered": tensor_manifest["checks"].get(
                "no_test_target"
            )
            is False,
        }
    )
    locked_tensor_manifest = {
        **tensor_manifest,
        "schema_version": 2,
        "access_mode": "one_shot_locked_test_after_selection",
        "evaluation_plan_sha256": fresh.sha256_file(plan_path(config)),
        "test_open_sha256": fresh.sha256_file(opened_path(config)),
        "checks": tensor_checks,
    }
    tensor_root = dataset.episode_root(config, episode_id) / "tensors"
    write_json(tensor_root / "locked_test_tensor_manifest.json", locked_tensor_manifest)
    admitted = all(numerical.values()) and all(interaction.values()) and all(
        tensor_checks.values()
    )
    result = {
        "schema_version": 1,
        "episode_id": episode_id,
        "split": "test",
        "holdout_group": episode["holdout_group"],
        "input_sha256": episode["input_sha256"],
        "complete": True,
        "admitted": admitted,
        "strict_mechanics_qualified": bool(manifest.get("mechanics_qualified")),
        "numerical_checks": numerical,
        "guide_contract": guide,
        "interaction_artifact_checks": interaction,
        "interaction_observed": {
            "particle_count": particle_count,
            "max_inside_particle_centers": inside,
            "max_inside_particle_fraction": float(inside / particle_count),
            "max_center_penetration_m": float(penetration["max_center_penetration_m"]),
            "gross_depth_limit_m": gross_depth,
        },
        "locked_tensor_manifest": locked_tensor_manifest,
        "artifacts": {
            "chrono_episode": str(dataset.chrono_episode(config, episode_id).resolve()),
            "newton_prior": str(
                dataset.prior_root(config, int(episode["initial_surface_seed"])).resolve()
            ),
            "newton_response": str(response.resolve()),
            "tensors": str(tensor_root.resolve()),
        },
    }
    write_json(dataset.episode_root(config, episode_id) / "episode_summary.json", result)
    return result


def summarize_test_dataset(
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    episodes = [
        analyze_test_episode(config, contract, plan, episode)
        for episode in plan["episodes"]
    ]
    groups = Counter(item.get("holdout_group") for item in episodes)
    checks = {
        "episode_count": len(episodes) == 24,
        "test_count": all(item.get("split") == "test" for item in episodes),
        "holdout_groups": dict(groups) == plan["holdout_groups"],
        "all_complete": all(item["complete"] for item in episodes),
        "all_admitted": all(item["admitted"] for item in episodes),
        "unlock_identity": require_unlocked(config, plan)["selection_summary_sha256"]
        == plan["selection_summary_sha256"],
        "opened_once": opened_path(config).is_file(),
    }
    summary = {
        "schema_version": 1,
        "evaluation_id": config["evaluation_id"],
        "status": "passed" if all(checks.values()) else "failed_or_incomplete",
        "prediction_permitted": all(checks.values()),
        "counts": {"total": len(episodes), "test": len(episodes)},
        "holdout_groups": dict(groups),
        "checks": checks,
        "identity": {
            "evaluation_plan_sha256": fresh.sha256_file(plan_path(config)),
            "test_unlock_sha256": fresh.sha256_file(unlock_path(config)),
            "test_open_sha256": fresh.sha256_file(opened_path(config)),
            "selected_test_manifest_sha256": plan["selected_test_manifest_sha256"],
            "test_lock_sha256": plan["test_lock_sha256"],
        },
        "episodes": {item["episode_id"]: item for item in episodes},
    }
    write_json(output_root(config) / "test_dataset_summary.json", summary)
    return summary


def surface_metrics(
    prediction_m: np.ndarray,
    target_m: np.ndarray,
    initial_m: np.ndarray,
    mask: np.ndarray,
    *,
    grid_spacing_m: float,
    deformation_threshold_m: float,
    relative_x_m: np.ndarray | None = None,
    relative_y_m: np.ndarray | None = None,
) -> dict[str, float | int | None]:
    prediction = np.asarray(prediction_m, dtype=np.float64)
    target = np.asarray(target_m, dtype=np.float64)
    initial = np.asarray(initial_m, dtype=np.float64)
    selected = np.asarray(mask, dtype=bool)
    if prediction.shape != target.shape or prediction.shape != initial.shape or selected.shape != prediction.shape:
        raise ValueError("surface metric arrays must have identical shapes")
    selected &= np.isfinite(prediction) & np.isfinite(target) & np.isfinite(initial)
    if not np.any(selected):
        raise ValueError("surface metric mask is empty")
    error = prediction[selected] - target[selected]
    pred_dep = initial - prediction
    target_dep = initial - target
    cell_area = float(grid_spacing_m) ** 2
    result: dict[str, float | int | None] = {
        "cells": int(np.count_nonzero(selected)),
        "rmse_m": float(np.sqrt(np.mean(error * error))),
        "mae_m": float(np.mean(np.abs(error))),
        "max_abs_m": float(np.max(np.abs(error))),
        "signed_mean_m": float(np.mean(error)),
        "peak_depression_m": float(np.max(pred_dep[selected])),
        "target_peak_depression_m": float(np.max(target_dep[selected])),
        "mean_depression_m": float(np.mean(pred_dep[selected])),
        "target_mean_depression_m": float(np.mean(target_dep[selected])),
        "displaced_volume_m3": float(np.sum(np.maximum(pred_dep[selected], 0.0)) * cell_area),
        "target_displaced_volume_m3": float(np.sum(np.maximum(target_dep[selected], 0.0)) * cell_area),
        "deformed_fraction": float(np.mean(np.abs(pred_dep[selected]) >= deformation_threshold_m)),
        "target_deformed_fraction": float(np.mean(np.abs(target_dep[selected]) >= deformation_threshold_m)),
    }
    if relative_x_m is None or relative_y_m is None:
        result["deformation_centroid_x_m"] = None
        result["deformation_centroid_y_m"] = None
        return result
    relative_x = np.asarray(relative_x_m, dtype=np.float64)
    relative_y = np.asarray(relative_y_m, dtype=np.float64)
    if relative_x.shape != prediction.shape or relative_y.shape != prediction.shape:
        raise ValueError("centroid coordinate arrays must match the surface shape")
    weights = np.where(selected, np.maximum(np.abs(pred_dep) - deformation_threshold_m, 0.0), 0.0)
    weight_sum = float(np.sum(weights))
    result["deformation_centroid_x_m"] = (
        float(np.sum(weights * relative_x) / weight_sum) if weight_sum > 0.0 else None
    )
    result["deformation_centroid_y_m"] = (
        float(np.sum(weights * relative_y) / weight_sum) if weight_sum > 0.0 else None
    )
    return result


def bootstrap_interval(
    values: Sequence[float],
    *,
    statistic: Callable[[np.ndarray], float] = np.median,
    resamples: int,
    confidence: float,
    seed: int,
) -> dict[str, float | int]:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or array.size < 2 or not np.isfinite(array).all():
        raise ValueError("bootstrap requires at least two finite episode values")
    if resamples <= 0 or not 0.0 < confidence < 1.0:
        raise ValueError("invalid bootstrap contract")
    rng = np.random.default_rng(int(seed))
    samples = rng.integers(0, array.size, size=(int(resamples), array.size))
    estimates = np.asarray([statistic(array[index]) for index in samples], dtype=np.float64)
    alpha = 0.5 * (1.0 - float(confidence))
    return {
        "episode_count": int(array.size),
        "estimate": float(statistic(array)),
        "lower": float(np.quantile(estimates, alpha)),
        "upper": float(np.quantile(estimates, 1.0 - alpha)),
        "confidence": float(confidence),
        "resamples": int(resamples),
        "seed": int(seed),
    }


CHECKPOINTS = ("loaded", "post_unload")
LOCAL_REGIONS = ("footprint", "twice_radius")
PREDICTORS = ("B0", "B1", "B2", "B3", "H0", "H1", "H2")
NEURAL_VARIANTS = ("B3", "H0", "H1", "H2")


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as archive:
        return {name: np.array(archive[name], copy=True) for name in archive.files}


def _training_modules() -> tuple[Any, Any, Any]:
    """Import CUDA-dependent modules only for prediction/report execution."""
    torch = importlib.import_module("torch")
    trainer = importlib.import_module("train_phase1_bed_state")
    lift = importlib.import_module("phase1_particle_lift")
    return torch, trainer, lift


def selected_model_paths(
    config: Mapping[str, Any], plan: Mapping[str, Any]
) -> dict[str, Path]:
    root = repo_path(config["selection_summary"]).parent / "models"
    paths: dict[str, Path] = {}
    for variant in NEURAL_VARIANTS:
        selected = plan["selected_model_artifacts"][variant]
        path = root / variant / f"seed_{int(selected['seed'])}" / "model.pt"
        if not path.is_file():
            raise RuntimeError(f"selected checkpoint is missing: {path}")
        if fresh.sha256_file(path) != selected["checkpoint_sha256"]:
            raise RuntimeError(f"selected checkpoint identity changed: {variant}")
        paths[variant] = path
    return paths


def load_selected_networks(
    config: Mapping[str, Any], plan: Mapping[str, Any]
) -> tuple[Any, Any, dict[str, Any], Mapping[str, Any], Mapping[str, Any]]:
    torch, trainer, _lift = _training_modules()
    training_config = trainer.load_config(repo_path(config["training_config"]))
    normalization = json.loads(
        repo_path(config["normalization"]).read_text(encoding="utf-8")
    )
    selection = json.loads(
        repo_path(config["selection_summary"]).read_text(encoding="utf-8")
    )
    device = torch.device(config["execution"]["device"])
    networks: dict[str, Any] = {}
    for variant, checkpoint_path in selected_model_paths(config, plan).items():
        network = trainer.instantiate_network(training_config, variant, device)
        checkpoint = torch.load(checkpoint_path, map_location=device)
        if checkpoint.get("variant") != variant:
            raise RuntimeError(f"checkpoint variant changed: {variant}")
        network.load_state_dict(checkpoint["state_dict"], strict=True)
        network.eval()
        networks[variant] = network
    return torch, trainer, networks, normalization, selection


def phase0_mlp_predictions(
    config: Mapping[str, Any],
    episode: Mapping[str, Any],
    inputs: Mapping[str, np.ndarray],
) -> np.ndarray:
    """Apply the frozen Phase 0 multi-load MLP without changing its model file."""
    model_path = repo_path(config["phase0_model"])
    with np.load(model_path, allow_pickle=False) as archive:
        required = (
            "feature_mean",
            "feature_std",
            "w1",
            "b1",
            "w2",
            "b2",
            "max_correction_m",
        )
        model = {name: np.asarray(archive[name]) for name in required}
    radius = float(episode["radius_m"])
    dx = np.asarray(inputs["action_relative_x_m"], dtype=np.float64) / radius
    dy = np.asarray(inputs["action_relative_y_m"], dtype=np.float64) / radius
    radial = np.sqrt(dx * dx + dy * dy)
    taper = np.zeros_like(radial)
    taper[radial <= 1.5] = 1.0
    transition = (radial > 1.5) & (radial < 2.0)
    taper[transition] = 0.5 * (
        1.0 + np.cos(np.pi * (radial[transition] - 1.5) / 0.5)
    )
    response = dataset.response_root(config, str(episode["episode_id"]))
    newton_initial = np.load(
        response / "initial_heightmap_m.npy", allow_pickle=False
    )
    initial = np.asarray(inputs["initial_height_m"], dtype=np.float64)
    alignment = initial - np.asarray(newton_initial, dtype=np.float64)
    force = float(episode["normal_force_n"]) / 30.65625
    predictions = []
    for phase_index, phase_value in enumerate((-1.0, 1.0)):
        displacement = np.asarray(
            inputs[
                "newton_loaded_displacement_m"
                if phase_index == 0
                else "newton_post_unload_displacement_m"
            ],
            dtype=np.float64,
        )
        features = np.stack(
            (
                dx,
                dy,
                radial,
                radial - 1.0,
                np.full_like(dx, phase_value),
                displacement,
                alignment,
                np.full_like(dx, force),
            ),
            axis=-1,
        )
        flat = features.reshape(-1, features.shape[-1])
        normalized = (flat - model["feature_mean"]) / model["feature_std"]
        hidden = np.tanh(normalized @ model["w1"] + model["b1"])
        bounded = np.tanh(hidden @ model["w2"] + model["b2"]).reshape(
            radial.shape
        )
        correction = float(model["max_correction_m"]) * taper * bounded
        # Preserve the frozen Phase 0 baseline exactly: its correction is
        # applied to the Newton height map, not to the Phase 1 aligned hybrid
        # base (Chrono initial plus Newton displacement).
        predictions.append(
            np.asarray(newton_initial, dtype=np.float64)
            + displacement
            + correction
        )
    return np.stack(predictions).astype(np.float32)


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
    condition = (
        arrays["global_condition"]
        if global_condition is None
        else np.asarray(global_condition, dtype=np.float32)
    )
    base = (
        np.stack((arrays["initial"], arrays["initial"]))
        if network.base_state == "initial"
        else arrays["hybrid"]
    )
    with torch.no_grad():
        result = network(
            torch.from_numpy(
                np.asarray(arrays["spatial"], dtype=np.float32)
            )[None].to(device),
            torch.from_numpy(condition.astype(np.float32))[None].to(device),
            torch.from_numpy(np.asarray(base, dtype=np.float32))[None].to(
                device
            ),
            torch.tensor(
                normalization["correction_scale_m"],
                dtype=torch.float32,
                device=device,
            ),
            torch.from_numpy(
                np.asarray(arrays["taper"], dtype=np.float32)
            )[None, None].to(device),
        )
    height = (
        result["height_m"][0].detach().cpu().numpy().astype(np.float32)
    )
    deviation = (
        torch.exp(0.5 * result["log_variance_m2"])[0]
        .detach()
        .cpu()
        .numpy()
        .astype(np.float32)
    )
    return height, deviation


def metric_masks(inputs: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
    valid = np.asarray(inputs["valid_support"], dtype=bool)
    # Phase 1 fixes the cylinder radius at 35 mm.
    radius = 0.035
    return {
        "footprint": np.asarray(inputs["action_footprint"], dtype=bool) & valid,
        "twice_radius": (
            np.asarray(
                inputs["action_signed_distance_m"], dtype=np.float64
            )
            <= radius
        )
        & valid,
        "valid_bed": valid,
    }


def recovery_metrics(
    initial: np.ndarray,
    loaded: np.ndarray,
    post: np.ndarray,
    mask: np.ndarray,
    grid_spacing_m: float,
) -> dict[str, float]:
    selected = np.asarray(mask, dtype=bool)
    loaded_dep = np.maximum(
        np.asarray(initial) - np.asarray(loaded), 0.0
    )
    post_dep = np.maximum(np.asarray(initial) - np.asarray(post), 0.0)
    loaded_peak = float(np.max(loaded_dep[selected]))
    post_peak = float(np.max(post_dep[selected]))
    cell_area = float(grid_spacing_m) ** 2
    loaded_volume = float(np.sum(loaded_dep[selected]) * cell_area)
    post_volume = float(np.sum(post_dep[selected]) * cell_area)
    return {
        "peak_recovery_m": loaded_peak - post_peak,
        "volume_recovery_m3": loaded_volume - post_volume,
        "peak_recovery_fraction": (loaded_peak - post_peak)
        / max(loaded_peak, 1.0e-12),
        "volume_recovery_fraction": (loaded_volume - post_volume)
        / max(loaded_volume, 1.0e-12),
    }


def episode_prediction_metrics(
    config: Mapping[str, Any],
    inputs: Mapping[str, np.ndarray],
    targets: Mapping[str, np.ndarray],
    predictions: Mapping[str, np.ndarray],
    half_widths: Mapping[str, np.ndarray],
) -> tuple[dict[str, Any], dict[str, Any]]:
    initial = np.asarray(inputs["initial_height_m"], dtype=np.float64)
    target = np.stack(
        (
            np.asarray(
                targets["chrono_loaded_height_m"], dtype=np.float64
            ),
            np.asarray(
                targets["chrono_post_unload_height_m"], dtype=np.float64
            ),
        )
    )
    masks = metric_masks(inputs)
    spacing = 0.005
    deformation_threshold = float(
        config["metrics"]["deformation_threshold_m"]
    )
    relative_x = np.asarray(
        inputs["action_relative_x_m"], dtype=np.float64
    )
    relative_y = np.asarray(
        inputs["action_relative_y_m"], dtype=np.float64
    )
    metrics: dict[str, Any] = {}
    uncertainty: dict[str, Any] = {}
    for name, prediction in predictions.items():
        values = np.asarray(prediction, dtype=np.float64)
        if (
            values.shape != target.shape
            or not np.isfinite(values[:, masks["valid_bed"]]).all()
        ):
            raise ValueError(
                f"prediction is nonfinite or has the wrong shape: {name}"
            )
        phases: dict[str, Any] = {}
        for phase_index, checkpoint in enumerate(CHECKPOINTS):
            phases[checkpoint] = {
                region: surface_metrics(
                    values[phase_index],
                    target[phase_index],
                    initial,
                    mask,
                    grid_spacing_m=spacing,
                    deformation_threshold_m=deformation_threshold,
                    relative_x_m=relative_x,
                    relative_y_m=relative_y,
                )
                for region, mask in masks.items()
            }
        phases["recovery"] = {
            "prediction": recovery_metrics(
                initial,
                values[0],
                values[1],
                masks["twice_radius"],
                spacing,
            ),
            "target": recovery_metrics(
                initial,
                target[0],
                target[1],
                masks["twice_radius"],
                spacing,
            ),
        }
        metrics[name] = phases
        if name in half_widths:
            widths = np.asarray(half_widths[name], dtype=np.float64)
            checkpoint_values: dict[str, Any] = {}
            for phase_index, checkpoint in enumerate(CHECKPOINTS):
                selected = masks["twice_radius"]
                covered = (
                    np.abs(values[phase_index] - target[phase_index])
                    <= widths[phase_index]
                )
                checkpoint_values[checkpoint] = {
                    "covered_cells": int(
                        np.count_nonzero(covered & selected)
                    ),
                    "cells": int(np.count_nonzero(selected)),
                    "coverage_fraction": float(np.mean(covered[selected])),
                    "mean_half_width_m": float(
                        np.mean(widths[phase_index][selected])
                    ),
                }
            uncertainty[name] = checkpoint_values
    return metrics, uncertainty


def lift_predictions(
    config: Mapping[str, Any],
    plan: Mapping[str, Any],
    episode: Mapping[str, Any],
    inputs: Mapping[str, np.ndarray],
    predictions: Mapping[str, np.ndarray],
    prediction_root: Path,
) -> dict[str, Any]:
    _torch, _trainer, lift = _training_modules()
    valid = np.asarray(inputs["valid_support"], dtype=bool)
    action = np.asarray(inputs["action_phase"], dtype=np.float64)
    center_x, center_y = action[0, :2]
    x_coordinates = (
        np.asarray(inputs["action_relative_x_m"], dtype=np.float64)[0]
        + center_x
    )
    y_coordinates = (
        np.asarray(inputs["action_relative_y_m"], dtype=np.float64)[:, 0]
        + center_y
    )
    training_config = json.loads(
        repo_path(config["training_config"]).read_text(encoding="utf-8")
    )
    lift_config = training_config["particle_lift"]
    response = dataset.response_root(config, str(episode["episode_id"]))
    audits: dict[str, Any] = {}
    for variant in NEURAL_VARIANTS:
        variant_audits: dict[str, Any] = {}
        model_identity = (
            f"{variant}:seed={plan['selected_model_artifacts'][variant]['seed']}:"
            f"sha256={plan['selected_model_artifacts'][variant]['checkpoint_sha256']}"
        )
        for phase_index, checkpoint in enumerate(CHECKPOINTS):
            state_label = "loaded" if checkpoint == "loaded" else "residual"
            source = response / f"newton_state_{state_label}.npz"
            surface_path = (
                prediction_root / f"{variant}_{checkpoint}_surface_m.npy"
            )
            np.save(
                surface_path,
                np.asarray(predictions[variant][phase_index], dtype=np.float32),
            )
            with np.load(source, allow_pickle=False) as archive:
                positions = np.asarray(archive["position_m"])
            corrected, displacement, _source_surface = (
                lift.lift_surface_to_particles(
                    positions,
                    predictions[variant][phase_index],
                    valid,
                    x_coordinates,
                    y_coordinates,
                    cutoff_depth_m=float(lift_config["cutoff_depth_m"]),
                )
            )
            destination = (
                prediction_root
                / "corrected_particles"
                / variant
                / f"{checkpoint}.npz"
            )
            lift.write_corrected_state(
                source,
                destination,
                corrected,
                displacement,
                model_id=model_identity,
            )
            audit = lift.audit_corrected_state(
                source,
                destination,
                surface_path,
                valid,
                x_coordinates,
                y_coordinates,
                model_id=model_identity,
                surface_tolerance_m=float(
                    lift_config["surface_reproduction_tolerance_m"]
                ),
            )
            variant_audits[checkpoint] = audit
            write_json(
                prediction_root
                / "corrected_particles"
                / variant
                / f"{checkpoint}_audit.json",
                audit,
            )
        audits[variant] = variant_audits
    return audits


def predict_test_episode(
    config: Mapping[str, Any],
    plan: Mapping[str, Any],
    episode: Mapping[str, Any],
    runtime: tuple[
        Any,
        Any,
        dict[str, Any],
        Mapping[str, Any],
        Mapping[str, Any],
    ],
) -> dict[str, Any]:
    torch, trainer, networks, normalization, selection = runtime
    episode_id = str(episode["episode_id"])
    prediction_root = (
        dataset.episode_root(config, episode_id) / "predictions"
    )
    summary_path = prediction_root / "prediction_summary.json"
    if summary_path.is_file():
        existing = json.loads(summary_path.read_text(encoding="utf-8"))
        if existing.get("selected_model_artifacts") != plan[
            "selected_model_artifacts"
        ]:
            raise RuntimeError(
                f"existing prediction identity changed: {episode_id}"
            )
        prediction_archive = (
            prediction_root / "predicted_surfaces.npz"
        )
        if (
            not prediction_archive.is_file()
            or fresh.sha256_file(prediction_archive)
            != existing.get("prediction_archive_sha256")
        ):
            raise RuntimeError(
                f"existing prediction archive changed: {episode_id}"
            )
        for variant in NEURAL_VARIANTS:
            for checkpoint in CHECKPOINTS:
                audit = existing["particle_audits"][variant][
                    checkpoint
                ]
                corrected = (
                    prediction_root
                    / "corrected_particles"
                    / variant
                    / f"{checkpoint}.npz"
                )
                surface = (
                    prediction_root
                    / f"{variant}_{checkpoint}_surface_m.npy"
                )
                if (
                    not corrected.is_file()
                    or fresh.sha256_file(corrected)
                    != audit["corrected_state_sha256"]
                    or not surface.is_file()
                    or fresh.sha256_file(surface)
                    != audit["predicted_surface_sha256"]
                ):
                    raise RuntimeError(
                        "existing particle-lift artifact changed: "
                        f"{episode_id}:{variant}:{checkpoint}"
                    )
        return existing
    if prediction_root.exists():
        raise RuntimeError(
            f"refusing incomplete prediction output: {prediction_root}"
        )
    prediction_root.mkdir(parents=True)
    tensor_root = dataset.episode_root(config, episode_id) / "tensors"
    inputs = _load_npz(tensor_root / "model_inputs.npz")
    targets = _load_npz(tensor_root / "targets.npz")
    arrays = inference_arrays(trainer, inputs, normalization)
    device = torch.device(config["execution"]["device"])
    response = dataset.response_root(config, episode_id)
    raw_newton = np.stack(
        (
            np.load(
                response / "loaded_heightmap_m.npy",
                allow_pickle=False,
            ),
            np.load(
                response / "residual_heightmap_m.npy",
                allow_pickle=False,
            ),
        )
    ).astype(np.float32)
    predictions: dict[str, np.ndarray] = {
        "B0": np.stack(
            (arrays["initial"], arrays["initial"])
        ).astype(np.float32),
        "B1": raw_newton,
        "B2": phase0_mlp_predictions(config, episode, inputs),
    }
    deviations: dict[str, np.ndarray] = {}
    for variant, network in networks.items():
        height, deviation = infer_network(
            torch, network, arrays, normalization, device
        )
        predictions[variant] = height
        deviations[variant] = deviation
    donor_id = plan["parameter_shuffle_mapping"][episode_id]
    donor_inputs = _load_npz(
        dataset.episode_root(config, donor_id)
        / "tensors"
        / "model_inputs.npz"
    )
    donor_soil = np.asarray(
        donor_inputs["soil_parameters"], dtype=np.float32
    )
    global_mean = np.asarray(
        normalization["global_mean"], dtype=np.float32
    )
    global_std = np.asarray(normalization["global_std"], dtype=np.float32)
    shuffled_raw = np.asarray(
        arrays["global_raw"], dtype=np.float32
    ).copy()
    shuffled_raw[3:] = donor_soil
    shuffled_condition = (shuffled_raw - global_mean) / global_std
    constant_condition = np.asarray(
        arrays["global_condition"], dtype=np.float32
    ).copy()
    constant_condition[3:] = 0.0
    predictions["H1_shuffled_p"], _ = infer_network(
        torch,
        networks["H1"],
        arrays,
        normalization,
        device,
        global_condition=shuffled_condition,
    )
    predictions["H1_constant_p"], _ = infer_network(
        torch,
        networks["H1"],
        arrays,
        normalization,
        device,
        global_condition=constant_condition,
    )
    half_widths: dict[str, np.ndarray] = {}
    for variant, deviation in deviations.items():
        calibration = selection["uncertainty_calibration"][variant]
        multipliers = np.asarray(
            [
                calibration["loaded_multiplier"],
                calibration["post_unload_multiplier"],
            ],
            dtype=np.float32,
        )[:, None, None]
        half_widths[variant] = deviation * multipliers
    metrics, uncertainty = episode_prediction_metrics(
        config, inputs, targets, predictions, half_widths
    )
    prediction_archive = prediction_root / "predicted_surfaces.npz"
    np.savez_compressed(
        prediction_archive,
        **{
            f"{name}_height_m": value
            for name, value in predictions.items()
        },
        **{
            f"{name}_half_width_m": value
            for name, value in half_widths.items()
        },
    )
    particle_audits = lift_predictions(
        config, plan, episode, inputs, predictions, prediction_root
    )
    valid = np.asarray(inputs["valid_support"], dtype=bool)
    scales = np.asarray(
        normalization["correction_scale_m"], dtype=np.float64
    )
    output_checks: dict[str, Any] = {}
    for variant in NEURAL_VARIANTS:
        base = (
            np.stack((arrays["initial"], arrays["initial"]))
            if networks[variant].base_state == "initial"
            else arrays["hybrid"]
        )
        correction = (
            np.asarray(predictions[variant], dtype=np.float64)
            - np.asarray(base)
        )
        output_checks[variant] = {
            "finite_on_valid_support": bool(
                np.isfinite(predictions[variant][:, valid]).all()
            ),
            "outside_support_unchanged": bool(
                np.allclose(
                    predictions[variant][:, ~valid],
                    np.asarray(base)[:, ~valid],
                    rtol=0.0,
                    atol=1.0e-7,
                )
            ),
            "within_correction_bound": bool(
                all(
                    float(np.max(np.abs(correction[index])))
                    <= float(scales[index]) + 1.0e-7
                    for index in range(2)
                )
            ),
            "particle_lift_passed": all(
                particle_audits[variant][checkpoint]["all_checks_pass"]
                for checkpoint in CHECKPOINTS
            ),
        }
    result = {
        "schema_version": 1,
        "episode_id": episode_id,
        "holdout_group": episode["holdout_group"],
        "prediction_archive_sha256": fresh.sha256_file(
            prediction_archive
        ),
        "selected_model_artifacts": plan["selected_model_artifacts"],
        "parameter_control": {
            "shuffled_soil_source_episode": donor_id,
            "constant_soil_parameters": "training_mean_normalized_to_zero",
        },
        "metrics": metrics,
        "uncertainty": uncertainty,
        "output_checks": output_checks,
        "particle_audits": particle_audits,
        "all_output_checks_pass": all(
            all(checks.values()) for checks in output_checks.values()
        ),
    }
    write_json(
        prediction_root / "prediction_summary.json", result
    )
    return result


def paired_bootstrap_difference(
    reference: Sequence[float],
    comparator: Sequence[float],
    *,
    config: Mapping[str, Any],
    seed_offset: int = 0,
) -> dict[str, float | int]:
    first = np.asarray(reference, dtype=np.float64)
    second = np.asarray(comparator, dtype=np.float64)
    if first.shape != second.shape:
        raise ValueError(
            "paired bootstrap inputs must have identical shapes"
        )
    return bootstrap_interval(
        second - first,
        resamples=int(config["metrics"]["bootstrap_resamples"]),
        confidence=float(config["metrics"]["bootstrap_confidence"]),
        seed=int(config["metrics"]["bootstrap_seed"])
        + int(seed_offset),
    )


def aggregate_prediction_results(
    config: Mapping[str, Any], results: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    if len(results) != 24:
        raise ValueError(
            "locked prediction aggregation requires 24 episodes"
        )
    by_id = {str(item["episode_id"]): item for item in results}
    if len(by_id) != 24:
        raise ValueError("prediction episode identities must be unique")

    def rmse(
        predictor: str,
        checkpoint: str,
        region: str,
        group: str | None = None,
    ) -> list[float]:
        selected = sorted(
            by_id.values(), key=lambda item: str(item["episode_id"])
        )
        if group is not None:
            selected = [
                item
                for item in selected
                if item["holdout_group"] == group
            ]
        return [
            float(
                item["metrics"][predictor][checkpoint][region][
                    "rmse_m"
                ]
            )
            for item in selected
        ]

    thresholds = config["success_thresholds"]
    aggregate: dict[str, Any] = {}
    for predictor in (
        *PREDICTORS,
        "H1_shuffled_p",
        "H1_constant_p",
    ):
        aggregate[predictor] = {}
        for phase_index, checkpoint in enumerate(CHECKPOINTS):
            aggregate[predictor][checkpoint] = {}
            for region_index, region in enumerate(
                config["metrics"]["regions"]
            ):
                values = rmse(predictor, checkpoint, region)
                aggregate[predictor][checkpoint][region] = (
                    bootstrap_interval(
                        values,
                        resamples=int(
                            config["metrics"]["bootstrap_resamples"]
                        ),
                        confidence=float(
                            config["metrics"]["bootstrap_confidence"]
                        ),
                        seed=int(config["metrics"]["bootstrap_seed"])
                        + 100 * phase_index
                        + region_index,
                    )
                )

    checks: dict[str, bool] = {}
    details: dict[str, Any] = {}
    for checkpoint in CHECKPOINTS:
        for region in LOCAL_REGIONS:
            h1 = np.asarray(rmse("H1", checkpoint, region))
            raw = np.asarray(rmse("B1", checkpoint, region))
            zero = np.asarray(rmse("B0", checkpoint, region))
            phase0 = np.asarray(rmse("B2", checkpoint, region))
            reduction_raw = 1.0 - float(
                np.median(h1) / np.median(raw)
            )
            reduction_phase0 = 1.0 - float(
                np.median(h1) / np.median(phase0)
            )
            improvement_fraction = float(
                np.mean((h1 < raw) & (h1 < zero))
            )
            tolerance = np.maximum(
                float(
                    thresholds[
                        "maximum_episode_regression_fraction_vs_raw_newton"
                    ]
                )
                * raw,
                float(
                    thresholds[
                        "maximum_episode_regression_absolute_m"
                    ]
                ),
            )
            no_bad_tail = bool(np.all(h1 <= raw + tolerance))
            key = f"{checkpoint}:{region}"
            details[key] = {
                "h1_median_reduction_vs_raw_newton": reduction_raw,
                "h1_median_reduction_vs_phase0_mlp": reduction_phase0,
                "h1_episode_improvement_fraction_vs_raw_and_no_deformation": improvement_fraction,
                "no_episode_exceeds_raw_newton_regression_tolerance": no_bad_tail,
                "raw_newton_minus_h1_rmse_m": paired_bootstrap_difference(
                    h1,
                    raw,
                    config=config,
                    seed_offset=5000,
                ),
                "phase0_mlp_minus_h1_rmse_m": paired_bootstrap_difference(
                    h1,
                    phase0,
                    config=config,
                    seed_offset=5001,
                ),
            }
            checks[f"h1_vs_raw:{key}"] = reduction_raw >= float(
                thresholds["h1_median_reduction_vs_raw_newton"]
            )
            checks[f"h1_vs_phase0:{key}"] = reduction_phase0 >= float(
                thresholds["h1_median_reduction_vs_phase0_mlp"]
            )
            checks[f"h1_episode_fraction:{key}"] = (
                improvement_fraction
                >= float(
                    thresholds[
                        "h1_episode_improvement_fraction_vs_raw_and_no_deformation"
                    ]
                )
            )
            checks[f"h1_failure_tail:{key}"] = no_bad_tail

    joint_details: dict[str, Any] = {}
    material_details: dict[str, Any] = {}
    parameter_controls: dict[str, Any] = {}
    for phase_index, checkpoint in enumerate(CHECKPOINTS):
        for region_index, region in enumerate(LOCAL_REGIONS):
            h1_joint = np.asarray(
                rmse(
                    "H1",
                    checkpoint,
                    region,
                    "joint_combination",
                )
            )
            b3_joint = np.asarray(
                rmse(
                    "B3",
                    checkpoint,
                    region,
                    "joint_combination",
                )
            )
            key = f"{checkpoint}:{region}"
            joint_details[key] = {
                "h1_median_rmse_m": float(np.median(h1_joint)),
                "b3_median_rmse_m": float(np.median(b3_joint)),
                "b3_minus_h1_rmse_m": paired_bootstrap_difference(
                    h1_joint,
                    b3_joint,
                    config=config,
                    seed_offset=6000
                    + 10 * phase_index
                    + region_index,
                ),
            }
            checks[f"h1_beats_b3_joint:{key}"] = float(
                np.median(h1_joint)
            ) < float(np.median(b3_joint))

            h1_material = np.asarray(
                rmse(
                    "H1",
                    checkpoint,
                    region,
                    "unseen_material_combination",
                )
            )
            h0_material = np.asarray(
                rmse(
                    "H0",
                    checkpoint,
                    region,
                    "unseen_material_combination",
                )
            )
            reduction = 1.0 - float(
                np.median(h1_material) / np.median(h0_material)
            )
            material_details[key] = {
                "h1_median_reduction_vs_h0": reduction,
                "h0_minus_h1_rmse_m": paired_bootstrap_difference(
                    h1_material,
                    h0_material,
                    config=config,
                    seed_offset=7000
                    + 10 * phase_index
                    + region_index,
                ),
            }
            checks[f"h1_beats_h0_material:{key}"] = (
                reduction
                >= float(
                    thresholds[
                        "h1_median_reduction_vs_h0_on_material_holdout"
                    ]
                )
            )

            h1 = rmse("H1", checkpoint, region)
            shuffled = rmse("H1_shuffled_p", checkpoint, region)
            constant = rmse("H1_constant_p", checkpoint, region)
            shuffled_interval = paired_bootstrap_difference(
                h1,
                shuffled,
                config=config,
                seed_offset=1000
                + 10 * phase_index
                + region_index,
            )
            constant_interval = paired_bootstrap_difference(
                h1,
                constant,
                config=config,
                seed_offset=2000
                + 10 * phase_index
                + region_index,
            )
            parameter_controls[key] = {
                "shuffle_minus_h1_rmse_m": shuffled_interval,
                "constant_minus_h1_rmse_m": constant_interval,
            }
            checks[f"parameter_shuffle_degrades:{key}"] = float(
                shuffled_interval["lower"]
            ) > float(
                config["parameter_controls"][
                    "minimum_shuffle_degradation_m"
                ]
            )
            checks[f"parameter_constant_degrades:{key}"] = float(
                constant_interval["lower"]
            ) > float(
                config["parameter_controls"][
                    "minimum_constant_degradation_m"
                ]
            )

    uncertainty: dict[str, Any] = {}
    for variant in NEURAL_VARIANTS:
        uncertainty[variant] = {}
        for checkpoint in CHECKPOINTS:
            values = [
                float(
                    item["uncertainty"][variant][checkpoint][
                        "coverage_fraction"
                    ]
                )
                for item in by_id.values()
            ]
            interval = bootstrap_interval(
                values,
                statistic=np.mean,
                resamples=int(
                    config["metrics"]["bootstrap_resamples"]
                ),
                confidence=float(
                    config["metrics"]["bootstrap_confidence"]
                ),
                seed=int(config["metrics"]["bootstrap_seed"]) + 3000,
            )
            uncertainty[variant][checkpoint] = interval
            if variant == "H1":
                checks[f"h1_uncertainty_coverage:{checkpoint}"] = (
                    float(
                        thresholds["uncertainty_coverage_minimum"]
                    )
                    <= float(interval["estimate"])
                    <= float(
                        thresholds["uncertainty_coverage_maximum"]
                    )
                )

    latent: dict[str, Any] = {}
    latent_neutral = True
    latent_improved = True
    for phase_index, checkpoint in enumerate(CHECKPOINTS):
        for region_index, region in enumerate(LOCAL_REGIONS):
            h1 = np.asarray(rmse("H1", checkpoint, region))
            h2 = np.asarray(rmse("H2", checkpoint, region))
            interval = paired_bootstrap_difference(
                h2,
                h1,
                config=config,
                seed_offset=4000
                + 10 * phase_index
                + region_index,
            )
            tolerance = np.maximum(
                float(
                    thresholds[
                        "maximum_episode_regression_fraction_vs_raw_newton"
                    ]
                )
                * h1,
                float(
                    thresholds[
                        "maximum_episode_regression_absolute_m"
                    ]
                ),
            )
            no_worse_tail = bool(np.all(h2 <= h1 + tolerance))
            key = f"{checkpoint}:{region}"
            latent[key] = {
                "h1_minus_h2_rmse_m": interval,
                "h2_no_worse_failure_tail": no_worse_tail,
            }
            latent_improved &= (
                float(interval["lower"]) > 0.0 and no_worse_tail
            )
            latent_neutral &= (
                float(interval["upper"]) >= 0.0
                and no_worse_tail
            )
    latent_status = (
        "improves_prediction"
        if latent_improved
        else "neutral_without_worse_tail"
        if latent_neutral
        else "worse_or_solver_artifact"
    )
    checks["particle_state_integrity"] = all(
        bool(item["all_output_checks_pass"])
        for item in by_id.values()
    )
    return {
        "aggregate_metrics": aggregate,
        "accuracy_details": details,
        "joint_baseline_details": joint_details,
        "material_ablation_details": material_details,
        "parameter_controls": parameter_controls,
        "uncertainty": uncertainty,
        "latent_mechanics": {
            "status": latent_status,
            "comparisons": latent,
        },
        "checks": checks,
    }


def sensitivity_case_inputs(
    trainer: Any,
    case: Mapping[str, Any],
    pairing: Mapping[str, Any],
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    artifacts = pairing["artifacts"]
    chrono_dir = Path(artifacts["chrono_episode"])
    response = Path(artifacts["newton_response"])
    manifest, _action, initial, chrono_valid = load_episode(chrono_dir)
    loaded = np.load(
        chrono_dir / manifest["states"]["loaded"], allow_pickle=False
    )
    post = np.load(
        chrono_dir / manifest["states"]["residual"], allow_pickle=False
    )
    newton_initial = np.load(
        response / "initial_heightmap_m.npy", allow_pickle=False
    )
    newton_loaded = np.load(
        response / "loaded_heightmap_m.npy", allow_pickle=False
    )
    newton_post = np.load(
        response / "residual_heightmap_m.npy", allow_pickle=False
    )
    newton_valid = np.load(
        response / "valid_heightmap_mask.npy", allow_pickle=False
    ).astype(bool)
    valid = np.asarray(chrono_valid, dtype=bool) & newton_valid
    xs, ys = dataset.heightmap_axes(manifest)
    grid_x, grid_y = np.meshgrid(xs, ys, indexing="xy")
    center = np.asarray(case["center_xy_m"], dtype=np.float64)
    relative_x = grid_x - center[0]
    relative_y = grid_y - center[1]
    radius = 0.035
    radial = np.sqrt(relative_x * relative_x + relative_y * relative_y)
    zero = np.zeros_like(initial, dtype=np.float32)
    inputs = {
        name: np.array(zero, copy=True)
        for name in trainer.SPATIAL_CHANNELS
    }
    inputs.update(
        {
            "initial_height_m": np.asarray(initial, dtype=np.float32),
            "newton_loaded_displacement_m": (
                np.asarray(newton_loaded) - np.asarray(newton_initial)
            ).astype(np.float32),
            "newton_post_unload_displacement_m": (
                np.asarray(newton_post) - np.asarray(newton_initial)
            ).astype(np.float32),
            "valid_support": valid,
            "action_relative_x_m": relative_x.astype(np.float32),
            "action_relative_y_m": relative_y.astype(np.float32),
            "action_signed_distance_m": (radial - radius).astype(
                np.float32
            ),
            "action_footprint": radial <= radius,
            "action_phase": np.asarray(
                [
                    [
                        center[0],
                        center[1],
                        case["normal_force_n"],
                        0.0,
                    ],
                    [
                        center[0],
                        center[1],
                        case["normal_force_n"],
                        1.0,
                    ],
                ],
                dtype=np.float32,
            ),
            "soil_parameters": np.asarray(
                [
                    case["bekker_kphi"],
                    case["mohr_friction_deg"],
                ],
                dtype=np.float32,
            ),
        }
    )
    targets = {
        "chrono_loaded_height_m": np.asarray(loaded, dtype=np.float32),
        "chrono_post_unload_height_m": np.asarray(post, dtype=np.float32),
    }
    return inputs, targets


def sensitivity_quantities(
    config: Mapping[str, Any],
    inputs: Mapping[str, np.ndarray],
    targets: Mapping[str, np.ndarray],
    prediction: np.ndarray,
) -> dict[str, dict[str, float]]:
    metrics, _uncertainty = episode_prediction_metrics(
        config,
        inputs,
        targets,
        {"H1": prediction},
        {},
    )
    h1 = metrics["H1"]
    loaded = h1["loaded"]["footprint"]
    recovery = h1["recovery"]
    return {
        "prediction": {
            "loaded_peak_sinkage_m": float(
                loaded["peak_depression_m"]
            ),
            "loaded_displaced_volume_m3": float(
                loaded["displaced_volume_m3"]
            ),
            "peak_recovery_m": float(
                recovery["prediction"]["peak_recovery_m"]
            ),
        },
        "chrono": {
            "loaded_peak_sinkage_m": float(
                loaded["target_peak_depression_m"]
            ),
            "loaded_displaced_volume_m3": float(
                loaded["target_displaced_volume_m3"]
            ),
            "peak_recovery_m": float(
                recovery["target"]["peak_recovery_m"]
            ),
        },
    }


def sensitivity_edges(
    cases: Sequence[Mapping[str, Any]]
) -> list[tuple[Mapping[str, Any], Mapping[str, Any], str]]:
    edges = []
    for first_index, first in enumerate(cases):
        for second in cases[first_index + 1 :]:
            k_equal = math.isclose(
                float(first["bekker_kphi"]),
                float(second["bekker_kphi"]),
            )
            f_equal = math.isclose(
                float(first["mohr_friction_deg"]),
                float(second["mohr_friction_deg"]),
            )
            if k_equal == f_equal:
                continue
            parameter = (
                "mohr_friction_deg" if k_equal else "bekker_kphi"
            )
            low, high = sorted(
                (first, second), key=lambda item: float(item[parameter])
            )
            edges.append((low, high, parameter))
    if len(edges) != 4:
        raise RuntimeError(
            f"matched material rectangle must expose four edges, got {len(edges)}"
        )
    return edges


def evaluate_sensitivity_values(
    config: Mapping[str, Any],
    cases: Sequence[Mapping[str, Any]],
    values: Mapping[str, Mapping[str, Mapping[str, float]]],
) -> dict[str, Any]:
    sensitivity = config["sensitivity"]
    comparisons = []
    eligible = 0
    direction_matches = 0
    saturation_failures = 0
    for low, high, parameter in sensitivity_edges(cases):
        for quantity in sensitivity["quantities"]:
            low_id = str(low["case_id"])
            high_id = str(high["case_id"])
            chrono_delta = (
                float(values[high_id]["chrono"][quantity])
                - float(values[low_id]["chrono"][quantity])
            )
            prediction_delta = (
                float(values[high_id]["prediction"][quantity])
                - float(values[low_id]["prediction"][quantity])
            )
            floor = float(
                sensitivity["chrono_repeatability_floor"][quantity]
            )
            included = abs(chrono_delta) > floor
            matches = (
                included
                and np.sign(prediction_delta) == np.sign(chrono_delta)
            )
            saturated = (
                included
                and abs(prediction_delta)
                <= float(
                    sensitivity["minimum_prediction_change"][
                        quantity
                    ]
                )
            )
            eligible += int(included)
            direction_matches += int(matches)
            saturation_failures += int(saturated)
            comparisons.append(
                {
                    "parameter": parameter,
                    "low_case": low_id,
                    "high_case": high_id,
                    "quantity": quantity,
                    "chrono_delta": chrono_delta,
                    "prediction_delta": prediction_delta,
                    "included_above_repeatability_floor": included,
                    "direction_matches": matches,
                    "prediction_saturated": saturated,
                }
            )
    direction_fraction = (
        float(direction_matches / eligible) if eligible else 0.0
    )
    corners = [
        item
        for item in cases
        if float(item["bekker_kphi"]) != 800000.0
        and float(item["mohr_friction_deg"]) != 28.0
    ]
    centers = [
        item
        for item in cases
        if math.isclose(float(item["bekker_kphi"]), 800000.0)
        and math.isclose(float(item["mohr_friction_deg"]), 28.0)
    ]
    if len(corners) != 4 or len(centers) != 1:
        raise RuntimeError("matched sensitivity center/corners changed")
    center_id = str(centers[0]["case_id"])
    smoothness: dict[str, Any] = {}
    smooth = True
    for quantity in sensitivity["quantities"]:
        corner_values = np.asarray(
            [
                values[str(item["case_id"])]["prediction"][quantity]
                for item in corners
            ],
            dtype=np.float64,
        )
        center_value = float(
            values[center_id]["prediction"][quantity]
        )
        corner_range = float(np.ptp(corner_values))
        scale = max(
            corner_range,
            float(sensitivity["minimum_prediction_change"][quantity]),
        )
        deviation = abs(center_value - float(np.mean(corner_values)))
        fraction = deviation / scale
        passed = (
            fraction
            <= float(
                sensitivity[
                    "maximum_center_bilinear_deviation_fraction"
                ]
            )
        )
        smooth &= passed
        smoothness[quantity] = {
            "center_value": center_value,
            "bilinear_corner_mean": float(
                np.mean(corner_values)
            ),
            "corner_range": corner_range,
            "normalized_center_deviation": fraction,
            "passed": passed,
        }
    return {
        "comparisons": comparisons,
        "eligible_comparisons": eligible,
        "direction_matches": direction_matches,
        "direction_fraction": direction_fraction,
        "saturation_failures": saturation_failures,
        "smoothness": smoothness,
        "checks": {
            "direction_fraction": direction_fraction
            >= float(
                config["success_thresholds"][
                    "matched_sensitivity_direction_fraction"
                ]
            ),
            "no_saturation": eligible > 0
            and saturation_failures == 0,
            "smooth_inside_box": smooth,
        },
    }


def run_matched_sensitivity(
    config: Mapping[str, Any],
    plan: Mapping[str, Any],
    runtime: tuple[
        Any,
        Any,
        dict[str, Any],
        Mapping[str, Any],
        Mapping[str, Any],
    ],
) -> dict[str, Any]:
    torch, trainer, networks, normalization, _selection = runtime
    pairing_path = prerequisite_paths(config)[
        "sensitivity_pairing_summary"
    ]
    pairing_summary = json.loads(
        pairing_path.read_text(encoding="utf-8")
    )
    if (
        pairing_summary.get("status") != "passed"
        or not pairing_summary.get("all_five_pairings_admitted")
    ):
        raise RuntimeError(
            "passing matched sensitivity pairings are required"
        )
    repeatability = json.loads(
        prerequisite_paths(config)[
            "chrono_repeatability_summary"
        ].read_text(encoding="utf-8")
    )
    if not bool(
        repeatability.get("chrono", {}).get("bitwise_identical")
    ):
        raise RuntimeError(
            "zero Chrono sensitivity floor requires exact repeats"
        )
    device = torch.device(config["execution"]["device"])
    contract = load_contract(repo_path(config["phase1_contract"]))
    values: dict[str, Any] = {}
    for case in plan["matched_sensitivity_cases"]:
        validate_inference_domain(
            contract, {**case, "radius_m": 0.035}
        )
        case_id = str(case["case_id"])
        pairing = pairing_summary["pairings"][case_id]
        inputs, targets = sensitivity_case_inputs(
            trainer, case, pairing
        )
        arrays = inference_arrays(trainer, inputs, normalization)
        prediction, _deviation = infer_network(
            torch,
            networks["H1"],
            arrays,
            normalization,
            device,
        )
        values[case_id] = sensitivity_quantities(
            config, inputs, targets, prediction
        )
    evaluation = evaluate_sensitivity_values(
        config, plan["matched_sensitivity_cases"], values
    )
    summary = {
        "schema_version": 1,
        "evaluation_id": config["evaluation_id"],
        "status": (
            "passed"
            if all(evaluation["checks"].values())
            else "failed"
        ),
        "model": "H1",
        "evaluation_plan_sha256": fresh.sha256_file(
            plan_path(config)
        ),
        "pairing_summary_sha256": fresh.sha256_file(
            pairing_path
        ),
        "used_for_training_normalization_calibration_or_selection": False,
        "used_for_locked_accuracy": False,
        "case_values": values,
        **evaluation,
    }
    write_json(
        output_root(config) / "sensitivity_summary.json", summary
    )
    return summary


def summarize_predictions(
    config: Mapping[str, Any], plan: Mapping[str, Any]
) -> dict[str, Any]:
    dataset_summary_path = (
        output_root(config) / "test_dataset_summary.json"
    )
    if not dataset_summary_path.is_file():
        raise RuntimeError(
            "admitted locked test dataset is required before prediction"
        )
    dataset_summary = json.loads(
        dataset_summary_path.read_text(encoding="utf-8")
    )
    if dataset_summary.get("status") != "passed" or not dataset_summary.get(
        "prediction_permitted"
    ):
        raise RuntimeError(
            "locked test dataset does not permit prediction"
        )
    results = []
    for episode in plan["episodes"]:
        path = (
            dataset.episode_root(
                config, str(episode["episode_id"])
            )
            / "predictions"
            / "prediction_summary.json"
        )
        if not path.is_file():
            raise RuntimeError(f"missing prediction summary: {path}")
        results.append(json.loads(path.read_text(encoding="utf-8")))
    aggregate = aggregate_prediction_results(config, results)
    failures = failure_case_report(config, results)
    summary = {
        "schema_version": 1,
        "evaluation_id": config["evaluation_id"],
        "status": "predictions_complete",
        "evaluation_plan_sha256": fresh.sha256_file(
            plan_path(config)
        ),
        "test_dataset_summary_sha256": fresh.sha256_file(
            dataset_summary_path
        ),
        "episode_count": len(results),
        **aggregate,
        "failure_cases": failures,
        "episodes": {
            str(item["episode_id"]): {
                "holdout_group": item["holdout_group"],
                "prediction_summary_sha256": fresh.sha256_file(
                    dataset.episode_root(
                        config, str(item["episode_id"])
                    )
                    / "predictions"
                    / "prediction_summary.json"
                ),
                "prediction_archive_sha256": item[
                    "prediction_archive_sha256"
                ],
                "all_output_checks_pass": item[
                    "all_output_checks_pass"
                ],
            }
            for item in results
        },
    }
    write_json(
        output_root(config) / "prediction_summary.json", summary
    )
    return summary


def failure_case_report(
    config: Mapping[str, Any], results: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Report the worst H1 episode and every raw-Newton regression."""
    thresholds = config["success_thresholds"]
    worst: dict[str, Any] = {}
    regressions: list[dict[str, Any]] = []
    tolerance_failures: list[dict[str, Any]] = []
    for checkpoint in CHECKPOINTS:
        for region in LOCAL_REGIONS:
            rows: list[dict[str, Any]] = []
            for result in results:
                metrics = result["metrics"]
                values = {
                    predictor: float(
                        metrics[predictor][checkpoint][region]["rmse_m"]
                    )
                    for predictor in PREDICTORS
                }
                raw = values["B1"]
                h1 = values["H1"]
                tolerance = max(
                    float(
                        thresholds[
                            "maximum_episode_regression_fraction_vs_raw_newton"
                        ]
                    )
                    * raw,
                    float(
                        thresholds[
                            "maximum_episode_regression_absolute_m"
                        ]
                    ),
                )
                row = {
                    "episode_id": str(result["episode_id"]),
                    "holdout_group": str(result["holdout_group"]),
                    "checkpoint": checkpoint,
                    "region": region,
                    "rmse_m": values,
                    "h1_minus_raw_newton_rmse_m": h1 - raw,
                    "allowed_regression_m": tolerance,
                    "worse_than_raw_newton": h1 > raw,
                    "exceeds_failure_tail_tolerance": h1 > raw + tolerance,
                }
                rows.append(row)
                if row["worse_than_raw_newton"]:
                    regressions.append(row)
                if row["exceeds_failure_tail_tolerance"]:
                    tolerance_failures.append(row)
            key = f"{checkpoint}:{region}"
            worst[key] = max(
                rows,
                key=lambda item: (
                    float(item["h1_minus_raw_newton_rmse_m"]),
                    str(item["episode_id"]),
                ),
            )
    return {
        "definition": (
            "Worst and regressed episodes are ranked by H1 RMSE minus raw-Newton "
            "RMSE; whole episodes remain the reporting unit."
        ),
        "worst_by_checkpoint_region": worst,
        "episodes_worse_than_raw_newton": regressions,
        "episodes_exceeding_failure_tail_tolerance": tolerance_failures,
    }


def final_artifact_integrity(
    config_path: Path,
    config: Mapping[str, Any],
    plan: Mapping[str, Any],
    prediction: Mapping[str, Any],
) -> tuple[dict[str, bool], dict[str, Any]]:
    """Revalidate every artifact needed to support a final Phase 1 claim."""
    current = build_plan(config_path, config)
    plan_changes = [
        key for key in STABLE_PLAN_KEYS if plan.get(key) != current.get(key)
    ]
    paths = prerequisite_paths(config)
    bulk = json.loads(paths["bulk_summary"].read_text(encoding="utf-8"))
    training_plan = json.loads(
        paths["training_plan"].read_text(encoding="utf-8")
    )
    selection = json.loads(
        paths["selection_summary"].read_text(encoding="utf-8")
    )
    dataset_summary_path = output_root(config) / "test_dataset_summary.json"
    dataset_summary = json.loads(
        dataset_summary_path.read_text(encoding="utf-8")
    )
    unlock = require_unlocked(config, plan)
    opened = require_opened(config, plan)
    expected_ids = {str(item["episode_id"]) for item in plan["episodes"]}

    dataset_artifact_failures: list[str] = []
    dataset_episodes = dataset_summary.get("episodes", {})
    if set(dataset_episodes) == expected_ids:
        for episode in plan["episodes"]:
            episode_id = str(episode["episode_id"])
            embedded = dataset_episodes[episode_id]
            episode_root = dataset.episode_root(config, episode_id)
            episode_summary_path = episode_root / "episode_summary.json"
            tensor_root = episode_root / "tensors"
            locked_manifest_path = tensor_root / "locked_test_tensor_manifest.json"
            try:
                stored_episode = json.loads(
                    episode_summary_path.read_text(encoding="utf-8")
                )
                stored_manifest = json.loads(
                    locked_manifest_path.read_text(encoding="utf-8")
                )
                locked_manifest = embedded["locked_tensor_manifest"]
                input_path = tensor_root / locked_manifest["model_input_file"]
                target_path = tensor_root / locked_manifest["target_file"]
                valid = (
                    stored_episode == embedded
                    and stored_manifest == locked_manifest
                    and bool(embedded.get("complete"))
                    and bool(embedded.get("admitted"))
                    and all(
                        bool(value)
                        for value in locked_manifest["checks"].values()
                    )
                    and input_path.is_file()
                    and target_path.is_file()
                    and fresh.sha256_file(input_path)
                    == locked_manifest["sha256"]["model_inputs"]
                    and fresh.sha256_file(target_path)
                    == locked_manifest["sha256"]["targets"]
                )
            except (KeyError, OSError, ValueError, json.JSONDecodeError):
                valid = False
            if not valid:
                dataset_artifact_failures.append(episode_id)
    else:
        dataset_artifact_failures.append("episode_membership")

    prediction_artifact_failures: list[str] = []
    prediction_episodes = prediction.get("episodes", {})
    if set(prediction_episodes) == expected_ids:
        for episode in plan["episodes"]:
            episode_id = str(episode["episode_id"])
            recorded = prediction_episodes[episode_id]
            root = dataset.episode_root(config, episode_id) / "predictions"
            summary_path = root / "prediction_summary.json"
            archive_path = root / "predicted_surfaces.npz"
            try:
                result = json.loads(summary_path.read_text(encoding="utf-8"))
                valid = (
                    fresh.sha256_file(summary_path)
                    == recorded["prediction_summary_sha256"]
                    and archive_path.is_file()
                    and fresh.sha256_file(archive_path)
                    == recorded["prediction_archive_sha256"]
                    == result["prediction_archive_sha256"]
                    and result["selected_model_artifacts"]
                    == plan["selected_model_artifacts"]
                    and bool(result["all_output_checks_pass"])
                )
                for variant in NEURAL_VARIANTS:
                    for checkpoint in CHECKPOINTS:
                        audit = result["particle_audits"][variant][checkpoint]
                        corrected = (
                            root
                            / "corrected_particles"
                            / variant
                            / f"{checkpoint}.npz"
                        )
                        surface = root / f"{variant}_{checkpoint}_surface_m.npy"
                        valid &= (
                            bool(audit["all_checks_pass"])
                            and corrected.is_file()
                            and surface.is_file()
                            and fresh.sha256_file(corrected)
                            == audit["corrected_state_sha256"]
                            and fresh.sha256_file(surface)
                            == audit["predicted_surface_sha256"]
                        )
            except (KeyError, OSError, ValueError, json.JSONDecodeError):
                valid = False
            if not valid:
                prediction_artifact_failures.append(episode_id)
    else:
        prediction_artifact_failures.append("episode_membership")

    model_artifact_failures: list[str] = []
    training_root = paths["selection_summary"].parent
    for variant, identity in plan["selected_model_artifacts"].items():
        root = training_root / "models" / variant / f"seed_{int(identity['seed'])}"
        for filename, key in (
            ("model_card.json", "model_card_sha256"),
            ("model.pt", "checkpoint_sha256"),
            ("history.json", "history_sha256"),
        ):
            path = root / filename
            if not path.is_file() or fresh.sha256_file(path) != identity[key]:
                model_artifact_failures.append(f"{variant}:{filename}")

    qualified = set(bulk.get("qualified_nonkinematic_families", []))
    h2_channels = set(
        selection.get("selected", {})
        .get("H2", {})
        .get("active_spatial_channels", [])
    )
    latent_included = bool(qualified) and all(
        any(f"_{family}_" in channel for channel in h2_channels)
        for family in qualified
    )
    model_counts = training_plan.get("model_parameter_counts", {})
    checks = {
        "integrity:locked_plan_revalidated": not plan_changes,
        "integrity:bulk_train_validation_passed": (
            bulk.get("status") == "passed"
            and bool(bulk.get("training_dataset_ready"))
            and all(bool(value) for value in bulk.get("checks", {}).values())
        ),
        "integrity:selection_preceded_unlock": (
            selection.get("status") == "models_selected_before_test_unlock"
            and not bool(selection.get("test_targets_opened"))
            and unlock.get("selection_summary_sha256")
            == plan["selection_summary_sha256"]
            and opened.get("selection_summary_sha256")
            == plan["selection_summary_sha256"]
        ),
        "integrity:fixed_capacity_model_ladder": (
            set(model_counts) == set(NEURAL_VARIANTS)
            and len(set(int(value) for value in model_counts.values())) == 1
        ),
        "integrity:selected_model_artifacts": not model_artifact_failures,
        "integrity:test_dataset_admitted": (
            dataset_summary.get("status") == "passed"
            and bool(dataset_summary.get("prediction_permitted"))
            and all(
                bool(value)
                for value in dataset_summary.get("checks", {}).values()
            )
            and dataset_summary.get("identity", {}).get(
                "evaluation_plan_sha256"
            )
            == fresh.sha256_file(plan_path(config))
        ),
        "integrity:test_tensor_artifacts": not dataset_artifact_failures,
        "integrity:prediction_summary_identity": (
            prediction.get("status") == "predictions_complete"
            and int(prediction.get("episode_count", -1)) == len(expected_ids)
            and prediction.get("evaluation_plan_sha256")
            == fresh.sha256_file(plan_path(config))
            and prediction.get("test_dataset_summary_sha256")
            == fresh.sha256_file(dataset_summary_path)
        ),
        "integrity:prediction_and_particle_artifacts": (
            not prediction_artifact_failures
        ),
        "integrity:qualified_latents_in_h2": latent_included,
    }
    details = {
        "plan_changes": plan_changes,
        "dataset_artifact_failures": dataset_artifact_failures,
        "prediction_artifact_failures": prediction_artifact_failures,
        "model_artifact_failures": model_artifact_failures,
        "qualified_nonkinematic_families": sorted(qualified),
        "excluded_nonkinematic_families": bulk.get(
            "excluded_nonkinematic_families", []
        ),
        "h2_active_spatial_channels": sorted(h2_channels),
        "source_sha256": plan["source_sha256"],
        "input_sha256": plan["input_sha256"],
        "selected_model_artifacts": plan["selected_model_artifacts"],
    }
    return checks, details


def build_final_report(
    config_path: Path,
    config: Mapping[str, Any],
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    prediction_path = output_root(config) / "prediction_summary.json"
    sensitivity_path = (
        output_root(config) / "sensitivity_summary.json"
    )
    if not prediction_path.is_file():
        raise RuntimeError("prediction summary is absent")
    prediction = json.loads(
        prediction_path.read_text(encoding="utf-8")
    )
    checks = dict(prediction["checks"])
    integrity_checks, integrity_details = final_artifact_integrity(
        config_path, config, plan, prediction
    )
    checks.update(integrity_checks)
    sensitivity: Mapping[str, Any] | None = None
    if sensitivity_path.is_file():
        sensitivity = json.loads(
            sensitivity_path.read_text(encoding="utf-8")
        )
        checks.update(
            {
                f"sensitivity:{name}": bool(value)
                for name, value in sensitivity["checks"].items()
            }
        )
        checks["sensitivity:identity"] = (
            sensitivity.get("status") == "passed"
            and sensitivity.get("evaluation_plan_sha256")
            == fresh.sha256_file(plan_path(config))
        )
    else:
        checks["sensitivity:complete"] = False
    passed = all(checks.values())
    latent_status = prediction["latent_mechanics"]["status"]
    final_model = (
        "H2"
        if latent_status
        in ("improves_prediction", "neutral_without_worse_tail")
        else "H1"
    )
    report = {
        "schema_version": 1,
        "evaluation_id": config["evaluation_id"],
        "status": "passed" if passed else "failed",
        "phase1_exit_demonstrated": passed,
        "supported_claim_permitted": passed,
        "checks": checks,
        "failed_checks": sorted(
            name for name, value in checks.items() if not value
        ),
        "final_model": final_model,
        "aggregate_metrics": prediction["aggregate_metrics"],
        "accuracy_details": prediction["accuracy_details"],
        "joint_baseline_details": prediction["joint_baseline_details"],
        "material_ablation_details": prediction[
            "material_ablation_details"
        ],
        "parameter_controls": prediction["parameter_controls"],
        "uncertainty": prediction["uncertainty"],
        "latent_mechanics": prediction["latent_mechanics"],
        "failure_cases": prediction["failure_cases"],
        "matched_sensitivity": sensitivity,
        "integrity": integrity_details,
        "positive_latent_value_claim_permitted": (
            latent_status == "improves_prediction"
        ),
        "prediction_summary_sha256": fresh.sha256_file(
            prediction_path
        ),
        "sensitivity_summary_sha256": (
            fresh.sha256_file(sensitivity_path)
            if sensitivity is not None
            else None
        ),
        "evaluation_plan_sha256": fresh.sha256_file(
            plan_path(config)
        ),
        "selection_summary_sha256": plan[
            "selection_summary_sha256"
        ],
        "claim_boundary": (
            "The Phase 1 claim is limited to the frozen single-action "
            "synthetic domain; it does not establish real-soil, "
            "sequential-action, or full latent-state fidelity."
        ),
    }
    write_json(
        output_root(config) / "final_evaluation_report.json", report
    )
    return report


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = load_evaluation_config(config_path)
    if args.stage == "plan":
        plan = write_plan(config_path, config)
        print(json.dumps({"plan": str(plan_path(config)), "test": len(plan["episodes"]), "targets_opened": False}, indent=2))
        return
    plan = load_plan(config_path, config)
    if args.stage == "unlock":
        marker = unlock_test(config, plan)
        print(json.dumps(marker, indent=2))
        return
    require_unlocked(config, plan)
    contract = load_contract(repo_path(config["phase1_contract"]))
    episodes = choose_episodes(plan, args.episode)
    if args.stage == "chrono":
        mark_targets_opened(config, plan)
        for episode in episodes:
            dataset.run_chrono(config, contract, episode)
        print(
            json.dumps(
                {
                    "stage": "chrono",
                    "completed": sum(
                        bool(dataset.chrono_result(config, contract, item).get("accepted"))
                        for item in plan["episodes"]
                    ),
                    "required": 24,
                    "targets_opened": True,
                },
                indent=2,
            )
        )
        return
    require_opened(config, plan)
    if args.stage == "bed":
        for seed in sorted({int(item["initial_surface_seed"]) for item in episodes}):
            build_test_bed(config, contract, plan, seed)
        print(json.dumps({"stage": "bed", "surface_seeds": plan["surface_seeds"]}, indent=2))
        return
    if args.stage == "newton":
        workers = int(config["execution"].get("newton_workers", 1))
        if workers < 1:
            raise ValueError("Newton worker count must be positive")
        for seed in sorted({int(item["initial_surface_seed"]) for item in episodes}):
            prepare_test_prior(config, contract, plan, seed)
        if workers == 1:
            for episode in episodes:
                run_test_newton(config, contract, plan, episode)
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [
                    pool.submit(run_test_newton, config, contract, plan, episode)
                    for episode in episodes
                ]
                for future in concurrent.futures.as_completed(futures):
                    future.result()
        print(
            json.dumps(
                {"stage": "newton", "episodes": len(episodes), "workers": workers},
                indent=2,
            )
        )
        return
    if args.stage == "admit":
        for episode in episodes:
            analyze_test_episode(config, contract, plan, episode)
        summary = summarize_test_dataset(config, contract, plan)
        print(
            json.dumps(
                {
                    "stage": "admit",
                    "status": summary["status"],
                    "prediction_permitted": summary["prediction_permitted"],
                    "checks": summary["checks"],
                },
                indent=2,
            )
        )
        return
    if args.stage == "predict":
        dataset_summary_path = (
            output_root(config) / "test_dataset_summary.json"
        )
        if not dataset_summary_path.is_file():
            raise RuntimeError(
                "locked test admission must pass before prediction"
            )
        dataset_summary = json.loads(
            dataset_summary_path.read_text(encoding="utf-8")
        )
        if (
            dataset_summary.get("status") != "passed"
            or not dataset_summary.get("prediction_permitted")
        ):
            raise RuntimeError(
                "locked test admission does not permit prediction"
            )
        runtime = load_selected_networks(config, plan)
        completed = [
            predict_test_episode(
                config, plan, episode, runtime
            )["episode_id"]
            for episode in episodes
        ]
        if args.episode:
            print(
                json.dumps(
                    {
                        "stage": "predict",
                        "completed": completed,
                        "aggregate_pending": True,
                    },
                    indent=2,
                )
            )
            return
        sensitivity = run_matched_sensitivity(
            config, plan, runtime
        )
        summary = summarize_predictions(config, plan)
        print(
            json.dumps(
                {
                    "stage": "predict",
                    "status": summary["status"],
                    "episode_count": summary["episode_count"],
                    "sensitivity_status": sensitivity["status"],
                },
                indent=2,
            )
        )
        return
    if args.stage == "report":
        report = build_final_report(config_path, config, plan)
        print(
            json.dumps(
                {
                    "stage": "report",
                    "status": report["status"],
                    "phase1_exit_demonstrated": report[
                        "phase1_exit_demonstrated"
                    ],
                    "failed_checks": report["failed_checks"],
                },
                indent=2,
            )
        )
        return
    raise RuntimeError(
        f"unhandled evaluator stage: {args.stage!r}"
    )


if __name__ == "__main__":
    main()

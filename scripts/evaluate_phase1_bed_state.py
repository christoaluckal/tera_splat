#!/usr/bin/env python3
"""Freeze and execute the one-shot Phase 1 locked evaluation."""

from __future__ import annotations

import argparse
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
    if value.get("evaluation_id") != "phase1_bed_state_evaluation_v1":
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
    sensitivity = value["sensitivity"]
    prohibited = bool(sensitivity["use_for_training_normalization_calibration_or_selection"])
    if prohibited or not bool(sensitivity["use_only_for_directional_parameter_sensitivity"]):
        raise ValueError("matched sensitivity cases must remain evaluation-only")
    dataset = value["test_dataset"]
    if int(dataset["required_episode_count"]) != 24 or int(dataset["required_test_count"]) != 24:
        raise ValueError("test dataset exit counts changed")
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
    return {
        "phase1_contract": repo_path(config["phase1_contract"]),
        "dataset_plan": repo_path(config["dataset_plan"]),
        "bulk_summary": repo_path(config["bulk_summary"]),
        "training_config": repo_path(config["training_config"]),
        "training_plan": repo_path(config["training_plan"]),
        "normalization": repo_path(config["normalization"]),
        "selection_summary": repo_path(config["selection_summary"]),
        "phase0_model": repo_path(config["phase0_model"]),
        "sensitivity_screening_plan": repo_path(sensitivity["screening_plan"]),
        "sensitivity_screening_summary": repo_path(sensitivity["screening_summary"]),
    }


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
    return {
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
    screening_plan = json.loads(
        paths["sensitivity_screening_plan"].read_text(encoding="utf-8")
    )
    sensitivity_cases = matched_sensitivity_cases(config, screening_plan)
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
    numerical = {
        "chrono_accepted": bool(chrono["accepted"]),
        "preparation_accepted": bool(prepared.get("accepted")),
        "preparation_converged": bool(manifest["preparation"]["convergence_passed"]),
        "finite": bool(manifest["finite"]),
        "guide": bool(manifest["cylinder"]["guide_constraint_passed"]),
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
        for episode in episodes:
            run_test_newton(config, contract, plan, episode)
        print(json.dumps({"stage": "newton", "episodes": len(episodes)}, indent=2))
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
    raise RuntimeError(
        f"stage {args.stage!r} is intentionally unavailable until its "
        "source-hashed inference/report implementation and tests are complete"
    )


if __name__ == "__main__":
    main()

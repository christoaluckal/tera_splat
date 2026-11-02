#!/usr/bin/env python3
"""Run the frozen twelve-member Phase 1 successor engineering smoke set."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_fresh_phase0_repeatability as fresh
import run_phase1_dataset as base


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_smoke_v1.json"
BASE_EXPORT_TENSORS = base.export_tensors
BASE_CHRONO_RESULT = base.chrono_result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--stage", choices=("plan", "chrono", "bed", "newton", "analyze", "all"), default="plan")
    parser.add_argument("--episode", action="append", default=[])
    parser.add_argument("--workers", type=int)
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_config(path: Path) -> dict[str, Any]:
    config = load_json(path.resolve())
    if config.get("schema_version") != 1 or config.get("dataset_id") != "phase1_one_action_successor_smoke_v1":
        raise ValueError("unexpected successor smoke configuration")
    if config.get("status") != "prospective_before_runtime":
        raise ValueError("successor smoke must be prospective before runtime")
    membership = config["membership"]
    if set(membership) != {"train", "validation", "test", "protected_sensitivity"}:
        raise ValueError("successor smoke membership keys changed")
    if membership["test"] or membership["protected_sensitivity"]:
        raise ValueError("successor smoke cannot open protected targets")
    ids = membership["train"] + membership["validation"]
    exit_contract = config["smoke_exit"]
    if len(ids) != int(exit_contract["required_episode_count"]) or len(set(ids)) != len(ids):
        raise ValueError("successor smoke membership count or uniqueness changed")
    if len(membership["train"]) != int(exit_contract["required_train_count"]) or len(membership["validation"]) != int(exit_contract["required_validation_count"]):
        raise ValueError("successor smoke split counts changed")
    if config["newton_prior"]["observation_time_mode"] != "independent_fixed" or not config["newton_prior"]["chrono_target_time_must_not_control_newton_rollout"]:
        raise ValueError("successor smoke Newton timing changed")
    schema = config["tensor_schema"]
    if schema["global_parameter_vector"] != ["bekker_kphi"]:
        raise ValueError("successor smoke must condition on Kphi alone")
    if "plastic_jacobian" not in schema["excluded_fields"] or not schema["target_arrays_are_never_model_inputs"]:
        raise ValueError("successor smoke tensor leakage or plastic exclusion changed")
    if int(config["execution"]["workers"]) != 2:
        raise ValueError("successor smoke requires the qualified two-worker identity")
    return config


def merged_contract(config: Mapping[str, Any]) -> tuple[Path, dict[str, Any], Path, dict[str, Any]]:
    successor_path = fresh.repo_path(config["successor_contract"])
    operations_path = fresh.repo_path(config["operations_contract"])
    successor = load_json(successor_path)
    operations = load_json(operations_path)
    if successor.get("contract_id") != "phase1_one_action_successor_contract_v1":
        raise ValueError("unexpected successor contract")
    merged = copy.deepcopy(operations)
    merged["phase_id"] = successor["contract_id"]
    merged["action_domain"] = copy.deepcopy(successor["action_domain"])
    merged["initial_surface_domain"] = copy.deepcopy(successor["initial_surface_domain"])
    retained_threads = copy.deepcopy(operations["chrono"]["thread_environment"])
    merged["chrono"].update(copy.deepcopy(successor["chrono"]))
    merged["chrono"]["thread_environment"] = retained_threads
    merged["chrono"]["soil_parameters"] = copy.deepcopy(successor["chrono"]["soil_parameters"])
    merged["newton"]["output_root"] = str(
        fresh.repo_path(config["execution"]["output_root"]).resolve()
    )
    return successor_path, successor, operations_path, merged


def output_root(config: Mapping[str, Any]) -> Path:
    return fresh.repo_path(config["execution"]["output_root"])


def plan_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "smoke_plan.json"


def surface_input_root(config: Mapping[str, Any], _contract: Mapping[str, Any], surface_seed: int) -> Path:
    return fresh.repo_path(config["execution"]["surface_root"]) / f"surface_{int(surface_seed)}"


def selected_episodes(config: Mapping[str, Any], dataset_plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    by_id = {
        item["episode_id"]: item
        for split in ("train", "validation")
        for item in dataset_plan["episodes"][split]
    }
    result = []
    for split in ("train", "validation"):
        for episode_id in config["membership"][split]:
            if episode_id not in by_id:
                raise ValueError(f"unknown frozen smoke member: {episode_id}")
            episode = by_id[episode_id]
            if episode["split"] != split or episode["target_access"] == "locked":
                raise ValueError(f"invalid smoke split or target access: {episode_id}")
            result.append(episode)
    expected = sorted(int(value) for value in config["smoke_exit"]["required_surface_seeds"])
    actual = sorted({int(item["initial_surface_seed"]) for item in result})
    if actual != expected:
        raise ValueError(f"successor smoke surface coverage changed: {actual} != {expected}")
    return result


def require_prerequisites(config: Mapping[str, Any], successor_path: Path) -> dict[str, Any]:
    prerequisites = config["prerequisites"]
    records = {}
    for name, path_key, hash_key in (
        ("directional", "directional_summary", "directional_summary_sha256"),
        ("surface", "surface_qualification_summary", "surface_qualification_summary_sha256"),
        ("surface_plan", "surface_qualification_plan", "surface_qualification_plan_sha256"),
        ("latent", "latent_summary", "latent_summary_sha256"),
    ):
        path = fresh.repo_path(prerequisites[path_key])
        if not path.is_file() or sha256(path) != prerequisites[hash_key]:
            raise RuntimeError(f"successor smoke prerequisite changed: {name}")
        records[name] = load_json(path)
    if records["directional"].get("status") != prerequisites["required_directional_status"]:
        raise RuntimeError("directional screen is not passed")
    if records["surface"].get("status") != prerequisites["required_surface_status"] or not records["surface"].get("smoke_target_generation_permitted"):
        raise RuntimeError("successor surface qualification does not permit smoke targets")
    if records["latent"].get("status") != prerequisites["required_latent_status"]:
        raise RuntimeError("historical field semantics qualification is not passed")
    qualified = sorted(records["latent"].get("qualified_nonkinematic_families", []))
    if qualified != sorted(prerequisites["qualified_optional_families"]):
        raise RuntimeError("qualified optional field families changed")
    successor = load_json(successor_path)
    if successor["permissions_after_dataset_plan_freeze"]["smoke_train_validation_target_generation"] is not True:
        raise RuntimeError("successor contract does not authorize smoke targets")
    return records


def source_paths(
    config_path: Path,
    config: Mapping[str, Any],
    successor_path: Path,
    operations_path: Path,
    contract: Mapping[str, Any],
) -> dict[str, Path]:
    chrono_repo = fresh.repo_path(contract["chrono"]["repo"])
    return {
        "smoke_config": config_path.resolve(),
        "successor_contract": successor_path,
        "operations_contract": operations_path,
        "successor_smoke_runner": Path(__file__).resolve(),
        "successor_smoke_tests": REPO_ROOT / "tests" / "test_phase1_one_action_successor_smoke.py",
        "base_dataset_runner": SCRIPT_DIR / "run_phase1_dataset.py",
        "execution_helpers": SCRIPT_DIR / "run_fresh_phase0_repeatability.py",
        "common_base_builder": SCRIPT_DIR / "phase1_metric_bed.py",
        "latent_fields": SCRIPT_DIR / "phase1_latent_fields.py",
        "chrono_episode_bridge": SCRIPT_DIR / "chrono_episode_bridge.py",
        "particle_io": SCRIPT_DIR / "particle_io.py",
        "newton_preparation": SCRIPT_DIR / "run_newton_prepared_bed.py",
        "newton_response": SCRIPT_DIR / "run_newton_cylinder_diagnostic.py",
        "newton_contract": SCRIPT_DIR / "newton_contract.py",
        "newton_base_config": fresh.repo_path(contract["newton"]["base_config"]),
        "common_base_contract": fresh.repo_path(config["newton_prior"]["builder_contract"]),
        "chrono_episode_cli": chrono_repo / "run_cylinder_episode.py",
        "chrono_episode_impl": chrono_repo / "quick_support_demo" / "chrono_demo" / "cylinder_episode.py",
        "chrono_scm_builder": chrono_repo / "quick_support_demo" / "chrono_demo" / "build_scm_pit.py",
        "chrono_terrain_config": chrono_repo / "quick_support_demo" / "configs" / "terrain.yaml",
    }


def input_paths(config: Mapping[str, Any], episodes: list[dict[str, Any]]) -> dict[str, Path]:
    paths = {
        "dataset_plan": fresh.repo_path(config["dataset_plan"]),
        "directional_summary": fresh.repo_path(config["prerequisites"]["directional_summary"]),
        "surface_qualification_plan": fresh.repo_path(config["prerequisites"]["surface_qualification_plan"]),
        "surface_qualification_summary": fresh.repo_path(config["prerequisites"]["surface_qualification_summary"]),
        "latent_summary": fresh.repo_path(config["prerequisites"]["latent_summary"]),
        "phase0_admission_contract": REPO_ROOT / "configs" / "static_proxy_hierarchical_v3_20261017.json",
    }
    for seed in sorted({int(item["initial_surface_seed"]) for item in episodes}):
        root = surface_input_root(config, {}, seed)
        paths[f"surface_{seed}:heightmap"] = root / "initial_heightmap_m.npy"
        paths[f"surface_{seed}:qualification"] = root / "qualification_summary.json"
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing successor smoke inputs: {missing}")
    return paths


def build_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    successor_path, successor, operations_path, contract = merged_contract(config)
    prerequisites = require_prerequisites(config, successor_path)
    dataset_path = fresh.repo_path(config["dataset_plan"])
    dataset = load_json(dataset_path)
    if dataset.get("contract_sha256") != sha256(successor_path):
        raise RuntimeError("dataset plan does not match successor contract")
    if dataset["permissions"] != successor["permissions_after_dataset_plan_freeze"]:
        raise RuntimeError("dataset-plan permissions changed")
    episodes = selected_episodes(config, dataset)
    sources = source_paths(config_path, config, successor_path, operations_path, contract)
    inputs = input_paths(config, episodes)
    missing = [str(path) for path in sources.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing successor smoke sources: {missing}")
    for seed in sorted({int(item["initial_surface_seed"]) for item in episodes}):
        qualification = load_json(surface_input_root(config, contract, seed) / "qualification_summary.json")
        if qualification.get("qualified") is not True:
            raise RuntimeError(f"successor surface is not qualified: {seed}")
    return {
        "schema_version": 1,
        "dataset_id": config["dataset_id"],
        "status": "frozen_before_first_target",
        "config_sha256": sha256(config_path),
        "successor_contract_sha256": sha256(successor_path),
        "operations_contract_sha256": sha256(operations_path),
        "dataset_plan_sha256": sha256(dataset_path),
        "episode_manifest_sha256": dataset["episode_manifest_sha256"],
        "test_lock_sha256": dataset["test_lock_sha256"],
        "sensitivity_lock_sha256": dataset["sensitivity_lock_sha256"],
        "selected_episode_manifest_sha256": base.canonical_sha256(episodes),
        "source_sha256": {name: sha256(path) for name, path in sources.items()},
        "input_sha256": {name: sha256(path) for name, path in inputs.items()},
        "environment": base.environment_probe(config, contract),
        "repository_revisions": {
            "tera_splat": fresh.command_output(["git", "rev-parse", "HEAD"], REPO_ROOT),
            "tera_splat_sim": fresh.command_output(["git", "rev-parse", "HEAD"], fresh.repo_path(contract["chrono"]["repo"])),
        },
        "episodes": episodes,
        "counts": {"train": len(config["membership"]["train"]), "validation": len(config["membership"]["validation"]), "test": 0, "protected_sensitivity": 0},
        "surface_seeds": sorted({int(item["initial_surface_seed"]) for item in episodes}),
        "qualified_nonkinematic_families": prerequisites["latent"]["qualified_nonkinematic_families"],
        "excluded_nonkinematic_families": config["prerequisites"]["excluded_families"],
        "newton_prior": config["newton_prior"],
        "tensor_schema": config["tensor_schema"],
        "worker_count": int(config["execution"]["workers"]),
        "remaining_train_validation_permitted": False,
        "test_or_protected_sensitivity_permitted": False,
    }


def stable_plan_keys() -> tuple[str, ...]:
    return (
        "config_sha256", "successor_contract_sha256", "operations_contract_sha256",
        "dataset_plan_sha256", "episode_manifest_sha256", "test_lock_sha256",
        "sensitivity_lock_sha256", "selected_episode_manifest_sha256",
        "source_sha256", "input_sha256", "environment", "episodes",
        "tensor_schema", "worker_count",
    )


def write_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    plan = build_plan(config_path, config)
    path = plan_path(config)
    if path.exists():
        existing = load_json(path)
        changed = [key for key in stable_plan_keys() if existing.get(key) != plan.get(key)]
        if changed:
            raise RuntimeError(f"refusing changed successor smoke plan: {changed}")
        return existing
    fresh.write_json(path, plan)
    return plan


def load_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    path = plan_path(config)
    if not path.is_file():
        raise RuntimeError("successor smoke plan is absent; run --stage plan")
    frozen = load_json(path)
    current = build_plan(config_path, config)
    changed = [key for key in stable_plan_keys() if frozen.get(key) != current.get(key)]
    if changed:
        raise RuntimeError(f"successor smoke identity changed: {changed}")
    return frozen


def choose_episodes(plan: Mapping[str, Any], requested: list[str]) -> list[dict[str, Any]]:
    episodes = list(plan["episodes"])
    by_id = {item["episode_id"]: item for item in episodes}
    unknown = sorted(set(requested) - set(by_id))
    if unknown:
        raise ValueError(f"unknown successor smoke episodes: {unknown}")
    return [by_id[name] for name in requested] if requested else episodes


def fixed_soil_checks(contract: Mapping[str, Any], actual: Mapping[str, Any]) -> dict[str, bool]:
    fixed = contract["chrono"]["soil_parameters"]["fixed"]
    expected = {
        "bekker_kc": fixed["bekker_kc"],
        "bekker_n": fixed["bekker_n"],
        "mohr_cohesion": fixed["mohr_cohesion_pa"],
        "mohr_friction_deg": fixed["mohr_friction_deg"],
        "janosi_shear_m": fixed["janosi_shear_m"],
        "elastic_k": fixed["elastic_k_pa_per_m"],
        "damping_r": fixed["damping_r_pa_s_per_m"],
    }
    return {name: math.isclose(float(actual[name]), float(value), rel_tol=1.0e-12, abs_tol=1.0e-12) for name, value in expected.items()}


def chrono_result(config: Mapping[str, Any], contract: Mapping[str, Any], episode: Mapping[str, Any]) -> dict[str, Any]:
    result = BASE_CHRONO_RESULT(config, contract, episode)
    if not result.get("complete"):
        return result
    root = base.chrono_episode(config, episode["episode_id"])
    manifest = yaml.safe_load((root / "manifest.yaml").read_text(encoding="utf-8"))
    checks = fixed_soil_checks(contract, manifest["chrono"]["soil_parameters"])
    return {**result, "accepted": bool(result["accepted"]) and all(checks.values()), "fixed_soil_checks": checks}


def chrono_command(config: Mapping[str, Any], contract: Mapping[str, Any], episode: Mapping[str, Any]) -> list[str]:
    cfg = contract["chrono"]
    fixed = cfg["soil_parameters"]["fixed"]
    source = surface_input_root(config, contract, int(episode["initial_surface_seed"])) / "initial_heightmap_m.npy"
    command = [
        *(str(value) for value in cfg["command"]),
        str(fresh.repo_path(cfg["repo"]) / "run_cylinder_episode.py"),
        "--episode-id", episode["episode_id"],
        "--mass-kg", str(episode["equivalent_mass_kg"]),
        "--xy", *(str(value) for value in episode["center_xy_m"]),
        "--radius-m", str(episode["radius_m"]),
        "--height-m", str(episode["height_m"]),
        "--start-clearance-m", str(contract["action_domain"]["start_clearance_m"]),
        "--timestep-s", str(cfg["timestep_s"]),
        "--scm-grid-spacing-m", str(cfg["scm_grid_spacing_m"]),
        "--scm-pit-size-m", *(str(value) for value in cfg["scm_pit_size_m"]),
        "--max-loading-time-s", str(cfg["max_loading_time_s"]),
        "--min-loading-time-s", str(cfg["min_loading_time_s"]),
        "--loading-linear-speed-threshold-mps", str(cfg["loading_linear_speed_threshold_mps"]),
        "--loading-angular-speed-threshold-radps", str(cfg["loading_angular_speed_threshold_radps"]),
        "--loading-hold-time-s", str(cfg["loading_hold_time_s"]),
        "--residual-settle-s", str(cfg["residual_duration_s"]),
        "--initial-heightmap-npy", str(source),
        "--bekker-kphi", str(episode["soil_parameters"]["bekker_kphi"]),
        "--bekker-kc", str(fixed["bekker_kc"]),
        "--bekker-n", str(fixed["bekker_n"]),
        "--mohr-cohesion-pa", str(fixed["mohr_cohesion_pa"]),
        "--mohr-friction-deg", str(fixed["mohr_friction_deg"]),
        "--janosi-shear-m", str(fixed["janosi_shear_m"]),
        "--elastic-k-pa-per-m", str(fixed["elastic_k_pa_per_m"]),
        "--damping-r-pa-s-per-m", str(fixed["damping_r_pa_s_per_m"]),
        "--output-dir", str(base.chrono_episode(config, episode["episode_id"])),
        "--vertical-guide",
    ]
    return command


def run_chrono(config: Mapping[str, Any], contract: Mapping[str, Any], episode: Mapping[str, Any]) -> dict[str, Any]:
    existing = chrono_result(config, contract, episode)
    if existing.get("complete"):
        if not existing["accepted"]:
            raise RuntimeError(f"stored successor Chrono episode rejected: {episode['episode_id']}")
        return existing
    destination = base.chrono_episode(config, episode["episode_id"])
    if destination.exists():
        raise RuntimeError(f"refusing incomplete successor Chrono episode: {destination}")
    fresh.run_logged(
        chrono_command(config, contract, episode),
        base.episode_root(config, episode["episode_id"]) / "logs" / "chrono.log",
        fresh.repo_path(contract["chrono"]["repo"]),
        contract["chrono"]["thread_environment"],
    )
    result = chrono_result(config, contract, episode)
    if not result["accepted"]:
        raise RuntimeError(f"successor Chrono smoke episode rejected: {episode['episode_id']}")
    return result


def adapt_model_inputs(path: Path, bekker_kphi: float) -> None:
    with np.load(path, allow_pickle=False) as archive:
        arrays = {name: np.array(archive[name], copy=True) for name in archive.files}
    arrays["soil_parameters"] = np.asarray([float(bekker_kphi)], dtype=np.float32)
    np.savez_compressed(path, **arrays)


def export_tensors(config: Mapping[str, Any], contract: Mapping[str, Any], episode: Mapping[str, Any]) -> dict[str, Any]:
    manifest = BASE_EXPORT_TENSORS(config, contract, episode)
    tensor_root = base.episode_root(config, episode["episode_id"]) / "tensors"
    input_path = tensor_root / manifest["model_input_file"]
    adapt_model_inputs(input_path, float(episode["soil_parameters"]["bekker_kphi"]))
    with np.load(input_path, allow_pickle=False) as archive:
        parameter_shape = list(archive["soil_parameters"].shape)
        finite = bool(np.isfinite(archive["soil_parameters"]).all())
    manifest["global_parameter_vector"] = ["bekker_kphi"]
    manifest["checks"]["single_kphi_parameter"] = parameter_shape == [1] and finite
    manifest["sha256"]["model_inputs"] = sha256(input_path)
    fresh.write_json(tensor_root / "tensor_manifest.json", manifest)
    return manifest


base.surface_input_root = surface_input_root
base.chrono_result = chrono_result
base.run_chrono = run_chrono
base.export_tensors = export_tensors


def run_parallel(label: str, items: list[Any], workers: int, function: Callable[[Any], Any]) -> None:
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for item in items:
            name = item["episode_id"] if isinstance(item, dict) else str(item)
            print(f"{label} start {name}", flush=True)
            futures[executor.submit(function, item)] = name
        for future in as_completed(futures):
            future.result()
            print(f"{label} complete {futures[future]}", flush=True)


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = load_config(config_path)
    workers = int(args.workers or config["execution"]["workers"])
    if workers != int(config["execution"]["workers"]):
        raise ValueError("worker count differs from frozen successor smoke identity")
    if args.stage == "plan":
        plan = write_plan(config_path, config)
        print(json.dumps({"plan": str(plan_path(config)), "sha256": sha256(plan_path(config)), "counts": plan["counts"], "surface_seeds": plan["surface_seeds"], "protected_targets_opened": False}, indent=2))
        return
    plan = load_plan(config_path, config)
    _successor_path, _successor, _operations_path, contract = merged_contract(config)
    episodes = choose_episodes(plan, args.episode)
    if args.stage in ("chrono", "all"):
        run_parallel("chrono", episodes, workers, lambda item: run_chrono(config, contract, item))
    seeds = sorted({int(item["initial_surface_seed"]) for item in episodes})
    if args.stage in ("bed", "all"):
        run_parallel("bed", seeds, workers, lambda seed: base.build_bed(config, contract, plan, seed))
    if args.stage in ("newton", "all"):
        run_parallel("preparation", seeds, workers, lambda seed: base.prepare_prior(config, contract, plan, seed))
        run_parallel("response", episodes, workers, lambda item: base.run_newton(config, contract, plan, item))
    if args.stage in ("analyze", "all"):
        for episode in episodes:
            base.analyze_episode(config, contract, episode)
    summary = base.summarize(config, contract, plan)
    summary["remaining_train_validation_permitted"] = bool(summary["full_dataset_permitted"])
    summary["test_or_protected_sensitivity_permitted"] = False
    fresh.write_json(base.summary_path(config), summary)
    print(json.dumps({"status": summary["status"], "remaining_train_validation_permitted": summary["remaining_train_validation_permitted"], "test_or_protected_sensitivity_permitted": False, "counts": summary["counts"], "checks": summary["checks"]}, indent=2))


if __name__ == "__main__":
    main()

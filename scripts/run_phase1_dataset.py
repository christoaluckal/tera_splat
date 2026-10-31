#!/usr/bin/env python3
"""Generate and validate the prospective Phase 1 engineering smoke dataset."""

from __future__ import annotations

import argparse
import json
import math
import platform
import sys
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_fresh_phase0_repeatability as fresh
import run_phase1_screening as screening
from chrono_episode_bridge import heightmap_axes, load_episode
from newton_contract import particle_mass_kg
from phase1_latent_fields import (
    PARTICLE_FIELDS,
    contact_column_fields,
    particle_column_fields,
)
from phase1_metric_bed import write_common_base_metric_bed
from run_phase1_contract_screen import canonical_sha256, load_contract


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SMOKE_CONFIG = REPO_ROOT / "configs" / "phase1_dataset_smoke_v1.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_SMOKE_CONFIG)
    parser.add_argument(
        "--stage",
        choices=("plan", "chrono", "bed", "newton", "analyze", "all"),
        default="plan",
    )
    parser.add_argument("--episode", action="append", default=[])
    return parser.parse_args()


def load_smoke_config(path: Path) -> dict[str, Any]:
    value = json.loads(path.resolve().read_text(encoding="utf-8"))
    if value.get("schema_version") != 1:
        raise ValueError("smoke config schema_version must be 1")
    if value.get("dataset_id") != "phase1_dataset_smoke_v1":
        raise ValueError("unexpected smoke dataset identity")
    membership = value["membership"]
    if set(membership) != {"train", "validation", "test"}:
        raise ValueError("smoke membership must declare train, validation, and test")
    if membership["test"]:
        raise ValueError("engineering smoke must not open test targets")
    all_ids = membership["train"] + membership["validation"]
    exit_contract = value["smoke_exit"]
    if len(all_ids) != int(exit_contract["required_episode_count"]):
        raise ValueError("smoke membership count does not match its exit contract")
    if len(membership["train"]) != int(exit_contract["required_train_count"]):
        raise ValueError("smoke train count does not match its exit contract")
    if len(membership["validation"]) != int(exit_contract["required_validation_count"]):
        raise ValueError("smoke validation count does not match its exit contract")
    if len(set(all_ids)) != len(all_ids):
        raise ValueError("smoke episode identities must be unique")
    prior = value["newton_prior"]
    if prior["observation_time_mode"] != "independent_fixed":
        raise ValueError("smoke Newton timing must be independent_fixed")
    if not bool(prior["chrono_target_time_must_not_control_newton_rollout"]):
        raise ValueError("Chrono target time must not control the Newton rollout")
    schema = value["tensor_schema"]
    if not bool(schema["target_arrays_are_never_model_inputs"]):
        raise ValueError("target arrays must be separated from model inputs")
    if "plastic_jacobian" not in schema["excluded_fields"]:
        raise ValueError("audit-rejected plastic state must remain excluded")
    return value


def output_root(config: Mapping[str, Any]) -> Path:
    return fresh.repo_path(config["execution"]["output_root"])


def chrono_root(config: Mapping[str, Any]) -> Path:
    return fresh.repo_path(config["execution"]["chrono_output_root"])


def plan_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "smoke_plan.json"


def summary_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "smoke_summary.json"


def episode_root(config: Mapping[str, Any], episode_id: str) -> Path:
    return output_root(config) / "episodes" / episode_id


def chrono_episode(config: Mapping[str, Any], episode_id: str) -> Path:
    return chrono_root(config) / episode_id


def prior_root(config: Mapping[str, Any], surface_seed: int) -> Path:
    return output_root(config) / "newton_priors" / f"surface_{int(surface_seed)}"


def surface_input_root(
    config: Mapping[str, Any], contract: Mapping[str, Any], surface_seed: int
) -> Path:
    qualification = config.get("surface_qualification")
    if qualification and int(surface_seed) == int(qualification["reserved_seed"]):
        return fresh.repo_path(qualification["root"]) / f"surface_{int(surface_seed)}"
    return screening.surface_dir(contract, int(surface_seed))


def response_root(config: Mapping[str, Any], episode_id: str) -> Path:
    return episode_root(config, episode_id) / "newton_response"


def source_paths(
    config_path: Path, config: Mapping[str, Any], contract: Mapping[str, Any]
) -> dict[str, Path]:
    chrono_repo = fresh.repo_path(contract["chrono"]["repo"])
    paths = {
        "smoke_config": config_path.resolve(),
        "dataset_runner": Path(__file__).resolve(),
        "dataset_tests": REPO_ROOT / "tests" / "test_phase1_dataset.py",
        "execution_helpers": SCRIPT_DIR / "run_fresh_phase0_repeatability.py",
        "contract_planner": SCRIPT_DIR / "run_phase1_contract_screen.py",
        "screening_runner": SCRIPT_DIR / "run_phase1_screening.py",
        "common_base_builder": SCRIPT_DIR / "phase1_metric_bed.py",
        "latent_fields": SCRIPT_DIR / "phase1_latent_fields.py",
        "chrono_episode_bridge": SCRIPT_DIR / "chrono_episode_bridge.py",
        "particle_io": SCRIPT_DIR / "particle_io.py",
        "newton_preparation": SCRIPT_DIR / "run_newton_prepared_bed.py",
        "newton_response": SCRIPT_DIR / "run_newton_cylinder_diagnostic.py",
        "newton_contract": SCRIPT_DIR / "newton_contract.py",
        "newton_base_config": fresh.repo_path(contract["newton"]["base_config"]),
        "common_base_contract": fresh.repo_path(
            config["newton_prior"]["builder_contract"]
        ),
        "chrono_episode_cli": chrono_repo / "run_cylinder_episode.py",
        "chrono_episode_impl": chrono_repo
        / "quick_support_demo"
        / "chrono_demo"
        / "cylinder_episode.py",
        "chrono_scm_builder": chrono_repo
        / "quick_support_demo"
        / "chrono_demo"
        / "build_scm_pit.py",
        "chrono_mesh_builder": chrono_repo
        / "quick_support_demo"
        / "chrono_demo"
        / "difficult_terrain.py",
        "chrono_world_builder": chrono_repo
        / "quick_support_demo"
        / "chrono_demo"
        / "build_world.py",
        "chrono_config_loader": chrono_repo / "quick_support_demo" / "config.py",
        "chrono_demo_config": chrono_repo
        / "quick_support_demo"
        / "configs"
        / "demo.yaml",
        "chrono_world_config": chrono_repo
        / "quick_support_demo"
        / "configs"
        / "world.yaml",
        "chrono_terrain_config": chrono_repo
        / "quick_support_demo"
        / "configs"
        / "terrain.yaml",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing smoke sources: {missing}")
    return paths


def prerequisite_paths(config: Mapping[str, Any]) -> dict[str, Path]:
    prerequisites = config["prerequisites"]
    paths = {
        "dataset_plan": fresh.repo_path(config["dataset_plan"]),
        "physical_summary": fresh.repo_path(prerequisites["physical_summary"]),
        "latent_summary": fresh.repo_path(prerequisites["latent_summary"]),
        "phase0_admission_contract": fresh.repo_path(
            "configs/static_proxy_hierarchical_v3_20261017.json"
        ),
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing smoke prerequisites: {missing}")
    return paths


def require_prerequisites(config: Mapping[str, Any]) -> dict[str, Any]:
    paths = prerequisite_paths(config)
    physical = json.loads(paths["physical_summary"].read_text(encoding="utf-8"))
    latent = json.loads(paths["latent_summary"].read_text(encoding="utf-8"))
    expected = config["prerequisites"]
    if physical.get("status") != expected["require_physical_status"]:
        raise RuntimeError("the passing physical screen is required")
    if not bool(physical.get("bulk_dataset_permitted")):
        raise RuntimeError("the physical screen does not permit dataset generation")
    if latent.get("status") != expected["require_latent_status"]:
        raise RuntimeError("the corrected latent qualification must pass")
    qualified = sorted(latent.get("qualified_nonkinematic_families", []))
    if qualified != sorted(expected["qualified_nonkinematic_families"]):
        raise RuntimeError("qualified non-kinematic families changed")
    for family in expected["excluded_nonkinematic_families"]:
        if family in qualified:
            raise RuntimeError(f"excluded latent family became qualified: {family}")
    return {"physical": physical, "latent": latent}


def selected_episodes(
    config: Mapping[str, Any], dataset_plan: Mapping[str, Any]
) -> list[dict[str, Any]]:
    by_id = {
        episode["episode_id"]: episode
        for split in ("train", "validation", "test")
        for episode in dataset_plan["episodes"][split]
    }
    result: list[dict[str, Any]] = []
    for split in ("train", "validation"):
        for episode_id in config["membership"][split]:
            if episode_id not in by_id:
                raise ValueError(f"unknown frozen episode: {episode_id}")
            episode = by_id[episode_id]
            if episode["split"] != split:
                raise ValueError(f"smoke episode split mismatch: {episode_id}")
            if episode["target_access"] == "locked":
                raise ValueError(f"smoke cannot open locked test target: {episode_id}")
            result.append(episode)
    expected_seeds = sorted(int(x) for x in config["smoke_exit"]["required_surface_seeds"])
    actual_seeds = sorted({int(x["initial_surface_seed"]) for x in result})
    if actual_seeds != expected_seeds:
        raise ValueError(
            f"smoke surface coverage changed: {actual_seeds} != {expected_seeds}"
        )
    return result


def environment_probe(config: Mapping[str, Any], contract: Mapping[str, Any]) -> dict[str, Any]:
    chrono_repo = fresh.repo_path(contract["chrono"]["repo"])
    chrono_command = [
        *(str(value) for value in contract["chrono"]["command"]),
        "-c",
        (
            "import json,platform; import pychrono; import pychrono.vehicle; "
            "print(json.dumps({'python':platform.python_version(),"
            "'pychrono':getattr(pychrono,'__version__','unknown'),"
            "'vehicle_binding':True}))"
        ),
    ]
    chrono_lines = [
        line.strip()
        for line in fresh.command_output(chrono_command, chrono_repo).splitlines()
        if line.strip()
    ]
    if not chrono_lines:
        raise RuntimeError("Chrono environment probe returned no output")
    chrono_environment = json.loads(chrono_lines[-1])
    if chrono_environment.get("vehicle_binding") is not True:
        raise RuntimeError("Chrono vehicle binding is unavailable")
    python = str(Path(config["execution"]["newton_python"]).resolve())
    newton_lines = [
        line.strip()
        for line in fresh.command_output(
            [
                python,
                "-c",
                (
                    "import json,platform,numpy,warp,newton; "
                    "print(json.dumps({'python':platform.python_version(),"
                    "'numpy':numpy.__version__,'warp':warp.__version__,"
                    "'newton':getattr(newton,'__version__','unknown')}))"
                ),
            ],
            REPO_ROOT,
        ).splitlines()
        if line.strip()
    ]
    if not newton_lines:
        raise RuntimeError("Newton environment probe returned no output")
    gpu = fresh.command_output(
        [
            "nvidia-smi",
            "--query-gpu=name,uuid,driver_version",
            "--format=csv,noheader",
        ],
        REPO_ROOT,
    )
    if not gpu or "failed" in gpu.lower():
        raise RuntimeError(f"GPU environment probe failed: {gpu}")
    return {
        "captured_by_python": platform.python_version(),
        "chrono": chrono_environment,
        "newton": json.loads(newton_lines[-1]),
        "gpu": gpu,
        "device": config["execution"]["device"],
    }


def build_plan(
    config_path: Path,
    config: Mapping[str, Any],
    contract_path: Path,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    prerequisites = require_prerequisites(config)
    paths = prerequisite_paths(config)
    dataset_plan = json.loads(paths["dataset_plan"].read_text(encoding="utf-8"))
    if dataset_plan.get("contract_sha256") != fresh.sha256_file(contract_path):
        raise RuntimeError("frozen dataset plan does not match the Phase 1 contract")
    episodes = selected_episodes(config, dataset_plan)
    surface_inputs: dict[str, str] = {}
    for seed in sorted({int(x["initial_surface_seed"]) for x in episodes}):
        root = surface_input_root(config, contract, seed)
        for label, filename in (
            ("heightmap", "initial_heightmap_m.npy"),
            ("qualification", "qualification_summary.json"),
        ):
            path = root / filename
            if not path.is_file():
                raise FileNotFoundError(f"missing qualified surface input: {path}")
            surface_inputs[f"surface_{seed}:{label}"] = fresh.sha256_file(path)
        qualification = json.loads(
            (root / "qualification_summary.json").read_text(encoding="utf-8")
        )
        if not bool(qualification.get("qualified")):
            raise RuntimeError(f"surface {seed} is not qualified")
    sources = source_paths(config_path, config, contract)
    return {
        "schema_version": 1,
        "dataset_id": config["dataset_id"],
        "status": "frozen_before_first_target",
        "config_sha256": fresh.sha256_file(config_path),
        "phase1_contract_sha256": fresh.sha256_file(contract_path),
        "dataset_plan_sha256": fresh.sha256_file(paths["dataset_plan"]),
        "episode_manifest_sha256": dataset_plan["episode_manifest_sha256"],
        "test_lock_sha256": dataset_plan["test_lock_sha256"],
        "selected_episode_manifest_sha256": canonical_sha256(episodes),
        "source_sha256": {
            name: fresh.sha256_file(path) for name, path in sources.items()
        },
        "input_sha256": {
            **{name: fresh.sha256_file(path) for name, path in paths.items()},
            **surface_inputs,
        },
        "environment": environment_probe(config, contract),
        "repository_revisions": {
            "tera_splat": fresh.command_output(
                ["git", "rev-parse", "HEAD"], REPO_ROOT
            ),
            "tera_splat_sim": fresh.command_output(
                ["git", "rev-parse", "HEAD"], fresh.repo_path(contract["chrono"]["repo"])
            ),
        },
        "episodes": episodes,
        "counts": {
            "train": len(config["membership"]["train"]),
            "validation": len(config["membership"]["validation"]),
            "test": 0,
        },
        "surface_seeds": sorted({int(x["initial_surface_seed"]) for x in episodes}),
        "qualified_nonkinematic_families": prerequisites["latent"][
            "qualified_nonkinematic_families"
        ],
        "excluded_nonkinematic_families": config["prerequisites"][
            "excluded_nonkinematic_families"
        ],
        "newton_prior": config["newton_prior"],
        "tensor_schema": config["tensor_schema"],
        "full_dataset_permitted": False,
    }


def write_plan(
    config_path: Path,
    config: Mapping[str, Any],
    contract_path: Path,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    plan = build_plan(config_path, config, contract_path, contract)
    path = plan_path(config)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        stable = (
            "config_sha256",
            "phase1_contract_sha256",
            "dataset_plan_sha256",
            "episode_manifest_sha256",
            "test_lock_sha256",
            "selected_episode_manifest_sha256",
            "source_sha256",
            "input_sha256",
            "environment",
            "episodes",
            "tensor_schema",
        )
        changed = [key for key in stable if existing.get(key) != plan.get(key)]
        if changed:
            raise RuntimeError(f"refusing to replace a different smoke plan: {changed}")
        return existing
    fresh.write_json(path, plan)
    return plan


def load_plan(
    config_path: Path,
    config: Mapping[str, Any],
    contract_path: Path,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    path = plan_path(config)
    if not path.is_file():
        raise RuntimeError("smoke plan is missing; run --stage plan first")
    existing = json.loads(path.read_text(encoding="utf-8"))
    current = build_plan(config_path, config, contract_path, contract)
    stable = (
        "config_sha256",
        "phase1_contract_sha256",
        "dataset_plan_sha256",
        "episode_manifest_sha256",
        "test_lock_sha256",
        "selected_episode_manifest_sha256",
        "source_sha256",
        "input_sha256",
        "environment",
        "episodes",
        "tensor_schema",
    )
    changed = [key for key in stable if existing.get(key) != current.get(key)]
    if changed:
        raise RuntimeError(f"smoke plan identity changed: {changed}")
    return existing


def choose_episodes(plan: Mapping[str, Any], requested: list[str]) -> list[dict[str, Any]]:
    episodes = list(plan["episodes"])
    by_id = {episode["episode_id"]: episode for episode in episodes}
    unknown = sorted(set(requested) - set(by_id))
    if unknown:
        raise ValueError(f"unknown smoke episodes: {unknown}")
    return [by_id[name] for name in requested] if requested else episodes


def chrono_result(
    config: Mapping[str, Any], contract: Mapping[str, Any], episode: Mapping[str, Any]
) -> dict[str, Any]:
    root = chrono_episode(config, episode["episode_id"])
    manifest_path = root / "manifest.yaml"
    if not manifest_path.is_file():
        return {"complete": False, "accepted": False, "episode": str(root)}
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    action = json.loads((root / manifest["action"]).read_text(encoding="utf-8"))
    surface_summary = json.loads(
        (
            surface_input_root(config, contract, int(episode["initial_surface_seed"]))
            / "generator_summary.json"
        ).read_text(encoding="utf-8")
    )
    valid_name = str(manifest["heightmap"]["valid_mask"]).split(";", 1)[0].strip()
    valid = np.load(root / valid_name, allow_pickle=False).astype(bool)
    states = [
        np.load(root / manifest["states"][name], allow_pickle=False)
        for name in ("initial", "loaded", "residual")
    ]
    soil = manifest["chrono"]["soil_parameters"]
    surface = manifest["initial_surface"]
    checks = {
        "episode_id": action["episode_id"] == episode["episode_id"],
        "mass": math.isclose(
            float(action["mass_kg"]), float(episode["equivalent_mass_kg"])
        ),
        "position": bool(
            np.allclose(action["center_xy_m"], episode["center_xy_m"], atol=1.0e-12)
        ),
        "radius": math.isclose(float(action["radius_m"]), float(episode["radius_m"])),
        "soil_kphi": math.isclose(
            float(soil["bekker_kphi"]),
            float(episode["soil_parameters"]["bekker_kphi"]),
        ),
        "soil_friction": math.isclose(
            float(soil["mohr_friction_deg"]),
            float(episode["soil_parameters"]["mohr_friction_deg"]),
        ),
        "initial_surface": surface["requested_array_sha256"]
        == surface_summary["metrics"]["array_sha256"],
        "initial_roundtrip": float(surface["sampled_max_abs_error_m"]) <= 1.0e-5,
        "loading_accepted": bool(manifest["chrono"]["loading_convergence"]["accepted"]),
        "finite_valid_surface": all(np.isfinite(value[valid]).all() for value in states),
    }
    return {
        "complete": True,
        "accepted": all(checks.values()),
        "episode": str(root.resolve()),
        "checks": checks,
        "loaded_time_s": float(
            manifest["chrono"]["loading_convergence"]["final_sample_time_s"]
        ),
        "valid_cells": int(np.count_nonzero(valid)),
    }


def run_chrono(
    config: Mapping[str, Any], contract: Mapping[str, Any], episode: Mapping[str, Any]
) -> dict[str, Any]:
    existing = chrono_result(config, contract, episode)
    if existing["complete"]:
        if not existing["accepted"]:
            raise RuntimeError(f"existing Chrono episode is rejected: {episode['episode_id']}")
        return existing
    destination = chrono_episode(config, episode["episode_id"])
    if destination.exists():
        raise RuntimeError(f"refusing incomplete Chrono episode: {destination}")
    cfg = contract["chrono"]
    source = (
        surface_input_root(config, contract, int(episode["initial_surface_seed"]))
        / "initial_heightmap_m.npy"
    )
    command = [
        *(str(value) for value in cfg["command"]),
        str(fresh.repo_path(cfg["repo"]) / "run_cylinder_episode.py"),
        "--episode-id",
        episode["episode_id"],
        "--mass-kg",
        str(episode["equivalent_mass_kg"]),
        "--xy",
        *(str(value) for value in episode["center_xy_m"]),
        "--radius-m",
        str(episode["radius_m"]),
        "--height-m",
        str(contract["action_domain"]["height_m"]),
        "--start-clearance-m",
        str(contract["action_domain"]["start_clearance_m"]),
        "--timestep-s",
        str(cfg["timestep_s"]),
        "--scm-grid-spacing-m",
        str(cfg["scm_grid_spacing_m"]),
        "--scm-pit-size-m",
        *(str(value) for value in cfg["scm_pit_size_m"]),
        "--max-loading-time-s",
        str(cfg["max_loading_time_s"]),
        "--min-loading-time-s",
        str(cfg["min_loading_time_s"]),
        "--loading-linear-speed-threshold-mps",
        str(cfg["loading_linear_speed_threshold_mps"]),
        "--loading-angular-speed-threshold-radps",
        str(cfg["loading_angular_speed_threshold_radps"]),
        "--loading-hold-time-s",
        str(cfg["loading_hold_time_s"]),
        "--residual-settle-s",
        str(cfg["residual_duration_s"]),
        "--initial-heightmap-npy",
        str(source),
        "--bekker-kphi",
        str(episode["soil_parameters"]["bekker_kphi"]),
        "--mohr-friction-deg",
        str(episode["soil_parameters"]["mohr_friction_deg"]),
        "--output-dir",
        str(destination),
    ]
    if cfg["vertical_guide"]:
        command.append("--vertical-guide")
    fresh.run_logged(
        command,
        episode_root(config, episode["episode_id"]) / "logs" / "chrono.log",
        fresh.repo_path(cfg["repo"]),
        cfg["thread_environment"],
    )
    result = chrono_result(config, contract, episode)
    if not result["accepted"]:
        raise RuntimeError(f"Chrono smoke episode rejected: {episode['episode_id']}")
    return result


def reference_episode_for_seed(
    plan: Mapping[str, Any], surface_seed: int
) -> dict[str, Any]:
    return next(
        episode
        for episode in plan["episodes"]
        if int(episode["initial_surface_seed"]) == int(surface_seed)
    )


def build_bed(
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    plan: Mapping[str, Any],
    surface_seed: int,
) -> Path:
    root = prior_root(config, surface_seed)
    output = root / "metric_bed"
    expected = (
        output / "particles_initial_mpm.ply",
        output / "ground_plane_metadata.json",
    )
    if all(path.is_file() for path in expected):
        return output
    if output.exists():
        raise RuntimeError(f"refusing incomplete smoke metric bed: {output}")
    episode = reference_episode_for_seed(plan, surface_seed)
    if not chrono_result(config, contract, episode).get("accepted"):
        raise RuntimeError("accepted Chrono episode required before metric-bed build")
    chrono_dir = chrono_episode(config, episode["episode_id"])
    manifest, _action, initial, _valid = load_episode(chrono_dir)
    builder_contract = json.loads(
        fresh.repo_path(config["newton_prior"]["builder_contract"]).read_text(
            encoding="utf-8"
        )
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
        "smoke_plan_sha256": fresh.sha256_file(plan_path(config)),
        "surface_seed": int(surface_seed),
        "reference_episode_id": episode["episode_id"],
        "reference_chrono_initial_sha256": fresh.sha256_file(
            chrono_dir / manifest["states"]["initial"]
        ),
        "loaded_or_post_unload_target_consumed": False,
    }
    fresh.write_json(output / "ground_plane_metadata.json", metadata)
    return output


def prepare_prior(
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    plan: Mapping[str, Any],
    surface_seed: int,
) -> Path:
    bed = build_bed(config, contract, plan, surface_seed)
    root = prior_root(config, surface_seed)
    preparation = root / "preparation"
    manifest_path = preparation / "newton_prepared_bed_manifest.json"
    if manifest_path.is_file():
        prepared = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not bool(prepared.get("accepted")):
            raise RuntimeError(f"existing preparation rejected for surface {surface_seed}")
        return preparation
    if preparation.exists():
        raise RuntimeError(f"refusing incomplete smoke preparation: {preparation}")
    episode = reference_episode_for_seed(plan, surface_seed)
    newton = contract["newton"]
    fresh.run_logged(
        [
            str(Path(config["execution"]["newton_python"]).resolve()),
            str(SCRIPT_DIR / "run_newton_prepared_bed.py"),
            "--config",
            str(fresh.repo_path(newton["base_config"])),
            "--particles-ply",
            str(bed / "particles_initial_mpm.ply"),
            "--metadata-json",
            str(bed / "ground_plane_metadata.json"),
            "--chrono-episode",
            str(chrono_episode(config, episode["episode_id"])),
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
        raise RuntimeError(f"Newton preparation rejected for surface {surface_seed}")
    return preparation


def run_newton(
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    plan: Mapping[str, Any],
    episode: Mapping[str, Any],
) -> Path:
    preparation = prepare_prior(
        config, contract, plan, int(episode["initial_surface_seed"])
    )
    response = response_root(config, episode["episode_id"])
    manifest_path = response / "newton_cylinder_manifest.json"
    if manifest_path.is_file():
        return response
    if response.exists():
        raise RuntimeError(f"refusing incomplete smoke Newton response: {response}")
    newton = contract["newton"]
    prior = config["newton_prior"]
    fresh.run_logged(
        [
            str(Path(config["execution"]["newton_python"]).resolve()),
            str(SCRIPT_DIR / "run_newton_cylinder_diagnostic.py"),
            "--config",
            str(fresh.repo_path(newton["base_config"])),
            "--prepared-dir",
            str(preparation),
            "--candidate-preparation",
            "--chrono-episode",
            str(chrono_episode(config, episode["episode_id"])),
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
        episode_root(config, episode["episode_id"])
        / "logs"
        / "newton_response.log",
        REPO_ROOT,
    )
    return response


def box_mean_2d(values: np.ndarray, width: int) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 2 or width <= 0 or width % 2 == 0:
        raise ValueError("box mean requires a 2D field and positive odd width")
    radius = width // 2
    padded = np.pad(array, radius, mode="edge")
    result = np.zeros_like(array)
    for row_offset in range(width):
        for column_offset in range(width):
            result += padded[
                row_offset : row_offset + array.shape[0],
                column_offset : column_offset + array.shape[1],
            ]
    return result / float(width * width)


def load_state_archive(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as archive:
        arrays = {name: np.array(archive[name], copy=True) for name in PARTICLE_FIELDS}
        for name in ("contact_position_m", "contact_impulse_ns", "contact_collider_id"):
            arrays[name] = np.array(archive[name], copy=True)
    return arrays


def _rmse(candidate: np.ndarray, target: np.ndarray, mask: np.ndarray) -> float:
    delta = np.asarray(candidate, dtype=np.float64)[mask] - np.asarray(
        target, dtype=np.float64
    )[mask]
    return float(np.sqrt(np.mean(delta * delta)))


def export_tensors(
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    episode: Mapping[str, Any],
) -> dict[str, Any]:
    episode_id = episode["episode_id"]
    chrono_dir = chrono_episode(config, episode_id)
    manifest, _action, chrono_initial, chrono_valid = load_episode(chrono_dir)
    chrono_loaded = np.load(
        chrono_dir / manifest["states"]["loaded"], allow_pickle=False
    )
    chrono_post = np.load(
        chrono_dir / manifest["states"]["residual"], allow_pickle=False
    )
    response = response_root(config, episode_id)
    newton_maps = {
        "initial": np.load(response / "initial_heightmap_m.npy", allow_pickle=False),
        "loaded": np.load(response / "loaded_heightmap_m.npy", allow_pickle=False),
        "post_unload": np.load(
            response / "residual_heightmap_m.npy", allow_pickle=False
        ),
    }
    newton_valid = np.load(
        response / "valid_heightmap_mask.npy", allow_pickle=False
    ).astype(bool)
    valid = chrono_valid & newton_valid
    xs, ys = heightmap_axes(manifest)
    grid_x, grid_y = np.meshgrid(xs, ys, indexing="xy")
    center = np.asarray(episode["center_xy_m"], dtype=np.float64)
    relative_x = grid_x - center[0]
    relative_y = grid_y - center[1]
    radius = float(episode["radius_m"])
    radial_distance = np.sqrt(relative_x * relative_x + relative_y * relative_y)

    base_config = json.loads(
        fresh.repo_path(contract["newton"]["base_config"]).read_text(encoding="utf-8")
    )
    mass = particle_mass_kg(
        float(base_config["material"]["density_kg_m3"]),
        float(contract["newton"]["metric_bed_source"]["particle_spacing_m"]),
    )
    h2_fields: dict[str, np.ndarray] = {}
    state_names = {"loaded": "loaded", "post_unload": "residual"}
    for checkpoint, filename_label in state_names.items():
        arrays = load_state_archive(response / f"newton_state_{filename_label}.npz")
        columns = particle_column_fields(
            arrays,
            x_coordinates_m=xs,
            y_coordinates_m=ys,
            particle_mass_kg=mass,
        )
        contacts = contact_column_fields(
            arrays["contact_position_m"],
            arrays["contact_impulse_ns"],
            x_coordinates_m=xs,
            y_coordinates_m=ys,
        )
        h2_fields.update(
            {
                f"{checkpoint}_column_particle_count": columns[
                    "column_particle_count"
                ].astype(np.int32),
                f"{checkpoint}_column_mass_kg": columns["column_mass_kg"].astype(
                    np.float32
                ),
                f"{checkpoint}_column_mean_action_velocity_mps": box_mean_2d(
                    columns["column_mean_velocity_xyz_mps"][..., 2], 3
                ).astype(np.float32),
                f"{checkpoint}_contact_node_count": contacts[
                    "contact_node_count"
                ].astype(np.int32),
                f"{checkpoint}_contact_normal_impulse_ns": contacts[
                    "contact_normal_impulse_ns"
                ].astype(np.float32),
                f"{checkpoint}_column_mean_stress_mean_pa": columns[
                    "column_mean_stress_mean_pa"
                ].astype(np.float32),
                f"{checkpoint}_column_mean_stress_von_mises_pa": columns[
                    "column_mean_stress_von_mises_pa"
                ].astype(np.float32),
                f"{checkpoint}_column_mean_elastic_jacobian": columns[
                    "column_mean_elastic_jacobian"
                ].astype(np.float32),
                f"{checkpoint}_column_mean_elastic_isochoric_shear": columns[
                    "column_mean_elastic_isochoric_shear"
                ].astype(np.float32),
            }
        )

    model_inputs = {
        "initial_height_m": chrono_initial.astype(np.float32),
        "newton_loaded_displacement_m": (
            newton_maps["loaded"] - newton_maps["initial"]
        ).astype(np.float32),
        "newton_post_unload_displacement_m": (
            newton_maps["post_unload"] - newton_maps["initial"]
        ).astype(np.float32),
        "valid_support": valid,
        "action_relative_x_m": relative_x.astype(np.float32),
        "action_relative_y_m": relative_y.astype(np.float32),
        "action_signed_distance_m": (radial_distance - radius).astype(np.float32),
        "action_footprint": (radial_distance <= radius),
        "action_phase": np.asarray(
            [
                [center[0], center[1], episode["normal_force_n"], 0.0],
                [center[0], center[1], episode["normal_force_n"], 1.0],
            ],
            dtype=np.float32,
        ),
        "soil_parameters": np.asarray(
            [
                episode["soil_parameters"]["bekker_kphi"],
                episode["soil_parameters"]["mohr_friction_deg"],
            ],
            dtype=np.float32,
        ),
        **h2_fields,
    }
    targets = {
        "chrono_loaded_height_m": np.asarray(chrono_loaded, dtype=np.float32),
        "chrono_post_unload_height_m": np.asarray(chrono_post, dtype=np.float32),
    }
    expected_shape = chrono_initial.shape
    nonfinite: list[str] = []
    wrong_shape: list[str] = []
    for name, value in {**model_inputs, **targets}.items():
        array = np.asarray(value)
        if array.ndim >= 2 and name not in {"action_phase"} and array.shape != expected_shape:
            wrong_shape.append(name)
        if not np.isfinite(array).all():
            nonfinite.append(name)
    plastic_keys = sorted(name for name in model_inputs if "plastic" in name)
    tensor_root = episode_root(config, episode_id) / "tensors"
    tensor_root.mkdir(parents=True, exist_ok=True)
    input_path = tensor_root / "model_inputs.npz"
    target_path = tensor_root / "targets.npz"
    np.savez_compressed(input_path, **model_inputs)
    np.savez_compressed(target_path, **targets)
    uncompressed_bytes = int(
        sum(np.asarray(value).nbytes for value in {**model_inputs, **targets}.values())
    )
    local = valid & (radial_distance <= 2.0 * radius)
    losses: dict[str, dict[str, float]] = {}
    signals: dict[str, float] = {}
    for checkpoint, target in (
        ("loaded", chrono_loaded),
        ("post_unload", chrono_post),
    ):
        signals[checkpoint] = _rmse(target, chrono_initial, local)
        losses[checkpoint] = {
            "no_deformation_local_rmse_m": _rmse(chrono_initial, target, local),
            "raw_newton_local_rmse_m": _rmse(
                newton_maps[checkpoint], target, local
            ),
        }
    checks = {
        "no_test_target": episode["split"] != "test",
        "model_inputs_targets_separate": input_path != target_path,
        "all_expected_shapes": not wrong_shape,
        "all_finite": not nonfinite,
        "valid_support_nonempty": bool(np.any(valid)),
        "twice_radius_support_nonempty": bool(np.any(local)),
        "plastic_excluded": not plastic_keys,
        "target_action_signal": min(signals.values())
        >= float(config["smoke_exit"]["minimum_target_action_rms_m"]),
        "memory_within_limit": uncompressed_bytes
        <= int(config["smoke_exit"]["maximum_uncompressed_tensor_bytes_per_episode"]),
        "finite_baseline_losses": all(
            np.isfinite(value)
            for checkpoint in losses.values()
            for value in checkpoint.values()
        ),
    }
    tensor_manifest = {
        "schema_version": 1,
        "episode_id": episode_id,
        "split": episode["split"],
        "grid_shape": list(expected_shape),
        "grid_spacing_m": float(manifest["heightmap"]["spacing_m"]),
        "model_input_file": input_path.name,
        "target_file": target_path.name,
        "model_input_fields": sorted(model_inputs),
        "target_fields": sorted(targets),
        "qualified_nonkinematic_families": ["stress", "elastic"],
        "excluded_nonkinematic_families": ["plastic"],
        "uncompressed_tensor_bytes": uncompressed_bytes,
        "target_action_rms_m": signals,
        "baseline_losses": losses,
        "checks": checks,
        "diagnostics": {
            "wrong_shape_fields": wrong_shape,
            "nonfinite_fields": nonfinite,
            "plastic_keys": plastic_keys,
        },
        "sha256": {
            "model_inputs": fresh.sha256_file(input_path),
            "targets": fresh.sha256_file(target_path),
        },
    }
    fresh.write_json(tensor_root / "tensor_manifest.json", tensor_manifest)
    return tensor_manifest


def admission_policy(contract: Mapping[str, Any]) -> dict[str, Any]:
    inherited = json.loads(
        fresh.repo_path(contract["inheritance"]["phase0_contract"]).read_text(
            encoding="utf-8"
        )
    )
    return inherited["hierarchical_admission"]


def analyze_episode(
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    episode: Mapping[str, Any],
) -> dict[str, Any]:
    episode_id = episode["episode_id"]
    chrono = chrono_result(config, contract, episode)
    preparation_path = (
        prior_root(config, int(episode["initial_surface_seed"]))
        / "preparation"
        / "newton_prepared_bed_manifest.json"
    )
    response = response_root(config, episode_id)
    response_path = response / "newton_cylinder_manifest.json"
    if not chrono.get("complete") or not preparation_path.is_file() or not response_path.is_file():
        return {
            "episode_id": episode_id,
            "split": episode["split"],
            "complete": False,
            "admitted": False,
        }
    prepared = json.loads(preparation_path.read_text(encoding="utf-8"))
    manifest = json.loads(response_path.read_text(encoding="utf-8"))
    metadata = json.loads(
        (
            prior_root(config, int(episode["initial_surface_seed"]))
            / "metric_bed"
            / "ground_plane_metadata.json"
        ).read_text(encoding="utf-8")
    )
    policy = admission_policy(contract)
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
    gross_depth = spacing * float(
        level_2["gross_penetration_fraction_of_particle_spacing"]
    )
    interaction = {
        "within_gross_depth": float(penetration["max_center_penetration_m"])
        <= gross_depth,
        "within_gross_affected_fraction": float(inside / particle_count)
        <= float(level_2["gross_inside_particle_fraction"]),
    }
    tensor_manifest = export_tensors(config, contract, episode)
    tensor_checks = tensor_manifest["checks"]
    result = {
        "schema_version": 1,
        "episode_id": episode_id,
        "split": episode["split"],
        "input_sha256": episode["input_sha256"],
        "complete": True,
        "admitted": all(numerical.values())
        and all(interaction.values())
        and all(tensor_checks.values()),
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
        "tensor_manifest": tensor_manifest,
        "artifacts": {
            "chrono_episode": str(chrono_episode(config, episode_id).resolve()),
            "newton_prior": str(
                prior_root(config, int(episode["initial_surface_seed"])).resolve()
            ),
            "newton_response": str(response.resolve()),
            "tensors": str(
                (episode_root(config, episode_id) / "tensors").resolve()
            ),
        },
    }
    fresh.write_json(episode_root(config, episode_id) / "episode_summary.json", result)
    return result


def summarize(
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    episodes = [analyze_episode(config, contract, episode) for episode in plan["episodes"]]
    exit_contract = config["smoke_exit"]
    counts = {
        "total": len(episodes),
        "train": sum(item["split"] == "train" for item in episodes),
        "validation": sum(item["split"] == "validation" for item in episodes),
        "test": sum(item["split"] == "test" for item in episodes),
    }
    checks = {
        "episode_count": counts["total"] == int(exit_contract["required_episode_count"]),
        "train_count": counts["train"] == int(exit_contract["required_train_count"]),
        "validation_count": counts["validation"]
        == int(exit_contract["required_validation_count"]),
        "test_targets_unopened": counts["test"] == 0,
        "all_complete": all(item["complete"] for item in episodes),
        "all_admitted": all(item["admitted"] for item in episodes),
        "surface_coverage": sorted(plan["surface_seeds"])
        == sorted(int(x) for x in exit_contract["required_surface_seeds"]),
    }
    passed = all(checks.values())
    summary = {
        "schema_version": 1,
        "dataset_id": config["dataset_id"],
        "status": "passed" if passed else "failed_or_incomplete",
        "full_dataset_permitted": passed,
        "counts": counts,
        "checks": checks,
        "qualified_nonkinematic_families": plan[
            "qualified_nonkinematic_families"
        ],
        "excluded_nonkinematic_families": plan[
            "excluded_nonkinematic_families"
        ],
        "identity": {
            "smoke_plan_sha256": fresh.sha256_file(plan_path(config)),
            "selected_episode_manifest_sha256": plan[
                "selected_episode_manifest_sha256"
            ],
            "episode_manifest_sha256": plan["episode_manifest_sha256"],
            "test_lock_sha256": plan["test_lock_sha256"],
        },
        "episodes": {item["episode_id"]: item for item in episodes},
    }
    fresh.write_json(summary_path(config), summary)
    return summary


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = load_smoke_config(config_path)
    contract_path = fresh.repo_path(config["phase1_contract"])
    contract = load_contract(contract_path)
    if args.stage == "plan":
        plan = write_plan(config_path, config, contract_path, contract)
        print(
            json.dumps(
                {
                    "plan": str(plan_path(config)),
                    "episodes": len(plan["episodes"]),
                    "counts": plan["counts"],
                    "surface_seeds": plan["surface_seeds"],
                    "test_targets_opened": False,
                },
                indent=2,
            )
        )
        return
    plan = load_plan(config_path, config, contract_path, contract)
    episodes = choose_episodes(plan, args.episode)
    if args.stage in ("chrono", "all"):
        for episode in episodes:
            run_chrono(config, contract, episode)
    if args.stage in ("bed", "all"):
        for seed in sorted({int(x["initial_surface_seed"]) for x in episodes}):
            build_bed(config, contract, plan, seed)
    if args.stage in ("newton", "all"):
        for episode in episodes:
            run_newton(config, contract, plan, episode)
    if args.stage in ("analyze", "all"):
        for episode in episodes:
            analyze_episode(config, contract, episode)
    summary = summarize(config, contract, plan)
    print(
        json.dumps(
            {
                "status": summary["status"],
                "full_dataset_permitted": summary["full_dataset_permitted"],
                "counts": summary["counts"],
                "checks": summary["checks"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

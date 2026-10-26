#!/usr/bin/env python3
"""Qualify Phase 1 initial surfaces and Chrono material-box points."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_fresh_phase0_matrix as phase0_matrix
import run_fresh_phase0_repeatability as fresh
from chrono_episode_bridge import load_episode, write_metric_bed
from phase1_surface import array_sha256, generate_surface, limits_from_contract
from run_phase1_contract_screen import load_contract


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = REPO_ROOT / "configs" / "phase1_bed_state_v1.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument(
        "--stage",
        choices=("plan", "surfaces", "chrono", "bed", "newton", "analyze", "all"),
        default="plan",
    )
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--newton-python", type=Path)
    parser.add_argument("--device")
    return parser.parse_args()


def output_root(contract: dict[str, Any]) -> Path:
    return fresh.repo_path(contract["newton"]["output_root"]) / "screening"


def chrono_root(contract: dict[str, Any]) -> Path:
    return fresh.repo_path(contract["chrono"]["output_root"]) / "screening" / "material"


def frozen_dataset_plan(contract: dict[str, Any]) -> Path:
    return fresh.repo_path(contract["dataset"]["plan_path"])


def screen_plan_path(contract: dict[str, Any]) -> Path:
    return output_root(contract) / "screening_plan.json"


def source_paths(contract: dict[str, Any]) -> dict[str, Path]:
    chrono_repo = fresh.repo_path(contract["chrono"]["repo"])
    paths = {
        "screening_runner": Path(__file__).resolve(),
        "surface_generator": SCRIPT_DIR / "phase1_surface.py",
        "contract_planner": SCRIPT_DIR / "run_phase1_contract_screen.py",
        "chrono_episode_bridge": SCRIPT_DIR / "chrono_episode_bridge.py",
        "particle_io": SCRIPT_DIR / "particle_io.py",
        "chrono_episode_cli": chrono_repo / "run_cylinder_episode.py",
        "chrono_episode_impl": chrono_repo / "quick_support_demo" / "chrono_demo" / "cylinder_episode.py",
        "chrono_scm_builder": chrono_repo / "quick_support_demo" / "chrono_demo" / "build_scm_pit.py",
        "chrono_mesh_builder": chrono_repo / "quick_support_demo" / "chrono_demo" / "difficult_terrain.py",
        "chrono_world_builder": chrono_repo / "quick_support_demo" / "chrono_demo" / "build_world.py",
        "chrono_heightmap_checker": chrono_repo / "check_scm_initial_heightmap.py",
        "chrono_config_loader": chrono_repo / "quick_support_demo" / "config.py",
        "chrono_demo_config": chrono_repo / "quick_support_demo" / "configs" / "demo.yaml",
        "chrono_world_config": chrono_repo / "quick_support_demo" / "configs" / "world.yaml",
        "chrono_terrain_config": chrono_repo / "quick_support_demo" / "configs" / "terrain.yaml",
        "newton_preparation": SCRIPT_DIR / "run_newton_prepared_bed.py",
        "newton_response": SCRIPT_DIR / "run_newton_cylinder_diagnostic.py",
        "newton_contract": SCRIPT_DIR / "newton_contract.py",
        "newton_base_config": fresh.repo_path(contract["newton"]["base_config"]),
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing screening sources: {missing}")
    return paths


def require_json_probe(output: str, label: str) -> dict[str, Any]:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"{label} environment probe returned no output")
    try:
        value = json.loads(lines[-1])
    except json.JSONDecodeError as error:
        raise RuntimeError(f"{label} environment probe did not return JSON: {output}") from error
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} environment probe returned a non-object")
    return value


def build_screening_plan(
    contract_path: Path, contract: dict[str, Any]
) -> dict[str, Any]:
    dataset_path = frozen_dataset_plan(contract)
    if not dataset_path.is_file():
        raise RuntimeError("frozen Phase 1 dataset plan is missing")
    dataset_plan = json.loads(dataset_path.read_text(encoding="utf-8"))
    if dataset_plan.get("contract_sha256") != fresh.sha256_file(contract_path):
        raise RuntimeError("dataset plan does not match the Phase 1 contract")
    sources = source_paths(contract)
    chrono_repo = fresh.repo_path(contract["chrono"]["repo"])
    chrono_probe = [
        *(str(value) for value in contract["chrono"]["command"]),
        "-c",
        (
            "import json,platform; import pychrono; import pychrono.vehicle; "
            "print(json.dumps({'python':platform.python_version(),"
            "'pychrono':getattr(pychrono,'__version__','unknown'),"
            "'vehicle_binding':True}))"
        ),
    ]
    newton_probe = [
        str(Path(contract["newton"]["python"]).resolve()),
        "-c",
        (
            "import json,platform,numpy,warp,newton; "
            "print(json.dumps({'python':platform.python_version(),"
            "'numpy':numpy.__version__,'warp':warp.__version__,"
            "'newton':getattr(newton,'__version__','unknown')}))"
        ),
    ]
    chrono_environment = require_json_probe(
        fresh.command_output(chrono_probe, chrono_repo), "Chrono"
    )
    if chrono_environment.get("vehicle_binding") is not True:
        raise RuntimeError("Chrono environment lacks the required vehicle binding")
    newton_environment = require_json_probe(
        fresh.command_output(newton_probe, REPO_ROOT), "Newton"
    )
    gpu_environment = fresh.command_output(
        [
            "nvidia-smi",
            "--query-gpu=name,uuid,driver_version",
            "--format=csv,noheader",
        ],
        REPO_ROOT,
    )
    if not gpu_environment or "failed" in gpu_environment.lower():
        raise RuntimeError(f"GPU environment probe failed: {gpu_environment}")
    return {
        "schema_version": 1,
        "phase_id": contract["phase_id"],
        "status": "screening_not_started",
        "contract": str(contract_path),
        "contract_sha256": fresh.sha256_file(contract_path),
        "dataset_plan": str(dataset_path),
        "dataset_plan_sha256": fresh.sha256_file(dataset_path),
        "episode_manifest_sha256": dataset_plan["episode_manifest_sha256"],
        "test_lock_sha256": dataset_plan["test_lock_sha256"],
        "source_sha256": {
            name: fresh.sha256_file(path) for name, path in sources.items()
        },
        "thread_environment": contract["chrono"]["thread_environment"],
        "environment_probes": {
            "chrono": chrono_environment,
            "newton": newton_environment,
            "gpu": gpu_environment,
        },
        "repositories": {
            "tera_splat": {
                "revision": fresh.command_output(["git", "rev-parse", "HEAD"], REPO_ROOT),
                "status_short": fresh.command_output(["git", "status", "--short"], REPO_ROOT).splitlines(),
            },
            "tera_splat_sim": {
                "revision": fresh.command_output(
                    ["git", "rev-parse", "HEAD"], fresh.repo_path(contract["chrono"]["repo"])
                ),
                "status_short": fresh.command_output(
                    ["git", "status", "--short"], fresh.repo_path(contract["chrono"]["repo"])
                ).splitlines(),
            },
        },
        "surface_cases": dataset_plan["screening"]["surface_cases"],
        "material_cases": dataset_plan["screening"]["material_cases"],
        "maximum_scm_roundtrip_error_m": 1.0e-5,
        "bulk_dataset_permitted": False,
    }


def write_screening_plan(contract_path: Path, contract: dict[str, Any]) -> dict[str, Any]:
    plan = build_screening_plan(contract_path, contract)
    path = screen_plan_path(contract)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        keys = (
            "contract_sha256",
            "dataset_plan_sha256",
            "episode_manifest_sha256",
            "test_lock_sha256",
            "source_sha256",
            "environment_probes",
        )
        if any(existing.get(key) != plan.get(key) for key in keys):
            raise RuntimeError(f"refusing to replace a different screening plan: {path}")
        return existing
    fresh.write_json(path, plan)
    return plan


def load_screening_plan(contract_path: Path, contract: dict[str, Any]) -> dict[str, Any]:
    path = screen_plan_path(contract)
    if not path.is_file():
        raise RuntimeError("screening plan is missing; run --stage plan first")
    plan = json.loads(path.read_text(encoding="utf-8"))
    if fresh.sha256_file(contract_path) != plan["contract_sha256"]:
        raise RuntimeError("Phase 1 contract changed after screening-plan freeze")
    if fresh.sha256_file(frozen_dataset_plan(contract)) != plan["dataset_plan_sha256"]:
        raise RuntimeError("frozen dataset plan changed after screening-plan freeze")
    for name, path_value in source_paths(contract).items():
        if fresh.sha256_file(path_value) != plan["source_sha256"][name]:
            raise RuntimeError(f"screening source changed after freeze: {name}")
    current = build_screening_plan(contract_path, contract)
    if current["environment_probes"] != plan["environment_probes"]:
        raise RuntimeError("screening software or GPU environment changed after freeze")
    return plan


def surface_dir(contract: dict[str, Any], seed: int) -> Path:
    return output_root(contract) / "surfaces" / f"surface_{seed}"


def qualify_surface(
    contract: dict[str, Any], plan: dict[str, Any], case: dict[str, Any]
) -> dict[str, Any]:
    seed = int(case["initial_surface_seed"])
    root = surface_dir(contract, seed)
    heightmap_path = root / "initial_heightmap_m.npy"
    generator_path = root / "generator_summary.json"
    native_dir = root / "chrono_scm_roundtrip"
    if heightmap_path.is_file() and generator_path.is_file():
        heightmap = np.load(heightmap_path, allow_pickle=False)
        generated = json.loads(generator_path.read_text(encoding="utf-8"))
        if array_sha256(heightmap) != generated["metrics"]["array_sha256"]:
            raise RuntimeError(f"stored surface hash mismatch for seed {seed}")
    elif root.exists():
        raise RuntimeError(f"refusing incomplete surface directory: {root}")
    else:
        heightmap, generated = generate_surface(seed, limits_from_contract(contract))
        root.mkdir(parents=True, exist_ok=False)
        np.save(heightmap_path, heightmap)
        fresh.write_json(generator_path, generated)

    if not (native_dir / "summary.json").is_file():
        if native_dir.exists():
            raise RuntimeError(f"refusing incomplete SCM round-trip directory: {native_dir}")
        chrono_cfg = contract["chrono"]
        varied = chrono_cfg["soil_parameters"]["varied"]
        command = [
            *(str(value) for value in chrono_cfg["command"]),
            str(fresh.repo_path(chrono_cfg["repo"]) / "check_scm_initial_heightmap.py"),
            "--heightmap-npy", str(heightmap_path),
            "--output-dir", str(native_dir),
            "--scm-grid-spacing-m", str(chrono_cfg["scm_grid_spacing_m"]),
            "--scm-pit-size-m", *(str(value) for value in chrono_cfg["scm_pit_size_m"]),
            "--bekker-kphi", str(varied["bekker_kphi"]["reference"]),
            "--mohr-friction-deg", str(varied["mohr_friction_deg"]["reference"]),
            "--maximum-roundtrip-error-m", str(plan["maximum_scm_roundtrip_error_m"]),
        ]
        fresh.run_logged(
            command,
            root / "chrono_scm_roundtrip.log",
            fresh.repo_path(chrono_cfg["repo"]),
            chrono_cfg["thread_environment"],
        )
    native = json.loads((native_dir / "summary.json").read_text(encoding="utf-8"))
    checks = {
        "generator": bool(generated["qualified"]),
        "native_scm": native["status"] == "passed" and all(native["checks"].values()),
        "identity": native["requested_array_sha256"] == generated["metrics"]["array_sha256"],
    }
    result = {
        "schema_version": 1,
        "case_id": case["case_id"],
        "seed": seed,
        "partition": case["partition"],
        "input_sha256": case["input_sha256"],
        "qualified": all(checks.values()),
        "checks": checks,
        "generator": generated,
        "chrono_scm_roundtrip": native,
    }
    fresh.write_json(root / "qualification_summary.json", result)
    return result


def material_case(contract: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    action = contract["action_domain"]
    force = float(raw["normal_force_n"])
    return {
        **raw,
        "equivalent_mass_kg": force / float(action["gravity_mps2"]),
        "radius_m": float(action["radius_m"]),
        "height_m": float(action["height_m"]),
    }


def selected_material_cases(
    contract: dict[str, Any], plan: dict[str, Any], requested: list[str]
) -> list[dict[str, Any]]:
    cases = [material_case(contract, case) for case in plan["material_cases"]]
    by_id = {case["case_id"]: case for case in cases}
    unknown = sorted(set(requested) - set(by_id))
    if unknown:
        raise ValueError(f"unknown material screening cases: {unknown}")
    return [by_id[name] for name in requested] if requested else cases


def material_root(contract: dict[str, Any], case_id: str) -> Path:
    return output_root(contract) / "material" / case_id


def chrono_episode(contract: dict[str, Any], case_id: str) -> Path:
    return chrono_root(contract) / case_id


def chrono_result(contract: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    episode = chrono_episode(contract, case["case_id"])
    manifest_path = episode / "manifest.yaml"
    if not manifest_path.is_file():
        return {"complete": False, "accepted": False, "episode": str(episode)}
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    action = json.loads((episode / manifest["action"]).read_text(encoding="utf-8"))
    initial = np.load(episode / manifest["states"]["initial"], allow_pickle=False)
    source = json.loads(
        (surface_dir(contract, int(case["initial_surface_seed"])) / "generator_summary.json").read_text(encoding="utf-8")
    )
    soil = manifest["chrono"]["soil_parameters"]
    surface = manifest["initial_surface"]
    valid_name = str(manifest["heightmap"]["valid_mask"]).split(";", 1)[0].strip()
    valid = np.load(episode / valid_name, allow_pickle=False).astype(bool)
    states = [
        np.load(episode / manifest["states"][name], allow_pickle=False)
        for name in ("initial", "loaded", "residual")
    ]
    checks = {
        "episode_id": action["episode_id"] == case["case_id"],
        "mass": math.isclose(float(action["mass_kg"]), float(case["equivalent_mass_kg"])),
        "position": bool(np.allclose(action["center_xy_m"], case["center_xy_m"], atol=1e-12)),
        "radius": math.isclose(float(action["radius_m"]), float(case["radius_m"])),
        "soil_kphi": math.isclose(float(soil["bekker_kphi"]), float(case["bekker_kphi"])),
        "soil_friction": math.isclose(float(soil["mohr_friction_deg"]), float(case["mohr_friction_deg"])),
        "initial_surface": surface["requested_array_sha256"] == source["metrics"]["array_sha256"],
        "initial_roundtrip": float(surface["sampled_max_abs_error_m"]) <= 1.0e-5,
        "loading_accepted": bool(manifest["chrono"]["loading_convergence"]["accepted"]),
        "finite_valid_surface": all(np.isfinite(value[valid]).all() for value in states),
        "initial_state_loaded": array_sha256(initial) == surface["sampled_array_sha256"],
    }
    return {
        "complete": True,
        "accepted": all(checks.values()),
        "episode": str(episode.resolve()),
        "checks": checks,
        "loaded_time_s": float(manifest["chrono"]["loading_convergence"]["final_sample_time_s"]),
        "valid_cells": int(np.count_nonzero(valid)),
    }


def run_chrono(contract: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    existing = chrono_result(contract, case)
    if existing["complete"]:
        return existing
    episode = chrono_episode(contract, case["case_id"])
    if episode.exists():
        raise RuntimeError(f"refusing incomplete Chrono screening directory: {episode}")
    cfg = contract["chrono"]
    source = surface_dir(contract, int(case["initial_surface_seed"])) / "initial_heightmap_m.npy"
    if not source.is_file():
        raise RuntimeError("surface qualification must run before material screening")
    command = [
        *(str(value) for value in cfg["command"]),
        str(fresh.repo_path(cfg["repo"]) / "run_cylinder_episode.py"),
        "--episode-id", case["case_id"],
        "--mass-kg", str(case["equivalent_mass_kg"]),
        "--xy", *(str(value) for value in case["center_xy_m"]),
        "--radius-m", str(case["radius_m"]),
        "--height-m", str(case["height_m"]),
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
        "--bekker-kphi", str(case["bekker_kphi"]),
        "--mohr-friction-deg", str(case["mohr_friction_deg"]),
        "--output-dir", str(episode),
    ]
    if cfg["vertical_guide"]:
        command.append("--vertical-guide")
    fresh.run_logged(
        command,
        material_root(contract, case["case_id"]) / "logs" / "chrono.log",
        fresh.repo_path(cfg["repo"]),
        cfg["thread_environment"],
    )
    result = chrono_result(contract, case)
    if not result["accepted"]:
        raise RuntimeError(f"Chrono material screen rejected: {case['case_id']}")
    return result


def bed_dir(contract: dict[str, Any], case_id: str) -> Path:
    return material_root(contract, case_id) / "metric_bed"


def build_bed(contract: dict[str, Any], case: dict[str, Any]) -> Path:
    if not chrono_result(contract, case).get("accepted"):
        raise RuntimeError(f"accepted Chrono screen required before bed: {case['case_id']}")
    output = bed_dir(contract, case["case_id"])
    expected = (output / "particles_initial_mpm.ply", output / "ground_plane_metadata.json")
    if all(path.is_file() for path in expected):
        return output
    if output.exists():
        raise RuntimeError(f"refusing incomplete metric-bed directory: {output}")
    manifest, _action, initial, _valid = load_episode(chrono_episode(contract, case["case_id"]))
    cfg = contract["newton"]["metric_bed_source"]
    write_metric_bed(output, initial, manifest, float(cfg["bed_depth_m"]), float(cfg["particle_spacing_m"]))
    return output


def response_dir(contract: dict[str, Any], case_id: str) -> Path:
    return material_root(contract, case_id) / "response"


def run_newton(
    contract: dict[str, Any], case: dict[str, Any], python_override: Path | None, device_override: str | None
) -> Path:
    bed = build_bed(contract, case)
    root = material_root(contract, case["case_id"])
    response = response_dir(contract, case["case_id"])
    if (response / "newton_cylinder_manifest.json").is_file():
        return response
    if response.exists():
        raise RuntimeError(f"refusing incomplete Newton response: {response}")
    cfg = contract["newton"]
    python = (python_override or Path(cfg["python"])).resolve()
    device = device_override or cfg["device"]
    preparation = root / "preparation"
    if not (preparation / "newton_prepared_bed_manifest.json").is_file():
        if preparation.exists():
            raise RuntimeError(f"refusing incomplete Newton preparation: {preparation}")
        fresh.run_logged(
            [
                str(python), str(SCRIPT_DIR / "run_newton_prepared_bed.py"),
                "--config", str(fresh.repo_path(cfg["base_config"])),
                "--particles-ply", str(bed / "particles_initial_mpm.ply"),
                "--metadata-json", str(bed / "ground_plane_metadata.json"),
                "--chrono-episode", str(chrono_episode(contract, case["case_id"])),
                "--output-dir", str(preparation), "--device", str(device),
                "--dt-s", str(cfg["selected_dt_s"]),
                "--duration-s", str(cfg["pre_settle_duration_s"]),
                "--required-duration-s", str(cfg["pre_settle_required_duration_s"]),
                "--particle-speed-threshold-mps", str(cfg["particle_speed_threshold_mps"]),
                "--center-crop-half-width-m", "0", "--speed-check-every", "1", "--qualification-run",
            ],
            root / "logs" / "newton_preparation.log", REPO_ROOT,
        )
    fresh.run_logged(
        [
            str(python), str(SCRIPT_DIR / "run_newton_cylinder_diagnostic.py"),
            "--config", str(fresh.repo_path(cfg["base_config"])),
            "--prepared-dir", str(preparation), "--candidate-preparation",
            "--chrono-episode", str(chrono_episode(contract, case["case_id"])),
            "--output-dir", str(response), "--device", str(device),
            "--dt-s", str(cfg["selected_dt_s"]),
            "--pre-settle-duration-s", str(cfg["pre_settle_duration_s"]),
            "--pre-settle-required-duration-s", str(cfg["pre_settle_required_duration_s"]),
            "--particle-speed-threshold-mps", str(cfg["particle_speed_threshold_mps"]),
            "--proxy-iterations", str(cfg["proxy_iterations"]),
            "--rigid-substeps", str(cfg["rigid_substeps"]),
            "--cylinder-friction-coefficient", str(cfg["cylinder_friction_coefficient"]),
            "--cylinder-collider-mode", str(cfg["collider_mode"]),
            "--cylinder-collider-segments", str(cfg["collider_segments"]),
            "--cylinder-collision-guard-m", str(cfg["collision_guard_m"]),
            "--cylinder-collision-bottom-inset-m", "0",
            "--cylinder-projection-threshold-m", str(cfg["projection_threshold_m"]),
        ],
        root / "logs" / "newton_response.log", REPO_ROOT,
    )
    return response


def admission_policy(contract: dict[str, Any]) -> dict[str, Any]:
    inherited = json.loads(
        fresh.repo_path(contract["inheritance"]["phase0_contract"]).read_text(encoding="utf-8")
    )
    return inherited["hierarchical_admission"]


def analyze_material(contract: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    case_id = case["case_id"]
    chrono = chrono_result(contract, case)
    response = response_dir(contract, case_id)
    manifest_path = response / "newton_cylinder_manifest.json"
    if not chrono.get("complete") or not manifest_path.is_file():
        return {"case_id": case_id, "complete": False, "pipeline_usable": False}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    bed_metadata = json.loads((bed_dir(contract, case_id) / "ground_plane_metadata.json").read_text(encoding="utf-8"))
    particle_count = int(bed_metadata["particle_count"])
    penetration = manifest["penetration"]
    inside = int(penetration["max_inside_particle_centers"])
    policy = admission_policy(contract)
    level_1 = policy["level_1_numerical_integrity"]
    level_2 = policy["level_2_interaction_artifact"]
    numerical = {
        "chrono_accepted": bool(chrono["accepted"]),
        "preparation_converged": bool(manifest["preparation"]["convergence_passed"]),
        "finite": bool(manifest["finite"]),
        "guide": bool(manifest["cylinder"]["guide_constraint_passed"]),
        "surface_cells": int(manifest["surface"]["valid_cells"]) >= int(level_1["min_surface_valid_cells"]),
        "initial_support": float(manifest["surface"]["initial_match"]["valid_fraction"]) >= float(level_1["min_initial_surface_valid_fraction"]),
    }
    spacing = float(contract["newton"]["metric_bed_source"]["particle_spacing_m"])
    gross_depth = spacing * float(level_2["gross_penetration_fraction_of_particle_spacing"])
    inside_fraction = float(inside / particle_count)
    interaction = {
        "within_gross_depth": float(penetration["max_center_penetration_m"]) <= gross_depth,
        "within_gross_affected_fraction": inside_fraction <= float(level_2["gross_inside_particle_fraction"]),
    }
    geometry = phase0_matrix.local_geometry_metrics(
        chrono_episode(contract, case_id), response, case
    )
    result = {
        "schema_version": 1,
        "case_id": case_id,
        "complete": True,
        "pipeline_usable": all(numerical.values()) and all(interaction.values()),
        "strict_mechanics_qualified": bool(manifest.get("mechanics_qualified")),
        "numerical_checks": numerical,
        "interaction_artifact_checks": interaction,
        "interaction_observed": {
            "particle_count": particle_count,
            "max_inside_particle_centers": inside,
            "max_inside_particle_fraction": inside_fraction,
            "max_center_penetration_m": float(penetration["max_center_penetration_m"]),
            "gross_depth_limit_m": gross_depth,
        },
        "geometry": geometry,
        "artifacts": {
            "chrono_episode": str(chrono_episode(contract, case_id).resolve()),
            "metric_bed": str(bed_dir(contract, case_id).resolve()),
            "newton_response": str(response.resolve()),
        },
    }
    fresh.write_json(material_root(contract, case_id) / "case_summary.json", result)
    return result


def summarize(contract: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    surfaces = []
    for case in plan["surface_cases"]:
        path = surface_dir(contract, int(case["initial_surface_seed"])) / "qualification_summary.json"
        surfaces.append(json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"case_id": case["case_id"], "qualified": False})
    materials = [
        analyze_material(contract, material_case(contract, case))
        for case in plan["material_cases"]
    ]
    surface_pass = len(surfaces) == 6 and all(item["qualified"] for item in surfaces)
    material_pass = len(materials) == 5 and all(item["complete"] and item["pipeline_usable"] for item in materials)
    summary = {
        "schema_version": 1,
        "phase_id": contract["phase_id"],
        "status": "passed" if surface_pass and material_pass else "incomplete_or_failed",
        "surface_screen_passed": surface_pass,
        "material_screen_passed": material_pass,
        "bulk_dataset_permitted": surface_pass and material_pass,
        "surfaces": {item["case_id"]: item for item in surfaces},
        "materials": {item["case_id"]: item for item in materials},
    }
    fresh.write_json(output_root(contract) / "screening_summary.json", summary)
    return summary


def main() -> None:
    args = parse_args()
    contract_path = args.contract.resolve()
    contract = load_contract(contract_path)
    if args.stage == "plan":
        plan = write_screening_plan(contract_path, contract)
        print(json.dumps({"screening_plan": str(screen_plan_path(contract)), "surface_cases": len(plan["surface_cases"]), "material_cases": len(plan["material_cases"])}, indent=2))
        return
    plan = load_screening_plan(contract_path, contract)
    cases = selected_material_cases(contract, plan, args.case)
    if args.stage in ("surfaces", "all"):
        for surface_case in plan["surface_cases"]:
            qualify_surface(contract, plan, surface_case)
    for case in cases:
        if args.stage in ("chrono", "all"):
            run_chrono(contract, case)
        if args.stage in ("bed", "all"):
            build_bed(contract, case)
        if args.stage in ("newton", "all"):
            run_newton(contract, case, args.newton_python, args.device)
        if args.stage in ("analyze", "all"):
            analyze_material(contract, case)
    summary = summarize(contract, plan)
    print(json.dumps({key: summary[key] for key in ("status", "surface_screen_passed", "material_screen_passed", "bulk_dataset_permitted")}, indent=2))


if __name__ == "__main__":
    main()

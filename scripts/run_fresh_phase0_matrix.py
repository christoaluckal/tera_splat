#!/usr/bin/env python3
"""Run the fresh Phase 0 action matrix progressively with local geometry metrics."""

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

import run_fresh_phase0_repeatability as fresh
from chrono_episode_bridge import load_episode, write_metric_bed


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = REPO_ROOT / "configs" / "static_proxy_hierarchical_v3_20261017.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument(
        "--stage",
        choices=("plan", "chrono", "bed", "newton", "analyze", "all"),
        default="plan",
    )
    parser.add_argument(
        "--rung",
        choices=("spatial31", "spatial46", "spatial61", "full"),
        default="spatial31",
        help="Progressive action slice. Repeated --case values override this selection.",
    )
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--chrono-python", type=Path)
    parser.add_argument("--newton-python", type=Path)
    parser.add_argument("--device")
    return parser.parse_args()


def matrix_roots(contract: dict[str, Any]) -> tuple[Path, Path, Path]:
    chrono_root, newton_root, _repeat_root = fresh.roots(contract)
    return chrono_root / "matrix", newton_root / "matrix", newton_root


def rung_cases(campaign_cases: list[dict[str, Any]]) -> dict[str, list[str]]:
    by_force = {
        "spatial31": "f031n",
        "spatial46": "f046n",
        "spatial61": "f061n",
    }
    result = {
        name: [case["case_id"] for case in campaign_cases if case["case_id"].endswith(suffix)]
        for name, suffix in by_force.items()
    }
    result["full"] = [case["case_id"] for case in campaign_cases]
    return result


def select_cases(
    campaign_cases: list[dict[str, Any]], rung: str, requested: list[str]
) -> list[dict[str, Any]]:
    by_id = {case["case_id"]: case for case in campaign_cases}
    ids = requested or rung_cases(campaign_cases)[rung]
    unknown = sorted(set(ids) - set(by_id))
    if unknown:
        raise ValueError(f"unknown matrix case ids: {unknown}")
    if len(ids) != len(set(ids)):
        raise ValueError("matrix case selection contains duplicates")
    return [by_id[case_id] for case_id in ids]


def require_sentinel(contract: dict[str, Any]) -> dict[str, Any]:
    _chrono_root, _newton_root, repeat_root = fresh.roots(contract)
    path = repeat_root / "repeatability_summary.json"
    if not path.is_file():
        raise RuntimeError("fresh sentinel summary is missing")
    summary = json.loads(path.read_text(encoding="utf-8"))
    if not bool(summary.get("matrix_expansion_permitted")):
        raise RuntimeError("fresh sentinel is incomplete or structurally unusable")
    return summary


def write_matrix_plan(
    contract_path: Path, contract: dict[str, Any], campaign_cases: list[dict[str, Any]]
) -> dict[str, Any]:
    base_plan = fresh.load_plan(contract)
    fresh.assert_source_freeze(contract_path, contract, base_plan)
    sentinel_summary = require_sentinel(contract)
    _chrono_matrix, matrix_root, newton_root = matrix_roots(contract)
    existing_cases = matrix_root / "cases"
    if existing_cases.exists() and any(existing_cases.iterdir()):
        raise RuntimeError("refusing to replace matrix plan after case execution began")
    plan = {
        "schema_version": 1,
        "qualification_id": contract["qualification_id"],
        "status": "matrix_not_started",
        "prior_outputs_admissible": False,
        "contract": str(contract_path.resolve()),
        "contract_sha256": fresh.sha256_file(contract_path.resolve()),
        "base_campaign_plan": str((newton_root / "campaign_plan.json").resolve()),
        "base_campaign_plan_sha256": fresh.sha256_file(newton_root / "campaign_plan.json"),
        "sentinel_summary": str(
            (fresh.roots(contract)[2] / "repeatability_summary.json").resolve()
        ),
        "sentinel_summary_sha256": fresh.sha256_file(
            fresh.roots(contract)[2] / "repeatability_summary.json"
        ),
        "matrix_runner": str(Path(__file__).resolve()),
        "matrix_runner_sha256": fresh.sha256_file(Path(__file__).resolve()),
        "cases": campaign_cases,
        "episode_split": contract["episode_split"],
        "rungs": rung_cases(campaign_cases),
        "sentinel_status": sentinel_summary["status"],
    }
    fresh.write_json(matrix_root / "matrix_plan.json", plan)
    return plan


def load_matrix_plan(contract: dict[str, Any]) -> dict[str, Any]:
    _chrono_matrix, matrix_root, _newton_root = matrix_roots(contract)
    path = matrix_root / "matrix_plan.json"
    if not path.is_file():
        raise RuntimeError("matrix plan is missing; run --stage plan first")
    return json.loads(path.read_text(encoding="utf-8"))


def assert_matrix_freeze(
    contract_path: Path, contract: dict[str, Any], plan: dict[str, Any]
) -> None:
    base_plan = fresh.load_plan(contract)
    fresh.assert_source_freeze(contract_path, contract, base_plan)
    if fresh.sha256_file(contract_path.resolve()) != plan["contract_sha256"]:
        raise RuntimeError("matrix contract changed after plan freeze")
    if fresh.sha256_file(Path(__file__).resolve()) != plan["matrix_runner_sha256"]:
        raise RuntimeError("matrix runner changed after plan freeze")
    sentinel_path = Path(plan["sentinel_summary"])
    if fresh.sha256_file(sentinel_path) != plan["sentinel_summary_sha256"]:
        raise RuntimeError("sentinel summary changed after matrix plan freeze")


def chrono_case_dir(contract: dict[str, Any], case_id: str) -> Path:
    chrono_matrix, _matrix_root, _newton_root = matrix_roots(contract)
    return chrono_matrix / case_id


def matrix_case_dir(contract: dict[str, Any], case_id: str) -> Path:
    _chrono_matrix, matrix_root, _newton_root = matrix_roots(contract)
    return matrix_root / "cases" / case_id


def split_for_case(contract: dict[str, Any], case_id: str) -> str:
    for partition in ("train", "validation", "test"):
        if case_id in contract["episode_split"][partition]:
            return partition
    raise ValueError(f"case is not assigned to the frozen split: {case_id}")


def chrono_case_result(contract: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    episode = chrono_case_dir(contract, case["case_id"])
    manifest_path = episode / "manifest.yaml"
    if not manifest_path.is_file():
        return {"complete": False, "accepted": False, "episode": str(episode)}
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    loading = manifest["chrono"]["loading_convergence"]
    action = json.loads((episode / manifest["action"]).read_text(encoding="utf-8"))
    states = {
        state: np.load(episode / manifest["states"][state], allow_pickle=False)
        for state in ("initial", "loaded", "residual")
    }
    mask_name = str(manifest["heightmap"]["valid_mask"]).split(";", 1)[0].strip()
    valid = np.load(episode / mask_name, allow_pickle=False).astype(bool)
    finite = all(np.isfinite(value[valid]).all() for value in states.values())
    checks = {
        "episode_id": action["episode_id"] == case["case_id"],
        "mass": math.isclose(float(action["mass_kg"]), float(case["equivalent_mass_kg"])),
        "position": bool(np.allclose(action["center_xy_m"], case["center_xy_m"], atol=1e-12)),
        "radius": math.isclose(float(action["radius_m"]), float(case["radius_m"])),
        "loading_accepted": bool(loading["accepted"]),
        "finite_valid_surface": bool(finite),
    }
    return {
        "complete": True,
        "accepted": all(checks.values()),
        "episode": str(episode.resolve()),
        "checks": checks,
        "loaded_time_s": float(loading["final_sample_time_s"]),
        "valid_cells": int(np.count_nonzero(valid)),
    }


def run_chrono_case(
    contract_path: Path,
    contract: dict[str, Any],
    plan: dict[str, Any],
    case: dict[str, Any],
    chrono_python: Path | None,
) -> dict[str, Any]:
    assert_matrix_freeze(contract_path, contract, plan)
    existing = chrono_case_result(contract, case)
    if existing["complete"]:
        return existing
    episode = chrono_case_dir(contract, case["case_id"])
    if episode.exists():
        raise RuntimeError(f"refusing incomplete Chrono matrix directory: {episode}")
    chrono_repo = fresh.repo_path(contract["chrono"]["repo"])
    prefix = (
        [str(chrono_python.resolve())]
        if chrono_python is not None
        else [str(value) for value in contract["chrono"]["command"]]
    )
    cfg = contract["chrono"]
    command = [
        *prefix,
        str(chrono_repo / "run_cylinder_episode.py"),
        "--episode-id", str(case["case_id"]),
        "--mass-kg", str(case["equivalent_mass_kg"]),
        "--xy", *(str(value) for value in case["center_xy_m"]),
        "--radius-m", str(case["radius_m"]),
        "--height-m", str(case["height_m"]),
        "--start-clearance-m", str(contract["action"]["start_clearance_m"]),
        "--timestep-s", str(cfg["timestep_s"]),
        "--scm-grid-spacing-m", str(cfg["scm_grid_spacing_m"]),
        "--scm-pit-size-m", *(str(value) for value in cfg["scm_pit_size_m"]),
        "--max-loading-time-s", str(cfg["max_loading_time_s"]),
        "--min-loading-time-s", str(cfg["min_loading_time_s"]),
        "--loading-linear-speed-threshold-mps", str(cfg["loading_linear_speed_threshold_mps"]),
        "--loading-angular-speed-threshold-radps", str(cfg["loading_angular_speed_threshold_radps"]),
        "--loading-hold-time-s", str(cfg["loading_hold_time_s"]),
        "--residual-settle-s", str(cfg["residual_duration_s"]),
        "--output-dir", str(episode),
    ]
    if bool(cfg["vertical_guide"]):
        command.append("--vertical-guide")
    fresh.run_logged(
        command,
        matrix_case_dir(contract, case["case_id"]) / "logs" / "chrono.log",
        chrono_repo,
        cfg["thread_environment"],
    )
    result = chrono_case_result(contract, case)
    if not result["accepted"]:
        raise RuntimeError(f"fresh Chrono matrix case is unusable: {case['case_id']}")
    return result


def bed_dir(contract: dict[str, Any], case_id: str) -> Path:
    return matrix_case_dir(contract, case_id) / "metric_bed"


def build_case_bed(
    contract_path: Path,
    contract: dict[str, Any],
    plan: dict[str, Any],
    case: dict[str, Any],
) -> Path:
    assert_matrix_freeze(contract_path, contract, plan)
    chrono = chrono_case_result(contract, case)
    if not chrono.get("accepted"):
        raise RuntimeError(f"accepted fresh Chrono case required before bed: {case['case_id']}")
    output = bed_dir(contract, case["case_id"])
    expected = (output / "particles_initial_mpm.ply", output / "ground_plane_metadata.json")
    if all(path.is_file() for path in expected):
        return output
    if output.exists():
        raise RuntimeError(f"refusing incomplete metric-bed directory: {output}")
    manifest, _action, initial, _valid = load_episode(chrono_case_dir(contract, case["case_id"]))
    cfg = contract["newton"]["metric_bed_source"]
    write_metric_bed(
        output,
        initial,
        manifest,
        float(cfg["bed_depth_m"]),
        float(cfg["particle_spacing_m"]),
    )
    return output


def response_dir(contract: dict[str, Any], case_id: str) -> Path:
    return matrix_case_dir(contract, case_id) / "response"


def run_newton_case(
    contract_path: Path,
    contract: dict[str, Any],
    plan: dict[str, Any],
    case: dict[str, Any],
    newton_python: Path | None,
    device_override: str | None,
) -> Path:
    assert_matrix_freeze(contract_path, contract, plan)
    bed = build_case_bed(contract_path, contract, plan, case)
    root = matrix_case_dir(contract, case["case_id"])
    response = response_dir(contract, case["case_id"])
    manifest_path = response / "newton_cylinder_manifest.json"
    if manifest_path.is_file():
        return response
    if response.exists():
        raise RuntimeError(f"refusing incomplete Newton response directory: {response}")
    cfg = contract["newton"]
    python = (newton_python or Path(cfg["python"])).resolve()
    device = device_override or str(cfg["device"])
    preparation = root / "preparation"
    preparation_manifest = preparation / "newton_prepared_bed_manifest.json"
    if not preparation_manifest.is_file():
        if preparation.exists():
            raise RuntimeError(f"refusing incomplete Newton preparation: {preparation}")
        fresh.run_logged(
            [
                str(python), str(REPO_ROOT / "scripts" / "run_newton_prepared_bed.py"),
                "--config", str(fresh.repo_path(cfg["base_config"])),
                "--particles-ply", str(bed / "particles_initial_mpm.ply"),
                "--metadata-json", str(bed / "ground_plane_metadata.json"),
                "--chrono-episode", str(chrono_case_dir(contract, case["case_id"])),
                "--output-dir", str(preparation),
                "--device", device,
                "--dt-s", str(cfg["selected_dt_s"]),
                "--duration-s", str(cfg["pre_settle_duration_s"]),
                "--required-duration-s", str(cfg["pre_settle_required_duration_s"]),
                "--particle-speed-threshold-mps", str(cfg["particle_speed_threshold_mps"]),
                "--center-crop-half-width-m", "0",
                "--speed-check-every", "1",
                "--qualification-run",
            ],
            root / "logs" / "newton_preparation.log",
            REPO_ROOT,
        )
    fresh.run_logged(
        [
            str(python), str(REPO_ROOT / "scripts" / "run_newton_cylinder_diagnostic.py"),
            "--config", str(fresh.repo_path(cfg["base_config"])),
            "--prepared-dir", str(preparation),
            "--candidate-preparation",
            "--chrono-episode", str(chrono_case_dir(contract, case["case_id"])),
            "--output-dir", str(response),
            "--device", device,
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
        root / "logs" / "newton_response.log",
        REPO_ROOT,
    )
    return response


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
        "no_deformation_rmse_m": float(np.sqrt(baseline_mse)),
        "mse_skill_vs_no_deformation": (
            float(1.0 - mse / baseline_mse) if baseline_mse > 0.0 else None
        ),
    }


def local_geometry_metrics(
    chrono_episode: Path, newton_response: Path, case: dict[str, Any]
) -> dict[str, Any]:
    manifest = yaml.safe_load((chrono_episode / "manifest.yaml").read_text(encoding="utf-8"))
    initial = np.load(chrono_episode / manifest["states"]["initial"], allow_pickle=False)
    chrono_valid_name = str(manifest["heightmap"]["valid_mask"]).split(";", 1)[0].strip()
    valid = np.load(chrono_episode / chrono_valid_name, allow_pickle=False).astype(bool)
    valid &= np.load(newton_response / "valid_heightmap_mask.npy", allow_pickle=False).astype(bool)
    rows, columns = initial.shape
    spacing = float(manifest["heightmap"]["spacing_m"])
    origin_x, origin_y = (float(value) for value in manifest["heightmap"]["origin_xy_m"])
    grid_x, grid_y = np.meshgrid(
        origin_x + np.arange(columns) * spacing,
        origin_y + np.arange(rows) * spacing,
    )
    radius = float(case["radius_m"])
    center_x, center_y = (float(value) for value in case["center_xy_m"])
    distance_sq = np.square(grid_x - center_x) + np.square(grid_y - center_y)
    masks = {
        "footprint": distance_sq <= radius**2 + 1.0e-12,
        "local_2r": distance_sq <= (2.0 * radius) ** 2 + 1.0e-12,
        "all_valid_bed": np.ones_like(valid, dtype=bool),
    }
    result: dict[str, Any] = {}
    for state in ("loaded", "residual"):
        target = np.load(chrono_episode / manifest["states"][state], allow_pickle=False)
        prediction = np.load(newton_response / f"{state}_heightmap_m.npy", allow_pickle=False)
        result[state] = {}
        for name, region in masks.items():
            mask = valid & region & np.isfinite(initial) & np.isfinite(target) & np.isfinite(prediction)
            result[state][name] = {
                "cells": int(np.count_nonzero(mask)),
                **error_metrics(prediction[mask], target[mask], initial[mask]),
            }
    return result


def analyze_case(contract: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    case_id = case["case_id"]
    chrono = chrono_case_result(contract, case)
    response = response_dir(contract, case_id)
    manifest_path = response / "newton_cylinder_manifest.json"
    if not chrono.get("complete") or not manifest_path.is_file():
        return {
            "case_id": case_id,
            "split": split_for_case(contract, case_id),
            "complete": False,
            "pipeline_usable": False,
        }
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    bed_metadata = json.loads(
        (bed_dir(contract, case_id) / "ground_plane_metadata.json").read_text(encoding="utf-8")
    )
    particle_count = int(bed_metadata["particle_count"])
    penetration = manifest["penetration"]
    inside = int(penetration["max_inside_particle_centers"])
    policy = contract["hierarchical_admission"]
    level_1 = policy["level_1_numerical_integrity"]
    level_2 = policy["level_2_interaction_artifact"]
    numerical_checks = {
        "chrono_accepted": bool(chrono["accepted"]),
        "preparation_converged": bool(manifest["preparation"]["convergence_passed"]),
        "finite": bool(manifest["finite"]),
        "guide": bool(manifest["cylinder"]["guide_constraint_passed"]),
        "surface_cells": int(manifest["surface"]["valid_cells"])
        >= int(level_1["min_surface_valid_cells"]),
        "initial_support": float(manifest["surface"]["initial_match"]["valid_fraction"])
        >= float(level_1["min_initial_surface_valid_fraction"]),
    }
    spacing = float(contract["newton"]["metric_bed_source"]["particle_spacing_m"])
    gross_depth = spacing * float(level_2["gross_penetration_fraction_of_particle_spacing"])
    inside_fraction = float(inside / particle_count)
    artifact_checks = {
        "within_gross_depth": float(penetration["max_center_penetration_m"]) <= gross_depth,
        "within_gross_affected_fraction": inside_fraction
        <= float(level_2["gross_inside_particle_fraction"]),
    }
    geometry = local_geometry_metrics(chrono_case_dir(contract, case_id), response, case)
    thresholds = policy["level_3_geometric_utility"]
    geometric_checks = {
        f"{state}_{region}_positive_skill": (
            geometry[state][region]["mse_skill_vs_no_deformation"] is not None
            and geometry[state][region]["mse_skill_vs_no_deformation"]
            > float(thresholds[f"min_{state}_{region}_mse_skill"])
        )
        for state in ("loaded", "residual")
        for region in ("footprint", "local_2r")
    }
    pipeline_usable = all(numerical_checks.values()) and all(artifact_checks.values())
    result = {
        "schema_version": 1,
        "case_id": case_id,
        "split": split_for_case(contract, case_id),
        "complete": True,
        "pipeline_usable": pipeline_usable,
        "strict_mechanics_qualified": bool(manifest.get("mechanics_qualified")),
        "contact_artifact": inside > 0,
        "numerical_checks": numerical_checks,
        "interaction_artifact_checks": artifact_checks,
        "interaction_observed": {
            "particle_count": particle_count,
            "max_inside_particle_centers": inside,
            "max_inside_particle_fraction": inside_fraction,
            "max_center_penetration_m": float(penetration["max_center_penetration_m"]),
            "loaded_inside_particle_centers": int(penetration["loaded"]["inside_particle_centers"]),
            "gross_depth_limit_m": gross_depth,
        },
        "geometry": geometry,
        "geometric_checks": geometric_checks,
        "geometric_gate_passed": all(geometric_checks.values()),
        "artifacts": {
            "chrono_episode": str(chrono_case_dir(contract, case_id).resolve()),
            "metric_bed": str(bed_dir(contract, case_id).resolve()),
            "newton_response": str(response.resolve()),
        },
    }
    fresh.write_json(matrix_case_dir(contract, case_id) / "case_summary.json", result)
    return result


def summarize_matrix(contract: dict[str, Any], campaign_cases: list[dict[str, Any]]) -> dict[str, Any]:
    results = [analyze_case(contract, case) for case in campaign_cases]
    by_id = {result["case_id"]: result for result in results}
    rungs = {}
    for name, ids in rung_cases(campaign_cases).items():
        complete = all(by_id[case_id]["complete"] for case_id in ids)
        usable = complete and all(by_id[case_id]["pipeline_usable"] for case_id in ids)
        geometric = usable and all(by_id[case_id].get("geometric_gate_passed", False) for case_id in ids)
        rungs[name] = {
            "case_ids": ids,
            "complete": complete,
            "pipeline_usable": usable,
            "geometric_gate_passed": geometric,
        }
    summary = {
        "schema_version": 1,
        "qualification_id": contract["qualification_id"],
        "prior_outputs_admissible": False,
        "completed_cases": sum(result["complete"] for result in results),
        "usable_cases": sum(result["pipeline_usable"] for result in results),
        "geometric_gate_cases": sum(result.get("geometric_gate_passed", False) for result in results),
        "total_cases": len(results),
        "residual_pilot_permitted": rungs["spatial31"]["pipeline_usable"],
        "phase0_coarse_prior_signal_demonstrated": rungs["spatial31"]["geometric_gate_passed"],
        "rungs": rungs,
        "cases": by_id,
    }
    _chrono_matrix, matrix_root, _newton_root = matrix_roots(contract)
    fresh.write_json(matrix_root / "matrix_summary.json", summary)
    return summary


def main() -> None:
    args = parse_args()
    contract_path = args.contract.resolve()
    contract = fresh.load_contract(contract_path)
    campaign_cases = fresh.cases(contract)
    fresh.validate_split(contract, campaign_cases)
    if args.stage == "plan":
        plan = write_matrix_plan(contract_path, contract, campaign_cases)
        print(json.dumps({"matrix_plan": str(matrix_roots(contract)[1] / "matrix_plan.json"), "rungs": plan["rungs"]}, indent=2))
        return
    plan = load_matrix_plan(contract)
    assert_matrix_freeze(contract_path, contract, plan)
    selected = select_cases(campaign_cases, args.rung, args.case)
    for case in selected:
        if args.stage in ("chrono", "all"):
            run_chrono_case(contract_path, contract, plan, case, args.chrono_python)
        if args.stage in ("bed", "all"):
            build_case_bed(contract_path, contract, plan, case)
        if args.stage in ("newton", "all"):
            run_newton_case(
                contract_path,
                contract,
                plan,
                case,
                args.newton_python,
                args.device,
            )
        if args.stage in ("analyze", "all"):
            analyze_case(contract, case)
    summary = summarize_matrix(contract, campaign_cases)
    print(json.dumps({
        "completed_cases": summary["completed_cases"],
        "usable_cases": summary["usable_cases"],
        "residual_pilot_permitted": summary["residual_pilot_permitted"],
        "spatial31": summary["rungs"]["spatial31"],
    }, indent=2))


if __name__ == "__main__":
    main()

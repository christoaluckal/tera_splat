#!/usr/bin/env python3
"""Recover the six-case successor screen with one qualified common-base prior."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_fresh_phase0_matrix as phase0_matrix
import run_fresh_phase0_repeatability as fresh
import run_phase1_one_action_successor_screen as successor
import run_phase1_screening as screening
from chrono_episode_bridge import load_episode
from phase1_metric_bed import write_common_base_metric_bed


REPO_ROOT = Path(__file__).resolve().parents[1]
RECOVERY_ROOT = (
    REPO_ROOT
    / "outputs"
    / "validity_experiment"
    / "newton"
    / "phase1_one_action_successor_v1"
    / "common_base_recovery_v1"
)
PLAN_PATH = RECOVERY_ROOT / "recovery_plan.json"
WORKERS = 2
LOADED_DURATION_S = 0.35
POST_UNLOAD_DURATION_S = 0.25


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage", choices=("plan", "bed", "newton", "analyze", "all"), default="plan"
    )
    parser.add_argument("--workers", type=int, default=WORKERS)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shared_root() -> Path:
    return RECOVERY_ROOT / "shared_newton_prior"


def case_root(case_id: str) -> Path:
    return RECOVERY_ROOT / "cases" / case_id


def response_dir(case_id: str) -> Path:
    return case_root(case_id) / "response"


def inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    proposal, input_plan, operations = successor.load_inputs()
    contract = successor.execution_contract(proposal, operations)
    cases = successor.material_cases(contract, proposal, input_plan, [])
    if len(cases) != 6:
        raise ValueError("common-base recovery requires all six frozen cases")
    return proposal, input_plan, contract, cases


def artifact_paths(
    contract: dict[str, Any], cases: list[dict[str, Any]]
) -> dict[str, Path]:
    paths: dict[str, Path] = {
        "proposal": successor.PROPOSAL_PATH,
        "input_plan": successor.INPUT_PLAN_PATH,
        "operations_contract": successor.OPERATIONS_CONTRACT_PATH,
        "failed_execution_plan": successor.execution_plan_path(contract),
    }
    for case in cases:
        case_id = case["case_id"]
        episode = screening.chrono_episode(contract, case_id)
        manifest_path = episode / "manifest.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        paths[f"{case_id}:chrono_manifest"] = manifest_path
        paths[f"{case_id}:chrono_action"] = episode / manifest["action"]
        paths[f"{case_id}:chrono_initial"] = episode / manifest["states"]["initial"]
        paths[f"{case_id}:failed_preparation"] = (
            screening.material_root(contract, case_id)
            / "preparation"
            / "newton_prepared_bed_manifest.json"
        )
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing recovery inputs: {missing}")
    return paths


def source_paths(contract: dict[str, Any]) -> dict[str, Path]:
    return {
        "recovery_runner": Path(__file__).resolve(),
        "frozen_successor_runner": SCRIPT_DIR / "run_phase1_one_action_successor_screen.py",
        "common_base_builder": SCRIPT_DIR / "phase1_metric_bed.py",
        "phase1_screening": SCRIPT_DIR / "run_phase1_screening.py",
        "phase0_analysis": SCRIPT_DIR / "run_fresh_phase0_matrix.py",
        "chrono_episode_bridge": SCRIPT_DIR / "chrono_episode_bridge.py",
        "particle_io": SCRIPT_DIR / "particle_io.py",
        "newton_preparation": SCRIPT_DIR / "run_newton_prepared_bed.py",
        "newton_response": SCRIPT_DIR / "run_newton_cylinder_diagnostic.py",
        "newton_contract": SCRIPT_DIR / "newton_contract.py",
        "newton_base_config": fresh.repo_path(contract["newton"]["base_config"]),
    }


def environment(contract: dict[str, Any]) -> dict[str, Any]:
    python = str(Path(contract["newton"]["python"]).resolve())
    packages = fresh.command_output(
        [
            python,
            "-c",
            (
                "import json,platform,numpy,warp,newton;"
                "print(json.dumps({'python':platform.python_version(),"
                "'numpy':numpy.__version__,'warp':warp.__version__,"
                "'newton':getattr(newton,'__version__','unknown')}))"
            ),
        ],
        REPO_ROOT,
    )
    gpu = fresh.command_output(
        ["nvidia-smi", "--query-gpu=name,uuid,driver_version", "--format=csv,noheader"],
        REPO_ROOT,
    )
    lines = [line for line in packages.splitlines() if line.strip().startswith("{")]
    if not lines or not gpu or "failed" in gpu.lower():
        raise RuntimeError("Newton or GPU environment probe failed")
    return {"packages": json.loads(lines[-1]), "device": gpu}


def build_plan() -> dict[str, Any]:
    proposal, input_plan, contract, cases = inputs()
    artifacts = artifact_paths(contract, cases)
    sources = source_paths(contract)
    missing_sources = [str(path) for path in sources.values() if not path.is_file()]
    if missing_sources:
        raise FileNotFoundError(f"missing recovery sources: {missing_sources}")

    initial_hashes: dict[str, str] = {}
    failed_preparations: dict[str, Any] = {}
    chrono_acceptance: dict[str, Any] = {}
    for case in cases:
        case_id = case["case_id"]
        chrono = successor.successor_chrono_result(contract, proposal, case)
        if not chrono.get("accepted"):
            raise RuntimeError(f"Chrono case is not accepted: {case_id}")
        chrono_acceptance[case_id] = chrono
        initial_hashes[case_id] = sha256(artifacts[f"{case_id}:chrono_initial"])
        failed = load_json(artifacts[f"{case_id}:failed_preparation"])
        if failed.get("accepted") is not False or failed.get("status") != "diagnostic_only":
            raise RuntimeError(f"antecedent preparation is not the preserved rejection: {case_id}")
        failed_preparations[case_id] = {
            "manifest_sha256": sha256(artifacts[f"{case_id}:failed_preparation"]),
            "status": failed["status"],
            "accepted": failed["accepted"],
            "surface": failed.get("surface"),
        }
    if len(set(initial_hashes.values())) != 1:
        raise RuntimeError("the six Chrono cases do not share one initial-state identity")

    return {
        "schema_version": 1,
        "identity": "phase1_one_action_successor_common_base_recovery_v1",
        "status": "frozen_before_runtime",
        "captured_by_python": platform.python_version(),
        "source_sha256": {name: sha256(path) for name, path in sources.items()},
        "input_sha256": {name: sha256(path) for name, path in artifacts.items()},
        "environment": environment(contract),
        "repository": {
            "revision": fresh.command_output(["git", "rev-parse", "HEAD"], REPO_ROOT),
            "branch": fresh.command_output(["git", "branch", "--show-current"], REPO_ROOT),
            "status_short": fresh.command_output(["git", "status", "--short"], REPO_ROOT).splitlines(),
        },
        "case_ids": [case["case_id"] for case in cases],
        "cases": cases,
        "chrono_acceptance": chrono_acceptance,
        "shared_initial_state_sha256": next(iter(initial_hashes.values())),
        "initial_state_sha256_by_case": initial_hashes,
        "antecedent_failed_preparations": failed_preparations,
        "recovery": {
            "preserve_antecedent_failure": True,
            "rerun_chrono": False,
            "builder_mode": "exact_surface_global_vertical_lattice_common_flat_base",
            "nominal_bed_depth_m": 0.1,
            "particle_spacing_m": 0.005,
            "minimum_top_gap_fraction": 0.95,
            "shared_fresh_preparation_count": 1,
            "fresh_response_count": 6,
            "observation_time_mode": "independent_fixed",
            "loaded_duration_s": LOADED_DURATION_S,
            "post_unload_duration_s": POST_UNLOAD_DURATION_S,
            "worker_count": WORKERS,
        },
        "bulk_training_validation_test_or_protected_target_generation_permitted": False,
    }


def write_plan() -> dict[str, Any]:
    plan = build_plan()
    if PLAN_PATH.exists():
        existing = load_json(PLAN_PATH)
        stable = ("source_sha256", "input_sha256", "environment", "case_ids", "recovery")
        if any(existing.get(key) != plan.get(key) for key in stable):
            raise RuntimeError(f"refusing changed recovery plan: {PLAN_PATH}")
        return existing
    fresh.write_json(PLAN_PATH, plan)
    return plan


def load_plan() -> dict[str, Any]:
    if not PLAN_PATH.is_file():
        raise RuntimeError("recovery plan is absent; run --stage plan first")
    frozen = load_json(PLAN_PATH)
    current = build_plan()
    stable = ("source_sha256", "input_sha256", "environment", "case_ids", "recovery")
    changed = [key for key in stable if frozen.get(key) != current.get(key)]
    if changed:
        raise RuntimeError(f"recovery identity changed after freeze: {changed}")
    return frozen


def build_bed(
    contract: dict[str, Any], cases: list[dict[str, Any]], plan: dict[str, Any]
) -> Path:
    output = shared_root() / "metric_bed"
    expected = output / "particles_initial_mpm.ply", output / "ground_plane_metadata.json"
    if all(path.is_file() for path in expected):
        return output
    if output.exists():
        raise RuntimeError(f"refusing incomplete recovery bed: {output}")
    reference = cases[0]
    episode = screening.chrono_episode(contract, reference["case_id"])
    manifest, _action, initial, _valid = load_episode(episode)
    metadata = write_common_base_metric_bed(
        output,
        initial,
        manifest,
        bed_depth_m=0.1,
        particle_spacing_m=0.005,
        minimum_top_gap_fraction=0.95,
    )
    metadata["provenance"] = {
        "recovery_plan_sha256": sha256(PLAN_PATH),
        "reference_chrono_episode": str(episode.resolve()),
        "shared_initial_state_sha256": plan["shared_initial_state_sha256"],
    }
    fresh.write_json(output / "ground_plane_metadata.json", metadata)
    return output


def run_preparation(
    contract: dict[str, Any], cases: list[dict[str, Any]], plan: dict[str, Any]
) -> Path:
    bed = build_bed(contract, cases, plan)
    output = shared_root() / "preparation"
    manifest_path = output / "newton_prepared_bed_manifest.json"
    if not manifest_path.is_file():
        if output.exists():
            raise RuntimeError(f"refusing incomplete recovery preparation: {output}")
        cfg = contract["newton"]
        episode = screening.chrono_episode(contract, cases[0]["case_id"])
        fresh.run_logged(
            [
                str(Path(cfg["python"]).resolve()),
                str(SCRIPT_DIR / "run_newton_prepared_bed.py"),
                "--config", str(fresh.repo_path(cfg["base_config"])),
                "--particles-ply", str(bed / "particles_initial_mpm.ply"),
                "--metadata-json", str(bed / "ground_plane_metadata.json"),
                "--chrono-episode", str(episode),
                "--output-dir", str(output),
                "--device", str(cfg["device"]),
                "--dt-s", str(cfg["selected_dt_s"]),
                "--duration-s", str(cfg["pre_settle_duration_s"]),
                "--required-duration-s", str(cfg["pre_settle_required_duration_s"]),
                "--particle-speed-threshold-mps", str(cfg["particle_speed_threshold_mps"]),
                "--center-crop-half-width-m", "0",
                "--speed-check-every", "1",
                "--qualification-run",
            ],
            shared_root() / "logs" / "newton_preparation.log",
            REPO_ROOT,
        )
    manifest = load_json(manifest_path)
    if not manifest.get("accepted"):
        raise RuntimeError("fresh common-base Newton preparation was not accepted")
    return output


def run_response(
    contract: dict[str, Any], case: dict[str, Any], preparation: Path
) -> Path:
    case_id = case["case_id"]
    output = response_dir(case_id)
    manifest_path = output / "newton_cylinder_manifest.json"
    if manifest_path.is_file():
        return output
    if output.exists():
        raise RuntimeError(f"refusing incomplete recovery response: {output}")
    cfg = contract["newton"]
    fresh.run_logged(
        [
            str(Path(cfg["python"]).resolve()),
            str(SCRIPT_DIR / "run_newton_cylinder_diagnostic.py"),
            "--config", str(fresh.repo_path(cfg["base_config"])),
            "--prepared-dir", str(preparation),
            "--candidate-preparation",
            "--chrono-episode", str(screening.chrono_episode(contract, case_id)),
            "--output-dir", str(output),
            "--device", str(cfg["device"]),
            "--dt-s", str(cfg["selected_dt_s"]),
            "--pre-settle-duration-s", str(cfg["pre_settle_duration_s"]),
            "--pre-settle-required-duration-s", str(cfg["pre_settle_required_duration_s"]),
            "--particle-speed-threshold-mps", str(cfg["particle_speed_threshold_mps"]),
            "--observation-time-mode", "independent_fixed",
            "--loaded-duration-s", str(LOADED_DURATION_S),
            "--residual-duration-s", str(POST_UNLOAD_DURATION_S),
            "--proxy-iterations", str(cfg["proxy_iterations"]),
            "--rigid-substeps", str(cfg["rigid_substeps"]),
            "--cylinder-friction-coefficient", str(cfg["cylinder_friction_coefficient"]),
            "--cylinder-collider-mode", str(cfg["collider_mode"]),
            "--cylinder-collider-segments", str(cfg["collider_segments"]),
            "--cylinder-collision-guard-m", str(cfg["collision_guard_m"]),
            "--cylinder-collision-bottom-inset-m", "0",
            "--cylinder-projection-threshold-m", str(cfg["projection_threshold_m"]),
        ],
        case_root(case_id) / "logs" / "newton_response.log",
        REPO_ROOT,
    )
    return output


def run_responses(
    contract: dict[str, Any], cases: list[dict[str, Any]], preparation: Path, workers: int
) -> None:
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for case in cases:
            print(f"newton response start {case['case_id']}", flush=True)
            futures[executor.submit(run_response, contract, case, preparation)] = case["case_id"]
        for future in as_completed(futures):
            future.result()
            print(f"newton response complete {futures[future]}", flush=True)


def analyze_case(
    contract: dict[str, Any], proposal: dict[str, Any], case: dict[str, Any]
) -> dict[str, Any]:
    case_id = case["case_id"]
    response = response_dir(case_id)
    manifest_path = response / "newton_cylinder_manifest.json"
    preparation_path = shared_root() / "preparation" / "newton_prepared_bed_manifest.json"
    if not manifest_path.is_file() or not preparation_path.is_file():
        return {"case_id": case_id, "complete": False, "pipeline_usable": False}
    manifest = load_json(manifest_path)
    prepared = load_json(preparation_path)
    metadata = load_json(shared_root() / "metric_bed" / "ground_plane_metadata.json")
    particle_count = int(metadata["particle_count"])
    policy = screening.admission_policy(contract)
    level_1 = policy["level_1_numerical_integrity"]
    level_2 = policy["level_2_interaction_artifact"]
    penetration = manifest["penetration"]
    inside = int(penetration["max_inside_particle_centers"])
    inside_fraction = float(inside / particle_count)
    spacing = float(metadata["particle_spacing_m"])
    gross_depth = spacing * float(level_2["gross_penetration_fraction_of_particle_spacing"])
    timing = manifest.get("observation_timing_s", {})
    chrono = successor.successor_chrono_result(contract, proposal, case)
    numerical = {
        "chrono_accepted": bool(chrono.get("accepted")),
        "preparation_accepted": bool(prepared.get("accepted")),
        "preparation_converged": bool(manifest["preparation"]["convergence_passed"]),
        "finite": bool(manifest["finite"]),
        "guide": bool(manifest["cylinder"]["guide_constraint_passed"]),
        "surface_cells": int(manifest["surface"]["valid_cells"]) >= int(level_1["min_surface_valid_cells"]),
        "initial_support": float(manifest["surface"]["initial_match"]["valid_fraction"]) >= float(level_1["min_initial_surface_valid_fraction"]),
        "independent_fixed_timing": timing.get("mode") == "independent_fixed" and timing.get("chrono_target_time_controls_newton") is False,
    }
    interaction = {
        "within_gross_depth": float(penetration["max_center_penetration_m"]) <= gross_depth,
        "within_gross_affected_fraction": inside_fraction <= float(level_2["gross_inside_particle_fraction"]),
    }
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
        "geometry": phase0_matrix.local_geometry_metrics(
            screening.chrono_episode(contract, case_id), response, case
        ),
        "artifacts": {
            "chrono_episode": str(screening.chrono_episode(contract, case_id).resolve()),
            "shared_preparation": str((shared_root() / "preparation").resolve()),
            "newton_response": str(response.resolve()),
        },
    }
    fresh.write_json(case_root(case_id) / "case_summary.json", result)
    return result


def analyze(
    contract: dict[str, Any], proposal: dict[str, Any], cases: list[dict[str, Any]]
) -> dict[str, Any]:
    results = [analyze_case(contract, proposal, case) for case in cases]
    passed = len(results) == 6 and all(item["complete"] and item["pipeline_usable"] for item in results)
    summary = {
        "schema_version": 1,
        "identity": "phase1_one_action_successor_common_base_recovery_v1",
        "status": "pipeline_passed_directional_analysis_pending" if passed else "failed_or_incomplete",
        "preparation_accepted": load_json(shared_root() / "preparation" / "newton_prepared_bed_manifest.json").get("accepted") if (shared_root() / "preparation" / "newton_prepared_bed_manifest.json").is_file() else False,
        "all_six_pairings_admitted": passed,
        "bulk_training_validation_test_or_protected_target_generation_permitted": False,
        "recovery_plan_sha256": sha256(PLAN_PATH),
        "cases": {result["case_id"]: result for result in results},
    }
    fresh.write_json(RECOVERY_ROOT / "recovery_summary.json", summary)
    return summary


def main() -> None:
    args = parse_args()
    if args.workers != WORKERS:
        raise ValueError("worker count differs from the frozen two-worker recovery")
    if args.stage == "plan":
        plan = write_plan()
        print(json.dumps({"plan": str(PLAN_PATH), "sha256": sha256(PLAN_PATH), "cases": len(plan["case_ids"])}, indent=2))
        return
    plan = load_plan()
    proposal, _input_plan, contract, cases = inputs()
    if args.stage in ("bed", "all"):
        print(build_bed(contract, cases, plan))
    if args.stage in ("newton", "all"):
        preparation = run_preparation(contract, cases, plan)
        run_responses(contract, cases, preparation, args.workers)
    if args.stage in ("analyze", "all"):
        summary = analyze(contract, proposal, cases)
        print(json.dumps({"status": summary["status"], "all_six_pairings_admitted": summary["all_six_pairings_admitted"]}, indent=2))


if __name__ == "__main__":
    main()

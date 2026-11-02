#!/usr/bin/env python3
"""Run the six-case Phase 1 one-action successor engineering screen."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

import numpy as np
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_fresh_phase0_repeatability as fresh
import run_phase1_screening as phase1_screen
from phase1_surface import array_sha256


REPO_ROOT = Path(__file__).resolve().parents[1]
PROPOSAL_PATH = REPO_ROOT / "configs" / "phase1_one_action_successor_v1.json"
INPUT_PLAN_PATH = (
    REPO_ROOT
    / "diagnostics"
    / "phase1_one_action_successor_v1"
    / "screening_plan.json"
)
OPERATIONS_CONTRACT_PATH = REPO_ROOT / "configs" / "phase1_bed_state_v1.json"
EXPECTED_INPUT_PLAN_SHA256 = (
    "5878257631bd0099afae3ce0c0792dd5f90c301515855a9de2292e8ad8bde2c4"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=("plan", "chrono", "bed", "newton", "analyze", "all"),
        default="plan",
    )
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--newton-python", type=Path)
    parser.add_argument("--device")
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    proposal = load_json(PROPOSAL_PATH)
    input_plan = load_json(INPUT_PLAN_PATH)
    operations = load_json(OPERATIONS_CONTRACT_PATH)
    if proposal.get("identity") != "phase1_one_action_successor_v1":
        raise ValueError("unexpected successor proposal identity")
    screen = proposal["prospective_screen"]
    if screen.get("engineering_screen_execution_permitted_after_input_plan_freeze") is not True:
        raise ValueError("engineering-screen execution is not permitted")
    if screen.get(
        "bulk_training_validation_test_or_protected_target_generation_permitted"
    ) is not False:
        raise ValueError("dataset/protected target generation must remain prohibited")
    if input_plan.get("status") != "input_only_frozen_no_execution":
        raise ValueError("input plan is not frozen at the pre-execution gate")
    if sha256(INPUT_PLAN_PATH) != EXPECTED_INPUT_PLAN_SHA256:
        raise ValueError("input screening plan hash changed")
    expected_contract = input_plan["source_sha256"][
        "phase1_one_action_successor_v1_json"
    ]
    if sha256(PROPOSAL_PATH) != expected_contract:
        raise ValueError("successor proposal changed after input-plan freeze")
    cases = input_plan.get("cases", [])
    if len(cases) != 6 or len({case["case_id"] for case in cases}) != 6:
        raise ValueError("successor screen must contain six unique cases")
    for case in cases:
        canonical = {key: value for key, value in case.items() if key != "input_sha256"}
        digest = hashlib.sha256(
            json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        if digest != case["input_sha256"]:
            raise ValueError(f"case input hash changed: {case['case_id']}")
    return proposal, input_plan, operations


def execution_contract(
    proposal: dict[str, Any], operations: dict[str, Any]
) -> dict[str, Any]:
    contract = copy.deepcopy(operations)
    contract["phase_id"] = proposal["identity"]
    contract["status"] = "successor_engineering_screen"
    contract["authority"] = "docs/newton/phase1.md"
    contract["chrono"]["output_root"] = (
        "../tera_splat_sim/validity_experiment/chrono_episodes/"
        "phase1_one_action_successor_v1"
    )
    contract["newton"]["output_root"] = (
        "outputs/validity_experiment/newton/phase1_one_action_successor_v1"
    )
    scm = proposal["domain"]["chrono_scm"]
    contract["chrono"]["soil_parameters"] = copy.deepcopy(scm)
    fixed = contract["chrono"]["soil_parameters"]["fixed"]
    contract["chrono"]["soil_parameters"]["fixed"] = {
        "bekker_kc": float(fixed["bekker_kc"]),
        "bekker_n": float(fixed["bekker_n"]),
        "mohr_cohesion": float(fixed["mohr_cohesion_pa"]),
        "mohr_friction_deg": float(fixed["mohr_friction_deg"]),
        "janosi_shear_m": float(fixed["janosi_shear_m"]),
        "elastic_k": float(fixed["elastic_k_pa_per_m"]),
        "damping_r": float(fixed["damping_r_pa_s_per_m"]),
    }
    return contract


def execution_plan_path(contract: dict[str, Any]) -> Path:
    return phase1_screen.output_root(contract) / "successor_screen_execution_plan.json"


def source_paths(contract: dict[str, Any]) -> dict[str, Path]:
    chrono_repo = fresh.repo_path(contract["chrono"]["repo"])
    return {
        "successor_runner": Path(__file__).resolve(),
        "phase1_screening_library": SCRIPT_DIR / "run_phase1_screening.py",
        "successor_proposal": PROPOSAL_PATH,
        "frozen_input_plan": INPUT_PLAN_PATH,
        "operations_contract": OPERATIONS_CONTRACT_PATH,
        "surface_generator": SCRIPT_DIR / "phase1_surface.py",
        "chrono_episode_bridge": SCRIPT_DIR / "chrono_episode_bridge.py",
        "chrono_episode_cli": chrono_repo / "run_cylinder_episode.py",
        "chrono_episode_impl": (
            chrono_repo
            / "quick_support_demo"
            / "chrono_demo"
            / "cylinder_episode.py"
        ),
        "chrono_scm_builder": (
            chrono_repo / "quick_support_demo" / "chrono_demo" / "build_scm_pit.py"
        ),
        "chrono_terrain_config": (
            chrono_repo / "quick_support_demo" / "configs" / "terrain.yaml"
        ),
        "newton_preparation": SCRIPT_DIR / "run_newton_prepared_bed.py",
        "newton_response": SCRIPT_DIR / "run_newton_cylinder_diagnostic.py",
        "newton_contract": SCRIPT_DIR / "newton_contract.py",
        "newton_base_config": fresh.repo_path(contract["newton"]["base_config"]),
    }


def environment_probes(contract: dict[str, Any]) -> dict[str, str]:
    chrono_repo = fresh.repo_path(contract["chrono"]["repo"])
    chrono = fresh.command_output(
        [
            *(str(value) for value in contract["chrono"]["command"]),
            "-c",
            "import platform,pychrono; print(platform.python_version(), getattr(pychrono,'__version__','unknown'))",
        ],
        chrono_repo,
    )
    newton = fresh.command_output(
        [
            str(Path(contract["newton"]["python"]).resolve()),
            "-c",
            "import platform,numpy,warp,newton; print(platform.python_version(),numpy.__version__,warp.__version__,getattr(newton,'__version__','unknown'))",
        ],
        REPO_ROOT,
    )
    gpu = fresh.command_output(
        ["nvidia-smi", "--query-gpu=name,uuid,driver_version", "--format=csv,noheader"],
        REPO_ROOT,
    )
    if not chrono or not newton or not gpu or "failed" in gpu.lower():
        raise RuntimeError("Chrono, Newton, or GPU environment probe failed")
    return {"chrono": chrono, "newton": newton, "gpu": gpu}


def build_execution_plan(
    contract: dict[str, Any], input_plan: dict[str, Any]
) -> dict[str, Any]:
    sources = source_paths(contract)
    missing = [str(path) for path in sources.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing successor-screen sources: {missing}")
    chrono_repo = fresh.repo_path(contract["chrono"]["repo"])
    return {
        "schema_version": 1,
        "identity": "phase1_one_action_successor_v1_screen_execution",
        "status": "ready_not_started",
        "proposal_sha256": sha256(PROPOSAL_PATH),
        "input_plan_sha256": sha256(INPUT_PLAN_PATH),
        "operations_contract_sha256": sha256(OPERATIONS_CONTRACT_PATH),
        "source_sha256": {name: sha256(path) for name, path in sources.items()},
        "environment_probes": environment_probes(contract),
        "repositories": {
            "tera_splat": {
                "revision": fresh.command_output(["git", "rev-parse", "HEAD"], REPO_ROOT),
                "status_short": fresh.command_output(
                    ["git", "status", "--short"], REPO_ROOT
                ).splitlines(),
            },
            "tera_splat_sim": {
                "revision": fresh.command_output(["git", "rev-parse", "HEAD"], chrono_repo),
                "status_short": fresh.command_output(
                    ["git", "status", "--short"], chrono_repo
                ).splitlines(),
            },
        },
        "case_ids": [case["case_id"] for case in input_plan["cases"]],
        "worker_count": 2,
        "bulk_or_protected_target_generation_permitted": False,
    }


def write_execution_plan(
    contract: dict[str, Any], input_plan: dict[str, Any]
) -> dict[str, Any]:
    plan = build_execution_plan(contract, input_plan)
    path = execution_plan_path(contract)
    if path.exists():
        existing = load_json(path)
        for key in (
            "proposal_sha256",
            "input_plan_sha256",
            "operations_contract_sha256",
            "source_sha256",
            "environment_probes",
            "case_ids",
            "worker_count",
        ):
            if existing.get(key) != plan.get(key):
                raise RuntimeError(f"refusing changed execution plan at {path}: {key}")
        return existing
    fresh.write_json(path, plan)
    return plan


def load_execution_plan(
    contract: dict[str, Any], input_plan: dict[str, Any]
) -> dict[str, Any]:
    path = execution_plan_path(contract)
    if not path.is_file():
        raise RuntimeError("execution plan is absent; run --stage plan first")
    frozen = load_json(path)
    current = build_execution_plan(contract, input_plan)
    for key in (
        "proposal_sha256",
        "input_plan_sha256",
        "operations_contract_sha256",
        "source_sha256",
        "environment_probes",
        "case_ids",
        "worker_count",
    ):
        if frozen.get(key) != current.get(key):
            raise RuntimeError(f"execution plan changed after freeze: {key}")
    return frozen


def material_cases(
    contract: dict[str, Any],
    proposal: dict[str, Any],
    input_plan: dict[str, Any],
    requested: list[str],
) -> list[dict[str, Any]]:
    friction = float(
        proposal["domain"]["chrono_scm"]["fixed"]["mohr_friction_deg"]
    )
    cases = [
        phase1_screen.material_case(
            contract, {**raw, "mohr_friction_deg": friction}
        )
        for raw in input_plan["cases"]
    ]
    by_id = {case["case_id"]: case for case in cases}
    unknown = sorted(set(requested) - set(by_id))
    if unknown:
        raise ValueError(f"unknown successor screen cases: {unknown}")
    return [by_id[name] for name in requested] if requested else cases


def historical_surface_dir(operations: dict[str, Any], seed: int) -> Path:
    return (
        fresh.repo_path(operations["newton"]["output_root"])
        / "screening"
        / "surfaces"
        / f"surface_{seed}"
    )


def prepare_surface_input(
    contract: dict[str, Any],
    operations: dict[str, Any],
    input_plan: dict[str, Any],
) -> Path:
    seed = int(input_plan["common_input"]["initial_surface_seed"])
    source = historical_surface_dir(operations, seed)
    qualification = load_json(source / "qualification_summary.json")
    if qualification.get("qualified") is not True:
        raise RuntimeError("declared reused surface is not qualified")
    destination = phase1_screen.surface_dir(contract, seed)
    files = ("initial_heightmap_m.npy", "generator_summary.json")
    if not destination.exists():
        destination.mkdir(parents=True)
        for name in files:
            shutil.copy2(source / name, destination / name)
        fresh.write_json(
            destination / "reuse_manifest.json",
            {
                "schema_version": 1,
                "policy": "qualified input identity reused; no response artifact reused",
                "source": str(source.resolve()),
                "source_qualification_sha256": sha256(
                    source / "qualification_summary.json"
                ),
                "files_sha256": {
                    name: sha256(destination / name) for name in files
                },
                "input_plan_sha256": sha256(INPUT_PLAN_PATH),
            },
        )
    manifest = load_json(destination / "reuse_manifest.json")
    for name in files:
        if sha256(destination / name) != manifest["files_sha256"][name]:
            raise RuntimeError(f"reused surface file changed: {name}")
    return destination / "initial_heightmap_m.npy"


def successor_chrono_result(
    contract: dict[str, Any],
    proposal: dict[str, Any],
    case: dict[str, Any],
) -> dict[str, Any]:
    result = phase1_screen.chrono_result(contract, case)
    if not result.get("complete"):
        return result
    manifest_path = (
        phase1_screen.chrono_episode(contract, case["case_id"]) / "manifest.yaml"
    )
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    actual = manifest["chrono"]["soil_parameters"]
    fixed = proposal["domain"]["chrono_scm"]["fixed"]
    expected = {
        "bekker_kc": fixed["bekker_kc"],
        "bekker_n": fixed["bekker_n"],
        "mohr_cohesion": fixed["mohr_cohesion_pa"],
        "mohr_friction_deg": fixed["mohr_friction_deg"],
        "janosi_shear_m": fixed["janosi_shear_m"],
        "elastic_k": fixed["elastic_k_pa_per_m"],
        "damping_r": fixed["damping_r_pa_s_per_m"],
    }
    fixed_checks = {
        name: math.isclose(
            float(actual[name]), float(value), rel_tol=1.0e-12, abs_tol=1.0e-12
        )
        for name, value in expected.items()
    }
    return {
        **result,
        "accepted": bool(result["accepted"]) and all(fixed_checks.values()),
        "fixed_soil_checks": fixed_checks,
        "actual_soil_parameters": actual,
    }


def run_chrono(
    contract: dict[str, Any],
    proposal: dict[str, Any],
    operations: dict[str, Any],
    input_plan: dict[str, Any],
    case: dict[str, Any],
) -> dict[str, Any]:
    existing = successor_chrono_result(contract, proposal, case)
    if existing.get("complete"):
        if not existing["accepted"]:
            raise RuntimeError(f"stored Chrono case is rejected: {case['case_id']}")
        return existing
    episode = phase1_screen.chrono_episode(contract, case["case_id"])
    if episode.exists():
        raise RuntimeError(f"refusing incomplete Chrono directory: {episode}")
    source = prepare_surface_input(contract, operations, input_plan)
    cfg = contract["chrono"]
    fixed = proposal["domain"]["chrono_scm"]["fixed"]
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
        "--loading-linear-speed-threshold-mps",
        str(cfg["loading_linear_speed_threshold_mps"]),
        "--loading-angular-speed-threshold-radps",
        str(cfg["loading_angular_speed_threshold_radps"]),
        "--loading-hold-time-s", str(cfg["loading_hold_time_s"]),
        "--residual-settle-s", str(cfg["residual_duration_s"]),
        "--initial-heightmap-npy", str(source),
        "--bekker-kphi", str(case["bekker_kphi"]),
        "--bekker-kc", str(fixed["bekker_kc"]),
        "--bekker-n", str(fixed["bekker_n"]),
        "--mohr-cohesion-pa", str(fixed["mohr_cohesion_pa"]),
        "--mohr-friction-deg", str(fixed["mohr_friction_deg"]),
        "--janosi-shear-m", str(fixed["janosi_shear_m"]),
        "--elastic-k-pa-per-m", str(fixed["elastic_k_pa_per_m"]),
        "--damping-r-pa-s-per-m", str(fixed["damping_r_pa_s_per_m"]),
        "--output-dir", str(episode),
        "--vertical-guide",
    ]
    fresh.run_logged(
        command,
        phase1_screen.material_root(contract, case["case_id"])
        / "logs"
        / "chrono.log",
        fresh.repo_path(cfg["repo"]),
        cfg["thread_environment"],
    )
    result = successor_chrono_result(contract, proposal, case)
    if not result["accepted"]:
        raise RuntimeError(f"Chrono successor screen rejected: {case['case_id']}")
    return result


def analyze_case(
    contract: dict[str, Any],
    proposal: dict[str, Any],
    case: dict[str, Any],
) -> dict[str, Any]:
    chrono = successor_chrono_result(contract, proposal, case)
    if not chrono.get("accepted"):
        return {
            "case_id": case["case_id"],
            "complete": False,
            "pipeline_usable": False,
            "successor_chrono": chrono,
        }
    result = phase1_screen.analyze_material(contract, case)
    result["successor_chrono"] = chrono
    result["input_sha256"] = case["input_sha256"]
    fresh.write_json(
        phase1_screen.material_root(contract, case["case_id"])
        / "case_summary.json",
        result,
    )
    return result


def summarize(
    contract: dict[str, Any],
    proposal: dict[str, Any],
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    materials = [analyze_case(contract, proposal, case) for case in cases]
    passed = len(materials) == 6 and all(
        item.get("complete") and item.get("pipeline_usable") for item in materials
    )
    summary = {
        "schema_version": 1,
        "identity": "phase1_one_action_successor_v1_screen",
        "status": "pipeline_passed_directional_analysis_pending"
        if passed
        else "incomplete_or_failed",
        "screen_execution_complete": passed,
        "bulk_or_protected_target_generation_permitted": False,
        "input_plan_sha256": sha256(INPUT_PLAN_PATH),
        "execution_plan_sha256": sha256(execution_plan_path(contract)),
        "materials": {item["case_id"]: item for item in materials},
    }
    fresh.write_json(
        phase1_screen.output_root(contract) / "screening_summary.json", summary
    )
    return summary


def run_parallel(
    label: str,
    cases: list[dict[str, Any]],
    workers: int,
    function: Callable[[dict[str, Any]], Any],
) -> None:
    if workers < 1:
        raise ValueError("workers must be positive")
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for case in cases:
            print(f"{label} start {case['case_id']}", flush=True)
            futures[executor.submit(function, case)] = case["case_id"]
        for future in as_completed(futures):
            case_id = futures[future]
            future.result()
            print(f"{label} complete {case_id}", flush=True)


def main() -> None:
    args = parse_args()
    proposal, input_plan, operations = load_inputs()
    contract = execution_contract(proposal, operations)
    if args.stage == "plan":
        plan = write_execution_plan(contract, input_plan)
        prepare_surface_input(contract, operations, input_plan)
        print(
            json.dumps(
                {
                    "execution_plan": str(execution_plan_path(contract)),
                    "execution_plan_sha256": sha256(execution_plan_path(contract)),
                    "status": plan["status"],
                    "case_count": len(plan["case_ids"]),
                },
                indent=2,
            )
        )
        return

    frozen = load_execution_plan(contract, input_plan)
    if int(args.workers) != int(frozen["worker_count"]):
        raise ValueError("worker count differs from frozen execution plan")
    prepare_surface_input(contract, operations, input_plan)
    selected = material_cases(contract, proposal, input_plan, args.case)

    if args.stage in ("chrono", "all"):
        run_parallel(
            "chrono",
            selected,
            args.workers,
            lambda case: run_chrono(
                contract, proposal, operations, input_plan, case
            ),
        )
    if args.stage in ("bed", "all"):
        run_parallel(
            "bed",
            selected,
            args.workers,
            lambda case: phase1_screen.build_bed(contract, case),
        )
    if args.stage in ("newton", "all"):
        run_parallel(
            "newton",
            selected,
            args.workers,
            lambda case: phase1_screen.run_newton(
                contract, case, args.newton_python, args.device
            ),
        )
    if args.stage in ("analyze", "all"):
        for case in selected:
            analyze_case(contract, proposal, case)

    all_cases = material_cases(contract, proposal, input_plan, [])
    summary = summarize(contract, proposal, all_cases)
    print(
        json.dumps(
            {
                "status": summary["status"],
                "screen_execution_complete": summary[
                    "screen_execution_complete"
                ],
                "case_count": len(summary["materials"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

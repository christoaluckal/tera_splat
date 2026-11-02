#!/usr/bin/env python3
"""Prospectively qualify the six successor initial-surface seeds."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path
from typing import Any

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_fresh_phase0_repeatability as fresh
from phase1_surface import array_sha256, generate_surface, limits_from_contract


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "configs" / "phase1_one_action_successor_contract_v1.json"
DATASET_PLAN = (
    REPO_ROOT / "outputs" / "validity_experiment" / "newton"
    / "phase1_one_action_successor_contract_v1" / "dataset_plan.json"
)
OUTPUT_ROOT = (
    REPO_ROOT / "outputs" / "validity_experiment" / "newton"
    / "phase1_one_action_successor_contract_v1" / "surface_qualification"
)
PLAN_PATH = OUTPUT_ROOT / "qualification_plan.json"
SUMMARY_PATH = OUTPUT_ROOT / "qualification_summary.json"
MAXIMUM_ROUNDTRIP_ERROR_M = 1.0e-5
THREAD_ENVIRONMENT = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("plan", "qualify", "analyze", "all"), default="plan")
    parser.add_argument("--seed", type=int, action="append", default=[])
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    contract = load_json(CONTRACT_PATH)
    dataset = load_json(DATASET_PLAN)
    if contract.get("contract_id") != "phase1_one_action_successor_contract_v1":
        raise ValueError("unexpected successor contract")
    if dataset.get("status") != "target_free_plan_frozen":
        raise ValueError("successor dataset plan is not frozen")
    if dataset.get("contract_sha256") != sha256(CONTRACT_PATH):
        raise RuntimeError("successor contract changed after dataset-plan freeze")
    if dataset["permissions"].get("surface_qualification") is not True:
        raise RuntimeError("surface qualification is not authorized")
    if dataset["permissions"].get("test_or_protected_sensitivity_target_generation") is not False:
        raise RuntimeError("protected targets must remain locked")
    return contract, dataset


def cases(contract: dict[str, Any]) -> list[dict[str, Any]]:
    domain = contract["initial_surface_domain"]
    bounds = {
        "relief_limit_m": domain["relief_limit_m"],
        "maximum_local_slope_deg": domain["maximum_local_slope_deg"],
        "minimum_correlation_length_m": domain["minimum_correlation_length_m"],
    }
    result = []
    for partition, seeds in domain["surface_seeds"].items():
        for seed in seeds:
            payload = {
                "partition": partition,
                "initial_surface_seed": int(seed),
                "generator": domain["generator"],
                "bounds": bounds,
            }
            result.append({"case_id": f"successor_surface_{int(seed)}", **payload, "input_sha256": canonical_sha256(payload)})
    return result


def source_paths(contract: dict[str, Any]) -> dict[str, Path]:
    chrono_repo = fresh.repo_path(contract["chrono"]["repo"])
    return {
        "qualifier": Path(__file__).resolve(),
        "surface_generator": SCRIPT_DIR / "phase1_surface.py",
        "execution_helpers": SCRIPT_DIR / "run_fresh_phase0_repeatability.py",
        "chrono_roundtrip_cli": chrono_repo / "check_scm_initial_heightmap.py",
        "chrono_scm_builder": chrono_repo / "quick_support_demo" / "chrono_demo" / "build_scm_pit.py",
        "chrono_world_builder": chrono_repo / "quick_support_demo" / "chrono_demo" / "build_world.py",
        "chrono_config_loader": chrono_repo / "quick_support_demo" / "config.py",
        "chrono_demo_config": chrono_repo / "quick_support_demo" / "configs" / "demo.yaml",
        "chrono_world_config": chrono_repo / "quick_support_demo" / "configs" / "world.yaml",
        "chrono_terrain_config": chrono_repo / "quick_support_demo" / "configs" / "terrain.yaml",
    }


def environment(contract: dict[str, Any]) -> dict[str, Any]:
    chrono_repo = fresh.repo_path(contract["chrono"]["repo"])
    lines = [
        line.strip()
        for line in fresh.command_output(
            [
                *(str(value) for value in contract["chrono"]["command"]),
                "-c",
                "import json,platform,pychrono; print(json.dumps({'python':platform.python_version(),'pychrono':getattr(pychrono,'__version__','unknown')}))",
            ],
            chrono_repo,
        ).splitlines()
        if line.strip().startswith("{")
    ]
    if not lines:
        raise RuntimeError("Chrono environment probe failed")
    return {"captured_by_python": platform.python_version(), "chrono": json.loads(lines[-1]), "thread_environment": THREAD_ENVIRONMENT}


def build_plan() -> dict[str, Any]:
    contract, dataset = load_inputs()
    sources = source_paths(contract)
    missing = [str(path) for path in sources.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing surface-qualification sources: {missing}")
    return {
        "schema_version": 1,
        "identity": "phase1_one_action_successor_surface_qualification_v1",
        "status": "frozen_before_runtime",
        "contract_sha256": sha256(CONTRACT_PATH),
        "dataset_plan_sha256": sha256(DATASET_PLAN),
        "episode_manifest_sha256": dataset["episode_manifest_sha256"],
        "test_lock_sha256": dataset["test_lock_sha256"],
        "sensitivity_lock_sha256": dataset["sensitivity_lock_sha256"],
        "source_sha256": {name: sha256(path) for name, path in sources.items()},
        "environment": environment(contract),
        "cases": cases(contract),
        "maximum_scm_roundtrip_error_m": MAXIMUM_ROUNDTRIP_ERROR_M,
        "target_generation_permitted": False,
    }


def write_plan() -> dict[str, Any]:
    plan = build_plan()
    if PLAN_PATH.exists():
        existing = load_json(PLAN_PATH)
        stable = ("contract_sha256", "dataset_plan_sha256", "episode_manifest_sha256", "test_lock_sha256", "sensitivity_lock_sha256", "source_sha256", "environment", "cases", "maximum_scm_roundtrip_error_m")
        if any(existing.get(key) != plan.get(key) for key in stable):
            raise RuntimeError("refusing changed surface-qualification plan")
        return existing
    fresh.write_json(PLAN_PATH, plan)
    return plan


def load_plan() -> dict[str, Any]:
    if not PLAN_PATH.is_file():
        raise RuntimeError("surface-qualification plan is absent; run --stage plan")
    frozen = load_json(PLAN_PATH)
    current = build_plan()
    stable = ("contract_sha256", "dataset_plan_sha256", "episode_manifest_sha256", "test_lock_sha256", "sensitivity_lock_sha256", "source_sha256", "environment", "cases", "maximum_scm_roundtrip_error_m")
    changed = [key for key in stable if frozen.get(key) != current.get(key)]
    if changed:
        raise RuntimeError(f"surface-qualification identity changed: {changed}")
    return frozen


def surface_root(seed: int) -> Path:
    return OUTPUT_ROOT / "surfaces" / f"surface_{int(seed)}"


def qualify(contract: dict[str, Any], plan: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    seed = int(case["initial_surface_seed"])
    root = surface_root(seed)
    heightmap_path = root / "initial_heightmap_m.npy"
    generator_path = root / "generator_summary.json"
    native_root = root / "chrono_scm_roundtrip"
    if heightmap_path.is_file() and generator_path.is_file():
        heightmap = np.load(heightmap_path, allow_pickle=False)
        generated = load_json(generator_path)
        if array_sha256(heightmap) != generated["metrics"]["array_sha256"]:
            raise RuntimeError(f"stored successor surface changed: {seed}")
    elif root.exists():
        raise RuntimeError(f"refusing incomplete successor surface: {root}")
    else:
        heightmap, generated = generate_surface(seed, limits_from_contract(contract))
        root.mkdir(parents=True, exist_ok=False)
        np.save(heightmap_path, heightmap)
        fresh.write_json(generator_path, generated)

    if not (native_root / "summary.json").is_file():
        if native_root.exists():
            raise RuntimeError(f"refusing incomplete SCM round trip: {native_root}")
        chrono = contract["chrono"]
        fresh.run_logged(
            [
                *(str(value) for value in chrono["command"]),
                str(fresh.repo_path(chrono["repo"]) / "check_scm_initial_heightmap.py"),
                "--heightmap-npy", str(heightmap_path),
                "--output-dir", str(native_root),
                "--scm-grid-spacing-m", str(chrono["scm_grid_spacing_m"]),
                "--scm-pit-size-m", *(str(value) for value in chrono["scm_pit_size_m"]),
                "--bekker-kphi", str(chrono["soil_parameters"]["varied"]["bekker_kphi"]["reference"]),
                "--mohr-friction-deg", str(chrono["soil_parameters"]["fixed"]["mohr_friction_deg"]),
                "--maximum-roundtrip-error-m", str(plan["maximum_scm_roundtrip_error_m"]),
            ],
            root / "chrono_scm_roundtrip.log",
            fresh.repo_path(chrono["repo"]),
            THREAD_ENVIRONMENT,
        )
    native = load_json(native_root / "summary.json")
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


def summarize(plan: dict[str, Any]) -> dict[str, Any]:
    results = []
    for case in plan["cases"]:
        path = surface_root(int(case["initial_surface_seed"])) / "qualification_summary.json"
        results.append(load_json(path) if path.is_file() else {"case_id": case["case_id"], "seed": case["initial_surface_seed"], "qualified": False})
    passed = len(results) == 6 and all(item.get("qualified") for item in results)
    summary = {
        "schema_version": 1,
        "identity": "phase1_one_action_successor_surface_qualification_v1",
        "status": "passed" if passed else "failed_or_incomplete",
        "all_six_surfaces_qualified": passed,
        "smoke_target_generation_permitted": passed,
        "remaining_train_validation_target_generation_permitted": False,
        "test_or_protected_sensitivity_target_generation_permitted": False,
        "qualification_plan_sha256": sha256(PLAN_PATH),
        "surfaces": {str(item["seed"]): item for item in results},
    }
    fresh.write_json(SUMMARY_PATH, summary)
    return summary


def main() -> None:
    args = parse_args()
    if args.stage == "plan":
        plan = write_plan()
        print(json.dumps({"plan": str(PLAN_PATH), "sha256": sha256(PLAN_PATH), "cases": len(plan["cases"])}, indent=2))
        return
    plan = load_plan()
    contract, _dataset = load_inputs()
    selected = [case for case in plan["cases"] if not args.seed or int(case["initial_surface_seed"]) in set(args.seed)]
    if args.seed and len(selected) != len(set(args.seed)):
        raise ValueError("unknown or duplicate requested successor surface seed")
    if args.stage in ("qualify", "all"):
        for case in selected:
            result = qualify(contract, plan, case)
            print(json.dumps({"seed": result["seed"], "qualified": result["qualified"]}), flush=True)
    if args.stage in ("analyze", "all"):
        summary = summarize(plan)
        print(json.dumps({"status": summary["status"], "all_six_surfaces_qualified": summary["all_six_surfaces_qualified"], "smoke_target_generation_permitted": summary["smoke_target_generation_permitted"]}, indent=2))


if __name__ == "__main__":
    main()

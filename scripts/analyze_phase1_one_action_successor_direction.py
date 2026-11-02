#!/usr/bin/env python3
"""Freeze and evaluate directional gates for the six-case successor screen."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_fresh_phase0_repeatability as fresh
import run_phase1_one_action_successor_screen as successor
import run_phase1_screening as screening
from chrono_episode_bridge import heightmap_axes, load_episode


REPO_ROOT = Path(__file__).resolve().parents[1]
RECOVERY_ROOT = (
    REPO_ROOT / "outputs" / "validity_experiment" / "newton"
    / "phase1_one_action_successor_v1" / "common_base_recovery_v1"
)
RECOVERY_PLAN = RECOVERY_ROOT / "recovery_plan.json"
RECOVERY_SUMMARY = RECOVERY_ROOT / "recovery_summary.json"
ANALYSIS_PLAN = RECOVERY_ROOT / "directional_analysis_plan.json"
ANALYSIS_SUMMARY = RECOVERY_ROOT / "directional_analysis_summary.json"
REPEATABILITY = (
    REPO_ROOT / "outputs" / "validity_experiment" / "newton"
    / "static_proxy_hierarchical_v3_20261017" / "repeatability"
    / "repeatability_summary.json"
)
PHASES = ("loaded", "post_unload")
METRICS = ("peak_depression_m", "mean_depression_m", "displaced_volume_m3")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("plan", "analyze", "all"), default="plan")
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def case_inputs() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    proposal, input_plan, operations = successor.load_inputs()
    contract = successor.execution_contract(proposal, operations)
    cases = successor.material_cases(contract, proposal, input_plan, [])
    return proposal, contract, cases


def input_paths(contract: dict[str, Any], cases: list[dict[str, Any]]) -> dict[str, Path]:
    paths = {
        "successor_proposal": successor.PROPOSAL_PATH,
        "frozen_input_plan": successor.INPUT_PLAN_PATH,
        "recovery_plan": RECOVERY_PLAN,
        "recovery_summary": RECOVERY_SUMMARY,
        "chrono_repeatability_summary": REPEATABILITY,
    }
    for case in cases:
        case_id = case["case_id"]
        episode = screening.chrono_episode(contract, case_id)
        manifest_path = episode / "manifest.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        paths[f"{case_id}:manifest"] = manifest_path
        for phase, state in (("initial", "initial"), ("loaded", "loaded"), ("post_unload", "residual")):
            paths[f"{case_id}:{phase}"] = episode / manifest["states"][state]
        valid_name = str(manifest["heightmap"]["valid_mask"]).split(";", 1)[0].strip()
        paths[f"{case_id}:valid_mask"] = episode / valid_name
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing directional-analysis inputs: {missing}")
    return paths


def build_plan() -> dict[str, Any]:
    _proposal, contract, cases = case_inputs()
    recovery = read_json(RECOVERY_SUMMARY)
    if recovery.get("all_six_pairings_admitted") is not True:
        raise RuntimeError("all six recovery pairings must be admitted")
    repeatability = read_json(REPEATABILITY)
    chrono_repeat = repeatability["chrono"]
    if chrono_repeat.get("bitwise_identical") is not True:
        raise RuntimeError("declared Chrono repeatability basis is not exact")
    paths = input_paths(contract, cases)
    sources = {
        "directional_analyzer": Path(__file__).resolve(),
        "successor_runner": SCRIPT_DIR / "run_phase1_one_action_successor_screen.py",
        "phase1_screening": SCRIPT_DIR / "run_phase1_screening.py",
        "chrono_episode_bridge": SCRIPT_DIR / "chrono_episode_bridge.py",
    }
    return {
        "schema_version": 1,
        "identity": "phase1_one_action_successor_directional_analysis_v1",
        "status": "frozen_before_analysis",
        "source_sha256": {name: sha256(path) for name, path in sources.items()},
        "input_sha256": {name: sha256(path) for name, path in paths.items()},
        "case_ids": [case["case_id"] for case in cases],
        "metrics": list(METRICS),
        "phases": list(PHASES),
        "gates": {
            "kphi_direction": "strictly decreasing deformation with increasing Kphi for every adjacent comparison",
            "endpoint_separation": "absolute endpoint change exceeds the exact-repeat Chrono metric floor",
            "force_direction": "strictly increasing deformation with increasing normal force",
            "repeatability_floor_basis": "bitwise-identical Chrono loaded and residual heightmaps imply zero metric floor",
        },
        "bulk_training_validation_test_or_protected_target_generation_permitted": False,
    }


def write_plan() -> dict[str, Any]:
    plan = build_plan()
    if ANALYSIS_PLAN.exists():
        existing = read_json(ANALYSIS_PLAN)
        for key in ("source_sha256", "input_sha256", "case_ids", "metrics", "phases", "gates"):
            if existing.get(key) != plan.get(key):
                raise RuntimeError(f"directional-analysis plan changed: {key}")
        return existing
    fresh.write_json(ANALYSIS_PLAN, plan)
    return plan


def load_plan() -> dict[str, Any]:
    if not ANALYSIS_PLAN.is_file():
        raise RuntimeError("directional-analysis plan is absent; run --stage plan")
    frozen = read_json(ANALYSIS_PLAN)
    current = build_plan()
    for key in ("source_sha256", "input_sha256", "case_ids", "metrics", "phases", "gates"):
        if frozen.get(key) != current.get(key):
            raise RuntimeError(f"directional-analysis identity changed: {key}")
    return frozen


def response_metrics(contract: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    episode = screening.chrono_episode(contract, case["case_id"])
    manifest, _action, initial, valid = load_episode(episode)
    xs, ys = heightmap_axes(manifest)
    grid_x, grid_y = np.meshgrid(xs, ys, indexing="xy")
    center = case["center_xy_m"]
    footprint = valid & (
        (grid_x - float(center[0])) ** 2 + (grid_y - float(center[1])) ** 2
        <= float(case["radius_m"]) ** 2 + 1.0e-15
    )
    spacing = float(manifest["heightmap"]["spacing_m"])
    result: dict[str, Any] = {
        "case_id": case["case_id"],
        "bekker_kphi": float(case["bekker_kphi"]),
        "normal_force_n": float(case["normal_force_n"]),
        "footprint_cells": int(np.count_nonzero(footprint)),
    }
    for output_phase, state_name in (("loaded", "loaded"), ("post_unload", "residual")):
        state = np.load(episode / manifest["states"][state_name], allow_pickle=False)
        depression = initial - state
        selected = depression[footprint]
        result[output_phase] = {
            "peak_depression_m": float(np.max(selected)),
            "mean_depression_m": float(np.mean(selected)),
            "displaced_volume_m3": float(
                np.sum(np.maximum(selected, 0.0)) * spacing * spacing
            ),
        }
    return result


def analyze() -> dict[str, Any]:
    plan = load_plan()
    _proposal, contract, cases = case_inputs()
    responses = [response_metrics(contract, case) for case in cases]
    forces = sorted({item["normal_force_n"] for item in responses})
    kphis = sorted({item["bekker_kphi"] for item in responses})
    by_pair = {(item["normal_force_n"], item["bekker_kphi"]): item for item in responses}

    kphi_checks: list[dict[str, Any]] = []
    endpoints: list[dict[str, Any]] = []
    force_checks: list[dict[str, Any]] = []
    for phase in PHASES:
        for metric in METRICS:
            for force in forces:
                values = [by_pair[(force, kphi)][phase][metric] for kphi in kphis]
                adjacent = [values[index + 1] - values[index] for index in range(len(values) - 1)]
                kphi_checks.append({
                    "phase": phase, "metric": metric, "normal_force_n": force,
                    "kphi": kphis, "values": values, "adjacent_changes": adjacent,
                    "passed": all(change < 0.0 for change in adjacent),
                })
                separation = abs(values[-1] - values[0])
                endpoints.append({
                    "phase": phase, "metric": metric, "normal_force_n": force,
                    "endpoint_separation": separation, "repeatability_floor": 0.0,
                    "passed": separation > 0.0,
                })
            for kphi in kphis:
                values = [by_pair[(force, kphi)][phase][metric] for force in forces]
                force_checks.append({
                    "phase": phase, "metric": metric, "bekker_kphi": kphi,
                    "normal_force_n": forces, "values": values,
                    "passed": values[-1] > values[0],
                })

    recovery = read_json(RECOVERY_SUMMARY)
    checks = {
        "all_six_pairings_admitted": bool(recovery["all_six_pairings_admitted"]),
        "all_kphi_directions_monotone": all(item["passed"] for item in kphi_checks),
        "all_endpoint_separations_above_repeatability": all(item["passed"] for item in endpoints),
        "all_force_directions_positive": all(item["passed"] for item in force_checks),
    }
    passed = all(checks.values())
    summary = {
        "schema_version": 1,
        "identity": "phase1_one_action_successor_directional_analysis_v1",
        "status": "screen_passed_successor_contract_freeze_permitted" if passed else "screen_failed",
        "checks": checks,
        "screen_passed": passed,
        "bulk_training_validation_test_or_protected_target_generation_permitted": False,
        "next_permitted_action": "freeze a prospective successor data/evaluation contract" if passed else "revise the prospective screen before target generation",
        "responses": {item["case_id"]: item for item in responses},
        "kphi_direction_checks": kphi_checks,
        "endpoint_separation_checks": endpoints,
        "force_direction_checks": force_checks,
        "identity_provenance": {
            "directional_analysis_plan_sha256": sha256(ANALYSIS_PLAN),
            "recovery_plan_sha256": sha256(RECOVERY_PLAN),
            "recovery_summary_sha256": sha256(RECOVERY_SUMMARY),
            "source_sha256": plan["source_sha256"],
            "input_sha256": plan["input_sha256"],
        },
    }
    fresh.write_json(ANALYSIS_SUMMARY, summary)
    return summary


def main() -> None:
    args = parse_args()
    if args.stage in ("plan", "all"):
        plan = write_plan()
        print(json.dumps({"plan": str(ANALYSIS_PLAN), "sha256": sha256(ANALYSIS_PLAN), "cases": len(plan["case_ids"])}, indent=2))
        if args.stage == "plan":
            return
    if args.stage in ("analyze", "all"):
        summary = analyze()
        print(json.dumps({"status": summary["status"], "checks": summary["checks"], "summary": str(ANALYSIS_SUMMARY)}, indent=2))


if __name__ == "__main__":
    main()

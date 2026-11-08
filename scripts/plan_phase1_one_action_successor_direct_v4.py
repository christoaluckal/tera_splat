#!/usr/bin/env python3
"""Freeze fresh target-free direct-v4 confirmation identities and locks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import evaluate_phase1_one_action_successor as evaluation
import plan_phase1_one_action_successor as original


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_direct_v4.json"
EXPECTED_ID = "phase1_one_action_successor_direct_v4"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    return parser.parse_args()


def repo_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (REPO_ROOT / path).resolve()


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.resolve().read_text(encoding="utf-8"))
    if config.get("schema_version") != 1 or config.get("branch_id") != EXPECTED_ID:
        raise ValueError("unexpected direct-v4 branch identity")
    design = config.get("confirmation_design", {})
    if design.get("test_episode_count") != 24 or design.get("sensitivity_episode_count") != 6:
        raise ValueError("direct-v4 confirmation counts changed")
    test_seeds = [int(value) for value in design.get("test_surface_seeds", [])]
    sensitivity_seed = int(design.get("sensitivity_surface_seed", -1))
    if len(test_seeds) != 5 or len(set(test_seeds + [sensitivity_seed])) != 6:
        raise ValueError("direct-v4 fresh surface identities changed")
    if not all(5101 <= value <= 5106 for value in test_seeds + [sensitivity_seed]):
        raise ValueError("direct-v4 surface seeds left the frozen fresh set")
    protocol = config.get("confirmation_protocol", {})
    if protocol.get("target_lock_required_before_authoritative_validation") is not True:
        raise ValueError("direct-v4 validation ordering weakened")
    return config


def require_source(config: Mapping[str, Any], name: str) -> Path:
    path = repo_path(config["frozen_sources"][name])
    expected = str(config["frozen_sources"][f"{name}_sha256"])
    if not path.is_file() or evaluation.sha256_file(path) != expected:
        raise RuntimeError(f"direct-v4 frozen source changed: {name}")
    return path


def make_test_episodes(config: Mapping[str, Any], contract: Mapping[str, Any]) -> list[dict[str, Any]]:
    design = config["confirmation_design"]
    start = int(design["halton_start_index"])
    seeds = [int(value) for value in design["test_surface_seeds"]]
    rows = []
    for ordinal in range(int(design["test_episode_count"])):
        row = original.make_episode(
            contract,
            "test",
            ordinal,
            original.continuous_sample(contract, start + ordinal),
            seeds[ordinal % len(seeds)],
            "fresh_joint_confirmation",
        )
        row["episode_id"] = f"p1d4_test_fresh-joint_{ordinal:03d}"
        rows.append(row)
    return rows


def make_sensitivity_episodes(config: Mapping[str, Any], contract: Mapping[str, Any]) -> list[dict[str, Any]]:
    design = config["confirmation_design"]
    rows = []
    for force in design["sensitivity_normal_force_points_n"]:
        for kphi in design["sensitivity_bekker_kphi_points"]:
            ordinal = len(rows)
            row = original.make_episode(
                contract,
                "protected_sensitivity",
                ordinal,
                {
                    "center_xy_m": design["sensitivity_center_xy_m"],
                    "normal_force_n": force,
                    "bekker_kphi": kphi,
                },
                int(design["sensitivity_surface_seed"]),
                "matched_kphi_sweep",
            )
            row["episode_id"] = f"p1d4_protected_sensitivity_matched-kphi-sweep_{ordinal:03d}"
            rows.append(row)
    return rows


def validate_episodes(
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    test: list[dict[str, Any]],
    sensitivity: list[dict[str, Any]],
) -> None:
    rows = test + sensitivity
    if len(test) != 24 or len(sensitivity) != 6:
        raise RuntimeError("direct-v4 confirmation membership changed")
    if len({row["episode_id"] for row in rows}) != 30:
        raise RuntimeError("direct-v4 episode identities are not unique")
    if len({row["input_sha256"] for row in rows}) != 30:
        raise RuntimeError("direct-v4 physical inputs are not unique")
    original_plan = json.loads(
        require_source(config, "original_dataset_plan").read_text(encoding="utf-8")
    )
    prior = {
        str(row["input_sha256"])
        for split in original_plan["episodes"].values()
        for row in split
    }
    if any(str(row["input_sha256"]) in prior for row in rows):
        raise RuntimeError("direct-v4 input reuses an original physical identity")
    origin = contract["action_domain"]["center_domain"]["origin_xy_m"]
    max_radius = float(contract["action_domain"]["center_domain"]["max_radius_m"])
    force_bounds = original.closed_range(contract["action_domain"]["normal_force_n"], "force")
    kphi_bounds = original.closed_range(
        contract["chrono"]["soil_parameters"]["varied"]["bekker_kphi"], "kphi"
    )
    import math

    for row in rows:
        x, y = (float(value) for value in row["center_xy_m"])
        if math.hypot(x - float(origin[0]), y - float(origin[1])) > max_radius + 1e-12:
            raise RuntimeError("direct-v4 position left the frozen domain")
        if not force_bounds[0] <= float(row["normal_force_n"]) <= force_bounds[1]:
            raise RuntimeError("direct-v4 force left the frozen domain")
        kphi = float(row["soil_parameters"]["bekker_kphi"])
        if not kphi_bounds[0] <= kphi <= kphi_bounds[1]:
            raise RuntimeError("direct-v4 kphi left the frozen domain")
        if row.get("target_access") != "locked":
            raise RuntimeError("direct-v4 target identity is not locked")
    shared = {
        (row["initial_surface_seed"], tuple(row["center_xy_m"]), row["radius_m"])
        for row in sensitivity
    }
    if len(shared) != 1:
        raise RuntimeError("direct-v4 sensitivity is not a matched sweep")


def source_paths(config_path: Path) -> dict[str, Path]:
    return {
        "config": config_path.resolve(),
        "planner": Path(__file__).resolve(),
        "validator": SCRIPT_DIR / "validate_phase1_one_action_successor_direct_v4.py",
        "planner_tests": REPO_ROOT / "tests" / "test_plan_phase1_one_action_successor_direct_v4.py",
        "validator_tests": REPO_ROOT / "tests" / "test_validate_phase1_one_action_successor_direct_v4.py",
    }


def build_plan(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    contract_path = require_source(config, "domain_contract")
    contract = original.load_contract(contract_path)
    test = make_test_episodes(config, contract)
    sensitivity = make_sensitivity_episodes(config, contract)
    validate_episodes(config, contract, test, sensitivity)
    dataset_root = repo_path(config["execution"]["dataset_output_root"])
    chrono_root = repo_path(config["execution"]["chrono_output_root"])
    if (dataset_root / "episodes").exists() or chrono_root.exists():
        raise RuntimeError("direct-v4 confirmation targets already exist before plan freeze")
    sources = source_paths(config_path)
    missing = [str(path) for path in sources.values() if not path.is_file()]
    if missing:
        raise RuntimeError(f"direct-v4 source set is incomplete: {missing}")
    lock_rows = lambda values: [
        {"episode_id": row["episode_id"], "input_sha256": row["input_sha256"]}
        for row in values
    ]
    payload = {
        "schema_version": 1,
        "branch_id": EXPECTED_ID,
        "status": "target_free_confirmation_plan_frozen_before_authoritative_validation",
        "config_sha256": evaluation.sha256_file(config_path.resolve()),
        "source_sha256": {
            name: evaluation.sha256_file(path) for name, path in sorted(sources.items())
        },
        "candidate": dict(config["candidate"]),
        "confirmation_protocol": dict(config["confirmation_protocol"]),
        "episodes": {"test": test, "protected_sensitivity": sensitivity},
        "counts": {"test": len(test), "protected_sensitivity": len(sensitivity)},
        "episode_manifest_sha256": evaluation.canonical_sha256(
            {"test": test, "protected_sensitivity": sensitivity}
        ),
        "test_lock_sha256": evaluation.canonical_sha256(lock_rows(test)),
        "sensitivity_lock_sha256": evaluation.canonical_sha256(lock_rows(sensitivity)),
        "targets_opened": False,
        "authoritative_validation_complete": False,
    }
    destination = repo_path(config["execution"]["confirmation_plan"])
    if destination.is_file():
        existing = json.loads(destination.read_text(encoding="utf-8"))
        if existing != payload:
            raise RuntimeError("refusing to replace a different direct-v4 confirmation plan")
        return existing
    evaluation.write_json(destination, payload)
    return payload


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    payload = build_plan(config_path, load_config(config_path))
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

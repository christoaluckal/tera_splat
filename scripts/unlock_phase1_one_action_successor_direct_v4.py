#!/usr/bin/env python3
"""Create or verify the one-time direct-v4 protected-target unlock."""

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
import plan_phase1_one_action_successor_direct_v4 as planner
import qualify_phase1_one_action_successor_direct_v4_surfaces as surfaces


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = planner.DEFAULT_CONFIG
TEST_PATH = REPO_ROOT / "tests" / "test_unlock_phase1_one_action_successor_direct_v4.py"
STATUS = (
    "test_and_sensitivity_generation_jointly_unlocked_after_authoritative_"
    "validation_and_surface_qualification"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def unlock_path(config: Mapping[str, Any]) -> Path:
    return planner.repo_path(config["execution"]["output_root"]) / "joint_unlock.json"


def opened_path(config: Mapping[str, Any]) -> Path:
    return planner.repo_path(config["execution"]["output_root"]) / "targets_opened.json"


def assert_targets_absent(config: Mapping[str, Any]) -> None:
    dataset_root = planner.repo_path(config["execution"]["dataset_output_root"])
    chrono_root = planner.repo_path(config["execution"]["chrono_output_root"])
    if (dataset_root / "episodes").exists() or chrono_root.exists():
        raise RuntimeError("direct-v4 protected targets already exist")
    if opened_path(config).exists():
        raise RuntimeError("direct-v4 protected targets were already marked open")


def validate_confirmation(
    config_path: Path, config: Mapping[str, Any]
) -> tuple[Path, dict[str, Any]]:
    path = planner.repo_path(config["execution"]["confirmation_plan"])
    plan = load_json(path)
    if plan.get("status") != (
        "target_free_confirmation_plan_frozen_before_authoritative_validation"
    ):
        raise RuntimeError("direct-v4 confirmation plan is not frozen")
    if plan.get("branch_id") != config["branch_id"]:
        raise RuntimeError("direct-v4 confirmation branch changed")
    if plan.get("config_sha256") != evaluation.sha256_file(config_path):
        raise RuntimeError("direct-v4 config changed after confirmation freeze")
    sources = planner.source_paths(config_path)
    expected_sources = {
        name: evaluation.sha256_file(source)
        for name, source in sorted(sources.items())
    }
    if plan.get("source_sha256") != expected_sources:
        raise RuntimeError("direct-v4 frozen confirmation sources changed")
    if plan.get("counts") != {"test": 24, "protected_sensitivity": 6}:
        raise RuntimeError("direct-v4 confirmation counts changed")
    if plan.get("targets_opened") is not False:
        raise RuntimeError("direct-v4 confirmation plan is not target-free")
    rows = {
        split: [
            {"episode_id": row["episode_id"], "input_sha256": row["input_sha256"]}
            for row in plan["episodes"][split]
        ]
        for split in ("test", "protected_sensitivity")
    }
    expected_locks = {
        "test_lock_sha256": evaluation.canonical_sha256(rows["test"]),
        "sensitivity_lock_sha256": evaluation.canonical_sha256(
            rows["protected_sensitivity"]
        ),
    }
    if any(plan.get(key) != value for key, value in expected_locks.items()):
        raise RuntimeError("direct-v4 protected lock identity changed")
    if any(
        row.get("target_access") != "locked"
        for split in ("test", "protected_sensitivity")
        for row in plan["episodes"][split]
    ):
        raise RuntimeError("direct-v4 confirmation target lock changed")
    return path, plan


def validate_authoritative_validation(
    config: Mapping[str, Any], confirmation_path: Path, plan: Mapping[str, Any]
) -> tuple[Path, dict[str, Any]]:
    path = planner.repo_path(config["validation"]["output"])
    result = load_json(path)
    checks = result.get("checks", {})
    expected = {
        "status": "authoritative_validation_passed_confirmation_unlock_permitted",
        "passed": True,
        "confirmation_targets_opened": False,
        "v1_test_episode_count_used": 0,
        "confirmation_plan_sha256": evaluation.sha256_file(confirmation_path),
        "test_lock_sha256": plan["test_lock_sha256"],
        "sensitivity_lock_sha256": plan["sensitivity_lock_sha256"],
    }
    if any(result.get(key) != value for key, value in expected.items()):
        raise RuntimeError("direct-v4 authoritative validation identity changed")
    if len(checks) != 20 or not all(value is True for value in checks.values()):
        raise RuntimeError("direct-v4 authoritative validation gates are incomplete")
    return path, result


def validate_surfaces(
    config: Mapping[str, Any],
    confirmation_path: Path,
    plan: Mapping[str, Any],
    validation_path: Path,
) -> tuple[Path, Path, dict[str, Any]]:
    qualification_plan_path = surfaces.plan_path(config)
    qualification_plan = load_json(qualification_plan_path)
    expected_plan = {
        "status": "frozen_before_surface_runtime",
        "confirmation_plan_sha256": evaluation.sha256_file(confirmation_path),
        "authoritative_validation_sha256": evaluation.sha256_file(validation_path),
        "test_lock_sha256": plan["test_lock_sha256"],
        "sensitivity_lock_sha256": plan["sensitivity_lock_sha256"],
        "target_generation_permitted": False,
    }
    if any(
        qualification_plan.get(key) != value for key, value in expected_plan.items()
    ):
        raise RuntimeError("direct-v4 surface qualification plan identity changed")
    summary_path = surfaces.summary_path(config)
    summary = load_json(summary_path)
    expected_summary = {
        "status": "passed",
        "all_six_surfaces_qualified": True,
        "joint_unlock_permitted": True,
        "targets_opened": False,
        "qualification_plan_sha256": evaluation.sha256_file(
            qualification_plan_path
        ),
    }
    if any(summary.get(key) != value for key, value in expected_summary.items()):
        raise RuntimeError("direct-v4 surface qualification did not pass closed")
    expected_seeds = {str(seed) for seed in range(5101, 5107)}
    if set(summary.get("surfaces", {})) != expected_seeds:
        raise RuntimeError("direct-v4 qualified surface membership changed")
    for seed in range(5101, 5107):
        recorded = summary["surfaces"][str(seed)]
        current = load_json(
            surfaces.surface_root(config, seed) / "qualification_summary.json"
        )
        if current != recorded or current.get("qualified") is not True:
            raise RuntimeError(f"direct-v4 surface qualification changed: {seed}")
        if not all(value is True for value in current.get("checks", {}).values()):
            raise RuntimeError(f"direct-v4 surface checks are incomplete: {seed}")
    return qualification_plan_path, summary_path, summary


def expected_marker(
    config_path: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    confirmation_path, plan = validate_confirmation(config_path, config)
    validation_path, _validation = validate_authoritative_validation(
        config, confirmation_path, plan
    )
    surface_plan_path, surface_summary_path, _surface_summary = validate_surfaces(
        config, confirmation_path, plan, validation_path
    )
    return {
        "schema_version": 1,
        "branch_id": config["branch_id"],
        "status": STATUS,
        "config_sha256": evaluation.sha256_file(config_path),
        "confirmation_plan_sha256": evaluation.sha256_file(confirmation_path),
        "authoritative_validation_sha256": evaluation.sha256_file(validation_path),
        "surface_qualification_plan_sha256": evaluation.sha256_file(
            surface_plan_path
        ),
        "surface_qualification_summary_sha256": evaluation.sha256_file(
            surface_summary_path
        ),
        "unlock_source_sha256": evaluation.sha256_file(Path(__file__).resolve()),
        "unlock_test_sha256": evaluation.sha256_file(TEST_PATH),
        "episode_manifest_sha256": plan["episode_manifest_sha256"],
        "test_lock_sha256": plan["test_lock_sha256"],
        "sensitivity_lock_sha256": plan["sensitivity_lock_sha256"],
        "counts": {"test": 24, "protected_sensitivity": 6},
        "targets_opened": False,
    }


def write_unlock(config_path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    assert_targets_absent(config)
    marker = expected_marker(config_path, config)
    path = unlock_path(config)
    if path.is_file():
        existing = load_json(path)
        if existing != marker:
            raise RuntimeError("direct-v4 joint unlock identity changed")
        return existing
    evaluation.write_json(path, marker)
    return marker


def require_unlocked(
    config_path: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    path = unlock_path(config)
    if not path.is_file():
        raise RuntimeError("direct-v4 protected target generation remains locked")
    marker = load_json(path)
    if marker != expected_marker(config_path, config):
        raise RuntimeError("direct-v4 joint unlock no longer matches its identity")
    return marker


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = planner.load_config(config_path)
    marker = (
        require_unlocked(config_path, config)
        if args.check
        else write_unlock(config_path, config)
    )
    print(
        json.dumps(
            {
                "path": str(unlock_path(config)),
                "sha256": evaluation.sha256_file(unlock_path(config)),
                "status": marker["status"],
                "targets_opened": marker["targets_opened"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

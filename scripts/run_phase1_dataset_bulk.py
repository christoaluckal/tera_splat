#!/usr/bin/env python3
"""Generate the frozen Phase 1 train/validation dataset without opening test targets."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path
from typing import Any, Mapping

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_fresh_phase0_repeatability as fresh
import run_phase1_dataset as smoke
import run_phase1_screening as screening
from chrono_episode_bridge import load_episode
from phase1_metric_bed import write_common_base_metric_bed
from run_phase1_contract_screen import canonical_sha256, load_contract


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BULK_CONFIG = REPO_ROOT / "configs" / "phase1_dataset_bulk_v1.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_BULK_CONFIG)
    parser.add_argument(
        "--stage",
        choices=("plan", "chrono", "bed", "newton", "analyze", "all"),
        default="plan",
    )
    parser.add_argument("--episode", action="append", default=[])
    return parser.parse_args()


def load_bulk_config(path: Path) -> dict[str, Any]:
    value = json.loads(path.resolve().read_text(encoding="utf-8"))
    if value.get("schema_version") != 1:
        raise ValueError("bulk config schema_version must be 1")
    if value.get("dataset_id") != "phase1_dataset_bulk_v1":
        raise ValueError("unexpected bulk dataset identity")
    membership = value["membership"]
    if int(membership["test"]) != 0:
        raise ValueError("bulk test target generation is prohibited")
    exit_contract = value["bulk_exit"]
    expected = {
        "train": int(exit_contract["required_train_count"]),
        "validation": int(exit_contract["required_validation_count"]),
        "test": int(exit_contract["required_test_count"]),
    }
    actual = {name: int(membership[name]) for name in expected}
    if actual != expected:
        raise ValueError(f"bulk membership does not match its exit contract: {actual}")
    if sum(actual.values()) != int(exit_contract["required_episode_count"]):
        raise ValueError("bulk episode count does not match its exit contract")
    if not bool(exit_contract["require_test_targets_unopened"]):
        raise ValueError("bulk contract must preserve the locked test boundary")
    prior = value["newton_prior"]
    if prior["observation_time_mode"] != "independent_fixed":
        raise ValueError("bulk Newton timing must be independent_fixed")
    if not bool(prior["chrono_target_time_must_not_control_newton_rollout"]):
        raise ValueError("Chrono target time must not control the Newton rollout")
    schema = value["tensor_schema"]
    if not bool(schema["target_arrays_are_never_model_inputs"]):
        raise ValueError("target arrays must be separated from model inputs")
    if "plastic_jacobian" not in schema["excluded_fields"]:
        raise ValueError("audit-rejected plastic state must remain excluded")
    # The frozen smoke implementation supplies the proven runtime and analyzer.
    # Its generic tensor/admission helpers read this key, so expose an in-memory
    # alias without changing the source JSON or the completed smoke runner.
    value["smoke_exit"] = dict(exit_contract)
    return value


def output_root(config: Mapping[str, Any]) -> Path:
    return fresh.repo_path(config["execution"]["output_root"])


def chrono_root(config: Mapping[str, Any]) -> Path:
    return fresh.repo_path(config["execution"]["chrono_output_root"])


def plan_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "bulk_plan.json"


def summary_path(config: Mapping[str, Any]) -> Path:
    return output_root(config) / "bulk_summary.json"


def prerequisite_paths(config: Mapping[str, Any]) -> dict[str, Path]:
    prerequisites = config["prerequisites"]
    paths = {
        "dataset_plan": fresh.repo_path(config["dataset_plan"]),
        "physical_summary": fresh.repo_path(prerequisites["physical_summary"]),
        "latent_summary": fresh.repo_path(prerequisites["latent_summary"]),
        "smoke_summary": fresh.repo_path(prerequisites["smoke_summary"]),
        "phase0_admission_contract": fresh.repo_path(
            "configs/static_proxy_hierarchical_v3_20261017.json"
        ),
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing bulk prerequisites: {missing}")
    return paths


def require_prerequisites(config: Mapping[str, Any]) -> dict[str, Any]:
    paths = prerequisite_paths(config)
    expected = config["prerequisites"]
    physical = json.loads(paths["physical_summary"].read_text(encoding="utf-8"))
    latent = json.loads(paths["latent_summary"].read_text(encoding="utf-8"))
    smoke_summary = json.loads(paths["smoke_summary"].read_text(encoding="utf-8"))
    if physical.get("status") != expected["require_physical_status"]:
        raise RuntimeError("the passing physical screen is required")
    if not bool(physical.get("bulk_dataset_permitted")):
        raise RuntimeError("the physical screen does not permit dataset generation")
    if latent.get("status") != expected["require_latent_status"]:
        raise RuntimeError("the corrected latent qualification must pass")
    qualified = sorted(latent.get("qualified_nonkinematic_families", []))
    if qualified != sorted(expected["qualified_nonkinematic_families"]):
        raise RuntimeError("qualified non-kinematic families changed")
    if smoke_summary.get("status") != expected["require_smoke_status"]:
        raise RuntimeError("the engineering smoke gate must pass")
    if bool(smoke_summary.get("full_dataset_permitted")) is not bool(
        expected["require_smoke_full_dataset_permitted"]
    ):
        raise RuntimeError("the smoke gate does not permit the bulk dataset")
    actual_smoke_sha = fresh.sha256_file(paths["smoke_summary"])
    if actual_smoke_sha != expected["smoke_summary_sha256"]:
        raise RuntimeError("the passing smoke summary hash changed")
    for family in expected["excluded_nonkinematic_families"]:
        if family in qualified:
            raise RuntimeError(f"excluded latent family became qualified: {family}")
    return {"physical": physical, "latent": latent, "smoke": smoke_summary}


def selected_episodes(
    config: Mapping[str, Any], dataset_plan: Mapping[str, Any]
) -> list[dict[str, Any]]:
    episodes = [
        dict(episode)
        for split in ("train", "validation")
        for episode in dataset_plan["episodes"][split]
    ]
    if any(item["split"] == "test" or item["target_access"] == "locked" for item in episodes):
        raise ValueError("bulk train/validation selection crossed the test lock")
    counts = {
        "train": sum(item["split"] == "train" for item in episodes),
        "validation": sum(item["split"] == "validation" for item in episodes),
    }
    membership = config["membership"]
    if counts != {
        "train": int(membership["train"]),
        "validation": int(membership["validation"]),
    }:
        raise ValueError(f"frozen bulk split counts changed: {counts}")
    expected_seeds = sorted(int(x) for x in config["bulk_exit"]["required_surface_seeds"])
    actual_seeds = sorted({int(item["initial_surface_seed"]) for item in episodes})
    if actual_seeds != expected_seeds:
        raise ValueError(f"bulk surface coverage changed: {actual_seeds}")
    return episodes


def locked_test_episodes(dataset_plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    episodes = [dict(item) for item in dataset_plan["episodes"]["test"]]
    if not episodes or any(item["target_access"] != "locked" for item in episodes):
        raise ValueError("the frozen test identity lock is invalid")
    expected = canonical_sha256(
        [
            {"episode_id": item["episode_id"], "input_sha256": item["input_sha256"]}
            for item in episodes
        ]
    )
    if dataset_plan["test_lock_sha256"] != expected:
        raise ValueError("the frozen test identity hash changed")
    return episodes


def assert_test_targets_absent(
    config: Mapping[str, Any], dataset_plan: Mapping[str, Any]
) -> None:
    present: list[str] = []
    for episode in locked_test_episodes(dataset_plan):
        episode_id = episode["episode_id"]
        for path in (
            chrono_root(config) / episode_id,
            output_root(config) / "episodes" / episode_id,
        ):
            if path.exists():
                present.append(str(path))
    if present:
        raise RuntimeError(f"locked test target artifacts are present: {present}")


def source_paths(
    config_path: Path, config: Mapping[str, Any], contract: Mapping[str, Any]
) -> dict[str, Path]:
    shared = smoke.source_paths(config_path, config, contract)
    paths = {
        "bulk_config": config_path.resolve(),
        "bulk_runner": Path(__file__).resolve(),
        "bulk_tests": REPO_ROOT / "tests" / "test_phase1_dataset_bulk.py",
        **{f"shared_{name}": path for name, path in shared.items()},
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing bulk sources: {missing}")
    return paths


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
    if canonical_sha256(dataset_plan["episodes"]) != dataset_plan["episode_manifest_sha256"]:
        raise RuntimeError("the frozen 88-episode manifest payload changed")
    assert_test_targets_absent(config, dataset_plan)
    episodes = selected_episodes(config, dataset_plan)
    surface_inputs: dict[str, str] = {}
    for seed in sorted({int(item["initial_surface_seed"]) for item in episodes}):
        root = screening.surface_dir(contract, seed)
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
        "status": "frozen_before_first_bulk_target",
        "config_sha256": fresh.sha256_file(config_path),
        "phase1_contract_sha256": fresh.sha256_file(contract_path),
        "dataset_plan_sha256": fresh.sha256_file(paths["dataset_plan"]),
        "episode_manifest_sha256": dataset_plan["episode_manifest_sha256"],
        "test_lock_sha256": dataset_plan["test_lock_sha256"],
        "selected_episode_manifest_sha256": canonical_sha256(episodes),
        "source_sha256": {name: fresh.sha256_file(path) for name, path in sources.items()},
        "input_sha256": {
            **{name: fresh.sha256_file(path) for name, path in paths.items()},
            **surface_inputs,
        },
        "environment": smoke.environment_probe(config, contract),
        "captured_by_python": platform.python_version(),
        "repository_revisions": {
            "tera_splat": fresh.command_output(["git", "rev-parse", "HEAD"], REPO_ROOT),
            "tera_splat_sim": fresh.command_output(
                ["git", "rev-parse", "HEAD"], fresh.repo_path(contract["chrono"]["repo"])
            ),
        },
        "episodes": episodes,
        "counts": {"train": 48, "validation": 16, "test": 0},
        "surface_seeds": sorted({int(item["initial_surface_seed"]) for item in episodes}),
        "qualified_nonkinematic_families": prerequisites["latent"][
            "qualified_nonkinematic_families"
        ],
        "excluded_nonkinematic_families": config["prerequisites"][
            "excluded_nonkinematic_families"
        ],
        "newton_prior": config["newton_prior"],
        "tensor_schema": config["tensor_schema"],
        "test_policy": {
            "identities_frozen": 24,
            "targets_opened": False,
            "generation_permitted_by_this_runner": False,
        },
    }


STABLE_PLAN_KEYS = (
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
    "test_policy",
)


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
        changed = [key for key in STABLE_PLAN_KEYS if existing.get(key) != plan.get(key)]
        if changed:
            raise RuntimeError(f"refusing to replace a different bulk plan: {changed}")
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
        raise RuntimeError("bulk plan is missing; run --stage plan first")
    existing = json.loads(path.read_text(encoding="utf-8"))
    current = build_plan(config_path, config, contract_path, contract)
    changed = [key for key in STABLE_PLAN_KEYS if existing.get(key) != current.get(key)]
    if changed:
        raise RuntimeError(f"bulk plan identity changed: {changed}")
    return existing


def choose_episodes(plan: Mapping[str, Any], requested: list[str]) -> list[dict[str, Any]]:
    episodes = list(plan["episodes"])
    by_id = {item["episode_id"]: item for item in episodes}
    unknown = sorted(set(requested) - set(by_id))
    if unknown:
        raise ValueError(f"unknown bulk episodes: {unknown}")
    return [by_id[name] for name in requested] if requested else episodes


def build_bed(
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    plan: Mapping[str, Any],
    surface_seed: int,
) -> Path:
    root = smoke.prior_root(config, surface_seed)
    output = root / "metric_bed"
    expected = output / "particles_initial_mpm.ply", output / "ground_plane_metadata.json"
    if all(path.is_file() for path in expected):
        return output
    if output.exists():
        raise RuntimeError(f"refusing incomplete bulk metric bed: {output}")
    episode = smoke.reference_episode_for_seed(plan, surface_seed)
    if not smoke.chrono_result(config, contract, episode).get("accepted"):
        raise RuntimeError("accepted Chrono episode required before metric-bed build")
    chrono_dir = smoke.chrono_episode(config, episode["episode_id"])
    manifest, _action, initial, _valid = load_episode(chrono_dir)
    builder_contract = json.loads(
        fresh.repo_path(config["newton_prior"]["builder_contract"]).read_text(encoding="utf-8")
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
        "bulk_plan_sha256": fresh.sha256_file(plan_path(config)),
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
    root = smoke.prior_root(config, surface_seed)
    preparation = root / "preparation"
    manifest_path = preparation / "newton_prepared_bed_manifest.json"
    if manifest_path.is_file():
        prepared = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not bool(prepared.get("accepted")):
            raise RuntimeError(f"existing preparation rejected for surface {surface_seed}")
        return preparation
    if preparation.exists():
        raise RuntimeError(f"refusing incomplete bulk preparation: {preparation}")
    episode = smoke.reference_episode_for_seed(plan, surface_seed)
    newton = contract["newton"]
    fresh.run_logged(
        [
            str(Path(config["execution"]["newton_python"]).resolve()),
            str(SCRIPT_DIR / "run_newton_prepared_bed.py"),
            "--config", str(fresh.repo_path(newton["base_config"])),
            "--particles-ply", str(bed / "particles_initial_mpm.ply"),
            "--metadata-json", str(bed / "ground_plane_metadata.json"),
            "--chrono-episode", str(smoke.chrono_episode(config, episode["episode_id"])),
            "--output-dir", str(preparation),
            "--device", str(config["execution"]["device"]),
            "--dt-s", str(newton["selected_dt_s"]),
            "--duration-s", str(newton["pre_settle_duration_s"]),
            "--required-duration-s", str(newton["pre_settle_required_duration_s"]),
            "--particle-speed-threshold-mps", str(newton["particle_speed_threshold_mps"]),
            "--center-crop-half-width-m", "0",
            "--speed-check-every", "1",
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
    preparation = prepare_prior(config, contract, plan, int(episode["initial_surface_seed"]))
    response = smoke.response_root(config, episode["episode_id"])
    manifest_path = response / "newton_cylinder_manifest.json"
    if manifest_path.is_file():
        return response
    if response.exists():
        raise RuntimeError(f"refusing incomplete bulk Newton response: {response}")
    newton = contract["newton"]
    prior = config["newton_prior"]
    fresh.run_logged(
        [
            str(Path(config["execution"]["newton_python"]).resolve()),
            str(SCRIPT_DIR / "run_newton_cylinder_diagnostic.py"),
            "--config", str(fresh.repo_path(newton["base_config"])),
            "--prepared-dir", str(preparation),
            "--candidate-preparation",
            "--chrono-episode", str(smoke.chrono_episode(config, episode["episode_id"])),
            "--output-dir", str(response),
            "--device", str(config["execution"]["device"]),
            "--dt-s", str(newton["selected_dt_s"]),
            "--pre-settle-duration-s", str(newton["pre_settle_duration_s"]),
            "--pre-settle-required-duration-s", str(newton["pre_settle_required_duration_s"]),
            "--particle-speed-threshold-mps", str(newton["particle_speed_threshold_mps"]),
            "--observation-time-mode", str(prior["observation_time_mode"]),
            "--loaded-duration-s", str(prior["loaded_duration_s"]),
            "--residual-duration-s", str(prior["post_unload_duration_s"]),
            "--proxy-iterations", str(newton["proxy_iterations"]),
            "--rigid-substeps", str(newton["rigid_substeps"]),
            "--cylinder-friction-coefficient", str(newton["cylinder_friction_coefficient"]),
            "--cylinder-collider-mode", str(newton["collider_mode"]),
            "--cylinder-collider-segments", str(newton["collider_segments"]),
            "--cylinder-collision-guard-m", str(newton["collision_guard_m"]),
            "--cylinder-collision-bottom-inset-m", "0",
            "--cylinder-projection-threshold-m", str(newton["projection_threshold_m"]),
        ],
        smoke.episode_root(config, episode["episode_id"]) / "logs" / "newton_response.log",
        REPO_ROOT,
    )
    return response


def summarize(
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    dataset_plan = json.loads(
        fresh.repo_path(config["dataset_plan"]).read_text(encoding="utf-8")
    )
    assert_test_targets_absent(config, dataset_plan)
    episodes = [smoke.analyze_episode(config, contract, item) for item in plan["episodes"]]
    exit_contract = config["bulk_exit"]
    counts = {
        "total": len(episodes),
        "train": sum(item["split"] == "train" for item in episodes),
        "validation": sum(item["split"] == "validation" for item in episodes),
        "test": sum(item["split"] == "test" for item in episodes),
    }
    checks = {
        "episode_count": counts["total"] == int(exit_contract["required_episode_count"]),
        "train_count": counts["train"] == int(exit_contract["required_train_count"]),
        "validation_count": counts["validation"] == int(exit_contract["required_validation_count"]),
        "test_count": counts["test"] == int(exit_contract["required_test_count"]),
        "test_targets_unopened": True,
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
        "training_dataset_ready": passed,
        "counts": counts,
        "checks": checks,
        "qualified_nonkinematic_families": plan["qualified_nonkinematic_families"],
        "excluded_nonkinematic_families": plan["excluded_nonkinematic_families"],
        "identity": {
            "bulk_plan_sha256": fresh.sha256_file(plan_path(config)),
            "selected_episode_manifest_sha256": plan["selected_episode_manifest_sha256"],
            "episode_manifest_sha256": plan["episode_manifest_sha256"],
            "test_lock_sha256": plan["test_lock_sha256"],
        },
        "test_policy": plan["test_policy"],
        "episodes": {item["episode_id"]: item for item in episodes},
    }
    fresh.write_json(summary_path(config), summary)
    return summary


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = load_bulk_config(config_path)
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
            smoke.run_chrono(config, contract, episode)
    if args.stage in ("bed", "all"):
        for seed in sorted({int(item["initial_surface_seed"]) for item in episodes}):
            build_bed(config, contract, plan, seed)
    if args.stage in ("newton", "all"):
        for episode in episodes:
            run_newton(config, contract, plan, episode)
    if args.stage in ("analyze", "all"):
        for episode in episodes:
            smoke.analyze_episode(config, contract, episode)
    summary = summarize(config, contract, plan)
    print(
        json.dumps(
            {
                "status": summary["status"],
                "training_dataset_ready": summary["training_dataset_ready"],
                "counts": summary["counts"],
                "checks": summary["checks"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

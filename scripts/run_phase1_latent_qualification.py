#!/usr/bin/env python3
"""Freeze, execute, and analyze Phase 1 Newton latent qualification repeats."""

from __future__ import annotations

import argparse
import csv
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
from newton_contract import particle_mass_kg
from phase1_latent_fields import (
    CHECKPOINTS,
    FIELD_SEMANTICS,
    contact_column_fields,
    load_state_archive,
    particle_column_fields,
    qualify_nonkinematic_families,
    repeat_field_evidence,
    triplet_field_evidence,
)
from run_phase1_contract_screen import load_contract as load_phase1_contract


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "phase1_latent_export_v3.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--stage", choices=("plan", "run", "analyze", "all"), default="plan"
    )
    parser.add_argument("--repeat", type=int, action="append", default=[])
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.resolve().read_text(encoding="utf-8"))
    if config.get("schema_version") != 1:
        raise ValueError("latent qualification schema_version must be 1")
    if config.get("qualification_id") != "phase1_latent_export_v3":
        raise ValueError("unexpected latent qualification identity")
    if config.get("status") != "frozen_before_runtime_qualification":
        raise ValueError("latent qualification contract is not frozen")
    if int(config["execution"]["independent_fresh_process_repeats"]) < 3:
        raise ValueError("latent qualification requires at least three repeats")
    return config


def phase1_contract(config: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    path = fresh.repo_path(config["phase1_contract"])
    return path, load_phase1_contract(path)


def raw_root(config: dict[str, Any]) -> Path:
    return fresh.repo_path(config["execution"]["raw_output_root"])


def report_root(config: dict[str, Any]) -> Path:
    return fresh.repo_path(config["execution"]["tracked_report_root"])


def plan_path(config: dict[str, Any]) -> Path:
    return raw_root(config) / "qualification_plan.json"


def chrono_episode(contract: dict[str, Any], case_id: str) -> Path:
    return (
        fresh.repo_path(contract["chrono"]["output_root"])
        / "screening"
        / "material"
        / case_id
    )


def screening_summary_path(config: dict[str, Any]) -> Path:
    return fresh.repo_path(config["physical_screen"]["qualification_summary"])


def prepared_dir(config: dict[str, Any]) -> Path:
    return fresh.repo_path(config["physical_screen"]["prepared_dir"])


def source_paths(
    config_path: Path, config: dict[str, Any], contract_path: Path, contract: dict[str, Any]
) -> dict[str, Path]:
    return {
        "latent_contract": config_path.resolve(),
        "phase1_contract": contract_path.resolve(),
        "qualification_runner": Path(__file__).resolve(),
        "latent_fields": SCRIPT_DIR / "phase1_latent_fields.py",
        "newton_response": SCRIPT_DIR / "run_newton_cylinder_diagnostic.py",
        "newton_preparation": SCRIPT_DIR / "run_newton_prepared_bed.py",
        "newton_contract": SCRIPT_DIR / "newton_contract.py",
        "newton_base_config": fresh.repo_path(contract["newton"]["base_config"]),
    }


def input_paths(
    config: dict[str, Any], contract: dict[str, Any], case_id: str
) -> dict[str, Path]:
    episode = chrono_episode(contract, case_id)
    preparation = prepared_dir(config)
    preparation_manifest = preparation / "newton_prepared_bed_manifest.json"
    paths = {
        "physical_screen_plan": fresh.repo_path(
            config["physical_screen"]["qualification_plan"]
        ),
        "physical_screen_summary": screening_summary_path(config),
        "physical_screen_case_summary": fresh.repo_path(
            config["physical_screen"]["case_summary"]
        ),
        "chrono_manifest": episode / "manifest.yaml",
        "chrono_action": episode / "action.json",
        "chrono_initial": episode / "initial_heightmap_m.npy",
        "chrono_loaded": episode / "loaded_heightmap_m.npy",
        "chrono_post_unload": episode / "residual_heightmap_m.npy",
        "chrono_valid_mask": episode / "valid_heightmap_mask.npy",
        "preparation_manifest": preparation_manifest,
    }
    if preparation_manifest.is_file():
        manifest = json.loads(preparation_manifest.read_text(encoding="utf-8"))
        paths["metric_bed_particles"] = Path(manifest["source"]["particles_ply"]).resolve()
        paths["metric_bed_metadata"] = Path(manifest["source"]["metadata_json"]).resolve()
    return paths


def _require_files(paths: dict[str, Path], label: str) -> None:
    missing = [f"{name}: {path}" for name, path in paths.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing {label}: {missing}")


def build_plan(
    config_path: Path, config: dict[str, Any], contract_path: Path, contract: dict[str, Any]
) -> dict[str, Any]:
    summary_path = screening_summary_path(config)
    if not summary_path.is_file():
        raise RuntimeError("material screening summary is missing")
    screen = json.loads(summary_path.read_text(encoding="utf-8"))
    if not (
        screen.get("status") == "passed"
        and screen.get("all_five_pairings_admitted")
        and screen.get("bulk_dataset_permitted")
    ):
        raise RuntimeError("latent qualification is blocked until material screening passes")
    case = config["source_case"]
    case_id = str(case["case_id"])
    case_summary_path = fresh.repo_path(config["physical_screen"]["case_summary"])
    if not case_summary_path.is_file():
        raise RuntimeError("reference material case summary is missing")
    case_summary = json.loads(case_summary_path.read_text(encoding="utf-8"))
    if not bool(case_summary.get("pipeline_usable")):
        raise RuntimeError("reference material case is not pipeline-usable")
    sources = source_paths(config_path, config, contract_path, contract)
    inputs = input_paths(config, contract, case_id)
    _require_files(sources, "qualification sources")
    _require_files(inputs, "qualification inputs")
    python = Path(config["execution"]["newton_python"]).resolve()
    environment_text = fresh.command_output(
        [
            str(python),
            "-c",
            (
                "import json,platform,numpy,newton,warp; "
                "print(json.dumps({'python':platform.python_version(),"
                "'numpy':numpy.__version__,'newton':newton.__version__,"
                "'warp':warp.__version__}))"
            ),
        ],
        REPO_ROOT,
    )
    environment = json.loads(environment_text.splitlines()[-1])
    return {
        "schema_version": 1,
        "qualification_id": config["qualification_id"],
        "status": "runtime_not_started",
        "latent_contract_sha256": fresh.sha256_file(config_path),
        "phase1_contract_sha256": fresh.sha256_file(contract_path),
        "screening_summary_sha256": fresh.sha256_file(summary_path),
        "source_sha256": {name: fresh.sha256_file(path) for name, path in sources.items()},
        "input_sha256": {name: fresh.sha256_file(path) for name, path in inputs.items()},
        "source_case": case,
        "repeat_count": int(config["execution"]["independent_fresh_process_repeats"]),
        "environment": environment,
        "device": config["execution"]["device"],
        "repository": {
            "revision": fresh.command_output(["git", "rev-parse", "HEAD"], REPO_ROOT),
            "branch": fresh.command_output(["git", "branch", "--show-current"], REPO_ROOT),
            "status_short": fresh.command_output(["git", "status", "--short"], REPO_ROOT).splitlines(),
        },
    }


def write_plan(
    config_path: Path, config: dict[str, Any], contract_path: Path, contract: dict[str, Any]
) -> dict[str, Any]:
    plan = build_plan(config_path, config, contract_path, contract)
    path = plan_path(config)
    if path.is_file():
        existing = json.loads(path.read_text(encoding="utf-8"))
        stable = (
            "latent_contract_sha256",
            "phase1_contract_sha256",
            "screening_summary_sha256",
            "source_sha256",
            "input_sha256",
            "environment",
            "device",
        )
        if any(existing.get(name) != plan.get(name) for name in stable):
            raise RuntimeError(f"refusing to replace a different qualification plan: {path}")
        return existing
    fresh.write_json(path, plan)
    return plan


def load_plan(
    config_path: Path, config: dict[str, Any], contract_path: Path, contract: dict[str, Any]
) -> dict[str, Any]:
    path = plan_path(config)
    if not path.is_file():
        raise RuntimeError("qualification plan is missing; run --stage plan first")
    plan = json.loads(path.read_text(encoding="utf-8"))
    current = build_plan(config_path, config, contract_path, contract)
    stable = (
        "latent_contract_sha256",
        "phase1_contract_sha256",
        "screening_summary_sha256",
        "source_sha256",
        "input_sha256",
        "environment",
        "device",
    )
    changed = [name for name in stable if plan.get(name) != current.get(name)]
    if changed:
        raise RuntimeError(f"qualification plan identity changed: {changed}")
    return plan


def response_command(
    config: dict[str, Any], contract: dict[str, Any], case_id: str, output: Path
) -> list[str]:
    newton = contract["newton"]
    root = prepared_dir(config)
    timing = config["observation_time_contract"]
    return [
        str(Path(config["execution"]["newton_python"]).resolve()),
        str(SCRIPT_DIR / "run_newton_cylinder_diagnostic.py"),
        "--config", str(fresh.repo_path(newton["base_config"])),
        "--prepared-dir", str(root),
        "--candidate-preparation",
        "--chrono-episode", str(chrono_episode(contract, case_id)),
        "--output-dir", str(output),
        "--device", str(config["execution"]["device"]),
        "--dt-s", str(newton["selected_dt_s"]),
        "--pre-settle-duration-s", str(newton["pre_settle_duration_s"]),
        "--pre-settle-required-duration-s", str(newton["pre_settle_required_duration_s"]),
        "--particle-speed-threshold-mps", str(newton["particle_speed_threshold_mps"]),
        "--observation-time-mode", str(timing["newton_mode"]),
        "--loaded-duration-s", str(timing["loaded_duration_s"]),
        "--residual-duration-s", str(timing["post_unload_duration_s"]),
        "--proxy-iterations", str(newton["proxy_iterations"]),
        "--rigid-substeps", str(newton["rigid_substeps"]),
        "--cylinder-friction-coefficient", str(newton["cylinder_friction_coefficient"]),
        "--cylinder-collider-mode", str(newton["collider_mode"]),
        "--cylinder-collider-segments", str(newton["collider_segments"]),
        "--cylinder-collision-guard-m", str(newton["collision_guard_m"]),
        "--cylinder-collision-bottom-inset-m", "0",
        "--cylinder-projection-threshold-m", str(newton["projection_threshold_m"]),
    ]


def repeat_dir(config: dict[str, Any], index: int) -> Path:
    return raw_root(config) / f"repeat_{index:02d}"


def validate_repeat(path: Path) -> dict[str, Any]:
    response = path / "response"
    manifest_path = response / "newton_cylinder_manifest.json"
    if not manifest_path.is_file():
        return {"complete": False, "response": str(response)}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    archives = {}
    for checkpoint, filename in {
        "initial": "newton_state_initial.npz",
        "loaded": "newton_state_loaded.npz",
        "post_unload": "newton_state_residual.npz",
    }.items():
        state = load_state_archive(response / filename)
        if int(state["schema_version"]) != 2:
            raise RuntimeError(f"{checkpoint} state does not use repaired schema v2")
        for required in ("contact_position_m", "contact_impulse_ns"):
            if required not in state:
                raise RuntimeError(f"{checkpoint} state lacks {required}")
        archives[checkpoint] = filename
    checks = {
        "finite": bool(manifest["finite"]),
        "guide": bool(manifest["cylinder"]["guide_constraint_passed"]),
        "preparation": bool(manifest["preparation"]["convergence_passed"]),
        "schema_v2": True,
    }
    return {
        "complete": True,
        "accepted_for_latent_analysis": all(checks.values()),
        "checks": checks,
        "response": str(response.resolve()),
        "archives": archives,
    }


def run_repeats(
    config: dict[str, Any], contract: dict[str, Any], plan: dict[str, Any], requested: list[int]
) -> list[dict[str, Any]]:
    total = int(plan["repeat_count"])
    indices = requested or list(range(1, total + 1))
    if any(index < 1 or index > total for index in indices):
        raise ValueError(f"repeat indices must be in [1, {total}]")
    case_id = str(config["source_case"]["case_id"])
    results = []
    for index in indices:
        root = repeat_dir(config, index)
        existing = validate_repeat(root) if root.exists() else {"complete": False}
        if existing.get("complete"):
            results.append(existing)
            continue
        if root.exists():
            raise RuntimeError(f"refusing incomplete latent repeat directory: {root}")
        output = root / "response"
        fresh.run_logged(
            response_command(config, contract, case_id, output),
            root / "newton_response.log",
            REPO_ROOT,
        )
        result = validate_repeat(root)
        if not result.get("accepted_for_latent_analysis"):
            raise RuntimeError(f"latent repeat failed integrity checks: {index}")
        results.append(result)
    return results


def load_repeat_states(config: dict[str, Any], index: int) -> dict[str, dict[str, np.ndarray]]:
    response = repeat_dir(config, index) / "response"
    return {
        "initial": load_state_archive(response / "newton_state_initial.npz"),
        "loaded": load_state_archive(response / "newton_state_loaded.npz"),
        "post_unload": load_state_archive(response / "newton_state_residual.npz"),
    }


def grid_coordinates(manifest: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    heightmap = manifest["heightmap"]
    rows, columns = (int(value) for value in heightmap["shape"])
    x0, y0 = (float(value) for value in heightmap["origin_xy_m"])
    spacing = float(heightmap["spacing_m"])
    return x0 + spacing * np.arange(columns), y0 + spacing * np.arange(rows)


def box_mean_2d(values: np.ndarray, width: int) -> np.ndarray:
    """Apply a deterministic odd-width edge-padded 2D box mean."""
    array = np.asarray(values, dtype=np.float64)
    size = int(width)
    if array.ndim != 2:
        raise ValueError("box mean input must be two-dimensional")
    if size < 1 or size % 2 == 0:
        raise ValueError("box mean width must be a positive odd integer")
    radius = size // 2
    padded = np.pad(array, radius, mode="edge")
    result = np.zeros_like(array)
    for row in range(size):
        for column in range(size):
            result += padded[
                row : row + array.shape[0], column : column + array.shape[1]
            ]
    return result / float(size * size)


def grid_field_evidence(
    runs: list[dict[str, dict[str, np.ndarray]]],
    *,
    local_mask: np.ndarray,
) -> dict[str, dict[str, Any]]:
    """Measure checkpoint signal and repeat stability for declared grid fields."""
    if len(runs) < 2:
        raise ValueError("grid evidence requires at least two runs")
    if any(set(run) != set(CHECKPOINTS) for run in runs):
        raise ValueError(f"grid runs must contain exactly {CHECKPOINTS}")
    fields = set(runs[0]["initial"])
    if any(set(state) != fields for run in runs for state in run.values()):
        raise ValueError("grid field sets differ across checkpoints or repeats")
    mask = np.asarray(local_mask, dtype=bool)
    evidence: dict[str, dict[str, Any]] = {}
    for field in sorted(fields):
        values = [
            {
                checkpoint: np.asarray(run[checkpoint][field], dtype=np.float64)[mask]
                for checkpoint in CHECKPOINTS
            }
            for run in runs
        ]
        if any(not np.isfinite(value).all() for run in values for value in run.values()):
            raise ValueError(f"grid field {field} contains non-finite values")
        checkpoint_rms = {
            "initial_to_loaded": float(
                np.sqrt(np.mean((values[0]["initial"] - values[0]["loaded"]) ** 2))
            ),
            "initial_to_post_unload": float(
                np.sqrt(
                    np.mean(
                        (values[0]["initial"] - values[0]["post_unload"]) ** 2
                    )
                )
            ),
            "loaded_to_post_unload": float(
                np.sqrt(
                    np.mean(
                        (values[0]["loaded"] - values[0]["post_unload"]) ** 2
                    )
                )
            ),
        }
        repeat_rms: list[float] = []
        repeat_correlation: list[float] = []
        for left in range(len(values)):
            for right in range(left + 1, len(values)):
                for checkpoint in CHECKPOINTS:
                    lhs = values[left][checkpoint].reshape(-1)
                    rhs = values[right][checkpoint].reshape(-1)
                    repeat_rms.append(float(np.sqrt(np.mean((lhs - rhs) ** 2))))
                    if np.array_equal(lhs, rhs):
                        repeat_correlation.append(1.0)
                    else:
                        lhs_centered = lhs - np.mean(lhs)
                        rhs_centered = rhs - np.mean(rhs)
                        denominator = float(
                            np.linalg.norm(lhs_centered) * np.linalg.norm(rhs_centered)
                        )
                        repeat_correlation.append(
                            float(np.dot(lhs_centered, rhs_centered) / denominator)
                            if denominator > 0.0
                            else 0.0
                        )
        signal = max(checkpoint_rms.values())
        maximum_repeat_rms = max(repeat_rms)
        evidence[field] = {
            "pairwise_checkpoint_rms_change": checkpoint_rms,
            "maximum_checkpoint_rms_change": signal,
            "maximum_pairwise_repeat_rms": maximum_repeat_rms,
            "repeat_rms_over_action_signal": (
                maximum_repeat_rms / signal if signal > 0.0 else None
            ),
            "minimum_pairwise_repeat_pearson": min(repeat_correlation),
        }
    return evidence


def apply_plastic_plausibility_gate(
    families: dict[str, Any],
    triplet: dict[str, Any],
    config: dict[str, Any],
) -> float:
    """Reject plastic state inconsistent with the selected elastic material."""
    spec = config["candidate_nonkinematic_families"]["plastic"]
    extrema = [
        float(stats[bound])
        for stats in triplet["fields"]["plastic_jacobian"]["checkpoint"].values()
        for bound in ("minimum", "maximum")
    ]
    maximum_abs_log = (
        max(abs(np.log(value)) for value in extrema)
        if all(value > 0.0 for value in extrema)
        else float("inf")
    )
    passed = bool(
        maximum_abs_log <= float(spec["maximum_absolute_log_jacobian"])
    )
    families["plastic"]["checks"]["plastic_constitutive_plausibility"] = passed
    families["plastic"]["qualified"] = all(
        families["plastic"]["checks"].values()
    )
    return maximum_abs_log


def analyze(
    config: dict[str, Any], contract: dict[str, Any], plan: dict[str, Any]
) -> dict[str, Any]:
    repeats = [
        load_repeat_states(config, index)
        for index in range(1, int(plan["repeat_count"]) + 1)
    ]
    case_id = str(config["source_case"]["case_id"])
    episode = chrono_episode(contract, case_id)
    chrono_manifest = yaml.safe_load((episode / "manifest.yaml").read_text(encoding="utf-8"))
    action = json.loads((episode / "action.json").read_text(encoding="utf-8"))
    scope = config["spatial_scope"]
    triplet = triplet_field_evidence(
        repeats[0],
        center_xy_m=action["center_xy_m"],
        radius_m=float(action["radius_m"]),
        radius_multiplier=float(scope["local_crop_radius_multiplier"]),
        minimum_local_particles=int(scope["minimum_local_particles"]),
    )
    action_signal = {
        field: float(evidence["maximum_pairwise_checkpoint_rms_change"])
        for field, evidence in triplet["fields"].items()
    }
    repeat = repeat_field_evidence(
        repeats,
        local_mask=triplet["local_particle_mask"],
        action_signal=action_signal,
    )
    families = qualify_nonkinematic_families(triplet, repeat, config)
    plastic_maximum_abs_log_jacobian = apply_plastic_plausibility_gate(
        families, triplet, config
    )

    xs, ys = grid_coordinates(chrono_manifest)
    spacing = float(contract["newton"]["metric_bed_source"]["particle_spacing_m"])
    newton_config = json.loads(
        fresh.repo_path(contract["newton"]["base_config"]).read_text(encoding="utf-8")
    )
    mass = particle_mass_kg(float(newton_config["material"]["density_kg_m3"]), spacing)
    column_runs = [
        {
            checkpoint: particle_column_fields(
                run[checkpoint],
                x_coordinates_m=xs,
                y_coordinates_m=ys,
                particle_mass_kg=mass,
            )
            for checkpoint in CHECKPOINTS
        }
        for run in repeats
    ]
    contact_runs = [
        {
            checkpoint: contact_column_fields(
                run[checkpoint]["contact_position_m"],
                run[checkpoint]["contact_impulse_ns"],
                x_coordinates_m=xs,
                y_coordinates_m=ys,
            )
            for checkpoint in CHECKPOINTS
        }
        for run in repeats
    ]
    columns = column_runs[0]
    contact_columns = contact_runs[0]
    expected_count = repeats[0]["initial"]["position_m"].shape[0]
    expected_mass = float(expected_count * mass)
    mass_errors = {
        f"repeat_{repeat_index:02d}_{checkpoint}": abs(
            float(np.sum(values["column_mass_kg"])) - expected_mass
        )
        / expected_mass
        for repeat_index, run in enumerate(column_runs, start=1)
        for checkpoint, values in run.items()
    }
    required = config["required_families"]
    grid_x, grid_y = np.meshgrid(xs, ys)
    grid_local = np.hypot(
        grid_x - float(action["center_xy_m"][0]),
        grid_y - float(action["center_xy_m"][1]),
    ) <= float(action["radius_m"]) * float(scope["local_crop_radius_multiplier"])
    velocity_width = int(required["velocity"]["box_mean_width_cells"])
    velocity_grid_runs = [
        {
            checkpoint: {
                "column_mean_action_velocity_mps": box_mean_2d(
                    run[checkpoint]["column_mean_velocity_xyz_mps"][..., 2],
                    velocity_width,
                )
            }
            for checkpoint in CHECKPOINTS
        }
        for run in column_runs
    ]
    contact_grid_runs = [
        {
            checkpoint: {
                "contact_node_count": run[checkpoint]["contact_node_count"],
                "contact_normal_impulse_ns": run[checkpoint][
                    "contact_normal_impulse_ns"
                ],
            }
            for checkpoint in CHECKPOINTS
        }
        for run in contact_runs
    ]
    velocity_evidence = grid_field_evidence(
        velocity_grid_runs, local_mask=grid_local
    )["column_mean_action_velocity_mps"]
    contact_evidence = grid_field_evidence(
        contact_grid_runs, local_mask=grid_local
    )
    loaded_velocity = velocity_grid_runs[0]["loaded"][
        "column_mean_action_velocity_mps"
    ][grid_local]
    initial_velocity = velocity_grid_runs[0]["initial"][
        "column_mean_action_velocity_mps"
    ][grid_local]
    velocity_span = float(
        np.percentile(loaded_velocity, 95) - np.percentile(loaded_velocity, 5)
    )
    velocity_change = float(
        np.sqrt(np.mean((loaded_velocity - initial_velocity) ** 2))
    )
    repeat_contract = config["repeatability"]
    maximum_ratio = float(repeat_contract["maximum_repeat_rms_over_action_signal"])
    minimum_correlation = float(
        repeat_contract["minimum_repeat_pearson_correlation"]
    )
    velocity_ratio = velocity_evidence["repeat_rms_over_action_signal"]
    contact_ratio_checks = {
        name: evidence["repeat_rms_over_action_signal"] is not None
        and float(evidence["repeat_rms_over_action_signal"]) <= maximum_ratio
        for name, evidence in contact_evidence.items()
    }
    contact_correlation_checks = {
        name: float(evidence["minimum_pairwise_repeat_pearson"])
        >= minimum_correlation
        for name, evidence in contact_evidence.items()
    }
    required_checks = {
        "occupancy_count_conserved": all(
            int(np.sum(values["column_particle_count"])) == expected_count
            for run in column_runs
            for values in run.values()
        ),
        "mass_conserved": max(mass_errors.values())
        <= float(required["occupancy_mass"]["mass_conservation_relative_tolerance"]),
        "velocity_nonconstant": velocity_span
        >= float(required["velocity"]["minimum_loaded_local_robust_span_mps"]),
        "velocity_checkpoint_change": velocity_change
        >= float(required["velocity"]["minimum_loaded_vs_initial_local_rms_mps"]),
        "velocity_repeat_ratio": velocity_ratio is not None
        and float(velocity_ratio) <= maximum_ratio,
        "velocity_repeat_correlation": float(
            velocity_evidence["minimum_pairwise_repeat_pearson"]
        )
        >= minimum_correlation,
        "loaded_contact_nodes": int(np.sum(contact_columns["loaded"]["contact_node_count"]))
        >= int(required["contact"]["minimum_loaded_impulse_nodes"]),
        "loaded_contact_impulse": float(np.sum(contact_columns["loaded"]["contact_normal_impulse_ns"]))
        >= float(required["contact"]["minimum_loaded_total_upward_impulse_ns"]),
        "initial_contact_zero": int(np.sum(contact_columns["initial"]["contact_node_count"])) == 0,
        "post_unload_contact_zero": int(np.sum(contact_columns["post_unload"]["contact_node_count"])) == 0,
        "contact_count_repeat_ratio": contact_ratio_checks["contact_node_count"],
        "contact_count_repeat_correlation": contact_correlation_checks[
            "contact_node_count"
        ],
        "contact_impulse_repeat_ratio": contact_ratio_checks[
            "contact_normal_impulse_ns"
        ],
        "contact_impulse_repeat_correlation": contact_correlation_checks[
            "contact_normal_impulse_ns"
        ],
    }
    qualified_nonkinematic = [name for name, result in families.items() if result["qualified"]]
    latent_export_qualified = (
        all(required_checks.values())
        and len(qualified_nonkinematic)
        >= int(config["admission"]["minimum_qualified_nonkinematic_families"])
    )
    serializable_triplet = {key: value for key, value in triplet.items() if key != "local_particle_mask"}
    summary = {
        "schema_version": 1,
        "qualification_id": config["qualification_id"],
        "status": "passed" if latent_export_qualified else "failed",
        "latent_export_qualified": latent_export_qualified,
        "qualified_nonkinematic_families": qualified_nonkinematic,
        "required_family_checks": required_checks,
        "mass_relative_error": mass_errors,
        "velocity": {
            "representation": "3x3 box mean of 5 mm column mean z velocity",
            "loaded_local_robust_span_mps": velocity_span,
            "loaded_vs_initial_local_rms_mps": velocity_change,
            "repeatability": velocity_evidence,
        },
        "contact": {
            checkpoint: {
                "active_nodes": int(np.sum(values["contact_node_count"])),
                "total_upward_impulse_ns": float(np.sum(values["contact_normal_impulse_ns"])),
            }
            for checkpoint, values in contact_columns.items()
        },
        "contact_repeatability": contact_evidence,
        "triplet": serializable_triplet,
        "repeatability": repeat,
        "nonkinematic_families": families,
        "plastic_maximum_absolute_log_jacobian": plastic_maximum_abs_log_jacobian,
        "field_semantics": FIELD_SEMANTICS,
        "provenance": {
            "qualification_plan_sha256": fresh.sha256_file(plan_path(config)),
            "latent_contract_sha256": plan["latent_contract_sha256"],
            "source_sha256": plan["source_sha256"],
            "input_sha256": plan["input_sha256"],
            "repeat_responses": [
                str((repeat_dir(config, index) / "response").resolve())
                for index in range(1, int(plan["repeat_count"]) + 1)
            ],
        },
    }
    fresh.write_json(raw_root(config) / "qualification_summary.json", summary)
    write_tracked_report(config, summary)
    return summary


def write_tracked_report(config: dict[str, Any], summary: dict[str, Any]) -> None:
    root = report_root(config)
    root.mkdir(parents=True, exist_ok=True)
    fresh.write_json(root / "summary.json", summary)
    rows = []
    for field, evidence in summary["triplet"]["fields"].items():
        rows.append(
            {
                "field": field,
                "loaded_local_robust_span": evidence["loaded_local_robust_span"],
                "minimum_checkpoint_rms_change": evidence["minimum_pairwise_checkpoint_rms_change"],
                "maximum_checkpoint_rms_change": evidence["maximum_pairwise_checkpoint_rms_change"],
                "maximum_repeat_rms": summary["repeatability"][field]["maximum_pairwise_repeat_rms"],
                "repeat_rms_over_action_signal": summary["repeatability"][field]["repeat_rms_over_action_signal"],
                "minimum_repeat_pearson": summary["repeatability"][field]["minimum_pairwise_repeat_pearson"],
            }
        )
    with (root / "field_metrics.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    family_lines = "\n".join(
        f"- `{name}`: {'qualified' if result['qualified'] else 'rejected'}"
        for name, result in summary["nonkinematic_families"].items()
    )
    (root / "README.md").write_text(
        "# Phase 1 latent export qualification\n\n"
        f"Status: **{summary['status']}**\n\n"
        "This report applies the prospectively frozen field-semantic, signal, "
        f"and three-repeat gates in `configs/{config['qualification_id']}.json`.\n\n"
        "## Non-kinematic families\n\n"
        f"{family_lines}\n\n"
        "The result qualifies solver inputs only. A claim that a qualified "
        "latent is predictively useful still requires the controlled H2 versus "
        "H1 evaluation. See `summary.json` and `field_metrics.csv` for complete "
        "metrics and provenance.\n",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = load_config(config_path)
    contract_path, contract = phase1_contract(config)
    if args.stage == "plan":
        plan = write_plan(config_path, config, contract_path, contract)
        print(json.dumps({"plan": str(plan_path(config)), "repeat_count": plan["repeat_count"]}, indent=2))
        return
    plan = load_plan(config_path, config, contract_path, contract)
    if args.stage in ("run", "all"):
        run_repeats(config, contract, plan, args.repeat)
    if args.stage in ("analyze", "all"):
        summary = analyze(config, contract, plan)
        print(json.dumps({"status": summary["status"], "qualified_nonkinematic_families": summary["qualified_nonkinematic_families"]}, indent=2))


if __name__ == "__main__":
    main()

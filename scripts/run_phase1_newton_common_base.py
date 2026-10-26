#!/usr/bin/env python3
"""Prospectively qualify the Phase 1 common-flat-base Newton repair."""

from __future__ import annotations

import argparse
import json
import math
import platform
import sys
from pathlib import Path
from typing import Any

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_fresh_phase0_matrix as phase0_matrix
import run_fresh_phase0_repeatability as fresh
import run_phase1_screening as screening
from chrono_episode_bridge import load_episode
from phase1_metric_bed import write_common_base_metric_bed
from run_phase1_contract_screen import load_contract


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUALIFICATION = (
    REPO_ROOT / "configs" / "phase1_newton_common_base_v2.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", type=Path, default=DEFAULT_QUALIFICATION)
    parser.add_argument(
        "--stage",
        choices=("plan", "bed", "newton", "analyze", "all"),
        default="plan",
    )
    return parser.parse_args()


def load_qualification(path: Path) -> dict[str, Any]:
    value = json.loads(path.resolve().read_text(encoding="utf-8"))
    if value.get("schema_version") != 1:
        raise ValueError("common-base qualification schema_version must be 1")
    if value.get("qualification_id") != "phase1_newton_common_base_v2":
        raise ValueError("unexpected common-base qualification identity")
    if not bool(value["antecedent_failure"]["preserve_original_failure"]):
        raise ValueError("the original failed screen must remain preserved")
    if value["builder"]["mode"] != (
        "exact_surface_global_vertical_lattice_common_flat_base"
    ):
        raise ValueError("common-base qualification requires the declared builder")
    timing = value["observation_time_contract"]
    if timing["newton_mode"] != "independent_fixed":
        raise ValueError("Newton observation timing must be independent_fixed")
    if not bool(timing["chrono_target_time_must_not_control_newton_rollout"]):
        raise ValueError("target-derived timing must be prohibited")
    admission = value["admission"]
    if float(admission["retain_phase0_surface_rmse_gate_m"]) != 0.005:
        raise ValueError("the inherited 5 mm preparation RMSE gate must remain")
    if float(admission["retain_phase0_surface_max_abs_gate_m"]) != 0.01:
        raise ValueError("the inherited 10 mm maximum surface gate must remain")
    return value


def qualification_root(config: dict[str, Any]) -> Path:
    return fresh.repo_path(config["execution"]["output_root"])


def plan_path(config: dict[str, Any]) -> Path:
    return qualification_root(config) / "qualification_plan.json"


def shared_root(config: dict[str, Any]) -> Path:
    return qualification_root(config) / "shared_newton_prior"


def source_paths(
    config_path: Path, config: dict[str, Any], contract: dict[str, Any]
) -> dict[str, Path]:
    paths = {
        "qualification_contract": config_path.resolve(),
        "qualification_runner": Path(__file__).resolve(),
        "common_base_builder": fresh.repo_path(config["builder"]["implementation"]),
        "phase1_screening": SCRIPT_DIR / "run_phase1_screening.py",
        "phase0_analysis": SCRIPT_DIR / "run_fresh_phase0_matrix.py",
        "chrono_episode_bridge": SCRIPT_DIR / "chrono_episode_bridge.py",
        "particle_io": SCRIPT_DIR / "particle_io.py",
        "newton_preparation": SCRIPT_DIR / "run_newton_prepared_bed.py",
        "newton_response": SCRIPT_DIR / "run_newton_cylinder_diagnostic.py",
        "newton_contract": SCRIPT_DIR / "newton_contract.py",
        "newton_base_config": fresh.repo_path(contract["newton"]["base_config"]),
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing common-base sources: {missing}")
    return paths


def material_cases(contract: dict[str, Any]) -> list[dict[str, Any]]:
    frozen = json.loads(screening.screen_plan_path(contract).read_text(encoding="utf-8"))
    return [
        screening.material_case(contract, raw) for raw in frozen["material_cases"]
    ]


def validate_shared_prior_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    if len(cases) != 5:
        raise ValueError("common-base material rescreen requires exactly five cases")
    keys = (
        "center_xy_m",
        "normal_force_n",
        "equivalent_mass_kg",
        "radius_m",
        "height_m",
        "initial_surface_seed",
    )
    reference = {key: cases[0][key] for key in keys}
    for case in cases[1:]:
        if any(case[key] != reference[key] for key in keys):
            raise ValueError("material cases do not share one Newton prior input")
    return reference


def input_paths(
    config: dict[str, Any], contract_path: Path, contract: dict[str, Any]
) -> dict[str, Path]:
    paths = {
        "phase1_contract": contract_path.resolve(),
        "dataset_plan": screening.frozen_dataset_plan(contract),
        "original_screening_plan": screening.screen_plan_path(contract),
        "original_screening_summary": fresh.repo_path(
            config["antecedent_failure"]["screening_summary"]
        ),
        "antecedent_preparation_manifest": fresh.repo_path(
            config["antecedent_failure"]["preparation_manifest"]
        ),
        "v1_qualification_plan": fresh.repo_path(
            config["antecedent_validation_failure"]["qualification_plan"]
        ),
        "v1_preparation_log": fresh.repo_path(
            config["antecedent_validation_failure"]["preparation_log"]
        ),
    }
    for case in material_cases(contract):
        episode = screening.chrono_episode(contract, case["case_id"])
        manifest_path = episode / "manifest.yaml"
        if not manifest_path.is_file():
            raise FileNotFoundError(f"missing Chrono manifest: {manifest_path}")
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        prefix = case["case_id"]
        paths[f"{prefix}:manifest"] = manifest_path
        paths[f"{prefix}:action"] = episode / manifest["action"]
        for checkpoint, filename in manifest["states"].items():
            paths[f"{prefix}:state:{checkpoint}"] = episode / filename
        mask_name = str(manifest["heightmap"]["valid_mask"]).split(";", 1)[0].strip()
        paths[f"{prefix}:valid_mask"] = episode / mask_name
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing common-base inputs: {missing}")
    return paths


def newton_environment(config: dict[str, Any]) -> dict[str, Any]:
    python = Path(config["execution"]["newton_python"]).resolve()
    output = fresh.command_output(
        [
            str(python),
            "-c",
            (
                "import json,platform,numpy,warp,newton; "
                "print(json.dumps({'python':platform.python_version(),"
                "'numpy':numpy.__version__,'warp':warp.__version__,"
                "'newton':getattr(newton,'__version__','unknown')}))"
            ),
        ],
        REPO_ROOT,
    )
    values = [line.strip() for line in output.splitlines() if line.strip()]
    if not values:
        raise RuntimeError("Newton environment probe returned no output")
    environment = json.loads(values[-1])
    gpu = fresh.command_output(
        [
            "nvidia-smi",
            "--query-gpu=name,uuid,driver_version",
            "--format=csv,noheader",
        ],
        REPO_ROOT,
    )
    if not gpu or "failed" in gpu.lower():
        raise RuntimeError(f"GPU probe failed: {gpu}")
    return {"packages": environment, "device": gpu}


def build_plan(
    config_path: Path,
    config: dict[str, Any],
    contract_path: Path,
    contract: dict[str, Any],
) -> dict[str, Any]:
    original = json.loads(
        fresh.repo_path(
            config["antecedent_failure"]["screening_summary"]
        ).read_text(encoding="utf-8")
    )
    if not bool(original.get("surface_screen_passed")):
        raise RuntimeError("original surface screen must pass before repair")
    if bool(original.get("material_screen_passed")):
        raise RuntimeError("repair is invalid because the original material screen passed")
    cases = material_cases(contract)
    shared = validate_shared_prior_cases(cases)
    chrono = {
        case["case_id"]: screening.chrono_result(contract, case) for case in cases
    }
    if not all(item.get("accepted") for item in chrono.values()):
        raise RuntimeError("all five frozen Chrono material cases must be accepted")
    sources = source_paths(config_path, config, contract)
    inputs = input_paths(config, contract_path, contract)
    return {
        "schema_version": 1,
        "qualification_id": config["qualification_id"],
        "status": "frozen_before_runtime",
        "captured_by_python": platform.python_version(),
        "qualification_contract_sha256": fresh.sha256_file(config_path),
        "phase1_contract_sha256": fresh.sha256_file(contract_path),
        "source_sha256": {
            name: fresh.sha256_file(path) for name, path in sources.items()
        },
        "input_sha256": {
            name: fresh.sha256_file(path) for name, path in inputs.items()
        },
        "environment": newton_environment(config),
        "repository": {
            "revision": fresh.command_output(["git", "rev-parse", "HEAD"], REPO_ROOT),
            "branch": fresh.command_output(["git", "branch", "--show-current"], REPO_ROOT),
            "status_short": fresh.command_output(
                ["git", "status", "--short"], REPO_ROOT
            ).splitlines(),
        },
        "shared_newton_input": shared,
        "material_cases": cases,
        "chrono_acceptance": chrono,
        "builder": config["builder"],
        "observation_time_contract": config["observation_time_contract"],
        "bulk_dataset_permitted": False,
    }


def write_plan(
    config_path: Path,
    config: dict[str, Any],
    contract_path: Path,
    contract: dict[str, Any],
) -> dict[str, Any]:
    plan = build_plan(config_path, config, contract_path, contract)
    path = plan_path(config)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        stable = (
            "qualification_contract_sha256",
            "phase1_contract_sha256",
            "source_sha256",
            "input_sha256",
            "environment",
            "shared_newton_input",
            "material_cases",
            "observation_time_contract",
        )
        if any(existing.get(key) != plan.get(key) for key in stable):
            raise RuntimeError(f"refusing to replace a different plan: {path}")
        return existing
    fresh.write_json(path, plan)
    return plan


def load_plan(
    config_path: Path,
    config: dict[str, Any],
    contract_path: Path,
    contract: dict[str, Any],
) -> dict[str, Any]:
    path = plan_path(config)
    if not path.is_file():
        raise RuntimeError("qualification plan is missing; run --stage plan first")
    plan = json.loads(path.read_text(encoding="utf-8"))
    current = build_plan(config_path, config, contract_path, contract)
    stable = (
        "qualification_contract_sha256",
        "phase1_contract_sha256",
        "source_sha256",
        "input_sha256",
        "environment",
        "shared_newton_input",
        "material_cases",
        "observation_time_contract",
    )
    changed = [key for key in stable if plan.get(key) != current.get(key)]
    if changed:
        raise RuntimeError(f"common-base plan identity changed: {changed}")
    return plan


def reference_case(
    config: dict[str, Any], cases: list[dict[str, Any]]
) -> dict[str, Any]:
    case_id = config["qualification_order"]["reference_case"]
    return next(case for case in cases if case["case_id"] == case_id)


def build_bed(
    config: dict[str, Any], contract: dict[str, Any], plan: dict[str, Any]
) -> Path:
    output = shared_root(config) / "metric_bed"
    expected = (
        output / "particles_initial_mpm.ply",
        output / "ground_plane_metadata.json",
    )
    if all(path.is_file() for path in expected):
        return output
    if output.exists():
        raise RuntimeError(f"refusing incomplete common-base bed: {output}")
    case = reference_case(config, plan["material_cases"])
    episode = screening.chrono_episode(contract, case["case_id"])
    manifest, _action, initial, _valid = load_episode(episode)
    builder = config["builder"]
    metadata = write_common_base_metric_bed(
        output,
        initial,
        manifest,
        bed_depth_m=float(builder["nominal_bed_depth_m"]),
        particle_spacing_m=float(builder["particle_spacing_m"]),
        minimum_top_gap_fraction=float(builder["minimum_top_gap_fraction"]),
    )
    metadata["provenance"] = {
        "qualification_plan_sha256": fresh.sha256_file(plan_path(config)),
        "reference_chrono_episode": str(episode.resolve()),
        "reference_initial_sha256": plan["input_sha256"][
            f"{case['case_id']}:state:initial"
        ],
    }
    fresh.write_json(output / "ground_plane_metadata.json", metadata)
    return output


def run_newton(
    config: dict[str, Any], contract: dict[str, Any], plan: dict[str, Any]
) -> Path | None:
    bed = build_bed(config, contract, plan)
    root = shared_root(config)
    logs = root / "logs"
    preparation = root / "preparation"
    preparation_manifest = preparation / "newton_prepared_bed_manifest.json"
    newton = contract["newton"]
    python = str(Path(config["execution"]["newton_python"]).resolve())
    device = str(config["execution"]["device"])
    case = reference_case(config, plan["material_cases"])
    episode = screening.chrono_episode(contract, case["case_id"])
    if not preparation_manifest.is_file():
        if preparation.exists():
            raise RuntimeError(f"refusing incomplete preparation: {preparation}")
        fresh.run_logged(
            [
                python,
                str(SCRIPT_DIR / "run_newton_prepared_bed.py"),
                "--config",
                str(fresh.repo_path(newton["base_config"])),
                "--particles-ply",
                str(bed / "particles_initial_mpm.ply"),
                "--metadata-json",
                str(bed / "ground_plane_metadata.json"),
                "--chrono-episode",
                str(episode),
                "--output-dir",
                str(preparation),
                "--device",
                device,
                "--dt-s",
                str(newton["selected_dt_s"]),
                "--duration-s",
                str(newton["pre_settle_duration_s"]),
                "--required-duration-s",
                str(newton["pre_settle_required_duration_s"]),
                "--particle-speed-threshold-mps",
                str(newton["particle_speed_threshold_mps"]),
                "--center-crop-half-width-m",
                "0",
                "--speed-check-every",
                "1",
                "--qualification-run",
            ],
            logs / "newton_preparation.log",
            REPO_ROOT,
        )
    prepared = json.loads(preparation_manifest.read_text(encoding="utf-8"))
    if not bool(prepared.get("accepted")):
        return None
    response = root / "response"
    manifest_path = response / "newton_cylinder_manifest.json"
    if manifest_path.is_file():
        return response
    if response.exists():
        raise RuntimeError(f"refusing incomplete response: {response}")
    timing = config["observation_time_contract"]
    fresh.run_logged(
        [
            python,
            str(SCRIPT_DIR / "run_newton_cylinder_diagnostic.py"),
            "--config",
            str(fresh.repo_path(newton["base_config"])),
            "--prepared-dir",
            str(preparation),
            "--candidate-preparation",
            "--chrono-episode",
            str(episode),
            "--output-dir",
            str(response),
            "--device",
            device,
            "--dt-s",
            str(newton["selected_dt_s"]),
            "--pre-settle-duration-s",
            str(newton["pre_settle_duration_s"]),
            "--pre-settle-required-duration-s",
            str(newton["pre_settle_required_duration_s"]),
            "--particle-speed-threshold-mps",
            str(newton["particle_speed_threshold_mps"]),
            "--observation-time-mode",
            str(timing["newton_mode"]),
            "--loaded-duration-s",
            str(timing["loaded_duration_s"]),
            "--residual-duration-s",
            str(timing["post_unload_duration_s"]),
            "--proxy-iterations",
            str(newton["proxy_iterations"]),
            "--rigid-substeps",
            str(newton["rigid_substeps"]),
            "--cylinder-friction-coefficient",
            str(newton["cylinder_friction_coefficient"]),
            "--cylinder-collider-mode",
            str(newton["collider_mode"]),
            "--cylinder-collider-segments",
            str(newton["collider_segments"]),
            "--cylinder-collision-guard-m",
            str(newton["collision_guard_m"]),
            "--cylinder-collision-bottom-inset-m",
            "0",
            "--cylinder-projection-threshold-m",
            str(newton["projection_threshold_m"]),
        ],
        logs / "newton_response.log",
        REPO_ROOT,
    )
    return response


def admission_policy(contract: dict[str, Any]) -> dict[str, Any]:
    inherited = json.loads(
        fresh.repo_path(contract["inheritance"]["phase0_contract"]).read_text(
            encoding="utf-8"
        )
    )
    return inherited["hierarchical_admission"]


def analyze(
    config: dict[str, Any], contract: dict[str, Any], plan: dict[str, Any]
) -> dict[str, Any]:
    root = shared_root(config)
    preparation_path = root / "preparation" / "newton_prepared_bed_manifest.json"
    response = root / "response"
    response_path = response / "newton_cylinder_manifest.json"
    prepared = (
        json.loads(preparation_path.read_text(encoding="utf-8"))
        if preparation_path.is_file()
        else None
    )
    manifest = (
        json.loads(response_path.read_text(encoding="utf-8"))
        if response_path.is_file()
        else None
    )
    pairings: dict[str, Any] = {}
    if prepared is not None and manifest is not None:
        bed_metadata = json.loads(
            (root / "metric_bed" / "ground_plane_metadata.json").read_text(
                encoding="utf-8"
            )
        )
        particle_count = int(bed_metadata["particle_count"])
        policy = admission_policy(contract)
        level_1 = policy["level_1_numerical_integrity"]
        level_2 = policy["level_2_interaction_artifact"]
        penetration = manifest["penetration"]
        inside = int(penetration["max_inside_particle_centers"])
        spacing = float(config["builder"]["particle_spacing_m"])
        gross_depth = spacing * float(
            level_2["gross_penetration_fraction_of_particle_spacing"]
        )
        inside_fraction = float(inside / particle_count)
        timing = manifest.get("observation_timing_s", {})
        for case in plan["material_cases"]:
            chrono = screening.chrono_result(contract, case)
            numerical = {
                "chrono_accepted": bool(chrono["accepted"]),
                "preparation_accepted": bool(prepared["accepted"]),
                "preparation_converged": bool(
                    manifest["preparation"]["convergence_passed"]
                ),
                "finite": bool(manifest["finite"]),
                "guide": bool(manifest["cylinder"]["guide_constraint_passed"]),
                "surface_cells": int(manifest["surface"]["valid_cells"])
                >= int(level_1["min_surface_valid_cells"]),
                "initial_support": float(
                    manifest["surface"]["initial_match"]["valid_fraction"]
                )
                >= float(level_1["min_initial_surface_valid_fraction"]),
                "independent_fixed_timing": (
                    timing.get("mode") == "independent_fixed"
                    and timing.get("chrono_target_time_controls_newton") is False
                ),
            }
            interaction = {
                "within_gross_depth": float(
                    penetration["max_center_penetration_m"]
                )
                <= gross_depth,
                "within_gross_affected_fraction": inside_fraction
                <= float(level_2["gross_inside_particle_fraction"]),
            }
            result = {
                "schema_version": 1,
                "case_id": case["case_id"],
                "complete": True,
                "shared_newton_prior": True,
                "pipeline_usable": all(numerical.values())
                and all(interaction.values()),
                "strict_mechanics_qualified": bool(
                    manifest.get("mechanics_qualified")
                ),
                "numerical_checks": numerical,
                "interaction_artifact_checks": interaction,
                "interaction_observed": {
                    "particle_count": particle_count,
                    "max_inside_particle_centers": inside,
                    "max_inside_particle_fraction": inside_fraction,
                    "max_center_penetration_m": float(
                        penetration["max_center_penetration_m"]
                    ),
                    "gross_depth_limit_m": gross_depth,
                },
                "geometry": phase0_matrix.local_geometry_metrics(
                    screening.chrono_episode(contract, case["case_id"]),
                    response,
                    case,
                ),
                "artifacts": {
                    "chrono_episode": str(
                        screening.chrono_episode(
                            contract, case["case_id"]
                        ).resolve()
                    ),
                    "metric_bed": str((root / "metric_bed").resolve()),
                    "newton_response": str(response.resolve()),
                },
            }
            pairings[case["case_id"]] = result
            fresh.write_json(
                qualification_root(config)
                / "cases"
                / case["case_id"]
                / "case_summary.json",
                result,
            )
    all_pairings = len(pairings) == 5 and all(
        item["pipeline_usable"] for item in pairings.values()
    )
    summary = {
        "schema_version": 1,
        "qualification_id": config["qualification_id"],
        "status": "passed" if all_pairings else "failed_or_incomplete",
        "preparation_present": prepared is not None,
        "preparation_accepted": bool(prepared and prepared.get("accepted")),
        "response_present": manifest is not None,
        "all_five_pairings_admitted": all_pairings,
        "bulk_dataset_permitted": all_pairings,
        "pairings": pairings,
        "identity": {
            "qualification_plan_sha256": fresh.sha256_file(plan_path(config)),
            "qualification_contract_sha256": plan[
                "qualification_contract_sha256"
            ],
            "source_sha256": plan["source_sha256"],
            "input_sha256": plan["input_sha256"],
        },
        "artifacts": {
            "shared_newton_prior": str(root.resolve()),
            "original_failed_screen": str(
                fresh.repo_path(
                    config["antecedent_failure"]["screening_summary"]
                ).resolve()
            ),
        },
    }
    fresh.write_json(qualification_root(config) / "qualification_summary.json", summary)
    return summary


def main() -> None:
    args = parse_args()
    config_path = args.qualification.resolve()
    config = load_qualification(config_path)
    contract_path = fresh.repo_path(config["phase1_contract"])
    contract = load_contract(contract_path)
    if args.stage == "plan":
        plan = write_plan(config_path, config, contract_path, contract)
        print(
            json.dumps(
                {
                    "plan": str(plan_path(config)),
                    "cases": len(plan["material_cases"]),
                    "reference_case": config["qualification_order"][
                        "reference_case"
                    ],
                },
                indent=2,
            )
        )
        return
    plan = load_plan(config_path, config, contract_path, contract)
    if args.stage in ("bed", "all"):
        print(build_bed(config, contract, plan))
    if args.stage in ("newton", "all"):
        print(run_newton(config, contract, plan))
    if args.stage in ("analyze", "all"):
        summary = analyze(config, contract, plan)
        print(
            json.dumps(
                {
                    key: summary[key]
                    for key in (
                        "status",
                        "preparation_accepted",
                        "response_present",
                        "all_five_pairings_admitted",
                        "bulk_dataset_permitted",
                    )
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()

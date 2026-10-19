#!/usr/bin/env python3
"""Run the initial static 35 mm Chrono-to-Newton qualification suite.

The suite deliberately tests a fixed baseline material and a static load
envelope before any material optimization or residual learning. It generates
15 position/load Chrono episodes, screens the selected Newton timestep through
the existing mechanics gates, then runs a three-level response-convergence
matrix on the declared high-load spatial anchor.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = REPO_ROOT / "configs" / "static_proxy_35mm_qualification.json"


@dataclass(frozen=True)
class CaseSpec:
    case_id: str
    position_label: str
    center_xy_m: tuple[float, float]
    support_weight_fraction: float
    equivalent_mass_kg: float
    normal_force_n: float
    nominal_pressure_pa: float
    radius_m: float
    height_m: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument(
        "--stage",
        choices=("plan", "chrono", "screen", "convergence", "all"),
        default="all",
        help="Execute only one resumable stage, or the complete qualification.",
    )
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help="Restrict chrono/screen execution to a case id; repeat as needed.",
    )
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--chrono-output-root", type=Path)
    parser.add_argument("--chrono-python", type=Path)
    parser.add_argument("--newton-python", type=Path)
    parser.add_argument("--device")
    return parser.parse_args()


def repo_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (REPO_ROOT / path).resolve()


def load_contract(path: Path) -> dict[str, Any]:
    contract = json.loads(path.resolve().read_text(encoding="utf-8"))
    if contract.get("schema_version") != 1:
        raise ValueError("static proxy contract schema_version must be 1")
    action = contract["action"]
    if action.get("load_mode") != "static_gravity_equivalent_mass":
        raise ValueError("initial proxy qualification must use a static load")
    if not action.get("dynamic_loads_excluded"):
        raise ValueError("the initial contract must explicitly exclude dynamic loads")
    positive = (
        "robot_mass_kg",
        "gravity_mps2",
        "radius_m",
        "height_m",
    )
    if any(not math.isfinite(float(action[key])) or float(action[key]) <= 0.0 for key in positive):
        raise ValueError("robot mass, gravity, radius, and height must be positive")
    fractions = [float(value) for value in action["support_weight_fractions"]]
    if not fractions or any(value <= 0.0 or value > 1.0 for value in fractions):
        raise ValueError("support weight fractions must lie in (0, 1]")
    positions = action["positions"]
    if not positions or len({item["label"] for item in positions}) != len(positions):
        raise ValueError("position labels must be present and unique")
    pit_x, pit_y = (float(value) for value in contract["chrono"]["scm_pit_size_m"])
    radius = float(action["radius_m"])
    for item in positions:
        x, y = (float(value) for value in item["xy_m"])
        if abs(x) + radius >= 0.5 * pit_x or abs(y) + radius >= 0.5 * pit_y:
            raise ValueError(f"position {item['label']} does not retain a full-foot pit margin")
    selected_dt = float(contract["newton"]["selected_dt_s"])
    convergence_dts = [float(value) for value in contract["response_convergence"]["timesteps_s"]]
    if selected_dt not in convergence_dts:
        raise ValueError("selected Newton timestep must appear in the convergence matrix")
    admission = contract["coarse_prior_admission"]
    if float(admission["max_transient_center_penetration_m"]) <= 0.0:
        raise ValueError("coarse-prior penetration tolerance must be positive")
    inside_fraction = float(admission["max_transient_inside_particle_fraction"])
    if inside_fraction <= 0.0 or inside_fraction >= 1.0:
        raise ValueError("coarse-prior inside-particle fraction must lie in (0, 1)")
    if bool(admission.get("strict_mechanics_claim_permitted")):
        raise ValueError("bounded coarse-prior admission cannot permit a strict mechanics claim")
    return contract


def force_label(normal_force_n: float) -> str:
    return f"f{round(normal_force_n):03d}n"


def build_cases(contract: dict[str, Any]) -> list[CaseSpec]:
    action = contract["action"]
    robot_mass = float(action["robot_mass_kg"])
    gravity = float(action["gravity_mps2"])
    radius = float(action["radius_m"])
    area = math.pi * radius * radius
    cases: list[CaseSpec] = []
    for position in action["positions"]:
        center = tuple(float(value) for value in position["xy_m"])
        for fraction_value in action["support_weight_fractions"]:
            fraction = float(fraction_value)
            mass = robot_mass * fraction
            force = mass * gravity
            cases.append(
                CaseSpec(
                    case_id=f"{position['label']}_{force_label(force)}",
                    position_label=str(position["label"]),
                    center_xy_m=(center[0], center[1]),
                    support_weight_fraction=fraction,
                    equivalent_mass_kg=mass,
                    normal_force_n=force,
                    nominal_pressure_pa=force / area,
                    radius_m=radius,
                    height_m=float(action["height_m"]),
                )
            )
    if len({case.case_id for case in cases}) != len(cases):
        raise ValueError("case ids are not unique after force-label rounding")
    return cases


def validate_episode_split(contract: dict[str, Any], cases: list[CaseSpec]) -> dict[str, str]:
    split = contract["episode_split"]
    assignments: dict[str, str] = {}
    for partition in ("train", "validation", "test"):
        values = [str(value) for value in split[partition]]
        if not values:
            raise ValueError(f"episode split partition is empty: {partition}")
        for case_id in values:
            if case_id in assignments:
                raise ValueError(f"episode split repeats case: {case_id}")
            assignments[case_id] = partition
    expected = {case.case_id for case in cases}
    observed = set(assignments)
    if observed != expected:
        missing = sorted(expected - observed)
        unknown = sorted(observed - expected)
        raise ValueError(
            f"episode split must assign every case exactly once; missing={missing}, unknown={unknown}"
        )
    return assignments


def dt_label(dt_s: float) -> str:
    return f"dt{dt_s * 1000:g}ms".replace(".", "p")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_plan(output_root: Path, contract_path: Path, contract: dict[str, Any], cases: list[CaseSpec]) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    write_json(
        output_root / "qualification_plan.json",
        {
            "schema_version": 1,
            "qualification_id": contract["qualification_id"],
            "contract": str(contract_path.resolve()),
            "claim_boundary": "static mechanics and numerical qualification only; no material calibration",
            "dynamic_loads_excluded": True,
            "case_count": len(cases),
            "cases": [asdict(case) for case in cases],
            "coarse_prior_admission": contract["coarse_prior_admission"],
            "episode_split": contract["episode_split"],
            "response_convergence": contract["response_convergence"],
        },
    )
    with (output_root / "cases.csv").open("w", newline="", encoding="utf-8") as file:
        rows = [
            {
                **asdict(case),
                "center_x_m": case.center_xy_m[0],
                "center_y_m": case.center_xy_m[1],
            }
            for case in cases
        ]
        for row in rows:
            row.pop("center_xy_m")
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_logged(command: list[str], log_path: Path, cwd: Path) -> bool:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    print("RUN", " ".join(command), flush=True)
    with log_path.open("w", encoding="utf-8") as output:
        result = subprocess.run(
            command,
            cwd=cwd,
            stdout=output,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    return result.returncode == 0


def chrono_paths(chrono_root: Path, case: CaseSpec) -> tuple[Path, Path]:
    episode = chrono_root / case.case_id
    return episode, episode / "manifest.yaml"


def read_chrono_result(episode: Path, case: CaseSpec) -> dict[str, Any]:
    manifest = yaml.safe_load((episode / "manifest.yaml").read_text(encoding="utf-8"))
    action = json.loads((episode / manifest["action"]).read_text(encoding="utf-8"))
    loading = manifest["chrono"]["loading_convergence"]
    initial = np.load(episode / manifest["states"]["initial"])
    loaded = np.load(episode / manifest["states"]["loaded"])
    residual = np.load(episode / manifest["states"]["residual"])
    mask_name = str(manifest["heightmap"]["valid_mask"]).split(";", 1)[0].strip()
    valid = np.load(episode / mask_name).astype(bool)
    rows, columns = initial.shape
    spacing = float(manifest["heightmap"]["spacing_m"])
    origin_x, origin_y = (float(value) for value in manifest["heightmap"]["origin_xy_m"])
    grid_x, grid_y = np.meshgrid(
        origin_x + np.arange(columns) * spacing,
        origin_y + np.arange(rows) * spacing,
    )
    footprint = (
        (grid_x - case.center_xy_m[0]) ** 2
        + (grid_y - case.center_xy_m[1]) ** 2
        <= case.radius_m**2
    )
    footprint_valid = valid & footprint
    loaded_delta = loaded - initial
    residual_delta = residual - initial
    surface_finite = bool(
        np.isfinite(initial[valid]).all()
        and np.isfinite(loaded[valid]).all()
        and np.isfinite(residual[valid]).all()
    )
    checks = {
        "episode_id": action["episode_id"] == case.case_id,
        "mass": math.isclose(float(action["mass_kg"]), case.equivalent_mass_kg),
        "position": np.allclose(action["center_xy_m"], case.center_xy_m, atol=1.0e-12),
        "radius": math.isclose(float(action["radius_m"]), case.radius_m),
        "height": math.isclose(float(action["height_m"]), case.height_m),
        "load_mode": action.get("load_mode") == "static_gravity_equivalent_mass",
        "normal_force": math.isclose(float(action.get("normal_force_n", math.nan)), case.normal_force_n),
        "loading_converged": bool(loading["accepted"]),
        "surface_finite": surface_finite,
        "footprint_present": bool(np.any(footprint_valid)),
    }
    return {
        "episode": str(episode.resolve()),
        "accepted": all(checks.values()),
        "checks": checks,
        "loaded_time_s": float(loading["final_sample_time_s"]),
        "normal_force_n": float(action.get("normal_force_n", math.nan)),
        "nominal_pressure_pa": float(action.get("nominal_pressure_pa", math.nan)),
        "surface": {
            "scope": "valid interior; one-cell SCM boundary ring excluded",
            "valid_cells": int(np.count_nonzero(valid)),
            "footprint_cells": int(np.count_nonzero(footprint_valid)),
            "loaded_peak_depression_m": float(-np.min(loaded_delta[valid])),
            "loaded_footprint_peak_depression_m": float(-np.min(loaded_delta[footprint_valid])),
            "loaded_footprint_mean_depression_m": float(-np.mean(loaded_delta[footprint_valid])),
            "residual_peak_depression_m": float(-np.min(residual_delta[valid])),
            "residual_footprint_peak_depression_m": float(-np.min(residual_delta[footprint_valid])),
            "all_cell_min_loaded_delta_m": float(np.min(loaded_delta)),
            "all_cell_min_residual_delta_m": float(np.min(residual_delta)),
        },
    }


def ensure_chrono_case(
    case: CaseSpec,
    contract: dict[str, Any],
    chrono_repo: Path,
    chrono_root: Path,
    chrono_command: list[str],
    log_root: Path,
) -> dict[str, Any]:
    episode, manifest_path = chrono_paths(chrono_root, case)
    if manifest_path.is_file():
        return read_chrono_result(episode, case)
    if episode.exists():
        raise RuntimeError(f"refusing incomplete existing Chrono directory: {episode}")
    cfg = contract["chrono"]
    command = [
        *chrono_command,
        str(chrono_repo / "run_cylinder_episode.py"),
        "--episode-id", case.case_id,
        "--mass-kg", str(case.equivalent_mass_kg),
        "--xy", str(case.center_xy_m[0]), str(case.center_xy_m[1]),
        "--radius-m", str(case.radius_m),
        "--height-m", str(case.height_m),
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
    if cfg["vertical_guide"]:
        command.append("--vertical-guide")
    if not run_logged(command, log_root / "chrono" / f"{case.case_id}.log", chrono_repo):
        return {"episode": str(episode), "accepted": False, "execution_failed": True}
    return read_chrono_result(episode, case)


def preparation_dir(output_root: Path, dt_s: float) -> Path:
    return output_root / "preparations" / dt_label(dt_s)


def response_dir(output_root: Path, case: CaseSpec, dt_s: float) -> Path:
    return output_root / "responses" / case.case_id / dt_label(dt_s)


def ensure_preparation(
    contract: dict[str, Any],
    episode: Path,
    output_root: Path,
    newton_python: Path,
    device: str,
    dt_s: float,
) -> tuple[Path, bool]:
    cfg = contract["newton"]
    output = preparation_dir(output_root, dt_s)
    manifest_path = output / "newton_prepared_bed_manifest.json"
    if manifest_path.is_file():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return output, bool(data.get("accepted"))
    if output.exists():
        raise RuntimeError(f"refusing incomplete existing Newton preparation: {output}")
    command = [
        str(newton_python), str(REPO_ROOT / "scripts" / "run_newton_prepared_bed.py"),
        "--config", str(repo_path(cfg["base_config"])),
        "--particles-ply", str(repo_path(cfg["particles_ply"])),
        "--metadata-json", str(repo_path(cfg["metadata_json"])),
        "--chrono-episode", str(episode),
        "--output-dir", str(output),
        "--device", device,
        "--dt-s", str(dt_s),
        "--duration-s", str(cfg["pre_settle_duration_s"]),
        "--required-duration-s", str(cfg["pre_settle_required_duration_s"]),
        "--particle-speed-threshold-mps", str(cfg["particle_speed_threshold_mps"]),
        "--center-crop-half-width-m", "0",
        "--speed-check-every", "1",
        "--qualification-run",
    ]
    ok = run_logged(command, output_root / "logs" / "preparations" / f"{dt_label(dt_s)}.log", REPO_ROOT)
    accepted = False
    if ok and manifest_path.is_file():
        accepted = bool(json.loads(manifest_path.read_text(encoding="utf-8")).get("accepted"))
    return output, accepted


def evaluate_coarse_prior_admission(
    manifest: dict[str, Any],
    prepared_manifest: dict[str, Any] | None,
    policy: dict[str, Any],
) -> dict[str, Any]:
    particle_count = int(
        (prepared_manifest or {}).get("selection", {}).get("particle_count", 0)
    )
    penetration = manifest["penetration"]
    loaded_penetration = penetration["loaded"]
    max_inside = int(penetration["max_inside_particle_centers"])
    inside_fraction = float(max_inside / particle_count) if particle_count > 0 else math.inf
    surface = manifest["surface"]
    checks = {
        "preparation_convergence": bool(
            manifest["preparation"].get("convergence_passed")
        ),
        "finite": bool(manifest.get("finite")),
        "guide_constraint": bool(manifest["cylinder"].get("guide_constraint_passed")),
        "transient_penetration_depth": float(penetration["max_center_penetration_m"])
        <= float(policy["max_transient_center_penetration_m"]),
        "transient_inside_particle_fraction": inside_fraction
        <= float(policy["max_transient_inside_particle_fraction"]),
        "loaded_zero_penetration": (
            not bool(policy["require_zero_loaded_center_penetration"])
            or (
                int(loaded_penetration["inside_particle_centers"]) == 0
                and float(loaded_penetration["max_center_penetration_m"]) == 0.0
            )
        ),
        "surface_support": int(surface["valid_cells"])
        >= int(policy["min_surface_valid_cells"]),
        "initial_surface_support": float(surface["initial_match"]["valid_fraction"])
        >= float(policy["min_initial_surface_valid_fraction"]),
        "particle_count_available": particle_count > 0,
    }
    return {
        "policy_id": str(policy["policy_id"]),
        "admissible": all(checks.values()),
        "strict_mechanics_qualified": bool(manifest.get("mechanics_qualified")),
        "strict_mechanics_claim_permitted": False,
        "checks": checks,
        "observed": {
            "particle_count": particle_count,
            "max_inside_particle_centers": max_inside,
            "max_inside_particle_fraction": inside_fraction,
            "max_center_penetration_m": float(penetration["max_center_penetration_m"]),
            "loaded_inside_particle_centers": int(
                loaded_penetration["inside_particle_centers"]
            ),
            "surface_valid_cells": int(surface["valid_cells"]),
            "initial_surface_valid_fraction": float(
                surface["initial_match"]["valid_fraction"]
            ),
        },
        "limits": {
            "max_transient_center_penetration_m": float(
                policy["max_transient_center_penetration_m"]
            ),
            "max_transient_inside_particle_fraction": float(
                policy["max_transient_inside_particle_fraction"]
            ),
            "require_zero_loaded_center_penetration": bool(
                policy["require_zero_loaded_center_penetration"]
            ),
            "min_surface_valid_cells": int(policy["min_surface_valid_cells"]),
            "min_initial_surface_valid_fraction": float(
                policy["min_initial_surface_valid_fraction"]
            ),
        },
    }


def read_newton_result(output: Path, contract: dict[str, Any]) -> dict[str, Any]:
    manifest = json.loads((output / "newton_cylinder_manifest.json").read_text(encoding="utf-8"))
    prepared_root = Path(manifest["preparation"]["contract_path"])
    prepared_manifest_path = prepared_root / "newton_prepared_bed_manifest.json"
    prepared_manifest = (
        json.loads(prepared_manifest_path.read_text(encoding="utf-8"))
        if prepared_manifest_path.is_file()
        else None
    )
    coarse_prior = evaluate_coarse_prior_admission(
        manifest, prepared_manifest, contract["coarse_prior_admission"]
    )
    return {
        "response": str(output.resolve()),
        "accepted": bool(manifest.get("accepted")),
        "mechanics_qualified": bool(manifest.get("mechanics_qualified")),
        "acceptance_blockers": manifest.get("acceptance_blockers", []),
        "zero_center_penetration": bool(manifest["penetration"]["passed_zero_center_penetration_gate"]),
        "max_center_penetration_m": float(manifest["penetration"]["max_center_penetration_m"]),
        "guide_constraint_passed": bool(manifest["cylinder"]["guide_constraint_passed"]),
        "loaded_sinkage_m": float(manifest["cylinder"]["sinkage_below_initial_surface_m"]),
        "loaded_rmse_m": manifest["surface"]["loaded_response_error"]["rmse_m"],
        "residual_rmse_m": manifest["surface"]["residual_response_error"]["rmse_m"],
        "wall_time_s": float(manifest["wall_time_s"]),
        "coarse_prior": coarse_prior,
    }


def ensure_newton_response(
    case: CaseSpec,
    contract: dict[str, Any],
    episode: Path,
    prepared: Path,
    output_root: Path,
    newton_python: Path,
    device: str,
    dt_s: float,
) -> dict[str, Any]:
    cfg = contract["newton"]
    output = response_dir(output_root, case, dt_s)
    manifest_path = output / "newton_cylinder_manifest.json"
    if manifest_path.is_file():
        return read_newton_result(output, contract)
    if output.exists():
        raise RuntimeError(f"refusing incomplete existing Newton response: {output}")
    command = [
        str(newton_python), str(REPO_ROOT / "scripts" / "run_newton_cylinder_diagnostic.py"),
        "--config", str(repo_path(cfg["base_config"])),
        "--prepared-dir", str(prepared),
        "--candidate-preparation",
        "--chrono-episode", str(episode),
        "--output-dir", str(output),
        "--device", device,
        "--dt-s", str(dt_s),
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
    ]
    ok = run_logged(
        command,
        output_root / "logs" / "responses" / case.case_id / f"{dt_label(dt_s)}.log",
        REPO_ROOT,
    )
    if not ok or not manifest_path.is_file():
        return {"response": str(output), "accepted": False, "execution_failed": True}
    return read_newton_result(output, contract)


def h0_consistency(chrono_root: Path, cases: list[CaseSpec]) -> dict[str, Any]:
    records = []
    reference: np.ndarray | None = None
    reference_case: str | None = None
    for case in cases:
        episode, manifest_path = chrono_paths(chrono_root, case)
        if not manifest_path.is_file():
            continue
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        current = np.load(episode / manifest["states"]["initial"])
        if reference is None:
            reference = current
            reference_case = case.case_id
        records.append(
            {
                "case_id": case.case_id,
                "shape_matches": current.shape == reference.shape,
                "exactly_equal": bool(current.shape == reference.shape and np.array_equal(current, reference)),
                "max_abs_difference_m": (
                    float(np.max(np.abs(current - reference))) if current.shape == reference.shape else None
                ),
            }
        )
    return {
        "reference_case": reference_case,
        "available_case_count": len(records),
        "all_available_exactly_equal": bool(records and all(row["exactly_equal"] for row in records)),
        "cases": records,
    }


def run_convergence_analysis(
    contract: dict[str, Any],
    case: CaseSpec,
    output_root: Path,
    newton_python: Path,
) -> bool:
    cfg = contract["response_convergence"]
    labels = {0.0005: "coarse", 0.00025: "medium", 0.000125: "fine"}
    command = [str(newton_python), str(REPO_ROOT / "scripts" / "analyze_newton_response_convergence.py")]
    for dt_s in sorted((float(value) for value in cfg["timesteps_s"]), reverse=True):
        command.extend(["--case", f"{labels[dt_s]}={response_dir(output_root, case, dt_s)}"])
    analysis = output_root / "response_convergence"
    command.extend(
        [
            "--output-dir", str(analysis),
            "--rmse-gate-m", str(cfg["response_rmse_gate_m"]),
            "--max-abs-gate-m", str(cfg["response_max_abs_gate_m"]),
            "--sinkage-gate-m", str(cfg["loaded_sinkage_gate_m"]),
        ]
    )
    return run_logged(command, output_root / "logs" / "response_convergence.log", REPO_ROOT)


def write_summary(
    output_root: Path,
    chrono_root: Path,
    cases: list[CaseSpec],
    contract: dict[str, Any],
) -> dict[str, Any]:
    selected_dt = float(contract["newton"]["selected_dt_s"])
    rows = []
    for case in cases:
        episode, chrono_manifest = chrono_paths(chrono_root, case)
        chrono_result = read_chrono_result(episode, case) if chrono_manifest.is_file() else None
        newton_output = response_dir(output_root, case, selected_dt)
        newton_result = (
            read_newton_result(newton_output, contract)
            if (newton_output / "newton_cylinder_manifest.json").is_file()
            else None
        )
        rows.append({"case": asdict(case), "chrono": chrono_result, "newton": newton_result})
    chrono_complete = all(row["chrono"] is not None for row in rows)
    chrono_passed = bool(chrono_complete and all(row["chrono"]["accepted"] for row in rows))
    chrono_attempted = [row for row in rows if row["chrono"] is not None]
    chrono_attempted_passed = bool(
        chrono_attempted and all(row["chrono"]["accepted"] for row in chrono_attempted)
    )
    screen_complete = all(row["newton"] is not None for row in rows)
    screen_passed = bool(screen_complete and all(row["newton"]["accepted"] for row in rows))
    screen_attempted = [row for row in rows if row["newton"] is not None]
    screen_attempted_passed = bool(
        screen_attempted and all(row["newton"]["accepted"] for row in screen_attempted)
    )
    coarse_screen_complete = bool(
        screen_complete
        and all(row["newton"]["coarse_prior"]["admissible"] for row in rows)
    )
    coarse_screen_attempted_passed = bool(
        screen_attempted
        and all(row["newton"]["coarse_prior"]["admissible"] for row in screen_attempted)
    )
    convergence_path = output_root / "response_convergence" / "summary.json"
    convergence = json.loads(convergence_path.read_text(encoding="utf-8")) if convergence_path.is_file() else None
    convergence_passed = bool(convergence and convergence.get("consistency_passed"))
    h0 = h0_consistency(chrono_root, cases)
    initial_domain_passed = bool(
        chrono_passed
        and h0["all_available_exactly_equal"]
        and screen_passed
        and convergence_passed
    )
    assignments = validate_episode_split(contract, cases)
    coarse_prior_domain_admitted = bool(
        chrono_passed
        and h0["all_available_exactly_equal"]
        and coarse_screen_complete
    )
    status = "strictly_qualified" if initial_domain_passed else "coarse_prior_incomplete"
    strict_status = "qualified" if initial_domain_passed else "incomplete"
    if (chrono_attempted and not chrono_attempted_passed) or (
        screen_attempted and not screen_attempted_passed
    ) or (
        convergence is not None and not convergence_passed
    ):
        strict_status = "not_qualified"
    if coarse_prior_domain_admitted:
        status = "coarse_prior_admitted"
    elif (chrono_attempted and not chrono_attempted_passed) or (
        screen_attempted and not coarse_screen_attempted_passed
    ):
        status = "coarse_prior_not_admitted"
    summary = {
        "schema_version": 1,
        "qualification_id": contract["qualification_id"],
        "status": status,
        "strict_status": strict_status,
        "claim_boundary": (
            "static 35 mm bounded coarse prior for residual-model data generation; "
            "not strict mechanics or timestep-convergence qualification"
        ),
        "dynamic_loads_excluded": True,
        "chrono_complete": chrono_complete,
        "chrono_passed": chrono_passed,
        "chrono_attempted_case_count": len(chrono_attempted),
        "chrono_attempted_passed": chrono_attempted_passed,
        "h0_consistency": h0,
        "screen_complete": screen_complete,
        "screen_passed": screen_passed,
        "screen_attempted_case_count": len(screen_attempted),
        "screen_attempted_passed": screen_attempted_passed,
        "coarse_prior_policy": contract["coarse_prior_admission"],
        "coarse_screen_complete": coarse_screen_complete,
        "coarse_screen_attempted_passed": coarse_screen_attempted_passed,
        "response_convergence_complete": convergence is not None,
        "response_convergence_passed": convergence_passed,
        "initial_static_domain_qualified": initial_domain_passed,
        "coarse_prior_domain_admitted": coarse_prior_domain_admitted,
        "material_calibrated": False,
        "residual_training_permitted": coarse_prior_domain_admitted,
        "episode_split": {
            "policy": contract["episode_split"]["policy"],
            "assignments": assignments,
        },
        "cases": rows,
    }
    write_json(output_root / "qualification_summary.json", summary)
    flat_rows = []
    for row in rows:
        case = row["case"]
        chrono = row["chrono"] or {}
        newton = row["newton"] or {}
        flat_rows.append(
            {
                "case_id": case["case_id"],
                "x_m": case["center_xy_m"][0],
                "y_m": case["center_xy_m"][1],
                "normal_force_n": case["normal_force_n"],
                "pressure_pa": case["nominal_pressure_pa"],
                "chrono_accepted": chrono.get("accepted"),
                "newton_accepted": newton.get("accepted"),
                "zero_center_penetration": newton.get("zero_center_penetration"),
                "coarse_prior_admissible": (newton.get("coarse_prior") or {}).get("admissible"),
                "loaded_sinkage_m": newton.get("loaded_sinkage_m"),
                "loaded_rmse_m": newton.get("loaded_rmse_m"),
                "residual_rmse_m": newton.get("residual_rmse_m"),
            }
        )
    with (output_root / "qualification_cases.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(flat_rows[0]))
        writer.writeheader()
        writer.writerows(flat_rows)
    return summary


def main() -> None:
    args = parse_args()
    contract_path = args.contract.resolve()
    contract = load_contract(contract_path)
    cases = build_cases(contract)
    validate_episode_split(contract, cases)
    known = {case.case_id for case in cases}
    unknown = sorted(set(args.case) - known)
    if unknown:
        raise ValueError(f"unknown case ids: {', '.join(unknown)}")
    selected = [case for case in cases if not args.case or case.case_id in args.case]

    newton_cfg = contract["newton"]
    chrono_cfg = contract["chrono"]
    output_root = (args.output_root or repo_path(newton_cfg["output_root"])).resolve()
    chrono_root = (args.chrono_output_root or repo_path(chrono_cfg["output_root"])).resolve()
    chrono_repo = repo_path(chrono_cfg["repo"])
    chrono_command = (
        [str(args.chrono_python.resolve())]
        if args.chrono_python is not None
        else [str(value) for value in chrono_cfg["command"]]
    )
    newton_python = (args.newton_python or Path(newton_cfg["python"])).resolve()
    device = args.device or str(newton_cfg["device"])
    write_plan(output_root, contract_path, contract, cases)
    if args.stage == "plan":
        summary = write_summary(output_root, chrono_root, cases, contract)
        print(json.dumps({"plan": str(output_root / "qualification_plan.json"), "status": summary["status"]}, indent=2))
        return

    sentinel_id = str(newton_cfg["sentinel_case_id"])
    sentinel = next(case for case in cases if case.case_id == sentinel_id)
    if args.stage == "all" and not args.case:
        sentinel_chrono = ensure_chrono_case(
            sentinel,
            contract,
            chrono_repo,
            chrono_root,
            chrono_command,
            output_root / "logs",
        )
        if not sentinel_chrono["accepted"]:
            summary = write_summary(output_root, chrono_root, cases, contract)
            print("STOP: Chrono sentinel failed; the full matrix was not launched.")
            print(json.dumps({"status": summary["status"]}, indent=2))
            return
        prepared, preparation_ok = ensure_preparation(
            contract,
            chrono_paths(chrono_root, sentinel)[0],
            output_root,
            newton_python,
            device,
            float(newton_cfg["selected_dt_s"]),
        )
        if not preparation_ok:
            raise RuntimeError("selected-timestep Newton preparation did not qualify")
        sentinel_newton = ensure_newton_response(
            sentinel,
            contract,
            chrono_paths(chrono_root, sentinel)[0],
            prepared,
            output_root,
            newton_python,
            device,
            float(newton_cfg["selected_dt_s"]),
        )
        if not sentinel_newton["coarse_prior"]["admissible"]:
            summary = write_summary(output_root, chrono_root, cases, contract)
            print("STOP: Newton sentinel failed coarse-prior admission; the full matrix was not launched.")
            print(json.dumps({"status": summary["status"]}, indent=2))
            return

    if args.stage in ("chrono", "all"):
        for case in selected:
            result = ensure_chrono_case(
                case, contract, chrono_repo, chrono_root, chrono_command, output_root / "logs"
            )
            print(f"CHRONO {case.case_id}: {'pass' if result['accepted'] else 'fail'}", flush=True)

    selected_dt = float(newton_cfg["selected_dt_s"])
    if args.stage in ("screen", "all"):
        available = [
            case for case in selected if chrono_paths(chrono_root, case)[1].is_file()
        ]
        if not available:
            raise RuntimeError("screen stage requires at least one generated Chrono episode")
        reference_episode = chrono_paths(chrono_root, available[0])[0]
        prepared, preparation_ok = ensure_preparation(
            contract, reference_episode, output_root, newton_python, device, selected_dt
        )
        if not preparation_ok:
            raise RuntimeError("selected-timestep Newton preparation did not qualify")
        for case in available:
            result = ensure_newton_response(
                case,
                contract,
                chrono_paths(chrono_root, case)[0],
                prepared,
                output_root,
                newton_python,
                device,
                selected_dt,
            )
            strict = "pass" if result["accepted"] else "fail"
            coarse = "pass" if result["coarse_prior"]["admissible"] else "fail"
            print(
                f"NEWTON {case.case_id}: strict={strict} coarse_prior={coarse}",
                flush=True,
            )

    require_convergence = bool(
        contract["coarse_prior_admission"]["require_response_convergence"]
    )
    if args.stage == "convergence" or (
        args.stage == "all" and not args.case and require_convergence
    ):
        anchor_id = str(contract["response_convergence"]["anchor_case_id"])
        anchor = next(case for case in cases if case.case_id == anchor_id)
        anchor_episode, anchor_manifest = chrono_paths(chrono_root, anchor)
        if not anchor_manifest.is_file():
            if args.stage == "all" and (not args.case or anchor_id in args.case):
                ensure_chrono_case(
                    anchor, contract, chrono_repo, chrono_root, chrono_command, output_root / "logs"
                )
            else:
                raise RuntimeError(f"convergence anchor Chrono episode is missing: {anchor_id}")
        for dt_s in (float(value) for value in contract["response_convergence"]["timesteps_s"]):
            prepared, preparation_ok = ensure_preparation(
                contract, anchor_episode, output_root, newton_python, device, dt_s
            )
            if not preparation_ok:
                raise RuntimeError(f"Newton preparation failed at {dt_s} s")
            ensure_newton_response(
                anchor,
                contract,
                anchor_episode,
                prepared,
                output_root,
                newton_python,
                device,
                dt_s,
            )
        run_convergence_analysis(contract, anchor, output_root, newton_python)

    summary = write_summary(output_root, chrono_root, cases, contract)
    print(json.dumps({key: summary[key] for key in (
        "status", "chrono_passed", "screen_passed", "response_convergence_passed",
        "initial_static_domain_qualified", "coarse_prior_domain_admitted",
        "residual_training_permitted"
    )}, indent=2))


if __name__ == "__main__":
    main()

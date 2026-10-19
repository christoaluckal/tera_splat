#!/usr/bin/env python3
"""Characterize same-build variation for the fresh Phase 0 campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from chrono_episode_bridge import load_episode, write_metric_bed


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = REPO_ROOT / "configs" / "static_proxy_hierarchical_v3_20261017.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument(
        "--stage",
        choices=("plan", "chrono", "bed", "newton", "analyze", "all"),
        default="plan",
    )
    parser.add_argument("--chrono-python", type=Path)
    parser.add_argument("--newton-python", type=Path)
    parser.add_argument("--device")
    return parser.parse_args()


def repo_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (REPO_ROOT / path).resolve()


def load_contract(path: Path) -> dict[str, Any]:
    contract = json.loads(path.resolve().read_text(encoding="utf-8"))
    if contract.get("schema_version") != 2:
        raise ValueError("fresh hierarchical contract schema_version must be 2")
    reuse = contract["reuse_policy"]
    if bool(reuse["prior_experiment_outputs_admissible"]):
        raise ValueError("fresh campaign must prohibit prior experiment outputs")
    required_fresh = (
        "require_fresh_chrono_h0",
        "require_fresh_metric_particle_bed_from_chrono_h0",
        "require_fresh_newton_preparation_per_response",
    )
    if not all(bool(reuse[key]) for key in required_fresh):
        raise ValueError("fresh campaign must require fresh H0, bed, and preparation")
    repeatability = contract["repeatability"]
    if bool(repeatability["required_before_matrix"]):
        raise ValueError("bitwise repeatability cannot be a matrix-expansion prerequisite")
    if int(repeatability["sequential_repeats"]) != 2:
        raise ValueError("the initial variation characterization requires exactly two repeats")
    if bool(repeatability["reuse_repeat_as_training_data"]):
        raise ValueError("repeatability duplicates cannot be duplicated in training")
    if contract["newton"]["metric_bed_source"]["mode"] != "build_from_fresh_chrono_h0":
        raise ValueError("Newton bed must be rebuilt from the fresh Chrono H0")
    if "particles_ply" in contract["newton"] or "metadata_json" in contract["newton"]:
        raise ValueError("fresh contract cannot reference a pre-existing particle bed")
    return contract


def force_label(normal_force_n: float) -> str:
    return f"f{round(normal_force_n):03d}n"


def cases(contract: dict[str, Any]) -> list[dict[str, Any]]:
    action = contract["action"]
    radius = float(action["radius_m"])
    area = math.pi * radius * radius
    result = []
    for position in action["positions"]:
        for fraction_value in action["support_weight_fractions"]:
            fraction = float(fraction_value)
            mass = float(action["robot_mass_kg"]) * fraction
            force = mass * float(action["gravity_mps2"])
            result.append(
                {
                    "case_id": f"{position['label']}_{force_label(force)}",
                    "position_label": str(position["label"]),
                    "center_xy_m": [float(value) for value in position["xy_m"]],
                    "support_weight_fraction": fraction,
                    "equivalent_mass_kg": mass,
                    "normal_force_n": force,
                    "nominal_pressure_pa": force / area,
                    "radius_m": radius,
                    "height_m": float(action["height_m"]),
                }
            )
    return result


def validate_split(contract: dict[str, Any], campaign_cases: list[dict[str, Any]]) -> None:
    expected = {case["case_id"] for case in campaign_cases}
    assigned: list[str] = []
    for partition in ("train", "validation", "test"):
        assigned.extend(str(value) for value in contract["episode_split"][partition])
    if len(assigned) != len(set(assigned)):
        raise ValueError("episode split contains duplicate assignments")
    if set(assigned) != expected:
        raise ValueError("episode split must assign every fresh case exactly once")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def command_output(command: list[str], cwd: Path) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def git_identity(repo: Path) -> dict[str, Any]:
    return {
        "root": str(repo.resolve()),
        "revision": command_output(["git", "rev-parse", "HEAD"], repo),
        "branch": command_output(["git", "branch", "--show-current"], repo),
        "status_short": command_output(["git", "status", "--short"], repo).splitlines(),
    }


def source_files(contract_path: Path, contract: dict[str, Any]) -> list[Path]:
    chrono_repo = repo_path(contract["chrono"]["repo"])
    values = [
        contract_path.resolve(),
        Path(__file__).resolve(),
        REPO_ROOT / "scripts" / "chrono_episode_bridge.py",
        REPO_ROOT / "scripts" / "particle_io.py",
        REPO_ROOT / "scripts" / "run_newton_prepared_bed.py",
        REPO_ROOT / "scripts" / "run_newton_cylinder_diagnostic.py",
        REPO_ROOT / "scripts" / "newton_contract.py",
        repo_path(contract["newton"]["base_config"]),
        chrono_repo / "run_cylinder_episode.py",
        chrono_repo / "quick_support_demo" / "chrono_demo" / "cylinder_episode.py",
        chrono_repo / "quick_support_demo" / "chrono_demo" / "build_scm_pit.py",
        chrono_repo / "quick_support_demo" / "chrono_demo" / "build_world.py",
        chrono_repo / "quick_support_demo" / "config.py",
        chrono_repo / "quick_support_demo" / "configs" / "demo.yaml",
        chrono_repo / "quick_support_demo" / "configs" / "world.yaml",
        chrono_repo / "quick_support_demo" / "configs" / "terrain.yaml",
    ]
    missing = [str(path) for path in values if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"provenance source files are missing: {missing}")
    return values


def provenance(contract_path: Path, contract: dict[str, Any]) -> dict[str, Any]:
    chrono_repo = repo_path(contract["chrono"]["repo"])
    chrono_probe = [
        *[str(value) for value in contract["chrono"]["command"]],
        "-c",
        (
            "import json, platform; from importlib.metadata import distributions; "
            "v={d.metadata['Name'].lower(): d.version for d in distributions()}; "
            "print(json.dumps({'python': platform.python_version(), "
            "'pychrono': v.get('pychrono', v.get('chrono', 'unknown'))}))"
        ),
    ]
    newton_probe = [
        str(Path(contract["newton"]["python"]).resolve()),
        "-c",
        (
            "import json, platform; from importlib.metadata import version; "
            "print(json.dumps({'python': platform.python_version(), "
            "'newton': version('newton'), 'warp': version('warp-lang')}))"
        ),
    ]
    return {
        "captured_by_python": platform.python_version(),
        "contract_sha256": sha256_file(contract_path.resolve()),
        "source_sha256": {
            str(path.resolve()): sha256_file(path.resolve())
            for path in source_files(contract_path, contract)
        },
        "repositories": {
            "tera_splat": git_identity(REPO_ROOT),
            "tera_splat_sim": git_identity(chrono_repo),
        },
        "thread_environment": contract["chrono"]["thread_environment"],
        "environment_probes": {
            "chrono": command_output(chrono_probe, chrono_repo),
            "newton": command_output(newton_probe, REPO_ROOT),
            "gpu": command_output(
                [
                    "nvidia-smi",
                    "--query-gpu=name,uuid,driver_version",
                    "--format=csv,noheader",
                ],
                REPO_ROOT,
            ),
        },
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def roots(contract: dict[str, Any]) -> tuple[Path, Path, Path]:
    chrono_root = repo_path(contract["chrono"]["output_root"])
    newton_root = repo_path(contract["newton"]["output_root"])
    repeat_root = newton_root / "repeatability"
    return chrono_root, newton_root, repeat_root


def sentinel(contract: dict[str, Any], campaign_cases: list[dict[str, Any]]) -> dict[str, Any]:
    sentinel_id = str(contract["repeatability"]["sentinel_case_id"])
    matches = [case for case in campaign_cases if case["case_id"] == sentinel_id]
    if len(matches) != 1:
        raise ValueError(f"repeatability sentinel is not a unique campaign case: {sentinel_id}")
    return matches[0]


def write_plan(contract_path: Path, contract: dict[str, Any]) -> dict[str, Any]:
    campaign_cases = cases(contract)
    validate_split(contract, campaign_cases)
    chrono_root, newton_root, repeat_root = roots(contract)
    plan = {
        "schema_version": 1,
        "qualification_id": contract["qualification_id"],
        "status": "variation_not_characterized",
        "prior_outputs_admissible": False,
        "contract": str(contract_path.resolve()),
        "campaign_case_count": len(campaign_cases),
        "cases": campaign_cases,
        "episode_split": contract["episode_split"],
        "sentinel": sentinel(contract, campaign_cases),
        "chrono_root": str(chrono_root),
        "newton_root": str(newton_root),
        "repeatability_root": str(repeat_root),
        "provenance": provenance(contract_path, contract),
    }
    write_json(newton_root / "campaign_plan.json", plan)
    return plan


def load_plan(contract: dict[str, Any]) -> dict[str, Any]:
    _chrono_root, newton_root, _repeat_root = roots(contract)
    plan_path = newton_root / "campaign_plan.json"
    if not plan_path.is_file():
        raise RuntimeError("campaign plan is missing; run --stage plan first")
    return json.loads(plan_path.read_text(encoding="utf-8"))


def assert_source_freeze(
    contract_path: Path, contract: dict[str, Any], plan: dict[str, Any]
) -> None:
    current = provenance(contract_path, contract)
    expected = plan["provenance"]
    if current["contract_sha256"] != expected["contract_sha256"]:
        raise RuntimeError("contract changed after the campaign plan was frozen")
    if current["source_sha256"] != expected["source_sha256"]:
        raise RuntimeError("relevant source files changed after the campaign plan was frozen")
    if current["environment_probes"] != expected["environment_probes"]:
        raise RuntimeError("software or GPU environment changed after the campaign plan was frozen")


def run_logged(
    command: list[str],
    log_path: Path,
    cwd: Path,
    extra_env: dict[str, str] | None = None,
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    if extra_env:
        environment.update({str(key): str(value) for key, value in extra_env.items()})
    print("RUN", " ".join(command), flush=True)
    with log_path.open("w", encoding="utf-8") as output:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            stdout=output,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    if result.returncode != 0:
        raise RuntimeError(f"command failed with status {result.returncode}; see {log_path}")


def repeat_chrono_dir(contract: dict[str, Any], repeat_index: int) -> Path:
    chrono_root, _newton_root, _repeat_root = roots(contract)
    sentinel_id = str(contract["repeatability"]["sentinel_case_id"])
    return chrono_root / "repeatability" / sentinel_id / f"repeat_{repeat_index}"


def run_chrono_repeats(
    contract_path: Path,
    contract: dict[str, Any],
    plan: dict[str, Any],
    chrono_python: Path | None,
) -> None:
    assert_source_freeze(contract_path, contract, plan)
    case = plan["sentinel"]
    chrono_repo = repo_path(contract["chrono"]["repo"])
    command_prefix = (
        [str(chrono_python.resolve())]
        if chrono_python is not None
        else [str(value) for value in contract["chrono"]["command"]]
    )
    cfg = contract["chrono"]
    _chrono_root, _newton_root, repeat_root = roots(contract)
    for repeat_index in range(2):
        assert_source_freeze(contract_path, contract, plan)
        output = repeat_chrono_dir(contract, repeat_index)
        if output.exists():
            raise RuntimeError(f"refusing to reuse or overwrite repeat output: {output}")
        command = [
            *command_prefix,
            str(chrono_repo / "run_cylinder_episode.py"),
            "--episode-id", str(case["case_id"]),
            "--mass-kg", str(case["equivalent_mass_kg"]),
            "--xy", *(str(value) for value in case["center_xy_m"]),
            "--radius-m", str(case["radius_m"]),
            "--height-m", str(case["height_m"]),
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
            "--output-dir", str(output),
        ]
        if bool(cfg["vertical_guide"]):
            command.append("--vertical-guide")
        run_logged(
            command,
            repeat_root / "logs" / f"chrono_repeat_{repeat_index}.log",
            chrono_repo,
            cfg["thread_environment"],
        )


def compare_arrays(first: Path, second: Path) -> dict[str, Any]:
    left = np.load(first, allow_pickle=False)
    right = np.load(second, allow_pickle=False)
    shape_equal = left.shape == right.shape
    exact = bool(shape_equal and np.array_equal(left, right, equal_nan=True))
    if shape_equal:
        left_finite = np.isfinite(left)
        right_finite = np.isfinite(right)
        finite_pattern_equal = bool(np.array_equal(left_finite, right_finite))
        common = left_finite & right_finite
        differences = np.abs(left[common] - right[common])
    else:
        finite_pattern_equal = False
        common = np.asarray([], dtype=bool)
        differences = np.asarray([], dtype=np.float64)
    return {
        "first": str(first),
        "second": str(second),
        "first_sha256": sha256_file(first),
        "second_sha256": sha256_file(second),
        "shape_equal": shape_equal,
        "exact": exact,
        "bitwise_identical_with_equal_nan": exact,
        "finite_pattern_equal": finite_pattern_equal,
        "comparable_value_count": int(np.count_nonzero(common)),
        "compatible": bool(shape_equal and finite_pattern_equal and np.count_nonzero(common) > 0),
        "max_abs_difference": float(np.max(differences)) if differences.size else 0.0,
        "mean_abs_difference": float(np.mean(differences)) if differences.size else 0.0,
        "rmse_difference": (
            float(np.sqrt(np.mean(np.square(differences)))) if differences.size else 0.0
        ),
    }


def analyze_chrono_repeats(contract: dict[str, Any]) -> dict[str, Any]:
    first = repeat_chrono_dir(contract, 0)
    second = repeat_chrono_dir(contract, 1)
    manifests = [
        yaml.safe_load((path / "manifest.yaml").read_text(encoding="utf-8"))
        for path in (first, second)
    ]
    loading = [manifest["chrono"]["loading_convergence"] for manifest in manifests]
    state_results = {
        state: compare_arrays(
            first / manifests[0]["states"][state],
            second / manifests[1]["states"][state],
        )
        for state in ("initial", "loaded", "residual")
    }
    auxiliary = {}
    for name in ("action.json", "metrics.json", "object_pose.csv", "valid_heightmap_mask.npy"):
        auxiliary[name] = {
            "first_sha256": sha256_file(first / name),
            "second_sha256": sha256_file(second / name),
            "exact": sha256_file(first / name) == sha256_file(second / name),
        }
    checks = {
        "accepted_both": bool(loading[0]["accepted"] and loading[1]["accepted"]),
        "identical_acceptance_time": (
            loading[0]["final_sample_time_s"] == loading[1]["final_sample_time_s"]
        ),
        "exact_initial": state_results["initial"]["exact"],
        "exact_loaded": state_results["loaded"]["exact"],
        "exact_residual": state_results["residual"]["exact"],
        "exact_action": auxiliary["action.json"]["exact"],
        "exact_pose_trace": auxiliary["object_pose.csv"]["exact"],
        "exact_valid_mask": auxiliary["valid_heightmap_mask.npy"]["exact"],
    }
    compatible = bool(
        checks["accepted_both"]
        and checks["exact_valid_mask"]
        and all(value["compatible"] for value in state_results.values())
    )
    return {
        "usable": compatible,
        "variation_characterized": compatible,
        "bitwise_identical": all(checks.values()),
        "passed": compatible,
        "checks": checks,
        "loading": loading,
        "acceptance_time_abs_difference_s": abs(
            float(loading[0]["final_sample_time_s"])
            - float(loading[1]["final_sample_time_s"])
        ),
        "states": state_results,
        "auxiliary": auxiliary,
    }


def metric_bed_dir(contract: dict[str, Any], repeat_index: int) -> Path:
    _chrono_root, _newton_root, repeat_root = roots(contract)
    return repeat_root / "metric_bed" / f"repeat_{repeat_index}"


def build_metric_bed_repeats(
    contract_path: Path, contract: dict[str, Any], plan: dict[str, Any]
) -> dict[str, Any]:
    assert_source_freeze(contract_path, contract, plan)
    chrono_result = analyze_chrono_repeats(contract)
    if not chrono_result["usable"]:
        raise RuntimeError("Chrono repeats are not structurally usable; metric beds were not generated")
    cfg = contract["newton"]["metric_bed_source"]
    for repeat_index in range(2):
        output = metric_bed_dir(contract, repeat_index)
        if output.exists():
            raise RuntimeError(f"refusing to reuse or overwrite metric bed: {output}")
        manifest, _action, initial, _valid = load_episode(
            repeat_chrono_dir(contract, repeat_index)
        )
        write_metric_bed(
            output,
            initial,
            manifest,
            float(cfg["bed_depth_m"]),
            float(cfg["particle_spacing_m"]),
        )
    names = ("particles_initial_mpm.ply", "ground_plane_metadata.json")
    comparisons = {
        name: {
            "repeat_0_sha256": sha256_file(metric_bed_dir(contract, 0) / name),
            "repeat_1_sha256": sha256_file(metric_bed_dir(contract, 1) / name),
            "exact": (
                sha256_file(metric_bed_dir(contract, 0) / name)
                == sha256_file(metric_bed_dir(contract, 1) / name)
            ),
        }
        for name in names
    }
    return {
        "usable": True,
        "bitwise_identical": all(value["exact"] for value in comparisons.values()),
        "passed": True,
        "files": comparisons,
    }


def load_bed_repeatability(contract: dict[str, Any]) -> dict[str, Any]:
    names = ("particles_initial_mpm.ply", "ground_plane_metadata.json")
    comparisons = {}
    for name in names:
        first = metric_bed_dir(contract, 0) / name
        second = metric_bed_dir(contract, 1) / name
        if not first.is_file() or not second.is_file():
            return {"usable": False, "passed": False, "missing": True, "files": comparisons}
        first_digest = sha256_file(first)
        second_digest = sha256_file(second)
        comparisons[name] = {
            "repeat_0_sha256": first_digest,
            "repeat_1_sha256": second_digest,
            "exact": first_digest == second_digest,
        }
    return {
        "usable": True,
        "bitwise_identical": all(value["exact"] for value in comparisons.values()),
        "passed": True,
        "files": comparisons,
    }


def newton_repeat_dir(contract: dict[str, Any], repeat_index: int) -> Path:
    _chrono_root, _newton_root, repeat_root = roots(contract)
    return repeat_root / "newton" / f"repeat_{repeat_index}"


def run_newton_repeats(
    contract_path: Path,
    contract: dict[str, Any],
    plan: dict[str, Any],
    newton_python: Path | None,
    device_override: str | None,
) -> None:
    assert_source_freeze(contract_path, contract, plan)
    if not analyze_chrono_repeats(contract)["usable"]:
        raise RuntimeError("Chrono repeats are not structurally usable; Newton repeats were not launched")
    if not load_bed_repeatability(contract)["usable"]:
        raise RuntimeError("fresh metric beds are incomplete; Newton repeats were not launched")
    cfg = contract["newton"]
    python = (newton_python or Path(cfg["python"])).resolve()
    device = device_override or str(cfg["device"])
    for repeat_index in range(2):
        assert_source_freeze(contract_path, contract, plan)
        root = newton_repeat_dir(contract, repeat_index)
        if root.exists():
            raise RuntimeError(f"refusing to reuse or overwrite Newton repeat: {root}")
        bed = metric_bed_dir(contract, repeat_index)
        chrono = repeat_chrono_dir(contract, repeat_index)
        preparation = root / "preparation"
        prepare_command = [
            str(python),
            str(REPO_ROOT / "scripts" / "run_newton_prepared_bed.py"),
            "--config", str(repo_path(cfg["base_config"])),
            "--particles-ply", str(bed / "particles_initial_mpm.ply"),
            "--metadata-json", str(bed / "ground_plane_metadata.json"),
            "--chrono-episode", str(chrono),
            "--output-dir", str(preparation),
            "--device", device,
            "--dt-s", str(cfg["selected_dt_s"]),
            "--duration-s", str(cfg["pre_settle_duration_s"]),
            "--required-duration-s", str(cfg["pre_settle_required_duration_s"]),
            "--particle-speed-threshold-mps", str(cfg["particle_speed_threshold_mps"]),
            "--center-crop-half-width-m", "0",
            "--speed-check-every", "1",
            "--qualification-run",
        ]
        run_logged(
            prepare_command,
            root.parent.parent / "logs" / f"newton_prepare_repeat_{repeat_index}.log",
            REPO_ROOT,
        )
        response = root / "response"
        response_command = [
            str(python),
            str(REPO_ROOT / "scripts" / "run_newton_cylinder_diagnostic.py"),
            "--config", str(repo_path(cfg["base_config"])),
            "--prepared-dir", str(preparation),
            "--candidate-preparation",
            "--chrono-episode", str(chrono),
            "--output-dir", str(response),
            "--device", device,
            "--dt-s", str(cfg["selected_dt_s"]),
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
        run_logged(
            response_command,
            root.parent.parent / "logs" / f"newton_response_repeat_{repeat_index}.log",
            REPO_ROOT,
        )


def compare_npz(first: Path, second: Path) -> dict[str, Any]:
    with np.load(first, allow_pickle=False) as left, np.load(second, allow_pickle=False) as right:
        keys_equal = set(left.files) == set(right.files)
        keys = sorted(set(left.files) & set(right.files))
        arrays = {}
        for key in keys:
            shape_equal = left[key].shape == right[key].shape
            numeric = np.issubdtype(left[key].dtype, np.number) and np.issubdtype(
                right[key].dtype, np.number
            )
            exact = bool(shape_equal and np.array_equal(left[key], right[key], equal_nan=numeric))
            if shape_equal and numeric:
                left_finite = np.isfinite(left[key])
                right_finite = np.isfinite(right[key])
                finite_pattern_equal = bool(np.array_equal(left_finite, right_finite))
                common = left_finite & right_finite
                differences = np.abs(left[key][common] - right[key][common])
            else:
                finite_pattern_equal = bool(shape_equal)
                differences = np.asarray([], dtype=np.float64)
            arrays[key] = {
                "shape_equal": shape_equal,
                "exact": exact,
                "finite_pattern_equal": finite_pattern_equal,
                "compatible": bool(shape_equal and finite_pattern_equal),
                "max_abs_difference": float(np.max(differences)) if differences.size else 0.0,
                "mean_abs_difference": float(np.mean(differences)) if differences.size else 0.0,
                "rmse_difference": (
                    float(np.sqrt(np.mean(np.square(differences))))
                    if differences.size
                    else 0.0
                ),
            }
    return {
        "keys_equal": keys_equal,
        "arrays": arrays,
        "exact": bool(keys_equal and all(value["exact"] for value in arrays.values())),
        "compatible": bool(
            keys_equal and all(value["compatible"] for value in arrays.values())
        ),
    }


def analyze_newton_repeats(contract: dict[str, Any]) -> dict[str, Any]:
    roots_ = [newton_repeat_dir(contract, index) / "response" for index in range(2)]
    if not all((root / "newton_cylinder_manifest.json").is_file() for root in roots_):
        return {"usable": False, "passed": False, "missing": True}
    heightmaps = {
        state: compare_arrays(
            roots_[0] / f"{state}_heightmap_m.npy",
            roots_[1] / f"{state}_heightmap_m.npy",
        )
        for state in ("initial", "loaded", "residual")
    }
    states = {
        state: compare_npz(
            roots_[0] / f"newton_state_{state}.npz",
            roots_[1] / f"newton_state_{state}.npz",
        )
        for state in ("initial", "loaded", "residual")
    }
    plys = {}
    for state in ("initial", "loaded", "residual"):
        name = f"particles_{state}_mpm.ply"
        first_digest = sha256_file(roots_[0] / name)
        second_digest = sha256_file(roots_[1] / name)
        plys[state] = {
            "repeat_0_sha256": first_digest,
            "repeat_1_sha256": second_digest,
            "exact": first_digest == second_digest,
        }
    manifests = [
        json.loads((root / "newton_cylinder_manifest.json").read_text(encoding="utf-8"))
        for root in roots_
    ]
    environment_equal = manifests[0]["environment"] == manifests[1]["environment"]
    bitwise_identical = bool(
        environment_equal
        and all(value["exact"] for value in heightmaps.values())
        and all(value["exact"] for value in states.values())
        and all(value["exact"] for value in plys.values())
    )
    usable = bool(
        environment_equal
        and all(value["compatible"] for value in heightmaps.values())
        and all(value["compatible"] for value in states.values())
    )
    return {
        "usable": usable,
        "variation_characterized": usable,
        "bitwise_identical": bitwise_identical,
        "passed": usable,
        "environment_equal": environment_equal,
        "environments": [manifest["environment"] for manifest in manifests],
        "heightmaps": heightmaps,
        "particle_states": states,
        "particle_plys": plys,
    }


def write_summary(contract: dict[str, Any]) -> dict[str, Any]:
    _chrono_root, _newton_root, repeat_root = roots(contract)
    chrono = analyze_chrono_repeats(contract)
    bed = load_bed_repeatability(contract)
    newton = analyze_newton_repeats(contract)
    complete = bool(chrono.get("usable") and bed.get("usable") and newton.get("usable"))
    summary = {
        "schema_version": 1,
        "qualification_id": contract["qualification_id"],
        "prior_outputs_admissible": False,
        "status": "variation_characterized" if complete else "variation_incomplete_or_unusable",
        "bitwise_identity_required": False,
        "bitwise_identical": bool(
            complete
            and chrono.get("bitwise_identical")
            and bed.get("bitwise_identical")
            and newton.get("bitwise_identical")
        ),
        "matrix_expansion_permitted": complete,
        "residual_training_permitted": False,
        "chrono": chrono,
        "metric_bed": bed,
        "newton": newton,
    }
    write_json(repeat_root / "repeatability_summary.json", summary)
    return summary


def main() -> None:
    args = parse_args()
    contract_path = args.contract.resolve()
    contract = load_contract(contract_path)
    plan = write_plan(contract_path, contract) if args.stage == "plan" else load_plan(contract)
    if args.stage == "plan":
        print(json.dumps({"plan": str(roots(contract)[1] / "campaign_plan.json")}, indent=2))
        return
    if args.stage in ("chrono", "all"):
        run_chrono_repeats(contract_path, contract, plan, args.chrono_python)
        chrono = analyze_chrono_repeats(contract)
        write_json(roots(contract)[2] / "chrono_repeatability.json", chrono)
        if not chrono["usable"]:
            raise RuntimeError("Chrono repeats are structurally unusable; stopping campaign")
    if args.stage in ("bed", "all"):
        bed = build_metric_bed_repeats(contract_path, contract, plan)
        write_json(roots(contract)[2] / "metric_bed_repeatability.json", bed)
        if not bed["usable"]:
            raise RuntimeError("metric-bed generation is incomplete; stopping campaign")
    if args.stage in ("newton", "all"):
        run_newton_repeats(
            contract_path,
            contract,
            plan,
            args.newton_python,
            args.device,
        )
    summary = write_summary(contract)
    print(json.dumps({
        "status": summary["status"],
        "matrix_expansion_permitted": summary["matrix_expansion_permitted"],
        "residual_training_permitted": summary["residual_training_permitted"],
    }, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run a fixed-domain, validity-gated Newton material BayesOpt study.

Each material candidate receives a fresh qualifying preparation and a separate
continuous in-process preparation/loading/removal response. Newton numerical
settings and Chrono I/O are fixed; no Genesis state or observation is reused.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "newton_sand_smoke_voxel7p8125mm.json"
DEFAULT_METRIC_ROOT = (
    REPO_ROOT / "outputs" / "validity_experiment"
    / "A0_oracle_guided_offset_5mm_gate6mm_prepared_5mm_n128_ratio_matched"
    / "metric_bed_source"
)
DEFAULT_ORACLE = Path(
    "/data/christoa/Chrono/tera_splat_sim/validity_experiment/chrono_episodes/"
    "A0_oracle_guided_offset_5mm_gate6mm_v1"
)
DEFAULT_OUTPUT = REPO_ROOT / "outputs" / "validity_experiment" / "newton_bayesopt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--particles-ply", type=Path, default=DEFAULT_METRIC_ROOT / "particles_initial_mpm.ply")
    parser.add_argument("--metadata-json", type=Path, default=DEFAULT_METRIC_ROOT / "ground_plane_metadata.json")
    parser.add_argument("--chrono-episode", type=Path, default=DEFAULT_ORACLE)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--dt-s", type=float, default=0.00025)
    parser.add_argument("--proxy-iterations", type=int, default=8)
    parser.add_argument("--rigid-substeps", type=int, default=16)
    parser.add_argument("--pre-settle-duration-s", type=float, default=2.0)
    parser.add_argument("--count", type=int, default=0, help="Number of proposed candidates to attempt.")
    parser.add_argument("--run-one", action="store_true")
    parser.add_argument("--log10-e", type=float, default=5.0)
    parser.add_argument("--nu", type=float, default=0.2)
    parser.add_argument("--friction-coefficient", type=float, default=0.68)
    parser.add_argument("--log10-e-min", type=float, default=4.8)
    parser.add_argument("--log10-e-max", type=float, default=5.2)
    parser.add_argument("--nu-min", type=float, default=0.15)
    parser.add_argument("--nu-max", type=float, default=0.30)
    parser.add_argument("--friction-min", type=float, default=0.4)
    parser.add_argument("--friction-max", type=float, default=0.9)
    parser.add_argument(
        "--seed-result",
        type=Path,
        action="append",
        default=[],
        help="Prior valid Newton result.json to seed; repeat for multiple observations.",
    )
    parser.add_argument("--seed", type=int, default=20260914)
    return parser.parse_args()


def candidate_from_args(args: argparse.Namespace) -> dict[str, float]:
    return {"log10_e": float(args.log10_e), "nu": float(args.nu), "friction_coefficient": float(args.friction_coefficient)}


def validate(args: argparse.Namespace) -> None:
    if (args.run_one, args.count > 0).count(True) != 1:
        raise ValueError("choose exactly one of --run-one or --count N")
    if not 0 < args.dt_s or args.proxy_iterations <= 0 or args.rigid_substeps <= 0:
        raise ValueError("dt, proxy iterations, and rigid substeps must be positive")
    if not args.log10_e_min < args.log10_e_max:
        raise ValueError("log10-E bounds must be ordered")
    if not 0 < args.nu_min < args.nu_max < 0.5:
        raise ValueError("Poisson bounds must lie in (0, 0.5)")
    if not 0 <= args.friction_min < args.friction_max:
        raise ValueError("friction bounds must be ordered and nonnegative")
    for path in (args.base_config, args.particles_ply, args.metadata_json, args.chrono_episode, *args.seed_result):
        if not path.exists():
            raise ValueError(f"required input not found: {path}")


def in_bounds(candidate: dict[str, float], args: argparse.Namespace) -> bool:
    return (args.log10_e_min <= candidate["log10_e"] <= args.log10_e_max and args.nu_min <= candidate["nu"] <= args.nu_max and args.friction_min <= candidate["friction_coefficient"] <= args.friction_max)


def random_candidate(rng: np.random.Generator, args: argparse.Namespace) -> dict[str, float]:
    return {"log10_e": float(rng.uniform(args.log10_e_min, args.log10_e_max)), "nu": float(rng.uniform(args.nu_min, args.nu_max)), "friction_coefficient": float(rng.uniform(args.friction_min, args.friction_max))}


def normal_cdf(value: np.ndarray) -> np.ndarray:
    return 0.5 * (1.0 + np.vectorize(math.erf)(value / math.sqrt(2.0)))


def propose(rng: np.random.Generator, observations: list[tuple[dict[str, float], float]], args: argparse.Namespace) -> dict[str, float]:
    if len(observations) < 4:
        return random_candidate(rng, args)
    keys = ("log10_e", "nu", "friction_coefficient")
    lower = np.array((args.log10_e_min, args.nu_min, args.friction_min))
    upper = np.array((args.log10_e_max, args.nu_max, args.friction_max))
    x = np.array([[item[0][key] for key in keys] for item in observations])
    x = (x - lower) / (upper - lower)
    y = np.array([item[1] for item in observations])
    y_mean, y_std = float(y.mean()), max(float(y.std()), 1e-9)
    y = (y - y_mean) / y_std
    kernel = np.exp(-0.5 * np.sum((x[:, None] - x[None, :]) ** 2 / 0.16, axis=2))
    inverse = np.linalg.inv(kernel + 1e-6 * np.eye(len(x)))
    pool = rng.uniform(lower, upper, size=(512, 3))
    z = (pool - lower) / (upper - lower)
    cross = np.exp(-0.5 * np.sum((z[:, None] - x[None, :]) ** 2 / 0.16, axis=2))
    mean = cross @ inverse @ y
    variance = np.maximum(1.0 - np.sum((cross @ inverse) * cross, axis=1), 1e-12)
    sigma = np.sqrt(variance)
    improvement = float(np.min(y)) - mean
    standard = improvement / sigma
    ei = improvement * normal_cdf(standard) + sigma * np.exp(-0.5 * standard**2) / math.sqrt(2.0 * math.pi)
    choice = pool[int(np.argmax(ei))]
    return dict(zip(keys, map(float, choice)))


def write_config(base: Path, candidate: dict[str, float], path: Path) -> None:
    config = json.loads(base.read_text())
    material = config["material"]
    material["young_modulus_pa"] = 10.0 ** candidate["log10_e"]
    material["poisson_ratio"] = candidate["nu"]
    material["friction_coefficient"] = candidate["friction_coefficient"]
    config["status"] = "newton_bayesopt_candidate"
    config.setdefault("provenance", {})["bayesopt_candidate"] = candidate
    path.write_text(json.dumps(config, indent=2) + "\n")


def command(arguments: list[str], log: Path) -> bool:
    with log.open("w", encoding="utf-8") as output:
        result = subprocess.run(arguments, stdout=output, stderr=subprocess.STDOUT, text=True)
    return result.returncode == 0


def residual_footprint_rmse(response: Path, episode: Path) -> float:
    manifest = yaml.safe_load((episode / "manifest.yaml").read_text())
    action = json.loads((episode / manifest["action"]).read_text())
    initial = np.load(response / "initial_heightmap_m.npy")
    residual = np.load(response / "residual_heightmap_m.npy")
    chrono_initial = np.load(episode / manifest["states"]["initial"])
    chrono_residual = np.load(episode / manifest["states"]["residual"])
    valid = np.load(response / "valid_heightmap_mask.npy").astype(bool)
    rows, columns = manifest["heightmap"]["shape"]
    spacing = float(manifest["heightmap"]["spacing_m"])
    ox, oy = manifest["heightmap"]["origin_xy_m"]
    x, y = np.meshgrid(ox + np.arange(columns) * spacing, oy + np.arange(rows) * spacing)
    cx, cy = action["center_xy_m"]
    footprint = (x - cx) ** 2 + (y - cy) ** 2 <= float(action["radius_m"]) ** 2
    mask = valid & footprint
    if not np.any(mask): raise ValueError("no valid cells in residual footprint")
    error = (residual - initial) - (chrono_residual - chrono_initial)
    return float(np.sqrt(np.mean(error[mask] ** 2)))


def episode_observation_times(episode: Path) -> tuple[float, float]:
    """Read required Chrono loaded/residual observation timing from its manifest."""
    manifest = yaml.safe_load((episode / "manifest.yaml").read_text())
    try:
        loaded = float(manifest["chrono"]["loading_convergence"]["final_sample_time_s"])
        residual = float(manifest["chrono"]["residual_recovery"]["fixed_duration_s"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(
            "Chrono episode must record loaded and residual observation timing"
        ) from error
    if not math.isfinite(loaded) or loaded <= 0.0:
        raise ValueError("Chrono loaded observation time must be finite and positive")
    if not math.isfinite(residual) or residual <= 0.0:
        raise ValueError("Chrono residual observation duration must be finite and positive")
    return loaded, residual


def evaluate(args: argparse.Namespace, candidate: dict[str, float], trial: Path) -> dict[str, Any]:
    trial.mkdir(parents=True, exist_ok=False)
    config = trial / "candidate_config.json"
    write_config(args.base_config.resolve(), candidate, config)
    prepared, response = trial / "prepared", trial / "response"
    chrono_loaded_duration_s, chrono_residual_duration_s = episode_observation_times(
        args.chrono_episode.resolve()
    )
    python = sys.executable
    prep_ok = command([python, str(REPO_ROOT / "scripts" / "run_newton_prepared_bed.py"), "--config", str(config), "--particles-ply", str(args.particles_ply.resolve()), "--metadata-json", str(args.metadata_json.resolve()), "--chrono-episode", str(args.chrono_episode.resolve()), "--output-dir", str(prepared), "--device", args.device, "--dt-s", str(args.dt_s), "--duration-s", str(args.pre_settle_duration_s), "--center-crop-half-width-m", "0", "--speed-check-every", "1", "--qualification-run"], trial / "preparation.log")
    result: dict[str, Any] = {
        "candidate": candidate,
        "valid": False,
        "backend": "newton",
        "numerical_domain": {
            "dt_s": args.dt_s,
            "proxy_iterations": args.proxy_iterations,
            "rigid_substeps": args.rigid_substeps,
        },
        "observation_timing_s": {
            "chrono_loaded": chrono_loaded_duration_s,
            "chrono_residual": chrono_residual_duration_s,
            "newton_requested_loaded": chrono_loaded_duration_s,
            "newton_requested_residual": chrono_residual_duration_s,
        },
        "paths": {"prepared": str(prepared), "response": str(response)},
    }
    manifest_path = prepared / "newton_prepared_bed_manifest.json"
    if not prep_ok or not manifest_path.is_file() or not json.loads(manifest_path.read_text()).get("accepted"):
        result["failure_type"] = "candidate_preparation"
    else:
        response_ok = command([python, str(REPO_ROOT / "scripts" / "run_newton_cylinder_diagnostic.py"), "--config", str(config), "--prepared-dir", str(prepared), "--candidate-preparation", "--chrono-episode", str(args.chrono_episode.resolve()), "--output-dir", str(response), "--device", args.device, "--dt-s", str(args.dt_s), "--pre-settle-duration-s", str(args.pre_settle_duration_s), "--loaded-duration-s", str(chrono_loaded_duration_s), "--residual-duration-s", str(chrono_residual_duration_s), "--proxy-iterations", str(args.proxy_iterations), "--rigid-substeps", str(args.rigid_substeps)], trial / "response.log")
        response_manifest = response / "newton_cylinder_manifest.json"
        if not response_ok or not response_manifest.is_file():
            result["failure_type"] = "response_execution"
        else:
            data = json.loads(response_manifest.read_text())
            actual_loaded = float(data["action"]["loaded_duration_s"])
            actual_residual = float(data["action"]["residual_duration_s"])
            result["observation_timing_s"].update(
                newton_loaded=actual_loaded, newton_residual=actual_residual
            )
            if not (
                math.isclose(actual_loaded, chrono_loaded_duration_s, rel_tol=0.0, abs_tol=1.0e-12)
                and math.isclose(actual_residual, chrono_residual_duration_s, rel_tol=0.0, abs_tol=1.0e-12)
            ):
                result["failure_type"] = "response_timing_contract"
                result["acceptance_blockers"] = [
                    "Newton observation timing differs from the supplied Chrono episode."
                ]
            elif not data.get("accepted"):
                result["failure_type"] = "response_mechanics"
                result["acceptance_blockers"] = data.get("acceptance_blockers", [])
            else:
                loaded = float(data["surface"]["loaded_response_error"]["rmse_m"])
                footprint = residual_footprint_rmse(response, args.chrono_episode.resolve())
                result.update(valid=True, objective_m=loaded + 0.5 * footprint, loaded_rmse_m=loaded, residual_footprint_rmse_m=footprint)
    (trial / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    args = parse_args(); validate(args)
    root = args.output_root.resolve(); root.mkdir(parents=True, exist_ok=True)
    study = root / f"study_{int(time.time())}_{args.seed}"
    study.mkdir()
    rng = np.random.default_rng(args.seed)
    observations: list[tuple[dict[str, float], float]] = []
    for seed_path in args.seed_result:
        seed = json.loads(seed_path.resolve().read_text())
        candidate = {key: float(seed["candidate"][key]) for key in ("log10_e", "nu", "friction_coefficient")}
        if not seed.get("valid") or "objective_m" not in seed or not in_bounds(candidate, args):
            raise ValueError(f"seed result is not a valid in-bound Newton observation: {seed_path}")
        observations.append((candidate, float(seed["objective_m"])))
    attempts = 1 if args.run_one else args.count
    for iteration in range(attempts):
        candidate = candidate_from_args(args) if args.run_one else propose(rng, observations, args)
        if not in_bounds(candidate, args): raise RuntimeError("candidate escaped fixed search bounds")
        print(f"[Newton BayesOpt] iteration={iteration} candidate={candidate}", flush=True)
        result = evaluate(args, candidate, study / "trials" / f"iteration_{iteration:03d}")
        if result["valid"]:
            observations.append((candidate, float(result["objective_m"])))
            print(f"[Newton BayesOpt] valid objective={result['objective_m'] * 1e3:.3f} mm", flush=True)
        else:
            print(f"[Newton BayesOpt] invalid: {result.get('failure_type')}", flush=True)
    summary = {"backend": "newton", "study_dir": str(study), "attempts": attempts, "seed_valid_observations": len(args.seed_result), "valid_observations": len(observations), "search_bounds": {"log10_e": [args.log10_e_min, args.log10_e_max], "nu": [args.nu_min, args.nu_max], "friction_coefficient": [args.friction_min, args.friction_max]}, "fixed_numerical_domain": {"config": str(args.base_config.resolve()), "dt_s": args.dt_s, "proxy_iterations": args.proxy_iterations, "rigid_substeps": args.rigid_substeps}}
    (study / "study_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run a validity-gated four-parameter Chrono-to-Genesis W&B BayesOpt campaign.

Each particle-spacing candidate builds and accepts its own complete Genesis
state before the cylinder rollout.  This makes spacing and particle size honest
optimization variables rather than changing them after a prepared state has
already been created.  Lower-layer random XY perturbation is deliberately not
implemented: it remains a future, separately versioned model variant.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHRONO_EPISODE = REPO_ROOT.parent / "tera_splat_sim" / "validity_experiment" / "chrono_episodes" / "A0_cal_full10mm"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "outputs" / "validity_experiment" / "bayesopt" / "A0_cal_full10mm_4d"
SPACING_CHOICES_M = (0.0125, 0.020)
SIZE_RATIO_CHOICES = (0.75, 0.85, 1.00)
PARTICLE_CHOICES = (
    (0.0125, 1.00),
    (0.020, 0.75),
    (0.020, 0.85),
    (0.020, 1.00),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chrono-episode", type=Path, default=DEFAULT_CHRONO_EPISODE)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--base-config", type=Path, default=REPO_ROOT / "configs" / "physgaussian_sand_stiff_mid.json")
    parser.add_argument("--backend", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--project", default="chrono-genesis-bayesopt")
    parser.add_argument("--entity", default=None, help="Optional W&B entity; otherwise use the authenticated default.")
    parser.add_argument("--count", type=int, default=0, help="Evaluate this many candidates in one sequential W&B study run.")
    parser.add_argument(
        "--target-valid-count",
        type=int,
        default=None,
        help="Stop after this many valid objectives, including any imported seed observations.",
    )
    parser.add_argument(
        "--seed-study-dir",
        type=Path,
        action="append",
        default=[],
        help="Prior single-study directory whose valid results seed the optimizer and W&B history; repeat as needed.",
    )
    parser.add_argument("--run-one", action="store_true", help="Run one explicitly supplied candidate in one W&B study run.")
    parser.add_argument("--wandb-init-only", action="store_true", help="Authenticate through wandb.init(), log no trial, and exit.")
    parser.add_argument("--log10-e", type=float, default=5.0, help="Used only with --run-one.")
    parser.add_argument("--phi-deg", type=float, default=30.0, help="Used only with --run-one.")
    parser.add_argument("--particle-spacing-m", type=float, default=0.020, help="Used only with --run-one.")
    parser.add_argument("--particle-size-ratio", type=float, default=1.0, help="Particle size / spacing; used only with --run-one.")
    parser.add_argument("--bed-depth-m", type=float, default=0.10)
    parser.add_argument("--pre-settle-max-time", type=float, default=2.0)
    parser.add_argument("--pre-settle-required-duration", type=float, default=0.02)
    parser.add_argument("--pre-settle-particle-speed-threshold", type=float, default=5.0e-4)
    parser.add_argument("--loaded-max-time", type=float, default=1.0)
    parser.add_argument("--post-max-time", type=float, default=1.0)
    parser.add_argument("--required-duration", type=float, default=0.02)
    parser.add_argument("--residual-weight", type=float, default=0.5)
    parser.add_argument("--minimum-common-valid-fraction", type=float, default=0.95)
    parser.add_argument("--n-grid", type=int, default=64)
    parser.add_argument("--dt", type=float, default=0.001)
    parser.add_argument("--enable-cpic", action=argparse.BooleanOptionalAction, default=True)
    return parser.parse_args()


def wandb_module() -> Any:
    try:
        import wandb
    except ImportError as error:
        raise SystemExit(
            "W&B is unavailable in this environment. Install its missing runtime dependency "
            "in the tsplat environment, then retry."
        ) from error
    return wandb


def phase_reasons(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as file:
        return {row["phase"]: row["termination_reason"] for row in csv.DictReader(file)}


def candidate_from_mapping(values: dict[str, Any]) -> dict[str, float]:
    candidate = {
        "log10_E": float(values["log10_E"]),
        "phi_deg": float(values["phi_deg"]),
        "particle_spacing_m": float(values["particle_spacing_m"]),
        "particle_size_ratio": float(values["particle_size_ratio"]),
    }
    if not 4.0 <= candidate["log10_E"] <= 6.0:
        raise ValueError("log10_E must lie in [4, 6]")
    if not 15.0 <= candidate["phi_deg"] <= 45.0:
        raise ValueError("phi_deg must lie in [15, 45]")
    if candidate["particle_spacing_m"] <= 0.0 or candidate["particle_size_ratio"] <= 0.0:
        raise ValueError("particle spacing and size ratio must be positive")
    candidate["E_pa"] = 10.0 ** candidate["log10_E"]
    candidate["particle_size_m"] = candidate["particle_spacing_m"] * candidate["particle_size_ratio"]
    return candidate


def trial_directory_name(run_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", run_id)


def log_stage(
    run: Any,
    started: float,
    iteration: int,
    stage: str,
    candidate: dict[str, float],
    **extra: Any,
) -> None:
    payload: dict[str, Any] = {
        "iteration": iteration,
        "time/elapsed_s": time.perf_counter() - started,
        "stage": stage,
        "params/log10_E": candidate["log10_E"],
        "params/E_pa": candidate["E_pa"],
        "params/phi_deg": candidate["phi_deg"],
        "params/particle_spacing_m": candidate["particle_spacing_m"],
        "params/particle_size_ratio": candidate["particle_size_ratio"],
        "params/particle_size_m": candidate["particle_size_m"],
        **extra,
    }
    run.log(payload)


def define_history(run: Any) -> None:
    run.define_metric("iteration")
    for metric in (
        "params/*", "loss/*", "dem/*", "diagnostic/*", "objective/m", "valid", "stage",
        "settling/*", "surface_match/*", "bridge/*", "time/elapsed_s",
    ):
        run.define_metric(metric, step_metric="iteration")


def load_target(episode_dir: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    initial = np.load(episode_dir / "initial_heightmap_m.npy")
    loaded = np.load(episode_dir / "loaded_heightmap_m.npy")
    residual = np.load(episode_dir / "residual_heightmap_m.npy")
    valid = np.load(episode_dir / "valid_heightmap_mask.npy").astype(bool)
    if initial.shape != loaded.shape or initial.shape != residual.shape or initial.shape != valid.shape:
        raise ValueError("Chrono target heightmaps and valid mask have inconsistent shapes")
    return initial, loaded, residual, valid


def dem_error_metrics(error_map: np.ndarray, valid: np.ndarray, phase: str, output_dir: Path) -> dict[str, float]:
    """Persist a masked Genesis-minus-Chrono DEM and summarize its real cells."""
    masked_error = np.full(error_map.shape, np.nan, dtype=np.float64)
    masked_error[valid] = error_map[valid]
    np.save(output_dir / f"{phase}_dem_difference_m.npy", masked_error)
    values = masked_error[valid]
    return {
        f"{phase}_rmse_m": float(np.sqrt(np.mean(values**2))),
        f"{phase}_mae_m": float(np.mean(np.abs(values))),
        f"{phase}_mean_signed_m": float(np.mean(values)),
        f"{phase}_min_signed_m": float(np.min(values)),
        f"{phase}_max_signed_m": float(np.max(values)),
        f"{phase}_p05_signed_m": float(np.quantile(values, 0.05)),
        f"{phase}_p95_signed_m": float(np.quantile(values, 0.95)),
    }


def compute_loss(episode_dir: Path, bridge_dir: Path, minimum_fraction: float, residual_weight: float) -> dict[str, float]:
    chrono_initial, chrono_loaded, chrono_residual, chrono_valid = load_target(episode_dir)
    genesis_initial = np.load(bridge_dir / "initial_heightmap_m.npy")
    genesis_loaded = np.load(bridge_dir / "loaded_heightmap_m.npy")
    genesis_residual = np.load(bridge_dir / "residual_heightmap_m.npy")
    genesis_valid = np.load(bridge_dir / "valid_heightmap_mask.npy").astype(bool)
    if genesis_initial.shape != chrono_initial.shape:
        raise ValueError("Genesis result does not use the Chrono target grid")
    valid = chrono_valid & genesis_valid
    common_cells = int(np.count_nonzero(valid))
    target_cells = int(np.count_nonzero(chrono_valid))
    fraction = common_cells / max(target_cells, 1)
    if fraction < minimum_fraction:
        raise ValueError(f"common valid fraction {fraction:.4f} is below {minimum_fraction:.4f}")
    loaded_error = (genesis_loaded - genesis_initial) - (chrono_loaded - chrono_initial)
    residual_error = (genesis_residual - genesis_initial) - (chrono_residual - chrono_initial)
    np.save(bridge_dir / "common_valid_mask.npy", valid)
    loaded_metrics = dem_error_metrics(loaded_error, valid, "loaded", bridge_dir)
    residual_metrics = dem_error_metrics(residual_error, valid, "residual", bridge_dir)
    return {
        "objective_m": loaded_metrics["loaded_rmse_m"] + residual_weight * residual_metrics["residual_rmse_m"],
        "common_valid_cells": common_cells,
        "common_valid_fraction": fraction,
        **loaded_metrics,
        **residual_metrics,
    }


def run_command(command: list[str]) -> None:
    subprocess.run(command, check=True, cwd=REPO_ROOT)


def evaluate_candidate(
    args: argparse.Namespace,
    run: Any,
    candidate_values: dict[str, Any],
    trial_dir: Path,
    iteration: int,
    started: float,
) -> dict[str, Any]:
    """Evaluate one candidate without creating a child W&B run."""
    result: dict[str, Any] = {"valid": False, "iteration": iteration}
    try:
        candidate = candidate_from_mapping(candidate_values)
        if trial_dir.exists():
            raise RuntimeError(f"Refusing to overwrite existing trial directory: {trial_dir}")
        trial_dir.mkdir(parents=True)
        material_config = json.loads(args.base_config.read_text(encoding="utf-8"))
        material_config["E"] = candidate["E_pa"]
        material_config["friction_angle"] = candidate["phi_deg"]
        material_config_path = trial_dir / "material_config.json"
        material_config_path.write_text(json.dumps(material_config, indent=2) + "\n", encoding="utf-8")
        (trial_dir / "candidate.json").write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")
        log_stage(run, started, iteration, "candidate", candidate)

        prepared_root = trial_dir / "prepared"
        build_command = [
            sys.executable, str(REPO_ROOT / "scripts" / "build_chrono_settled_bed.py"),
            "--chrono-episode", str(args.chrono_episode.resolve()),
            "--output-dir", str(prepared_root),
            "--config", str(material_config_path),
            "--backend", args.backend,
            "--bed-depth-m", str(args.bed_depth_m),
            "--particle-spacing-m", str(candidate["particle_spacing_m"]),
            "--particle-size", str(candidate["particle_size_m"]),
            "--pre-settle-max-time", str(args.pre_settle_max_time),
            "--pre-settle-required-duration", str(args.pre_settle_required_duration),
            "--pre-settle-particle-speed-threshold", str(args.pre_settle_particle_speed_threshold),
            "--n-grid", str(args.n_grid),
            "--dt", str(args.dt),
        ]
        if args.enable_cpic:
            build_command.append("--enable-cpic")
        run_command(build_command)
        prepared_manifest = json.loads((prepared_root / "prepared_bed_manifest.json").read_text(encoding="utf-8"))
        if not prepared_manifest.get("accepted", False):
            raise RuntimeError("builder returned a rejected prepared bed")
        log_stage(
            run,
            started,
            iteration,
            "prepared",
            candidate,
            **{
                "settling/duration_s": prepared_manifest["settling"]["duration_s"],
                "settling/final_particle_speed_p99_mps": prepared_manifest["settling"]["final_particle_speed_p99_mps"],
                "surface_match/rmse_m": prepared_manifest["surface_match"]["rmse_m"],
                "surface_match/max_abs_m": prepared_manifest["surface_match"]["max_abs_m"],
            },
        )

        bridge_dir = trial_dir / "bridge"
        bridge_command = [
            sys.executable, str(REPO_ROOT / "scripts" / "run_chrono_genesis_bridge.py"),
            "--chrono-episode", str(args.chrono_episode.resolve()),
            "--prepared-bed", str(prepared_root / "prepared_bed"),
            "--output-dir", str(bridge_dir),
            "--config", str(material_config_path),
            "--backend", args.backend,
            "--particle-spacing-m", str(candidate["particle_spacing_m"]),
            "--loaded-max-time", str(args.loaded_max_time),
            "--post-max-time", str(args.post_max_time),
            "--required-duration", str(args.required_duration),
        ]
        run_command(bridge_command)
        reasons = phase_reasons(bridge_dir / "genesis_raw" / "phase_summary.csv")
        loss = compute_loss(args.chrono_episode.resolve(), bridge_dir, args.minimum_common_valid_fraction, args.residual_weight)
        dem_payload = {f"dem/{name}": value for name, value in loss.items() if name != "objective_m"}
        if reasons.get("loaded") != "equilibrium" or reasons.get("post_removal") != "equilibrium":
            result = {
                "valid": False,
                "failure_type": "non_equilibrium",
                "failure": f"bridge did not settle: {reasons}",
                "candidate": candidate,
                "phase_reasons": reasons,
                **loss,
            }
            log_stage(
                run,
                started,
                iteration,
                "invalid",
                candidate,
                valid=0,
                **{
                    "bridge/loaded_reason": reasons.get("loaded"),
                    "bridge/post_reason": reasons.get("post_removal"),
                    "diagnostic/objective_m": loss["objective_m"],
                    **dem_payload,
                },
            )
            return result
        log_stage(
            run,
            started,
            iteration,
            "bridge",
            candidate,
            **{"bridge/loaded_reason": reasons["loaded"], "bridge/post_reason": reasons["post_removal"]},
        )

        result = {"valid": True, "candidate": candidate, "phase_reasons": reasons, **loss}
        log_stage(
            run,
            started,
            iteration,
            "objective",
            candidate,
            valid=1,
            **{
                "objective/m": loss["objective_m"],
                "diagnostic/objective_m": loss["objective_m"],
                "loss/loaded_rmse_m": loss["loaded_rmse_m"],
                "loss/residual_rmse_m": loss["residual_rmse_m"],
                "loss/common_valid_fraction": loss["common_valid_fraction"],
                "loss/common_valid_cells": loss["common_valid_cells"],
                **dem_payload,
            },
        )
    except Exception as error:  # A failed settle/contact evaluation is an invalid sample, not a BO observation.
        result = {"valid": False, "iteration": iteration, "failure_type": type(error).__name__, "failure": str(error)}
        candidate = locals().get("candidate")
        if candidate is not None:
            result["candidate"] = candidate
            log_stage(run, started, iteration, "invalid", candidate, valid=0, failure_type=type(error).__name__)
        else:
            run.log({"iteration": iteration, "time/elapsed_s": time.perf_counter() - started, "stage": "invalid", "valid": 0, "failure_type": type(error).__name__})
    (trial_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def halton(index: int, base: int) -> float:
    value = 0.0
    scale = 1.0
    while index:
        index, remainder = divmod(index, base)
        scale /= base
        value += remainder * scale
    return value


def bootstrap_candidate(iteration: int) -> dict[str, float]:
    """A deterministic, space-filling start that begins at the known valid point."""
    if iteration == 0:
        return {"log10_E": 5.0, "phi_deg": 45.0, "particle_spacing_m": 0.020, "particle_size_ratio": 1.0}
    index = iteration + 1
    return {
        "log10_E": 4.0 + 2.0 * halton(index, 2),
        "phi_deg": 15.0 + 30.0 * halton(index, 3),
        "particle_spacing_m": PARTICLE_CHOICES[min(int(halton(index, 5) * len(PARTICLE_CHOICES)), len(PARTICLE_CHOICES) - 1)][0],
        "particle_size_ratio": PARTICLE_CHOICES[min(int(halton(index, 5) * len(PARTICLE_CHOICES)), len(PARTICLE_CHOICES) - 1)][1],
    }


def candidate_vector(candidate: dict[str, float]) -> np.ndarray:
    return np.asarray(
        [
            (candidate["log10_E"] - 4.0) / 2.0,
            (candidate["phi_deg"] - 15.0) / 30.0,
            SPACING_CHOICES_M.index(candidate["particle_spacing_m"]) / max(len(SPACING_CHOICES_M) - 1, 1),
            SIZE_RATIO_CHOICES.index(candidate["particle_size_ratio"]) / max(len(SIZE_RATIO_CHOICES) - 1, 1),
        ],
        dtype=np.float64,
    )


def propose_candidate(iteration: int, observations: list[tuple[dict[str, float], float]]) -> dict[str, float]:
    if len(observations) < 3:
        return bootstrap_candidate(iteration)
    rng = np.random.default_rng(10_000 + iteration)
    pool = []
    for _ in range(1024):
        spacing, size_ratio = PARTICLE_CHOICES[int(rng.integers(len(PARTICLE_CHOICES)))]
        pool.append(
            {
                "log10_E": float(rng.uniform(4.0, 6.0)),
                "phi_deg": float(rng.uniform(15.0, 45.0)),
                "particle_spacing_m": spacing,
                "particle_size_ratio": size_ratio,
            }
        )
    x_train = np.asarray([candidate_vector(candidate) for candidate, _loss in observations])
    y = np.asarray([loss for _candidate, loss in observations], dtype=np.float64)
    y_mean = float(y.mean())
    y_scale = max(float(y.std()), 1.0e-6)
    y_normalized = (y - y_mean) / y_scale
    squared_distance = np.sum((x_train[:, None, :] - x_train[None, :, :]) ** 2, axis=2)
    kernel = np.exp(-0.5 * squared_distance / (0.35**2)) + np.eye(len(x_train)) * 1.0e-6
    inverse_kernel = np.linalg.inv(kernel)
    x_pool = np.asarray([candidate_vector(candidate) for candidate in pool])
    cross = np.exp(-0.5 * np.sum((x_pool[:, None, :] - x_train[None, :, :]) ** 2, axis=2) / (0.35**2))
    mean = cross @ inverse_kernel @ y_normalized
    variance = np.maximum(1.0 - np.einsum("ij,jk,ik->i", cross, inverse_kernel, cross), 1.0e-12)
    sigma = np.sqrt(variance)
    improvement = float(np.min(y_normalized)) - mean
    z = improvement / sigma
    normal_cdf = 0.5 * (1.0 + np.vectorize(math.erf)(z / math.sqrt(2.0)))
    normal_pdf = np.exp(-0.5 * z**2) / math.sqrt(2.0 * math.pi)
    expected_improvement = improvement * normal_cdf + sigma * normal_pdf
    return pool[int(np.argmax(expected_improvement))]


def load_seed_results(study_dir: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for path in sorted((study_dir / "trials").glob("iteration_*/result.json")):
        with path.open(encoding="utf-8") as file:
            result = json.load(file)
        if result.get("valid") and "candidate" in result and "objective_m" in result:
            result["_source_path"] = str(path)
            results.append(result)
    return results


def run_study(args: argparse.Namespace, wandb: Any, count: int) -> None:
    run = wandb.init(project=args.project, entity=args.entity, job_type="chrono-genesis-bayesopt-study")
    define_history(run)
    started = time.perf_counter()
    study_dir = args.output_root.resolve() / f"study_{trial_directory_name(run.id)}"
    study_dir.mkdir(parents=True, exist_ok=False)
    seed_results = [result for seed_dir in args.seed_study_dir for result in load_seed_results(seed_dir.resolve())]
    observations = [(candidate_from_mapping(result["candidate"]), float(result["objective_m"])) for result in seed_results]
    target_valid_count = args.target_valid_count if args.target_valid_count is not None else len(observations) + count
    if target_valid_count <= 0:
        raise ValueError("target valid count must be positive")
    run.config.update(
        {
            "optimizer": "fixed-kernel Gaussian process expected improvement",
            "max_new_attempts": count,
            "target_valid_count": target_valid_count,
            "seed_valid_count": len(seed_results),
            "seed_study_dirs": [str(seed_dir.resolve()) for seed_dir in args.seed_study_dir],
        },
        allow_val_change=True,
    )
    print(
        f"[BayesOpt] study={run.id} started; target_valid={target_valid_count}; "
        f"seed_valid={len(seed_results)}; max_new_attempts={count}; output={study_dir}",
        flush=True,
    )
    for iteration, result in enumerate(seed_results):
        candidate = candidate_from_mapping(result["candidate"])
        dem_payload = {
            f"dem/{name}": value
            for name, value in result.items()
            if name.endswith("_m") or name in {"common_valid_cells", "common_valid_fraction"}
        }
        log_stage(
            run,
            started,
            iteration,
            "seed",
            candidate,
            valid=1,
            source="imported_prior_study",
            **{"objective/m": result["objective_m"], "diagnostic/objective_m": result["objective_m"], **dem_payload},
        )
    completed_new_attempts = 0
    while completed_new_attempts < count and len(observations) < target_valid_count:
        iteration = len(seed_results) + completed_new_attempts
        candidate = propose_candidate(iteration, observations)
        print(
            "[BayesOpt] "
            f"iteration={iteration + 1} started "
            f"E=10^{candidate['log10_E']:.4f}, phi={candidate['phi_deg']:.3f}, "
            f"spacing={candidate['particle_spacing_m'] * 1e3:.1f}mm, "
            f"size_ratio={candidate['particle_size_ratio']:.2f}",
            flush=True,
        )
        result = evaluate_candidate(args, run, candidate, study_dir / "trials" / f"iteration_{iteration:03d}", iteration, started)
        if result.get("valid"):
            observations.append((candidate_from_mapping(candidate), float(result["objective_m"])))
            print(
                f"[BayesOpt] iteration={iteration + 1} complete: valid; "
                f"objective={float(result['objective_m']) * 1e3:.3f}mm; "
                f"valid_observations={len(observations)}",
                flush=True,
            )
        else:
            print(
                f"[BayesOpt] iteration={iteration + 1} complete: invalid; "
                f"reason={result.get('failure_type', 'unknown')}; "
                f"valid_observations={len(observations)}",
                flush=True,
            )
        completed_new_attempts += 1
        run.summary["study/valid_observations"] = len(observations)
        run.summary["study/completed_iterations"] = len(seed_results) + completed_new_attempts
    print(
        f"[BayesOpt] study={run.id} complete; valid_observations={len(observations)}; "
        f"target_reached={len(observations) >= target_valid_count}",
        flush=True,
    )
    run.finish()


def run_one(args: argparse.Namespace, wandb: Any) -> None:
    candidate = {
        "log10_E": args.log10_e,
        "phi_deg": args.phi_deg,
        "particle_spacing_m": args.particle_spacing_m,
        "particle_size_ratio": args.particle_size_ratio,
    }
    run = wandb.init(project=args.project, entity=args.entity, job_type="chrono-genesis-bayesopt-study", config=candidate)
    define_history(run)
    started = time.perf_counter()
    study_dir = args.output_root.resolve() / f"study_{trial_directory_name(run.id)}"
    study_dir.mkdir(parents=True, exist_ok=False)
    evaluate_candidate(args, run, candidate, study_dir / "trials" / "iteration_000", 0, started)
    run.finish()


def init_only(args: argparse.Namespace, wandb: Any) -> None:
    run = wandb.init(project=args.project, entity=args.entity, job_type="bayesopt-init", config={"campaign": "chrono-genesis-4d"})
    define_history(run)
    run.log({"time/elapsed_s": 0.0, "stage": "initialized", "init_only": 1})
    receipt = {"project": run.project, "entity": run.entity, "run_id": run.id, "mode": "wandb.init_only"}
    args.output_root.resolve().mkdir(parents=True, exist_ok=True)
    (args.output_root.resolve() / "wandb_init.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    run.finish()
    print(json.dumps(receipt))


def main() -> None:
    args = parse_args()
    if sum((args.wandb_init_only, args.run_one, args.count > 0)) != 1:
        raise SystemExit("Choose exactly one mode: --wandb-init-only, --run-one, or --count N.")
    if not args.chrono_episode.is_dir():
        raise SystemExit(f"Chrono episode not found: {args.chrono_episode}")
    if not args.base_config.is_file():
        raise SystemExit(f"Material config not found: {args.base_config}")
    wandb = wandb_module()
    if args.wandb_init_only:
        init_only(args, wandb)
        return
    if args.run_one:
        run_one(args, wandb)
        return
    run_study(args, wandb, args.count)


if __name__ == "__main__":
    main()

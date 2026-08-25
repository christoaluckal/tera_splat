#!/usr/bin/env python3
"""Run one Genesis gravity-cylinder episode from a canonical Chrono export."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

from chrono_episode_bridge import (
    load_episode,
    project_surface_to_chrono_grid,
)
from particle_io import read_particle_ply


REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chrono-episode", type=Path, required=True)
    parser.add_argument(
        "--prepared-bed",
        type=Path,
        required=True,
        help="accepted prepared_bed directory emitted by build_chrono_settled_bed.py",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=REPO_ROOT / "configs" / "physgaussian_sand_stiff_mid.json")
    parser.add_argument("--backend", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--bed-depth-m", type=float, default=0.10)
    parser.add_argument("--particle-spacing-m", type=float, default=None)
    parser.add_argument("--loaded-max-time", type=float, default=0.25)
    parser.add_argument("--post-max-time", type=float, default=0.25)
    parser.add_argument(
        "--post-observation-times",
        type=float,
        nargs="+",
        default=None,
        help="Fixed post-removal times to export as surface checkpoints; requires --post-max-time to cover the final time.",
    )
    parser.add_argument("--required-duration", type=float, default=0.02)
    parser.add_argument("--residual-weight", type=float, default=0.5)
    parser.add_argument("--candidate-pre-settle-max-time", type=float, default=1.0)
    parser.add_argument("--candidate-pre-settle-required-duration", type=float, default=0.02)
    parser.add_argument("--candidate-pre-settle-speed-threshold", type=float, default=5.0e-4)
    parser.add_argument(
        "--candidate-initial-hold-time",
        type=float,
        default=0.25,
        help="Fixed no-action hold after candidate preparation used to measure restored Genesis-state surface drift.",
    )
    parser.add_argument(
        "--candidate-initial-hold-rmse-tolerance",
        type=float,
        default=5.0e-4,
        help="Maximum projected-surface RMSE permitted over the no-action initial-state hold, in meters.",
    )
    parser.add_argument(
        "--candidate-initial-hold-max-abs-tolerance",
        type=float,
        default=1.0e-3,
        help="Maximum absolute projected-surface change permitted over the no-action initial-state hold, in meters.",
    )
    parser.add_argument("--containment-wall-height", type=float, default=None)
    parser.add_argument("--containment-wall-thickness", type=float, default=None)
    parser.add_argument("--removal-speed", type=float, default=0.005)
    parser.add_argument("--max-removal-steps", type=int, default=0)
    parser.add_argument("--n-grid", type=int, default=64)
    parser.add_argument("--particle-size", type=float, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    episode_dir = args.chrono_episode.resolve()
    output_dir = args.output_dir.resolve()
    if output_dir.exists():
        raise SystemExit(f"Refusing to overwrite existing output directory: {output_dir}")
    manifest, action, initial, chrono_valid_mask = load_episode(episode_dir)
    prepared_dir = args.prepared_bed.resolve()
    prepared_manifest_path = prepared_dir.parent / "prepared_bed_manifest.json"
    if not prepared_manifest_path.is_file():
        raise SystemExit(f"Prepared-bed manifest not found beside {prepared_dir}")
    with prepared_manifest_path.open("r", encoding="utf-8") as file:
        prepared = json.load(file)
    if not prepared.get("accepted", False):
        raise SystemExit("Refusing to run a cylinder episode from a rejected prepared bed")
    if Path(prepared["source_chrono_episode"]).resolve() != episode_dir:
        raise SystemExit("Prepared bed was built from a different Chrono episode")
    state_path = prepared_dir / "mpm_state.npz"
    particle_path = prepared_dir / "particles_initial_mpm.ply"
    metadata_path = prepared_dir / "ground_plane_metadata.json"
    if not (state_path.is_file() and particle_path.is_file() and metadata_path.is_file()):
        raise SystemExit("Prepared bed is missing particles, metadata, or complete MPM state")
    spacing = float(args.particle_spacing_m or manifest["heightmap"]["spacing_m"])
    output_dir.mkdir(parents=True)
    containment_height = float(
        prepared["settling"]["containment_wall_height_m"]
        if args.containment_wall_height is None else args.containment_wall_height
    )
    containment_thickness = float(
        prepared["settling"]["containment_wall_thickness_m"]
        if args.containment_wall_thickness is None else args.containment_wall_thickness
    )
    runner = REPO_ROOT / "scripts" / "run_mass_controlled_terrain.py"
    common_solver_args = [
        "--initial-particles-ply", str(particle_path),
        "--initial-metadata-json", str(metadata_path),
        "--config", str(args.config.resolve()),
        "--containment-wall-height", str(containment_height),
        "--containment-wall-thickness", str(containment_thickness),
        "--backend", args.backend,
        "--n-grid", str(prepared["settling"].get("n_grid", args.n_grid)),
        "--particle-size", str(prepared["settling"].get("particle_size_m", args.particle_size or 0.0125)),
        "--dt", str(prepared["settling"].get("dt_s", 0.0005)),
    ]
    if prepared["settling"].get("enable_cpic", False):
        common_solver_args.append("--enable-cpic")

    candidate_prepare_dir = output_dir / "candidate_prepare_raw"
    prepare_command = [
        sys.executable, str(runner),
        *common_solver_args,
        "--initial-mpm-state-npz", str(state_path),
        "--reinitialize-geostatic-stress-from-state",
        "--geostatic-stress-scale", str(prepared["settling"].get("geostatic_stress_scale", 1.0)),
        "--output-dir", str(candidate_prepare_dir),
        "--pre-settle-only",
        "--pre-settle-max-time", str(args.candidate_pre_settle_max_time),
        "--pre-settle-required-duration", str(args.candidate_pre_settle_required_duration),
        "--pre-settle-particle-speed-threshold", str(args.candidate_pre_settle_speed_threshold),
        "--require-pre-settle",
    ]
    subprocess.run(prepare_command, check=True, cwd=REPO_ROOT)

    candidate_points = read_particle_ply(candidate_prepare_dir / "particles_initial_mpm.ply")
    candidate_h0, candidate_supported = project_surface_to_chrono_grid(candidate_points, manifest, 1.51 * spacing)
    candidate_valid = chrono_valid_mask & candidate_supported
    if not np.any(candidate_valid):
        raise RuntimeError("Candidate stress initialization supports no Chrono-valid H0 cells")
    candidate_h0_error = candidate_h0[candidate_valid] - initial[candidate_valid]
    candidate_h0_rmse = float(np.sqrt(np.mean(candidate_h0_error**2)))
    candidate_h0_max_abs = float(np.max(np.abs(candidate_h0_error)))
    rmse_tolerance = float(prepared["surface_match"]["rmse_tolerance_m"])
    max_abs_tolerance = float(prepared["surface_match"]["max_abs_tolerance_m"])
    if candidate_h0_rmse > rmse_tolerance or candidate_h0_max_abs > max_abs_tolerance:
        raise RuntimeError(
            "Candidate stress initialization failed frozen H0 gate: "
            f"rmse={candidate_h0_rmse:.6g}, max={candidate_h0_max_abs:.6g}"
        )

    candidate_initial_stability: dict[str, float | int | str | bool] = {
        "enabled": bool(args.candidate_initial_hold_time > 0.0),
        "hold_time_s": float(args.candidate_initial_hold_time),
    }
    if args.candidate_initial_hold_time > 0.0:
        initial_hold_dir = output_dir / "candidate_initial_hold_raw"
        initial_hold_command = [
            sys.executable, str(runner),
            *common_solver_args,
            "--initial-mpm-state-npz", str(candidate_prepare_dir / "mpm_state.npz"),
            "--output-dir", str(initial_hold_dir),
            "--pre-settle-only",
            "--pre-settle-max-time", str(args.candidate_initial_hold_time),
            "--pre-settle-run-full-duration",
            "--pre-settle-required-duration", str(args.candidate_pre_settle_required_duration),
            "--pre-settle-particle-speed-threshold", str(args.candidate_pre_settle_speed_threshold),
            "--require-pre-settle",
        ]
        subprocess.run(initial_hold_command, check=True, cwd=REPO_ROOT)
        hold_start_points = read_particle_ply(initial_hold_dir / "particles_unsettled_mpm.ply")
        hold_end_points = read_particle_ply(initial_hold_dir / "particles_initial_mpm.ply")
        hold_start_map, hold_start_supported = project_surface_to_chrono_grid(hold_start_points, manifest, 1.51 * spacing)
        hold_end_map, hold_end_supported = project_surface_to_chrono_grid(hold_end_points, manifest, 1.51 * spacing)
        hold_valid = chrono_valid_mask & hold_start_supported & hold_end_supported
        if not np.any(hold_valid):
            raise RuntimeError("Candidate initial no-action hold supports no Chrono-valid cells")
        hold_delta = hold_end_map[hold_valid] - hold_start_map[hold_valid]
        hold_rmse = float(np.sqrt(np.mean(hold_delta**2)))
        hold_max_abs = float(np.max(np.abs(hold_delta)))
        candidate_initial_stability.update(
            {
                "valid_cells": int(np.count_nonzero(hold_valid)),
                "surface_change_rmse_m": hold_rmse,
                "surface_change_max_abs_m": hold_max_abs,
                "surface_change_mean_signed_m": float(np.mean(hold_delta)),
                "surface_change_min_signed_m": float(np.min(hold_delta)),
                "surface_change_max_signed_m": float(np.max(hold_delta)),
                "rmse_tolerance_m": float(args.candidate_initial_hold_rmse_tolerance),
                "max_abs_tolerance_m": float(args.candidate_initial_hold_max_abs_tolerance),
                "raw_output": str(initial_hold_dir),
            }
        )
        if hold_rmse > args.candidate_initial_hold_rmse_tolerance or hold_max_abs > args.candidate_initial_hold_max_abs_tolerance:
            raise RuntimeError(
                "Candidate initial no-action hold failed stability gate: "
                f"rmse={hold_rmse:.6g}, max={hold_max_abs:.6g}"
            )

    raw_dir = output_dir / "genesis_raw"
    command = [
        sys.executable, str(runner),
        *common_solver_args,
        "--initial-mpm-state-npz", str(candidate_prepare_dir / "mpm_state.npz"),
        "--output-dir", str(raw_dir),
        "--query-xy", str(action["center_xy_m"][0]), str(action["center_xy_m"][1]),
        "--indenter-radius", str(action["radius_m"]),
        "--indenter-height", str(action["height_m"]),
        "--indenter-mass", str(action["mass_kg"]),
        "--start-clearance", str(action["start_clearance_m"]),
        "--loaded-max-time", str(args.loaded_max_time),
        "--post-max-time", str(args.post_max_time),
        "--required-duration", str(args.required_duration),
        *( ["--post-observation-times", *(str(value) for value in args.post_observation_times)] if args.post_observation_times else []),
        "--removal-mode", str(action.get("removal", "lift")),
        "--removal-speed", str(args.removal_speed),
        "--max-removal-steps", str(args.max_removal_steps),
    ]
    subprocess.run(command, check=True, cwd=REPO_ROOT)

    unsettled_points = read_particle_ply(raw_dir / "particles_unsettled_mpm.ply")
    initial_points = read_particle_ply(raw_dir / "particles_initial_mpm.ply")
    loaded_points = read_particle_ply(raw_dir / "particles_loaded_mpm.ply")
    residual_points = read_particle_ply(raw_dir / "particles_final_mpm.ply")
    max_fill = 1.51 * spacing
    unsettled_map, unsettled_supported = project_surface_to_chrono_grid(unsettled_points, manifest, max_fill)
    initial_map, initial_supported = project_surface_to_chrono_grid(initial_points, manifest, max_fill)
    loaded_map, loaded_supported = project_surface_to_chrono_grid(loaded_points, manifest, max_fill)
    residual_map, residual_supported = project_surface_to_chrono_grid(residual_points, manifest, max_fill)
    valid_mask = chrono_valid_mask & unsettled_supported & initial_supported & loaded_supported & residual_supported
    np.save(output_dir / "initial_heightmap_m.npy", initial_map)
    np.save(output_dir / "unsettled_heightmap_m.npy", unsettled_map)
    np.save(output_dir / "loaded_heightmap_m.npy", loaded_map)
    np.save(output_dir / "residual_heightmap_m.npy", residual_map)
    np.save(output_dir / "valid_heightmap_mask.npy", valid_mask)

    post_observation_summary: list[dict] = []
    observations_csv = raw_dir / "post_removal_observations.csv"
    if observations_csv.is_file():
        chrono_loaded = np.load(episode_dir / manifest["states"]["loaded"])
        chrono_residual = np.load(episode_dir / manifest["states"]["residual"])
        common_loaded_valid = chrono_valid_mask & initial_supported & loaded_supported
        loaded_error = (loaded_map - initial_map) - (chrono_loaded - initial)
        loaded_rmse = float(np.sqrt(np.mean(loaded_error[common_loaded_valid] ** 2)))
        previous_map: np.ndarray | None = None
        previous_supported: np.ndarray | None = None
        with observations_csv.open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                requested_time = float(row["requested_time_s"])
                tag = f"{requested_time:.3f}s".replace(".", "p")
                checkpoint_path = raw_dir / f"particles_post_removal_{tag}_mpm.ply"
                checkpoint_points = read_particle_ply(checkpoint_path)
                checkpoint_map, checkpoint_supported = project_surface_to_chrono_grid(checkpoint_points, manifest, max_fill)
                checkpoint_valid = chrono_valid_mask & checkpoint_supported
                np.save(output_dir / f"residual_heightmap_{tag}.npy", checkpoint_map)
                residual_error = (checkpoint_map - initial_map) - (chrono_residual - initial)
                residual_rmse = float(np.sqrt(np.mean(residual_error[checkpoint_valid] ** 2)))
                summary = {
                    "requested_time_s": requested_time,
                    "actual_time_s": float(row["actual_time_s"]),
                    "first_equilibrium_time_s": None if not row["first_equilibrium_time_s"] else float(row["first_equilibrium_time_s"]),
                    "checkpoint_particles": str(checkpoint_path),
                    "residual_heightmap": str(output_dir / f"residual_heightmap_{tag}.npy"),
                    "valid_cells": int(np.count_nonzero(checkpoint_valid)),
                    "particle_speed_percentiles_mps": {key: float(value) for key, value in row.items() if key.startswith("particle_speed_p")},
                    "residual_rmse_m": residual_rmse,
                    "objective_m": loaded_rmse + args.residual_weight * residual_rmse,
                }
                if previous_map is not None and previous_supported is not None:
                    pair_valid = chrono_valid_mask & checkpoint_supported & previous_supported
                    delta = checkpoint_map[pair_valid] - previous_map[pair_valid]
                    summary["residual_dem_change_from_previous_rmse_m"] = float(np.sqrt(np.mean(delta**2)))
                    summary["residual_dem_change_from_previous_max_abs_m"] = float(np.max(np.abs(delta)))
                    summary["residual_dem_change_cells"] = int(np.count_nonzero(pair_valid))
                post_observation_summary.append(summary)
                previous_map = checkpoint_map
                previous_supported = checkpoint_supported
        with (output_dir / "post_removal_observations.json").open("w", encoding="utf-8") as file:
            json.dump(post_observation_summary, file, indent=2)
    shutil.copy2(episode_dir / "action.json", output_dir / "action.json")
    shutil.copy2(episode_dir / "manifest.yaml", output_dir / "chrono_manifest.yaml")
    bridge_manifest = {
        "schema_version": 1,
        "source_chrono_episode": str(episode_dir),
        "coordinate_frame": manifest["coordinate_frame"],
        "heightmap": manifest["heightmap"],
        "prepared_bed": {
            "path": str(prepared_dir),
            "manifest": str(prepared_manifest_path),
            "accepted": True,
            "state": "complete MPM restore (pos, vel, C, F, Jp, active)",
        },
        "surface_projection": {
            "method": "highest_particle_per_Chrono_cell_then_nearest_fill",
            "max_fill_distance_m": max_fill,
            "valid_cells": int(np.count_nonzero(valid_mask)),
            "total_cells": int(valid_mask.size),
        },
        "state_restore": "frozen geometry with candidate-material geostatic stress reconstruction",
        "candidate_initialization": {
            "method": "analytic geostatic F from frozen positions, then cylinder-free settling",
            "prepared_state": str(candidate_prepare_dir / "mpm_state.npz"),
            "h0_rmse_m": candidate_h0_rmse,
            "h0_max_abs_m": candidate_h0_max_abs,
            "h0_valid_cells": int(np.count_nonzero(candidate_valid)),
            "speed_threshold_mps": args.candidate_pre_settle_speed_threshold,
            "no_action_stability": candidate_initial_stability,
        },
        "removal": {
            "mode": action.get("removal", "lift"),
            "speed_mps": args.removal_speed,
            "max_steps": args.max_removal_steps,
            "capped": bool(args.max_removal_steps),
        },
        "prepared_settling": prepared["settling"],
        "post_removal_observations": {
            "requested_times_s": args.post_observation_times or [],
            "residual_weight": args.residual_weight,
            "summary": str(output_dir / "post_removal_observations.json") if post_observation_summary else None,
        },
    }
    with (output_dir / "manifest.json").open("w", encoding="utf-8") as file:
        json.dump(bridge_manifest, file, indent=2)
    print(output_dir)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Prepare, validate, and persist one gravity-settled Genesis bed for a Chrono H0.

The output is deliberately an acceptance-gated artifact.  It contains the
surface PLY *and* the complete MPM state, so a subsequent cylinder episode does
not silently reset the constitutive state that made the bed stable.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

from chrono_episode_bridge import load_episode, project_surface_to_chrono_grid, write_metric_bed
from particle_io import read_particle_ply


REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chrono-episode", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--resume-prepared-bed",
        type=Path,
        default=None,
        help="Continue settling this prior prepared_bed using its complete saved MPM state.",
    )
    parser.add_argument("--config", type=Path, default=REPO_ROOT / "configs" / "physgaussian_sand_stiff_mid.json")
    parser.add_argument("--backend", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--bed-depth-m", type=float, default=0.10)
    parser.add_argument("--particle-spacing-m", type=float, default=None)
    parser.add_argument("--pre-settle-max-time", type=float, default=2.0)
    parser.add_argument("--pre-settle-required-duration", type=float, default=0.02)
    parser.add_argument("--pre-settle-particle-speed-threshold", type=float, default=5.0e-4)
    parser.add_argument("--containment-wall-height", type=float, default=0.20)
    parser.add_argument("--containment-wall-thickness", type=float, default=0.02)
    parser.add_argument("--geostatic-stress-scale", type=float, default=1.0)
    parser.add_argument("--surface-rmse-tolerance-m", type=float, default=0.005)
    parser.add_argument("--surface-max-abs-tolerance-m", type=float, default=0.010)
    parser.add_argument("--n-grid", type=int, default=64)
    parser.add_argument("--particle-size", type=float, default=None)
    parser.add_argument("--enable-cpic", action="store_true", help="Enable and record Genesis CPIC rigid--MPM coupling.")
    parser.add_argument("--dt", type=float, default=0.0005, help="Genesis simulation timestep, persisted in the prepared-bed manifest.")
    return parser.parse_args()


def metrics_by_name(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as file:
        return {row["metric"]: row["value"] for row in csv.DictReader(file)}


def main() -> None:
    args = parse_args()
    episode_dir = args.chrono_episode.resolve()
    output_dir = args.output_dir.resolve()
    if output_dir.exists():
        raise SystemExit(f"Refusing to overwrite existing output directory: {output_dir}")
    manifest, _action, chrono_h0, chrono_valid = load_episode(episode_dir)
    spacing = float(args.particle_spacing_m or manifest["heightmap"]["spacing_m"])
    particle_size = float(args.particle_size if args.particle_size is not None else spacing)
    output_dir.mkdir(parents=True)
    source_dir = output_dir / "metric_bed_source"
    resume_state_path = None
    if args.resume_prepared_bed is None:
        metadata = write_metric_bed(source_dir, chrono_h0, manifest, args.bed_depth_m, spacing)
        state_source = "analytic geostatic F followed by gravity settling"
    else:
        resume_dir = args.resume_prepared_bed.resolve()
        resume_manifest_path = resume_dir.parent / "prepared_bed_manifest.json"
        if not resume_manifest_path.is_file():
            raise SystemExit(f"Prepared-bed manifest not found beside {resume_dir}")
        with resume_manifest_path.open("r", encoding="utf-8") as file:
            resume_manifest = json.load(file)
        if Path(resume_manifest["source_chrono_episode"]).resolve() != episode_dir:
            raise SystemExit("Resume prepared bed was built from a different Chrono episode")
        resume_state_path = resume_dir / "mpm_state.npz"
        for name in ("particles_initial_mpm.ply", "ground_plane_metadata.json"):
            if not (resume_dir / name).is_file():
                raise SystemExit(f"Resume prepared bed is missing {name}")
        if not resume_state_path.is_file():
            raise SystemExit("Resume prepared bed is missing mpm_state.npz")
        source_dir.mkdir()
        shutil.copy2(resume_dir / "particles_initial_mpm.ply", source_dir / "particles_initial_mpm.ply")
        shutil.copy2(resume_dir / "ground_plane_metadata.json", source_dir / "ground_plane_metadata.json")
        metadata = resume_manifest["metric_bed"]
        state_source = f"complete-state continuation of {resume_dir}"
    settle_dir = output_dir / "settle_raw"
    runner = REPO_ROOT / "scripts" / "run_mass_controlled_terrain.py"
    command = [
        sys.executable, str(runner),
        "--initial-particles-ply", str(source_dir / "particles_initial_mpm.ply"),
        "--initial-metadata-json", str(source_dir / "ground_plane_metadata.json"),
        "--config", str(args.config.resolve()),
        "--output-dir", str(settle_dir),
        "--pre-settle-only",
        "--pre-settle-max-time", str(args.pre_settle_max_time),
        "--pre-settle-required-duration", str(args.pre_settle_required_duration),
        "--pre-settle-particle-speed-threshold", str(args.pre_settle_particle_speed_threshold),
        "--containment-wall-height", str(args.containment_wall_height),
        "--containment-wall-thickness", str(args.containment_wall_thickness),
        "--backend", args.backend,
        "--n-grid", str(args.n_grid),
        "--particle-size", str(particle_size),
        "--dt", str(args.dt),
    ]
    if resume_state_path is None:
        command.extend(("--initialize-geostatic-stress", "--geostatic-stress-scale", str(args.geostatic_stress_scale)))
    else:
        command.extend(("--initial-mpm-state-npz", str(resume_state_path)))
    if args.enable_cpic:
        command.append("--enable-cpic")
    subprocess.run(command, check=True, cwd=REPO_ROOT)

    settled_points = read_particle_ply(settle_dir / "particles_initial_mpm.ply")
    settled_h0, settled_supported = project_surface_to_chrono_grid(settled_points, manifest, 1.51 * spacing)
    valid = chrono_valid & settled_supported
    if not np.any(valid):
        raise RuntimeError("Prepared bed did not support any Chrono-valid heightmap cells")
    surface_error = settled_h0[valid] - chrono_h0[valid]
    surface_rmse = float(np.sqrt(np.mean(surface_error**2)))
    surface_max = float(np.max(np.abs(surface_error)))
    metrics = metrics_by_name(settle_dir / "run_metrics.csv")
    equilibrium = metrics.get("pre_settle_termination_reason") == "equilibrium"
    accepted = bool(
        equilibrium
        and surface_rmse <= args.surface_rmse_tolerance_m
        and surface_max <= args.surface_max_abs_tolerance_m
    )
    np.save(output_dir / "settled_heightmap_m.npy", settled_h0)
    np.save(output_dir / "valid_heightmap_mask.npy", valid)
    prepared_dir = output_dir / "prepared_bed"
    prepared_dir.mkdir()
    for name in ("particles_initial_mpm.ply", "mpm_state.npz"):
        shutil.copy2(settle_dir / name, prepared_dir / name)
    shutil.copy2(source_dir / "ground_plane_metadata.json", prepared_dir / "ground_plane_metadata.json")
    prepared_manifest = {
        "schema_version": 1,
        "accepted": accepted,
        "source_chrono_episode": str(episode_dir),
        "coordinate_frame": manifest["coordinate_frame"],
        "heightmap": manifest["heightmap"],
        "metric_bed": metadata,
        "state": {
            "path": "prepared_bed/mpm_state.npz",
            "format": "complete Genesis MPM state: pos, vel, C, F, Jp, active",
            "source": state_source,
        },
        "settling": {
            "termination_reason": metrics.get("pre_settle_termination_reason"),
            "duration_s": float(metrics["pre_settle_duration"]),
            "final_particle_speed_p99_mps": float(metrics["pre_settle_final_particle_speed_p99"]),
            "threshold_mps": args.pre_settle_particle_speed_threshold,
            "containment_wall_height_m": args.containment_wall_height,
            "containment_wall_thickness_m": args.containment_wall_thickness,
            "geostatic_stress_scale": args.geostatic_stress_scale,
            "dt_s": args.dt,
            "n_grid": args.n_grid,
            "particle_size_m": particle_size,
            "enable_cpic": args.enable_cpic,
        },
        "surface_match": {
            "projection": "highest_particle_per_Chrono_cell_then_nearest_fill",
            "valid_cells": int(np.count_nonzero(valid)),
            "rmse_m": surface_rmse,
            "max_abs_m": surface_max,
            "rmse_tolerance_m": args.surface_rmse_tolerance_m,
            "max_abs_tolerance_m": args.surface_max_abs_tolerance_m,
        },
    }
    with (output_dir / "prepared_bed_manifest.json").open("w", encoding="utf-8") as file:
        json.dump(prepared_manifest, file, indent=2)
    if not accepted:
        raise SystemExit(
            "Prepared bed rejected: require equilibrium and surface error within the recorded tolerances; "
            f"equilibrium={equilibrium}, rmse={surface_rmse:.6g}, max={surface_max:.6g}"
        )
    print(prepared_dir)


if __name__ == "__main__":
    main()

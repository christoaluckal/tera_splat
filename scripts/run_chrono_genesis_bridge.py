#!/usr/bin/env python3
"""Run one Genesis gravity-cylinder episode from a canonical Chrono export."""

from __future__ import annotations

import argparse
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
    parser.add_argument("--required-duration", type=float, default=0.02)
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
    raw_dir = output_dir / "genesis_raw"
    runner = REPO_ROOT / "scripts" / "run_mass_controlled_terrain.py"
    command = [
        sys.executable,
        str(runner),
        "--initial-particles-ply", str(particle_path),
        "--initial-metadata-json", str(metadata_path),
        "--initial-mpm-state-npz", str(state_path),
        "--config", str(args.config.resolve()),
        "--output-dir", str(raw_dir),
        "--query-xy", str(action["center_xy_m"][0]), str(action["center_xy_m"][1]),
        "--indenter-radius", str(action["radius_m"]),
        "--indenter-height", str(action["height_m"]),
        "--indenter-mass", str(action["mass_kg"]),
        "--start-clearance", str(action["start_clearance_m"]),
        "--loaded-max-time", str(args.loaded_max_time),
        "--post-max-time", str(args.post_max_time),
        "--required-duration", str(args.required_duration),
        "--removal-mode", str(action.get("removal", "lift")),
        "--containment-wall-height", str(containment_height),
        "--containment-wall-thickness", str(containment_thickness),
        "--removal-speed", str(args.removal_speed),
        "--max-removal-steps", str(args.max_removal_steps),
        "--backend", args.backend,
        "--n-grid", str(prepared["settling"].get("n_grid", args.n_grid)),
        "--particle-size", str(prepared["settling"].get("particle_size_m", args.particle_size or 0.0125)),
        "--dt", str(prepared["settling"].get("dt_s", 0.0005)),
    ]
    if prepared["settling"].get("enable_cpic", False):
        command.append("--enable-cpic")
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
        "state_restore": "fresh Genesis process rebuilt from the accepted metric bed and restored full MPM state",
        "removal": {
            "mode": action.get("removal", "lift"),
            "speed_mps": args.removal_speed,
            "max_steps": args.max_removal_steps,
            "capped": bool(args.max_removal_steps),
        },
        "prepared_settling": prepared["settling"],
    }
    with (output_dir / "manifest.json").open("w", encoding="utf-8") as file:
        json.dump(bridge_manifest, file, indent=2)
    print(output_dir)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run a 3x3x3 Genesis matrix from the accepted splat-slice initializer."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from create_splat_subsurface_ply import build_regular_grid_subsurface, write_colored_ply
from particle_io import write_particle_ply
from view_iteration_7000 import AXIS_TRANSFORMS, DEFAULT_PLY, load_3dgs_ply


DEFAULT_CONFIG = REPO_ROOT / "configs" / "physgaussian_sand_soft.json"


def parse_float_list(value: str) -> list[float]:
    return [float(part) for part in value.split(",") if part.strip()]


def parse_int_list(value: str) -> list[int]:
    return [int(part) for part in value.split(",") if part.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ply", type=Path, default=DEFAULT_PLY)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-root", type=Path, default=REPO_ROOT / "outputs" / "splat_matrix_3x3x3")
    parser.add_argument("--z-min", type=float, default=-2.4)
    parser.add_argument("--z-max", type=float, default=-2.1)
    parser.add_argument("--box-size", type=float, default=1.0)
    parser.add_argument("--xy-spacing", type=float, default=0.025)
    parser.add_argument(
        "--xy-spacing-from-particle-size",
        action="store_true",
        help="Use each case's --particle-size as the regular subsurface XY grid spacing.",
    )
    parser.add_argument("--xy-jitter", type=float, default=0.8)
    parser.add_argument("--noise-scalar", type=float, default=1.5)
    parser.add_argument("--max-surface-distance", type=float, default=0.05)
    parser.add_argument("--surface-neighbors", type=int, default=32)
    parser.add_argument("--surface-quantile", type=float, default=0.9)
    parser.add_argument("--min-surface-clearance", type=float, default=0.0)
    parser.add_argument("--layer-counts", default="8,16,24")
    parser.add_argument("--layer-depths", default="0.1,0.2,0.3")
    parser.add_argument("--particle-sizes", default="0.015,0.025,0.035")
    parser.add_argument("--ground-offset", type=float, default=0.01)
    parser.add_argument("--opacity-threshold", type=float, default=0.02)
    parser.add_argument("--max-gaussians", type=int, default=300_000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--axis-transform", choices=tuple(AXIS_TRANSFORMS.keys()), default="opencv-to-zup")
    parser.add_argument("--align-ground-z", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--steps", type=int, default=240)
    parser.add_argument("--dt", type=float, default=5e-4)
    parser.add_argument("--substeps", type=int, default=1)
    parser.add_argument("--save-every", type=int, default=12)
    parser.add_argument("--metrics-interval", type=int, default=60)
    parser.add_argument("--backend", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--gravity-scale", type=float, default=1.0)
    parser.add_argument(
        "--velocity-damping",
        type=float,
        default=None,
        help="Per-step MPM velocity multiplier passed to Genesis. Values below 1 dissipate bounce.",
    )
    parser.add_argument("--n-grid", type=int, default=64)
    parser.add_argument("--ground-coup-friction", type=float, default=0.2)
    parser.add_argument("--ground-coup-softness", type=float, default=0.0)
    parser.add_argument("--ground-coup-restitution", type=float, default=0.0)
    parser.add_argument("--video-duration", type=float, default=2.0)
    parser.add_argument("--video-fps", type=float, default=60.0)
    parser.add_argument("--video-point-radius", type=int, default=1)
    parser.add_argument("--video-view", choices=("oblique", "top"), default="oblique")
    parser.add_argument("--video-sample-fraction", type=float, default=1.0)
    parser.add_argument("--video-max-points", type=int, default=0)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Generate initial states and metadata only.")
    return parser.parse_args()


def case_name(layer_count: int, layer_depth: float, particle_size: float) -> str:
    depth_label = f"{layer_depth:.4f}".rstrip("0").rstrip(".").replace(".", "p")
    particle_label = f"{particle_size:.4f}".rstrip("0").rstrip(".").replace(".", "p")
    return f"layers{layer_count:02d}_depth{depth_label}_ps{particle_label}"


def case_xy_spacing(args: argparse.Namespace, particle_size: float) -> float:
    if args.xy_spacing_from_particle_size:
        return float(particle_size)
    return float(args.xy_spacing)


def load_surface(args: argparse.Namespace) -> tuple[np.ndarray, np.ndarray, dict]:
    data = load_3dgs_ply(
        args.ply,
        opacity_threshold=args.opacity_threshold,
        max_gaussians=args.max_gaussians,
        seed=args.seed,
        scale_multiplier=1.0,
        axis_transform=args.axis_transform,
        align_ground_z=args.align_ground_z,
    )
    keep = (data.centers[:, 2] >= args.z_min) & (data.centers[:, 2] <= args.z_max)
    box_center_xy = None
    if args.box_size > 0.0:
        zband = data.centers[keep]
        if zband.shape[0] == 0:
            raise ValueError("No splats remain after Z filtering")
        box_center_xy = zband[:, :2].mean(axis=0)
        half_box = args.box_size * 0.5
        keep &= np.all(np.abs(data.centers[:, :2] - box_center_xy) <= half_box, axis=1)

    surface = data.centers[keep]
    colors = data.colors[keep]
    if surface.shape[0] == 0:
        raise ValueError("No splats remain after Z/box filtering")
    source_metadata = {
        "source_ply": str(args.ply),
        "input_splat_count": int(data.centers.shape[0]),
        "z_min": args.z_min,
        "z_max": args.z_max,
        "box_size": args.box_size,
        "box_center_xy": box_center_xy.tolist() if box_center_xy is not None else None,
        "axis_transform": args.axis_transform,
        "align_ground_z": args.align_ground_z,
        "opacity_threshold": args.opacity_threshold,
        "max_gaussians": args.max_gaussians,
    }
    return surface, colors, source_metadata


def write_case_initial_state(
    args: argparse.Namespace,
    case_dir: Path,
    surface: np.ndarray,
    surface_colors: np.ndarray,
    source_metadata: dict,
    *,
    layer_count: int,
    layer_depth: float,
    particle_size: float,
) -> dict:
    layer_spacing = layer_depth / layer_count
    xy_spacing = case_xy_spacing(args, particle_size)
    subsurface, subsurface_colors, subsurface_metadata = build_regular_grid_subsurface(
        surface,
        surface_colors,
        depth=layer_depth,
        xy_spacing=xy_spacing,
        layer_spacing=layer_spacing,
        xy_jitter_fraction=args.xy_jitter,
        noise_scalar=args.noise_scalar,
        max_surface_distance=args.max_surface_distance,
        surface_neighbors=args.surface_neighbors,
        surface_quantile=args.surface_quantile,
        min_surface_clearance=args.min_surface_clearance,
        seed=args.seed + layer_count + int(layer_depth * 1000) + int(particle_size * 10000),
    )
    particles = np.concatenate([surface, subsurface], axis=0).astype(np.float32)
    colors = np.concatenate([surface_colors, subsurface_colors], axis=0)
    ground_z = float(subsurface[:, 2].min() - args.ground_offset)

    case_dir.mkdir(parents=True, exist_ok=True)
    write_particle_ply(particles, case_dir / "particles_initial_mpm.ply")
    write_particle_ply(surface, case_dir / "particles_surface_mpm.ply")
    write_particle_ply(subsurface, case_dir / "particles_subsurface_mpm.ply")
    write_colored_ply(surface, surface_colors, case_dir / "splat_surface_zband_colored.ply")
    write_colored_ply(subsurface, subsurface_colors, case_dir / "regular_grid_subsurface_colored.ply")
    write_colored_ply(particles, colors, case_dir / "splat_surface_plus_subsurface_colored.ply")

    metadata = {
        **source_metadata,
        "particle_count": int(particles.shape[0]),
        "surface_particle_count": int(surface.shape[0]),
        "entity_counts": {
            "surface": int(surface.shape[0]),
            "subsurface": int(subsurface.shape[0]),
            "ground_plane": 1,
        },
        "matrix_case": {
            "layer_count": int(layer_count),
            "layer_depth": float(layer_depth),
            "particle_size": float(particle_size),
            "layer_spacing": float(layer_spacing),
            "xy_spacing": float(xy_spacing),
            "xy_spacing_from_particle_size": bool(args.xy_spacing_from_particle_size),
            "velocity_damping": args.velocity_damping,
            "substeps": args.substeps,
            "ground_coup_friction": args.ground_coup_friction,
            "ground_coup_softness": args.ground_coup_softness,
            "ground_coup_restitution": args.ground_coup_restitution,
            "min_surface_clearance": args.min_surface_clearance,
        },
        "subsurface_fill": {
            **subsurface_metadata,
            "subsurface_particle_count": int(subsurface.shape[0]),
            "surface_entity_source": "manual_splat_zband",
        },
        "surface_bounds_min": surface.min(axis=0).tolist(),
        "surface_bounds_max": surface.max(axis=0).tolist(),
        "subsurface_bounds_min": subsurface.min(axis=0).tolist(),
        "subsurface_bounds_max": subsurface.max(axis=0).tolist(),
        "ground_plane_mpm": {
            "point": [0.0, 0.0, ground_z],
            "normal": [0.0, 0.0, 1.0],
            "surface": "sticky",
            "friction": 0.0,
            "height_source": "subsurface_min_minus_offset",
            "offset_below_subsurface": args.ground_offset,
        },
    }
    with (case_dir / "ground_plane_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    return metadata


def read_metric_csv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return {row["metric"]: row["value"] for row in csv.DictReader(f)}


def run_command(command: list[str], cwd: Path) -> None:
    print(" ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def main() -> None:
    args = parse_args()
    layer_counts = parse_int_list(args.layer_counts)
    layer_depths = parse_float_list(args.layer_depths)
    particle_sizes = parse_float_list(args.particle_sizes)
    if not layer_counts or not layer_depths or not particle_sizes:
        raise ValueError("Expected at least one value for layer counts, layer depths, and particle sizes")

    args.output_root.mkdir(parents=True, exist_ok=True)
    surface, surface_colors, source_metadata = load_surface(args)
    rows = []
    matrix_start = time.perf_counter()

    for layer_count in layer_counts:
        for layer_depth in layer_depths:
            for particle_size in particle_sizes:
                name = case_name(layer_count, layer_depth, particle_size)
                case_dir = args.output_root / name
                video_path = case_dir / "solver_animation.mp4"
                if args.skip_existing and video_path.exists():
                    print(f"skip existing: {case_dir}", flush=True)
                    continue

                case_start = time.perf_counter()
                metadata = write_case_initial_state(
                    args,
                    case_dir,
                    surface,
                    surface_colors,
                    source_metadata,
                    layer_count=layer_count,
                    layer_depth=layer_depth,
                    particle_size=particle_size,
                )
                if not args.dry_run:
                    solver_command = [
                        sys.executable,
                        "scripts/run_genesis_ground_plane_solver.py",
                        "--config",
                        str(args.config),
                        "--initial-particles-ply",
                        str(case_dir / "particles_initial_mpm.ply"),
                        "--initial-metadata-json",
                        str(case_dir / "ground_plane_metadata.json"),
                        "--output-dir",
                        str(case_dir),
                        "--backend",
                        args.backend,
                        "--steps",
                        str(args.steps),
                        "--dt",
                        str(args.dt),
                        "--substeps",
                        str(args.substeps),
                        "--save-every",
                        str(args.save_every),
                        "--metrics-interval",
                        str(args.metrics_interval),
                        "--gravity-scale",
                        str(args.gravity_scale),
                        "--n-grid",
                        str(args.n_grid),
                        "--particle-size",
                        str(particle_size),
                        "--ground-coup-friction",
                        str(args.ground_coup_friction),
                        "--ground-coup-softness",
                        str(args.ground_coup_softness),
                        "--ground-coup-restitution",
                        str(args.ground_coup_restitution),
                    ]
                    if args.velocity_damping is not None:
                        solver_command.extend(["--velocity-damping", str(args.velocity_damping)])
                    run_command(solver_command, REPO_ROOT)
                    run_command(
                        [
                            sys.executable,
                            "scripts/render_solver_video.py",
                            str(case_dir),
                            "--output",
                            str(video_path),
                            "--duration",
                            str(args.video_duration),
                            "--fps",
                            str(args.video_fps),
                            "--point-radius",
                            str(args.video_point_radius),
                            "--view",
                            args.video_view,
                            "--sample-fraction",
                            str(args.video_sample_fraction),
                            "--max-points",
                            str(args.video_max_points),
                        ],
                        REPO_ROOT,
                    )

                metrics = read_metric_csv(case_dir / "run_metrics.csv")
                rows.append(
                    {
                        "case": name,
                        "layer_count": layer_count,
                        "layer_depth": layer_depth,
                        "layer_spacing": layer_depth / layer_count,
                        "particle_size": particle_size,
                        "xy_spacing": case_xy_spacing(args, particle_size),
                        "substeps": args.substeps,
                        "ground_coup_friction": args.ground_coup_friction,
                        "ground_coup_softness": args.ground_coup_softness,
                        "ground_coup_restitution": args.ground_coup_restitution,
                        "surface_particles": metadata["surface_particle_count"],
                        "subsurface_particles": metadata["subsurface_fill"]["subsurface_particle_count"],
                        "total_particles": metadata["particle_count"],
                        "ground_z": metadata["ground_plane_mpm"]["point"][2],
                        "video": str(video_path) if video_path.exists() else "",
                        "status": metrics.get("status", "dry_run" if args.dry_run else "unknown"),
                        "total_wall_seconds": metrics.get("total_wall_seconds", ""),
                        "simulation_loop_seconds": metrics.get("simulation_loop_seconds", ""),
                        "steps_per_second": metrics.get("steps_per_second", ""),
                        "case_wall_seconds": time.perf_counter() - case_start,
                    }
                )

                with (args.output_root / "summary.csv").open("w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                    writer.writeheader()
                    writer.writerows(rows)

    with (args.output_root / "matrix_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(
            {
                "cases": len(rows),
                "layer_counts": layer_counts,
                "layer_depths": layer_depths,
                "particle_sizes": particle_sizes,
                "total_wall_seconds": time.perf_counter() - matrix_start,
                "output_root": str(args.output_root),
            },
            f,
            indent=2,
        )
    print(f"summary: {args.output_root / 'summary.csv'}")


if __name__ == "__main__":
    main()

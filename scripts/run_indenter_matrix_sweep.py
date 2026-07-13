#!/usr/bin/env python3
"""Run a large coupled-rigid indenter sweep and collect sinkage metrics."""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from particle_io import load_material_config, read_particle_ply


DEFAULT_BASE = REPO_ROOT / "assets" / "base_settled_stiff_mid"
DEFAULT_CONFIG = REPO_ROOT / "configs" / "physgaussian_sand_sinkage_mid.json"


def parse_float_list(value: str) -> list[float]:
    return [float(part) for part in value.split(",") if part.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--initial-particles-ply", type=Path, default=DEFAULT_BASE / "particles_initial_mpm.ply")
    parser.add_argument("--initial-metadata-json", type=Path, default=DEFAULT_BASE / "ground_plane_metadata.json")
    parser.add_argument("--base-config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-root", type=Path, default=REPO_ROOT / "outputs" / "indenter_matrix_sweep_4level")
    parser.add_argument("--query-xy", type=float, nargs=2, default=(0.2955, 0.17895))
    parser.add_argument("--masses", default="2.5,5,10,20", help="Comma-separated kg values.")
    parser.add_argument("--radii", default="0.03,0.04,0.06,0.08", help="Comma-separated meter values.")
    parser.add_argument("--sand-e-values", default="25000,50000,100000,200000", help="Comma-separated Pa values.")
    parser.add_argument("--friction-angles", default="25,35,45,55", help="Comma-separated degree values.")
    parser.add_argument("--softnesses", default="0,0.0025,0.005,0.01", help="Comma-separated rigid-MPM coup_softness values.")
    parser.add_argument("--steps", type=int, default=16000)
    parser.add_argument("--dt", type=float, default=0.00025)
    parser.add_argument("--substeps", type=int, default=10)
    parser.add_argument("--save-every", type=int, default=160)
    parser.add_argument("--particle-size", type=float, default=0.0125)
    parser.add_argument("--n-grid", type=int, default=64)
    parser.add_argument("--start-clearance", type=float, default=0.0)
    parser.add_argument("--indenter-height", type=float, default=0.04)
    parser.add_argument("--indenter-friction", type=float, default=0.8)
    parser.add_argument("--indenter-restitution", type=float, default=0.0)
    parser.add_argument("--backend", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--video-duration", type=float, default=8.0)
    parser.add_argument("--video-fps", type=float, default=60.0)
    parser.add_argument("--video-width", type=int, default=1280)
    parser.add_argument("--video-height", type=int, default=720)
    parser.add_argument("--video-view", choices=("oblique", "top"), default="oblique")
    parser.add_argument("--video-point-radius", type=int, default=1)
    parser.add_argument("--video-sample-fraction", type=float, default=1.0)
    parser.add_argument("--video-max-points", type=int, default=0)
    parser.add_argument("--skip-render", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-cases", type=int, default=0, help="Stop after this many selected cases. 0 means all cases.")
    parser.add_argument("--case-stride", type=int, default=1, help="Run every Nth Cartesian-product case.")
    parser.add_argument("--case-offset", type=int, default=0, help="Start selection at this Cartesian-product case index.")
    return parser.parse_args()


def metric_csv_to_dict(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as f:
        return {row["metric"]: row["value"] for row in csv.DictReader(f)}


def read_pose_final(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[-1] if rows else {}


def case_name(case: dict[str, float]) -> str:
    def f(value: float) -> str:
        return f"{value:.5g}".replace(".", "p").replace("-", "m")

    return (
        f"m{f(case['mass'])}_r{f(case['radius'])}_"
        f"E{f(case['sand_E'])}_phi{f(case['friction_angle'])}_soft{f(case['softness'])}"
    )


def write_case_config(base_config: dict, path: Path, *, sand_e: float, friction_angle: float) -> None:
    config = dict(base_config)
    config["E"] = float(sand_e)
    config["friction_angle"] = float(friction_angle)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def run_command(command: list[str], cwd: Path) -> None:
    print(" ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def compute_displacement_metrics(case_dir: Path) -> dict[str, float | int]:
    metadata_path = case_dir / "ground_plane_metadata.json"
    initial_path = case_dir / "particles_initial_mpm.ply"
    final_path = case_dir / "particles_final_mpm.ply"
    if not metadata_path.exists() or not initial_path.exists() or not final_path.exists():
        return {}

    with metadata_path.open("r", encoding="utf-8") as f:
        metadata = json.load(f)
    initial = read_particle_ply(initial_path)
    final = read_particle_ply(final_path)
    surface_count = int(metadata.get("surface_particle_count", initial.shape[0]))
    query_xy = np.asarray(metadata.get("query_xy", [0.0, 0.0]), dtype=np.float32)
    radius = float((metadata.get("indenter") or {}).get("radius", 0.08))

    surface_initial = initial[:surface_count]
    surface_final = final[:surface_count]
    dz = surface_final[:, 2] - surface_initial[:, 2]
    dxy = surface_final[:, :2] - surface_initial[:, :2]
    dnorm = np.linalg.norm(surface_final - surface_initial, axis=1)
    distance = np.linalg.norm(surface_initial[:, :2] - query_xy[None, :], axis=1)
    under = distance <= radius
    near = distance <= radius * 2.0
    if not np.any(under):
        under = distance <= np.partition(distance, min(128, distance.size - 1))[min(128, distance.size - 1)]

    return {
        "surface_particles": int(surface_count),
        "under_disk_particles": int(np.count_nonzero(under)),
        "near_disk_particles": int(np.count_nonzero(near)),
        "under_mean_dz_m": float(np.mean(dz[under])),
        "under_min_dz_m": float(np.min(dz[under])),
        "under_p05_dz_m": float(np.quantile(dz[under], 0.05)),
        "under_max_dz_m": float(np.max(dz[under])),
        "under_mean_xy_disp_m": float(np.mean(np.linalg.norm(dxy[under], axis=1))),
        "near_mean_dz_m": float(np.mean(dz[near])) if np.any(near) else 0.0,
        "surface_mean_norm_disp_m": float(np.mean(dnorm)),
        "surface_max_norm_disp_m": float(np.max(dnorm)),
    }


def write_overlay_stats(path: Path, row: dict[str, object]) -> None:
    lines = [
        f"case: {row['case']}",
        f"m={float(row['mass_kg']):.3g} kg  r={float(row['radius_m']):.3g} m",
        f"E={float(row['sand_E_Pa']):.3g} Pa  phi={float(row['friction_angle_deg']):.3g} deg",
        f"soft={float(row['softness']):.4g}  particles={row.get('particles', '')}",
        f"drop={float(row.get('final_actual_depth_m') or 0.0) * 100.0:.2f} cm",
        f"mean dz={float(row.get('under_mean_dz_m') or 0.0) * 100.0:.2f} cm",
        f"min dz={float(row.get('under_min_dz_m') or 0.0) * 100.0:.2f} cm",
        f"sim={float(row.get('simulation_loop_seconds') or 0.0):.1f}s wall={float(row.get('total_wall_seconds') or 0.0):.1f}s",
    ]
    with path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n")


def selected_cases(args: argparse.Namespace) -> list[tuple[int, dict[str, float]]]:
    masses = parse_float_list(args.masses)
    radii = parse_float_list(args.radii)
    sand_e_values = parse_float_list(args.sand_e_values)
    friction_angles = parse_float_list(args.friction_angles)
    softnesses = parse_float_list(args.softnesses)
    for name, values in {
        "masses": masses,
        "radii": radii,
        "sand-e-values": sand_e_values,
        "friction-angles": friction_angles,
        "softnesses": softnesses,
    }.items():
        if len(values) != 4:
            raise ValueError(f"--{name} must contain exactly 4 values; got {len(values)}")

    cases = []
    for index, values in enumerate(itertools.product(masses, radii, sand_e_values, friction_angles, softnesses)):
        if index < args.case_offset:
            continue
        if (index - args.case_offset) % max(args.case_stride, 1) != 0:
            continue
        mass, radius, sand_e, friction_angle, softness = values
        cases.append(
            (
                index,
                {
                    "mass": mass,
                    "radius": radius,
                    "sand_E": sand_e,
                    "friction_angle": friction_angle,
                    "softness": softness,
                },
            )
        )
        if args.max_cases > 0 and len(cases) >= args.max_cases:
            break
    return cases


def write_summary(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    keys = list(rows[0].keys())
    for row in rows[1:]:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    base_config = load_material_config(args.base_config)
    cases = selected_cases(args)
    rows: list[dict[str, object]] = []
    matrix_start = time.perf_counter()

    for product_index, case in cases:
        name = case_name(case)
        case_dir = args.output_root / f"{product_index:04d}_{name}"
        config_path = case_dir / "material_config.json"
        video_path = case_dir / "indenter_animation_stats.mp4"
        row: dict[str, object] = {
            "product_index": product_index,
            "case": name,
            "case_dir": str(case_dir),
            "mass_kg": case["mass"],
            "radius_m": case["radius"],
            "sand_E_Pa": case["sand_E"],
            "friction_angle_deg": case["friction_angle"],
            "softness": case["softness"],
            "status": "dry_run" if args.dry_run else "pending",
        }
        rows.append(row)

        if args.skip_existing and (case_dir / "run_metrics.csv").exists():
            metrics = metric_csv_to_dict(case_dir / "run_metrics.csv")
            displacement = compute_displacement_metrics(case_dir)
            pose = read_pose_final(case_dir / "indenter_pose.csv")
            row.update(metrics)
            row.update(displacement)
            row["final_actual_depth_m"] = pose.get("actual_depth", row.get("final_actual_depth", ""))
            row["video"] = str(video_path) if video_path.exists() else ""
            row["status"] = metrics.get("status", "existing")
            write_summary(args.output_root / "summary.csv", rows)
            continue

        case_start = time.perf_counter()
        case_dir.mkdir(parents=True, exist_ok=True)
        write_case_config(
            base_config,
            config_path,
            sand_e=case["sand_E"],
            friction_angle=case["friction_angle"],
        )

        if not args.dry_run:
            run_command(
                [
                    sys.executable,
                    "scripts/run_genesis_indenter_test.py",
                    "--config",
                    str(config_path),
                    "--initial-particles-ply",
                    str(args.initial_particles_ply),
                    "--initial-metadata-json",
                    str(args.initial_metadata_json),
                    "--output-dir",
                    str(case_dir),
                    "--backend",
                    args.backend,
                    "--indenter-body-mode",
                    "rigid",
                    "--debug-contact-mode",
                    "none",
                    "--indenter-control-mode",
                    "gravity",
                    "--indenter-mass",
                    str(case["mass"]),
                    "--indenter-radius",
                    str(case["radius"]),
                    "--indenter-height",
                    str(args.indenter_height),
                    "--query-xy",
                    str(args.query_xy[0]),
                    str(args.query_xy[1]),
                    "--start-clearance",
                    str(args.start_clearance),
                    "--indenter-softness",
                    str(case["softness"]),
                    "--indenter-friction",
                    str(args.indenter_friction),
                    "--indenter-restitution",
                    str(args.indenter_restitution),
                    "--steps",
                    str(args.steps),
                    "--dt",
                    str(args.dt),
                    "--substeps",
                    str(args.substeps),
                    "--save-every",
                    str(args.save_every),
                    "--particle-size",
                    str(args.particle_size),
                    "--n-grid",
                    str(args.n_grid),
                ],
                REPO_ROOT,
            )

            metrics = metric_csv_to_dict(case_dir / "run_metrics.csv")
            displacement = compute_displacement_metrics(case_dir)
            pose = read_pose_final(case_dir / "indenter_pose.csv")
            row.update(metrics)
            row.update(displacement)
            row["final_actual_depth_m"] = pose.get("actual_depth", row.get("final_actual_depth", ""))
            row["case_wall_seconds"] = time.perf_counter() - case_start
            row["status"] = metrics.get("status", "completed")
            stats_path = case_dir / "video_overlay_stats.txt"
            write_overlay_stats(stats_path, row)

            if not args.skip_render:
                run_command(
                    [
                        sys.executable,
                        "scripts/render_indenter_animation.py",
                        str(case_dir),
                        "--output",
                        str(video_path),
                        "--duration",
                        str(args.video_duration),
                        "--fps",
                        str(args.video_fps),
                        "--width",
                        str(args.video_width),
                        "--height",
                        str(args.video_height),
                        "--point-radius",
                        str(args.video_point_radius),
                        "--view",
                        args.video_view,
                        "--sample-fraction",
                        str(args.video_sample_fraction),
                        "--max-points",
                        str(args.video_max_points),
                        "--stats-text",
                        str(stats_path),
                    ],
                    REPO_ROOT,
                )
                row["video"] = str(video_path)
        else:
            row["case_wall_seconds"] = time.perf_counter() - case_start

        write_summary(args.output_root / "summary.csv", rows)

    metadata = {
        "output_root": str(args.output_root),
        "selected_cases": len(cases),
        "full_cartesian_cases": 4**5,
        "knobs": {
            "masses": parse_float_list(args.masses),
            "radii": parse_float_list(args.radii),
            "sand_E_values": parse_float_list(args.sand_e_values),
            "friction_angles": parse_float_list(args.friction_angles),
            "softnesses": parse_float_list(args.softnesses),
        },
        "steps": args.steps,
        "dt": args.dt,
        "substeps": args.substeps,
        "save_every": args.save_every,
        "total_wall_seconds": time.perf_counter() - matrix_start,
    }
    with (args.output_root / "matrix_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"summary: {args.output_root / 'summary.csv'}")
    print(f"metadata: {args.output_root / 'matrix_metadata.json'}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Compute indenter sinkage/displacement metrics for an existing run folder."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from particle_io import read_particle_ply
from run_genesis_indenter_test import surface_displacement_metric_rows
from view_solver_animation import find_frame_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def read_pose_rows(path: Path) -> list[dict[str, float | int]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = []
        for row in csv.DictReader(f):
            parsed: dict[str, float | int] = {}
            for key, value in row.items():
                parsed[key] = int(value) if key == "step" else float(value)
            rows.append(parsed)
    return rows


def frame_for_step(frame_paths: list[Path], step: int) -> Path:
    target = f"sim_{step:04d}.ply"
    for path in frame_paths:
        if path.name == target:
            return path
    available_steps = np.asarray([int(path.stem.split("_")[-1]) for path in frame_paths])
    nearest = int(np.argmin(np.abs(available_steps - step)))
    return frame_paths[nearest]


def write_metric_rows(path: Path, rows: list[tuple[str, object, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value", "unit"])
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    output = args.output or args.run_dir / "sinkage_metrics.csv"
    metadata_path = args.run_dir / "ground_plane_metadata.json"
    pose_path = args.run_dir / "indenter_pose.csv"
    final_path = args.run_dir / "particles_final_mpm.ply"
    if not metadata_path.exists():
        raise SystemExit(f"Missing metadata: {metadata_path}")
    if not pose_path.exists():
        raise SystemExit(f"Missing pose CSV: {pose_path}")
    if not final_path.exists():
        raise SystemExit(f"Missing final particles: {final_path}")

    with metadata_path.open("r", encoding="utf-8") as f:
        metadata = json.load(f)
    pose_rows = read_pose_rows(pose_path)
    frame_paths = find_frame_paths(args.run_dir)
    baseline_path = frame_for_step(frame_paths, 0)
    peak_pose = max(pose_rows, key=lambda row: max(float(row.get("actual_depth", 0.0)), 0.0))
    peak_path = frame_for_step(frame_paths, int(peak_pose["step"]))

    baseline = read_particle_ply(baseline_path)
    peak = read_particle_ply(peak_path)
    final = read_particle_ply(final_path)
    surface_count = int(metadata.get("surface_particle_count", baseline.shape[0]))
    query_xy = np.asarray(metadata.get("query_xy", [0.0, 0.0]), dtype=np.float32)
    radius = float((metadata.get("indenter") or {}).get("radius", 0.08))

    rows: list[tuple[str, object, str]] = [
        ("run_dir", args.run_dir, ""),
        ("baseline_frame", baseline_path.name, ""),
        ("peak_frame", peak_path.name, ""),
        ("peak_step", peak_pose["step"], "count"),
        ("peak_time", peak_pose.get("time", 0.0), "seconds"),
        ("peak_actual_depth", max(float(peak_pose.get("actual_depth", 0.0)), 0.0), "meters"),
        ("radius", radius, "meters"),
    ]
    rows.extend(
        surface_displacement_metric_rows(
            prefix="peak",
            baseline_points=baseline,
            current_points=peak,
            query_xy=query_xy,
            radius=radius,
            surface_count=surface_count,
        )
    )
    rows.extend(
        surface_displacement_metric_rows(
            prefix="final",
            baseline_points=baseline,
            current_points=final,
            query_xy=query_xy,
            radius=radius,
            surface_count=surface_count,
        )
    )
    write_metric_rows(output, rows)
    print(f"output: {output}")


if __name__ == "__main__":
    main()

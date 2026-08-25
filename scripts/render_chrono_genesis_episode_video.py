#!/usr/bin/env python3
"""Render captured Chrono and Genesis cylinder episodes side by side.

The component timelines are phase-normalized: each full stored episode is sampled
uniformly into the requested output duration. This is suitable for visual
comparison, not a claim that the two solvers share physical timestamps.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
CHRONO_RENDERER = REPO_ROOT.parent / "tera_splat_sim" / "render_cylinder_drop_dem.py"
GENESIS_RENDERER = REPO_ROOT / "scripts" / "render_indenter_animation.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chrono-episode", type=Path, required=True)
    parser.add_argument("--genesis-raw", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--duration", type=float, default=8.0)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--cell-width", type=int, default=960)
    parser.add_argument("--cell-height", type=int, default=540)
    return parser.parse_args()


def labeled(frame: np.ndarray, text: str) -> np.ndarray:
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 34), (245, 245, 245), thickness=-1)
    cv2.putText(frame, text, (12, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (25, 25, 25), 2, cv2.LINE_AA)
    return frame


def compose(chrono_video: Path, genesis_video: Path, output: Path, fps: int, width: int, height: int) -> int:
    chrono = cv2.VideoCapture(str(chrono_video))
    genesis = cv2.VideoCapture(str(genesis_video))
    if not chrono.isOpened() or not genesis.isOpened():
        raise RuntimeError("Could not read one or both component videos")
    frame_count = min(int(chrono.get(cv2.CAP_PROP_FRAME_COUNT)), int(genesis.get(cv2.CAP_PROP_FRAME_COUNT)))
    if frame_count <= 0:
        raise RuntimeError("Component videos contain no frames")
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*"mp4v"), fps, (2 * width, height))
    if not writer.isOpened():
        raise RuntimeError(f"Could not open output video: {output}")
    for index in range(frame_count):
        ok_chrono, chrono_frame = chrono.read()
        ok_genesis, genesis_frame = genesis.read()
        if not ok_chrono or not ok_genesis:
            raise RuntimeError("Component video ended before its reported frame count")
        chrono_frame = labeled(cv2.resize(chrono_frame, (width, height), interpolation=cv2.INTER_AREA), "Chrono SCM")
        genesis_frame = labeled(cv2.resize(genesis_frame, (width, height), interpolation=cv2.INTER_AREA), "Genesis MPM")
        writer.write(np.concatenate((chrono_frame, genesis_frame), axis=1))
    writer.release()
    chrono.release()
    genesis.release()
    return frame_count


def main() -> None:
    args = parse_args()
    if args.duration <= 0.0 or args.fps <= 0 or args.cell_width <= 0 or args.cell_height <= 0:
        raise ValueError("duration, fps, and cell dimensions must be positive")
    chrono_episode = args.chrono_episode.resolve()
    genesis_raw = args.genesis_raw.resolve()
    snapshots_manifest = chrono_episode / "terrain_snapshots" / "manifest.json"
    if not snapshots_manifest.is_file():
        raise SystemExit(
            "Chrono episode has no terrain snapshots. Recreate the identical Chrono episode "
            "with run_cylinder_episode.py --capture-interval-s before rendering an episode video."
        )
    with snapshots_manifest.open(encoding="utf-8") as file:
        snapshot_records = json.load(file).get("records", [])
    if not snapshot_records:
        raise SystemExit("Chrono terrain snapshot manifest contains no records")
    if not (genesis_raw / "simulation_ply").is_dir():
        raise SystemExit("Genesis raw rollout is missing simulation_ply frames")
    output = args.output.resolve()
    chrono_component = output.with_name(output.stem + "_chrono_component.mp4")
    genesis_component = output.with_name(output.stem + "_genesis_component.mp4")
    target_frames = max(1, int(round(args.duration * args.fps)))
    frames_per_snapshot = max(1, int(math.ceil(target_frames / len(snapshot_records))))
    subprocess.run(
        [
            sys.executable, str(CHRONO_RENDERER),
            "--chrono-episode", str(chrono_episode),
            "--output", str(chrono_component),
            "--fps", str(args.fps),
            "--frames-per-snapshot", str(frames_per_snapshot),
        ],
        check=True,
        cwd=REPO_ROOT.parent / "tera_splat_sim",
    )
    subprocess.run(
        [
            sys.executable, str(GENESIS_RENDERER), str(genesis_raw),
            "--output", str(genesis_component),
            "--duration", str(args.duration),
            "--fps", str(args.fps),
            "--width", str(args.cell_width),
            "--height", str(args.cell_height),
            "--particle-view", "surface",
        ],
        check=True,
        cwd=REPO_ROOT,
    )
    frame_count = compose(chrono_component, genesis_component, output, args.fps, args.cell_width, args.cell_height)
    video_manifest = {
        "schema_version": 1,
        "description": "Chrono and Genesis episodes sampled uniformly over each stored phase; not physical-time synchronized.",
        "chrono_episode": str(chrono_episode),
        "genesis_raw": str(genesis_raw),
        "output": str(output),
        "fps": args.fps,
        "frames": frame_count,
        "chrono_component": str(chrono_component),
        "genesis_component": str(genesis_component),
    }
    output.with_suffix(".json").write_text(json.dumps(video_manifest, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()

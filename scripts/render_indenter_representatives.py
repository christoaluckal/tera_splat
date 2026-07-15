#!/usr/bin/env python3
"""Render selected indenter representative cases with solid-cylinder overlays."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--case-ids", type=int, nargs="+", required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--duration", type=float, default=8.0)
    parser.add_argument("--fps", type=float, default=60.0)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with args.summary.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    selected_ids = set(args.case_ids)
    selected = [row for row in rows if int(float(row["product_index"])) in selected_ids]
    selected.sort(key=lambda row: args.case_ids.index(int(float(row["product_index"]))))
    if len(selected) != len(selected_ids):
        found = {int(float(row["product_index"])) for row in selected}
        missing = sorted(selected_ids - found)
        raise SystemExit(f"Missing cases in {args.summary}: {missing}")

    for index, row in enumerate(selected, start=1):
        case_dir = Path(row["video"]).parent
        solid_video = case_dir / "indenter_animation_solid_stats.mp4"
        print(f"[{index}/{len(selected)}] rendering {case_dir.name}", flush=True)
        subprocess.run(
            [
                sys.executable,
                "scripts/render_indenter_animation.py",
                str(case_dir),
                "--output",
                str(solid_video),
                "--duration",
                str(args.duration),
                "--fps",
                str(args.fps),
                "--width",
                str(args.width),
                "--height",
                str(args.height),
                "--point-radius",
                "1",
                "--view",
                "oblique",
                "--stats-text",
                str(case_dir / "video_overlay_stats.txt"),
                "--indenter-style",
                "solid",
            ],
            check=True,
        )
        row["solid_video"] = str(solid_video)

    fields = list(rows[0].keys())
    if "solid_video" not in fields:
        fields.append("solid_video")
    args.output_summary.parent.mkdir(parents=True, exist_ok=True)
    with args.output_summary.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(selected)
    print(f"summary: {args.output_summary}")


if __name__ == "__main__":
    main()

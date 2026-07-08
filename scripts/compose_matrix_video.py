#!/usr/bin/env python3
"""Compose case videos from a matrix run into a labeled grid MP4."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix_root", type=Path)
    parser.add_argument("--summary", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--rows", type=int, default=3)
    parser.add_argument("--cols", type=int, default=3)
    parser.add_argument("--fps", type=float, default=60.0)
    parser.add_argument("--cell-width", type=int, default=640)
    parser.add_argument("--cell-height", type=int, default=360)
    return parser.parse_args()


def read_summary(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def open_video(path: Path) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise SystemExit(f"Could not open video: {path}")
    return cap


def label_for(row: dict[str, str]) -> str:
    particle_size = float(row["particle_size"])
    layer_count = int(float(row["layer_count"]))
    layer_spacing = float(row["layer_spacing"])
    total_particles = int(float(row["total_particles"]))
    return (
        f"ps={particle_size:.4f}  layers={layer_count}  "
        f"dz={layer_spacing:.4f}  n={total_particles:,}"
    )


def draw_label(frame: np.ndarray, text: str) -> None:
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 34), (245, 245, 245), thickness=-1)
    cv2.putText(frame, text, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (25, 25, 25), 2, cv2.LINE_AA)


def main() -> None:
    args = parse_args()
    summary = args.summary or args.matrix_root / "summary.csv"
    output = args.output or args.matrix_root / "comparison_3x3.mp4"
    rows = read_summary(summary)
    rows = [row for row in rows if row.get("video")]
    rows.sort(key=lambda r: (float(r["particle_size"]), int(float(r["layer_count"]))))
    expected = args.rows * args.cols
    if len(rows) < expected:
        raise SystemExit(f"Expected at least {expected} videos, found {len(rows)} in {summary}")
    rows = rows[:expected]

    captures = [open_video(Path(row["video"])) for row in rows]
    labels = [label_for(row) for row in rows]
    frame_counts = [int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) for cap in captures]
    frame_total = min(frame_counts)
    if frame_total <= 0:
        raise SystemExit("No readable video frames found")

    output.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(output),
        cv2.VideoWriter_fourcc(*"mp4v"),
        args.fps,
        (args.cols * args.cell_width, args.rows * args.cell_height),
    )
    if not writer.isOpened():
        raise SystemExit(f"Could not open video writer for {output}")

    blank = np.full((args.cell_height, args.cell_width, 3), 245, dtype=np.uint8)
    for frame_index in range(frame_total):
        cells = []
        for cap, label in zip(captures, labels):
            ok, frame = cap.read()
            if not ok:
                frame = blank.copy()
            else:
                frame = cv2.resize(frame, (args.cell_width, args.cell_height), interpolation=cv2.INTER_AREA)
            draw_label(frame, label)
            cells.append(frame)

        grid_rows = []
        for row_index in range(args.rows):
            start = row_index * args.cols
            grid_rows.append(np.concatenate(cells[start : start + args.cols], axis=1))
        writer.write(np.concatenate(grid_rows, axis=0))
        if (frame_index + 1) % max(int(args.fps), 1) == 0:
            print(f"composed {frame_index + 1}/{frame_total} frames")

    writer.release()
    for cap in captures:
        cap.release()
    print(f"output: {output}")


if __name__ == "__main__":
    main()

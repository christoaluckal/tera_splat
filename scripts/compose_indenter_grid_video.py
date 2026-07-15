#!/usr/bin/env python3
"""Compose selected indenter case videos into a labeled comparison grid."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--case-ids", type=int, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rows", type=int, default=2)
    parser.add_argument("--cols", type=int, default=2)
    parser.add_argument("--fps", type=float, default=60.0)
    parser.add_argument("--cell-width", type=int, default=640)
    parser.add_argument("--cell-height", type=int, default=360)
    parser.add_argument("--video-column", default="solid_video")
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def label_for(row: dict[str, str]) -> str:
    if row.get("sink_cm"):
        sink_cm = float(row["sink_cm"])
    else:
        sink_cm = -100.0 * float(row["under_mean_dz_m"])
    return (
        f"{int(float(row['product_index']))}: m={float(row['mass_kg']):.3g}kg "
        f"r={float(row['radius_m']):.2f} E={float(row['sand_E_Pa']):.2g} "
        f"phi={float(row['friction_angle_deg']):.0f} soft={float(row['softness']):.4g} "
        f"sink={sink_cm:.2f}cm"
    )


def draw_label(frame: np.ndarray, text: str) -> None:
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 36), (245, 245, 245), thickness=-1)
    cv2.putText(frame, text, (8, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (25, 25, 25), 1, cv2.LINE_AA)


def main() -> None:
    args = parse_args()
    rows_by_id = {int(float(row["product_index"])): row for row in read_rows(args.summary)}
    selected = []
    for case_id in args.case_ids:
        if case_id not in rows_by_id:
            raise SystemExit(f"Case id {case_id} not found in {args.summary}")
        selected.append(rows_by_id[case_id])
    expected = args.rows * args.cols
    if len(selected) != expected:
        raise SystemExit(f"Expected exactly {expected} case ids for a {args.rows}x{args.cols} grid")

    captures = []
    for row in selected:
        video = row.get(args.video_column) or row.get("video")
        if not video:
            raise SystemExit(f"No video path for case {row['product_index']}")
        cap = cv2.VideoCapture(str(Path(video)))
        if not cap.isOpened():
            raise SystemExit(f"Could not open video: {video}")
        captures.append(cap)

    frame_total = min(int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) for cap in captures)
    if frame_total <= 0:
        raise SystemExit("No readable video frames found")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(args.output),
        cv2.VideoWriter_fourcc(*"mp4v"),
        args.fps,
        (args.cols * args.cell_width, args.rows * args.cell_height),
    )
    if not writer.isOpened():
        raise SystemExit(f"Could not open video writer for {args.output}")

    blank = np.full((args.cell_height, args.cell_width, 3), 245, dtype=np.uint8)
    labels = [label_for(row) for row in selected]
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
    print(f"output: {args.output}")


if __name__ == "__main__":
    main()

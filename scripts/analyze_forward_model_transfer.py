#!/usr/bin/env python3
"""Summarize Chrono-GT versus Newton terrain-deformation characteristics.

Each ``--case`` is ``label=chrono_episode:newton_output_root``.  The Newton
root may contain one or more study directories; the newest valid
``result.json`` is selected.  The script deliberately reports characteristics
of the deformation field in addition to the scalar objective used by the
BayesOpt driver, so it can be used as a forward-model transfer audit.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
import yaml


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case", action="append", required=True,
                   help="label=chrono_episode:newton_output_root; repeat per case")
    p.add_argument("--output-dir", type=Path, required=True)
    return p.parse_args()


def parse_case(spec: str) -> tuple[str, Path, Path]:
    try:
        label, paths = spec.split("=", 1)
        chrono, newton = paths.split(":", 1)
    except ValueError as exc:
        raise ValueError(f"invalid --case {spec!r}; expected label=chrono:newton") from exc
    if not label or not chrono or not newton:
        raise ValueError(f"invalid --case {spec!r}")
    return label, Path(chrono), Path(newton)


def newest_valid_result(root: Path) -> tuple[dict[str, Any], Path]:
    candidates = []
    for path in root.glob("study_*/trials/iteration_*/result.json"):
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("valid") and data.get("paths", {}).get("response"):
            candidates.append((path.stat().st_mtime_ns, data, path))
    if not candidates:
        raise FileNotFoundError(f"no valid Newton result.json under {root}")
    _, data, path = max(candidates, key=lambda item: item[0])
    response = Path(data["paths"]["response"])
    if not response.is_dir():
        # Results use the host's /data path; resolve the equivalent workspace path.
        response = path.parent / "response"
    return data, response


def map_stats(episode: Path, state: str) -> dict[str, float]:
    manifest = yaml.safe_load((episode / "manifest.yaml").read_text())
    initial = np.load(episode / manifest["states"]["initial"]).astype(float)
    surface = np.load(episode / manifest["states"][state]).astype(float)
    valid = np.load(episode / manifest["heightmap"]["valid_mask"]).astype(bool)
    action = json.loads((episode / manifest["action"]).read_text())
    spacing = float(manifest["heightmap"]["spacing_m"])
    rows, cols = initial.shape
    ox, oy = manifest["heightmap"]["origin_xy_m"]
    xx, yy = np.meshgrid(ox + np.arange(cols) * spacing,
                         oy + np.arange(rows) * spacing)
    cx, cy = action["center_xy_m"]
    footprint = (xx - cx) ** 2 + (yy - cy) ** 2 <= float(action["radius_m"]) ** 2
    delta = surface - initial
    depression = np.maximum(-delta, 0.0)
    support = valid & np.isfinite(delta)
    fp = support & footprint
    weights = depression * fp
    total = float(np.sum(weights) * spacing * spacing)
    denom = float(np.sum(weights))
    return {
        "max_depression_mm": float(np.max(depression[support]) * 1000.0),
        "mean_depression_mm": float(np.mean(depression[support]) * 1000.0),
        "footprint_max_depression_mm": float(np.max(depression[fp]) * 1000.0),
        "footprint_mean_depression_mm": float(np.mean(depression[fp]) * 1000.0),
        "depression_volume_cm3": total * 1.0e6,
        "depression_centroid_x_mm": float(np.sum(xx * weights) / denom * 1000.0) if denom else float("nan"),
        "depression_centroid_y_mm": float(np.sum(yy * weights) / denom * 1000.0) if denom else float("nan"),
    }


def compare(episode: Path, response: Path, result: dict[str, Any]) -> dict[str, Any]:
    manifest = yaml.safe_load((episode / "manifest.yaml").read_text())
    chrono = {}
    for state in ("loaded", "residual"):
        chrono[state] = map_stats(episode, state)
    initial = np.load(episode / manifest["states"]["initial"]).astype(float)
    valid = np.load(episode / manifest["heightmap"]["valid_mask"]).astype(bool)
    action = json.loads((episode / manifest["action"]).read_text())
    newton_initial = np.load(response / "initial_heightmap_m.npy").astype(float)
    pred = {}
    for state in ("loaded", "residual"):
        newton = np.load(response / f"{state}_heightmap_m.npy").astype(float)
        delta = newton - newton_initial
        support = valid & np.isfinite(delta)
        pred[state] = {
            **map_stats(response, state) if False else {},
            "max_depression_mm": float(np.max(np.maximum(-delta[support], 0.0)) * 1000.0),
            "mean_depression_mm": float(np.mean(np.maximum(-delta[support], 0.0)) * 1000.0),
        }
        # Reuse the Chrono coordinate/action geometry for footprint statistics.
        spacing = float(manifest["heightmap"]["spacing_m"])
        rows, cols = initial.shape
        ox, oy = manifest["heightmap"]["origin_xy_m"]
        xx, yy = np.meshgrid(ox + np.arange(cols) * spacing,
                             oy + np.arange(rows) * spacing)
        cx, cy = action["center_xy_m"]
        fp = support & ((xx - cx) ** 2 + (yy - cy) ** 2 <= float(action["radius_m"]) ** 2)
        dep = np.maximum(-delta, 0.0)
        weights = dep * fp
        denom = float(np.sum(weights))
        pred[state].update({
            "footprint_max_depression_mm": float(np.max(dep[fp]) * 1000.0),
            "footprint_mean_depression_mm": float(np.mean(dep[fp]) * 1000.0),
            "depression_volume_cm3": float(np.sum(weights) * spacing * spacing * 1.0e6),
            "depression_centroid_x_mm": float(np.sum(xx * weights) / denom * 1000.0) if denom else float("nan"),
            "depression_centroid_y_mm": float(np.sum(yy * weights) / denom * 1000.0) if denom else float("nan"),
        })
    return {
        "chrono_episode": str(episode),
        "newton_response": str(response),
        "candidate": result["candidate"],
        "objective_mm": float(result["objective_m"] * 1000.0),
        "loaded_rmse_mm": float(result["loaded_rmse_m"] * 1000.0),
        "residual_footprint_rmse_mm": float(result["residual_footprint_rmse_m"] * 1000.0),
        "chrono": chrono,
        "newton": pred,
        "characteristic_error": {
            state: {key: pred[state][key] - chrono[state][key]
                    for key in chrono[state]}
            for state in ("loaded", "residual")
        },
    }


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for spec in args.case:
        label, episode, root = parse_case(spec)
        result, response = newest_valid_result(root)
        record = compare(episode, response, result)
        record["label"] = label
        records.append(record)
    (args.output_dir / "summary.json").write_text(json.dumps(records, indent=2, allow_nan=True) + "\n")
    rows = []
    for r in records:
        for state in ("loaded", "residual"):
            rows.append({
                "label": r["label"], "state": state,
                "objective_mm": r["objective_mm"],
                "loaded_rmse_mm": r["loaded_rmse_mm"],
                "residual_footprint_rmse_mm": r["residual_footprint_rmse_mm"],
                "chrono_max_depression_mm": r["chrono"][state]["max_depression_mm"],
                "newton_max_depression_mm": r["newton"][state]["max_depression_mm"],
                "max_depression_error_mm": r["characteristic_error"][state]["max_depression_mm"],
                "chrono_volume_cm3": r["chrono"][state]["depression_volume_cm3"],
                "newton_volume_cm3": r["newton"][state]["depression_volume_cm3"],
                "volume_error_cm3": r["characteristic_error"][state]["depression_volume_cm3"],
                "centroid_x_error_mm": r["characteristic_error"][state]["depression_centroid_x_mm"],
                "centroid_y_error_mm": r["characteristic_error"][state]["depression_centroid_y_mm"],
            })
    with (args.output_dir / "characteristics.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(records)} cases to {args.output_dir}")


if __name__ == "__main__":
    main()

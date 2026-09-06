#!/usr/bin/env python3
"""Analyze Newton preparation consistency across timestep and solver tolerance."""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class Case:
    label: str
    root: Path
    manifest: dict[str, Any]
    heightmap: np.ndarray
    mask: np.ndarray

    @property
    def dt_s(self) -> float:
        return float(self.manifest["solver"]["dt_s"])

    @property
    def tolerance(self) -> float:
        return float(self.manifest["solver"]["tolerance"])


def parse_case(value: str) -> tuple[str, Path]:
    label, separator, path = value.partition("=")
    if not separator or not label or not path:
        raise argparse.ArgumentTypeError("case must have the form LABEL=OUTPUT_DIRECTORY")
    return label, Path(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", type=parse_case, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--reference-tolerance", type=float, default=1.0e-4)
    parser.add_argument("--tolerance-check-dt-s", type=float, default=0.00025)
    parser.add_argument("--rmse-gate-m", type=float, default=0.0005)
    parser.add_argument("--max-abs-gate-m", type=float, default=0.001)
    return parser.parse_args()


def load_case(label: str, root: Path) -> Case:
    root = root.resolve()
    manifest = json.loads(
        (root / "newton_prepared_bed_manifest.json").read_text(encoding="utf-8")
    )
    if manifest.get("backend") != "newton":
        raise ValueError(f"{label}: expected a Newton manifest")
    heightmap = np.load(root / "settled_heightmap_m.npy")
    mask = np.load(root / "valid_heightmap_mask.npy").astype(bool)
    if heightmap.shape != mask.shape:
        raise ValueError(f"{label}: heightmap and mask shapes differ")
    return Case(label=label, root=root, manifest=manifest, heightmap=heightmap, mask=mask)


def compare_cases(left: Case, right: Case) -> dict[str, Any]:
    common = (
        left.mask
        & right.mask
        & np.isfinite(left.heightmap)
        & np.isfinite(right.heightmap)
    )
    if not np.any(common):
        raise ValueError(f"{left.label}/{right.label}: no common supported cells")
    delta = right.heightmap[common] - left.heightmap[common]
    return {
        "left": left.label,
        "right": right.label,
        "left_dt_s": left.dt_s,
        "right_dt_s": right.dt_s,
        "left_tolerance": left.tolerance,
        "right_tolerance": right.tolerance,
        "common_cells": int(np.count_nonzero(common)),
        "signed_mean_m": float(np.mean(delta)),
        "rmse_m": float(np.sqrt(np.mean(delta * delta))),
        "max_abs_m": float(np.max(np.abs(delta))),
    }


def observed_order(coarse_to_medium_rmse: float, medium_to_fine_rmse: float) -> float | None:
    if coarse_to_medium_rmse <= 0.0 or medium_to_fine_rmse <= 0.0:
        return None
    return float(math.log2(coarse_to_medium_rmse / medium_to_fine_rmse))


def close(value: float, expected: float) -> bool:
    return math.isclose(value, expected, rel_tol=1.0e-9, abs_tol=1.0e-12)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    if args.rmse_gate_m <= 0.0 or args.max_abs_gate_m <= 0.0:
        raise ValueError("consistency gates must be positive")
    cases = [load_case(label, root) for label, root in args.case]
    identities = {(case.dt_s, case.tolerance) for case in cases}
    if len(identities) != len(cases):
        raise ValueError("matrix contains duplicate timestep/tolerance cells")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    case_rows = []
    for case in sorted(cases, key=lambda item: (item.tolerance, -item.dt_s)):
        settling = case.manifest["settling"]
        match = case.manifest["surface_match"]["settled"]
        case_rows.append(
            {
                "label": case.label,
                "path": str(case.root),
                "dt_s": case.dt_s,
                "tolerance": case.tolerance,
                "accepted": bool(case.manifest["accepted"]),
                "first_equilibrium_s": settling["first_equilibrium_s"],
                "final_speed_p99_mps": settling["final_speed"]["p99_mps"],
                "h0_rmse_m": match["rmse_m"],
                "h0_max_abs_m": match["max_abs_m"],
                "valid_fraction": match["valid_fraction"],
            }
        )

    pairwise_rows = []
    reference_cases = sorted(
        (case for case in cases if close(case.tolerance, args.reference_tolerance)),
        key=lambda item: item.dt_s,
        reverse=True,
    )
    for left, right in zip(reference_cases, reference_cases[1:]):
        row = compare_cases(left, right)
        row["axis"] = "timestep"
        row["passes_gate"] = (
            row["rmse_m"] <= args.rmse_gate_m
            and row["max_abs_m"] <= args.max_abs_gate_m
        )
        pairwise_rows.append(row)

    tolerance_cases = sorted(
        (case for case in cases if close(case.dt_s, args.tolerance_check_dt_s)),
        key=lambda item: item.tolerance,
        reverse=True,
    )
    for left, right in zip(tolerance_cases, tolerance_cases[1:]):
        row = compare_cases(left, right)
        row["axis"] = "tolerance"
        row["passes_gate"] = (
            row["rmse_m"] <= args.rmse_gate_m
            and row["max_abs_m"] <= args.max_abs_gate_m
        )
        pairwise_rows.append(row)

    timestep_rows = [row for row in pairwise_rows if row["axis"] == "timestep"]
    order = None
    if len(timestep_rows) >= 2:
        order = observed_order(timestep_rows[0]["rmse_m"], timestep_rows[1]["rmse_m"])
    required_timestep_pairs = max(0, len(reference_cases) - 1)
    required_tolerance_pairs = max(0, len(tolerance_cases) - 1)
    matrix_complete = (
        len(reference_cases) >= 3
        and len(tolerance_cases) >= 2
        and len(timestep_rows) == required_timestep_pairs
        and len([row for row in pairwise_rows if row["axis"] == "tolerance"])
        == required_tolerance_pairs
    )
    all_cases_accepted = all(bool(case.manifest["accepted"]) for case in cases)
    consistency_passed = bool(
        matrix_complete
        and all_cases_accepted
        and pairwise_rows
        and all(bool(row["passes_gate"]) for row in pairwise_rows)
    )
    summary = {
        "schema_version": 1,
        "backend": "newton",
        "status": "passed" if consistency_passed else "not_demonstrated",
        "matrix_complete": matrix_complete,
        "all_cases_accepted": all_cases_accepted,
        "consistency_passed": consistency_passed,
        "reference_tolerance": args.reference_tolerance,
        "tolerance_check_dt_s": args.tolerance_check_dt_s,
        "rmse_gate_m": args.rmse_gate_m,
        "max_abs_gate_m": args.max_abs_gate_m,
        "observed_timestep_order": order,
        "cases": case_rows,
        "pairwise": pairwise_rows,
        "interpretation": (
            "Preparation is numerically consistent under the predeclared map gates."
            if consistency_passed
            else "Preparation convergence is not demonstrated under the predeclared map gates."
        ),
    }
    write_csv(output / "cases.csv", case_rows)
    write_csv(output / "pairwise.csv", pairwise_rows)
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

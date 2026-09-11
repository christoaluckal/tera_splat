#!/usr/bin/env python3
"""Analyze full Newton response consistency across timestep."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


REQUIRED_TIMESTEPS_S = (0.0005, 0.00025, 0.000125)
FORWARD_MODEL_FILES = (
    "configs/newton_sand_smoke.json",
    "scripts/newton_contract.py",
    "scripts/newton_collider_activation.py",
    "scripts/run_newton_prepared_bed.py",
    "scripts/run_newton_cylinder_diagnostic.py",
)


@dataclass(frozen=True)
class Case:
    label: str
    root: Path
    manifest: dict[str, Any]
    config: dict[str, Any]
    initial: np.ndarray
    loaded: np.ndarray
    residual: np.ndarray
    mask: np.ndarray

    @property
    def dt_s(self) -> float:
        return float(self.manifest["solver"]["dt_s"])

    @property
    def loaded_response(self) -> np.ndarray:
        return self.loaded - self.initial

    @property
    def residual_response(self) -> np.ndarray:
        return self.residual - self.initial


def parse_case(value: str) -> tuple[str, Path]:
    label, separator, path = value.partition("=")
    if not separator or not label or not path:
        raise argparse.ArgumentTypeError("case must have the form LABEL=OUTPUT_DIRECTORY")
    return label, Path(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", type=parse_case, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--rmse-gate-m", type=float, default=0.0005)
    parser.add_argument("--max-abs-gate-m", type=float, default=0.001)
    parser.add_argument("--sinkage-gate-m", type=float, default=0.0005)
    return parser.parse_args()


def close(value: float, expected: float) -> bool:
    return math.isclose(value, expected, rel_tol=1.0e-9, abs_tol=1.0e-12)


def load_case(label: str, root: Path) -> Case:
    root = root.resolve()
    manifest = json.loads(
        (root / "newton_cylinder_manifest.json").read_text(encoding="utf-8")
    )
    config = json.loads((root / "resolved_config.json").read_text(encoding="utf-8"))
    if manifest.get("backend") != "newton" or config.get("backend") != "newton":
        raise ValueError(f"{label}: expected Newton manifest and configuration")
    arrays = [
        np.load(root / "initial_heightmap_m.npy"),
        np.load(root / "loaded_heightmap_m.npy"),
        np.load(root / "residual_heightmap_m.npy"),
        np.load(root / "valid_heightmap_mask.npy").astype(bool),
    ]
    if len({array.shape for array in arrays}) != 1:
        raise ValueError(f"{label}: response maps and mask have different shapes")
    return Case(label, root, manifest, config, *arrays)


def case_qualifies(case: Case) -> bool:
    manifest = case.manifest
    return bool(
        manifest.get("accepted")
        and manifest.get("mechanics_qualified")
        and manifest.get("finite")
        and manifest.get("preparation", {}).get("convergence_passed")
        and manifest.get("cylinder", {}).get("guide_constraint_passed", False)
        and manifest.get("penetration", {}).get(
            "passed_zero_center_penetration_gate"
        )
        and int(manifest.get("surface", {}).get("valid_cells", -1))
        == int(np.count_nonzero(case.mask))
    )


def invariant_settings(case: Case) -> dict[str, Any]:
    manifest = case.manifest
    action = manifest["action"]
    cylinder = manifest["cylinder"]
    contact_activation = manifest.get("contact_activation", {})
    solver = dict(manifest["solver"])
    solver.pop("dt_s", None)
    return {
        "config": case.config,
        "chrono_episode": manifest["chrono_episode"],
        "environment": manifest["environment"],
        "solver_except_dt": solver,
        "action": {
            key: action[key]
            for key in (
                "episode_id",
                "mass_kg",
                "center_xy_m",
                "radius_m",
                "height_m",
                "start_clearance_m",
                "removal",
                "geometry",
                "gravity_mps2",
                "loaded_duration_s",
                "residual_duration_s",
                "removal_implementation",
            )
        },
        "cylinder": {
            key: cylinder[key]
            for key in (
                "friction_coefficient",
                "collider_mode",
                "collider_segments",
                "analytic_radius_m",
                "collision_mesh_vertex_radius_m",
                "collision_mesh_half_height_m",
                "collision_guard_m",
                "collision_bottom_inset_m",
                "collision_center_offset_z_m",
                "projection_threshold_m",
                "guided_body_position_update",
            )
        },
        "contact_activation": {
            key: contact_activation.get(key)
            for key in (
                "implementation",
                "requested_activation_distance_voxels",
                "newton_default_activation_distance_voxels",
                "containment_uses_newton_default",
                "signed_distance_geometry_unchanged",
                "project_outside_geometry_unchanged",
                "distance_unit",
                "voxel_size_m",
            )
        },
    }


def invariant_mismatches(cases: list[Case]) -> list[str]:
    if not cases:
        return ["no cases"]
    reference = invariant_settings(cases[0])
    mismatches = []
    for case in cases[1:]:
        candidate = invariant_settings(case)
        for key in reference:
            if candidate[key] != reference[key]:
                mismatches.append(f"{case.label}: {key} differs from {cases[0].label}")
    return mismatches


def response_metrics(delta: np.ndarray) -> dict[str, float]:
    return {
        "signed_mean_m": float(np.mean(delta)),
        "rmse_m": float(np.sqrt(np.mean(delta * delta))),
        "max_abs_m": float(np.max(np.abs(delta))),
    }


def compare_cases(
    left: Case,
    right: Case,
    rmse_gate_m: float,
    max_abs_gate_m: float,
    sinkage_gate_m: float,
) -> dict[str, Any]:
    common = (
        left.mask
        & right.mask
        & np.isfinite(left.initial)
        & np.isfinite(left.loaded)
        & np.isfinite(left.residual)
        & np.isfinite(right.initial)
        & np.isfinite(right.loaded)
        & np.isfinite(right.residual)
    )
    if not np.any(common):
        raise ValueError(f"{left.label}/{right.label}: no common valid response cells")
    loaded = response_metrics(
        right.loaded_response[common] - left.loaded_response[common]
    )
    residual = response_metrics(
        right.residual_response[common] - left.residual_response[common]
    )
    left_sinkage = float(left.manifest["cylinder"]["sinkage_below_initial_surface_m"])
    right_sinkage = float(right.manifest["cylinder"]["sinkage_below_initial_surface_m"])
    left_velocity = float(left.manifest["cylinder"]["loaded_vertical_speed_mps"])
    right_velocity = float(right.manifest["cylinder"]["loaded_vertical_speed_mps"])
    sinkage_difference = abs(right_sinkage - left_sinkage)
    passes = bool(
        loaded["rmse_m"] <= rmse_gate_m
        and loaded["max_abs_m"] <= max_abs_gate_m
        and residual["rmse_m"] <= rmse_gate_m
        and residual["max_abs_m"] <= max_abs_gate_m
        and sinkage_difference <= sinkage_gate_m
    )
    return {
        "left": left.label,
        "right": right.label,
        "left_dt_s": left.dt_s,
        "right_dt_s": right.dt_s,
        "common_cells": int(np.count_nonzero(common)),
        "loaded_signed_mean_m": loaded["signed_mean_m"],
        "loaded_rmse_m": loaded["rmse_m"],
        "loaded_max_abs_m": loaded["max_abs_m"],
        "residual_signed_mean_m": residual["signed_mean_m"],
        "residual_rmse_m": residual["rmse_m"],
        "residual_max_abs_m": residual["max_abs_m"],
        "left_sinkage_m": left_sinkage,
        "right_sinkage_m": right_sinkage,
        "sinkage_abs_difference_m": sinkage_difference,
        "left_loaded_vertical_speed_mps": left_velocity,
        "right_loaded_vertical_speed_mps": right_velocity,
        "loaded_vertical_speed_abs_difference_mps": abs(
            right_velocity - left_velocity
        ),
        "passes_gate": passes,
    }


def observed_order(coarse_to_medium: float, medium_to_fine: float) -> float | None:
    if coarse_to_medium <= 0.0 or medium_to_fine <= 0.0:
        return None
    return float(math.log2(coarse_to_medium / medium_to_fine))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_provenance(repo_root: Path) -> dict[str, Any]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--short", "--", *FORWARD_MODEL_FILES],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return {
        "git_commit": commit,
        "forward_model_files_match_commit": not bool(status),
        "forward_model_status": status.splitlines(),
        "file_sha256": {
            relative: file_sha256(repo_root / relative)
            for relative in FORWARD_MODEL_FILES
        },
    }


def main() -> None:
    args = parse_args()
    gates = (args.rmse_gate_m, args.max_abs_gate_m, args.sinkage_gate_m)
    if any(not math.isfinite(value) or value <= 0.0 for value in gates):
        raise ValueError("all response convergence gates must be finite and positive")
    cases = [load_case(label, root) for label, root in args.case]
    if len({case.label for case in cases}) != len(cases):
        raise ValueError("case labels must be unique")
    if len({case.dt_s for case in cases}) != len(cases):
        raise ValueError("matrix contains duplicate timesteps")
    cases.sort(key=lambda case: case.dt_s, reverse=True)
    matrix_complete = bool(
        len(cases) == len(REQUIRED_TIMESTEPS_S)
        and all(
            close(case.dt_s, required)
            for case, required in zip(cases, REQUIRED_TIMESTEPS_S)
        )
    )
    mismatches = invariant_mismatches(cases)
    all_cases_qualified = all(case_qualifies(case) for case in cases)
    pairwise = [
        compare_cases(
            left,
            right,
            args.rmse_gate_m,
            args.max_abs_gate_m,
            args.sinkage_gate_m,
        )
        for left, right in zip(cases, cases[1:])
    ]
    consistency_passed = bool(
        matrix_complete
        and not mismatches
        and all_cases_qualified
        and len(pairwise) == 2
        and all(row["passes_gate"] for row in pairwise)
    )
    case_rows = []
    for case in cases:
        manifest = case.manifest
        case_rows.append(
            {
                "label": case.label,
                "path": str(case.root),
                "dt_s": case.dt_s,
                "status": manifest["status"],
                "accepted": bool(manifest["accepted"]),
                "mechanics_qualified": bool(manifest["mechanics_qualified"]),
                "finite": bool(manifest["finite"]),
                "preparation_convergence_passed": bool(
                    manifest["preparation"]["convergence_passed"]
                ),
                "preparation_final_speed_p99_mps": manifest["preparation"][
                    "pre_settle"
                ]["final_speed"]["p99_mps"],
                "valid_cells": int(np.count_nonzero(case.mask)),
                "zero_center_penetration_passed": bool(
                    manifest["penetration"]["passed_zero_center_penetration_gate"]
                ),
                "max_inside_particle_centers": manifest["penetration"][
                    "max_inside_particle_centers"
                ],
                "max_center_penetration_m": manifest["penetration"][
                    "max_center_penetration_m"
                ],
                "guide_constraint_passed": bool(
                    manifest["cylinder"]["guide_constraint_passed"]
                ),
                "contact_activation_distance_voxels": manifest.get(
                    "contact_activation", {}
                ).get("requested_activation_distance_voxels"),
                "first_significant_contact_bottom_gap_m": manifest.get(
                    "contact_activation", {}
                ).get(
                    "first_impulse_analytic_bottom_relative_to_initial_surface_m"
                ),
                "loaded_sinkage_m": manifest["cylinder"][
                    "sinkage_below_initial_surface_m"
                ],
                "loaded_bottom_relative_to_initial_surface_m": manifest["cylinder"][
                    "bottom_relative_to_initial_surface_m"
                ],
                "loaded_vertical_speed_mps": manifest["cylinder"][
                    "loaded_vertical_speed_mps"
                ],
                "loaded_chrono_rmse_m": manifest["surface"][
                    "loaded_response_error"
                ]["rmse_m"],
                "residual_chrono_rmse_m": manifest["surface"][
                    "residual_response_error"
                ]["rmse_m"],
                "residual_particle_speed_p99_mps": manifest["surface"][
                    "residual_particle_speed"
                ]["p99_mps"],
                "max_contact_nodes": manifest["cylinder"]["max_contact_nodes"],
                "max_impulse_contact_nodes": manifest["cylinder"].get(
                    "max_impulse_contact_nodes"
                ),
                "max_upward_impulse_ns": manifest["cylinder"][
                    "max_upward_impulse_ns"
                ],
                "wall_time_s": manifest["wall_time_s"],
            }
        )
    orders = {"loaded": None, "residual": None}
    if len(pairwise) == 2:
        orders = {
            "loaded": observed_order(
                pairwise[0]["loaded_rmse_m"], pairwise[1]["loaded_rmse_m"]
            ),
            "residual": observed_order(
                pairwise[0]["residual_rmse_m"],
                pairwise[1]["residual_rmse_m"],
            ),
        }
    repo_root = Path(__file__).resolve().parents[1]
    summary = {
        "schema_version": 1,
        "backend": "newton",
        "status": "passed" if consistency_passed else "not_demonstrated",
        "matrix_complete": matrix_complete,
        "invariant_settings_passed": not mismatches,
        "invariant_mismatches": mismatches,
        "all_cases_mechanics_qualified": all_cases_qualified,
        "consistency_passed": consistency_passed,
        "required_timesteps_s": list(REQUIRED_TIMESTEPS_S),
        "gates": {
            "response_rmse_m": args.rmse_gate_m,
            "response_max_abs_m": args.max_abs_gate_m,
            "loaded_sinkage_abs_difference_m": args.sinkage_gate_m,
        },
        "comparison": {
            "loaded": "loaded_heightmap_m - initial_heightmap_m",
            "residual": "residual_heightmap_m - initial_heightmap_m",
            "scope": "pairwise common valid finite cells",
            "chrono_error_is_gate": False,
        },
        "observed_timestep_order": orders,
        "source_provenance": source_provenance(repo_root),
        "cases": case_rows,
        "pairwise": pairwise,
        "interpretation": (
            "The full Newton response path is consistent under the predeclared timestep gates."
            if consistency_passed
            else "Newton response convergence is not demonstrated under the predeclared timestep gates."
        ),
    }
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "cases.csv", case_rows)
    write_csv(output / "pairwise.csv", pairwise)
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

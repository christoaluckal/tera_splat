#!/usr/bin/env python3
"""Run small validation checks for the mass-controlled cylinder bridge."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
WRITABLE_CACHE = REPO_ROOT / "outputs" / ".cache"
os.environ.setdefault("XDG_CACHE_HOME", str(WRITABLE_CACHE))
os.environ.setdefault("GS_CACHE_FILE_PATH", str(WRITABLE_CACHE / "genesis"))
os.environ.setdefault("NUMBA_CACHE_DIR", str(WRITABLE_CACHE / "numba"))
os.environ.setdefault("MPLCONFIGDIR", str(WRITABLE_CACHE / "matplotlib"))


CYLINDER_DIAMETER_M = 0.14605
CYLINDER_RADIUS_M = 0.073025
CYLINDER_HEIGHT_M = 0.0508
CYLINDER_MASS_KG = 1.5
CYLINDER_EQUIV_DENSITY_KG_M3 = 1762.522
EXPECTED_INERTIA_DIAG_KG_M2 = [0.002322324, 0.002322324, 0.003999488]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--dt", type=float, default=0.001)
    parser.add_argument("--steps", type=int, default=160)
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "outputs" / "mass_controlled_bridge_checks" / "free_fall_report.json")
    return parser.parse_args()


def tensor3_to_list(value) -> list[float]:
    return [float(v) for v in value.detach().cpu().numpy().reshape(-1)[:3]]


def inertia_diag(entity) -> list[float] | None:
    if not getattr(entity, "links", None):
        return None
    inertia = getattr(entity.links[0], "inertial_i", None)
    if inertia is None:
        return None
    return [float(v) for v in np.diag(np.asarray(inertia, dtype=np.float64))]


def run_free_fall(args: argparse.Namespace) -> dict:
    import genesis as gs

    backend = gs.cuda if args.backend == "cuda" else gs.cpu
    gs.init(backend=backend, precision="32", seed=0, logging_level="warning")
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=args.dt,
            substeps=10,
            gravity=(0.0, 0.0, -9.81),
            floor_height=-10.0,
        ),
        show_viewer=False,
    )
    cylinder = scene.add_entity(
        gs.morphs.Cylinder(
            pos=(0.0, 0.0, 1.0),
            radius=CYLINDER_RADIUS_M,
            height=CYLINDER_HEIGHT_M,
            fixed=False,
        ),
        material=gs.materials.Rigid(rho=CYLINDER_EQUIV_DENSITY_KG_M3),
        name="mass_controlled_cylinder_free_fall",
    )
    scene.build()
    mass_before = float(cylinder.get_mass())
    cylinder.set_mass(CYLINDER_MASS_KG)
    mass_after = float(cylinder.get_mass())
    inertia_after = inertia_diag(cylinder)

    rows = []
    start = time.perf_counter()
    for step in range(args.steps + 1):
        t = step * args.dt
        pos = tensor3_to_list(cylinder.get_pos())
        vel = tensor3_to_list(cylinder.get_vel())
        rows.append({"step": step, "time_s": t, "pos_m": pos, "vel_mps": vel})
        if step < args.steps:
            scene.step(update_visualizer=False, refresh_visualizer=False)
    elapsed_s = time.perf_counter() - start

    times = np.asarray([row["time_s"] for row in rows], dtype=np.float64)
    vel_z = np.asarray([row["vel_mps"][2] for row in rows], dtype=np.float64)
    fit_start = max(5, args.steps // 10)
    acceleration_z = float(np.polyfit(times[fit_start:], vel_z[fit_start:], deg=1)[0])
    final_z_expected = 1.0 + 0.5 * -9.81 * (args.steps * args.dt) ** 2
    final_z_observed = float(rows[-1]["pos_m"][2])
    mass_relative_error = abs(mass_after - CYLINDER_MASS_KG) / CYLINDER_MASS_KG
    gravity_relative_error = abs(acceleration_z + 9.81) / 9.81

    return {
        "status": "pass" if mass_relative_error < 1.0e-3 and gravity_relative_error < 0.10 else "fail",
        "backend": args.backend,
        "dt_s": args.dt,
        "steps": args.steps,
        "wall_seconds": elapsed_s,
        "geometry": {
            "diameter_m": CYLINDER_DIAMETER_M,
            "radius_m": CYLINDER_RADIUS_M,
            "height_m": CYLINDER_HEIGHT_M,
        },
        "mass": {
            "target_kg": CYLINDER_MASS_KG,
            "before_override_kg": mass_before,
            "after_override_kg": mass_after,
            "relative_error": mass_relative_error,
        },
        "inertia": {
            "expected_uniform_solid_cylinder_diag_kg_m2": EXPECTED_INERTIA_DIAG_KG_M2,
            "genesis_runtime_diag_kg_m2": inertia_after,
            "note": "Genesis scales inertia when set_mass rescales runtime mass.",
        },
        "free_fall": {
            "fitted_acceleration_z_mps2": acceleration_z,
            "expected_acceleration_z_mps2": -9.81,
            "relative_error": gravity_relative_error,
            "initial_z_m": float(rows[0]["pos_m"][2]),
            "final_z_observed_m": final_z_observed,
            "final_z_expected_no_collision_m": final_z_expected,
            "final_vel_z_mps": float(rows[-1]["vel_mps"][2]),
        },
        "trajectory": rows,
    }


def main() -> None:
    args = parse_args()
    report = run_free_fall(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"report: {args.output}")
    print(f"status: {report['status']}")
    print(f"mass_after_kg: {report['mass']['after_override_kg']:.9g}")
    print(f"acceleration_z_mps2: {report['free_fall']['fitted_acceleration_z_mps2']:.9g}")


if __name__ == "__main__":
    main()

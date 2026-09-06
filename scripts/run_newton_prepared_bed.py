#!/usr/bin/env python3
"""Build and settle a fresh Newton MPM bed from Chrono-derived metric geometry.

This stage intentionally does not load the Genesis state archive. Cropped runs
are API/physics smoke tests only and are never acceptance-eligible.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import platform
import time
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from plyfile import PlyData
from scipy.spatial import cKDTree

from newton_contract import (
    containment_bounds,
    load_newton_config,
    particle_mass_kg,
    select_center_crop,
    speed_summary,
    validate_metric_bed,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METRIC_ROOT = (
    REPO_ROOT
    / "outputs"
    / "validity_experiment"
    / "A0_oracle_guided_offset_5mm_gate6mm_prepared_5mm_n128_ratio_matched"
    / "metric_bed_source"
)
DEFAULT_ORACLE = Path(
    "/data/christoa/Chrono/tera_splat_sim/validity_experiment/chrono_episodes/"
    "A0_oracle_guided_offset_5mm_gate6mm_v1"
)
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "outputs"
    / "validity_experiment"
    / "newton"
    / "A0_oracle_guided_offset_5mm_gate6mm_preparation_smoke"
)

os.environ.setdefault("XDG_CACHE_HOME", str(REPO_ROOT / "outputs" / ".cache"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--particles-ply",
        type=Path,
        default=DEFAULT_METRIC_ROOT / "particles_initial_mpm.ply",
    )
    parser.add_argument(
        "--metadata-json",
        type=Path,
        default=DEFAULT_METRIC_ROOT / "ground_plane_metadata.json",
    )
    parser.add_argument("--chrono-episode", type=Path, default=DEFAULT_ORACLE)
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "configs" / "newton_sand_smoke.json",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--dt-s", type=float, default=0.0005)
    parser.add_argument(
        "--solver-tolerance",
        type=float,
        default=None,
        help="Override the Newton rheology tolerance while retaining the pinned config.",
    )
    parser.add_argument(
        "--transfer-scheme",
        choices=("apic", "pic"),
        default=None,
        help="Override particle/grid transfer for controlled numerical diagnosis.",
    )
    parser.add_argument(
        "--material-damping-s",
        type=float,
        default=None,
        help="Override Newton elastic damping relaxation time for diagnosis.",
    )
    parser.add_argument(
        "--collider-projection-threshold-m",
        type=float,
        default=None,
        help=(
            "Override the allowed penetration before project_outside for every "
            "static containment collider. Newton's default is 0.01 voxel."
        ),
    )
    parser.add_argument("--duration-s", type=float, default=0.005)
    parser.add_argument("--required-duration-s", type=float, default=0.02)
    parser.add_argument("--particle-speed-threshold-mps", type=float, default=0.0005)
    parser.add_argument(
        "--center-crop-half-width-m",
        type=float,
        default=0.05,
        help="Centered square half-width for smoke runs. Set 0 for the full metric bed.",
    )
    parser.add_argument(
        "--speed-check-every",
        type=int,
        default=1,
        help="Compute particle speed percentiles every N solver steps.",
    )
    parser.add_argument("--max-fill-distance-m", type=float, default=0.0075)
    parser.add_argument(
        "--qualification-run",
        action="store_true",
        help=(
            "Enable acceptance evaluation. Requires the complete metric bed, "
            "per-step speed checks, and a duration at least as long as the hold gate."
        ),
    )
    return parser.parse_args()


def read_particle_ply(path: Path) -> np.ndarray:
    vertex = PlyData.read(path)["vertex"].data
    return np.stack([vertex["x"], vertex["y"], vertex["z"]], axis=1).astype(np.float32)


def write_particle_ply(points: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as file:
        header = (
            "ply\n"
            "format binary_little_endian 1.0\n"
            f"element vertex {points.shape[0]}\n"
            "property float x\n"
            "property float y\n"
            "property float z\n"
            "end_header\n"
        )
        file.write(header.encode("ascii"))
        file.write(np.asarray(points, dtype=np.float32).tobytes())


def load_oracle(episode: Path) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    manifest = yaml.safe_load((episode / "manifest.yaml").read_text(encoding="utf-8"))
    initial = np.load(episode / manifest["states"]["initial"]).astype(np.float32)
    valid = np.load(episode / "valid_heightmap_mask.npy").astype(bool)
    shape = tuple(int(value) for value in manifest["heightmap"]["shape"])
    if initial.shape != shape or valid.shape != shape:
        raise ValueError("Chrono initial map and valid mask must match manifest shape")
    return manifest, initial, valid


def project_surface(
    points: np.ndarray,
    manifest: dict[str, Any],
    max_fill_distance_m: float,
) -> tuple[np.ndarray, np.ndarray]:
    heightmap_info = manifest["heightmap"]
    rows, columns = (int(value) for value in heightmap_info["shape"])
    spacing = float(heightmap_info["spacing_m"])
    origin_x, origin_y = (float(value) for value in heightmap_info["origin_xy_m"])
    xs = origin_x + np.arange(columns) * spacing
    ys = origin_y + np.arange(rows) * spacing
    columns_for_particle = np.rint((points[:, 0] - origin_x) / spacing).astype(int)
    rows_for_particle = np.rint((points[:, 1] - origin_y) / spacing).astype(int)
    in_bounds = (
        (columns_for_particle >= 0)
        & (columns_for_particle < columns)
        & (rows_for_particle >= 0)
        & (rows_for_particle < rows)
    )
    heightmap = np.full((rows, columns), -np.inf, dtype=np.float32)
    np.maximum.at(
        heightmap,
        (rows_for_particle[in_bounds], columns_for_particle[in_bounds]),
        points[in_bounds, 2],
    )
    heightmap[~np.isfinite(heightmap)] = np.nan
    observed = np.isfinite(heightmap)
    if not np.any(observed):
        return heightmap, observed

    observed_rows, observed_columns = np.nonzero(observed)
    tree = cKDTree(np.column_stack((xs[observed_columns], ys[observed_rows])))
    grid_x, grid_y = np.meshgrid(xs, ys, indexing="xy")
    distances, nearest = tree.query(np.column_stack((grid_x.ravel(), grid_y.ravel())))
    supported = distances.reshape(rows, columns) <= max_fill_distance_m
    missing_supported = ~observed & supported
    observed_values = heightmap[observed]
    heightmap[missing_supported] = observed_values[
        nearest.reshape(rows, columns)[missing_supported]
    ]
    return heightmap, observed | supported


def surface_match(
    candidate: np.ndarray,
    supported: np.ndarray,
    oracle_initial: np.ndarray,
    oracle_valid: np.ndarray,
) -> dict[str, Any]:
    common = supported & oracle_valid & np.isfinite(candidate)
    if not np.any(common):
        return {
            "valid_cells": 0,
            "valid_fraction": 0.0,
            "rmse_m": None,
            "max_abs_m": None,
        }
    error = candidate[common] - oracle_initial[common]
    return {
        "valid_cells": int(np.count_nonzero(common)),
        "valid_fraction": float(np.count_nonzero(common) / np.count_nonzero(oracle_valid)),
        "rmse_m": float(np.sqrt(np.mean(error**2))),
        "max_abs_m": float(np.max(np.abs(error))),
    }


def add_static_containment(
    builder,
    newton,
    wp,
    *,
    bounds: tuple[float, float, float, float],
    ground_z: float,
    wall_height: float,
    wall_thickness: float,
    ground_mu: float,
    wall_mu: float,
) -> None:
    min_x, max_x, min_y, max_y = bounds
    center_x = 0.5 * (min_x + max_x)
    center_y = 0.5 * (min_y + max_y)
    half_x = 0.5 * (max_x - min_x)
    half_y = 0.5 * (max_y - min_y)
    half_t = 0.5 * wall_thickness
    half_h = 0.5 * wall_height
    center_z = ground_z + half_h
    ground_cfg = newton.ModelBuilder.ShapeConfig(mu=ground_mu, density=0.0)
    wall_cfg = newton.ModelBuilder.ShapeConfig(mu=wall_mu, density=0.0)
    builder.add_ground_plane(height=ground_z, cfg=ground_cfg, label="newton_ground")
    for label, position, extents in (
        (
            "newton_wall_x_min",
            (min_x - half_t, center_y, center_z),
            (half_t, half_y + wall_thickness, half_h),
        ),
        (
            "newton_wall_x_max",
            (max_x + half_t, center_y, center_z),
            (half_t, half_y + wall_thickness, half_h),
        ),
        (
            "newton_wall_y_min",
            (center_x, min_y - half_t, center_z),
            (half_x + wall_thickness, half_t, half_h),
        ),
        (
            "newton_wall_y_max",
            (center_x, max_y + half_t, center_z),
            (half_x + wall_thickness, half_t, half_h),
        ),
    ):
        builder.add_shape_box(
            -1,
            xform=wp.transform(wp.vec3(position), wp.quat_identity()),
            hx=extents[0],
            hy=extents[1],
            hz=extents[2],
            cfg=wall_cfg,
            label=label,
        )


def assign_material(model, material) -> None:
    values = {
        "young_modulus": material.young_modulus_pa,
        "poisson_ratio": material.poisson_ratio,
        "friction": material.friction_coefficient,
        "damping": material.damping_s,
        "yield_pressure": material.yield_pressure_pa,
        "tensile_yield_ratio": material.tensile_yield_ratio,
        "yield_stress": material.yield_stress_pa,
        "hardening": material.hardening,
        "dilatancy": material.dilatancy,
        "viscosity": material.viscosity,
    }
    missing = [name for name in values if not hasattr(model.mpm, name)]
    if missing:
        raise RuntimeError(f"Installed Newton is missing MPM material fields: {missing}")
    for name, value in values.items():
        getattr(model.mpm, name).fill_(float(value))


def state_arrays(state) -> dict[str, np.ndarray]:
    return {
        "position_m": state.particle_q.numpy(),
        "velocity_mps": state.particle_qd.numpy(),
        "velocity_gradient_per_s": state.mpm.particle_qd_grad.numpy(),
        "elastic_strain": state.mpm.particle_elastic_strain.numpy(),
        "plastic_jacobian": state.mpm.particle_Jp.numpy(),
        "stress_pa": state.mpm.particle_stress.numpy(),
        "deformation_transform": state.mpm.particle_transform.numpy(),
    }


def write_state(path: Path, state) -> None:
    arrays = state_arrays(state)
    np.savez_compressed(
        path,
        schema_version=np.asarray(1, dtype=np.int64),
        backend=np.asarray("newton"),
        **arrays,
    )


def write_metric_csv(path: Path, rows: list[tuple[str, Any, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(("metric", "value", "units"))
        writer.writerows(rows)


def qualification_preconditions(args: argparse.Namespace) -> None:
    if args.dt_s <= 0.0 or args.duration_s <= 0.0:
        raise ValueError("dt-s and duration-s must be positive")
    if args.solver_tolerance is not None and (
        not math.isfinite(args.solver_tolerance) or args.solver_tolerance <= 0.0
    ):
        raise ValueError("solver-tolerance must be finite and positive")
    if args.material_damping_s is not None and (
        not math.isfinite(args.material_damping_s) or args.material_damping_s < 0.0
    ):
        raise ValueError("material-damping-s must be finite and nonnegative")
    if args.collider_projection_threshold_m is not None and (
        not math.isfinite(args.collider_projection_threshold_m)
        or args.collider_projection_threshold_m < 0.0
    ):
        raise ValueError(
            "collider-projection-threshold-m must be finite and nonnegative"
        )
    if args.required_duration_s <= 0.0 or args.particle_speed_threshold_mps <= 0.0:
        raise ValueError("speed hold duration and threshold must be positive")
    if args.center_crop_half_width_m < 0.0:
        raise ValueError("center-crop-half-width-m must be nonnegative")
    if args.speed_check_every <= 0:
        raise ValueError("speed-check-every must be positive")
    if args.qualification_run:
        if args.center_crop_half_width_m != 0.0:
            raise ValueError("qualification runs require the complete metric bed")
        if args.speed_check_every != 1:
            raise ValueError("qualification runs require per-step speed checks")
        if args.duration_s < args.required_duration_s:
            raise ValueError("qualification duration is shorter than the speed hold gate")


def main() -> None:
    args = parse_args()
    qualification_preconditions(args)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    config = load_newton_config(args.config.resolve())
    solver_tolerance = (
        config.solver.tolerance
        if args.solver_tolerance is None
        else float(args.solver_tolerance)
    )
    resolved_config = json.loads(json.dumps(config.raw))
    resolved_config["solver"]["tolerance"] = solver_tolerance
    transfer_scheme = config.solver.transfer_scheme
    if args.transfer_scheme is not None:
        transfer_scheme = args.transfer_scheme
    material_damping_s = config.material.damping_s
    if args.material_damping_s is not None:
        material_damping_s = float(args.material_damping_s)
    resolved_config["solver"]["transfer_scheme"] = transfer_scheme
    resolved_config["material"]["damping_s"] = material_damping_s
    source_metadata = json.loads(args.metadata_json.resolve().read_text(encoding="utf-8"))
    source_points = read_particle_ply(args.particles_ply.resolve())
    source_surface_count, spacing, ground_z = validate_metric_bed(
        source_points, source_metadata
    )
    points, surface_count, selection = select_center_crop(
        source_points,
        source_surface_count,
        args.center_crop_half_width_m,
    )
    bounds = containment_bounds(points, spacing)
    mass = particle_mass_kg(config.material.density_kg_m3, spacing)

    import newton
    import warp as wp
    from newton.solvers import SolverImplicitMPM

    wp.init()
    device = wp.get_device(args.device)
    builder = newton.ModelBuilder()
    SolverImplicitMPM.register_custom_attributes(builder)
    count = points.shape[0]
    builder.add_particles(
        pos=points,
        vel=np.zeros_like(points),
        mass=np.full(count, mass, dtype=np.float32),
        radius=np.full(count, 0.5 * spacing, dtype=np.float32),
    )
    add_static_containment(
        builder,
        newton,
        wp,
        bounds=bounds,
        ground_z=ground_z,
        wall_height=config.contact.wall_height_m,
        wall_thickness=config.contact.wall_thickness_m,
        ground_mu=config.contact.ground_friction_coefficient,
        wall_mu=config.contact.wall_friction_coefficient,
    )
    model = builder.finalize(device=device)
    model.set_gravity((0.0, 0.0, -9.81))
    assign_material(model, config.material)
    model.mpm.damping.fill_(material_damping_s)

    solver_config = SolverImplicitMPM.Config(
        voxel_size=config.solver.voxel_size_m,
        grid_type=config.solver.grid_type,
        grid_padding=config.solver.grid_padding,
        transfer_scheme=transfer_scheme,
        integration_scheme=config.solver.integration_scheme,
        strain_basis=config.solver.strain_basis,
        collider_basis=config.solver.collider_basis,
        velocity_basis=config.solver.velocity_basis,
        max_iterations=config.solver.max_iterations,
        tolerance=solver_tolerance,
        air_drag=config.solver.air_drag,
        critical_fraction=config.solver.critical_fraction,
    )
    state_0 = model.state()
    state_1 = model.state()
    solver = SolverImplicitMPM(model, config=solver_config)
    if args.collider_projection_threshold_m is not None:
        collider_count = int(solver.collider_body_index.shape[0])
        solver.setup_collider(
            collider_projection_threshold=[
                float(args.collider_projection_threshold_m)
            ]
            * collider_count
        )

    initial_arrays = state_arrays(state_0)
    write_particle_ply(initial_arrays["position_m"], output / "particles_initial_mpm.ply")
    write_state(output / "newton_state_initial.npz", state_0)

    total_steps = int(math.ceil(args.duration_s / args.dt_s))
    required_checks = int(math.ceil(args.required_duration_s / (args.dt_s * args.speed_check_every)))
    low_speed_checks = 0
    first_equilibrium_s = None
    diagnostic_rows: list[dict[str, Any]] = []
    wall_start = time.perf_counter()
    for step in range(1, total_steps + 1):
        solver.step(state_0, state_1, None, None, args.dt_s)
        solver.project_outside(state_1, state_1, args.dt_s)
        state_0, state_1 = state_1, state_0
        if step % args.speed_check_every == 0 or step == total_steps:
            summary = speed_summary(state_0.particle_qd.numpy())
            diagnostic_rows.append(
                {
                    "step": step,
                    "time_s": step * args.dt_s,
                    **summary,
                }
            )
            if summary["p99_mps"] <= args.particle_speed_threshold_mps:
                low_speed_checks += 1
                if low_speed_checks >= required_checks and first_equilibrium_s is None:
                    first_equilibrium_s = step * args.dt_s
            else:
                low_speed_checks = 0
    wp.synchronize_device(device)
    elapsed_s = time.perf_counter() - wall_start

    final_arrays = state_arrays(state_0)
    final_speed = speed_summary(final_arrays["velocity_mps"])
    finite = all(np.isfinite(array).all() for array in final_arrays.values())
    write_particle_ply(final_arrays["position_m"], output / "particles_final_mpm.ply")
    write_state(output / "newton_state_final.npz", state_0)

    oracle_manifest, oracle_initial, oracle_valid = load_oracle(args.chrono_episode.resolve())
    initial_map, initial_supported = project_surface(
        initial_arrays["position_m"],
        oracle_manifest,
        args.max_fill_distance_m,
    )
    final_map, final_supported = project_surface(
        final_arrays["position_m"],
        oracle_manifest,
        args.max_fill_distance_m,
    )
    initial_match = surface_match(initial_map, initial_supported, oracle_initial, oracle_valid)
    final_match = surface_match(final_map, final_supported, oracle_initial, oracle_valid)
    common_valid = final_supported & oracle_valid & np.isfinite(final_map)
    np.save(output / "initial_heightmap_m.npy", initial_map)
    np.save(output / "settled_heightmap_m.npy", final_map)
    np.save(output / "valid_heightmap_mask.npy", common_valid)

    equilibrium = first_equilibrium_s is not None
    accepted = bool(
        args.qualification_run
        and finite
        and equilibrium
        and final_match["valid_fraction"] >= 0.95
        and final_match["rmse_m"] is not None
        and final_match["rmse_m"] <= 0.005
        and final_match["max_abs_m"] <= 0.010
    )
    manifest = {
        "schema_version": 1,
        "backend": "newton",
        "accepted": accepted,
        "acceptance_eligible": bool(args.qualification_run),
        "status": "accepted" if accepted else "diagnostic_only",
        "source": {
            "particles_ply": str(args.particles_ply.resolve()),
            "metadata_json": str(args.metadata_json.resolve()),
            "chrono_episode": str(args.chrono_episode.resolve()),
            "coordinate_frame": "bed",
            "geometry_role": "Chrono-derived metric geometry",
            "genesis_state_loaded": False,
            "source_particle_count": int(source_points.shape[0]),
            "source_surface_particle_count": int(source_surface_count),
        },
        "selection": {
            "mode": "full" if args.center_crop_half_width_m == 0.0 else "center_crop_smoke",
            "center_crop_half_width_m": float(args.center_crop_half_width_m),
            "particle_count": int(points.shape[0]),
            "surface_particle_count": int(surface_count),
            "source_fraction": float(np.count_nonzero(selection) / selection.size),
        },
        "environment": {
            "python": platform.python_version(),
            "newton": newton.__version__,
            "warp": wp.__version__,
            "device": str(device),
        },
        "material": resolved_config["material"],
        "solver": {
            **resolved_config["solver"],
            "dt_s": float(args.dt_s),
            "duration_s": float(total_steps * args.dt_s),
            "steps": total_steps,
            "project_outside_each_step": True,
            "collider_projection_threshold_m": args.collider_projection_threshold_m,
        },
        "contact": {
            **config.raw["contact"],
            "ground_z_m": ground_z,
            "bounds_xy_m": list(bounds),
        },
        "particle": {
            "spacing_m": spacing,
            "radius_m": 0.5 * spacing,
            "mass_kg": mass,
            "total_mass_kg": mass * points.shape[0],
        },
        "settling": {
            "finite": finite,
            "equilibrium": equilibrium,
            "first_equilibrium_s": first_equilibrium_s,
            "speed_threshold_mps": float(args.particle_speed_threshold_mps),
            "required_duration_s": float(args.required_duration_s),
            "speed_check_every_steps": int(args.speed_check_every),
            "final_speed": final_speed,
            "wall_time_s": elapsed_s,
        },
        "surface_match": {
            "projection": "highest_particle_per_Chrono_cell_then_nearest_fill",
            "max_fill_distance_m": float(args.max_fill_distance_m),
            "initial": initial_match,
            "settled": final_match,
            "acceptance_rmse_m": 0.005,
            "acceptance_max_abs_m": 0.010,
            "acceptance_min_valid_fraction": 0.95,
        },
        "state": {
            "initial": "newton_state_initial.npz",
            "final": "newton_state_final.npz",
            "format": (
                "Newton particle arrays: position, velocity, velocity gradient, elastic strain, "
                "plastic Jacobian, stress, and deformation transform"
            ),
            "restart_qualified": False,
            "restart_note": (
                "The archive does not serialize solver grid/warm-start history; "
                "reconstructed response models must requalify H0 and speed or prepare in-process."
            ),
        },
    }
    (output / "newton_prepared_bed_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "resolved_config.json").write_text(
        json.dumps(resolved_config, indent=2) + "\n",
        encoding="utf-8",
    )
    with (output / "pre_settle_diagnostic.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(diagnostic_rows[0]))
        writer.writeheader()
        writer.writerows(diagnostic_rows)
    write_metric_csv(
        output / "run_metrics.csv",
        [
            ("acceptance_eligible", int(args.qualification_run), "boolean"),
            ("accepted", int(accepted), "boolean"),
            ("particle_count", points.shape[0], "count"),
            ("surface_particle_count", surface_count, "count"),
            ("duration", total_steps * args.dt_s, "seconds"),
            ("wall_time", elapsed_s, "seconds"),
            ("final_particle_speed_p50", final_speed["p50_mps"], "m/s"),
            ("final_particle_speed_p95", final_speed["p95_mps"], "m/s"),
            ("final_particle_speed_p99", final_speed["p99_mps"], "m/s"),
            ("final_particle_speed_max", final_speed["max_mps"], "m/s"),
            ("settled_h0_valid_fraction", final_match["valid_fraction"], "fraction"),
            ("settled_h0_rmse", final_match["rmse_m"], "meters"),
            ("settled_h0_max_abs", final_match["max_abs_m"], "meters"),
        ],
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

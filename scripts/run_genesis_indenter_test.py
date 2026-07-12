#!/usr/bin/env python3
"""Run a minimal displacement-controlled cylinder indenter on the settled base."""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WRITABLE_CACHE = REPO_ROOT / "outputs" / ".cache"
os.environ.setdefault("XDG_CACHE_HOME", str(WRITABLE_CACHE))
os.environ.setdefault("GS_CACHE_FILE_PATH", str(WRITABLE_CACHE / "genesis"))
os.environ.setdefault("NUMBA_CACHE_DIR", str(WRITABLE_CACHE / "numba"))
os.environ.setdefault("MPLCONFIGDIR", str(WRITABLE_CACHE / "matplotlib"))

import numpy as np
import torch

from particle_io import load_material_config, read_particle_ply, write_particle_ply
from run_genesis_ground_plane_solver import cuda_device_name, directory_size_bytes, make_bounds, tensor_to_numpy


DEFAULT_BASE = REPO_ROOT / "outputs" / "base_settled_stiff_mid"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--initial-particles-ply", type=Path, default=DEFAULT_BASE / "particles_initial_mpm.ply")
    parser.add_argument("--initial-metadata-json", type=Path, default=DEFAULT_BASE / "ground_plane_metadata.json")
    parser.add_argument("--config", type=Path, default=REPO_ROOT / "configs" / "physgaussian_sand_stiff_mid.json")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "outputs" / "indenter_smoke_test")
    parser.add_argument("--query-xy", type=float, nargs=2, default=(0.0, 0.0))
    parser.add_argument("--indenter-radius", type=float, default=0.08)
    parser.add_argument("--indenter-height", type=float, default=0.04)
    parser.add_argument("--indent-depth", type=float, default=0.02)
    parser.add_argument("--indent-start-time", type=float, default=0.10)
    parser.add_argument("--indent-ramp-time", type=float, default=0.45)
    parser.add_argument("--indent-hold-time", type=float, default=0.45)
    parser.add_argument("--start-clearance", type=float, default=0.02)
    parser.add_argument("--indenter-friction", type=float, default=0.4)
    parser.add_argument("--indenter-softness", type=float, default=0.0)
    parser.add_argument("--indenter-restitution", type=float, default=0.0)
    parser.add_argument(
        "--indenter-body-mode",
        choices=("rigid", "tool"),
        default="rigid",
        help=(
            "rigid uses a coupled Genesis rigid body. tool uses a prescribed Genesis Tool SDF collider, "
            "which is one-way tool->MPM contact and does not directly edit particles."
        ),
    )
    parser.add_argument(
        "--indenter-sdf-res",
        type=int,
        default=128,
        help="SDF resolution for --indenter-body-mode tool.",
    )
    parser.add_argument(
        "--fixed-indenter",
        action="store_true",
        help="Keep the cylinder fixed and move only its pose. Default uses a free rigid body with commanded velocity.",
    )
    parser.add_argument(
        "--indenter-control-mode",
        choices=("pose", "pd"),
        default="pd",
        help="How to drive the rigid indenter. pd uses Genesis DOF controllers; pose uses direct set_pos.",
    )
    parser.add_argument("--indenter-kp", type=float, default=8.0e5)
    parser.add_argument("--indenter-kv", type=float, default=2.0e4)
    parser.add_argument("--indenter-force-limit", type=float, default=2.0e5)
    parser.add_argument(
        "--debug-kinematic-contact",
        action="store_true",
        help="Deprecated alias for --debug-contact-mode column-clamp.",
    )
    parser.add_argument(
        "--debug-contact-mode",
        choices=("none", "column-clamp", "surface-plastic"),
        default="none",
        help=(
            "Debug contact approximation. column-clamp moves every particle under the disk below the bottom. "
            "surface-plastic only edits surface particles and adds a simple radial rim."
        ),
    )
    parser.add_argument(
        "--surface-contact-band",
        type=float,
        default=0.0,
        help="If positive, only surface particles within this distance above the indenter bottom are clamped. 0 disables the upper band.",
    )
    parser.add_argument(
        "--surface-lateral-scale",
        type=float,
        default=0.35,
        help="Outward XY displacement scale for surface particles directly under the indenter.",
    )
    parser.add_argument(
        "--rim-height-scale",
        type=float,
        default=0.35,
        help="Accumulated rim height scale as a fraction of positive indentation increment.",
    )
    parser.add_argument(
        "--rim-width-scale",
        type=float,
        default=0.45,
        help="Rim width as a fraction of indenter radius.",
    )
    parser.add_argument("--backend", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--steps", type=int, default=4000)
    parser.add_argument("--dt", type=float, default=0.00025)
    parser.add_argument("--substeps", type=int, default=10)
    parser.add_argument("--save-every", type=int, default=40)
    parser.add_argument("--metrics-interval", type=int, default=400)
    parser.add_argument("--n-grid", type=int, default=64)
    parser.add_argument("--grid-lim", type=float, default=None)
    parser.add_argument("--particle-size", type=float, default=0.0125)
    parser.add_argument("--ground-coup-friction", type=float, default=0.2)
    parser.add_argument("--ground-coup-softness", type=float, default=0.0)
    parser.add_argument("--ground-coup-restitution", type=float, default=0.0)
    return parser.parse_args()


def smoothstep_depth(t: float, *, start: float, ramp: float, depth: float) -> float:
    tau = np.clip((t - start) / max(ramp, 1e-12), 0.0, 1.0)
    s = tau * tau * (3.0 - 2.0 * tau)
    return float(depth * s)


def estimate_surface_z(points: np.ndarray, query_xy: np.ndarray, radius: float) -> float:
    distance = np.linalg.norm(points[:, :2] - query_xy[None, :], axis=1)
    local = points[distance <= max(radius, 1e-6)]
    if local.shape[0] == 0:
        local = points[np.argsort(distance)[: min(512, points.shape[0])]]
    return float(np.quantile(local[:, 2], 0.95))


def write_pose_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def get_tool_position(tool) -> tuple[float, float, float]:
    state = tool.get_state()
    pos = state.pos.detach().cpu().numpy().reshape(-1, 3)[0]
    return float(pos[0]), float(pos[1]), float(pos[2])


def write_metrics_csv(path: Path, rows: list[tuple[str, object, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value", "unit"])
        writer.writerows(rows)


def write_unit_cylinder_obj(path: Path, *, sections: int = 96) -> None:
    """Write a z-up cylinder with radius 0.5 and height 1.0."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return

    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []
    for z in (-0.5, 0.5):
        for i in range(sections):
            theta = 2.0 * np.pi * i / sections
            verts.append((0.5 * np.cos(theta), 0.5 * np.sin(theta), z))
    bottom_center = len(verts)
    verts.append((0.0, 0.0, -0.5))
    top_center = len(verts)
    verts.append((0.0, 0.0, 0.5))

    for i in range(sections):
        j = (i + 1) % sections
        bottom_i = i
        bottom_j = j
        top_i = sections + i
        top_j = sections + j
        faces.append((bottom_i + 1, bottom_j + 1, top_j + 1))
        faces.append((bottom_i + 1, top_j + 1, top_i + 1))
        faces.append((bottom_center + 1, bottom_j + 1, bottom_i + 1))
        faces.append((top_center + 1, top_i + 1, top_j + 1))

    with path.open("w", encoding="utf-8") as f:
        f.write("# Unit z-up cylinder for Genesis Tool indenter\n")
        for v in verts:
            f.write(f"v {v[0]:.9f} {v[1]:.9f} {v[2]:.9f}\n")
        for face in faces:
            f.write(f"f {face[0]} {face[1]} {face[2]}\n")


def radial_unit(dx: torch.Tensor, dy: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    radius = torch.sqrt(dx * dx + dy * dy)
    safe_radius = torch.clamp(radius, min=1e-8)
    ux = dx / safe_radius
    uy = dy / safe_radius
    center = radius < 1e-8
    if torch.any(center):
        ux = ux.clone()
        uy = uy.clone()
        ux[center] = 1.0
        uy[center] = 0.0
    return ux, uy, radius


def apply_column_clamp_contact(
    *,
    sand,
    query_xy: np.ndarray,
    indenter_radius: float,
    bottom_z: float,
    velocity_z: float,
) -> None:
    pos = sand.get_particles_pos()
    dx = pos[:, 0] - float(query_xy[0])
    dy = pos[:, 1] - float(query_xy[1])
    contact_mask = (dx * dx + dy * dy <= indenter_radius * indenter_radius) & (pos[:, 2] > bottom_z)
    if not torch.any(contact_mask):
        return

    pos = pos.clone()
    vel = sand.get_particles_vel().clone()
    pos[contact_mask, 2] = bottom_z
    vel[contact_mask, 2] = torch.minimum(
        vel[contact_mask, 2],
        torch.as_tensor(velocity_z, dtype=vel.dtype, device=vel.device),
    )
    sand.set_particles_pos(pos)
    sand.set_particles_vel(vel)


def apply_surface_plastic_contact(
    *,
    sand,
    initial_surface_pos: torch.Tensor,
    query_xy: np.ndarray,
    surface_count: int,
    indenter_radius: float,
    bottom_z: float,
    velocity_z: float,
    current_depth: float,
    surface_contact_band: float,
    surface_lateral_scale: float,
    rim_height_scale: float,
    rim_width_scale: float,
) -> None:
    if surface_count <= 0:
        return

    pos_all = sand.get_particles_pos()
    vel_all = sand.get_particles_vel()
    pos = pos_all[:surface_count]
    vel = vel_all[:surface_count]
    dx = pos[:, 0] - float(query_xy[0])
    dy = pos[:, 1] - float(query_xy[1])
    ux, uy, radius = radial_unit(dx, dy)

    inside = radius <= indenter_radius
    contact = inside & (pos[:, 2] > bottom_z)
    if surface_contact_band > 0.0:
        contact &= pos[:, 2] <= bottom_z + surface_contact_band
    if torch.any(contact):
        contact_idx = torch.nonzero(contact, as_tuple=False).squeeze(1)
        penetration = pos[contact, 2] - bottom_z
        pos_all = pos_all.clone()
        vel_all = vel_all.clone()
        pos_all[contact_idx, 2] = bottom_z
        lateral = torch.clamp(penetration * surface_lateral_scale, min=0.0, max=indenter_radius * 0.25)
        edge_weight = 0.35 + 0.65 * torch.clamp(radius[contact] / max(indenter_radius, 1e-8), 0.0, 1.0)
        pos_all[contact_idx, 0] += ux[contact] * lateral * edge_weight
        pos_all[contact_idx, 1] += uy[contact] * lateral * edge_weight
        vel_all[contact_idx, 2] = torch.minimum(
            vel[contact, 2],
            torch.as_tensor(velocity_z, dtype=vel.dtype, device=vel.device),
        )
    else:
        pos_all = None
        vel_all = None

    if current_depth > 0.0 and rim_height_scale > 0.0:
        if pos_all is None:
            pos_all = sand.get_particles_pos().clone()
            vel_all = sand.get_particles_vel().clone()
            pos = pos_all[:surface_count]
            vel = vel_all[:surface_count]
            dx = pos[:, 0] - float(query_xy[0])
            dy = pos[:, 1] - float(query_xy[1])
            ux, uy, radius = radial_unit(dx, dy)
        initial_surface = initial_surface_pos[:surface_count]
        dx0 = initial_surface[:, 0] - float(query_xy[0])
        dy0 = initial_surface[:, 1] - float(query_xy[1])
        ux0, uy0, radius0 = radial_unit(dx0, dy0)
        rim_width = max(indenter_radius * rim_width_scale, 1e-8)
        annulus = (radius0 > indenter_radius) & (radius0 <= indenter_radius + 2.5 * rim_width)
        if torch.any(annulus):
            annulus_idx = torch.nonzero(annulus, as_tuple=False).squeeze(1)
            normalized = (radius0[annulus] - indenter_radius) / rim_width
            shape = torch.exp(-(normalized * normalized))
            rim_target_z = initial_surface_pos[annulus_idx, 2] + current_depth * rim_height_scale * shape
            outward = current_depth * surface_lateral_scale * 0.5 * shape
            target_x = initial_surface_pos[annulus_idx, 0] + ux0[annulus] * outward
            target_y = initial_surface_pos[annulus_idx, 1] + uy0[annulus] * outward
            pos_all[annulus_idx, 2] = torch.maximum(pos_all[annulus_idx, 2], rim_target_z)
            pos_all[annulus_idx, 0] = target_x
            pos_all[annulus_idx, 1] = target_y

    if pos_all is not None:
        sand.set_particles_pos(pos_all)
        sand.set_particles_vel(vel_all)


def main() -> None:
    args = parse_args()
    if args.debug_kinematic_contact and args.debug_contact_mode == "none":
        args.debug_contact_mode = "column-clamp"
    total_start = time.perf_counter()
    import genesis as gs

    points = read_particle_ply(args.initial_particles_ply)
    with args.initial_metadata_json.open("r", encoding="utf-8") as f:
        metadata = json.load(f)
    config = load_material_config(args.config)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    surface_count = int(metadata.get("surface_particle_count", 0))

    query_xy = np.asarray(args.query_xy, dtype=np.float32)
    surface_z = estimate_surface_z(points, query_xy, args.indenter_radius)
    initial_center_z = surface_z + args.start_clearance + args.indenter_height * 0.5

    backend = gs.cuda if args.backend == "cuda" else gs.cpu
    init_start = time.perf_counter()
    gs.init(backend=backend, precision="32", seed=0, logging_level="warning")
    genesis_init_seconds = time.perf_counter() - init_start

    grid_lim = float(args.grid_lim if args.grid_lim is not None else config.get("grid_lim", 2.0))
    lower_bound, upper_bound = make_bounds(points, metadata, grid_lim)
    n_grid = int(args.n_grid)
    gravity = tuple(float(v) for v in config.get("g", [0.0, 0.0, -9.81]))

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=args.dt, substeps=args.substeps, gravity=gravity, floor_height=lower_bound[2]),
        coupler_options=gs.options.LegacyCouplerOptions(rigid_mpm=True),
        tool_options=gs.options.ToolOptions(dt=args.dt, floor_height=lower_bound[2]),
        mpm_options=gs.options.MPMOptions(
            dt=args.dt,
            gravity=gravity,
            grid_density=n_grid / grid_lim,
            particle_size=args.particle_size,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
        ),
        show_viewer=False,
    )
    ground_z = float(metadata["ground_plane_mpm"]["point"][2])
    scene.add_entity(
        gs.morphs.Plane(pos=(0.0, 0.0, ground_z), normal=(0.0, 0.0, 1.0), fixed=True, plane_size=(grid_lim * 3.0, grid_lim * 3.0)),
        material=gs.materials.Rigid(
            needs_coup=True,
            coup_friction=args.ground_coup_friction,
            coup_softness=args.ground_coup_softness,
            coup_restitution=args.ground_coup_restitution,
        ),
        name="ground_plane",
    )
    indenter = None
    if args.indenter_body_mode == "tool":
        tool_mesh_path = args.output_dir / "assets" / "unit_cylinder_tool.obj"
        write_unit_cylinder_obj(tool_mesh_path)
        indenter = scene.add_entity(
            gs.morphs.Mesh(
                file=str(tool_mesh_path),
                pos=(float(query_xy[0]), float(query_xy[1]), initial_center_z),
                scale=(args.indenter_radius * 2.0, args.indenter_radius * 2.0, args.indenter_height),
            ),
            material=gs.materials.Tool(
                friction=args.indenter_friction,
                coup_softness=max(args.indenter_softness, 1.0e-6),
                collision=True,
                sdf_res=args.indenter_sdf_res,
            ),
            name="circular_indenter_tool",
        )
    else:
        indenter = scene.add_entity(
            gs.morphs.Cylinder(
                pos=(float(query_xy[0]), float(query_xy[1]), initial_center_z),
                radius=args.indenter_radius,
                height=args.indenter_height,
                fixed=args.fixed_indenter,
            ),
            material=gs.materials.Rigid(
                needs_coup=True,
                coup_friction=args.indenter_friction,
                coup_softness=args.indenter_softness,
                coup_restitution=args.indenter_restitution,
            ),
            name="circular_indenter",
        )
    sand = scene.add_entity(
        gs.morphs.Nowhere(n_particles=int(points.shape[0])),
        material=gs.materials.MPM.Sand(
            E=float(config.get("E", 1e5)),
            nu=float(config.get("nu", 0.2)),
            rho=float(config.get("density", config.get("rho", 1000.0))),
            friction_angle=float(config.get("friction_angle", 45.0)),
            sampler="random",
        ),
        name="sand",
    )

    build_start = time.perf_counter()
    scene.build()
    scene_build_seconds = time.perf_counter() - build_start
    sand.set_particles_pos(torch.as_tensor(points, dtype=torch.float32, device=gs.device))
    sand.set_particles_vel(torch.zeros((points.shape[0], 3), dtype=torch.float32, device=gs.device))
    sand.set_particles_active(torch.ones((points.shape[0],), dtype=torch.bool, device=gs.device))
    initial_surface_pos = torch.as_tensor(points[:surface_count], dtype=torch.float32, device=gs.device)
    if args.indenter_body_mode == "tool":
        indenter.set_position([[float(query_xy[0]), float(query_xy[1]), initial_center_z]])
        indenter.set_velocity(vel=[[0.0, 0.0, 0.0]])
    elif args.indenter_control_mode == "pd" and indenter.n_dofs > 0:
        dof_position = np.zeros((indenter.n_dofs,), dtype=np.float32)
        dof_velocity = np.zeros((indenter.n_dofs,), dtype=np.float32)
        dof_kp = np.full((indenter.n_dofs,), args.indenter_kp, dtype=np.float32)
        dof_kv = np.full((indenter.n_dofs,), args.indenter_kv, dtype=np.float32)
        force_lower = np.full((indenter.n_dofs,), -args.indenter_force_limit, dtype=np.float32)
        force_upper = np.full((indenter.n_dofs,), args.indenter_force_limit, dtype=np.float32)
        dof_position[:3] = (float(query_xy[0]), float(query_xy[1]), initial_center_z)
        indenter.set_dofs_kp(dof_kp)
        indenter.set_dofs_kv(dof_kv)
        indenter.set_dofs_force_range(force_lower, force_upper)
        indenter.set_dofs_position(dof_position, zero_velocity=True)
        indenter.control_dofs_position_velocity(dof_position, dof_velocity)

    sim_dir = args.output_dir / "simulation_ply"
    write_particle_ply(tensor_to_numpy(sand.get_particles_pos()), sim_dir / "sim_0000.ply")
    write_particle_ply(points, args.output_dir / "particles_initial_mpm.ply")

    run_metadata = {
        **metadata,
        "load_mode": "indenter-displacement",
        "query_xy": query_xy.astype(float).tolist(),
        "surface_z_at_query": surface_z,
        "indenter": {
            "radius": args.indenter_radius,
            "height": args.indenter_height,
            "indent_depth": args.indent_depth,
            "indent_start_time": args.indent_start_time,
            "indent_ramp_time": args.indent_ramp_time,
            "indent_hold_time": args.indent_hold_time,
            "start_clearance": args.start_clearance,
            "friction": args.indenter_friction,
            "softness": args.indenter_softness,
            "restitution": args.indenter_restitution,
            "initial_center_z": initial_center_z,
            "body_mode": args.indenter_body_mode,
            "sdf_res": args.indenter_sdf_res,
            "control_mode": args.indenter_control_mode,
            "kp": args.indenter_kp,
            "kv": args.indenter_kv,
            "force_limit": args.indenter_force_limit,
            "debug_contact_mode": args.debug_contact_mode,
            "surface_contact_band": args.surface_contact_band,
            "surface_lateral_scale": args.surface_lateral_scale,
            "rim_height_scale": args.rim_height_scale,
            "rim_width_scale": args.rim_width_scale,
        },
    }
    with (args.output_dir / "ground_plane_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(run_metadata, f, indent=2)

    actual_x = float(query_xy[0])
    actual_y = float(query_xy[1])
    actual_z = initial_center_z
    if args.indenter_body_mode == "tool":
        actual_x, actual_y, actual_z = get_tool_position(indenter)
    pose_rows = [
        {
            "step": 0,
            "time": 0.0,
            "x": actual_x,
            "y": actual_y,
            "z": actual_z,
            "command_x": float(query_xy[0]),
            "command_y": float(query_xy[1]),
            "command_z": initial_center_z,
            "depth": 0.0,
            "bottom_z": actual_z - args.indenter_height * 0.5,
            "command_bottom_z": initial_center_z - args.indenter_height * 0.5,
        }
    ]
    loop_start = time.perf_counter()
    previous_center_z = initial_center_z
    previous_depth = 0.0
    for step in range(1, args.steps + 1):
        t = step * args.dt
        depth = smoothstep_depth(t, start=args.indent_start_time, ramp=args.indent_ramp_time, depth=args.indent_depth)
        center_z = initial_center_z - depth
        velocity_z = (center_z - previous_center_z) / args.dt
        if args.indenter_body_mode == "tool":
            # ToolEntity is an advected prescribed collider. Updating velocity
            # each step keeps motion in Genesis' local Tool frame buffer.
            indenter.set_velocity(vel=[[0.0, 0.0, velocity_z]])
        elif args.indenter_control_mode == "pd" and indenter.n_dofs > 0:
            dof_position = np.zeros((indenter.n_dofs,), dtype=np.float32)
            dof_velocity = np.zeros((indenter.n_dofs,), dtype=np.float32)
            dof_position[:3] = (float(query_xy[0]), float(query_xy[1]), center_z)
            if indenter.n_dofs >= 3:
                dof_velocity[2] = velocity_z
            indenter.control_dofs_position_velocity(dof_position, dof_velocity)
        else:
            indenter.set_pos((float(query_xy[0]), float(query_xy[1]), center_z), zero_velocity=False)
            if not args.fixed_indenter and indenter.n_dofs > 0:
                dof_velocity = np.zeros((indenter.n_dofs,), dtype=np.float32)
                if indenter.n_dofs >= 3:
                    dof_velocity[2] = velocity_z
                indenter.set_dofs_velocity(dof_velocity)
        scene.step(update_visualizer=False, refresh_visualizer=False)
        bottom_z = center_z - args.indenter_height * 0.5
        if args.debug_contact_mode == "column-clamp":
            apply_column_clamp_contact(
                sand=sand,
                query_xy=query_xy,
                indenter_radius=args.indenter_radius,
                bottom_z=bottom_z,
                velocity_z=velocity_z,
            )
        elif args.debug_contact_mode == "surface-plastic":
            apply_surface_plastic_contact(
                sand=sand,
                initial_surface_pos=initial_surface_pos,
                query_xy=query_xy,
                surface_count=surface_count,
                indenter_radius=args.indenter_radius,
                bottom_z=bottom_z,
                velocity_z=velocity_z,
                current_depth=depth,
                surface_contact_band=args.surface_contact_band,
                surface_lateral_scale=args.surface_lateral_scale,
                rim_height_scale=args.rim_height_scale,
                rim_width_scale=args.rim_width_scale,
            )
        previous_center_z = center_z
        previous_depth = depth
        if step % max(args.save_every, 1) == 0 or step == args.steps:
            write_particle_ply(tensor_to_numpy(sand.get_particles_pos()), sim_dir / f"sim_{step:04d}.ply")
        if step % max(args.save_every, 1) == 0 or step == args.steps:
            actual_x = float(query_xy[0])
            actual_y = float(query_xy[1])
            actual_z = center_z
            if args.indenter_body_mode == "tool":
                actual_x, actual_y, actual_z = get_tool_position(indenter)
            pose_rows.append(
                {
                    "step": step,
                    "time": t,
                    "x": actual_x,
                    "y": actual_y,
                    "z": actual_z,
                    "command_x": float(query_xy[0]),
                    "command_y": float(query_xy[1]),
                    "command_z": center_z,
                    "depth": depth,
                    "bottom_z": actual_z - args.indenter_height * 0.5,
                    "command_bottom_z": center_z - args.indenter_height * 0.5,
                }
            )
    loop_seconds = time.perf_counter() - loop_start

    write_pose_csv(args.output_dir / "indenter_pose.csv", pose_rows)
    final_points = tensor_to_numpy(sand.get_particles_pos())
    write_particle_ply(final_points, args.output_dir / "particles_final_mpm.ply")
    write_metrics_csv(
        args.output_dir / "run_metrics.csv",
        [
            ("status", "completed", ""),
            ("backend", args.backend, ""),
            ("cuda_device", cuda_device_name(), ""),
            ("particles", points.shape[0], "count"),
            ("steps", args.steps, "count"),
            ("dt", args.dt, "seconds"),
            ("substeps", args.substeps, "count"),
            ("duration", args.steps * args.dt, "seconds"),
            ("particle_size", args.particle_size, "meters"),
            ("surface_z_at_query", surface_z, "meters"),
            ("target_indent_depth", args.indent_depth, "meters"),
            ("final_indent_depth", pose_rows[-1]["depth"], "meters"),
            ("indenter_body_mode", args.indenter_body_mode, ""),
            ("indenter_sdf_res", args.indenter_sdf_res, ""),
            ("indenter_control_mode", args.indenter_control_mode, ""),
            ("indenter_kp", args.indenter_kp, ""),
            ("indenter_kv", args.indenter_kv, ""),
            ("indenter_force_limit", args.indenter_force_limit, "newtons"),
            ("debug_kinematic_contact", args.debug_kinematic_contact, ""),
            ("debug_contact_mode", args.debug_contact_mode, ""),
            ("surface_contact_band", args.surface_contact_band, "meters"),
            ("surface_lateral_scale", args.surface_lateral_scale, ""),
            ("rim_height_scale", args.rim_height_scale, ""),
            ("rim_width_scale", args.rim_width_scale, ""),
            ("genesis_init_seconds", genesis_init_seconds, "seconds"),
            ("scene_build_seconds", scene_build_seconds, "seconds"),
            ("simulation_loop_seconds", loop_seconds, "seconds"),
            ("steps_per_second", args.steps / max(loop_seconds, 1e-12), "steps/second"),
            ("total_wall_seconds", time.perf_counter() - total_start, "seconds"),
            ("output_dir_bytes", directory_size_bytes(args.output_dir), "bytes"),
        ],
    )
    print(f"particles: {points.shape[0]}")
    print(f"surface_z_at_query: {surface_z:.6f}")
    print(f"output: {args.output_dir}")


if __name__ == "__main__":
    main()

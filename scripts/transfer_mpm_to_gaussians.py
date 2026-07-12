#!/usr/bin/env python3
"""Transfer MPM surface displacement back to a 3DGS PLY.

This is the first Phase-6 transfer path: center-only updates. It preserves all
non-position Gaussian attributes and updates the source PLY's x/y/z fields for
the splats that were used as the simulated surface entity.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from plyfile import PlyData, PlyElement

from particle_io import read_particle_ply
from view_iteration_7000 import (
    AXIS_TRANSFORMS,
    DEFAULT_PLY,
    choose_indices,
    estimate_plane_normal_ransac,
    read_fields,
    rotation_between_vectors,
    sigmoid,
)


DEFAULT_RUN = Path(__file__).resolve().parents[1] / "assets" / "indenter_rigid_coupled_base"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--source-ply", type=Path, default=None)
    parser.add_argument("--output-ply", type=Path, default=None)
    parser.add_argument("--output-metadata", type=Path, default=None)
    parser.add_argument("--opacity-threshold", type=float, default=None)
    parser.add_argument("--max-gaussians", type=int, default=None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--axis-transform", choices=tuple(AXIS_TRANSFORMS.keys()), default=None)
    parser.add_argument("--align-ground-z", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument(
        "--transfer-mode",
        choices=("final-position", "indenter-delta"),
        default="final-position",
        help=(
            "final-position writes selected splats to the final MPM surface positions. "
            "indenter-delta applies only final-initial particle displacement to the source splat centers."
        ),
    )
    parser.add_argument("--match-tolerance", type=float, default=1.0e-5)
    parser.add_argument(
        "--max-displacement",
        type=float,
        default=0.25,
        help="Reject transfers with any selected-splat displacement above this aligned/source-unit magnitude.",
    )
    return parser.parse_args()


def load_metadata(run_dir: Path) -> dict:
    metadata_path = run_dir / "ground_plane_metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Missing run metadata: {metadata_path}")
    with metadata_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def transformed_centers_and_indices(
    *,
    vertex: np.ndarray,
    opacity_threshold: float,
    max_gaussians: int,
    seed: int,
    axis_transform: str,
    align_ground_z: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    raw_centers = read_fields(vertex, ["x", "y", "z"])
    raw_opacity = read_fields(vertex, ["opacity"])
    opacities = sigmoid(raw_opacity)
    opacity_keep = opacities[:, 0] >= opacity_threshold
    retained_raw_indices = np.nonzero(opacity_keep)[0]

    retained_centers = raw_centers[opacity_keep]
    retained_opacities = opacities[opacity_keep]
    selected_local = choose_indices(retained_centers.shape[0], max_gaussians, retained_opacities, seed)
    selected_raw_indices = retained_raw_indices[selected_local]
    centers = retained_centers[selected_local]

    axis = AXIS_TRANSFORMS[axis_transform]
    transform = axis.copy()
    centers = centers @ axis.T
    if align_ground_z:
        ground_normal = estimate_plane_normal_ransac(centers, seed=seed)
        ground_alignment = rotation_between_vectors(ground_normal, np.array([0.0, 0.0, 1.0]))
        centers = centers @ ground_alignment.T
        transform = ground_alignment @ transform

    return centers.astype(np.float32), selected_raw_indices, transform.astype(np.float32)


def surface_selection(metadata: dict, centers: np.ndarray) -> np.ndarray:
    z_min = float(metadata["z_min"])
    z_max = float(metadata["z_max"])
    keep = (centers[:, 2] >= z_min) & (centers[:, 2] <= z_max)
    box_size = float(metadata.get("box_size", 0.0))
    box_center_xy = metadata.get("box_center_xy")
    if box_size > 0.0:
        if box_center_xy is None:
            zband = centers[keep]
            if zband.shape[0] == 0:
                raise ValueError("No centers remain after z-band selection")
            box_center = zband[:, :2].mean(axis=0)
        else:
            box_center = np.asarray(box_center_xy, dtype=np.float32)
        keep &= np.all(np.abs(centers[:, :2] - box_center[None, :]) <= box_size * 0.5, axis=1)
    return keep


def write_metadata(path: Path, metadata: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


def main() -> None:
    args = parse_args()
    run_dir = args.run_dir
    metadata = load_metadata(run_dir)

    source_ply = args.source_ply or Path(metadata.get("source_ply", DEFAULT_PLY))
    output_ply = args.output_ply or run_dir / "terrain_deformed_center_only.ply"
    output_metadata = args.output_metadata or run_dir / "terrain_deformed_center_only_metadata.json"

    opacity_threshold = float(args.opacity_threshold if args.opacity_threshold is not None else metadata.get("opacity_threshold", 0.02))
    max_gaussians = int(args.max_gaussians if args.max_gaussians is not None else metadata.get("max_gaussians", 0))
    axis_transform = args.axis_transform or metadata.get("axis_transform", "opencv-to-zup")
    align_ground_z = bool(args.align_ground_z if args.align_ground_z is not None else metadata.get("align_ground_z", True))

    ply = PlyData.read(source_ply)
    vertex = ply["vertex"].data
    centers_aligned, selected_raw_indices, transform = transformed_centers_and_indices(
        vertex=vertex,
        opacity_threshold=opacity_threshold,
        max_gaussians=max_gaussians,
        seed=args.seed,
        axis_transform=axis_transform,
        align_ground_z=align_ground_z,
    )

    surface_keep = surface_selection(metadata, centers_aligned)
    surface_centers = centers_aligned[surface_keep]
    surface_raw_indices = selected_raw_indices[surface_keep]
    surface_count = int(metadata["surface_particle_count"])
    if surface_centers.shape[0] != surface_count:
        raise ValueError(
            f"Surface selection count mismatch: selected {surface_centers.shape[0]}, metadata has {surface_count}"
        )

    initial_particles = read_particle_ply(run_dir / "particles_initial_mpm.ply")
    final_particles = read_particle_ply(run_dir / "particles_final_mpm.ply")
    initial_surface = initial_particles[:surface_count]
    final_surface = final_particles[:surface_count]
    displacement_aligned = final_surface - initial_surface

    mismatch = np.linalg.norm(surface_centers - initial_surface, axis=1)
    max_mismatch = float(mismatch.max()) if mismatch.size else 0.0
    mean_mismatch = float(mismatch.mean()) if mismatch.size else 0.0
    if args.transfer_mode == "indenter-delta" and max_mismatch > args.match_tolerance:
        raise ValueError(
            "Surface splat centers do not match initial surface particles: "
            f"max mismatch {max_mismatch:.8f} > tolerance {args.match_tolerance:.8f}"
        )

    displacement_norm = np.linalg.norm(displacement_aligned, axis=1)
    max_displacement = float(displacement_norm.max()) if displacement_norm.size else 0.0
    if args.max_displacement > 0.0 and max_displacement > args.max_displacement:
        raise ValueError(
            f"Max transfer displacement {max_displacement:.6f} exceeds --max-displacement {args.max_displacement}"
        )

    if args.transfer_mode == "final-position":
        deformed_aligned = final_surface
    else:
        deformed_aligned = surface_centers + displacement_aligned
    deformed_source = deformed_aligned @ transform

    out_vertex = vertex.copy()
    out_vertex["x"][surface_raw_indices] = deformed_source[:, 0].astype(out_vertex["x"].dtype)
    out_vertex["y"][surface_raw_indices] = deformed_source[:, 1].astype(out_vertex["y"].dtype)
    out_vertex["z"][surface_raw_indices] = deformed_source[:, 2].astype(out_vertex["z"].dtype)

    output_ply.parent.mkdir(parents=True, exist_ok=True)
    PlyData([PlyElement.describe(out_vertex, "vertex")], text=ply.text).write(output_ply)

    transfer_metadata = {
        "method": "center_only_surface_particle_transfer",
        "physgaussian_stage": "center_update_before_covariance_update",
        "transfer_mode": args.transfer_mode,
        "source_ply": str(source_ply),
        "output_ply": str(output_ply),
        "run_dir": str(run_dir),
        "axis_transform": axis_transform,
        "align_ground_z": align_ground_z,
        "opacity_threshold": opacity_threshold,
        "max_gaussians": max_gaussians,
        "selected_splat_count": int(surface_raw_indices.shape[0]),
        "source_vertex_count": int(vertex.shape[0]),
        "surface_particle_count": surface_count,
        "match_tolerance": float(args.match_tolerance),
        "surface_match_max": max_mismatch,
        "surface_match_mean": mean_mismatch,
        "initial_relaxation_min": (initial_surface - surface_centers).min(axis=0).astype(float).tolist(),
        "initial_relaxation_max": (initial_surface - surface_centers).max(axis=0).astype(float).tolist(),
        "initial_relaxation_mean": (initial_surface - surface_centers).mean(axis=0).astype(float).tolist(),
        "displacement_min": displacement_aligned.min(axis=0).astype(float).tolist(),
        "displacement_max": displacement_aligned.max(axis=0).astype(float).tolist(),
        "displacement_mean": displacement_aligned.mean(axis=0).astype(float).tolist(),
        "displacement_norm_max": max_displacement,
        "displacement_norm_mean": float(displacement_norm.mean()) if displacement_norm.size else 0.0,
        "covariance_update": "not_applied",
        "unchanged_attributes": "all non-position PLY vertex properties preserved",
    }
    write_metadata(output_metadata, transfer_metadata)

    print(f"source vertices: {vertex.shape[0]}")
    print(f"updated splats: {surface_raw_indices.shape[0]}")
    print(f"surface match max: {max_mismatch:.8f}")
    print(f"transfer mode: {args.transfer_mode}")
    print(f"displacement norm max: {max_displacement:.6f}")
    print(f"output ply: {output_ply}")
    print(f"metadata: {output_metadata}")


if __name__ == "__main__":
    main()

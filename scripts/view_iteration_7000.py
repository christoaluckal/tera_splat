#!/usr/bin/env python3
"""Live Viser viewer for the EDGS iteration-7000 Gaussian checkpoint.

The current prototype assumption is simple: every Gaussian in the scene is sand.
This viewer is for inspecting the trained splat before patch extraction and
deformation. It decodes standard 3DGS PLY attributes into Viser Gaussian splats.
"""

from __future__ import annotations

import argparse
import dataclasses
import time
from pathlib import Path

import numpy as np
import viser
from plyfile import PlyData


SH_C0 = 0.28209479177387814
DEFAULT_PLY = (
    Path(__file__).resolve().parents[2]
    / "EDGS"
    / "output"
    / "point_cloud"
    / "iteration_7000"
    / "point_cloud.ply"
)


@dataclasses.dataclass(frozen=True)
class GaussianSplatData:
    centers: np.ndarray
    covariances: np.ndarray
    colors: np.ndarray
    opacities: np.ndarray
    bounds_min: np.ndarray
    bounds_max: np.ndarray
    ground_normal: np.ndarray | None = None
    ground_alignment: np.ndarray | None = None


AXIS_TRANSFORMS = {
    "identity": np.eye(3, dtype=np.float32),
    # OpenCV/COLMAP-style axes: x right, y down, z forward.
    # Z-up world axes: x right, y forward, z up.
    "opencv-to-zup": np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, -1.0, 0.0],
        ],
        dtype=np.float32,
    ),
    # OpenCV/COLMAP camera convention to OpenGL/Blender camera convention.
    "opencv-to-opengl": np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 0.0, -1.0],
        ],
        dtype=np.float32,
    ),
}


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def normalize_quaternions(q: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(q, axis=1, keepdims=True)
    return q / np.maximum(norm, 1e-12)


def quaternion_wxyz_to_rotation_matrix(q: np.ndarray) -> np.ndarray:
    """Convert normalized wxyz quaternions to rotation matrices."""

    q = normalize_quaternions(q)
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]

    rot = np.empty((q.shape[0], 3, 3), dtype=np.float32)
    rot[:, 0, 0] = 1.0 - 2.0 * (y * y + z * z)
    rot[:, 0, 1] = 2.0 * (x * y - w * z)
    rot[:, 0, 2] = 2.0 * (x * z + w * y)
    rot[:, 1, 0] = 2.0 * (x * y + w * z)
    rot[:, 1, 1] = 1.0 - 2.0 * (x * x + z * z)
    rot[:, 1, 2] = 2.0 * (y * z - w * x)
    rot[:, 2, 0] = 2.0 * (x * z - w * y)
    rot[:, 2, 1] = 2.0 * (y * z + w * x)
    rot[:, 2, 2] = 1.0 - 2.0 * (x * x + y * y)
    return rot


def make_positive_definite(covariances: np.ndarray, min_eigenvalue: float = 1e-8) -> np.ndarray:
    covariances = 0.5 * (covariances + np.swapaxes(covariances, 1, 2))
    eigvals, eigvecs = np.linalg.eigh(covariances.astype(np.float64))
    eigvals = np.maximum(eigvals, min_eigenvalue)
    fixed = eigvecs @ (eigvals[..., None] * np.swapaxes(eigvecs, 1, 2))
    return fixed.astype(np.float32)


def rotation_between_vectors(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    source = source.astype(np.float64)
    target = target.astype(np.float64)
    source /= max(np.linalg.norm(source), 1e-12)
    target /= max(np.linalg.norm(target), 1e-12)

    cross = np.cross(source, target)
    dot = float(np.clip(np.dot(source, target), -1.0, 1.0))
    cross_norm = float(np.linalg.norm(cross))

    if cross_norm < 1e-10:
        if dot > 0.0:
            return np.eye(3, dtype=np.float32)
        axis = np.array([1.0, 0.0, 0.0])
        if abs(source[0]) > 0.9:
            axis = np.array([0.0, 1.0, 0.0])
        axis = np.cross(source, axis)
        axis /= max(np.linalg.norm(axis), 1e-12)
        cross_matrix = skew(axis)
        return (np.eye(3) + 2.0 * cross_matrix @ cross_matrix).astype(np.float32)

    cross_matrix = skew(cross)
    rotation = np.eye(3) + cross_matrix + cross_matrix @ cross_matrix * ((1.0 - dot) / (cross_norm * cross_norm))
    return rotation.astype(np.float32)


def skew(vector: np.ndarray) -> np.ndarray:
    x, y, z = vector
    return np.array(
        [
            [0.0, -z, y],
            [z, 0.0, -x],
            [-y, x, 0.0],
        ],
        dtype=np.float64,
    )


def estimate_plane_normal_ransac(
    points: np.ndarray,
    *,
    seed: int,
    max_points: int = 50000,
    iterations: int = 384,
    threshold_fraction: float = 0.01,
) -> np.ndarray:
    if points.shape[0] < 3:
        raise ValueError("Need at least 3 points to estimate a ground plane")

    rng = np.random.default_rng(seed)
    if points.shape[0] > max_points:
        sample_ids = rng.choice(points.shape[0], size=max_points, replace=False)
        sample = points[sample_ids].astype(np.float64)
    else:
        sample = points.astype(np.float64)

    scene_scale = float(np.linalg.norm(sample.max(axis=0) - sample.min(axis=0)))
    threshold = max(scene_scale * threshold_fraction, 1e-5)
    best_inliers: np.ndarray | None = None
    best_count = -1

    for _ in range(iterations):
        ids = rng.choice(sample.shape[0], size=3, replace=False)
        p0, p1, p2 = sample[ids]
        normal = np.cross(p1 - p0, p2 - p0)
        norm = np.linalg.norm(normal)
        if norm < 1e-10:
            continue
        normal /= norm
        distances = np.abs((sample - p0) @ normal)
        inliers = distances < threshold
        count = int(inliers.sum())
        if count > best_count:
            best_count = count
            best_inliers = inliers

    if best_inliers is None or best_count < 3:
        raise RuntimeError("Could not estimate a dominant plane")

    inlier_points = sample[best_inliers]
    centered = inlier_points - inlier_points.mean(axis=0, keepdims=True)
    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    normal = vh[-1]
    normal /= max(np.linalg.norm(normal), 1e-12)
    if normal[2] < 0.0:
        normal = -normal
    return normal.astype(np.float32)


def read_fields(vertex: np.ndarray, names: list[str]) -> np.ndarray:
    return np.stack([vertex[name] for name in names], axis=1).astype(np.float32)


def choose_indices(
    count: int,
    max_gaussians: int,
    opacity: np.ndarray,
    seed: int,
) -> np.ndarray:
    if max_gaussians <= 0 or count <= max_gaussians:
        return np.arange(count)

    rng = np.random.default_rng(seed)
    weights = opacity.reshape(-1).astype(np.float64)
    weights = np.maximum(weights, 1e-6)
    weights /= weights.sum()
    return np.sort(rng.choice(count, size=max_gaussians, replace=False, p=weights))


def load_3dgs_ply(
    path: Path,
    *,
    opacity_threshold: float,
    max_gaussians: int,
    seed: int,
    scale_multiplier: float,
    axis_transform: str,
    align_ground_z: bool,
) -> GaussianSplatData:
    ply = PlyData.read(path)
    vertex = ply["vertex"].data

    centers = read_fields(vertex, ["x", "y", "z"])
    f_dc = read_fields(vertex, ["f_dc_0", "f_dc_1", "f_dc_2"])
    raw_opacity = read_fields(vertex, ["opacity"])
    raw_scales = read_fields(vertex, ["scale_0", "scale_1", "scale_2"])
    rotations = read_fields(vertex, ["rot_0", "rot_1", "rot_2", "rot_3"])

    colors = np.clip(0.5 + SH_C0 * f_dc, 0.0, 1.0)
    opacities = sigmoid(raw_opacity)
    keep = opacities[:, 0] >= opacity_threshold

    centers = centers[keep]
    colors = colors[keep]
    opacities = opacities[keep]
    raw_scales = raw_scales[keep]
    rotations = rotations[keep]

    selected = choose_indices(centers.shape[0], max_gaussians, opacities, seed)
    centers = centers[selected]
    colors = colors[selected]
    opacities = opacities[selected]
    raw_scales = raw_scales[selected]
    rotations = rotations[selected]

    scales = np.exp(raw_scales) * scale_multiplier
    rot = quaternion_wxyz_to_rotation_matrix(rotations)
    covariances = rot @ np.einsum("ni,ij->nij", scales * scales, np.eye(3, dtype=np.float32)) @ np.swapaxes(rot, 1, 2)
    axis = AXIS_TRANSFORMS[axis_transform]
    centers = centers @ axis.T
    covariances = axis @ covariances @ axis.T

    ground_normal = None
    ground_alignment = None
    if align_ground_z:
        ground_normal = estimate_plane_normal_ransac(centers, seed=seed)
        ground_alignment = rotation_between_vectors(ground_normal, np.array([0.0, 0.0, 1.0]))
        centers = centers @ ground_alignment.T
        covariances = ground_alignment @ covariances @ ground_alignment.T

    covariances = make_positive_definite(covariances)

    return GaussianSplatData(
        centers=centers.astype(np.float32),
        covariances=covariances.astype(np.float32),
        colors=colors.astype(np.float32),
        opacities=opacities.astype(np.float32),
        bounds_min=centers.min(axis=0),
        bounds_max=centers.max(axis=0),
        ground_normal=ground_normal,
        ground_alignment=ground_alignment,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ply", type=Path, default=DEFAULT_PLY)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--opacity-threshold", type=float, default=0.02)
    parser.add_argument(
        "--max-gaussians",
        type=int,
        default=300_000,
        help="Maximum splats sent to Viser. Use 0 to send all retained splats.",
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--scale-multiplier",
        type=float,
        default=1.0,
        help="Debug multiplier for rendered covariance scale.",
    )
    parser.add_argument(
        "--axis-transform",
        choices=tuple(AXIS_TRANSFORMS.keys()),
        default="opencv-to-zup",
        help="Rigid axis conversion applied to centers and covariances.",
    )
    parser.add_argument(
        "--align-ground-z",
        action="store_true",
        help="Fit the dominant plane and rotate its normal onto +Z.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load and report stats without starting the Viser server.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = load_3dgs_ply(
        args.ply,
        opacity_threshold=args.opacity_threshold,
        max_gaussians=args.max_gaussians,
        seed=args.seed,
        scale_multiplier=args.scale_multiplier,
        axis_transform=args.axis_transform,
        align_ground_z=args.align_ground_z,
    )

    print(f"PLY: {args.ply}")
    print("Assumption: all retained Gaussians are sand.")
    print(f"Axis transform: {args.axis_transform}")
    print(f"Ground alignment: {args.align_ground_z}")
    if data.ground_normal is not None:
        print(f"Estimated ground normal before alignment: {data.ground_normal.tolist()}")
        print(f"Ground alignment matrix: {data.ground_alignment.tolist()}")
    print(f"Loaded splats: {data.centers.shape[0]:,}")
    print(f"Bounds min: {data.bounds_min.tolist()}")
    print(f"Bounds max: {data.bounds_max.tolist()}")

    if args.dry_run:
        return

    server = viser.ViserServer(host=args.host, port=args.port)
    server.scene.world_axes.visible = True
    center = (data.bounds_min + data.bounds_max) / 2.0
    span = float(np.max(data.bounds_max - data.bounds_min))
    server.scene.add_grid(
        "/grid",
        width=span,
        height=span,
        plane="xy",
        position=(float(center[0]), float(center[1]), float(data.bounds_min[2])),
    )
    server.scene._add_gaussian_splats(
        "/edgs_iteration_7000_all_sand",
        centers=data.centers,
        covariances=data.covariances,
        rgbs=data.colors,
        opacities=data.opacities,
    )
    print(f"Open http://localhost:{args.port}")

    while True:
        time.sleep(1.0)


if __name__ == "__main__":
    main()

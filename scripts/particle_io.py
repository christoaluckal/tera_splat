"""Shared particle extraction and PLY I/O for terrain MPM tests."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import numpy as np

from view_iteration_7000 import load_3dgs_ply


def load_material_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_to_mpm_domain(
    points: np.ndarray,
    *,
    grid_lim: float,
    padding: float,
) -> tuple[np.ndarray, dict]:
    bounds_min = points.min(axis=0)
    bounds_max = points.max(axis=0)
    center = (bounds_min + bounds_max) / 2.0
    span = float(np.max(bounds_max - bounds_min))
    usable = grid_lim * (1.0 - 2.0 * padding)
    scale = usable / span
    offset = np.array([grid_lim * 0.5, grid_lim * 0.5, grid_lim * padding], dtype=np.float32)
    normalized = (points - center) * scale + offset
    normalized[:, 2] -= normalized[:, 2].min() - grid_lim * padding
    metadata = {
        "source_bounds_min": bounds_min.tolist(),
        "source_bounds_max": bounds_max.tolist(),
        "source_center": center.tolist(),
        "source_span": span,
        "grid_lim": grid_lim,
        "padding": padding,
        "scale_to_mpm": scale,
        "offset_after_centering": offset.tolist(),
    }
    return normalized.astype(np.float32), metadata


def filter_high_z_outliers(points: np.ndarray, stddev_limit: float) -> tuple[np.ndarray, dict | None]:
    if stddev_limit <= 0.0:
        return points, None

    z_values = points[:, 2]
    z_mean = float(z_values.mean())
    z_std = float(z_values.std())
    z_max = z_mean + stddev_limit * z_std
    keep = z_values <= z_max
    metadata = {
        "stddev_limit": stddev_limit,
        "z_mean": z_mean,
        "z_std": z_std,
        "z_max": z_max,
        "input_count": int(points.shape[0]),
        "kept_count": int(np.count_nonzero(keep)),
        "removed_count": int(points.shape[0] - np.count_nonzero(keep)),
    }
    return points[keep], metadata


def filter_center_radius(points: np.ndarray, radius: float) -> tuple[np.ndarray, dict | None]:
    if radius <= 0.0:
        return points, None

    center_xy = points[:, :2].mean(axis=0)
    distances = np.linalg.norm(points[:, :2] - center_xy, axis=1)
    keep = distances <= radius
    metadata = {
        "radius": radius,
        "center_xy": center_xy.tolist(),
        "input_count": int(points.shape[0]),
        "kept_count": int(np.count_nonzero(keep)),
        "removed_count": int(points.shape[0] - np.count_nonzero(keep)),
        "max_kept_radius": float(distances[keep].max()) if np.any(keep) else 0.0,
    }
    return points[keep], metadata


def filter_below_local_surface(
    points: np.ndarray,
    *,
    k_neighbors: int,
    top_quantile: float,
    tolerance_mpm: float,
) -> tuple[np.ndarray, dict | None]:
    if k_neighbors <= 1 or tolerance_mpm < 0.0:
        return points, None

    from scipy.spatial import cKDTree

    k = min(k_neighbors, points.shape[0])
    tree = cKDTree(points[:, :2])
    _, indices = tree.query(points[:, :2], k=k)
    if k == 1:
        indices = indices[:, None]
    local_top = np.quantile(points[indices, 2], top_quantile, axis=1)
    keep = points[:, 2] >= local_top - tolerance_mpm
    metadata = {
        "k_neighbors": int(k),
        "top_quantile": float(top_quantile),
        "tolerance_mpm": float(tolerance_mpm),
        "input_count": int(points.shape[0]),
        "kept_count": int(np.count_nonzero(keep)),
        "removed_count": int(points.shape[0] - np.count_nonzero(keep)),
        "max_removed_depth_below_local_top": float(np.max(local_top[~keep] - points[~keep, 2])) if np.any(~keep) else 0.0,
    }
    return points[keep], metadata


def add_subsurface_particles(
    surface_points: np.ndarray,
    *,
    spacing_mpm: float,
    max_depth_mpm: float,
    layer_spacing_mpm: float,
    layer_depths_mpm: np.ndarray | None,
    xy_jitter_mpm: float,
    fill_radius_mpm: float,
    max_surface_distance_mpm: float,
    surface_height_method: str,
    include_surface_cap: bool,
    seed: int,
) -> tuple[np.ndarray, dict | None]:
    if spacing_mpm <= 0.0 or layer_spacing_mpm <= 0.0:
        return surface_points, None

    from scipy.spatial import cKDTree
    from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator

    rng = np.random.default_rng(seed)
    xy_center = surface_points[:, :2].mean(axis=0)
    if fill_radius_mpm > 0.0:
        xs = np.arange(xy_center[0] - fill_radius_mpm, xy_center[0] + fill_radius_mpm + spacing_mpm, spacing_mpm)
        ys = np.arange(xy_center[1] - fill_radius_mpm, xy_center[1] + fill_radius_mpm + spacing_mpm, spacing_mpm)
    else:
        xy_min = surface_points[:, :2].min(axis=0)
        xy_max = surface_points[:, :2].max(axis=0)
        xs = np.arange(xy_min[0], xy_max[0] + spacing_mpm, spacing_mpm)
        ys = np.arange(xy_min[1], xy_max[1] + spacing_mpm, spacing_mpm)

    grid_x, grid_y = np.meshgrid(xs, ys, indexing="xy")
    grid_xy = np.stack([grid_x.ravel(), grid_y.ravel()], axis=1).astype(np.float32)
    if fill_radius_mpm > 0.0:
        distances_from_center = np.linalg.norm(grid_xy - xy_center, axis=1)
        grid_xy = grid_xy[distances_from_center <= fill_radius_mpm]

    tree = cKDTree(surface_points[:, :2])
    nearest_distance, nearest = tree.query(grid_xy, k=1)
    if max_surface_distance_mpm > 0.0:
        valid = nearest_distance <= max_surface_distance_mpm
        grid_xy = grid_xy[valid]
        nearest = nearest[valid]
        nearest_distance = nearest_distance[valid]
    if grid_xy.shape[0] == 0:
        raise ValueError("No subsurface grid points remain after surface-distance masking")

    if surface_height_method == "linear":
        linear = LinearNDInterpolator(surface_points[:, :2], surface_points[:, 2])
        nearest_interp = NearestNDInterpolator(surface_points[:, :2], surface_points[:, 2])

        def sample_surface_z(query_xy: np.ndarray) -> np.ndarray:
            sampled_z = linear(query_xy)
            missing = ~np.isfinite(sampled_z)
            if np.any(missing):
                sampled_z[missing] = nearest_interp(query_xy[missing])
            return sampled_z.astype(np.float32)

        surface_z = sample_surface_z(grid_xy)
    elif surface_height_method == "nearest":
        def sample_surface_z(query_xy: np.ndarray) -> np.ndarray:
            _, sampled_nearest = tree.query(query_xy, k=1)
            return surface_points[sampled_nearest, 2].astype(np.float32)

        surface_z = surface_points[nearest, 2].astype(np.float32)
    else:
        raise ValueError("--subsurface-surface-height-method must be 'linear' or 'nearest'")

    cap_points = np.empty((grid_xy.shape[0], 3), dtype=np.float32)
    cap_points[:, :2] = grid_xy
    cap_points[:, 2] = surface_z
    if not include_surface_cap:
        cap_points = np.empty((0, 3), dtype=np.float32)
        sample_visible_surface_z = sample_surface_z
    else:
        visible_linear = LinearNDInterpolator(cap_points[:, :2], cap_points[:, 2])
        visible_nearest = NearestNDInterpolator(cap_points[:, :2], cap_points[:, 2])

        def sample_visible_surface_z(query_xy: np.ndarray) -> np.ndarray:
            sampled_z = visible_linear(query_xy)
            missing = ~np.isfinite(sampled_z)
            if np.any(missing):
                sampled_z[missing] = visible_nearest(query_xy[missing])
            return sampled_z.astype(np.float32)

    if layer_depths_mpm is None:
        layer_depths = np.arange(layer_spacing_mpm, max_depth_mpm + layer_spacing_mpm * 0.5, layer_spacing_mpm)
    else:
        layer_depths = layer_depths_mpm[(layer_depths_mpm > 0.0) & (layer_depths_mpm <= max_depth_mpm)]
    if layer_depths.size == 0:
        return surface_points, None
    support_layers = []
    for layer_index, depth in enumerate(layer_depths):
        layer = np.empty((grid_xy.shape[0], 3), dtype=np.float32)
        layer[:, :2] = grid_xy
        if layer.shape[0] > 0:
            layer_shift = rng.uniform(-spacing_mpm * 0.5, spacing_mpm * 0.5, size=(1, 2))
            layer[:, :2] += layer_shift
        if xy_jitter_mpm > 0.0:
            layer[:, :2] += rng.uniform(-xy_jitter_mpm, xy_jitter_mpm, size=(layer.shape[0], 2))
        if fill_radius_mpm > 0.0:
            keep_radius = np.linalg.norm(layer[:, :2] - xy_center, axis=1) <= fill_radius_mpm
            layer = layer[keep_radius]
        if max_surface_distance_mpm > 0.0 and layer.shape[0] > 0:
            layer_nearest_distance, _ = tree.query(layer[:, :2], k=1)
            layer = layer[layer_nearest_distance <= max_surface_distance_mpm]
        if layer.shape[0] == 0:
            support_layers.append(layer)
            continue
        layer_surface_z = np.minimum(
            sample_surface_z(layer[:, :2]),
            sample_visible_surface_z(layer[:, :2]),
        )
        layer[:, 2] = layer_surface_z - float(depth)
        min_allowed = layer_surface_z - max_depth_mpm - 1e-6
        max_allowed = layer_surface_z + 1e-6
        keep = (layer[:, 2] >= min_allowed) & (layer[:, 2] <= max_allowed)
        layer = layer[keep]
        support_layers.append(layer)
    support_points = np.concatenate(support_layers, axis=0).astype(np.float32)
    if include_surface_cap:
        combined_surface = cap_points
    else:
        combined_surface = surface_points
    combined = np.concatenate([combined_surface, support_points], axis=0)
    recommended_ground_z = float(support_points[:, 2].min() - spacing_mpm * 0.5)

    metadata = {
        "fill_strategy": "regular_grid_subsurface_layers",
        "surface_height_method": surface_height_method,
        "spacing_mpm": float(spacing_mpm),
        "max_depth_mpm": float(max_depth_mpm),
        "layer_spacing_mpm": float(layer_spacing_mpm),
        "layer_depths_mpm": layer_depths.astype(float).tolist(),
        "layer_count": int(layer_depths.shape[0]),
        "xy_jitter_mpm": float(xy_jitter_mpm),
        "grid_xy_count": int(grid_xy.shape[0]),
        "grid_xy_center": xy_center.tolist(),
        "fill_radius_mpm": float(fill_radius_mpm),
        "max_surface_distance_mpm": float(max_surface_distance_mpm),
        "nearest_distance_min": float(nearest_distance.min()) if nearest_distance.size else 0.0,
        "nearest_distance_max": float(nearest_distance.max()) if nearest_distance.size else 0.0,
        "nearest_distance_mean": float(nearest_distance.mean()) if nearest_distance.size else 0.0,
        "splat_surface_particle_count": int(surface_points.shape[0]),
        "surface_cap_particle_count": int(cap_points.shape[0]),
        "surface_particle_count": int(combined_surface.shape[0]),
        "surface_entity_source": "interpolated_cap" if include_surface_cap else "raw_splats",
        "subsurface_particle_count": int(support_points.shape[0]),
        "raw_splat_z_min": float(surface_points[:, 2].min()),
        "raw_splat_z_max": float(surface_points[:, 2].max()),
        "surface_cap_z_min": float(cap_points[:, 2].min()) if cap_points.size else None,
        "surface_cap_z_max": float(cap_points[:, 2].max()) if cap_points.size else None,
        "subsurface_z_min": float(support_points[:, 2].min()),
        "subsurface_z_max": float(support_points[:, 2].max()),
        "recommended_ground_z": recommended_ground_z,
    }
    return combined.astype(np.float32), metadata


def resolve_particle_size_mpm(args: Namespace, config: dict) -> float:
    if hasattr(args, "particle_size") and args.particle_size is not None:
        return float(args.particle_size)
    n_grid = int(args.n_grid if getattr(args, "n_grid", None) is not None else config.get("n_grid", 64))
    return float(config.get("particle_size", 0.01 * 64.0 / n_grid))


def parse_float_list(value: str | None) -> list[float] | None:
    if value is None or value == "":
        return None
    return [float(part) for part in value.split(",") if part.strip()]


def build_particles(args: Namespace, config: dict) -> tuple[np.ndarray, dict]:
    grid_lim = float(args.grid_lim if args.grid_lim is not None else config.get("grid_lim", 2.0))
    ground_quantile = float(getattr(args, "ground_quantile", 0.0))
    trim_quantile = float(getattr(args, "trim_quantile", 0.0))
    subsurface_depth = float(getattr(args, "subsurface_depth", 0.2))
    subsurface_spacing_mpm = getattr(args, "subsurface_spacing_mpm", None)
    subsurface_xy_jitter = float(getattr(args, "subsurface_xy_jitter", 0.45))
    subsurface_layer_depths = parse_float_list(getattr(args, "subsurface_layer_depths", None))
    subsurface_surface_height_method = getattr(args, "subsurface_surface_height_method", "linear")
    subsurface_max_surface_distance = float(getattr(args, "subsurface_max_surface_distance", 2.0))
    include_surface_cap = bool(getattr(args, "surface_cap", True))
    ground_offset_below_subsurface = float(getattr(args, "ground_offset_below_subsurface", 0.01))
    ground_subsurface_quantile = float(getattr(args, "ground_subsurface_quantile", 0.01))
    surface_filter_neighbors = int(getattr(args, "surface_filter_neighbors", 0))
    surface_filter_quantile = float(getattr(args, "surface_filter_quantile", 0.9))
    surface_filter_tolerance = float(getattr(args, "surface_filter_tolerance", 0.03))
    z_stddev_filter = float(getattr(args, "z_stddev_filter", 1.0))
    center_radius = float(getattr(args, "center_radius", 0.0))
    data = load_3dgs_ply(
        args.ply,
        opacity_threshold=args.opacity_threshold,
        max_gaussians=args.max_particles,
        seed=args.seed,
        scale_multiplier=1.0,
        axis_transform=args.axis_transform,
        align_ground_z=True,
    )
    centers = data.centers
    trim_metadata = None
    if trim_quantile > 0.0:
        if trim_quantile >= 0.5:
            raise ValueError("--trim-quantile must be less than 0.5")
        low = np.quantile(centers, trim_quantile, axis=0)
        high = np.quantile(centers, 1.0 - trim_quantile, axis=0)
        keep = np.all((centers >= low) & (centers <= high), axis=1)
        trim_metadata = {
            "trim_quantile": trim_quantile,
            "bounds_min": low.tolist(),
            "bounds_max": high.tolist(),
            "input_count": int(centers.shape[0]),
            "kept_count": int(np.count_nonzero(keep)),
            "removed_count": int(centers.shape[0] - np.count_nonzero(keep)),
        }
        centers = centers[keep]

    centers, z_filter_metadata = filter_high_z_outliers(centers, z_stddev_filter)
    if centers.shape[0] == 0:
        raise ValueError("No particles remain after high-Z filtering")
    centers, radius_filter_metadata = filter_center_radius(centers, center_radius)
    if centers.shape[0] == 0:
        raise ValueError("No particles remain after center-radius filtering")

    surface_points, transform_metadata = normalize_to_mpm_domain(
        centers,
        grid_lim=grid_lim,
        padding=args.padding,
    )
    surface_filter_tolerance_mpm = surface_filter_tolerance * float(transform_metadata["scale_to_mpm"])
    surface_points, surface_filter_metadata = filter_below_local_surface(
        surface_points,
        k_neighbors=surface_filter_neighbors,
        top_quantile=surface_filter_quantile,
        tolerance_mpm=surface_filter_tolerance_mpm,
    )
    if surface_points.shape[0] == 0:
        raise ValueError("No particles remain after local surface filtering")
    if surface_filter_metadata is not None:
        surface_filter_metadata["tolerance_source_units"] = surface_filter_tolerance
    if subsurface_spacing_mpm is None:
        spacing_mpm = subsurface_depth * float(transform_metadata["scale_to_mpm"])
        spacing_source_units = subsurface_depth
    else:
        spacing_mpm = float(subsurface_spacing_mpm)
        spacing_source_units = spacing_mpm / float(transform_metadata["scale_to_mpm"])
    max_depth_mpm = subsurface_depth * float(transform_metadata["scale_to_mpm"])
    layer_spacing_mpm = spacing_mpm
    layer_depths_mpm = None
    if subsurface_layer_depths is not None:
        layer_depths_mpm = np.asarray(
            [depth * float(transform_metadata["scale_to_mpm"]) for depth in subsurface_layer_depths],
            dtype=np.float32,
        )
    xy_jitter_mpm = max(spacing_mpm * subsurface_xy_jitter, 0.0)
    fill_radius_mpm = center_radius * float(transform_metadata["scale_to_mpm"]) if center_radius > 0.0 else 0.0
    max_surface_distance_mpm = spacing_mpm * subsurface_max_surface_distance
    points, subsurface_metadata = add_subsurface_particles(
        surface_points,
        spacing_mpm=spacing_mpm,
        max_depth_mpm=max_depth_mpm,
        layer_spacing_mpm=layer_spacing_mpm,
        layer_depths_mpm=layer_depths_mpm,
        xy_jitter_mpm=xy_jitter_mpm,
        fill_radius_mpm=fill_radius_mpm,
        max_surface_distance_mpm=max_surface_distance_mpm,
        surface_height_method=subsurface_surface_height_method,
        include_surface_cap=include_surface_cap,
        seed=args.seed,
    )
    if subsurface_metadata is not None:
        subsurface_metadata["spacing_source_units"] = float(spacing_source_units)
        subsurface_metadata["max_depth_source_units"] = float(subsurface_depth)
        subsurface_metadata["layer_depths_source_units"] = (
            subsurface_layer_depths
            if subsurface_layer_depths is not None
            else [float(depth / float(transform_metadata["scale_to_mpm"])) for depth in subsurface_metadata["layer_depths_mpm"]]
        )
        subsurface_metadata["particle_size_mpm"] = resolve_particle_size_mpm(args, config)
        subsurface_metadata["xy_jitter_fraction_of_spacing"] = subsurface_xy_jitter
    if subsurface_metadata is not None:
        surface_count = int(subsurface_metadata["surface_particle_count"])
        combined_surface_points = points[:surface_count]
        subsurface_points = points[surface_count:]
        ground_z = float(
            np.quantile(subsurface_points[:, 2], ground_subsurface_quantile)
            - ground_offset_below_subsurface * float(transform_metadata["scale_to_mpm"])
        )
        ground_source = "subsurface_quantile_minus_offset"
        surface_keep = combined_surface_points[:, 2] > ground_z
        subsurface_keep = subsurface_points[:, 2] > ground_z
        ground_filter_metadata = {
            "ground_z": ground_z,
            "surface_input_count": int(combined_surface_points.shape[0]),
            "surface_kept_count": int(np.count_nonzero(surface_keep)),
            "surface_removed_count": int(combined_surface_points.shape[0] - np.count_nonzero(surface_keep)),
            "subsurface_input_count": int(subsurface_points.shape[0]),
            "subsurface_kept_count": int(np.count_nonzero(subsurface_keep)),
            "subsurface_removed_count": int(subsurface_points.shape[0] - np.count_nonzero(subsurface_keep)),
        }
        surface_points = combined_surface_points[surface_keep]
        subsurface_points = subsurface_points[subsurface_keep]
        points = np.concatenate([surface_points, subsurface_points], axis=0).astype(np.float32)
        subsurface_metadata["surface_particle_count"] = int(surface_points.shape[0])
        subsurface_metadata["subsurface_particle_count"] = int(subsurface_points.shape[0])
        subsurface_metadata["surface_z_min"] = float(surface_points[:, 2].min()) if surface_points.size else None
        subsurface_metadata["surface_z_max"] = float(surface_points[:, 2].max()) if surface_points.size else None
        subsurface_metadata["subsurface_z_min"] = float(subsurface_points[:, 2].min()) if subsurface_points.size else None
        subsurface_metadata["subsurface_z_max"] = float(subsurface_points[:, 2].max()) if subsurface_points.size else None
    else:
        ground_z = float(np.quantile(surface_points[:, 2], ground_quantile))
        ground_source = "surface_height_quantile"
        ground_filter_metadata = None
    metadata = {
        "ply": str(args.ply),
        "particle_count": int(points.shape[0]),
        "surface_particle_count": int(surface_points.shape[0]),
        "entity_counts": {
            "surface": int(surface_points.shape[0]),
            "subsurface": int((subsurface_metadata or {}).get("subsurface_particle_count", 0)),
            "ground_plane": 1,
        },
        "axis_transform": args.axis_transform,
        "align_ground_z": True,
        "ground_normal_before_alignment": None
        if data.ground_normal is None
        else data.ground_normal.tolist(),
        "ground_alignment_matrix": None
        if data.ground_alignment is None
        else data.ground_alignment.tolist(),
        "outlier_trim": trim_metadata,
        "high_z_filter": z_filter_metadata,
        "center_radius_filter": radius_filter_metadata,
        "local_surface_filter": surface_filter_metadata,
        "ground_filter": ground_filter_metadata,
        "subsurface_fill": subsurface_metadata,
        "mpm_transform": transform_metadata,
        "ground_plane_mpm": {
            "point": [0.0, 0.0, ground_z],
            "normal": [0.0, 0.0, 1.0],
            "surface": "sticky",
            "friction": 0.0,
            "height_quantile": ground_quantile,
            "height_source": ground_source,
            "subsurface_quantile": ground_subsurface_quantile,
            "offset_below_subsurface_source_units": ground_offset_below_subsurface,
        },
    }
    return points, metadata


def write_particle_ply(points: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        header = f"""ply
format binary_little_endian 1.0
element vertex {points.shape[0]}
property float x
property float y
property float z
end_header
"""
        f.write(header.encode("ascii"))
        f.write(points.astype(np.float32).tobytes())


def read_particle_ply(path: Path) -> np.ndarray:
    from plyfile import PlyData

    vertex = PlyData.read(path)["vertex"].data
    return np.stack([vertex["x"], vertex["y"], vertex["z"]], axis=1).astype(np.float32)


def write_metadata(metadata: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

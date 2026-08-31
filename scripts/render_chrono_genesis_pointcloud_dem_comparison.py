#!/usr/bin/env python3
"""Render aligned Chrono/Genesis surface point clouds beside DEM error maps.

The isometric panels contain only points sampled on the frozen comparison
grid; they do not reconstruct or interpolate a surface.  Elevation is shown as
change from each solver's own initial state, matching the scored DEM response.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import yaml
from matplotlib.patches import Circle


PHASES = ("loaded", "residual")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chrono-episode", type=Path, required=True)
    parser.add_argument("--genesis-bridge", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dpi", type=int, default=200)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def comparison_grid(spec: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, tuple[float, float, float, float]]:
    rows, columns = (int(value) for value in spec["shape"])
    spacing = float(spec["spacing_m"])
    origin_x, origin_y = (float(value) for value in spec["origin_xy_m"])
    xs = origin_x + spacing * np.arange(columns)
    ys = origin_y + spacing * np.arange(rows)
    grid_x, grid_y = np.meshgrid(xs, ys, indexing="xy")
    extent = (
        origin_x - 0.5 * spacing,
        origin_x + (columns - 0.5) * spacing,
        origin_y - 0.5 * spacing,
        origin_y + (rows - 0.5) * spacing,
    )
    return grid_x, grid_y, extent


def style_isometric(axis: Any, z_limits_mm: tuple[float, float]) -> None:
    axis.set_xlabel("bed x (m)", labelpad=5)
    axis.set_ylabel("bed y (m)", labelpad=5)
    axis.set_zlabel("surface change (mm)", labelpad=5)
    axis.set_xlim(-0.3, 0.3)
    axis.set_ylim(-0.3, 0.3)
    axis.set_zlim(*z_limits_mm)
    axis.set_box_aspect((1.0, 1.0, 0.42))
    axis.set_proj_type("ortho")
    axis.view_init(elev=27, azim=-48)
    axis.tick_params(labelsize=7, pad=0)
    axis.xaxis.pane.fill = False
    axis.yaxis.pane.fill = False
    axis.zaxis.pane.fill = False
    axis.grid(True, linewidth=0.35, alpha=0.45)


def plot_point_cloud(
    axis: Any,
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    delta_mm: np.ndarray,
    valid: np.ndarray,
    title: str,
    deformation_limits_mm: tuple[float, float],
) -> Any:
    points = axis.scatter(
        grid_x[valid],
        grid_y[valid],
        delta_mm[valid],
        c=delta_mm[valid],
        cmap="terrain",
        vmin=deformation_limits_mm[0],
        vmax=deformation_limits_mm[1],
        s=2.0,
        marker="o",
        linewidths=0,
        alpha=0.95,
        depthshade=False,
        rasterized=True,
    )
    style_isometric(axis, deformation_limits_mm)
    axis.set_title(f"{title}\n{int(np.count_nonzero(valid)):,} surface points", fontsize=10)
    return points


def phase_metrics(error_mm: np.ndarray, valid: np.ndarray, footprint: np.ndarray, phase: str) -> dict[str, float]:
    metric_mask = valid if phase == "loaded" else valid & footprint
    values = error_mm[metric_mask]
    return {
        "cells": int(np.count_nonzero(metric_mask)),
        "rmse_mm": float(np.sqrt(np.mean(values * values))),
        "mae_mm": float(np.mean(np.abs(values))),
        "mean_signed_mm": float(np.mean(values)),
        "minimum_signed_mm": float(np.min(values)),
        "maximum_signed_mm": float(np.max(values)),
    }


def plot_error_map(
    axis: Any,
    error_mm: np.ndarray,
    valid: np.ndarray,
    extent: tuple[float, float, float, float],
    action: dict[str, Any],
    error_limit_mm: float,
    metrics: dict[str, float],
    phase: str,
) -> Any:
    image = axis.imshow(
        np.ma.array(error_mm, mask=~valid),
        extent=extent,
        origin="lower",
        cmap="RdBu_r",
        vmin=-error_limit_mm,
        vmax=error_limit_mm,
        interpolation="nearest",
    )
    axis.add_patch(
        Circle(
            action["center_xy_m"],
            float(action["radius_m"]),
            fill=False,
            color="black",
            linewidth=1.2,
            linestyle="--",
        )
    )
    metric_scope = "common support" if phase == "loaded" else "cylinder footprint"
    axis.set_title(
        "Genesis minus Chrono DEM response\n"
        f"RMSE {metrics['rmse_mm']:.3f} mm; mean {metrics['mean_signed_mm']:+.3f} mm ({metric_scope})",
        fontsize=10,
    )
    axis.set_xlabel("bed x (m)")
    axis.set_ylabel("bed y (m)")
    axis.set_aspect("equal")
    return image


def render_phase(
    output: Path,
    phase: str,
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    extent: tuple[float, float, float, float],
    valid: np.ndarray,
    footprint: np.ndarray,
    chrono_delta_mm: np.ndarray,
    genesis_delta_mm: np.ndarray,
    error_mm: np.ndarray,
    action: dict[str, Any],
    deformation_limits_mm: tuple[float, float],
    error_limit_mm: float,
    metrics: dict[str, float],
    dpi: int,
) -> None:
    figure = plt.figure(figsize=(16, 5.8), layout="constrained")
    chrono_axis = figure.add_subplot(1, 3, 1, projection="3d")
    genesis_axis = figure.add_subplot(1, 3, 2, projection="3d")
    error_axis = figure.add_subplot(1, 3, 3)
    points = plot_point_cloud(
        chrono_axis,
        grid_x,
        grid_y,
        chrono_delta_mm,
        valid,
        f"Chrono SCM — {phase}",
        deformation_limits_mm,
    )
    plot_point_cloud(
        genesis_axis,
        grid_x,
        grid_y,
        genesis_delta_mm,
        valid,
        f"Genesis MPM — {phase}",
        deformation_limits_mm,
    )
    image = plot_error_map(
        error_axis,
        error_mm,
        valid,
        extent,
        action,
        error_limit_mm,
        metrics,
        phase,
    )
    figure.colorbar(points, ax=(chrono_axis, genesis_axis), shrink=0.74, pad=0.01, label="surface change (mm)")
    figure.colorbar(image, ax=error_axis, shrink=0.82, pad=0.02, label="Genesis − Chrono response (mm)")
    figure.suptitle(
        f"{phase.capitalize()} response — aligned bed frame and common 5 mm grid; point centers only, no interpolation",
        fontsize=13,
    )
    figure.savefig(output, dpi=dpi, facecolor="white")
    plt.close(figure)


def render_combined(
    output: Path,
    phase_data: dict[str, dict[str, Any]],
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    extent: tuple[float, float, float, float],
    valid: np.ndarray,
    footprint: np.ndarray,
    action: dict[str, Any],
    deformation_limits_mm: tuple[float, float],
    error_limit_mm: float,
    dpi: int,
) -> None:
    figure = plt.figure(figsize=(16, 10.5), layout="constrained")
    point_artist = None
    error_artist = None
    point_axes = []
    error_axes = []
    for row, phase in enumerate(PHASES):
        data = phase_data[phase]
        chrono_axis = figure.add_subplot(2, 3, 3 * row + 1, projection="3d")
        genesis_axis = figure.add_subplot(2, 3, 3 * row + 2, projection="3d")
        error_axis = figure.add_subplot(2, 3, 3 * row + 3)
        point_artist = plot_point_cloud(
            chrono_axis,
            grid_x,
            grid_y,
            data["chrono_delta_mm"],
            valid,
            f"Chrono SCM — {phase}",
            deformation_limits_mm,
        )
        plot_point_cloud(
            genesis_axis,
            grid_x,
            grid_y,
            data["genesis_delta_mm"],
            valid,
            f"Genesis MPM — {phase}",
            deformation_limits_mm,
        )
        error_artist = plot_error_map(
            error_axis,
            data["error_mm"],
            valid,
            extent,
            action,
            error_limit_mm,
            data["metrics"],
            phase,
        )
        point_axes.extend((chrono_axis, genesis_axis))
        error_axes.append(error_axis)
    figure.colorbar(point_artist, ax=point_axes, shrink=0.72, pad=0.01, label="surface change (mm)")
    figure.colorbar(error_artist, ax=error_axes, shrink=0.78, pad=0.02, label="Genesis − Chrono response (mm)")
    figure.suptitle(
        "Confirmed Chrono–Genesis incumbent: isometric surface point clouds and aligned DEM error",
        fontsize=14,
    )
    figure.savefig(output, dpi=dpi, facecolor="white")
    plt.close(figure)


def main() -> None:
    args = parse_args()
    chrono_dir = args.chrono_episode.resolve()
    genesis_dir = args.genesis_bridge.resolve()
    output_dir = args.output_dir.resolve()
    if output_dir.exists():
        raise SystemExit(f"Refusing to overwrite existing output directory: {output_dir}")
    if args.dpi <= 0:
        raise ValueError("--dpi must be positive")

    chrono_manifest = yaml.safe_load((chrono_dir / "manifest.yaml").read_text(encoding="utf-8"))
    genesis_manifest = load_json(genesis_dir / "manifest.json")
    action = load_json(chrono_dir / "action.json")
    if chrono_manifest["heightmap"] != genesis_manifest["heightmap"]:
        raise ValueError("Chrono and Genesis manifests do not describe the same comparison grid")

    chrono_valid = np.load(chrono_dir / "valid_heightmap_mask.npy").astype(bool)
    genesis_valid = np.load(genesis_dir / "valid_heightmap_mask.npy").astype(bool)
    valid = chrono_valid & genesis_valid
    grid_x, grid_y, extent = comparison_grid(chrono_manifest["heightmap"])
    footprint = (
        (grid_x - float(action["center_xy_m"][0])) ** 2
        + (grid_y - float(action["center_xy_m"][1])) ** 2
        <= float(action["radius_m"]) ** 2
    )
    chrono_initial = np.load(chrono_dir / "initial_heightmap_m.npy")
    genesis_initial = np.load(genesis_dir / "initial_heightmap_m.npy")

    phase_data: dict[str, dict[str, Any]] = {}
    deformation_values = []
    error_values = []
    for phase in PHASES:
        chrono_delta_mm = (np.load(chrono_dir / f"{phase}_heightmap_m.npy") - chrono_initial) * 1000.0
        genesis_delta_mm = (np.load(genesis_dir / f"{phase}_heightmap_m.npy") - genesis_initial) * 1000.0
        error_mm = genesis_delta_mm - chrono_delta_mm
        metrics = phase_metrics(error_mm, valid, footprint, phase)
        phase_data[phase] = {
            "chrono_delta_mm": chrono_delta_mm,
            "genesis_delta_mm": genesis_delta_mm,
            "error_mm": error_mm,
            "metrics": metrics,
        }
        deformation_values.extend((chrono_delta_mm[valid], genesis_delta_mm[valid]))
        error_values.append(error_mm[valid])

    combined_deformation = np.concatenate(deformation_values)
    deformation_limits_mm = (
        min(float(np.min(combined_deformation)), -1.0),
        max(float(np.max(combined_deformation)), 1.0),
    )
    error_limit_mm = max(float(np.max(np.abs(np.concatenate(error_values)))), 1.0)

    output_dir.mkdir(parents=True)
    for phase in PHASES:
        data = phase_data[phase]
        render_phase(
            output_dir / f"{phase}_pointcloud_dem_error.png",
            phase,
            grid_x,
            grid_y,
            extent,
            valid,
            footprint,
            data["chrono_delta_mm"],
            data["genesis_delta_mm"],
            data["error_mm"],
            action,
            deformation_limits_mm,
            error_limit_mm,
            data["metrics"],
            args.dpi,
        )
        np.savez_compressed(
            output_dir / f"{phase}_comparison_raw.npz",
            x_m=grid_x,
            y_m=grid_y,
            common_valid_mask=valid,
            footprint_mask=footprint,
            chrono_response_mm=data["chrono_delta_mm"],
            genesis_response_mm=data["genesis_delta_mm"],
            genesis_minus_chrono_error_mm=data["error_mm"],
        )
    render_combined(
        output_dir / "loaded_residual_pointcloud_dem_error.png",
        phase_data,
        grid_x,
        grid_y,
        extent,
        valid,
        footprint,
        action,
        deformation_limits_mm,
        error_limit_mm,
        args.dpi,
    )
    manifest = {
        "schema_version": 1,
        "description": "Aligned surface point clouds and DEM response error; no surface interpolation.",
        "chrono_episode": str(chrono_dir),
        "genesis_bridge": str(genesis_dir),
        "coordinate_frame": chrono_manifest["coordinate_frame"],
        "heightmap": chrono_manifest["heightmap"],
        "common_valid_cells": int(np.count_nonzero(valid)),
        "error_sign": "Genesis response minus Chrono response",
        "deformation_limits_mm": list(deformation_limits_mm),
        "error_limit_mm": error_limit_mm,
        "phases": {phase: phase_data[phase]["metrics"] for phase in PHASES},
        "figures": [
            "loaded_pointcloud_dem_error.png",
            "residual_pointcloud_dem_error.png",
            "loaded_residual_pointcloud_dem_error.png",
        ],
        "raw_arrays": ["loaded_comparison_raw.npz", "residual_comparison_raw.npz"],
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(output_dir)


if __name__ == "__main__":
    main()

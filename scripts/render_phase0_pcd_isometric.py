#!/usr/bin/env python3
"""Render matched isometric surface-PCD views for Phase 0 held-out cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import TwoSlopeNorm
import numpy as np
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
MATRIX_ROOT = (
    REPO_ROOT
    / "outputs/validity_experiment/newton/static_proxy_hierarchical_v3_20261017/matrix"
)
DEFAULT_OUTPUT_DIR = REPO_ROOT / "docs/newton/figures/phase0_pcd_isometric"
CASE_IDS = ("yplus100_f046n", "yminus100_f046n")
PHASES = (
    ("loaded", "Loaded"),
    ("residual", "Post-unload"),
)
VIEWS = (
    ("ne", 28.0, -45.0),
    ("sw", 28.0, 135.0),
)
METHODS = ("Chrono", "Newton", "Hybrid")
LOCAL_RADIUS_M = 0.12
FOOT_RADIUS_M = 0.035
COLOR_NORM = TwoSlopeNorm(vmin=-50.0, vcenter=0.0, vmax=5.0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix-root", type=Path, default=MATRIX_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def load_case(
    matrix_root: Path, case_id: str
) -> tuple[dict[str, object], dict[str, object]]:
    summary = json.loads(
        (matrix_root / "cases" / case_id / "case_summary.json").read_text()
    )
    plan = json.loads((matrix_root / "matrix_plan.json").read_text())
    case = next(item for item in plan["cases"] if item["case_id"] == case_id)
    return summary, case


def surface_clouds(
    matrix_root: Path, case_id: str, phase: str
) -> dict[str, np.ndarray]:
    summary, case = load_case(matrix_root, case_id)
    chrono_dir = Path(summary["artifacts"]["chrono_episode"])
    response_dir = Path(summary["artifacts"]["newton_response"])
    hybrid_dir = matrix_root / "residual_pilot_v2_multiload/cases" / case_id
    manifest = yaml.safe_load((chrono_dir / "manifest.yaml").read_text())

    rows, columns = (int(value) for value in manifest["heightmap"]["shape"])
    spacing = float(manifest["heightmap"]["spacing_m"])
    origin_x, origin_y = (
        float(value) for value in manifest["heightmap"]["origin_xy_m"]
    )
    grid_x, grid_y = np.meshgrid(
        origin_x + np.arange(columns) * spacing,
        origin_y + np.arange(rows) * spacing,
    )
    center_x, center_y = (float(value) for value in case["center_xy_m"])
    relative_x = grid_x - center_x
    relative_y = grid_y - center_y
    radius = np.sqrt(relative_x**2 + relative_y**2)

    chrono_initial = np.load(chrono_dir / "initial_heightmap_m.npy")
    newton_initial = np.load(response_dir / "initial_heightmap_m.npy")
    chrono_surface = np.load(chrono_dir / f"{phase}_heightmap_m.npy")
    newton_surface = np.load(response_dir / f"{phase}_heightmap_m.npy")
    hybrid_surface = np.load(
        hybrid_dir / f"particle_corrected_{phase}_heightmap_m.npy"
    )
    valid = np.load(chrono_dir / "valid_heightmap_mask.npy").astype(bool)
    valid &= np.load(response_dir / "valid_heightmap_mask.npy").astype(bool)
    valid &= radius <= LOCAL_RADIUS_M
    for array in (
        chrono_initial,
        newton_initial,
        chrono_surface,
        newton_surface,
        hybrid_surface,
    ):
        valid &= np.isfinite(array)

    datum_mask = valid & (radius >= 0.09)
    datum_m = float(np.median(chrono_initial[datum_mask]))
    common = {
        "x_mm": 1000.0 * relative_x[valid],
        "y_mm": 1000.0 * relative_y[valid],
    }
    result: dict[str, np.ndarray] = {}
    for method, surface, initial in (
        ("Chrono", chrono_surface, chrono_initial),
        ("Newton", newton_surface, newton_initial),
        ("Hybrid", hybrid_surface, newton_initial),
    ):
        result[f"{method}_z_mm"] = 1000.0 * (surface[valid] - datum_m)
        result[f"{method}_dz_mm"] = 1000.0 * (surface[valid] - initial[valid])
    return common | result


def render_case(
    matrix_root: Path,
    output_dir: Path,
    case_id: str,
    view_name: str,
    elevation: float,
    azimuth: float,
) -> Path:
    clouds_by_phase = {
        phase: surface_clouds(matrix_root, case_id, phase) for phase, _ in PHASES
    }
    z_values = np.concatenate(
        [
            clouds[f"{method}_z_mm"]
            for clouds in clouds_by_phase.values()
            for method in METHODS
        ]
    )
    z_min = min(-50.0, float(np.floor(np.min(z_values) / 5.0) * 5.0))
    z_max = max(5.0, float(np.ceil(np.max(z_values) / 5.0) * 5.0))

    fig = plt.figure(figsize=(15.5, 9.2), constrained_layout=True)
    axes = np.empty((2, 3), dtype=object)
    theta = np.linspace(0.0, 2.0 * np.pi, 181)
    circle_x = 1000.0 * FOOT_RADIUS_M * np.cos(theta)
    circle_y = 1000.0 * FOOT_RADIUS_M * np.sin(theta)

    for row, (phase, phase_label) in enumerate(PHASES):
        clouds = clouds_by_phase[phase]
        for column, method in enumerate(METHODS):
            ax = fig.add_subplot(2, 3, row * 3 + column + 1, projection="3d")
            axes[row, column] = ax
            ax.scatter(
                clouds["x_mm"],
                clouds["y_mm"],
                clouds[f"{method}_z_mm"],
                c=clouds[f"{method}_dz_mm"],
                cmap="coolwarm",
                norm=COLOR_NORM,
                s=5.5,
                linewidths=0,
                rasterized=True,
                depthshade=False,
            )
            ax.plot(
                circle_x,
                circle_y,
                np.full_like(circle_x, 3.0),
                color="#202020",
                linestyle="--",
                linewidth=1.2,
                alpha=0.9,
            )
            ax.set_xlim(-120.0, 120.0)
            ax.set_ylim(-120.0, 120.0)
            ax.set_zlim(z_min, z_max)
            ax.set_box_aspect((1.0, 1.0, 0.32))
            ax.view_init(elev=elevation, azim=azimuth)
            ax.set_xticks((-100.0, 0.0, 100.0))
            ax.set_yticks((-100.0, 0.0, 100.0))
            ax.tick_params(labelsize=8, pad=0)
            ax.grid(True, alpha=0.25)
            ax.set_xlabel("foot-relative x (mm)", fontsize=8, labelpad=2)
            ax.set_ylabel("foot-relative y (mm)", fontsize=8, labelpad=2)
            if column == 0:
                ax.set_zlabel("z from local datum (mm)", fontsize=8, labelpad=2)
            ax.set_title(method, fontsize=13, fontweight="semibold", pad=4)
            if column == 0:
                ax.text2D(
                    -0.10,
                    0.92,
                    phase_label,
                    transform=ax.transAxes,
                    rotation=90,
                    va="top",
                    ha="center",
                    fontsize=12,
                    fontweight="semibold",
                )

    direction = "+y validation" if case_id.startswith("yplus") else "-y test"
    fig.suptitle(
        f"Phase 0 surface point clouds — {direction}, 46 N — {view_name.upper()} view",
        fontsize=16,
        fontweight="bold",
    )
    colorbar = fig.colorbar(
        ScalarMappable(norm=COLOR_NORM, cmap="coolwarm"),
        ax=axes.ravel().tolist(),
        shrink=0.72,
        pad=0.045,
        aspect=35,
    )
    colorbar.set_label("vertical displacement from each method's initial surface (mm)")
    fig.text(
        0.5,
        0.005,
        "Shared 240 mm crop and color scale; dashed circle = 35 mm foot radius.",
        ha="center",
        fontsize=9,
        color="#333333",
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{case_id}_isometric_{view_name}.png"
    fig.savefig(path, dpi=180, facecolor="white")
    plt.close(fig)
    return path


def main() -> None:
    args = parse_args()
    for case_id in CASE_IDS:
        for view_name, elevation, azimuth in VIEWS:
            path = render_case(
                args.matrix_root,
                args.output_dir,
                case_id,
                view_name,
                elevation,
                azimuth,
            )
            print(path)


if __name__ == "__main__":
    main()

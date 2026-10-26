from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from chrono_episode_bridge import build_metric_bed
from phase1_metric_bed import build_common_base_metric_bed


def manifest(rows: int = 3, cols: int = 4, spacing: float = 0.005) -> dict:
    return {
        "coordinate_frame": "bed",
        "heightmap": {
            "shape": [rows, cols],
            "spacing_m": spacing,
            "origin_xy_m": [-0.01, -0.005],
        },
    }


def columns(points: np.ndarray) -> dict[tuple[float, float], np.ndarray]:
    result = {}
    for x, y in np.unique(points[:, :2], axis=0):
        mask = np.isclose(points[:, 0], x) & np.isclose(points[:, 1], y)
        result[(float(x), float(y))] = np.sort(points[mask, 2])
    return result


def test_flat_surface_matches_legacy_particle_coordinates() -> None:
    surface = np.zeros((3, 4), dtype=np.float32)
    old, _old_metadata = build_metric_bed(
        surface, manifest(), bed_depth_m=0.1, particle_spacing_m=0.005
    )
    new, metadata = build_common_base_metric_bed(
        surface,
        manifest(),
        bed_depth_m=0.1,
        particle_spacing_m=0.005,
    )
    old_sorted = old[np.lexsort((old[:, 2], old[:, 1], old[:, 0]))]
    new_sorted = new[np.lexsort((new[:, 2], new[:, 1], new[:, 0]))]
    np.testing.assert_array_equal(new_sorted, old_sorted)
    assert metadata["base_contract"]["base_z_m"] == pytest.approx(-0.1)
    assert metadata["ground_plane_mpm"]["point"][2] == pytest.approx(-0.105)


def test_varying_surface_has_exact_top_and_one_common_base() -> None:
    surface = np.array(
        [
            [-0.0040, -0.0020, 0.0010, 0.0047],
            [-0.0030, -0.0010, 0.0020, 0.0030],
            [-0.0025, 0.0, 0.0015, 0.0],
        ],
        dtype=np.float32,
    )
    points, metadata = build_common_base_metric_bed(
        surface,
        manifest(),
        bed_depth_m=0.1,
        particle_spacing_m=0.005,
    )
    by_column = columns(points)
    xs = np.array(manifest()["heightmap"]["origin_xy_m"][0]) + np.arange(4) * 0.005
    ys = np.array(manifest()["heightmap"]["origin_xy_m"][1]) + np.arange(3) * 0.005
    base = metadata["base_contract"]["base_z_m"]
    for row, y in enumerate(ys):
        for col, x in enumerate(xs):
            z = by_column[(float(np.float32(x)), float(np.float32(y)))]
            assert z[0] == pytest.approx(base, abs=1.0e-7)
            assert z[-1] == pytest.approx(float(surface[row, col]), abs=1.0e-7)
            assert z[-1] - z[-2] >= 0.95 * 0.005 - 1.0e-7
    assert metadata["base_contract"]["all_columns_include_base"] is True
    assert metadata["base_contract"]["minimum_column_particles"] < metadata[
        "base_contract"
    ]["maximum_column_particles"]


def test_builder_rejects_spacing_or_shape_mismatch() -> None:
    with pytest.raises(ValueError, match="spacing"):
        build_common_base_metric_bed(
            np.zeros((3, 4)),
            manifest(),
            bed_depth_m=0.1,
            particle_spacing_m=0.004,
        )
    with pytest.raises(ValueError, match="shape"):
        build_common_base_metric_bed(
            np.zeros((2, 4)),
            manifest(),
            bed_depth_m=0.1,
            particle_spacing_m=0.005,
        )

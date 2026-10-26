#!/usr/bin/env python3
"""Tests for deterministic Phase 1 surface-to-particle lifting."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "phase1_particle_lift.py"
spec = importlib.util.spec_from_file_location("phase1_particle_lift", SCRIPT_PATH)
assert spec and spec.loader
lift = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = lift
spec.loader.exec_module(lift)


def column_particles() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    xs = np.asarray([-0.01, 0.0, 0.01], dtype=np.float64)
    ys = np.asarray([-0.01, 0.0, 0.01], dtype=np.float64)
    points = []
    for y in ys:
        for x in xs:
            for z in (0.0, -0.025, -0.075, -0.1):
                points.append((x, y, z))
    return np.asarray(points, dtype=np.float32), xs, ys


class Phase1ParticleLiftTests(unittest.TestCase):
    def test_positive_and_negative_surface_are_reproduced(self) -> None:
        points, xs, ys = column_particles()
        target = np.asarray(
            [[0.01, -0.02, 0.005], [0.0, -0.01, 0.02], [-0.005, 0.0, 0.01]],
            dtype=np.float32,
        )
        valid = np.ones(target.shape, dtype=bool)
        corrected, displacement, source = lift.lift_surface_to_particles(
            points, target, valid, xs, ys, cutoff_depth_m=0.1
        )
        projected, observed = lift.project_particle_surface(corrected, xs, ys)
        np.testing.assert_allclose(source, 0.0, atol=0.0)
        np.testing.assert_allclose(projected, target, atol=1.0e-7)
        self.assertTrue(np.all(observed))
        np.testing.assert_array_equal(corrected[:, :2], points[:, :2])
        self.assertGreater(float(np.max(np.abs(displacement))), 0.0)

    def test_depth_taper_preserves_order_and_bottom(self) -> None:
        points, xs, ys = column_particles()
        target = np.full((3, 3), -0.04, dtype=np.float32)
        corrected, displacement, _source = lift.lift_surface_to_particles(
            points, target, np.ones((3, 3), dtype=bool), xs, ys, cutoff_depth_m=0.1
        )
        center = np.isclose(points[:, 0], 0.0) & np.isclose(points[:, 1], 0.0)
        corrected_column = corrected[center, 2]
        self.assertTrue(np.all(np.diff(corrected_column) < 0.0))
        self.assertAlmostEqual(float(displacement[center][-1]), 0.0, places=7)

    def test_invalid_support_particles_are_unchanged(self) -> None:
        points, xs, ys = column_particles()
        valid = np.zeros((3, 3), dtype=bool)
        valid[1, 1] = True
        target = np.full((3, 3), 0.01, dtype=np.float32)
        corrected, displacement, _source = lift.lift_surface_to_particles(
            points, target, valid, xs, ys, cutoff_depth_m=0.1
        )
        center = np.isclose(points[:, 0], 0.0) & np.isclose(points[:, 1], 0.0)
        np.testing.assert_array_equal(corrected[~center], points[~center])
        np.testing.assert_array_equal(displacement[~center], 0.0)

    def test_order_violating_downward_correction_is_rejected(self) -> None:
        points, xs, ys = column_particles()
        with self.assertRaisesRegex(ValueError, "preserve particle ordering"):
            lift.lift_surface_to_particles(
                points,
                np.full((3, 3), -0.1, dtype=np.float32),
                np.ones((3, 3), dtype=bool),
                xs,
                ys,
                cutoff_depth_m=0.1,
            )

    def test_corrected_archive_preserves_every_source_field(self) -> None:
        points, xs, ys = column_particles()
        valid = np.ones((3, 3), dtype=bool)
        target = np.full((3, 3), -0.015, dtype=np.float32)
        corrected, displacement, _source = lift.lift_surface_to_particles(
            points, target, valid, xs, ys, cutoff_depth_m=0.1
        )
        count = points.shape[0]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "source.npz"
            corrected_path = root / "corrected.npz"
            surface_path = root / "predicted.npy"
            np.savez_compressed(
                source_path,
                schema_version=np.asarray(2, dtype=np.int64),
                backend=np.asarray("newton"),
                position_m=points,
                velocity_mps=np.arange(count * 3, dtype=np.float32).reshape(count, 3),
                stress_pa=np.arange(count * 9, dtype=np.float32).reshape(count, 3, 3),
                contact_collider_id=np.asarray([0, 1], dtype=np.int64),
            )
            np.save(surface_path, target)
            lift.write_corrected_state(
                source_path,
                corrected_path,
                corrected,
                displacement,
                model_id="H1-seed-7",
            )
            audit = lift.audit_corrected_state(
                source_path,
                corrected_path,
                surface_path,
                valid,
                xs,
                ys,
                model_id="H1-seed-7",
                surface_tolerance_m=1.0e-6,
            )
        self.assertTrue(audit["all_checks_pass"])
        self.assertEqual(audit["source_particle_count"], count)
        self.assertEqual(audit["corrected_particle_count"], count)
        self.assertLessEqual(audit["maximum_surface_reproduction_error_m"], 1.0e-6)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Unit tests for the dependency-light Newton integration contract."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from newton_contract import (  # noqa: E402
    containment_bounds,
    load_newton_config,
    particle_mass_kg,
    select_center_crop,
    speed_summary,
    validate_metric_bed,
)
from run_newton_cylinder_diagnostic import (  # noqa: E402
    advance_guided_body,
    circumscribed_cylinder_radius,
    convergence_qualifies_preparation,
    cylinder_projection_thresholds,
    cylinder_penetration,
    response_error,
)

ANALYZER_SPEC = __import__("importlib.util").util.spec_from_file_location(
    "newton_preparation_convergence",
    SCRIPTS / "analyze_newton_preparation_convergence.py",
)
assert ANALYZER_SPEC is not None and ANALYZER_SPEC.loader is not None
ANALYZER = __import__("importlib.util").util.module_from_spec(ANALYZER_SPEC)
sys.modules[ANALYZER_SPEC.name] = ANALYZER
ANALYZER_SPEC.loader.exec_module(ANALYZER)


def valid_config() -> dict:
    return {
        "schema_version": 1,
        "backend": "newton",
        "material": {
            "density_kg_m3": 1000.0,
            "young_modulus_pa": 100000.0,
            "poisson_ratio": 0.2,
            "friction_coefficient": 0.68,
        },
        "solver": {"voxel_size_m": 0.015625},
        "contact": {"wall_height_m": 0.2, "wall_thickness_m": 0.02},
    }


class NewtonConfigTest(unittest.TestCase):
    def write_config(self, value: dict) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "config.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_explicit_friction_coefficient_is_required(self) -> None:
        value = valid_config()
        value["material"].pop("friction_coefficient")
        value["material"]["friction_angle"] = 35.0
        with self.assertRaisesRegex(ValueError, "explicit friction_coefficient"):
            load_newton_config(self.write_config(value))

    def test_config_keeps_solver_and_material_semantics_separate(self) -> None:
        config = load_newton_config(self.write_config(valid_config()))
        self.assertEqual(config.material.friction_coefficient, 0.68)
        self.assertEqual(config.material.young_modulus_pa, 100000.0)
        self.assertEqual(config.solver.voxel_size_m, 0.015625)
        self.assertEqual(config.solver.grid_type, "sparse")

    def test_repository_default_uses_qualified_pic_transfer(self) -> None:
        config = load_newton_config(
            Path(__file__).resolve().parents[1] / "configs" / "newton_sand_smoke.json"
        )
        self.assertEqual(config.solver.transfer_scheme, "pic")


class NewtonMetricBedTest(unittest.TestCase):
    def setUp(self) -> None:
        surface = np.array(
            [
                [-0.005, -0.005, 0.0],
                [0.005, -0.005, 0.0],
                [-0.005, 0.005, 0.0],
                [0.005, 0.005, 0.0],
            ],
            dtype=np.float32,
        )
        self.points = np.concatenate(
            [surface, surface - np.array([0.0, 0.0, 0.005], dtype=np.float32)]
        )
        self.metadata = {
            "coordinate_frame": "bed",
            "particle_count": 8,
            "surface_particle_count": 4,
            "particle_spacing_m": 0.005,
            "ground_plane_mpm": {
                "point": [0.0, 0.0, -0.010],
                "normal": [0.0, 0.0, 1.0],
            },
        }

    def test_metric_bed_validation_and_mass(self) -> None:
        surface_count, spacing, ground_z = validate_metric_bed(self.points, self.metadata)
        self.assertEqual(surface_count, 4)
        self.assertEqual(spacing, 0.005)
        self.assertEqual(ground_z, -0.010)
        self.assertAlmostEqual(particle_mass_kg(1000.0, spacing), 0.000125)

    def test_center_crop_preserves_layers(self) -> None:
        cropped, cropped_surface, keep = select_center_crop(
            self.points, surface_count=4, radius_m=0.006
        )
        self.assertEqual(cropped_surface, 4)
        self.assertEqual(cropped.shape, (8, 3))
        self.assertTrue(np.all(keep))

    def test_bounds_and_speed_summary(self) -> None:
        np.testing.assert_allclose(
            containment_bounds(self.points, 0.005),
            (-0.0075, 0.0075, -0.0075, 0.0075),
            atol=1.0e-9,
        )
        summary = speed_summary(np.zeros((8, 3), dtype=np.float32))
        self.assertEqual(summary["p99_mps"], 0.0)
        self.assertEqual(summary["max_mps"], 0.0)


class NewtonPreparationConvergenceTest(unittest.TestCase):
    def test_observed_order(self) -> None:
        self.assertAlmostEqual(ANALYZER.observed_order(0.004, 0.001), 2.0)
        self.assertIsNone(ANALYZER.observed_order(0.0, 0.001))


class NewtonCylinderDiagnosticTest(unittest.TestCase):
    def test_convergence_summary_must_contain_selected_preparation(self) -> None:
        root = Path("/tmp/selected_preparation")
        summary = {
            "backend": "newton",
            "status": "passed",
            "matrix_complete": True,
            "all_cases_accepted": True,
            "consistency_passed": True,
            "cases": [{"path": str(root)}],
        }
        self.assertTrue(convergence_qualifies_preparation(summary, root))
        self.assertFalse(
            convergence_qualifies_preparation(summary, Path("/tmp/other_preparation"))
        )

    def test_circumscribed_mesh_facets_do_not_enter_analytic_radius(self) -> None:
        analytic_radius = 0.073025
        segments = 128
        vertex_radius = circumscribed_cylinder_radius(analytic_radius, segments)
        facet_radius = vertex_radius * np.cos(np.pi / segments)
        self.assertAlmostEqual(facet_radius, analytic_radius)
        self.assertGreater(vertex_radius, analytic_radius)

    def test_projection_threshold_override_targets_only_cylinder(self) -> None:
        result = cylinder_projection_thresholds(
            np.array([-1, 3, 7]), cylinder_body=3, threshold_m=0.0
        )
        self.assertEqual(result, [None, 0.0, None])

    def test_forward_consistent_position_uses_pre_impulse_velocity(self) -> None:
        z_forward, vz_forward = advance_guided_body(
            1.0, -0.1, 0.2, 2.0, 0.01, "forward_consistent"
        )
        z_semi, vz_semi = advance_guided_body(
            1.0, -0.1, 0.2, 2.0, 0.01, "semi_implicit"
        )
        self.assertAlmostEqual(vz_forward, vz_semi)
        self.assertAlmostEqual(z_forward, 0.999)
        self.assertAlmostEqual(z_semi, 1.0 + vz_semi * 0.01)

    def test_penetration_counts_particle_centers(self) -> None:
        points = np.array(
            [[0.0, 0.0, 0.0], [0.02, 0.0, 0.0], [0.0, 0.0, 0.02]],
            dtype=np.float32,
        )
        result = cylinder_penetration(
            points,
            center_xy=(0.0, 0.0),
            center_z=0.0,
            radius=0.01,
            half_height=0.01,
        )
        self.assertEqual(result["inside_particle_centers"], 1)
        self.assertAlmostEqual(result["max_center_penetration_m"], 0.01)

    def test_response_error_uses_change_from_each_initial_map(self) -> None:
        initial = np.zeros((2, 2), dtype=np.float32)
        candidate = np.full((2, 2), -0.002, dtype=np.float32)
        target_initial = np.full((2, 2), 0.01, dtype=np.float32)
        target = np.full((2, 2), 0.007, dtype=np.float32)
        result = response_error(
            candidate,
            initial,
            target,
            target_initial,
            np.ones((2, 2), dtype=bool),
        )
        self.assertEqual(result["valid_cells"], 4)
        self.assertAlmostEqual(result["rmse_m"], 0.001)
        self.assertAlmostEqual(result["signed_mean_m"], 0.001)


if __name__ == "__main__":
    unittest.main()

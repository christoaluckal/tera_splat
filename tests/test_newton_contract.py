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
    active_cylinder_contact_arrays,
    advance_guided_body,
    circumscribed_cylinder_radius,
    convergence_qualifies_preparation,
    cylinder_collision_center_offset_z,
    cylinder_projection_thresholds,
    cylinder_penetration,
    finite_cylinder_signed_distance,
    guide_constraint_error,
    phase1_state_arrays,
    response_error,
    summarize_cylinder_contacts,
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

    def test_common_base_allows_variable_column_counts(self) -> None:
        surface = np.array(
            [
                [-0.005, -0.005, 0.0],
                [0.005, -0.005, 0.004],
            ],
            dtype=np.float32,
        )
        points = np.concatenate(
            [
                surface,
                np.array(
                    [
                        [-0.005, -0.005, -0.010],
                        [-0.005, -0.005, -0.015],
                        [0.005, -0.005, -0.010],
                        [0.005, -0.005, -0.015],
                        [0.005, -0.005, -0.005],
                    ],
                    dtype=np.float32,
                ),
            ]
        )
        metadata = {
            "coordinate_frame": "bed",
            "particle_count": 7,
            "surface_particle_count": 2,
            "particle_spacing_m": 0.005,
            "base_contract": {
                "mode": "common_flat_base",
                "base_z_m": -0.015,
                "minimum_column_particles": 3,
                "maximum_column_particles": 4,
            },
            "ground_plane_mpm": {
                "point": [0.0, 0.0, -0.020],
                "normal": [0.0, 0.0, 1.0],
            },
        }
        surface_count, spacing, ground_z = validate_metric_bed(points, metadata)
        self.assertEqual(surface_count, 2)
        self.assertEqual(spacing, 0.005)
        self.assertEqual(ground_z, -0.020)

    def test_common_base_rejects_one_raised_column_bottom(self) -> None:
        points = np.array(
            [
                [-0.005, 0.0, 0.0],
                [0.005, 0.0, 0.0],
                [-0.005, 0.0, -0.010],
                [0.005, 0.0, -0.005],
            ],
            dtype=np.float32,
        )
        metadata = {
            "coordinate_frame": "bed",
            "particle_count": 4,
            "surface_particle_count": 2,
            "particle_spacing_m": 0.005,
            "base_contract": {
                "mode": "common_flat_base",
                "base_z_m": -0.010,
                "minimum_column_particles": 2,
                "maximum_column_particles": 2,
            },
            "ground_plane_mpm": {
                "point": [0.0, 0.0, -0.015],
                "normal": [0.0, 0.0, 1.0],
            },
        }
        with self.assertRaisesRegex(ValueError, "share the declared base"):
            validate_metric_bed(points, metadata)

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
    def test_phase1_snapshot_uses_coupled_entry_mechanics(self) -> None:
        class Array:
            def __init__(self, value):
                self.value = np.asarray(value)

            def numpy(self):
                return self.value

        class Namespace:
            pass

        def state(stress):
            value = Namespace()
            value.particle_q = Array(np.zeros((1, 3)))
            value.particle_qd = Array(np.zeros((1, 3)))
            value.mpm = Namespace()
            value.mpm.particle_qd_grad = Array(np.zeros((1, 3, 3)))
            value.mpm.particle_elastic_strain = Array(
                np.repeat(np.eye(3)[None], 1, axis=0)
            )
            value.mpm.particle_Jp = Array(np.ones(1))
            value.mpm.particle_stress = Array(
                np.full((1, 3, 3), stress, dtype=float)
            )
            value.mpm.particle_transform = Array(
                np.repeat(np.eye(3)[None], 1, axis=0)
            )
            return value

        parent = state(0.0)
        entry = state(7.0)

        class Solver:
            def entry_state(self, name, phase):
                self.call = (name, phase)
                return entry

        solver = Solver()
        arrays = phase1_state_arrays(parent, solver, "native_proxy")
        np.testing.assert_array_equal(arrays["stress_pa"], np.full((1, 3, 3), 7.0))
        self.assertEqual(solver.call, ("mpm", "current"))

    def test_active_contact_archive_filters_to_cylinder_body(self) -> None:
        class Array:
            def __init__(self, value):
                self.value = np.asarray(value)

            def numpy(self):
                return self.value

        class Solver:
            collider_body_index = Array([3, 4])

            def collect_collider_impulses(self, state):
                return (
                    Array([[0, 0, 2], [0, 0, 0], [0, 0, 5]]),
                    Array([[0, 0, 0], [1, 0, 0], [2, 0, 0]]),
                    Array([0, 0, 1]),
                )

        contacts = active_cylinder_contact_arrays(Solver(), object(), 3)
        np.testing.assert_array_equal(
            contacts["contact_position_m"], [[0.0, 0.0, 0.0]]
        )
        np.testing.assert_array_equal(
            contacts["contact_impulse_ns"], [[0.0, 0.0, 2.0]]
        )

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

    def test_collision_proxy_offset_preserves_requested_bottom_inset(self) -> None:
        analytic_half_height = 0.0254
        collision_half_height = analytic_half_height + 1.0e-5
        requested_inset = 0.00975
        center_offset = cylinder_collision_center_offset_z(
            requested_inset, analytic_half_height, collision_half_height
        )
        proxy_bottom = center_offset - collision_half_height
        analytic_bottom = -analytic_half_height
        self.assertAlmostEqual(proxy_bottom - analytic_bottom, requested_inset)
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            cylinder_collision_center_offset_z(
                -1.0e-3, analytic_half_height, collision_half_height
            )

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

    def test_guide_constraint_error_reports_only_forbidden_motion(self) -> None:
        ideal = guide_constraint_error(
            np.array([0.0, 0.005, -0.01, 0.0, 0.0, 0.0, 1.0]),
            np.array([0.0, 0.0, -0.2, 0.0, 0.0, 0.0]),
            (0.0, 0.005),
        )
        self.assertEqual(
            ideal,
            {
                "horizontal_position_error_m": 0.0,
                "orientation_quaternion_error": 0.0,
                "horizontal_speed_mps": 0.0,
                "angular_speed_radps": 0.0,
            },
        )
        shifted = guide_constraint_error(
            np.array([0.003, 0.001, -0.01, 0.0, 0.0, 0.0, -1.0]),
            np.array([0.003, 0.004, -0.2, 0.0, 0.0, 0.02]),
            (0.0, 0.005),
        )
        self.assertAlmostEqual(shifted["horizontal_position_error_m"], 0.005)
        self.assertAlmostEqual(shifted["orientation_quaternion_error"], 0.0)
        self.assertAlmostEqual(shifted["horizontal_speed_mps"], 0.005)
        self.assertAlmostEqual(shifted["angular_speed_radps"], 0.02)

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

    def test_finite_cylinder_signed_distance_uses_analytic_surface(self) -> None:
        result = finite_cylinder_signed_distance(
            np.array(
                [
                    [0.0, 0.0, 0.0],
                    [0.0, 0.0, -0.02],
                    [0.03, 0.0, 0.0],
                    [0.03, 0.0, 0.03],
                ]
            ),
            center_xy=(0.0, 0.0),
            center_z=0.0,
            radius=0.02,
            half_height=0.01,
        )
        np.testing.assert_allclose(
            result,
            np.array([-0.01, 0.01, 0.01, np.sqrt(0.01**2 + 0.02**2)]),
        )

    def test_contact_summary_separates_assigned_and_impulse_nodes(self) -> None:
        summary = summarize_cylinder_contacts(
            impulses=np.array(
                [[0.0, 0.0, 0.0], [0.0, 0.0, 0.3], [0.0, 0.0, 9.0]]
            ),
            positions=np.array(
                [[0.0, 0.0, -0.02], [0.0, 0.0, -0.012], [0.0, 0.0, 0.0]]
            ),
            collider_ids=np.array([1, 1, -1]),
            collider_body_indices=np.array([-1, 4]),
            body_index=4,
            center_xy=(0.0, 0.0),
            center_z=0.0,
            radius=0.02,
            half_height=0.01,
        )
        self.assertEqual(summary["assigned_nodes"], 2)
        self.assertEqual(summary["impulse_nodes"], 1)
        self.assertAlmostEqual(summary["upward_impulse_ns"], 0.3)
        self.assertAlmostEqual(summary["assigned_sdf_min_m"], 0.002)
        self.assertAlmostEqual(summary["assigned_sdf_max_m"], 0.01)
        self.assertAlmostEqual(summary["impulse_sdf_min_m"], 0.002)
        self.assertAlmostEqual(summary["impulse_sdf_max_m"], 0.002)

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

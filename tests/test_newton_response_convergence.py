#!/usr/bin/env python3
"""Unit tests for the Newton full-response convergence analyzer."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SPEC = importlib.util.spec_from_file_location(
    "newton_response_convergence",
    SCRIPTS / "analyze_newton_response_convergence.py",
)
assert SPEC is not None and SPEC.loader is not None
ANALYZER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ANALYZER
SPEC.loader.exec_module(ANALYZER)


def synthetic_case(label: str, dt_s: float, offset: float) -> object:
    initial = np.full((2, 2), offset, dtype=np.float64)
    loaded = initial + np.full((2, 2), -0.002, dtype=np.float64)
    residual = initial + np.full((2, 2), -0.001, dtype=np.float64)
    manifest = {
        "backend": "newton",
        "status": "mechanics_qualified_uncalibrated",
        "accepted": True,
        "mechanics_qualified": True,
        "finite": True,
        "chrono_episode": "/tmp/oracle",
        "environment": {"python": "3.11", "newton": "1.5.1", "warp": "1.17.0"},
        "solver": {"dt_s": dt_s, "transfer_scheme": "pic"},
        "preparation": {
            "convergence_passed": True,
            "pre_settle": {"final_speed": {"p99_mps": 0.0}},
        },
        "action": {
            "episode_id": "A0",
            "mass_kg": 1.5,
            "center_xy_m": [0.0, 0.005],
            "radius_m": 0.073025,
            "height_m": 0.0508,
            "start_clearance_m": 0.02,
            "removal": "remove_body",
            "geometry": "right_circular_cylinder",
            "gravity_mps2": [0.0, 0.0, -9.81],
            "loaded_duration_s": 3.595,
            "residual_duration_s": 0.25,
            "removal_implementation": "instantaneous",
        },
        "cylinder": {
            "friction_coefficient": 0.2,
            "collider_mode": "circumscribed_mesh",
            "collider_segments": 128,
            "analytic_radius_m": 0.073025,
            "collision_mesh_vertex_radius_m": 0.073057,
            "guide_constraint_passed": True,
            "collision_mesh_half_height_m": 0.02541,
            "collision_guard_m": 1.0e-5,
            "collision_bottom_inset_m": 0.009375,
            "collision_center_offset_z_m": 0.009385,
            "projection_threshold_m": 0.0,
            "guided_body_position_update": "forward_consistent",
            "sinkage_below_initial_surface_m": 0.008,
            "loaded_vertical_speed_mps": -0.004,
        },
        "contact_activation": {
            "implementation": "process-local per-collider rasterization threshold",
            "requested_activation_distance_voxels": -0.25,
            "newton_default_activation_distance_voxels": 0.25,
            "containment_uses_newton_default": True,
            "signed_distance_geometry_unchanged": True,
            "project_outside_geometry_unchanged": True,
            "distance_unit": "grid voxels",
            "voxel_size_m": 0.015625,
        },
        "penetration": {
            "passed_zero_center_penetration_gate": True,
            "max_inside_particle_centers": 0,
            "max_center_penetration_m": 0.0,
        },
        "surface": {"valid_cells": 4},
    }
    return ANALYZER.Case(
        label=label,
        root=Path("/tmp") / label,
        manifest=manifest,
        config={"backend": "newton", "material": {"young_modulus_pa": 100000.0}},
        initial=initial,
        loaded=loaded,
        residual=residual,
        mask=np.ones((2, 2), dtype=bool),
    )


class NewtonResponseConvergenceTest(unittest.TestCase):
    def test_response_comparison_removes_each_initial_offset(self) -> None:
        coarse = synthetic_case("coarse", 0.0005, 0.0)
        fine = synthetic_case("fine", 0.00025, 0.01)
        result = ANALYZER.compare_cases(coarse, fine, 0.0005, 0.001, 0.0005)
        self.assertAlmostEqual(result["loaded_rmse_m"], 0.0)
        self.assertAlmostEqual(result["residual_rmse_m"], 0.0)
        self.assertTrue(result["passes_gate"])

    def test_each_case_must_retain_mechanics_gates(self) -> None:
        case = synthetic_case("case", 0.0005, 0.0)
        self.assertTrue(ANALYZER.case_qualifies(case))
        case.manifest["penetration"]["passed_zero_center_penetration_gate"] = False
        self.assertFalse(ANALYZER.case_qualifies(case))
        case.manifest["penetration"]["passed_zero_center_penetration_gate"] = True
        case.manifest["cylinder"]["guide_constraint_passed"] = False
        self.assertFalse(ANALYZER.case_qualifies(case))

    def test_invariants_allow_only_timestep_to_change(self) -> None:
        coarse = synthetic_case("coarse", 0.0005, 0.0)
        fine = synthetic_case("fine", 0.00025, 0.0)
        self.assertEqual(ANALYZER.invariant_mismatches([coarse, fine]), [])
        fine.manifest["cylinder"]["collision_bottom_inset_m"] = 0.0
        self.assertEqual(
            ANALYZER.invariant_mismatches([coarse, fine]),
            ["fine: cylinder differs from coarse"],
        )
        fine.manifest["cylinder"]["collision_bottom_inset_m"] = 0.009375
        fine.manifest["contact_activation"][
            "requested_activation_distance_voxels"
        ] = -0.5
        self.assertEqual(
            ANALYZER.invariant_mismatches([coarse, fine]),
            ["fine: contact_activation differs from coarse"],
        )
        fine.manifest["contact_activation"][
            "requested_activation_distance_voxels"
        ] = -0.25
        fine.config["material"]["young_modulus_pa"] = 200000.0
        self.assertEqual(
            ANALYZER.invariant_mismatches([coarse, fine]),
            ["fine: config differs from coarse"],
        )

    def test_observed_order_is_report_only(self) -> None:
        self.assertAlmostEqual(ANALYZER.observed_order(0.004, 0.001), 2.0)
        self.assertIsNone(ANALYZER.observed_order(0.0, 0.001))


if __name__ == "__main__":
    unittest.main()

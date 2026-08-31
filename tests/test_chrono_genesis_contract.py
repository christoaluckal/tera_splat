#!/usr/bin/env python3
"""Regression checks for the frozen Chrono-to-Genesis n128 contract.

The test uses the compact retained incumbent evidence.  Paths may be
overridden for another installation through ``TERA_SPLAT_ORACLE``,
``TERA_SPLAT_PREPARED_ROOT``, ``TERA_SPLAT_CONTRACT_TRIAL``,
``TERA_SPLAT_REFERENCE_TRIAL``, and ``TERA_SPLAT_REPEAT_TRIAL``.
"""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

import numpy as np
import yaml


DEFAULT_ORACLE = Path(
    "/data/christoa/Chrono/tera_splat_sim/validity_experiment/chrono_episodes/"
    "A0_oracle_guided_offset_5mm_gate6mm_v1"
)
DEFAULT_PREPARED_ROOT = Path(
    "/data/christoa/Chrono/tera_splat/outputs/validity_experiment/"
    "A0_oracle_guided_offset_5mm_gate6mm_prepared_5mm_n128_ratio_matched"
)
DEFAULT_CONTRACT_TRIAL = Path(
    "/data/christoa/Chrono/tera_splat/outputs/validity_experiment/resolution_replay/"
    "A0_oracle_guided_offset_5mm_gate6mm_5mm_n128_anchor_e20k_pre4s/"
    "study_qgk3079l/trials/iteration_000"
)
DEFAULT_REPEAT_REFERENCE = Path(
    "/data/christoa/Chrono/tera_splat/outputs/validity_experiment/bayesopt/"
    "A0_oracle_guided_offset_5mm_gate6mm_5mm_n128_lowphi_boundary_20260829/"
    "study_yab3idti/trials/iteration_011"
)
DEFAULT_REPEAT_TRIAL = Path(
    "/data/christoa/Chrono/tera_splat/outputs/validity_experiment/bayesopt/"
    "A0_oracle_guided_offset_5mm_gate6mm_5mm_n128_lowphi_winner_exact_replay_20260830/"
    "study_r2at0vvb/trials/iteration_000"
)


def configured_path(environment_name: str, default: Path) -> Path:
    return Path(os.environ.get(environment_name, str(default))).resolve()


class ChronoGenesisContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.oracle = configured_path("TERA_SPLAT_ORACLE", DEFAULT_ORACLE)
        cls.prepared_root = configured_path("TERA_SPLAT_PREPARED_ROOT", DEFAULT_PREPARED_ROOT)
        cls.trial = configured_path("TERA_SPLAT_CONTRACT_TRIAL", DEFAULT_CONTRACT_TRIAL)
        cls.bridge = cls.trial / "bridge"

        required = (
            cls.oracle / "manifest.yaml",
            cls.oracle / "action.json",
            cls.prepared_root / "prepared_bed_manifest.json",
            cls.trial / "candidate.json",
            cls.trial / "material_config.json",
            cls.trial / "result.json",
            cls.bridge / "manifest.json",
            cls.bridge / "initial_heightmap_m.npy",
            cls.bridge / "loaded_heightmap_m.npy",
            cls.bridge / "residual_heightmap_m.npy",
            cls.bridge / "valid_heightmap_mask.npy",
        )
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise unittest.SkipTest("frozen regression artifacts are unavailable: " + ", ".join(missing))

        cls.oracle_manifest = yaml.safe_load((cls.oracle / "manifest.yaml").read_text(encoding="utf-8"))
        cls.action = json.loads((cls.oracle / "action.json").read_text(encoding="utf-8"))
        cls.prepared_manifest = json.loads(
            (cls.prepared_root / "prepared_bed_manifest.json").read_text(encoding="utf-8")
        )
        cls.bridge_manifest = json.loads((cls.bridge / "manifest.json").read_text(encoding="utf-8"))
        cls.candidate = json.loads((cls.trial / "candidate.json").read_text(encoding="utf-8"))
        cls.material = json.loads((cls.trial / "material_config.json").read_text(encoding="utf-8"))
        cls.result = json.loads((cls.trial / "result.json").read_text(encoding="utf-8"))

    def test_geometry_frame_grid_and_timing_contract(self) -> None:
        expected_heightmap = {
            "axis_order": "rows=y_increasing, columns=x_increasing",
            "units": "m",
            "origin_xy_m": [-0.3, -0.3],
            "spacing_m": 0.005,
            "shape": [121, 121],
        }
        self.assertEqual(self.oracle_manifest["episode_id"], "A0_oracle_guided_offset_5mm_gate6mm_v1")
        self.assertEqual(self.oracle_manifest["coordinate_frame"], "bed")
        self.assertEqual(self.prepared_manifest["coordinate_frame"], "bed")
        self.assertEqual(self.bridge_manifest["coordinate_frame"], "bed")
        for manifest in (self.oracle_manifest, self.prepared_manifest, self.bridge_manifest):
            for key, value in expected_heightmap.items():
                self.assertEqual(manifest["heightmap"][key], value)

        self.assertEqual(self.action["mass_kg"], 1.5)
        self.assertEqual(self.action["center_xy_m"], [0.0, 0.005])
        self.assertEqual(self.action["radius_m"], 0.073025)
        self.assertEqual(self.action["height_m"], 0.0508)
        self.assertEqual(self.action["removal"], "remove_body")

        convergence = self.oracle_manifest["chrono"]["loading_convergence"]
        self.assertTrue(convergence["accepted"])
        self.assertAlmostEqual(convergence["accepted_time_s"], 3.595, places=12)
        self.assertAlmostEqual(convergence["linear_speed_threshold_mps"], 0.006)
        self.assertAlmostEqual(convergence["angular_speed_threshold_radps"], 0.01)
        self.assertAlmostEqual(convergence["hold_time_s"], 0.10)
        self.assertAlmostEqual(self.oracle_manifest["chrono"]["residual_recovery"]["fixed_duration_s"], 0.25)

        timing = self.bridge_manifest["timing"]
        self.assertAlmostEqual(timing["loaded_max_time_s"], 3.595)
        self.assertTrue(timing["loaded_run_full_duration"])
        self.assertAlmostEqual(timing["post_max_time_s"], 0.25)
        self.assertEqual(timing["post_observation_times_s"], [0.25])

    def test_prepared_bed_and_candidate_contract(self) -> None:
        prepared = self.prepared_manifest
        settling = prepared["settling"]
        metric_bed = prepared["metric_bed"]
        self.assertTrue(prepared["accepted"])
        self.assertEqual(Path(prepared["source_chrono_episode"]).resolve(), self.oracle)
        self.assertEqual(metric_bed["particle_count"], 307461)
        self.assertAlmostEqual(metric_bed["particle_spacing_m"], 0.005)
        self.assertAlmostEqual(settling["particle_size_m"], 0.005)
        self.assertEqual(settling["n_grid"], 128)
        self.assertAlmostEqual(settling["dt_s"], 0.0005)
        self.assertTrue(settling["enable_cpic"])
        self.assertAlmostEqual(settling["geostatic_stress_scale"], 1.0)
        self.assertLessEqual(settling["final_particle_speed_p99_mps"], settling["threshold_mps"])
        self.assertLessEqual(prepared["surface_match"]["rmse_m"], prepared["surface_match"]["rmse_tolerance_m"])
        self.assertLessEqual(
            prepared["surface_match"]["max_abs_m"], prepared["surface_match"]["max_abs_tolerance_m"]
        )

        expected_candidate = {
            "E_pa": 20000.0,
            "phi_deg": 18.149,
            "nu": 0.100004,
            "particle_spacing_m": 0.005,
            "particle_size_ratio": 1.0,
            "particle_size_m": 0.005,
        }
        for key, expected in expected_candidate.items():
            self.assertAlmostEqual(self.candidate[key], expected)
            self.assertAlmostEqual(self.result["candidate"][key], expected)
        self.assertAlmostEqual(self.material["E"], expected_candidate["E_pa"])
        self.assertAlmostEqual(self.material["friction_angle"], expected_candidate["phi_deg"])
        self.assertAlmostEqual(self.material["nu"], expected_candidate["nu"])
        # The retained pre-regression material file inherited a stale n64
        # display value, while the prepared-bed manifest and CLI enforced
        # n128.  New trials persist the resolved grid and timestep explicitly.
        runtime = self.bridge_manifest.get("genesis_runtime")
        if runtime is not None:
            self.assertEqual(runtime["backend"], "cuda")
            self.assertEqual(runtime["n_grid"], 128)
            self.assertAlmostEqual(runtime["dt_s"], 0.0005)
            self.assertAlmostEqual(runtime["particle_spacing_m"], 0.005)
            self.assertAlmostEqual(runtime["particle_size_m"], 0.005)
            self.assertTrue(runtime["enable_cpic"])
            self.assertAlmostEqual(runtime["geostatic_stress_scale"], 1.0)
            self.assertEqual(self.material["n_grid"], runtime["n_grid"])
            self.assertAlmostEqual(self.material["substep_dt"], runtime["dt_s"])

        initialization = self.bridge_manifest["candidate_initialization"]
        stability = initialization["no_action_stability"]
        self.assertLessEqual(initialization["h0_rmse_m"], 0.005)
        self.assertLessEqual(initialization["h0_max_abs_m"], 0.010)
        self.assertEqual(initialization["h0_valid_cells"], 14161)
        self.assertLessEqual(stability["surface_change_rmse_m"], stability["rmse_tolerance_m"])
        self.assertLessEqual(stability["surface_change_max_abs_m"], stability["max_abs_tolerance_m"])

    def test_saved_maps_reproduce_masks_metrics_and_objective(self) -> None:
        oracle_initial = np.load(self.oracle / "initial_heightmap_m.npy")
        oracle_loaded = np.load(self.oracle / "loaded_heightmap_m.npy")
        oracle_residual = np.load(self.oracle / "residual_heightmap_m.npy")
        oracle_valid = np.load(self.oracle / "valid_heightmap_mask.npy").astype(bool)
        genesis_initial = np.load(self.bridge / "initial_heightmap_m.npy")
        genesis_loaded = np.load(self.bridge / "loaded_heightmap_m.npy")
        genesis_residual = np.load(self.bridge / "residual_heightmap_m.npy")
        genesis_valid = np.load(self.bridge / "valid_heightmap_mask.npy").astype(bool)

        expected_shape = (121, 121)
        for array in (
            oracle_initial,
            oracle_loaded,
            oracle_residual,
            oracle_valid,
            genesis_initial,
            genesis_loaded,
            genesis_residual,
            genesis_valid,
        ):
            self.assertEqual(array.shape, expected_shape)

        common_valid = oracle_valid & genesis_valid
        self.assertEqual(int(np.count_nonzero(oracle_valid)), 14161)
        self.assertEqual(int(np.count_nonzero(common_valid)), self.result["common_valid_cells"])
        self.assertAlmostEqual(
            np.count_nonzero(common_valid) / np.count_nonzero(oracle_valid),
            self.result["common_valid_fraction"],
        )
        np.testing.assert_array_equal(np.load(self.bridge / "common_valid_mask.npy").astype(bool), common_valid)
        for array in (oracle_initial, oracle_loaded, oracle_residual, genesis_initial, genesis_loaded, genesis_residual):
            self.assertTrue(np.all(np.isfinite(array[common_valid])))

        loaded_error = (genesis_loaded - genesis_initial) - (oracle_loaded - oracle_initial)
        residual_error = (genesis_residual - genesis_initial) - (oracle_residual - oracle_initial)
        loaded_rmse = float(np.sqrt(np.mean(loaded_error[common_valid] ** 2)))

        heightmap = self.oracle_manifest["heightmap"]
        rows, columns = expected_shape
        xs = float(heightmap["origin_xy_m"][0]) + np.arange(columns) * float(heightmap["spacing_m"])
        ys = float(heightmap["origin_xy_m"][1]) + np.arange(rows) * float(heightmap["spacing_m"])
        grid_x, grid_y = np.meshgrid(xs, ys, indexing="xy")
        center_x, center_y = self.action["center_xy_m"]
        footprint = (grid_x - center_x) ** 2 + (grid_y - center_y) ** 2 <= self.action["radius_m"] ** 2
        footprint_valid = common_valid & footprint
        residual_footprint_rmse = float(np.sqrt(np.mean(residual_error[footprint_valid] ** 2)))
        objective = loaded_rmse + 0.5 * residual_footprint_rmse

        self.assertEqual(int(np.count_nonzero(footprint_valid)), self.result["residual_footprint_cells"])
        serialization_tolerance_m = 1.0e-9
        self.assertAlmostEqual(
            loaded_rmse, self.result["loaded_rmse_m"], delta=serialization_tolerance_m
        )
        self.assertAlmostEqual(
            residual_footprint_rmse,
            self.result["residual_footprint_rmse_m"],
            delta=serialization_tolerance_m,
        )
        self.assertAlmostEqual(
            objective, self.result["objective_m"], delta=serialization_tolerance_m
        )
        self.assertTrue(self.result["valid"])
        self.assertEqual(self.result["phase_acceptance"]["loaded"]["mode"], "fixed_duration")
        self.assertEqual(self.result["phase_acceptance"]["post_removal"]["mode"], "fixed_observation")


class ChronoGenesisRepeatabilityTest(unittest.TestCase):
    def test_incumbent_forward_replay_is_within_frozen_tolerances(self) -> None:
        reference = configured_path("TERA_SPLAT_REFERENCE_TRIAL", DEFAULT_REPEAT_REFERENCE)
        repeat = configured_path("TERA_SPLAT_REPEAT_TRIAL", DEFAULT_REPEAT_TRIAL)
        if not (reference / "result.json").is_file() or not (repeat / "result.json").is_file():
            self.skipTest("reference and repeat trial artifacts are both required")

        reference_result = json.loads((reference / "result.json").read_text(encoding="utf-8"))
        repeat_result = json.loads((repeat / "result.json").read_text(encoding="utf-8"))
        self.assertTrue(reference_result["valid"])
        self.assertTrue(repeat_result["valid"])
        self.assertEqual(reference_result["candidate"], repeat_result["candidate"])
        self.assertEqual(reference_result["common_valid_cells"], repeat_result["common_valid_cells"])
        self.assertEqual(reference_result["phase_acceptance"], repeat_result["phase_acceptance"])

        # These bounds are far below the current inter-candidate separation.
        self.assertLessEqual(abs(repeat_result["objective_m"] - reference_result["objective_m"]), 2.0e-5)
        self.assertLessEqual(abs(repeat_result["loaded_rmse_m"] - reference_result["loaded_rmse_m"]), 2.0e-6)
        self.assertLessEqual(
            abs(
                repeat_result["residual_footprint_rmse_m"]
                - reference_result["residual_footprint_rmse_m"]
            ),
            2.0e-5,
        )

        reference_bridge = reference / "bridge"
        repeat_bridge = repeat / "bridge"
        reference_valid = np.load(reference_bridge / "valid_heightmap_mask.npy").astype(bool)
        repeat_valid = np.load(repeat_bridge / "valid_heightmap_mask.npy").astype(bool)
        np.testing.assert_array_equal(reference_valid, repeat_valid)
        for name in ("initial_heightmap_m.npy", "loaded_heightmap_m.npy", "residual_heightmap_m.npy"):
            difference = np.abs(np.load(repeat_bridge / name) - np.load(reference_bridge / name))
            values = difference[reference_valid]
            self.assertLessEqual(float(np.quantile(values, 0.99)), 2.0e-5)
            # A few upper-envelope particles can cross a discrete projection
            # bin between CUDA runs.  Bound that sparse effect separately from
            # the robust p99 and objective tolerances above.
            self.assertLessEqual(int(np.count_nonzero(values > 1.0e-3)), 3)
            self.assertLessEqual(float(np.max(values)), 1.5e-2)


if __name__ == "__main__":
    unittest.main()

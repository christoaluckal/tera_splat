from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_phase0_residual_pilot.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("run_phase0_residual_pilot", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ResidualPilotTests(unittest.TestCase):
    def test_radial_taper_has_bounded_support(self) -> None:
        radius = np.asarray([0.0, 1.5, 1.75, 2.0, 2.1])
        taper = MODULE.radial_taper(radius)
        np.testing.assert_allclose(taper, [1.0, 1.0, 0.5, 0.0, 0.0], atol=1.0e-12)

    def test_small_mlp_learns_bounded_synthetic_residual(self) -> None:
        grid = np.linspace(-1.0, 1.0, 21)
        x, y = np.meshgrid(grid, grid)
        features = np.column_stack(
            (
                x.ravel(),
                y.ravel(),
                np.sqrt(x.ravel() ** 2 + y.ravel() ** 2),
            )
        )
        target = 0.004 * x.ravel() - 0.002 * y.ravel()
        taper = np.ones(target.shape)
        model, _ = MODULE.fit_model(
            features,
            target,
            taper,
            np.ones(target.shape),
            hidden_width=12,
            epochs=1200,
            learning_rate=0.01,
            l2=1.0e-6,
            max_correction_m=0.02,
            seed=7,
        )
        prediction = MODULE.predict(model, features, taper)
        self.assertLess(float(np.sqrt(np.mean((prediction - target) ** 2))), 2.0e-4)
        self.assertLessEqual(float(np.max(np.abs(prediction))), 0.02)

    def test_particle_lift_preserves_order_and_tapers_with_depth(self) -> None:
        manifest = {
            "heightmap": {
                "shape": [3, 3],
                "spacing_m": 1.0,
                "origin_xy_m": [0.0, 0.0],
            }
        }
        surface = np.zeros((3, 3), dtype=float)
        correction = np.full((3, 3), 0.01, dtype=float)
        points = np.asarray([[1.0, 1.0, 0.0], [1.0, 1.0, -0.02], [1.0, 1.0, -0.2]])
        corrected, displacement = MODULE.lift_to_particles(
            points, surface, correction, manifest, depth_scale_m=0.02
        )
        np.testing.assert_allclose(corrected[:, :2], points[:, :2])
        self.assertAlmostEqual(float(displacement[0]), 0.01, places=7)
        self.assertGreater(float(displacement[1]), 0.0)
        self.assertLess(float(displacement[1]), float(displacement[0]))
        self.assertEqual(float(displacement[2]), 0.0)

    def test_split_policy_keeps_whole_positions_out_of_training(self) -> None:
        plan = {
            "episode_split": {
                "policy": "position-held-out",
                "train": ["center_f031n", "xplus100_f031n", "xminus100_f031n"],
                "validation": ["yplus100_f031n"],
                "test": ["yminus100_f031n"],
            }
        }
        self.assertEqual(MODULE.split_for_case(plan, "yplus100_f031n"), "validation")
        self.assertNotIn("yplus100_f031n", plan["episode_split"]["train"])
        self.assertNotIn("yminus100_f031n", plan["episode_split"]["train"])


if __name__ == "__main__":
    unittest.main()

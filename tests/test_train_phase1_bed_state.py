#!/usr/bin/env python3
"""Unit tests for Phase 1 normalization, loss, and training locks."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "train_phase1_bed_state.py"
spec = importlib.util.spec_from_file_location("train_phase1_bed_state", SCRIPT_PATH)
assert spec and spec.loader
trainer = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = trainer
spec.loader.exec_module(trainer)


class Phase1TrainingTests(unittest.TestCase):
    def test_training_config_locks_models_seeds_and_train_only_normalization(self) -> None:
        config = trainer.load_config(trainer.DEFAULT_CONFIG)
        self.assertEqual(tuple(config["models"]), trainer.MODEL_VARIANTS)
        self.assertEqual(config["normalization"]["fit_split"], "train")
        self.assertEqual(config["optimization"]["training_seeds"], [20261022, 20261023, 20261024])
        self.assertTrue(config["controls"]["model_selection_before_test_unlock"])
        self.assertEqual(config["uncertainty_calibration"]["fit_split"], "validation")
        self.assertEqual(config["uncertainty_calibration"]["nominal_coverage"], 0.9)

    def test_boundary_taper_is_zero_outside_and_one_interior(self) -> None:
        valid = np.ones((9, 9), dtype=bool)
        valid[0, :] = False
        taper = trainer.boundary_taper(valid, 3)
        self.assertTrue(np.all(taper[0] == 0))
        self.assertTrue(np.all((taper >= 0) & (taper <= 1)))
        self.assertEqual(float(taper[5, 5]), 1.0)
        self.assertLess(float(taper[1, 4]), float(taper[4, 4]))

    def test_global_vector_rejects_phase_action_drift(self) -> None:
        inputs = {
            "action_phase": np.asarray([[0, 0, 31, 0], [0, 0, 32, 1]], dtype=np.float32),
            "soil_parameters": np.asarray([800000, 28], dtype=np.float32),
        }
        with self.assertRaisesRegex(ValueError, "action identity changed"):
            trainer.global_vector(inputs)

    def test_no_action_channels_represent_physical_zero_before_normalization(self) -> None:
        shape = (5, 7)
        inputs = {
            name: np.full(shape, index + 1.0, dtype=np.float32)
            for index, name in enumerate(trainer.SPATIAL_CHANNELS)
        }
        means = np.linspace(-2.0, 3.0, len(trainer.SPATIAL_CHANNELS), dtype=np.float32)
        stds = np.linspace(0.5, 2.0, len(trainer.SPATIAL_CHANNELS), dtype=np.float32)
        normalization = {
            "spatial_mean": means.tolist(),
            "spatial_std": stds.tolist(),
        }
        normalized = trainer.normalized_spatial_arrays(
            inputs, normalization, no_action=True
        )
        recovered = normalized * stds[:, None, None] + means[:, None, None]
        retained = set(trainer.NO_ACTION_RETAINED_SPATIAL_CHANNELS)
        for index, name in enumerate(trainer.SPATIAL_CHANNELS):
            expected = inputs[name] if name in retained else np.zeros(shape)
            np.testing.assert_allclose(recovered[index], expected, atol=1.0e-6)

    def test_normalization_payload_and_file_hashes_are_unambiguous(self) -> None:
        value = {"schema_version": 1, "values": [1.0, 2.0]}
        self.assertNotEqual(
            trainer.canonical_sha256(value), trainer.serialized_json_sha256(value)
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "normalization.json"
            trainer.write_json(path, value)
            self.assertEqual(
                trainer.sha256_file(path), trainer.serialized_json_sha256(value)
            )

    def test_conformal_multiplier_uses_declared_higher_quantile(self) -> None:
        errors = np.asarray([0.1, 0.2, 0.3, 0.4])
        deviations = np.asarray([0.1, 0.1, 0.1, 0.1])
        multiplier = trainer.conformal_multiplier(errors, deviations, 0.75)
        self.assertEqual(multiplier, 4.0)
        coverage = np.mean(errors <= multiplier * deviations)
        self.assertGreaterEqual(coverage, 0.75)

    def test_multiterm_loss_is_finite_and_differentiable(self) -> None:
        config = trainer.load_config(trainer.DEFAULT_CONFIG)
        network = trainer.Phase1BedStateUNet("H1", base_channels=16)
        torch.nn.init.normal_(network.mean_head.weight, std=1.0e-3)
        batch_size, size = 2, 33
        spatial = torch.randn(batch_size, len(trainer.SPATIAL_CHANNELS), size, size)
        condition = torch.randn(batch_size, len(trainer.GLOBAL_FEATURES))
        initial = torch.randn(batch_size, 1, size, size) * 0.002
        base = initial.repeat(1, 2, 1, 1)
        taper = torch.ones(batch_size, 1, size, size)
        scale = torch.tensor([0.02, 0.02])
        result = network(spatial, condition, base, scale, taper)
        batch = {
            "spatial": spatial,
            "no_action_spatial": spatial.clone(),
            "global_condition": condition,
            "no_action_global_condition": condition.clone(),
            "initial": initial,
            "target": base + torch.randn_like(base) * 0.001,
            "valid": torch.ones(batch_size, 1, size, size, dtype=torch.bool),
            "footprint": torch.ones(batch_size, 1, size, size, dtype=torch.bool),
            "twice_radius": torch.ones(batch_size, 1, size, size, dtype=torch.bool),
            "taper": taper,
            "relative_x": torch.zeros(batch_size, 1, size, size),
            "relative_y": torch.zeros(batch_size, 1, size, size),
        }
        loss, parts = trainer.phase1_loss(network, result, batch, config["loss_weights"], scale)
        loss.backward()
        self.assertTrue(torch.isfinite(loss))
        self.assertEqual(set(parts), set(config["loss_weights"]))
        self.assertEqual(float(parts["particle_surface_reproduction"]), 0.0)
        self.assertEqual(float(parts["particle_state_preservation"]), 0.0)
        self.assertEqual(config["loss_weights"]["particle_surface_reproduction"], 0.0)
        self.assertIn("particle_surface_reproduction", config["hard_constraints"])

    def test_plan_gate_refuses_missing_bulk_summary(self) -> None:
        config = trainer.load_config(trainer.DEFAULT_CONFIG)
        with tempfile.TemporaryDirectory() as directory:
            modified = json.loads(json.dumps(config))
            modified["bulk_summary"] = str(Path(directory) / "absent.json")
            with self.assertRaisesRegex(RuntimeError, "bulk summary is absent"):
                trainer.require_bulk_summary(modified)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Focused tests for the bulk-gated successor model and trainer adapter."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
MODEL_SCRIPT = REPO_ROOT / "scripts" / "phase1_one_action_successor_model.py"
TRAIN_SCRIPT = REPO_ROOT / "scripts" / "train_phase1_one_action_successor.py"
CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_training_v1.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


MODEL = load_module("phase1_successor_model", MODEL_SCRIPT)
TRAIN = load_module("phase1_successor_train", TRAIN_SCRIPT)


def config() -> dict:
    return TRAIN.load_config(CONFIG)


def passing_bulk_summary() -> dict:
    episodes = {
        f"episode_{index:03d}": {
            "episode_id": f"episode_{index:03d}",
            "split": "train" if index < 48 else "validation",
            "complete": True,
            "admitted": True,
        }
        for index in range(64)
    }
    return {
        "status": "passed",
        "training_plan_freeze_permitted": True,
        "test_or_protected_sensitivity_permitted": False,
        "counts": {
            "total": 64,
            "train": 48,
            "validation": 16,
            "test": 0,
            "protected_sensitivity": 0,
        },
        "checks": {"test_and_sensitivity_targets_unopened": True},
        "identity": {
            "test_lock_sha256": TRAIN.EXPECTED_TEST_LOCK_SHA256,
            "sensitivity_lock_sha256": TRAIN.EXPECTED_SENSITIVITY_LOCK_SHA256,
        },
        "episodes": episodes,
    }


class SuccessorTrainingTests(unittest.TestCase):
    def test_config_freezes_core_selection_optional_ablations_and_three_seeds(self) -> None:
        cfg = config()
        self.assertEqual(tuple(cfg["models"]), MODEL.MODEL_VARIANTS)
        self.assertEqual(tuple(cfg["selection_pool"]), MODEL.SELECTION_VARIANTS)
        self.assertEqual(
            tuple(cfg["optional_ablation_pool"]),
            MODEL.OPTIONAL_ABLATION_VARIANTS,
        )
        self.assertEqual(
            cfg["optimization"]["training_seeds"],
            [20261101, 20261102, 20261103],
        )
        self.assertEqual(cfg["normalization"]["fit_split"], "train")
        self.assertEqual(
            cfg["uncertainty_calibration"]["fit_split"], "validation"
        )
        self.assertTrue(
            cfg["controls"]["model_selection_before_test_or_sensitivity_unlock"]
        )

    def test_all_variants_have_identical_capacity_in_the_frozen_range(self) -> None:
        counts = {
            name: MODEL.parameter_count(MODEL.SuccessorBedStateUNet(name))
            for name in MODEL.MODEL_VARIANTS
        }
        self.assertEqual(len(set(counts.values())), 1)
        count = next(iter(counts.values()))
        self.assertGreaterEqual(count, 100_000)
        self.assertLessEqual(count, 1_000_000)

    def test_variant_masks_separate_all_declared_input_families(self) -> None:
        active = {
            name: {
                MODEL.SPATIAL_CHANNELS[index]
                for index in MODEL.variant_channel_indices(name)
            }
            for name in MODEL.MODEL_VARIANTS
        }
        self.assertTrue(set(MODEL.NEWTON_CHANNELS).isdisjoint(active["D0"]))
        self.assertTrue(set(MODEL.NEWTON_CHANNELS).issubset(active["R0"]))
        self.assertTrue(set(MODEL.ROBOTICS_CHANNELS).isdisjoint(active["R0"]))
        self.assertTrue(set(MODEL.ROBOTICS_CHANNELS).issubset(active["R1"]))
        self.assertTrue(set(MODEL.STRESS_CHANNELS).isdisjoint(active["R1"]))
        self.assertTrue(set(MODEL.ELASTIC_CHANNELS).isdisjoint(active["R1"]))
        self.assertTrue(set(MODEL.STRESS_CHANNELS).issubset(active["R2S"]))
        self.assertTrue(set(MODEL.ELASTIC_CHANNELS).isdisjoint(active["R2S"]))
        self.assertTrue(set(MODEL.ELASTIC_CHANNELS).issubset(active["R2E"]))
        self.assertTrue(set(MODEL.STRESS_CHANNELS).isdisjoint(active["R2E"]))
        self.assertFalse(any("plastic" in name for name in MODEL.SPATIAL_CHANNELS))

    def test_four_feature_conditioning_excludes_fixed_friction(self) -> None:
        self.assertEqual(
            MODEL.GLOBAL_FEATURES,
            ("center_x_m", "center_y_m", "normal_force_n", "bekker_kphi"),
        )
        inputs = {
            "action_phase": np.asarray(
                [[0.01, -0.02, 38.0, 0.0], [0.01, -0.02, 38.0, 1.0]],
                dtype=np.float32,
            ),
            "soil_parameters": np.asarray([1.75e6], dtype=np.float32),
        }
        np.testing.assert_allclose(
            TRAIN.global_vector(inputs),
            np.asarray([0.01, -0.02, 38.0, 1.75e6], dtype=np.float64),
        )
        changed = copy.deepcopy(inputs)
        changed["soil_parameters"] = np.asarray(
            [1.75e6, 30.0], dtype=np.float32
        )
        with self.assertRaisesRegex(ValueError, "global tensor shape"):
            TRAIN.global_vector(changed)

    def test_zero_initialized_heads_reproduce_each_declared_base(self) -> None:
        batch, size = 1, 17
        spatial = torch.randn(
            batch, len(MODEL.SPATIAL_CHANNELS), size, size
        )
        condition = torch.randn(batch, len(MODEL.GLOBAL_FEATURES))
        initial = torch.randn(batch, 1, size, size) * 0.002
        newton = initial.repeat(1, 2, 1, 1) + torch.randn(
            batch, 2, size, size
        ) * 0.001
        taper = torch.ones(batch, 1, size, size)
        scale = torch.tensor([0.02, 0.03])
        for variant in MODEL.MODEL_VARIANTS:
            with self.subTest(variant=variant):
                network = MODEL.SuccessorBedStateUNet(variant)
                base = initial.repeat(1, 2, 1, 1) if variant == "D0" else newton
                result = network(spatial, condition, base, scale, taper)
                torch.testing.assert_close(result["height_m"], base)
                torch.testing.assert_close(
                    result["correction_m"], torch.zeros_like(base)
                )
                self.assertTrue(torch.isfinite(result["log_variance_m2"]).all())

    def test_trainer_adapter_rebinds_the_proven_pipeline(self) -> None:
        self.assertEqual(TRAIN.base.MODEL_VARIANTS, MODEL.MODEL_VARIANTS)
        self.assertEqual(TRAIN.base.GLOBAL_FEATURES, MODEL.GLOBAL_FEATURES)
        self.assertIs(TRAIN.base.Phase1BedStateUNet, TRAIN.SuccessorBedStateUNet)
        self.assertEqual(
            tuple(TRAIN.base.VARIANT_CONTRACTS), tuple(MODEL.VARIANT_CONTRACTS)
        )
        for name in MODEL.MODEL_VARIANTS:
            adapted = TRAIN.base.VARIANT_CONTRACTS[name]
            expected = MODEL.VARIANT_CONTRACTS[name]
            self.assertEqual(adapted.spatial_channels, expected.spatial_channels)
            self.assertEqual(adapted.global_features, expected.global_features)
            self.assertEqual(adapted.base_state, expected.base_state)

    def test_training_plan_refuses_absent_bulk_summary(self) -> None:
        cfg = config()
        with tempfile.TemporaryDirectory() as directory:
            cfg["bulk_summary"] = str(Path(directory) / "absent.json")
            with self.assertRaisesRegex(RuntimeError, "bulk summary is absent"):
                TRAIN.require_bulk_summary(cfg)

    def test_bulk_gate_requires_both_protected_permissions_false(self) -> None:
        cfg = config()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bulk_summary.json"
            path.write_text(json.dumps(passing_bulk_summary()), encoding="utf-8")
            cfg["bulk_summary"] = str(path)
            self.assertEqual(len(TRAIN.require_bulk_summary(cfg)["episodes"]), 64)
            changed = passing_bulk_summary()
            changed["test_or_protected_sensitivity_permitted"] = True
            path.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaisesRegex(
                RuntimeError, "protected-target permission changed"
            ):
                TRAIN.require_bulk_summary(cfg)

    def test_source_manifest_resolves_without_creating_training_plan(self) -> None:
        sources = TRAIN.source_paths(CONFIG)
        self.assertTrue(sources)
        self.assertTrue(all(path.is_file() for path in sources.values()))
        self.assertFalse(TRAIN.plan_path(config()).exists())


if __name__ == "__main__":
    unittest.main()

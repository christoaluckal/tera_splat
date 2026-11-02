#!/usr/bin/env python3
"""Pure tests for the protected successor prediction adapter."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "predict_phase1_one_action_successor.py"
CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_evaluation_v1.json"


def load_module():
    spec = importlib.util.spec_from_file_location("successor_predict", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


prediction = load_module()


def config() -> dict:
    return prediction.evaluation.load_config(CONFIG)


def inputs() -> dict[str, np.ndarray]:
    return {
        "initial_height_m": np.zeros((3, 3), dtype=np.float32),
        "valid_support": np.ones((3, 3), dtype=bool),
        "action_footprint": np.ones((3, 3), dtype=bool),
        "action_signed_distance_m": np.zeros((3, 3), dtype=np.float32),
    }


class SuccessorPredictionTests(unittest.TestCase):
    def test_parameter_shuffle_is_deterministic_derangement(self) -> None:
        identities = [f"episode_{index:02d}" for index in range(24)]
        first = prediction.parameter_shuffle_mapping(identities, 11)
        second = prediction.parameter_shuffle_mapping(reversed(identities), 11)
        self.assertEqual(first, second)
        self.assertEqual(set(first), set(identities))
        self.assertEqual(set(first.values()), set(identities))
        self.assertTrue(all(source != donor for source, donor in first.items()))

    def test_rmse_and_coverage_use_both_frozen_regions(self) -> None:
        source = inputs()
        target = np.zeros((2, 3, 3), dtype=np.float32)
        predicted = np.full((2, 3, 3), 0.002, dtype=np.float32)
        metrics = prediction.rmse_tree(predicted, target, source)
        for checkpoint in prediction.CHECKPOINTS:
            self.assertEqual(set(metrics[checkpoint]), set(prediction.REGIONS))
            self.assertAlmostEqual(metrics[checkpoint]["footprint"], 0.002)
        coverage = prediction.coverage_tree(
            predicted,
            np.full_like(predicted, 0.002),
            target,
            source,
            {"loaded_multiplier": 1.0, "post_unload_multiplier": 1.0},
        )
        self.assertTrue(
            all(value == 1.0 for phase in coverage.values() for value in phase.values())
        )

    def test_sensitivity_direction_uses_24_adjacent_geometry_comparisons(self) -> None:
        cfg = config()
        episodes = []
        inputs_by_id = {}
        targets_by_id = {}
        predictions_by_id = {}
        for force_index, force in enumerate((30.65625, 45.984375)):
            for kphi_index, kphi in enumerate((1.5e6, 1.75e6, 2.0e6)):
                episode_id = f"force_{force_index}_kphi_{kphi_index}"
                episodes.append(
                    {
                        "episode_id": episode_id,
                        "normal_force_n": force,
                        "soil_parameters": {"bekker_kphi": kphi},
                    }
                )
                source = inputs()
                depth = 0.001 + 0.001 * kphi_index + 0.0002 * force_index
                target = np.full((2, 3, 3), -depth, dtype=np.float32)
                inputs_by_id[episode_id] = source
                targets_by_id[episode_id] = target
                predictions_by_id[episode_id] = {
                    model: np.array(target, copy=True)
                    for model in prediction.evaluation.LEARNED_MODELS
                }
        summary = prediction.sensitivity_direction_summary(
            cfg,
            episodes,
            inputs_by_id,
            targets_by_id,
            predictions_by_id,
        )
        for model in prediction.evaluation.LEARNED_MODELS:
            self.assertEqual(summary[model]["eligible_comparisons"], 24)
            self.assertEqual(summary[model]["direction_fraction"], 1.0)

    def test_prediction_refuses_before_protected_dataset_admission(self) -> None:
        cfg = config()
        with tempfile.TemporaryDirectory() as directory:
            cfg["execution"]["output_root"] = str(Path(directory) / "evaluation")
            with mock.patch.object(
                prediction.evaluation,
                "protected_artifact_identity",
                return_value={},
            ):
                with self.assertRaisesRegex(RuntimeError, "dataset summary"):
                    prediction.predict(cfg, {})

    def test_completed_prediction_payload_is_idempotent_and_revalidated(self) -> None:
        cfg = config()
        with tempfile.TemporaryDirectory() as directory:
            cfg["execution"]["output_root"] = str(Path(directory) / "evaluation")
            plan = {}
            prediction.evaluation.write_json(
                prediction.evaluation.plan_path(cfg), plan
            )
            payload = {
                "status": "protected_predictions_complete",
                "evaluation_plan_sha256": prediction.evaluation.sha256_file(
                    prediction.evaluation.plan_path(cfg)
                ),
            }
            destination = (
                prediction.evaluation.output_root(cfg)
                / "protected_prediction_results.json"
            )
            prediction.evaluation.write_json(destination, payload)
            with (
                mock.patch.object(
                    prediction.evaluation,
                    "protected_artifact_identity",
                    return_value={},
                ),
                mock.patch.object(
                    prediction.evaluation,
                    "prediction_artifact_identity",
                    return_value={},
                ) as verify,
            ):
                self.assertEqual(prediction.predict(cfg, plan), payload)
                verify.assert_called_once()

    def test_evaluation_source_manifest_includes_predictor_and_tests(self) -> None:
        sources = prediction.evaluation.source_paths(CONFIG)
        self.assertIn("protected_predictor", sources)
        self.assertIn("protected_predictor_tests", sources)
        self.assertTrue(all(path.is_file() for path in sources.values()))


if __name__ == "__main__":
    unittest.main()

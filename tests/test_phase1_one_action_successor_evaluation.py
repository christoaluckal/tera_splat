#!/usr/bin/env python3
"""Focused tests for the locked one-action successor evaluation."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "evaluate_phase1_one_action_successor.py"
CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_evaluation_v1.json"
DATASET_PLAN = (
    REPO_ROOT
    / "outputs"
    / "validity_experiment"
    / "newton"
    / "phase1_one_action_successor_contract_v1"
    / "dataset_plan.json"
)


def load_module():
    spec = importlib.util.spec_from_file_location("successor_evaluation", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


evaluation = load_module()


def config() -> dict:
    return evaluation.load_config(CONFIG)


def membership() -> dict:
    return evaluation.selected_membership(
        config(), json.loads(DATASET_PLAN.read_text(encoding="utf-8"))
    )


def metric_tree(value: float) -> dict:
    return {
        checkpoint: {region: value for region in ("footprint", "twice_radius")}
        for checkpoint in ("loaded", "post_unload")
    }


def payload_for(
    cfg: dict,
    plan: dict,
    model_values: dict[str, float],
) -> dict:
    episodes = []
    for episode in plan["episodes"]["test"]:
        controls = {
            model: {
                control: metric_tree(value * 1.10)
                for control in ("kphi_shuffled", "kphi_constant_reference")
            }
            for model, value in model_values.items()
        }
        episodes.append(
            {
                "episode_id": episode["episode_id"],
                "holdout_group": episode["holdout_group"],
                "rmse_m": {
                    "no_deformation": metric_tree(0.010),
                    "raw_newton": metric_tree(0.008),
                    **{model: metric_tree(value) for model, value in model_values.items()},
                },
                "parameter_controls": controls,
                "coverage_fraction": {
                    model: metric_tree(0.90) for model in model_values
                },
            }
        )
    return {
        "status": "protected_predictions_complete",
        "evaluation_plan_sha256": evaluation.sha256_file(
            evaluation.plan_path(cfg)
        ),
        "episodes": episodes,
        "protected_sensitivity": {
            model: {"direction_fraction": 1.0, "eligible_comparisons": 24}
            for model in model_values
        },
    }


class SuccessorEvaluationTests(unittest.TestCase):
    def test_config_freezes_models_metrics_and_joint_unlock(self) -> None:
        cfg = config()
        self.assertEqual(tuple(cfg["models"]["learned"]), evaluation.LEARNED_MODELS)
        self.assertEqual(tuple(cfg["models"]["core_selection_pool"]), evaluation.CORE_MODELS)
        self.assertEqual(
            tuple(cfg["models"]["optional_ablation_pool"]),
            evaluation.OPTIONAL_MODELS,
        )
        self.assertEqual(cfg["membership"]["test"], 24)
        self.assertEqual(cfg["membership"]["protected_sensitivity"], 6)
        self.assertTrue(cfg["membership"]["single_joint_unlock_marker"])
        self.assertTrue(cfg["metrics"]["episode_is_resampling_unit"])
        self.assertEqual(cfg["metrics"]["bootstrap_resamples"], 10_000)
        self.assertEqual(
            cfg["required_bulk_recovery_id"],
            evaluation.EXPECTED_BULK_RECOVERY_ID,
        )
        self.assertEqual(
            cfg["required_identity"]["legacy_bulk_summary_sha256"],
            evaluation.EXPECTED_LEGACY_BULK_SUMMARY_SHA256,
        )

    def test_locked_membership_rechecks_groups_and_sensitivity_grid(self) -> None:
        selected = membership()
        self.assertEqual(len(selected["test"]), 24)
        self.assertEqual(len(selected["protected_sensitivity"]), 6)
        self.assertTrue(
            all(
                item["target_access"] == "locked"
                for rows in selected.values()
                for item in rows
            )
        )
        changed = json.loads(DATASET_PLAN.read_text(encoding="utf-8"))
        changed["episodes"]["test"][0]["target_access"] = "open"
        with self.assertRaisesRegex(ValueError, "membership lock is invalid"):
            evaluation.selected_membership(config(), changed)

    def test_selection_gate_refuses_absent_prerequisites(self) -> None:
        cfg = config()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for key in (
                "successor_contract",
                "dataset_plan",
                "bulk_summary",
                "training_config",
                "training_plan",
                "normalization",
                "selection_summary",
            ):
                cfg[key] = str(root / f"absent_{key}.json")
            with self.assertRaisesRegex(RuntimeError, "prerequisites are absent"):
                evaluation.require_prerequisites(cfg)

    def test_selected_artifacts_bind_card_checkpoint_and_history(self) -> None:
        cfg = config()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            training_config = root / "training.json"
            evaluation.write_json(
                training_config,
                {"execution": {"output_root": str(root / "training")}},
            )
            cfg["training_config"] = str(training_config)
            selected = {}
            for index, variant in enumerate(evaluation.LEARNED_MODELS):
                seed = 100 + index
                model_root = root / "training" / "models" / variant / f"seed_{seed}"
                model_root.mkdir(parents=True)
                checkpoint = model_root / "model.pt"
                history = model_root / "history.json"
                checkpoint.write_bytes(f"{variant}:checkpoint".encode())
                history.write_text("[]\n", encoding="utf-8")
                card = {
                    "variant": variant,
                    "seed": seed,
                    "model_sha256": evaluation.sha256_file(checkpoint),
                    "history_sha256": evaluation.sha256_file(history),
                    "test_targets_opened": False,
                }
                evaluation.write_json(model_root / "model_card.json", card)
                selected[variant] = card
            artifacts = evaluation.selected_artifacts(cfg, {"selected": selected})
            self.assertEqual(set(artifacts), set(evaluation.LEARNED_MODELS))
            checkpoint = root / "training" / "models" / "R1" / "seed_102" / "model.pt"
            checkpoint.write_bytes(b"mutated")
            with self.assertRaisesRegex(RuntimeError, "checkpoint identity changed"):
                evaluation.selected_artifacts(cfg, {"selected": selected})

    def test_unlock_is_joint_idempotent_and_refuses_opened_targets(self) -> None:
        cfg = config()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cfg["execution"]["output_root"] = str(root / "evaluation")
            cfg["execution"]["dataset_output_root"] = str(root / "dataset")
            cfg["execution"]["chrono_output_root"] = str(root / "chrono")
            plan = {
                "selection_summary_sha256": "selection",
                "test_lock_sha256": evaluation.EXPECTED_TEST_LOCK_SHA256,
                "sensitivity_lock_sha256": evaluation.EXPECTED_SENSITIVITY_LOCK_SHA256,
                "episodes": membership(),
            }
            evaluation.write_json(evaluation.plan_path(cfg), plan)
            first = evaluation.unlock_protected(cfg, plan)
            second = evaluation.unlock_protected(cfg, plan)
            self.assertEqual(first, second)
            self.assertEqual(first["test_target_count"], 24)
            self.assertEqual(first["protected_sensitivity_target_count"], 6)
            self.assertFalse(first["targets_opened"])
            evaluation.write_json(evaluation.opened_path(cfg), {"opened": True})
            with self.assertRaisesRegex(RuntimeError, "already been opened"):
                evaluation.unlock_protected(cfg, plan)

    def test_open_marker_precedes_generation_and_report_binds_artifacts(self) -> None:
        cfg = config()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cfg["execution"]["output_root"] = str(root / "evaluation")
            cfg["execution"]["dataset_output_root"] = str(root / "dataset")
            cfg["execution"]["chrono_output_root"] = str(root / "chrono")
            plan = {
                "selection_summary_sha256": "selection",
                "test_lock_sha256": evaluation.EXPECTED_TEST_LOCK_SHA256,
                "sensitivity_lock_sha256": evaluation.EXPECTED_SENSITIVITY_LOCK_SHA256,
                "episodes": membership(),
            }
            evaluation.write_json(evaluation.plan_path(cfg), plan)
            evaluation.unlock_protected(cfg, plan)
            marker = evaluation.mark_protected_opened(cfg, plan)
            self.assertTrue(marker["targets_opened"])
            self.assertEqual(marker, evaluation.require_opened(cfg, plan))
            artifacts = evaluation.protected_artifact_paths(cfg, plan)
            for name, path in artifacts.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                if name.endswith(":episode_summary"):
                    evaluation.write_json(path, {"complete": True, "admitted": True})
                else:
                    path.write_bytes(name.encode())
            identity = evaluation.protected_artifact_identity(cfg, plan)
            self.assertEqual(set(identity), set(artifacts))
            target_name = next(name for name in artifacts if name.endswith(":targets"))
            before = identity[target_name]
            artifacts[target_name].write_bytes(b"mutated")
            after = evaluation.protected_artifact_identity(cfg, plan)
            self.assertNotEqual(before, after[target_name])

    def test_bootstrap_is_whole_episode_and_deterministic(self) -> None:
        first = evaluation.bootstrap_interval(
            [1.0, 2.0, 3.0, 4.0], resamples=500, confidence=0.95, seed=4
        )
        second = evaluation.bootstrap_interval(
            [1.0, 2.0, 3.0, 4.0], resamples=500, confidence=0.95, seed=4
        )
        self.assertEqual(first, second)
        self.assertEqual(first["episode_count"], 4)
        self.assertEqual(first["estimate"], 2.5)

    def _aggregate(self, values: dict[str, float]) -> dict:
        cfg = config()
        cfg["metrics"]["bootstrap_resamples"] = 200
        selected = membership()
        plan = {
            "episodes": selected,
            "episode_ids": {
                split: [item["episode_id"] for item in rows]
                for split, rows in selected.items()
            },
        }
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        cfg["execution"]["output_root"] = str(Path(temporary.name) / "evaluation")
        evaluation.write_json(evaluation.plan_path(cfg), plan)
        return evaluation.aggregate_results(cfg, plan, payload_for(cfg, plan, values))

    def test_claim_routes_to_newton_added_value_when_R1_passes_and_beats_D0(self) -> None:
        report = self._aggregate(
            {"D0": 0.0028, "R0": 0.0025, "R1": 0.0020, "R2S": 0.0017, "R2E": 0.0018}
        )
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["passing_correction_models"], ["R0", "R1"])
        self.assertEqual(report["newton_added_value_models"], ["R0", "R1"])
        self.assertEqual(
            report["claim_route"], "neural_correction_with_newton_added_value"
        )
        self.assertTrue(report["newton_added_value"]["R1"]["passed"])
        self.assertTrue(report["optional_field_value"]["R2S"]["passed"])

    def test_claim_routes_to_correction_without_newton_added_value(self) -> None:
        report = self._aggregate(
            {"D0": 0.0025, "R0": 0.00245, "R1": 0.00240, "R2S": 0.00239, "R2E": 0.00238}
        )
        self.assertEqual(
            report["claim_route"], "neural_correction_without_newton_added_value"
        )
        self.assertFalse(report["newton_added_value"]["R1"]["passed"])
        self.assertFalse(report["optional_field_value"]["R2S"]["passed"])

    def test_claim_routes_to_direct_surrogate_when_corrections_fail(self) -> None:
        report = self._aggregate(
            {"D0": 0.0020, "R0": 0.0060, "R1": 0.0060, "R2S": 0.0060, "R2E": 0.0060}
        )
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["claim_route"], "learned_direct_surrogate")
        self.assertTrue(report["model_pass"]["D0"])
        self.assertFalse(report["model_pass"]["R0"])

    def test_incomplete_sensitivity_blocks_claim_and_added_value(self) -> None:
        cfg = config()
        cfg["metrics"]["bootstrap_resamples"] = 200
        selected = membership()
        plan = {
            "episodes": selected,
            "episode_ids": {
                split: [item["episode_id"] for item in rows]
                for split, rows in selected.items()
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            cfg["execution"]["output_root"] = str(Path(directory) / "evaluation")
            evaluation.write_json(evaluation.plan_path(cfg), plan)
            payload = payload_for(
                cfg,
                plan,
                {"D0": 0.0028, "R0": 0.0060, "R1": 0.0020, "R2S": 0.0017, "R2E": 0.0018},
            )
            payload["protected_sensitivity"]["R1"]["eligible_comparisons"] = 23
            payload["protected_sensitivity"]["R2S"]["direction_fraction"] = 0.0
            report = evaluation.aggregate_results(cfg, plan, payload)
            self.assertFalse(report["model_pass"]["R1"])
            self.assertFalse(report["newton_added_value"]["R1"]["passed"])
            self.assertFalse(report["model_pass"]["R2S"])
            self.assertFalse(report["optional_field_value"]["R2S"]["passed"])
            self.assertEqual(report["claim_route"], "learned_direct_surrogate")

    def test_exact_test_membership_is_required_for_reporting(self) -> None:
        cfg = config()
        cfg["metrics"]["bootstrap_resamples"] = 100
        selected = membership()
        plan = {
            "episodes": selected,
            "episode_ids": {
                split: [item["episode_id"] for item in rows]
                for split, rows in selected.items()
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            cfg["execution"]["output_root"] = str(Path(directory) / "evaluation")
            evaluation.write_json(evaluation.plan_path(cfg), plan)
            payload = payload_for(
                cfg,
                plan,
                {"D0": 0.002, "R0": 0.002, "R1": 0.002, "R2S": 0.002, "R2E": 0.002},
            )
            payload["episodes"].pop()
            with self.assertRaisesRegex(ValueError, "exact 24 test episodes"):
                evaluation.aggregate_results(cfg, plan, payload)

    def test_prediction_artifact_integrity_covers_all_30_members(self) -> None:
        cfg = config()
        selected = membership()
        plan = {
            "episodes": selected,
            "episode_ids": {
                split: [item["episode_id"] for item in rows]
                for split, rows in selected.items()
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cfg["execution"]["dataset_output_root"] = str(root / "dataset")
            declared = {}
            test_ids = set(plan["episode_ids"]["test"])
            payload_rows = []
            sensitivity_summaries = []
            plan_sha = "plan-sha"
            for split in ("test", "protected_sensitivity"):
                for item in selected[split]:
                    episode_id = item["episode_id"]
                    prediction_root = (
                        root / "dataset" / "episodes" / episode_id / "predictions"
                    )
                    prediction_root.mkdir(parents=True)
                    if episode_id in test_ids:
                        summary = prediction_root / "successor_prediction_summary.json"
                        archive = prediction_root / "successor_predictions.npz"
                    else:
                        summary = prediction_root / "successor_sensitivity_prediction_summary.json"
                        archive = prediction_root / "successor_sensitivity_predictions.npz"
                    archive.write_bytes(f"{episode_id}:archive".encode())
                    if episode_id in test_ids:
                        row = {
                            "episode_id": episode_id,
                            "holdout_group": item["holdout_group"],
                        }
                        payload_rows.append(row)
                        summary_value = {
                            **row,
                            "evaluation_plan_sha256": plan_sha,
                            "prediction_archive_sha256": evaluation.sha256_file(archive),
                        }
                    else:
                        kphi_index = {
                            1500000.0: 1.0,
                            1750000.0: 2.0,
                            2000000.0: 3.0,
                        }[float(item["soil_parameters"]["bekker_kphi"])]
                        phase_quantities = {
                            checkpoint: {
                                "peak_depression_m": 0.001 * kphi_index,
                                "mean_depression_m": 0.0005 * kphi_index,
                                "displaced_volume_m3": 1.0e-7 * kphi_index,
                            }
                            for checkpoint in ("loaded", "post_unload")
                        }
                        summary_value = {
                            "episode_id": episode_id,
                            "normal_force_n": item["normal_force_n"],
                            "bekker_kphi": item["soil_parameters"]["bekker_kphi"],
                            "evaluation_plan_sha256": plan_sha,
                            "prediction_archive_sha256": evaluation.sha256_file(archive),
                            "used_for_training_normalization_calibration_or_selection": False,
                            "directional_quantities": {
                                "target": phase_quantities,
                                "predictions": {
                                    model: phase_quantities
                                    for model in evaluation.LEARNED_MODELS
                                },
                            },
                        }
                        sensitivity_summaries.append(summary_value)
                    evaluation.write_json(summary, summary_value)
                    declared[episode_id] = {
                        "summary_sha256": evaluation.sha256_file(summary),
                        "archive_sha256": evaluation.sha256_file(archive),
                    }
            payload = {
                "evaluation_plan_sha256": plan_sha,
                "episodes": payload_rows,
                "protected_sensitivity": evaluation.sensitivity_from_prediction_summaries(
                    cfg, sensitivity_summaries
                ),
                "prediction_artifacts": declared,
            }
            self.assertEqual(
                evaluation.prediction_artifact_identity(cfg, plan, payload),
                declared,
            )
            changed = copy.deepcopy(payload)
            changed["episodes"][0]["holdout_group"] = "mutated"
            with self.assertRaisesRegex(RuntimeError, "payload row changed"):
                evaluation.prediction_artifact_identity(cfg, plan, changed)
            changed = copy.deepcopy(payload)
            changed["protected_sensitivity"]["D0"]["direction_fraction"] = 0.0
            with self.assertRaisesRegex(RuntimeError, "sensitivity payload changed"):
                evaluation.prediction_artifact_identity(cfg, plan, changed)
            first_id = plan["episode_ids"]["test"][0]
            path = (
                root
                / "dataset"
                / "episodes"
                / first_id
                / "predictions"
                / "successor_predictions.npz"
            )
            path.write_bytes(b"mutated")
            with self.assertRaisesRegex(RuntimeError, "identity changed"):
                evaluation.prediction_artifact_identity(cfg, plan, payload)


if __name__ == "__main__":
    unittest.main()

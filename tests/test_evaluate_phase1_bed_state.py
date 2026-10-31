#!/usr/bin/env python3
"""Tests for the Phase 1 locked-evaluation contract and pure metrics."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "evaluate_phase1_bed_state.py"
spec = importlib.util.spec_from_file_location("evaluate_phase1_bed_state", SCRIPT_PATH)
assert spec and spec.loader
evaluation = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = evaluation
spec.loader.exec_module(evaluation)


class Phase1EvaluationTests(unittest.TestCase):
    def test_config_locks_test_groups_and_episode_bootstrap(self) -> None:
        config = evaluation.load_evaluation_config(evaluation.DEFAULT_CONFIG)
        self.assertEqual(config["membership"]["test"], 24)
        self.assertEqual(sum(config["membership"]["required_holdout_groups"].values()), 24)
        self.assertTrue(config["membership"]["selection_must_precede_unlock"])
        self.assertTrue(config["metrics"]["episode_is_resampling_unit"])
        self.assertEqual(
            config["parameter_controls"]["minimum_shuffle_degradation_m"],
            0.0,
        )
        self.assertEqual(
            config["parameter_controls"]["minimum_constant_degradation_m"],
            0.0,
        )
        self.assertFalse(
            config["sensitivity"]["use_for_training_normalization_calibration_or_selection"]
        )
        self.assertEqual(
            set(config["sensitivity"]["quantities"]),
            {
                "loaded_peak_sinkage_m",
                "loaded_displaced_volume_m3",
                "peak_recovery_m",
            },
        )
        self.assertTrue(
            all(
                value == 0.0
                for value in config["sensitivity"][
                    "chrono_repeatability_floor"
                ].values()
            )
        )

    def test_test_episode_selection_rechecks_lock_groups_and_surfaces(self) -> None:
        config = evaluation.load_evaluation_config(evaluation.DEFAULT_CONFIG)
        groups = []
        for name, count in config["membership"]["required_holdout_groups"].items():
            groups.extend([name] * count)
        seeds = config["membership"]["required_surface_seeds"]
        episodes = [
            {
                "episode_id": f"test_{index:02d}",
                "split": "test",
                "holdout_group": group,
                "initial_surface_seed": seeds[index % len(seeds)],
                "input_sha256": f"sha-{index}",
                "target_access": "locked",
            }
            for index, group in enumerate(groups)
        ]
        plan = {
            "episodes": {"test": episodes},
            "test_lock_sha256": evaluation.canonical_sha256(
                [
                    {"episode_id": item["episode_id"], "input_sha256": item["input_sha256"]}
                    for item in episodes
                ]
            ),
        }
        selected = evaluation.selected_test_episodes(config, plan)
        self.assertEqual(len(selected), 24)
        plan["episodes"]["test"][0]["target_access"] = "open"
        with self.assertRaisesRegex(ValueError, "lock is invalid"):
            evaluation.selected_test_episodes(config, plan)

    def test_parameter_shuffle_is_deterministic_derangement(self) -> None:
        identities = [f"episode_{index:02d}" for index in range(24)]
        first = evaluation.parameter_shuffle_mapping(identities, 17)
        second = evaluation.parameter_shuffle_mapping(reversed(identities), 17)
        self.assertEqual(first, second)
        self.assertEqual(set(first), set(identities))
        self.assertEqual(set(first.values()), set(identities))
        self.assertTrue(all(source != target for source, target in first.items()))

    def test_inference_domain_rejects_out_of_box_action_and_soil(self) -> None:
        contract = evaluation.load_contract(
            evaluation.repo_path(
                "configs/phase1_bed_state_v1.json"
            )
        )
        episode = {
            "center_xy_m": [0.0, 0.0],
            "radius_m": 0.035,
            "normal_force_n": 40.0,
            "soil_parameters": {
                "bekker_kphi": 800000.0,
                "mohr_friction_deg": 28.0,
            },
        }
        evaluation.validate_inference_domain(contract, episode)
        episode["center_xy_m"] = [0.101, 0.0]
        with self.assertRaisesRegex(ValueError, "center"):
            evaluation.validate_inference_domain(contract, episode)
        episode["center_xy_m"] = [0.0, 0.0]
        episode["soil_parameters"]["bekker_kphi"] = 1.0e6
        with self.assertRaisesRegex(ValueError, "bekker_kphi"):
            evaluation.validate_inference_domain(contract, episode)

    def test_matched_sensitivity_contract_requires_rectangle_and_common_action(self) -> None:
        config = evaluation.load_evaluation_config(evaluation.DEFAULT_CONFIG)
        combinations = [
            (640000.0, 24.0),
            (640000.0, 32.0),
            (960000.0, 24.0),
            (960000.0, 32.0),
            (800000.0, 28.0),
        ]
        cases = [
            {
                "case_id": f"case_{index}",
                "initial_surface_seed": 1101,
                "center_xy_m": [0.0, 0.0],
                "normal_force_n": 45.984375,
                "bekker_kphi": kphi,
                "mohr_friction_deg": friction,
            }
            for index, (kphi, friction) in enumerate(combinations)
        ]
        self.assertEqual(
            len(evaluation.matched_sensitivity_cases(config, {"material_cases": cases})),
            5,
        )
        cases[0]["normal_force_n"] = 31.0
        with self.assertRaisesRegex(ValueError, "not action matched"):
            evaluation.matched_sensitivity_cases(config, {"material_cases": cases})

    def test_surface_metrics_report_geometry_and_error(self) -> None:
        initial = np.zeros((3, 3), dtype=np.float64)
        target = np.zeros((3, 3), dtype=np.float64)
        target[1, 1] = -0.01
        prediction = np.zeros((3, 3), dtype=np.float64)
        prediction[1, 1] = -0.008
        mask = np.ones((3, 3), dtype=bool)
        x, y = np.meshgrid(np.arange(3) - 1, np.arange(3) - 1)
        metrics = evaluation.surface_metrics(
            prediction,
            target,
            initial,
            mask,
            grid_spacing_m=0.005,
            deformation_threshold_m=0.0005,
            relative_x_m=x,
            relative_y_m=y,
        )
        self.assertAlmostEqual(metrics["rmse_m"], 0.002 / 3.0)
        self.assertEqual(metrics["peak_depression_m"], 0.008)
        self.assertEqual(metrics["target_peak_depression_m"], 0.01)
        self.assertAlmostEqual(metrics["deformation_centroid_x_m"], 0.0)
        self.assertAlmostEqual(metrics["deformation_centroid_y_m"], 0.0)

    def test_bootstrap_resamples_whole_episode_values_deterministically(self) -> None:
        values = [1.0, 2.0, 3.0, 4.0]
        first = evaluation.bootstrap_interval(
            values, resamples=500, confidence=0.95, seed=9
        )
        second = evaluation.bootstrap_interval(
            values, resamples=500, confidence=0.95, seed=9
        )
        self.assertEqual(first, second)
        self.assertEqual(first["episode_count"], 4)
        self.assertEqual(first["estimate"], 2.5)
        self.assertLessEqual(first["lower"], first["estimate"])
        self.assertGreaterEqual(first["upper"], first["estimate"])

    def test_prerequisite_gate_refuses_absent_selection(self) -> None:
        config = evaluation.load_evaluation_config(evaluation.DEFAULT_CONFIG)
        with tempfile.TemporaryDirectory() as directory:
            modified = json.loads(json.dumps(config))
            modified["selection_summary"] = str(Path(directory) / "absent.json")
            with self.assertRaisesRegex(RuntimeError, "prerequisites are absent"):
                evaluation.require_prerequisites(modified)

    def test_recovery_metrics_separate_peak_and_volume_recovery(self) -> None:
        initial = np.zeros((2, 2), dtype=np.float64)
        loaded = np.asarray([[-0.010, -0.006], [0.0, 0.0]])
        post = np.asarray([[-0.004, -0.002], [0.0, 0.0]])
        result = evaluation.recovery_metrics(
            initial,
            loaded,
            post,
            np.ones((2, 2), dtype=bool),
            0.005,
        )
        self.assertAlmostEqual(result["peak_recovery_m"], 0.006)
        self.assertAlmostEqual(result["peak_recovery_fraction"], 0.6)
        self.assertGreater(result["volume_recovery_m3"], 0.0)
        self.assertGreater(result["volume_recovery_fraction"], 0.0)

    def test_sensitivity_edges_and_direction_gate(self) -> None:
        config = evaluation.load_evaluation_config(evaluation.DEFAULT_CONFIG)
        combinations = [
            ("klo_flo", 640000.0, 24.0),
            ("klo_fhi", 640000.0, 32.0),
            ("khi_flo", 960000.0, 24.0),
            ("khi_fhi", 960000.0, 32.0),
            ("kref_fref", 800000.0, 28.0),
        ]
        cases = [
            {
                "case_id": name,
                "bekker_kphi": kphi,
                "mohr_friction_deg": friction,
            }
            for name, kphi, friction in combinations
        ]
        values = {}
        for case in cases:
            response = (
                (case["bekker_kphi"] - 640000.0) / 320000.0
                + (case["mohr_friction_deg"] - 24.0) / 8.0
                + 1.0
            )
            quantities = {
                "loaded_peak_sinkage_m": response * 1.0e-3,
                "loaded_displaced_volume_m3": response * 1.0e-6,
                "peak_recovery_m": response * 2.0e-4,
            }
            values[case["case_id"]] = {
                "chrono": quantities,
                "prediction": dict(quantities),
            }
        result = evaluation.evaluate_sensitivity_values(
            config, cases, values
        )
        self.assertEqual(len(evaluation.sensitivity_edges(cases)), 4)
        self.assertEqual(result["eligible_comparisons"], 12)
        self.assertEqual(result["direction_fraction"], 1.0)
        self.assertTrue(all(result["checks"].values()))

    def test_aggregate_prediction_results_enforces_all_phase1_gates(self) -> None:
        config = evaluation.load_evaluation_config(evaluation.DEFAULT_CONFIG)
        config = json.loads(json.dumps(config))
        config["metrics"]["bootstrap_resamples"] = 100
        groups = []
        for name, count in config["membership"][
            "required_holdout_groups"
        ].items():
            groups.extend([name] * count)
        predictor_rmse = {
            "B0": 0.010,
            "B1": 0.008,
            "B2": 0.006,
            "B3": 0.005,
            "H0": 0.005,
            "H1": 0.003,
            "H2": 0.003,
            "H1_shuffled_p": 0.004,
            "H1_constant_p": 0.004,
        }
        results = []
        for index, group in enumerate(groups):
            metrics = {}
            for predictor, value in predictor_rmse.items():
                metrics[predictor] = {
                    checkpoint: {
                        region: {"rmse_m": value}
                        for region in config["metrics"]["regions"]
                    }
                    for checkpoint in evaluation.CHECKPOINTS
                }
            uncertainty = {
                variant: {
                    checkpoint: {"coverage_fraction": 0.9}
                    for checkpoint in evaluation.CHECKPOINTS
                }
                for variant in evaluation.NEURAL_VARIANTS
            }
            results.append(
                {
                    "episode_id": f"episode_{index:02d}",
                    "holdout_group": group,
                    "metrics": metrics,
                    "uncertainty": uncertainty,
                    "all_output_checks_pass": True,
                }
            )
        summary = evaluation.aggregate_prediction_results(
            config, results
        )
        self.assertTrue(all(summary["checks"].values()))
        self.assertTrue(
            summary["checks"][
                "parameter_constant_degrades:loaded:footprint"
            ]
        )
        self.assertEqual(
            summary["latent_mechanics"]["status"],
            "neutral_without_worse_tail",
        )
        failures = evaluation.failure_case_report(config, results)
        self.assertEqual(len(failures["worst_by_checkpoint_region"]), 4)
        self.assertEqual(failures["episodes_worse_than_raw_newton"], [])
        self.assertEqual(
            failures["episodes_exceeding_failure_tail_tolerance"], []
        )
        results[0]["metrics"]["H1"]["loaded"]["footprint"][
            "rmse_m"
        ] = 0.010
        failures = evaluation.failure_case_report(config, results)
        self.assertEqual(
            failures["episodes_worse_than_raw_newton"][0]["episode_id"],
            "episode_00",
        )
        self.assertTrue(
            failures["episodes_exceeding_failure_tail_tolerance"][0][
                "exceeds_failure_tail_tolerance"
            ]
        )

    def test_final_artifact_integrity_detects_prediction_mutation(self) -> None:
        config = evaluation.load_evaluation_config(evaluation.DEFAULT_CONFIG)
        config = json.loads(json.dumps(config))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "evaluation"
            training = root / "training"
            output.mkdir()
            training.mkdir()
            config["execution"]["output_root"] = str(output)
            episode_id = "locked_test_00"
            episode = {
                "episode_id": episode_id,
                "holdout_group": "joint_combination",
            }
            plan = {
                "status": "frozen_after_validation_selection_before_first_test_target",
                "episodes": [episode],
                "source_sha256": {},
                "input_sha256": {},
                "selection_summary_sha256": "selection-sha",
                "selected_model_artifacts": {},
            }
            for key in evaluation.STABLE_PLAN_KEYS:
                plan.setdefault(key, {})
            plan["episodes"] = [episode]
            plan_path = output / "evaluation_plan.json"
            evaluation.write_json(plan_path, plan)

            selected = {}
            for variant in evaluation.NEURAL_VARIANTS:
                model_root = training / "models" / variant / "seed_7"
                model_root.mkdir(parents=True)
                identities = {}
                for filename, key in (
                    ("model_card.json", "model_card_sha256"),
                    ("model.pt", "checkpoint_sha256"),
                    ("history.json", "history_sha256"),
                ):
                    path = model_root / filename
                    path.write_bytes(f"{variant}:{filename}".encode())
                    identities[key] = evaluation.fresh.sha256_file(path)
                plan["selected_model_artifacts"][variant] = {
                    "seed": 7,
                    **identities,
                }
                selected[variant] = {
                    "active_spatial_channels": [
                        "loaded_column_mean_stress_mean_pa",
                        "loaded_column_mean_elastic_jacobian",
                    ]
                }
            evaluation.write_json(plan_path, plan)

            bulk_path = root / "bulk_summary.json"
            training_plan_path = training / "training_plan.json"
            selection_path = training / "selection_summary.json"
            evaluation.write_json(
                bulk_path,
                {
                    "status": "passed",
                    "training_dataset_ready": True,
                    "checks": {"all_admitted": True},
                    "qualified_nonkinematic_families": ["stress", "elastic"],
                    "excluded_nonkinematic_families": ["plastic"],
                },
            )
            evaluation.write_json(
                training_plan_path,
                {
                    "model_parameter_counts": {
                        variant: 289172
                        for variant in evaluation.NEURAL_VARIANTS
                    }
                },
            )
            evaluation.write_json(
                selection_path,
                {
                    "status": "models_selected_before_test_unlock",
                    "test_targets_opened": False,
                    "selected": selected,
                },
            )

            episode_root = evaluation.dataset.episode_root(config, episode_id)
            tensor_root = episode_root / "tensors"
            prediction_root = episode_root / "predictions"
            tensor_root.mkdir(parents=True)
            prediction_root.mkdir(parents=True)
            model_input = tensor_root / "model_inputs.npz"
            target = tensor_root / "targets.npz"
            model_input.write_bytes(b"model-input")
            target.write_bytes(b"target")
            locked_manifest = {
                "model_input_file": model_input.name,
                "target_file": target.name,
                "checks": {"all_finite": True},
                "sha256": {
                    "model_inputs": evaluation.fresh.sha256_file(model_input),
                    "targets": evaluation.fresh.sha256_file(target),
                },
            }
            evaluation.write_json(
                tensor_root / "locked_test_tensor_manifest.json",
                locked_manifest,
            )
            embedded_episode = {
                "episode_id": episode_id,
                "complete": True,
                "admitted": True,
                "locked_tensor_manifest": locked_manifest,
            }
            evaluation.write_json(
                episode_root / "episode_summary.json", embedded_episode
            )
            dataset_summary_path = output / "test_dataset_summary.json"
            evaluation.write_json(
                dataset_summary_path,
                {
                    "status": "passed",
                    "prediction_permitted": True,
                    "checks": {"all_admitted": True},
                    "identity": {
                        "evaluation_plan_sha256": evaluation.fresh.sha256_file(
                            plan_path
                        )
                    },
                    "episodes": {episode_id: embedded_episode},
                },
            )

            archive = prediction_root / "predicted_surfaces.npz"
            archive.write_bytes(b"predictions")
            particle_audits = {}
            for variant in evaluation.NEURAL_VARIANTS:
                particle_audits[variant] = {}
                corrected_root = prediction_root / "corrected_particles" / variant
                corrected_root.mkdir(parents=True)
                for checkpoint in evaluation.CHECKPOINTS:
                    corrected = corrected_root / f"{checkpoint}.npz"
                    surface = prediction_root / f"{variant}_{checkpoint}_surface_m.npy"
                    corrected.write_bytes(f"{variant}:{checkpoint}:state".encode())
                    surface.write_bytes(f"{variant}:{checkpoint}:surface".encode())
                    particle_audits[variant][checkpoint] = {
                        "all_checks_pass": True,
                        "corrected_state_sha256": evaluation.fresh.sha256_file(
                            corrected
                        ),
                        "predicted_surface_sha256": evaluation.fresh.sha256_file(
                            surface
                        ),
                    }
            prediction_result = {
                "episode_id": episode_id,
                "prediction_archive_sha256": evaluation.fresh.sha256_file(archive),
                "selected_model_artifacts": plan["selected_model_artifacts"],
                "all_output_checks_pass": True,
                "particle_audits": particle_audits,
            }
            prediction_result_path = prediction_root / "prediction_summary.json"
            evaluation.write_json(prediction_result_path, prediction_result)
            prediction = {
                "status": "predictions_complete",
                "episode_count": 1,
                "evaluation_plan_sha256": evaluation.fresh.sha256_file(plan_path),
                "test_dataset_summary_sha256": evaluation.fresh.sha256_file(
                    dataset_summary_path
                ),
                "episodes": {
                    episode_id: {
                        "prediction_summary_sha256": evaluation.fresh.sha256_file(
                            prediction_result_path
                        ),
                        "prediction_archive_sha256": evaluation.fresh.sha256_file(
                            archive
                        ),
                    }
                },
            }
            paths = {
                "bulk_summary": bulk_path,
                "training_plan": training_plan_path,
                "selection_summary": selection_path,
            }
            marker = {"selection_summary_sha256": "selection-sha"}
            with (
                mock.patch.object(evaluation, "build_plan", return_value=plan),
                mock.patch.object(
                    evaluation, "prerequisite_paths", return_value=paths
                ),
                mock.patch.object(
                    evaluation, "require_unlocked", return_value=marker
                ),
                mock.patch.object(
                    evaluation, "require_opened", return_value=marker
                ),
            ):
                checks, _details = evaluation.final_artifact_integrity(
                    evaluation.DEFAULT_CONFIG, config, plan, prediction
                )
                self.assertTrue(all(checks.values()))
                archive.write_bytes(b"mutated")
                checks, details = evaluation.final_artifact_integrity(
                    evaluation.DEFAULT_CONFIG, config, plan, prediction
                )
                self.assertFalse(
                    checks["integrity:prediction_and_particle_artifacts"]
                )
                self.assertEqual(
                    details["prediction_artifact_failures"], [episode_id]
                )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_phase1_latent_qualification as qualification


CONFIG_PATH = REPO_ROOT / "configs" / "phase1_latent_export_v3.json"


def test_latent_contract_is_prospective_and_requires_three_repeats() -> None:
    config = qualification.load_config(CONFIG_PATH)

    assert config["status"] == "frozen_before_runtime_qualification"
    assert config["source_case"]["case_id"] == "screen_material_kref_fref"
    assert config["execution"]["independent_fresh_process_repeats"] == 3
    assert config["required_families"]["velocity"]["box_mean_width_cells"] == 3
    assert config["admission"]["minimum_qualified_nonkinematic_families"] == 1
    assert config["admission"]["unqualified_fields_excluded_from_h2"] is True


def test_repeat_command_inherits_frozen_newton_screen_settings(tmp_path: Path) -> None:
    config = qualification.load_config(CONFIG_PATH)
    _contract_path, contract = qualification.phase1_contract(config)

    command = qualification.response_command(
        config,
        contract,
        str(config["source_case"]["case_id"]),
        tmp_path / "response",
    )
    joined = " ".join(command)

    assert Path(command[0]).samefile(Path(config["execution"]["newton_python"]))
    assert "run_newton_cylinder_diagnostic.py" in command[1]
    assert "--candidate-preparation" in command
    assert "--observation-time-mode independent_fixed" in joined
    assert "--loaded-duration-s 0.35" in joined
    assert "--residual-duration-s 0.25" in joined
    assert "--dt-s 0.00025" in joined
    assert "--proxy-iterations 8" in joined
    assert "--rigid-substeps 16" in joined
    assert "--cylinder-collider-mode circumscribed_mesh" in joined
    assert "--cylinder-collider-segments 128" in joined
    assert "--cylinder-collision-guard-m 1e-05" in joined
    assert "screen_material_kref_fref" in joined
    assert "newton_common_base_v2/shared_newton_prior/preparation" in joined


def test_box_mean_is_fixed_odd_width_and_preserves_shape() -> None:
    values = np.arange(25, dtype=float).reshape(5, 5)

    smoothed = qualification.box_mean_2d(values, 3)

    assert smoothed.shape == values.shape
    assert smoothed[2, 2] == 12.0
    assert smoothed[0, 0] == np.mean([[0, 0, 1], [0, 0, 1], [5, 5, 6]])


def test_grid_field_evidence_detects_stable_and_unstable_repeats() -> None:
    base = np.asarray([[0.0, 0.0], [0.0, 0.0]])
    loaded = np.asarray([[0.0, 1.0], [2.0, 3.0]])
    stable_runs = []
    for delta in (0.0, 0.01, -0.01):
        stable_runs.append(
            {
                "initial": {"field": base},
                "loaded": {"field": loaded + delta},
                "post_unload": {"field": base},
            }
        )
    stable = qualification.grid_field_evidence(
        stable_runs, local_mask=np.ones((2, 2), dtype=bool)
    )["field"]
    assert stable["repeat_rms_over_action_signal"] < 0.25
    assert stable["minimum_pairwise_repeat_pearson"] > 0.95

    unstable_runs = list(stable_runs)
    unstable_runs[2] = {
        "initial": {"field": base},
        "loaded": {"field": np.flip(loaded, axis=1)},
        "post_unload": {"field": base},
    }
    unstable = qualification.grid_field_evidence(
        unstable_runs, local_mask=np.ones((2, 2), dtype=bool)
    )["field"]
    assert unstable["minimum_pairwise_repeat_pearson"] < 0.95


def test_plastic_plausibility_rejects_elastic_material_outlier() -> None:
    config = qualification.load_config(CONFIG_PATH)
    families = {"plastic": {"qualified": True, "checks": {"signal": True}}}
    triplet = {
        "fields": {
            "plastic_jacobian": {
                "checkpoint": {
                    "initial": {"minimum": 1.0, "maximum": 1.0},
                    "loaded": {"minimum": 1.0, "maximum": 100.0},
                    "post_unload": {"minimum": 1.0, "maximum": 1.0},
                }
            }
        }
    }

    maximum_abs_log = qualification.apply_plastic_plausibility_gate(
        families, triplet, config
    )

    assert maximum_abs_log == np.log(100.0)
    assert families["plastic"]["qualified"] is False
    assert (
        families["plastic"]["checks"]["plastic_constitutive_plausibility"]
        is False
    )

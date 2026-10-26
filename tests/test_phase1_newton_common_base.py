from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_phase1_newton_common_base as common_base
import run_phase1_screening as screening
from run_phase1_contract_screen import load_contract


CONFIG_PATH = REPO_ROOT / "configs" / "phase1_newton_common_base_v2.json"
CONTRACT_PATH = REPO_ROOT / "configs" / "phase1_bed_state_v1.json"


def test_repair_contract_preserves_failure_and_inference_safe_timing() -> None:
    config = common_base.load_qualification(CONFIG_PATH)
    assert config["antecedent_failure"]["preserve_original_failure"] is True
    assert config["antecedent_validation_failure"]["preserve_v1_failure"] is True
    assert config["antecedent_failure"]["settled_surface_rmse_m"] > 0.005
    assert config["admission"]["retain_phase0_surface_rmse_gate_m"] == 0.005
    assert config["observation_time_contract"] == {
        "newton_mode": "independent_fixed",
        "loaded_duration_s": 0.35,
        "post_unload_duration_s": 0.25,
        "chrono_target_checkpoint": "independently accepted_settled_state",
        "chrono_target_time_must_not_control_newton_rollout": True,
    }


def test_five_material_cases_share_one_newton_input() -> None:
    contract = load_contract(CONTRACT_PATH)
    cases = common_base.material_cases(contract)
    shared = common_base.validate_shared_prior_cases(cases)
    assert len(cases) == 5
    assert shared["center_xy_m"] == [0.0, 0.0]
    assert shared["normal_force_n"] == 45.984375
    assert shared["initial_surface_seed"] == 1101
    assert {case["bekker_kphi"] for case in cases} == {640000.0, 800000.0, 960000.0}


def test_shared_prior_validation_rejects_action_difference() -> None:
    contract = load_contract(CONTRACT_PATH)
    cases = common_base.material_cases(contract)
    changed = json.loads(json.dumps(cases))
    changed[-1]["normal_force_n"] += 1.0
    with pytest.raises(ValueError, match="share one Newton prior"):
        common_base.validate_shared_prior_cases(changed)


def test_all_frozen_chrono_cases_are_present_and_accepted() -> None:
    contract = load_contract(CONTRACT_PATH)
    results = [
        screening.chrono_result(contract, case)
        for case in common_base.material_cases(contract)
    ]
    assert len(results) == 5
    assert all(result["complete"] and result["accepted"] for result in results)

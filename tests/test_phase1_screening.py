from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_phase1_screening as screening
from run_phase1_contract_screen import load_contract


CONTRACT_PATH = REPO_ROOT / "configs" / "phase1_bed_state_v1.json"


def test_screening_plan_inherits_frozen_dataset_identities() -> None:
    contract = load_contract(CONTRACT_PATH)
    plan = screening.build_screening_plan(CONTRACT_PATH, contract)
    dataset = json.loads(screening.frozen_dataset_plan(contract).read_text(encoding="utf-8"))
    assert plan["episode_manifest_sha256"] == dataset["episode_manifest_sha256"]
    assert plan["test_lock_sha256"] == dataset["test_lock_sha256"]
    assert len(plan["surface_cases"]) == 6
    assert len(plan["material_cases"]) == 5
    assert plan["bulk_dataset_permitted"] is False


def test_material_cases_derive_only_frozen_action_values() -> None:
    contract = load_contract(CONTRACT_PATH)
    plan = screening.build_screening_plan(CONTRACT_PATH, contract)
    cases = screening.selected_material_cases(contract, plan, [])
    assert len(cases) == 5
    assert {case["case_id"] for case in cases} == {
        "screen_material_klo_flo",
        "screen_material_klo_fhi",
        "screen_material_khi_flo",
        "screen_material_khi_fhi",
        "screen_material_kref_fref",
    }
    for case in cases:
        assert case["radius_m"] == 0.035
        assert case["height_m"] == 0.035
        assert case["equivalent_mass_kg"] == 4.6875
        assert case["initial_surface_seed"] == 1101

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_phase0_multiload_residual_pilot.py"
)
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("run_phase0_multiload_residual_pilot", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def synthetic_plan() -> dict:
    positions = ("center", "xplus", "xminus", "yplus", "yminus")
    rungs = {
        "spatial31": [f"{position}_f031n" for position in positions],
        "spatial46": [f"{position}_f046n" for position in positions],
        "spatial61": [f"{position}_f061n" for position in positions],
    }
    train = [
        case_id
        for rung in rungs.values()
        for case_id in rung
        if case_id.startswith(("center_", "xplus_", "xminus_"))
    ]
    validation = [case_id for rung in rungs.values() for case_id in rung if case_id.startswith("yplus_")]
    test = [case_id for rung in rungs.values() for case_id in rung if case_id.startswith("yminus_")]
    return {
        "rungs": rungs,
        "episode_split": {
            "policy": "position-held-out",
            "train": train,
            "validation": validation,
            "test": test,
        },
    }


class MultiloadResidualPilotTests(unittest.TestCase):
    def test_training_uses_six_actions_at_two_loads(self) -> None:
        ids = MODULE.training_case_ids(synthetic_plan())
        self.assertEqual(len(ids), 6)
        self.assertTrue(all("yplus" not in case_id and "yminus" not in case_id for case_id in ids))
        self.assertEqual({case_id[-5:] for case_id in ids}, {"f031n", "f046n"})

    def test_fit_lock_protects_46n_holdouts_and_all_61n_actions(self) -> None:
        plan = synthetic_plan()
        protected = MODULE.protected_case_ids(plan)
        self.assertEqual(
            protected[:2],
            ["yplus_f046n", "yminus_f046n"],
        )
        self.assertEqual(protected[2:], plan["rungs"]["spatial61"])

    def test_v2_has_distinct_model_identity(self) -> None:
        self.assertNotEqual(MODULE.MODEL_ID, "phase0_action_aligned_particle_mlp_v1_20261018")
        self.assertEqual(MODULE.base.MODEL_ID, MODULE.MODEL_ID)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Regression tests for the conditional v2 JSON compatibility shim."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import continue_phase1_evaluation_v2 as continuation


class Phase1EvaluationV2ContinuationTests(unittest.TestCase):
    def test_numpy_scalars_are_json_compatible_without_value_changes(self) -> None:
        value = {
            "direction_matches": np.bool_(True),
            "count": np.int64(3),
            "fraction": np.float64(0.75),
        }
        converted = continuation.json_builtin(value)
        self.assertEqual(
            json.loads(json.dumps(converted)),
            {"direction_matches": True, "count": 3, "fraction": 0.75},
        )


if __name__ == "__main__":
    unittest.main()

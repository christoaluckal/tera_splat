#!/usr/bin/env python3
"""Pure tests for direct-v4 authoritative-validation ordering."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "validate_phase1_one_action_successor_direct_v4.py"
CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_direct_v4.json"


def load_module():
    spec = importlib.util.spec_from_file_location("successor_direct_v4_validation", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


validation = load_module()


class DirectV4ValidationTests(unittest.TestCase):
    def test_config_keeps_v3_as_preflight_only(self) -> None:
        config = validation.planner.load_config(CONFIG)
        self.assertTrue(
            config["antecedent"][
                "direct_v3_preflight_only_because_confirmation_lock_followed_validation"
            ]
        )
        self.assertTrue(config["validation"]["v1_test_ids_forbidden"])

    def test_source_set_includes_planner_validator_and_tests(self) -> None:
        sources = validation.planner.source_paths(CONFIG)
        self.assertEqual(
            set(sources),
            {"config", "planner", "validator", "planner_tests", "validator_tests"},
        )
        self.assertTrue(all(path.is_file() for path in sources.values()))


if __name__ == "__main__":
    unittest.main()

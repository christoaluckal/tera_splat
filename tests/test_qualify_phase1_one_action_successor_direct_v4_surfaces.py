#!/usr/bin/env python3
"""Pure tests for direct-v4 fresh-surface qualification."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "qualify_phase1_one_action_successor_direct_v4_surfaces.py"
CONFIG = REPO_ROOT / "configs" / "phase1_one_action_successor_direct_v4.json"


def load_module():
    spec = importlib.util.spec_from_file_location("direct_v4_surfaces", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


qualification = load_module()


class DirectV4SurfaceTests(unittest.TestCase):
    def test_cases_are_exactly_fresh_5101_through_5106(self) -> None:
        config = qualification.planner.load_config(CONFIG)
        plan = json_load(
            qualification.planner.repo_path(config["execution"]["confirmation_plan"])
        )
        rows = qualification.cases(config, plan)
        self.assertEqual([row["initial_surface_seed"] for row in rows], list(range(5101, 5107)))
        self.assertEqual(len({row["input_sha256"] for row in rows}), 6)

    def test_cases_preserve_fresh_partition_membership(self) -> None:
        config = qualification.planner.load_config(CONFIG)
        plan = json_load(
            qualification.planner.repo_path(config["execution"]["confirmation_plan"])
        )
        rows = qualification.cases(config, plan)
        partitions = {
            row["initial_surface_seed"]: row["partition"] for row in rows
        }
        self.assertEqual(
            partitions,
            {
                5101: "fresh_test",
                5102: "fresh_test",
                5103: "fresh_test",
                5104: "fresh_test",
                5105: "fresh_test",
                5106: "fresh_sensitivity",
            },
        )


def json_load(path: Path):
    import json

    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

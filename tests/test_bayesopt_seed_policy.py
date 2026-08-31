#!/usr/bin/env python3
"""Unit tests for narrowed-region BayesOpt seed handling."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import numpy as np

from scripts import run_chrono_genesis_bayesopt as bayesopt


class BayesOptSeedPolicyTest(unittest.TestCase):
    def test_same_fidelity_seed_can_be_outside_proposal_bounds_explicitly(self) -> None:
        values = {
            "log10_E": 4.315517277570874,
            "phi_deg": 16.50770096909899,
            "nu": 0.10151632356135101,
            "particle_spacing_m": 0.005,
            "particle_size_ratio": 1.0,
        }
        with (
            patch.object(bayesopt, "LOG10_E_MIN", 4.255272505103306),
            patch.object(bayesopt, "LOG10_E_MAX", 4.380211241711606),
            patch.object(bayesopt, "PHI_MIN_DEG", 12.0),
            patch.object(bayesopt, "PHI_MAX_DEG", 16.5),
            patch.object(bayesopt, "NU_MIN", 0.10),
            patch.object(bayesopt, "NU_MAX", 0.115),
            patch.object(bayesopt, "SPACING_CHOICES_M", (0.005,)),
            patch.object(bayesopt, "SIZE_RATIO_CHOICES", (1.0,)),
        ):
            with self.assertRaises(ValueError):
                bayesopt.candidate_from_mapping(values)
            seed = bayesopt.candidate_from_mapping(values, enforce_search_bounds=False)
            vector = bayesopt.candidate_vector(seed)

        self.assertAlmostEqual(seed["E_pa"], 20678.416453867667)
        self.assertTrue(np.all(np.isfinite(vector)))
        self.assertGreater(vector[1], 1.0)

    def test_out_of_region_mode_still_rejects_nonphysical_seed(self) -> None:
        values = {
            "log10_E": 4.3,
            "phi_deg": 16.0,
            "nu": 0.5,
            "particle_spacing_m": 0.005,
            "particle_size_ratio": 1.0,
        }
        with self.assertRaisesRegex(ValueError, "seed nu"):
            bayesopt.candidate_from_mapping(values, enforce_search_bounds=False)


if __name__ == "__main__":
    unittest.main()

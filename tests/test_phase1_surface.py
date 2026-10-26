from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from phase1_surface import SurfaceLimits, array_sha256, generate_surface, limits_from_contract


CONTRACT_PATH = REPO_ROOT / "configs" / "phase1_bed_state_v1.json"


def contract_and_limits() -> tuple[dict, SurfaceLimits]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    return contract, limits_from_contract(contract)


def all_surface_seeds(contract: dict) -> list[int]:
    groups = contract["initial_surface_domain"]["surface_seeds"]
    return [int(seed) for values in groups.values() for seed in values]


def test_all_declared_surfaces_pass_bounds_and_are_distinct() -> None:
    contract, limits = contract_and_limits()
    hashes = set()
    for seed in all_surface_seeds(contract):
        surface, metadata = generate_surface(seed, limits)
        assert surface.shape == (121, 121)
        assert surface.dtype == np.float32
        assert metadata["qualified"]
        assert all(metadata["checks"].values())
        assert metadata["metrics"]["maximum_absolute_relief_m"] <= 0.005
        assert metadata["metrics"]["maximum_local_slope_deg"] <= 10.0
        assert metadata["metrics"]["spectral_correlation_floor_m"] >= 0.05
        assert abs(metadata["metrics"]["mean_m"]) <= 1.0e-9
        hashes.add(array_sha256(surface))
    assert len(hashes) == len(all_surface_seeds(contract))


def test_surface_generation_is_bitwise_deterministic() -> None:
    _contract, limits = contract_and_limits()
    first, first_metadata = generate_surface(1101, limits)
    second, second_metadata = generate_surface(1101, limits)
    np.testing.assert_array_equal(first, second)
    assert first_metadata == second_metadata


def test_generator_rejects_impossible_correlation_constraint() -> None:
    _contract, limits = contract_and_limits()
    impossible = SurfaceLimits(
        **{
            **limits.__dict__,
            "minimum_correlation_length_m": 0.08,
            "wavelength_max_m": 0.3,
        }
    )
    with pytest.raises(ValueError, match="correlation floor"):
        generate_surface(1101, impossible)

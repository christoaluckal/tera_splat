#!/usr/bin/env python3
"""Contract tests for the shared Phase 1 direct/hybrid U-Net."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "phase1_bed_state_model.py"
spec = importlib.util.spec_from_file_location("phase1_bed_state_model", SCRIPT_PATH)
assert spec and spec.loader
model = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = model
spec.loader.exec_module(model)


def inputs(batch: int = 2, size: int = 33):
    spatial = torch.randn(batch, len(model.SPATIAL_CHANNELS), size, size)
    global_condition = torch.randn(batch, len(model.GLOBAL_FEATURES))
    initial = torch.randn(batch, 1, size, size) * 0.002
    newton = initial.repeat(1, 2, 1, 1) + torch.randn(batch, 2, size, size) * 0.001
    taper = torch.ones(batch, 1, size, size)
    scales = torch.tensor([0.02, 0.03])
    return spatial, global_condition, initial, newton, taper, scales


class Phase1BedStateModelTests(unittest.TestCase):
    def test_all_variants_share_capacity_in_declared_range(self) -> None:
        counts = {
            name: model.parameter_count(model.Phase1BedStateUNet(name))
            for name in model.MODEL_VARIANTS
        }
        self.assertEqual(len(set(counts.values())), 1)
        count = next(iter(counts.values()))
        self.assertGreaterEqual(count, 100_000)
        self.assertLessEqual(count, 1_000_000)

    def test_zero_initialized_mean_heads_reproduce_declared_base(self) -> None:
        spatial, condition, initial, newton, taper, scales = inputs()
        for variant in model.MODEL_VARIANTS:
            with self.subTest(variant=variant):
                network = model.Phase1BedStateUNet(variant)
                base = initial.repeat(1, 2, 1, 1) if variant == "B3" else newton
                result = network(spatial, condition, base, scales, taper)
                torch.testing.assert_close(result["height_m"], base)
                torch.testing.assert_close(
                    result["correction_m"], torch.zeros_like(base)
                )
                self.assertTrue(torch.isfinite(result["log_variance_m2"]).all())
                self.assertEqual(result["height_m"].shape, (2, 2, 33, 33))

    def test_variant_masks_define_direct_parameter_and_latent_ablations(self) -> None:
        networks = {
            name: model.Phase1BedStateUNet(name) for name in model.MODEL_VARIANTS
        }
        active = {
            name: {
                model.SPATIAL_CHANNELS[index]
                for index in model.variant_channel_indices(name)
            }
            for name in model.MODEL_VARIANTS
        }
        self.assertTrue(set(model.NEWTON_CHANNELS).isdisjoint(active["B3"]))
        self.assertTrue(set(model.NEWTON_CHANNELS).issubset(active["H0"]))
        self.assertTrue(set(model.MECHANICS_CHANNELS).isdisjoint(active["H1"]))
        self.assertTrue(set(model.MECHANICS_CHANNELS).issubset(active["H2"]))
        self.assertEqual(networks["H0"].global_mask[0, 3:].count_nonzero(), 0)
        self.assertEqual(networks["H1"].global_mask[0, 3:].count_nonzero(), 2)
        self.assertFalse(any("plastic" in name for name in model.SPATIAL_CHANNELS))

    def test_film_conditioning_exists_at_every_unet_scale(self) -> None:
        network = model.Phase1BedStateUNet("H1")
        stages = (
            network.encoder0,
            network.encoder1,
            network.bottleneck,
            network.decoder1,
            network.decoder0,
        )
        self.assertTrue(all(len(stage.blocks) == 2 for stage in stages))
        self.assertTrue(
            all(
                isinstance(block.condition, torch.nn.Linear)
                for stage in stages
                for block in stage.blocks
            )
        )

    def test_correction_is_bounded_and_tapered_after_head_update(self) -> None:
        spatial, condition, _initial, newton, taper, scales = inputs(batch=1)
        network = model.Phase1BedStateUNet("H2")
        torch.nn.init.constant_(network.mean_head.weight, 2.0)
        torch.nn.init.constant_(network.mean_head.bias, 2.0)
        taper[:, :, :3, :] = 0.0
        result = network(spatial, condition, newton, scales, taper)
        correction = result["correction_m"]
        self.assertLessEqual(torch.max(torch.abs(correction[:, 0])), scales[0] + 1.0e-7)
        self.assertLessEqual(torch.max(torch.abs(correction[:, 1])), scales[1] + 1.0e-7)
        self.assertEqual(torch.count_nonzero(correction[:, :, :3, :]), 0)

    def test_odd_grid_forward_and_backward_are_finite(self) -> None:
        spatial, condition, _initial, newton, taper, scales = inputs(batch=1, size=121)
        network = model.Phase1BedStateUNet("H1")
        torch.nn.init.normal_(network.mean_head.weight, std=1.0e-3)
        result = network(spatial, condition, newton, scales, taper)
        loss = result["height_m"].square().mean() + result[
            "log_variance_m2"
        ].mean()
        loss.backward()
        self.assertTrue(torch.isfinite(loss))
        self.assertTrue(
            all(
                value.grad is None or torch.isfinite(value.grad).all()
                for value in network.parameters()
            )
        )


if __name__ == "__main__":
    unittest.main()

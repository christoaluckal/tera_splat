#!/usr/bin/env python3
"""Shared capacity-controlled U-Net for Phase 1 direct and hybrid models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import torch
from torch import nn
from torch.nn import functional as F


SPATIAL_CHANNELS = (
    "initial_height_m",
    "valid_support",
    "action_relative_x_m",
    "action_relative_y_m",
    "action_signed_distance_m",
    "action_footprint",
    "newton_loaded_displacement_m",
    "newton_post_unload_displacement_m",
    "loaded_column_particle_count",
    "loaded_column_mass_kg",
    "loaded_column_mean_action_velocity_mps",
    "loaded_contact_node_count",
    "loaded_contact_normal_impulse_ns",
    "loaded_column_mean_stress_mean_pa",
    "loaded_column_mean_stress_von_mises_pa",
    "loaded_column_mean_elastic_jacobian",
    "loaded_column_mean_elastic_isochoric_shear",
    "post_unload_column_particle_count",
    "post_unload_column_mass_kg",
    "post_unload_column_mean_action_velocity_mps",
    "post_unload_contact_node_count",
    "post_unload_contact_normal_impulse_ns",
    "post_unload_column_mean_stress_mean_pa",
    "post_unload_column_mean_stress_von_mises_pa",
    "post_unload_column_mean_elastic_jacobian",
    "post_unload_column_mean_elastic_isochoric_shear",
)

GLOBAL_FEATURES = (
    "center_x_m",
    "center_y_m",
    "normal_force_n",
    "bekker_kphi",
    "mohr_friction_deg",
)

GEOMETRY_CHANNELS = SPATIAL_CHANNELS[:6]
NEWTON_CHANNELS = SPATIAL_CHANNELS[6:8]
MECHANICS_CHANNELS = SPATIAL_CHANNELS[8:]
MODEL_VARIANTS = ("B3", "H0", "H1", "H2")


@dataclass(frozen=True)
class VariantContract:
    spatial_channels: tuple[str, ...]
    global_features: tuple[str, ...]
    base_state: str


VARIANT_CONTRACTS: Mapping[str, VariantContract] = {
    "B3": VariantContract(
        spatial_channels=GEOMETRY_CHANNELS,
        global_features=GLOBAL_FEATURES,
        base_state="initial",
    ),
    "H0": VariantContract(
        spatial_channels=GEOMETRY_CHANNELS + NEWTON_CHANNELS,
        global_features=GLOBAL_FEATURES[:3],
        base_state="newton",
    ),
    "H1": VariantContract(
        spatial_channels=GEOMETRY_CHANNELS + NEWTON_CHANNELS,
        global_features=GLOBAL_FEATURES,
        base_state="newton",
    ),
    "H2": VariantContract(
        spatial_channels=SPATIAL_CHANNELS,
        global_features=GLOBAL_FEATURES,
        base_state="newton",
    ),
}


def _group_count(channels: int) -> int:
    for groups in (8, 4, 2, 1):
        if channels % groups == 0:
            return groups
    return 1


class ConditionedResidualBlock(nn.Module):
    """Residual 3x3 block with global feature-wise affine conditioning."""

    def __init__(self, in_channels: int, out_channels: int, condition_dim: int):
        super().__init__()
        self.norm1 = nn.GroupNorm(_group_count(in_channels), in_channels)
        self.conv1 = nn.Conv2d(in_channels, out_channels, 3, padding=1)
        self.norm2 = nn.GroupNorm(_group_count(out_channels), out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, 3, padding=1)
        self.condition = nn.Linear(condition_dim, 2 * out_channels)
        self.skip = (
            nn.Identity()
            if in_channels == out_channels
            else nn.Conv2d(in_channels, out_channels, 1)
        )
        nn.init.zeros_(self.condition.weight)
        nn.init.zeros_(self.condition.bias)

    def forward(self, values: torch.Tensor, condition: torch.Tensor) -> torch.Tensor:
        hidden = self.conv1(F.silu(self.norm1(values)))
        scale, shift = self.condition(condition).chunk(2, dim=1)
        hidden = self.norm2(hidden)
        hidden = hidden * (1.0 + scale[:, :, None, None]) + shift[:, :, None, None]
        hidden = self.conv2(F.silu(hidden))
        return self.skip(values) + hidden


class ConditionedStage(nn.Module):
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        condition_dim: int,
        blocks: int,
    ):
        super().__init__()
        layers = [ConditionedResidualBlock(in_channels, out_channels, condition_dim)]
        layers.extend(
            ConditionedResidualBlock(out_channels, out_channels, condition_dim)
            for _ in range(blocks - 1)
        )
        self.blocks = nn.ModuleList(layers)

    def forward(self, values: torch.Tensor, condition: torch.Tensor) -> torch.Tensor:
        for block in self.blocks:
            values = block(values, condition)
        return values


class Phase1BedStateUNet(nn.Module):
    """One shared U-Net code path for B3, H0, H1, and H2.

    All variants retain exactly the same trainable parameter count. Inputs and
    global features excluded by an ablation are multiplied by immutable masks,
    rather than removing layers and changing capacity.
    """

    def __init__(
        self,
        variant: str,
        *,
        base_channels: int = 16,
        condition_dim: int = len(GLOBAL_FEATURES),
        blocks_per_scale: int = 2,
        initial_variance_m2: float = 2.5e-5,
        variance_floor_m2: float = 1.0e-8,
    ):
        super().__init__()
        if variant not in VARIANT_CONTRACTS:
            raise ValueError(f"unknown Phase 1 model variant: {variant}")
        if base_channels <= 0 or blocks_per_scale <= 0:
            raise ValueError("channel and block counts must be positive")
        if initial_variance_m2 <= variance_floor_m2 or variance_floor_m2 <= 0:
            raise ValueError("initial variance must exceed the positive floor")
        self.variant = variant
        self.base_state = VARIANT_CONTRACTS[variant].base_state
        self.variance_floor_m2 = float(variance_floor_m2)
        spatial_active = set(VARIANT_CONTRACTS[variant].spatial_channels)
        global_active = set(VARIANT_CONTRACTS[variant].global_features)
        self.register_buffer(
            "spatial_mask",
            torch.tensor(
                [float(name in spatial_active) for name in SPATIAL_CHANNELS]
            )[None, :, None, None],
            persistent=True,
        )
        self.register_buffer(
            "global_mask",
            torch.tensor([float(name in global_active) for name in GLOBAL_FEATURES])[None, :],
            persistent=True,
        )

        widths = (base_channels, 2 * base_channels, 4 * base_channels)
        self.stem = nn.Conv2d(len(SPATIAL_CHANNELS), widths[0], 3, padding=1)
        self.encoder0 = ConditionedStage(
            widths[0], widths[0], condition_dim, blocks_per_scale
        )
        self.down1 = nn.Conv2d(widths[0], widths[1], 3, stride=2, padding=1)
        self.encoder1 = ConditionedStage(
            widths[1], widths[1], condition_dim, blocks_per_scale
        )
        self.down2 = nn.Conv2d(widths[1], widths[2], 3, stride=2, padding=1)
        self.bottleneck = ConditionedStage(
            widths[2], widths[2], condition_dim, blocks_per_scale
        )
        self.up1 = nn.Conv2d(widths[2], widths[1], 1)
        self.decoder1 = ConditionedStage(
            2 * widths[1], widths[1], condition_dim, blocks_per_scale
        )
        self.up0 = nn.Conv2d(widths[1], widths[0], 1)
        self.decoder0 = ConditionedStage(
            2 * widths[0], widths[0], condition_dim, blocks_per_scale
        )
        self.mean_head = nn.Conv2d(widths[0], 2, 1)
        self.log_variance_head = nn.Conv2d(widths[0], 2, 1)
        nn.init.zeros_(self.mean_head.weight)
        nn.init.zeros_(self.mean_head.bias)
        nn.init.zeros_(self.log_variance_head.weight)
        nn.init.constant_(
            self.log_variance_head.bias,
            torch.log(torch.tensor(initial_variance_m2 - variance_floor_m2)).item(),
        )

    def _features(
        self, spatial: torch.Tensor, global_condition: torch.Tensor
    ) -> torch.Tensor:
        if spatial.ndim != 4 or spatial.shape[1] != len(SPATIAL_CHANNELS):
            raise ValueError(
                f"spatial input must be [B,{len(SPATIAL_CHANNELS)},H,W]"
            )
        if global_condition.ndim != 2 or global_condition.shape[1] != len(
            GLOBAL_FEATURES
        ):
            raise ValueError(
                f"global condition must be [B,{len(GLOBAL_FEATURES)}]"
            )
        spatial = spatial * self.spatial_mask.to(dtype=spatial.dtype)
        condition = global_condition * self.global_mask.to(dtype=global_condition.dtype)
        skip0 = self.encoder0(self.stem(spatial), condition)
        skip1 = self.encoder1(self.down1(skip0), condition)
        hidden = self.bottleneck(self.down2(skip1), condition)
        hidden = F.interpolate(
            self.up1(hidden), size=skip1.shape[-2:], mode="bilinear", align_corners=False
        )
        hidden = self.decoder1(torch.cat((hidden, skip1), dim=1), condition)
        hidden = F.interpolate(
            self.up0(hidden), size=skip0.shape[-2:], mode="bilinear", align_corners=False
        )
        return self.decoder0(torch.cat((hidden, skip0), dim=1), condition)

    def forward(
        self,
        spatial: torch.Tensor,
        global_condition: torch.Tensor,
        base_height_m: torch.Tensor,
        correction_scale_m: torch.Tensor,
        boundary_taper: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        features = self._features(spatial, global_condition)
        if base_height_m.ndim != 4 or base_height_m.shape[1] != 2:
            raise ValueError("base height must be [B,2,H,W]")
        if boundary_taper.ndim != 4 or boundary_taper.shape[1] != 1:
            raise ValueError("boundary taper must be [B,1,H,W]")
        if correction_scale_m.numel() != 2:
            raise ValueError("correction scale must contain loaded and post-unload values")
        raw_mean = self.mean_head(features)
        scale = correction_scale_m.reshape(1, 2, 1, 1).to(
            device=raw_mean.device, dtype=raw_mean.dtype
        )
        correction = scale * torch.tanh(raw_mean) * boundary_taper
        raw_log_variance = self.log_variance_head(features)
        variance = self.variance_floor_m2 + torch.exp(raw_log_variance)
        return {
            "height_m": base_height_m + correction,
            "correction_m": correction,
            "log_variance_m2": torch.log(variance),
        }


def stack_spatial_channels(arrays: Mapping[str, torch.Tensor]) -> torch.Tensor:
    missing = [name for name in SPATIAL_CHANNELS if name not in arrays]
    if missing:
        raise KeyError(f"missing Phase 1 spatial channels: {missing}")
    return torch.stack([arrays[name] for name in SPATIAL_CHANNELS], dim=0)


def parameter_count(model: nn.Module) -> int:
    return sum(value.numel() for value in model.parameters() if value.requires_grad)


def variant_channel_indices(variant: str) -> Sequence[int]:
    if variant not in VARIANT_CONTRACTS:
        raise ValueError(f"unknown Phase 1 model variant: {variant}")
    active = set(VARIANT_CONTRACTS[variant].spatial_channels)
    return tuple(index for index, name in enumerate(SPATIAL_CHANNELS) if name in active)

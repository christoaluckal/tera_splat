# Phase 6: Gaussian Update From Simulation

## Goal

Transfer MPM deformation back to the renderable Gaussian map.

## Inputs

- Original Gaussian attributes.
- MPM particle positions before/after.
- Optional MPM deformation gradients.
- Mapping between render Gaussians and simulated particles.

## Method

Start with center-only transfer:

```text
x_i' = x_i + interpolate_displacement(x_i)
```

Use nearest-neighbor or kernel interpolation from MPM particles to Gaussian
centers. Keep opacity and appearance unchanged.

Current implementation:

```bash
conda run -n tsplat python scripts/transfer_mpm_to_gaussians.py \
  --run-dir assets/indenter_rigid_coupled_base
```

This writes:

```text
assets/indenter_rigid_coupled_base/terrain_deformed_center_only.ply
assets/indenter_rigid_coupled_base/terrain_deformed_center_only_metadata.json
```

The current accepted run starts from a settled base, so the default transfer
mode is `final-position`: selected surface splat centers are set to the final
MPM surface particle positions, then transformed back into the source PLY
coordinate frame. All non-position Gaussian attributes are preserved. The
script also exposes `--transfer-mode indenter-delta` for debugging only, which
applies only the final-minus-initial MPM displacement to the source centers.

Then add covariance transfer:

```text
Sigma_i' = F_i Sigma_i F_i^T
```

This matches the PhysGaussian paper more closely, but should wait until
center-only transfer produces clean renders.

## PhysGaussian Reuse

PhysGaussian already exports simulated particle positions and covariance-like
state for rendering. Its render path applies inverse preprocessing transforms
before rasterization. The terrain prototype should preserve that idea:

- simulate in local/normalized MPM space,
- convert updated centers/covariance back to world/render space,
- merge unmodified outside-patch splats with modified local splats.

## Deliverables

- Deformed Gaussian splat map.
- Center-only update option.
- Covariance-update option.
- Before/after renders from multiple views.
- Transfer diagnostics: displacement range, invalid covariance count, selected
  splat count.

## Success Criteria

- Center-only updates render without artifacts.
- Full-scene output preserves unmodified regions outside the patch.
- Covariance updates do not create severe stretching, disappearing splats, or
  invalid matrices.
- The same query can be rendered from more than one camera.

## Risks / Open Questions

- Wrong coordinate transforms will make deformation appear in the wrong place.
- Covariance update can amplify unstable deformation gradients.
- Rendered filled particles may look wrong unless appearance inheritance is
  handled carefully.

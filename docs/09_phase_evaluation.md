# Phase 9: Evaluation

## Goal

Show that the system is doing more than visual editing.

## Inputs

- Before/after predictions from analytic and MPM methods.
- Controlled real or synthetic indentation references.
- Camera poses and optional depth maps.
- Run metrics from each query.

## Method

Start with a controlled sand tray:

1. Capture before images.
2. Apply known shallow indentation with a flat circular stamp.
3. Capture after images.
4. Reconstruct or estimate before/after geometry.
5. Compare predicted and observed after-state.

Use the same query locations, contact radius, and indentation depth for all
baselines.

## PhysGaussian Reuse

PhysGaussian provides rendered images and simulated particle/Gaussian states.
The terrain evaluation should add terrain-specific metrics rather than only
using visual similarity.

## Deliverables

- Evaluation dataset notes.
- Baseline comparisons:
  - no deformation,
  - analytic indentation,
  - MPM without subsurface support,
  - MPM with subsurface support,
  - MPM with material conditioning.
- Metrics report for each query.

## Success Criteria

- MPM with subsurface support beats no-deformation and analytic-only baselines
  on geometry-focused metrics.
- Rendered after-view is plausible and localized.
- Multiple query locations can be evaluated in the same terrain map.
- Results include both successes and failure cases.

## Metrics

Rendering:

- PSNR,
- SSIM,
- LPIPS.

Geometry and terrain:

- depth error,
- indentation depth error,
- deformation radius error,
- pile-up height error,
- displaced volume proxy,
- lateral spread error.

## Risks / Open Questions

- Real sand measurements are noisy and hard to align.
- Rendering metrics may penalize lighting differences more than deformation.
- Geometry metrics depend on reliable depth or reconstructed after-state.


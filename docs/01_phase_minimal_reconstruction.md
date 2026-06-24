# Phase 1: Minimal Terrain Splat Reconstruction

## Goal

Create or load a small sand terrain Gaussian scene that renders reliably and can
be exported or loaded as splat attributes.

## Inputs

- Synthetic sand height field, controlled sand tray capture, or existing local
  Gaussian scene.
- Camera poses and images if training a new scene.
- A target coordinate convention for "up" and terrain scale.

## Method

Start with the simplest scene that gives stable splats over a mostly flat sand
surface. Train with Nerfstudio `splatfacto`/`splatfacto-big` or use a compatible
3DGS checkpoint if one is already available. Export or keep the Gaussian
checkpoint so positions, covariance/scales, opacity, and color/SH features can
be loaded.

Prefer a controlled, low-clutter scene before public terrain or outdoor data.
Avoid slopes, vegetation, rocks, and holes until the local deformation pipeline
works.

## PhysGaussian Reuse

PhysGaussian expects checkpoints in a Gaussian Splatting-style model directory,
with splats under `point_cloud/iteration_*/point_cloud.ply`. Its loader then
extracts positions, covariance, opacity, and SH features for simulation and
rendering.

If using a different exporter, document any conversion needed to match this
attribute set before simulation phases begin.

## Deliverables

- Initial terrain Gaussian scene.
- Before-render images from known views.
- Camera pose metadata.
- Notes on scene scale and vertical axis.
- Attribute-loading sanity check for Gaussian centers, covariance/scales,
  opacity, and colors/SH.

## Success Criteria

- Terrain renders from held-out or inspection views.
- Gaussian centers visibly cover the terrain surface.
- Scene scale is known well enough to define centimeter-level contact radius and
  indentation depth.
- A local region around a query point can be cropped without losing the terrain
  surface.

## Risks / Open Questions

- Poor reconstruction density can make later deformation look like visual noise.
- Unknown scene scale makes physical parameters meaningless.
- If the scene is only a thin visual shell, MPM will need Phase 5 subsurface
  support before results are credible.


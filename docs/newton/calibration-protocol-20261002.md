# Chrono→Newton forward-model calibration protocol

## Model definition

Use the public stock Newton rollout as the forward model. Inputs are the
canonical initial bed, rigid action geometry/pose/mass, material candidate,
gravity, and the fixed numerical domain (7.8125 mm voxel, PIC/PIC, P0/S2/Q1,
0.25 ms, 8 proxy iterations, 16 rigid substeps). Chrono SCM episodes supply
the loaded and residual surfaces used as synthetic targets.

The model must emit both heightfields and deformation characteristics:

- loaded and residual surface maps;
- maximum and mean depression;
- footprint maximum/mean depression;
- depression volume;
- depression centroid;
- strict mechanics status, guide status, timing, and penetration maximum.

## Hard validity gates

Reject a candidate before scoring if any of the following fail: exact
episode-specific timing, finite/full-support I/O, prismatic-guide compliance,
or zero analytic particle-center penetration over the full sampled trajectory.
Invalid candidates are not optimizer observations.

## Multi-characteristic loss

For each valid action, retain the existing map terms but add normalized
characteristic terms:

```text
L = RMSE_loaded
  + 0.5 * RMSE_residual_footprint
  + wV * |V_newton - V_chrono| / SV
  + wP * |P_newton - P_chrono| / SP
  + wC * ||c_newton - c_chrono|| / SC
```

The current diagnostic defaults are `wV=wP=wC=0.25`, `SV=100 cm³`,
`SP=10 mm`, and `SC=5 mm`; these are selection diagnostics, not frozen
physical constants. The full map and characteristic columns are produced by
`diagnostics/forward_model_transfer_20261002/`.

## Split and interpretation

Use A0 (the fitted guided action) only for material selection. Use A2–A4 for
mass transfer and A5–A6 for spatial transfer validation. Never use a rejected
mechanics trial as an observation. Report scalar map error and characteristic
errors separately: A5 and A6 already show that the scalar winner can change
with action location.

## Current evidence boundary

The frozen incumbent is admissible across A4–A6 and wins A4 and A6 scalar
holdouts, but not A5. The 100 kPa control remains admissible and underpredicts
Chrono depression volume in the guided mass sweep. This supports a useful
Chrono-matched surrogate, not universal characteristic fidelity or real-sand
calibration.

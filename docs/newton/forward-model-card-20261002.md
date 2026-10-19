# Chrono→Newton terrain-deformation forward model

## Purpose

Predict loaded and residual terrain deformation for a known rigid-cylinder
action on the canonical prepared bed, using Chrono SCM episodes as synthetic
ground truth.

## Inputs

- canonical initial heightfield and valid support mask;
- cylinder mass, center, radius/height, guide/removal action;
- material `(E, nu, mu)`;
- fixed Newton domain: 7.8125 mm voxel, PIC/PIC, P0/S2/Q1, dt=0.25 ms,
  8 proxy iterations, 16 rigid substeps;
- episode-specific Chrono loaded and residual observation times.

## Outputs

- loaded/residual heightfields;
- surface RMSE and footprint RMSE against Chrono;
- peak/mean depression, depression volume, footprint statistics, and centroid;
- mechanics validity, guide/timing status, and strict penetration diagnostics.

## What is established

Chrono A2–A6 provide accepted GT episodes. The frozen A0-fitted Newton
material is mechanics-admissible for A4–A6 and the multi-characteristic A0
archive rescoring selects the same parameter point. A5/A6 demonstrate spatial
transfer and show that scalar objective winners can differ by action location.

## What is not established

This is not a universal real-sand model, a grain-level Chrono↔MPM equivalence,
or a guarantee of characteristic fidelity outside the guided cylinder family.
The A2/A3 incumbent gate failures and the A5/A6 action-dependent ranking are
part of the model boundary, not noise to be discarded.

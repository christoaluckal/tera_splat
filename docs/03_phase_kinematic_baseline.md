# Phase 3: Kinematic Deformation Baseline

## Goal

Build a simple analytic indentation baseline before using MPM. This creates a
visual proof-of-concept and a debugging target for later simulation.

## Inputs

- Local patch from Phase 2.
- Query point and local normal.
- Contact radius `r_contact`.
- Maximum displacement `d_max`.
- Optional rim parameters.

## Method

Move Gaussian centers downward with a Gaussian-shaped indentation:

```text
d_i = d_max * exp(-||xy_i - xy_query||^2 / (2 r_contact^2))
x_i' = x_i - d_i * normal
```

Optionally add a shallow rim or pile-up outside the contact radius:

```text
rim_i = a * exp(-(||xy_i - xy_query|| - r_rim)^2 / (2 sigma_rim^2))
x_i' = x_i' + rim_i * normal
```

Do not update covariance in the first pass. Center-only deformation makes render
artifacts easier to diagnose. Add covariance changes only after the baseline
produces stable before/after renders.

## PhysGaussian Reuse

The analytic baseline should use the same loaded Gaussian attributes and render
path expected by later PhysGaussian-based MPM phases. That keeps before/after
render differences attributable to deformation rather than renderer changes.

## Deliverables

- Before/after Gaussian patch or full-scene splat export.
- Before/after RGB renders.
- Optional before/after depth renders.
- Metrics: indentation depth, affected radius, displaced volume proxy.

## Success Criteria

- The dent is localized around the query point.
- The before/after render shows a visible but plausible terrain change.
- Rendering does not explode due to invalid positions or covariance.
- The output becomes the baseline for MPM comparisons.

## Risks / Open Questions

- Analytic indentation is not physically predictive; it is a controlled baseline.
- Without rim/pile-up, the result may look like pure heightfield editing.
- If the renderer cannot consume modified splats cleanly, fix that before MPM.


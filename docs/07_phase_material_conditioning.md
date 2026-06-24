# Phase 7: Material Conditioning

## Goal

Make terrain queries material-aware, starting with sand.

## Inputs

- Material label, initially `sand`.
- Material parameter table.
- MPM config fields used by PhysGaussian.

## Method

Start with one sand preset and tune only a few parameters:

```text
density
Young's modulus E
Poisson ratio nu
friction_angle
damping
```

Once sand is stable, add controlled variants such as wet sand, mud, gravel, and
snow. These do not need perfect physical realism at first. They need to produce
consistent counterfactual behavior under the same query.

## PhysGaussian Reuse

PhysGaussian supports `material: "sand"` and uses `friction_angle` for
Drucker-Prager-style sand behavior. The existing `wolf_config.json` is the
closest sand example. Other available material concepts include elastic,
plastic, metal-like, foam/snow-like, and viscoplastic behavior depending on the
solver's material mapping.

The terrain prototype should map high-level materials into the JSON fields that
the solver actually consumes. Avoid adding a broad material schema until the
sand-first pipeline is working.

## Deliverables

- Sand preset documentation.
- Material parameter table for early variants.
- Comparison renders for sand versus at least one alternate material.
- Run configs saved alongside query outputs.

## Success Criteria

- Changing material parameters changes deformation visibly and repeatably.
- Sand produces localized granular collapse/pile-up behavior.
- Softer or wetter variants produce smoother or wider deformation.
- Parameters are easy to inspect and reproduce.

## Risks / Open Questions

- Material parameters are manually tuned and may not match real sand.
- Different scenes may require scale-dependent retuning.
- Too many material variants early will slow down the core prototype.


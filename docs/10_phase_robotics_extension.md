# Phase 10: Robotics Extension

## Goal

Extend the coupled rigid-MPM terrain contact prototype toward robot-relevant
terrain interaction only after the local sand deformation pipeline works.

## Inputs

- Working query interface from Phase 8.
- Validated shallow deformation behavior from Phase 9.
- Robot contact descriptions: coupled rigid wheel/foot/blade geometry, shear
  direction, commanded motion or load, and repeated contact schedule.
- Optional robot observations from depth, LiDAR, odometry, torque/current, or
  IMU.

## Method

Replace the simple coupled rigid cylinder with contact shapes and histories
that matter for locomotion:

- coupled rigid wheel geometry,
- coupled rigid foot or plate geometry,
- tangential shear force,
- repeated contacts,
- online before/after terrain updates,
- slip and sinkage estimates,
- planner queries for lower-deformation terrain regions.

Keep these as extensions, not requirements for the first prototype. Follow the
Genesis example convention for physical contact: robot-relevant objects should
be `gs.materials.Rigid(needs_coup=True)` in a scene with
`gs.options.LegacyCouplerOptions(rigid_mpm=True)`. Analytic pressure footprints
are acceptable baselines, but not the default physical mechanism.

## PhysGaussian Reuse

The same Gaussian-to-MPM-to-Gaussian loop should remain the core. Robotics adds
contact semantics and observation updates; it should not require a separate
terrain representation if the earlier phases succeeded.

## Deliverables

- Robot contact query schema.
- Coupled rigid wheel or foot contact model.
- Repeated-contact simulation case.
- Sinkage/rut-depth metric.
- Updated terrain splat map after observed contact.

## Success Criteria

- Given a planned foot or wheel contact, predict terrain deformation.
- Predict sinkage or rut depth.
- Update the persistent terrain splat map after the robot acts.
- Provide planner-facing metrics without requiring full-scene MPM.

## Risks / Open Questions

- Wheel and foot contact introduce shear and repeated loading, which are harder
  than shallow vertical displacement.
- Robot observations may be noisy, partial, and delayed.
- Planner integration should wait until the prediction pipeline is credible.

# Phase 10: Robotics Extension

## Goal

Extend the shallow pressure prototype toward robot-relevant terrain contact only
after the local sand deformation pipeline works.

## Inputs

- Working query interface from Phase 8.
- Validated shallow deformation behavior from Phase 9.
- Robot contact descriptions: wheel patch, foot patch, shear direction, load,
  and repeated contact schedule.
- Optional robot observations from depth, LiDAR, odometry, torque/current, or
  IMU.

## Method

Replace the simple circular pressure patch with contact shapes and histories
that matter for locomotion:

- wheel contact patch,
- footstep-shaped pressure patch,
- tangential shear force,
- repeated contacts,
- online before/after terrain updates,
- slip and sinkage estimates,
- planner queries for lower-deformation terrain regions.

Keep these as extensions, not requirements for the first prototype.

## PhysGaussian Reuse

The same Gaussian-to-MPM-to-Gaussian loop should remain the core. Robotics adds
contact semantics and observation updates; it should not require a separate
terrain representation if the earlier phases succeeded.

## Deliverables

- Robot contact query schema.
- Wheel or foot pressure footprint model.
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


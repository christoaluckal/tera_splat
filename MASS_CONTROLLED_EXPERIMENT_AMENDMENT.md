# Amendment: Mass-Controlled Cylinder Placement

Date: 2026-08-06  
Applies to: `CURRENT_STATE(1).md`  
Status: This amendment supersedes every displacement-controlled action assumption in the current-state document.

## Reason for this amendment

The real cylinder was placed on the sand bed and was not intentionally pushed,
driven to a target depth, or subjected to an additional applied force. The real
experiment must therefore be modeled as **mass-controlled gravitational
loading**, not prescribed displacement-controlled indentation.

The available real observation remains one transition:

```text
(S0, A, S1)
```

where:

- `S0` is the pre-placement surface.
- `A` is placement of a cylinder of known geometry and mass at a known planar
  location.
- `S1` is the residual surface after the cylinder was removed and the bed
  settled.
- There is no loaded-state surface and no measured force-time or
  displacement-time history.

The immediate goal is unchanged: estimate a noise-aware **plausible region**
for the two effective Genesis parameters

```text
log10_E = log10(E / Pa)
phi_deg = friction angle in degrees
```

from this one residual surface transition. Do not claim recovery of unique or
true soil properties.

Gaussian-splat deformation remains a later milestone. The current milestone is
to make the Genesis forward model reproduce the observed residual DEM as well
as the available data permit.

## Correct physical interpretation

The real action is idealized in Genesis as follows:

1. Create a dynamic rigid cylinder with the measured geometry and mass.
2. Position its bottom face at first contact with the initial terrain surface at
   the resolved contact location.
3. Set its initial linear and angular velocities to zero.
4. Release it under gravity with no commanded downward motion and no added
   force.
5. Let the coupled cylinder--terrain system settle according to a fixed
   equilibrium criterion.
6. Remove the cylinder using one fixed, documented numerical protocol.
7. Let the terrain settle again according to a fixed equilibrium criterion.
8. Project the terminal terrain surface to the same DEM grid as the real data.

Accordingly:

- Downward `vertical_speed_mps` is not a real action input.
- `target_depth_m` is not prescribed.
- Cylinder penetration is an output of each candidate simulation.
- `mass_kg` is a required control variable, not metadata.
- No additional applied force should be introduced.
- Quasi-static does not mean commanding a downward speed of zero. Here, zero is
  the cylinder's **initial velocity at release**; its later motion results from
  gravity and contact forces.

The hand placement before release and the hand removal were not measured. They
must not be reconstructed as if they were known trajectories. Their numerical
idealizations are fixed model assumptions whose sensitivity must be reported.

## Replacement action schema

Replace the displacement-controlled fields in
`data/single_trial_real3/action.yaml` with the following schema:

```yaml
tool: cylinder
radius_m: 0.14605
height_m: 0.0508
mass_kg: 1.5

# Required. Resolve from recorded localization/geometry when available. If it
# must be estimated from the residual DEM, document the estimator and freeze the
# resulting value before the material sweep.
contact_center_xy_world_m: [null, null]

placement:
  mode: mass_controlled
  initial_condition: first_contact
  initial_linear_velocity_mps: [0.0, 0.0, 0.0]
  initial_angular_velocity_radps: [0.0, 0.0, 0.0]
  release_under_gravity: true
  additional_applied_force_n: [0.0, 0.0, 0.0]

loaded_settling:
  max_time_s: 5.0
  max_cylinder_speed_mps: 0.0005
  max_particle_speed_mps: 0.0005
  required_duration_s: 0.25

# This is a fixed simulation protocol, not a claimed measurement of the real
# hand trajectory. Prefer a slow vertical kinematic lift and test sensitivity.
removal:
  mode: kinematic_vertical_lift
  vertical_speed_mps: 0.005
  clearance_above_initial_surface_m: 0.010

post_removal_settling:
  max_time_s: 5.0
  max_particle_speed_mps: 0.0005
  required_duration_s: 0.25

calibration_ready: false
```

The numerical thresholds and removal speed above are initial simulation
settings, not measured facts. They must be recorded in the resolved
configuration and checked with sensitivity runs.

Do not include these obsolete fields:

```text
placement.mode: displacement_controlled
placement.vertical_speed_mps
placement.target_depth_m
hold_time_s
post_removal_settle_time_s as the sole stopping rule
```

If the actual duration for which the cylinder remained on the bed is known, it
may be stored as observational metadata. It is not required to drive the
simulation after equilibrium has been reached.

## Contact-location handling

`contact_center_xy_world_m` is still needed to compare the simulated and real
deformation in a shared frame. Resolve it in this order:

1. Use a directly localized cylinder center if one was recorded.
2. Otherwise use scene geometry that independently identifies the placement
   location.
3. If neither exists, estimate the center once from the residual deformation
   footprint, record the estimator and uncertainty, and freeze the result before
   evaluating material candidates.

Do not optimize contact center independently for every `(log10_E, phi_deg)`
candidate. That would allow pose error to absorb material-model error. Run a
small fixed-center perturbation test to quantify the effect of center
uncertainty.

## Required implementation change

The current entry points are designed around prescribed indentation depth:

```text
scripts/run_genesis_indenter_test.py
scripts/run_indenter_matrix_sweep.py
```

They may be reused only after adding a genuine mass-controlled mode. The real
forward-model path must:

- Instantiate the cylinder as a dynamic rigid body with the specified mass and
  corresponding inertia.
- Place the bottom face at a documented first-contact height.
- Start with zero linear and angular velocity.
- Enable gravity and two-way rigid--MPM contact.
- Avoid a prescribed downward pose, speed, depth, or force after release.
- Stop loaded settling by the documented equilibrium criterion or maximum
  duration.
- Log equilibrium cylinder pose and penetration as outputs.
- Apply the fixed removal protocol.
- Stop post-removal settling by the documented equilibrium criterion or maximum
  duration.
- Restore exactly the same settled terrain base before every material
  candidate.

Add an explicit mode at the loader boundary, for example:

```text
--action-mode mass_controlled
```

The runner must reject configurations that combine `mass_controlled` with
`target_depth_m`, a prescribed downward trajectory, or an added downward
force.

## First-contact convention

Document all of the following before calibration:

- Bed/world vertical axis and positive direction.
- Whether the cylinder pose represents center of mass, geometric center, or
  bottom-face center.
- The method used to obtain terrain height below the footprint.
- The first-contact rule used for a nonplanar `S0`.

For the initial implementation, define first contact as the lowest cylinder
bottom-face height that touches the initial terrain without overlap. Use one
fixed robust surface statistic and record it. Because local roughness may alter
the effective drop/contact state, test a small range of initial clearances, such
as `0`, `1`, and `2` mm, without optimizing clearance per material candidate.

## Revised readiness gates

The following gates replace the action blockers in `CURRENT_STATE(1).md`:

1. Cylinder radius, height, and mass are verified.
2. Contact center is resolved and its source is documented.
3. Cylinder mass and inertia are applied by the Genesis rigid-body model.
4. First-contact pose and axis/sign conventions are unit tested.
5. A released cylinder moves only under gravity and contact; no prescribed
   downward motion or force remains active.
6. Two-way rigid--MPM contact is verified with a single midrange material.
7. Loaded and post-removal equilibrium checks terminate correctly.
8. The same settled volumetric base is restored for every rollout.
9. Simulated `S0` and `S1` are projected to the exact real DEM grid and mask.
10. The provisional noise scale is replaced using two-view disagreement and/or
    a static undeformed border.
11. The cylinder footprint is overlaid on `delta_h_real` before calibration.

Until these gates pass, the real material sweep remains invalid. Synthetic
debugging and recovery tests are still allowed.

## Revised calibration procedure

Only vary:

```text
log10_E
phi_deg
```

Keep density, Poisson ratio, contact friction, cohesion, gravity, particle/grid
resolution, settled initial state, contact center, first-contact convention,
equilibrium thresholds, and removal protocol fixed.

Use the existing shared-grid residual comparison:

```text
delta_h_real = S1_height - S0_height
delta_h_sim  = S1_sim_height - S0_sim_height
```

and retain the composite loss already specified in `CURRENT_STATE(1).md`:

```text
L = 0.50 * L_height
  + 0.15 * L_depth
  + 0.20 * L_radial
  + 0.15 * L_volume
```

Execution order:

1. Update and validate `action.yaml` using the mass-controlled schema.
2. Add mass-controlled mode to the Genesis runner.
3. Unit test first contact, mass/inertia, gravity release, and rejection of
   incompatible displacement controls.
4. Run one midrange candidate at `(log10_E=5.5, phi_deg=30)`.
5. Confirm nonzero gravitational settling, stable contact, plausible
   penetration, cylinder equilibrium, removal, and post-removal settling.
6. Verify deterministic base restoration and terminal DEM projection.
7. Implement or verify the composite loss and candidate logging.
8. Run a `3 x 3` smoke grid.
9. Run synthetic parameter recovery using the mass-controlled runner.
10. Replace the provisional real-scan noise estimate.
11. Run the full `8 x 8` grid over:

```text
log10_E in [4, 7]
phi_deg in [15, 45]
```

12. Report the loss landscape and a noise-aware plausible region.
13. Run fixed-protocol sensitivity experiments described below.

## Required sensitivity experiments

Because the real placement/removal histories were not measured, report whether
the fitted region changes materially under:

- Initial clearance/contact convention: nominal and small fixed perturbations.
- Contact-center perturbations based on localization uncertainty.
- Removal speed: `0.5x`, `1x`, and `2x` the nominal lift speed.
- Equilibrium thresholds or maximum settling durations.
- At least one reasonable fixed rigid--terrain contact-friction alternative if
  contact friction is not independently measured.

These are sensitivity analyses, not extra calibration dimensions. Do not choose
the protocol variant that merely produces the lowest real-data loss.

There is no downward-speed sensitivity test because no downward speed is
commanded in the corrected experiment.

## Outputs to add

In addition to the outputs already required by `CURRENT_STATE(1).md`, log:

```text
action_mode
cylinder mass and inertia
initial cylinder pose
first-contact convention
initial clearance
loaded equilibrium cylinder pose
equilibrium penetration depth (simulation output)
loaded-settling termination reason
removal protocol
post-removal termination reason
center/contact/removal sensitivity results
```

Do not populate a real `target_depth_m`; no such command or measurement exists
for this trial.

## Interpretation and limitations

This correction makes the simulator consistent with the real action, but it
does not make the single transition strongly identifiable.

- Only the residual post-removal surface is observed.
- Equilibrium penetration and reaction force were not measured.
- The placement and removal trajectories were not recorded.
- Several `(log10_E, phi_deg)` pairs may reproduce similar residual surfaces.
- Effective `E` may be especially weakly constrained because elastic response
  during loading was not observed.
- Errors in contact friction, bed compaction, initial state, contact location,
  or the removal idealization can be absorbed into the fitted pair.

Therefore the valid primary result is:

```text
a loss landscape and plausible effective-parameter region
```

not a unique physical estimate. Synthetic recovery, scan-noise perturbations,
and protocol-sensitivity tests are required to show what this one experiment
can actually constrain.

## Superseded statements in the current-state document

Treat the following statements in `CURRENT_STATE(1).md` as obsolete:

- The cylinder is a displacement-controlled indenter.
- `placement.mode` should become `displacement_controlled`.
- `mass_kg` is metadata only.
- Insertion speed and target depth are required physical values.
- A target-depth reference is required for the real action.
- Downward speed sensitivity at `0.5x`, `1x`, and `2x` is required.
- The existing prescribed-depth runner is already a plausible real
  forward-model entry point without a mass-controlled extension.

All preprocessing results, real DEM statistics, settled volumetric-bed
requirements, loss definition, uncertainty requirements, prohibited parameter
expansion, and the decision to defer splat deformation remain in force unless
explicitly changed above.

# Single-Trial Genesis MPM Calibration

## Goal

Integrate the single-trial calibration plan with the current `tera_splat`
pipeline and the RealSense real3 artifacts in:

```text
../lamp/ros2_ws/src/realsense_splat
```

Estimate only two effective Genesis MPM parameters from one real terrain
interaction:

```text
theta = (log10_E, phi_deg)
```

The output is an effective Genesis parameter estimate and plausible parameter
region for this measured setup, not a claim of unique real geotechnical material
properties.

## RealSense Data Already Available

Useful package docs:

```text
../lamp/ros2_ws/src/realsense_splat/README.md
```

The recorder uses `bed` as the world frame and
`camera_color_optical_frame` as the camera frame. Recorded depth scale is:

```text
depth_scale_m_per_unit: 0.001
```

Relevant real3 artifacts:

```text
../lamp/ros2_ws/src/realsense_splat/episodes/real3_compare_metrics_3tag/real3_dem_report_3tag.json
../lamp/ros2_ws/src/realsense_splat/episodes/real3_compare_metrics_3tag/before_dem_3tag.npy
../lamp/ros2_ws/src/realsense_splat/episodes/real3_compare_metrics_3tag/after_dem_3tag.npy
../lamp/ros2_ws/src/realsense_splat/episodes/real3_compare_metrics_3tag/after_icp_aligned_dem_3tag.npy
../lamp/ros2_ws/src/realsense_splat/episodes/real3_compare_metrics_3tag/after_fused_points_icp_aligned.ply
../lamp/ros2_ws/src/realsense_splat/episodes/real3_pre_metrics_offline/
../lamp/ros2_ws/src/realsense_splat/episodes/real3_post_metrics_offline/
../lamp/ros2_ws/src/realsense_splat/episodes/real3_single_view_extract/
```

The 3-tag DEM report records:

```text
before_points: 95074
after_points: 105127
cell_size_m: 0.01
bounds_xy_m: [-0.75, 0.75, -0.75, 0.75]
direct median_change_m: -0.004533652836303314
direct p05_m: -0.020956224004381584
direct cut_volume_m3: -0.015604724772013683
icp_aligned median_change_m: -0.003966818893742027
icp_aligned p05_m: -0.020171034773506017
icp_aligned cut_volume_m3: -0.01459486115823346
```

Single-view extraction report gives selected RGB-D frames and pose quality for
4-tag captures. These are useful for diagnostics and visualization, but the
calibration loss should prefer fused DEM products where available.

## Data Contract For Calibration

Use a single trial directory under `tera_splat` for normalized inputs:

```text
data/single_trial_real3/
  manifest.yaml
  action.yaml
  processed/
    S0_fused.ply
    S1_fused.ply
    S1_fused_icp_aligned.ply
    S0_height.npz
    S1_height.npz
    delta_h_real.npz
    valid_mask.npz
    noise_stats.json
```

Initial integration can symlink or copy from `realsense_splat` outputs, but the
calibration runner should consume only this normalized contract.

Required manifest fields:

```yaml
trial_id: real3_single_trial
length_unit: meter
angle_unit: degree
world_frame: bed
camera_frame: camera_color_optical_frame
depth_scale_m_per_unit: 0.001
height_cell_size_m: 0.01
source_package: ../lamp/ros2_ws/src/realsense_splat
roi_world:
  x_min: -0.75
  x_max: 0.75
  y_min: -0.75
  y_max: 0.75
```

Action fields must be completed before calibration. The current calibration
milestone uses mass-controlled gravitational loading, not prescribed target-depth
indentation:

```yaml
tool: cylinder
geometry:
  diameter_m: 0.14605
  radius_m: 0.073025
  height_m: 0.0508
rigid_body:
  mass_kg: 1.5
  equivalent_uniform_density_kg_m3: 1762.522
  inertia_model: uniform_solid_cylinder_approximation
  inertia_diagonal_kg_m2: [0.002322324, 0.002322324, 0.003999488]
contact_center_xy_world_m: [0.0, 0.0]
placement:
  mode: mass_controlled
  initial_condition: first_contact
  initial_linear_velocity_mps: [0.0, 0.0, 0.0]
  initial_angular_velocity_radps: [0.0, 0.0, 0.0]
  release_under_gravity: true
  additional_applied_force_n: [0.0, 0.0, 0.0]
first_contact:
  surface_statistic: percentile
  percentile: 99.0
  nominal_clearance_m: 0.0
loaded_settling:
  max_time_s: 5.0
  cylinder_speed_threshold_mps: 0.0005
  local_particle_speed_percentile: 99
  particle_speed_threshold_mps: 0.0005
  required_duration_s: 0.25
removal:
  mode: kinematic_lift_after_loaded_equilibrium
  upward_speed_mps: 0.005
  clearance_above_surface_m: 0.010
post_removal_settling:
  max_time_s: 5.0
  local_particle_speed_percentile: 99
  particle_speed_threshold_mps: 0.0005
  required_duration_s: 0.25
```

Fail loudly if units, depth scale, transforms, DEM cell size, or action fields
are missing.

Critical geometry correction: `0.14605 m` is the cylinder diameter, not radius.
The correct radius is `0.073025 m`. Using `radius_m: 0.14605` makes the contact
area four times too large and nominal pressure four times too small.

### Action Semantics

The intended sequence is:

1. Create a dynamic rigid cylinder with measured geometry and mass.
2. Place its bottom face at the 99th-percentile first-contact height within the
   fixed footprint.
3. Set initial linear and angular velocities to zero.
4. Release under gravity with no commanded downward motion and no added force.
5. Stop loaded settling by the fixed equilibrium criterion or max duration.
6. Remove using the fixed kinematic vertical-lift protocol.
7. Stop post-removal settling by the fixed equilibrium criterion or max duration.
8. Extract the residual simulated surface.

Cylinder penetration is an output of each candidate simulation. Do not include
or populate `target_depth_m` for this real trial.

The action loader must document:

- World/bed vertical axis and sign.
- Indenter pose point: center, center of mass, or bottom face.
- First-contact height rule for nonplanar `S0`.
- How mass and inertia are applied in Genesis.
- Loaded and post-removal equilibrium thresholds.
- Removal protocol and whether removal speeds are positive magnitudes or signed
  world-axis velocities.

Normalize these conventions once at the loader boundary. Add tests for vertical
sign, pose point, first-contact calculation, mass/inertia application, gravity
release, and rejection of incompatible displacement controls.

## Calibration Model

Treat Genesis as the forward model:

```text
S1_hat(log10_E, phi_deg) = residual surface after load, removal, and settling
```

Only vary:

- `log10_E`
- `phi_deg`

Fixed across all candidates:

- density
- Poisson ratio
- contact friction
- particle spacing
- grid resolution
- bed depth
- gravity
- boundary conditions
- mass-controlled action protocol
- initial settled state

Restore the exact same deterministic settled initial state before every
candidate rollout.

Use the phrase **effective Genesis parameters** in reports. With one residual
scan, a diagonal or flat loss ridge is a valid outcome, not an optimizer failure.

## Loss

Use deformation fields, not Chamfer distance alone.

Primary real target:

```text
delta_h_real = h1 - h0
```

Composite loss:

```text
L = 0.50 * L_height
  + 0.15 * L_depth
  + 0.20 * L_radial
  + 0.15 * L_volume
```

Terms:

- Height-field Huber loss over valid cells.
- Depression depth using a robust low percentile, not one minimum cell.
- Radial median deformation profile around cylinder center.
- Cut/fill volume error.

Set Huber delta and plausible-region threshold from scan noise, ideally from
two-view disagreement and static border cells. Until that is computed, use the
DEM report values as diagnostics, not as final uncertainty.

Before final calibration, correct relative pre/post scan bias using only a
known or assumed undeformed static border:

```text
delta_h_corrected(x, y) = h1(x, y) - h0(x, y) - (a*x + b*y + c)
```

If rotation is already constrained by localization, fit only the vertical offset
`c`. Do not use unconstrained ICP over the deforming surface.

## Search

Do not launch the full sweep immediately. First run one midrange candidate, then
a `3 x 3` smoke grid, then the full landscape.

Start the full landscape with an explicit grid:

```text
log10_E in [4, 7], 8 values
phi_deg in [15, 45], 8 values
```

Then refine around competitive basins with about 20-30 more candidates.

For every candidate save:

```text
candidate_id
log10_E
E_pa
phi_deg
resolved_config_hash
initial_state_hash
action_hash
status
runtime_s
loss_total
loss_height
loss_depth
loss_radial
loss_volume
output_paths
```

Report the full loss landscape, not only the best point.

For every completed candidate, also save enough hashes/metadata to make reruns
skippable only when the resolved config, initial-state hash, and action hash
match.

## Readiness Gate

Before the full `8 x 8` search, one candidate must pass all checks:

- Action metadata has no unresolved required fields.
- Tool radius, height, mass, contact center, first-contact height rule, and
  pose convention are visually verified.
- Radius is `0.073025 m`; `0.14605 m` appears only as diameter.
- Static-border vertical/plane bias correction has been applied.
- Separate localized views are exported for both `S0` and `S1`, and two-view
  noise produces the final Huber threshold.
- Simulated and real bed axes, units, origin, and ROI agree.
- The indenter footprint overlays the intended real deformation region.
- Initial simulated and real reference surfaces are compared on the same grid.
- The terminal simulation is projected to the exact existing DEM grid.
- The complete settled MPM state is restored, not only particle positions.
- No-cylinder drift is characterized or subtracted per material candidate.
- Duplicate rollouts agree within numerical tolerance.
- The mass-controlled runner rejects target depth, prescribed downward motion,
  and added downward force for this real action.
- The released cylinder moves only under gravity and coupled contact.
- Free-fall gravity, runtime mass, two-way contact, and mass monotonicity tests
  pass.
- Loaded and post-removal settling stop from the documented equilibrium checks.
- A real-vs-simulated `delta_h` overlay is generated with a shared color scale.
- All non-target physics values are recorded in a resolved configuration.

Use `(log10_E=5.5, phi_deg=30)` only as a pipeline smoke test, not as a material
assumption.

## Required Outputs

Each calibration run should retain:

```text
resolved_config.yaml
environment.json
results.csv
noise_stats.json
initial_state_metadata.json
action_resolved.yaml
candidate diagnostics and terminal state references
total/component loss heatmaps
best real/sim delta_h comparison
best difference map
best radial-profile plot
plausible-region plot
synthetic-recovery results
determinism results
report.md
```

`environment.json` should include git commit, Genesis version, device, seed, and
important package versions.

## Verification

There is no honest held-out real action yet. Do not construct a train/test claim
from patches of the same crater.

Required verification before a final report:

- Unit/coordinate tests for pose composition, depth units, DEM projection,
  vertical sign, first-contact height, and degree/radian conversion.
- State restore/recreation determinism.
- Free-fall, mass/inertia, two-way contact, and mass-monotonicity coupling
  tests.
- Synthetic parameter recovery using at least three known `(log10_E, phi_deg)`
  pairs.
- Observation perturbation/bootstrap using measured scan noise.
- Optional inner-ROI versus outer-annulus comparison labeled only as a spatial
  diagnostic.

Run protocol sensitivity checks near the best candidate:

- Initial first-contact/clearance convention.
- Contact-center perturbations within measured uncertainty.
- Removal speed at `0.5x`, `1x`, and `2x` the nominal lift speed.
- Loaded and post-removal equilibrium thresholds.
- Fixed contact-friction alternatives.

There is no downward-speed sensitivity test because the real action has no
commanded downward speed.

## Implementation Steps

Implemented:

1. `scripts/preprocess_single_trial_real3.py` normalizes real3 inputs into
   `data/single_trial_real3/`.
2. `scripts/make_single_trial_report.py` creates a Markdown readiness report.
3. The normalized data includes height `.npz` files, `delta_h_real`, valid mask,
   provisional noise stats, copied center-ROI PLYs, manifest, action template,
   and source-report copies.
4. Static-border plane correction, footprint coverage diagnostics, and
   corrected `delta_h` are generated.
5. `scripts/run_mass_controlled_bridge_checks.py` validates dynamic free fall,
   runtime mass, and inertia for the corrected cylinder.
6. Short terrain gravity smokes show monotonic sinkage for `0.75`, `1.5`, and
   `3.0 kg` over `0.04 s`, but do not replace equilibrium/removal validation.
7. `scripts/run_mass_controlled_terrain.py` implements the first load,
   removal, and post-removal phase machine. The current CPU smoke is capped and
   intentionally times out, so it proves artifact wiring but not calibration
   readiness.

Current generated report:

```text
reports/single_trial_real3_report.md
```

Run:

```bash
conda run -n tsplat python scripts/preprocess_single_trial_real3.py --copy-plys
conda run -n tsplat python scripts/make_single_trial_report.py \
  --output reports/single_trial_real3_report.md
```

Still to implement before real calibration:

1. Verify the `[0.0, 0.0]` center footprint overlay; do not optimize center from
   material-candidate loss.
2. Review the generated static-border scan correction and footprint diagnostic.
3. Preserve/export separate localized views for `S0` and `S1`, then estimate
   final two-view noise.
4. Add mass-controlled mode to the Genesis runner and action loader.
5. Verify free-fall gravity, runtime mass/inertia, two-way contact, and mass
   monotonicity.
6. Verify bed/world/DEM transforms and overlay the cylinder footprint on the
   real deformation.
7. Verify initial simulated `S0` projection against the real `S0` grid.
8. Add complete MPM state restore or deterministic reconstruction.
9. Characterize/subtract no-cylinder drift per material candidate if needed.
10. Add a Genesis calibration runner that reuses the settled base and
   mass-controlled cylinder action.
11. Add loss computation and write per-candidate JSON/CSV rows.
12. Add a coarse grid script over `log10_E` and `phi_deg`.
13. Add report generation: heatmaps, best candidate, plausible region, and
   failure table.
14. Run midrange single-candidate smoke.
15. Run duplicate rollout determinism check.
16. Run synthetic `3 x 3` parameter-recovery tests.
17. Run real `3 x 3` smoke grid.
18. Run full `8 x 8` real-data grid.
19. Refine competitive basin(s).
20. Run protocol sensitivity and scan-noise perturbation analyses.
21. Generate final report and update `docs/current_state.md`.

The existing indenter runner can be reused only after adding a genuine
`mass_controlled` mode. That mode must reject `target_depth_m`, prescribed
downward trajectories, and added downward forces for this real trial.

## Non-Goals

- Do not tune density, Poisson ratio, gravity, contact friction, cohesion, or
  hidden state in this first calibration.
- Do not jointly optimize camera extrinsics or scale.
- Do not train a neural network from one example.
- Do not call spatial patches a real validation split.
- Do not change Genesis update equations for this calibration.
- Do not implement Gaussian appearance/covariance deformation in this step.
- Do not tune loss weights after seeing which values favor a desired parameter pair.
- Do not use unconstrained ICP on the deforming surface.
- Do not prescribe target depth for this real trial.
- Do not add a downward force beyond gravity.

## Current Blocking Questions

These must be resolved before a real calibration run:

- Center footprint overlay verification for `[0.0, 0.0]`.
- Static-border scan bias correction.
- Separate two-view exports and final two-view noise estimate.
- Genesis support for dynamic rigid-cylinder release with mass and inertia.
- Two-way rigid-MPM contact validation.
- Free-fall and mass-monotonicity validation.
- Fixed removal speed/clearance and loaded/post-removal equilibrium thresholds.
- Which DEM is the calibration target: direct localized DEM or ICP-aligned DEM.
- Complete MPM state restore and no-cylinder drift handling.

## Later Extension

When a second real action is available, freeze the plausible parameter set from
this trial and predict the second residual surface without refitting. That is
the first genuine transfer test.

After calibration is stable, expose terminal Genesis particle positions,
deformation gradients, plastic/volume state, and active masks for splat coupling.
That coupling is outside the present two-parameter calibration task.

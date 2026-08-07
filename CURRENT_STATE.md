# Current Experiment State

Last updated: 2026-08-06

This document is the concise handoff for the current experiment set after the
mass-controlled amendment.

## Objective

Calibrate two effective Genesis MPM sand parameters from one RealSense
before/action/after sand-bed experiment:

```text
log10_E = log10(E / Pa)
phi_deg = friction angle in degrees
```

The real action was placement of a known cylinder on the sand bed, not an
intentional push to a target depth. The valid forward model is therefore
**mass-controlled gravitational loading**:

1. Put the cylinder bottom face at first contact with the initial terrain.
2. Release it with zero initial linear/angular velocity.
3. Let gravity and coupled rigid-MPM contact determine penetration.
4. Stop loaded settling by a fixed equilibrium criterion.
5. Remove the cylinder with a fixed documented numerical lift protocol.
6. Stop post-removal settling by a fixed equilibrium criterion.
7. Compare the residual simulated surface to the real residual DEM.

The output should be a loss landscape and plausible region for **effective
Genesis parameters**, not unique physical soil properties. Gaussian-splat
deformation is outside this milestone.

## Environment

Run from:

```text
/home/moog-2/christo/splatting_stuff/physical/tera_splat
```

Use:

```text
conda env: tsplat
```

CUDA is available on the host but may be hidden inside sandboxed commands. Use
an unsandboxed execution path for CUDA Genesis jobs.

## Source Inputs

```text
EDGS splat:        ../EDGS/output/point_cloud/iteration_7000/point_cloud.ply
PhysGaussian:      ../PhysGaussian/
RealSense package: ../lamp/ros2_ws/src/realsense_splat/
real3 artifacts:   ../lamp/ros2_ws/src/realsense_splat/episodes/real3_compare_metrics_3tag/
```

RealSense convention used by normalized data:

```text
world frame: bed
camera frame: camera_color_optical_frame
depth_scale_m_per_unit: 0.001
```

## Normalized Real Trial

Regenerate:

```bash
conda run -n tsplat python scripts/preprocess_single_trial_real3.py --copy-plys
conda run -n tsplat python scripts/make_single_trial_report.py \
  --output reports/single_trial_real3_report.md
```

Normalized output:

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
    preprocess_summary.json
```

Current report:

```text
reports/single_trial_real3_report.md
```

Real deformation summary:

```text
DEM: center 1 ft, 0.005 m/cell
ROI: [-0.1524, 0.1524, -0.1524, 0.1524] m in bed frame
shape: 61 x 61
valid overlap cells: 1038
valid area: 0.02595 m^2
mean change: 0.00313604613 m
median change: 0.00347291209 m
p05: -0.00668277459 m
p95: 0.012975668 m
cut volume: -3.94610965e-05 m^3
fill volume: 0.000120841494 m^3
net volume: 8.13803971e-05 m^3
```

Noise estimate:

```text
provisional Huber delta: 0.00880404522 m
source: ICP RMSE / direct-vs-ICP DEM delta proxy
```

This is provisional. Replace it with two-view disagreement and/or static-border
residuals before final calibration.

## Current Action Metadata

Current file:

```text
data/single_trial_real3/action.yaml
```

Current schema:

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
calibration_ready: false
```

Completed bridge steps:

- Static-border plane correction is implemented and saved in
  `data/single_trial_real3/processed/delta_h_real_corrected.npz`.
- Footprint/mask diagnostic is saved at
  `data/single_trial_real3/processed/scan_correction_footprint_diagnostic.png`.
- Raw median `delta_h` was `+0.00347291209 m`; plane-corrected median
  `delta_h` is `+0.0000524610803 m`.
- Plane-corrected net volume is `-2.30016048e-06 m^3`.
- First-contact height using the 99th percentile inside the footprint is
  `0.0464380514 m`; zero-clearance cylinder center z is `0.0718380514 m`.
- Genesis free-fall/mass check passed on CPU:
  `outputs/mass_controlled_bridge_checks/free_fall_report.json`.
- Runtime mass after override is `1.5 kg`; fitted vertical acceleration is
  `-9.80977783 m/s^2`; runtime inertia diagonal matches the expected uniform
  solid-cylinder approximation.
- Short terrain gravity smoke using the existing gravity control path completed
  for `0.75`, `1.5`, and `3.0 kg`.
- Short-run sinkage was monotonic over `0.04 s`:
  `0.00132496872 m`, `0.00242455521 m`, `0.00399621048 m`.
- `scripts/run_mass_controlled_terrain.py` implements the load, removal, and
  post-removal phase machine for a released cylinder.
- Capped CPU smoke output:
  `outputs/mass_controlled_bridge_checks/mass_controlled_terrain_smoke_cpu_capped`.
- Capped smoke loaded depth was `0.00160224953 m`; loaded and post-removal
  phases timed out under deliberately short limits, and removal was capped.
- Longer CUDA rollout with uncapped removal completed:
  `outputs/mass_controlled_bridge_checks/mass_controlled_terrain_cuda_longer`.
- Longer CUDA result: loaded phase timed out after `0.25 s` at
  `0.00289781609 m` depth; removal completed uncapped in `5160` steps; post
  removal reached equilibrium in `0.02 s`.
- Extended CUDA loaded-settling output:
  `outputs/mass_controlled_bridge_checks/mass_controlled_terrain_cuda_loaded1s`.
  The loaded phase still timed out at `1.0 s`, but depth was stable at
  `0.00289662399 m`. The cylinder speed was `0.292996793 mm/s` while local p99
  particle speed was `0.672453374 mm/s`, exceeding the `0.5 mm/s` threshold.
- The runner now writes a loaded-phase percentile diagnostic. For a second
  `1.0 s` CUDA baseline, penetration drift was zero at stored float32 precision
  over the last `0.1 s`; local p95 was `0.188-0.205 mm/s` and p99 was
  `0.670-0.720 mm/s`. This motivates threshold sensitivity, not a protocol
  change based on one material/mass case.

Current blockers:

1. Center footprint overlay has an artifact but is not independently visually
   accepted. The current `[0.0, 0.0]` assumes the bed-frame origin is the
   physical center.
2. Static-border correction depends on an assumed undeformed border. Valid
   static-border coverage is only `0.231`, so this assumption still needs review.
3. Two localized views per surface are not exported separately for final
   two-view noise estimation.
4. Genesis mass-controlled terrain action mode has a runner and reproducible
   uncapped CUDA removal, but not a calibration-ready loaded-equilibrium rule.
5. Two-way rigid-MPM contact has only short smoke tests. It is not validated
   through loaded equilibrium and removal.
6. Settled/equilibrium mass monotonicity is not tested for `0.75`, `1.5`, and
   `3.0 kg`.
7. Loaded-settling termination logic is implemented but not validated: the
   particle-speed criterion times out even after penetration stabilizes.
8. Post-removal settling termination logic is implemented and has a CUDA smoke,
   but is not yet validated across material and mass cases.
9. Initial simulated `S0` projection/footprint match is not verified.
10. Complete MPM state restore is not implemented or validated. A PLY with only
    positions is not enough state for calibrated rollouts.
11. No-cylinder drift is not characterized or subtracted.
12. Synthetic `3 x 3` parameter recovery is not complete.
13. Final scan-noise estimate is missing. The current Huber delta is only an ICP
   RMSE / direct-vs-ICP proxy.

Critical correction: `0.14605 m` is the cylinder diameter, not radius. The
correct radius is `0.073025 m`. Using `radius_m: 0.14605` makes contact area
four times too large and nominal pressure four times too small.

Do not add `placement.target_depth_m`; no target depth was commanded or
measured. Cylinder penetration is a simulation output.

## Simulation Baseline

Do not calibrate from raw surface-only splat particles. Use the settled
volumetric/subsurface-supported base:

```text
assets/base_settled_stiff_mid/
  particles_initial_mpm.ply
  ground_plane_metadata.json

configs/physgaussian_sand_stiff_mid.json
```

Every material candidate must restore or deterministically recreate the same
settled base state.

Current indenter entry points:

```bash
conda run -n tsplat python scripts/run_genesis_indenter_test.py --help
conda run -n tsplat python scripts/run_indenter_matrix_sweep.py --help
conda run -n tsplat python scripts/run_mass_controlled_terrain.py --help
```

Important discrepancy: these scripts were originally built around prescribed
indent depth. They may be reused only after adding a genuine `mass_controlled`
mode that rejects target-depth, prescribed downward motion, and added downward
force.

## What Can Be Run Now

Safe/current:

```bash
conda run -n tsplat python scripts/preprocess_single_trial_real3.py --copy-plys
conda run -n tsplat python scripts/make_single_trial_report.py \
  --output reports/single_trial_real3_report.md
conda run -n tsplat python scripts/run_genesis_indenter_test.py --help
conda run -n tsplat python scripts/run_indenter_matrix_sweep.py --help
```

Allowed only as synthetic/debug work:

- Add/test mass-controlled Genesis release mode.
- One midrange synthetic candidate after contact center and first-contact
  convention are fixed.
- Synthetic recovery using generated observations.

Not valid yet:

- Real `log10_E` / `phi_deg` calibration sweep.
- Real `3 x 3` or `8 x 8` material search.
- Any report claiming a real material fit.

Reason: footprint/static-border review, final two-view noise estimation,
Genesis mass-controlled terrain release, two-way rigid-MPM contact, settling
termination, deterministic state restoration, no-cylinder drift, and synthetic
recovery are not complete.

## Required Mass-Controlled Implementation

The real forward-model path must:

1. Instantiate a dynamic rigid cylinder with specified mass and inertia.
2. Place its bottom face at documented first contact.
3. Set initial linear/angular velocities to zero.
4. Enable gravity and two-way rigid-MPM contact.
5. Avoid prescribed downward pose, speed, target depth, or added force.
6. Stop loaded settling by equilibrium thresholds or max duration.
7. Log equilibrium cylinder pose and penetration as outputs.
8. Apply the fixed removal protocol.
9. Stop post-removal settling by equilibrium thresholds or max duration.
10. Restore the same settled terrain base before every candidate.

Suggested loader/runner boundary:

```text
--action-mode mass_controlled
```

The runner must reject configs that combine `mass_controlled` with
`target_depth_m`, prescribed downward trajectory, or added downward force.

## Calibration Procedure Once Ready

Only vary:

```text
log10_E
phi_deg
```

Everything else is fixed and recorded.

Execution order:

1. Verify the `[0.0, 0.0]` center footprint overlay on `S0` and the observed
   residual deformation.
2. Correct static-border vertical/plane bias and estimate two-view noise.
3. Add mass-controlled mode to the Genesis runner.
4. Unit test first contact, mass/inertia, gravity release, and rejection of
   incompatible displacement controls.
5. Verify free-fall gravity, runtime mass, two-way contact, and mass
   monotonicity.
6. Verify real/sim axes, units, ROI, DEM grid, masks, and initial `S0`
   projection/footprint overlay.
7. Implement complete state restore and no-cylinder drift characterization.
8. Run one midrange candidate: `(log10_E=5.5, phi_deg=30)`.
9. Confirm nonzero gravitational settling, stable contact, plausible
   penetration, cylinder equilibrium, removal, and post-removal settling.
10. Repeat exact rollout twice and confirm determinism.
11. Project simulated terminal surface to the exact real DEM grid.
12. Implement or verify composite loss and candidate logging.
13. Run synthetic `3 x 3` recovery using the mass-controlled runner.
14. Run a real `3 x 3` smoke grid.
15. Run full `8 x 8` grid:

```text
log10_E in [4, 7]
phi_deg in [15, 45]
```

16. Run protocol sensitivity and scan-noise perturbation experiments.
17. Generate final report with loss landscape and plausible region.

Do not jump directly to the full sweep.

## Loss

Use shared-grid residual height fields:

```text
delta_h_real = S1_height - S0_height
delta_h_sim  = S1_sim_height - S0_sim_height
```

Composite loss:

```text
L = 0.50 * L_height
  + 0.15 * L_depth
  + 0.20 * L_radial
  + 0.15 * L_volume
```

Terms:

- Huber height-field loss over common valid mask.
- Robust depression depth from low percentile.
- Radial median deformation profile around fixed cylinder center.
- Cut/fill volume error.

## Required Sensitivity Experiments

Because placement/removal histories were not measured, report sensitivity to:

- First-contact/initial-clearance convention, e.g. nominal, +1 mm, +2 mm.
- Contact-center perturbations from localization/estimator uncertainty.
- Removal speed: `0.5x`, `1x`, `2x`.
- Equilibrium thresholds and max settling durations.
- At least one fixed contact-friction alternative if contact friction is not
  independently measured.

These are sensitivity analyses, not extra calibration dimensions. Do not pick
the protocol variant just because it minimizes real-data loss.

There is no downward-speed sensitivity test because no downward speed is
commanded in the corrected experiment.

## Required Final Outputs

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
protocol-sensitivity results
report.md
```

Also log:

```text
action_mode
cylinder mass and inertia
initial cylinder pose
first-contact convention
initial clearance
loaded equilibrium cylinder pose
equilibrium penetration depth
loaded-settling termination reason
removal protocol
post-removal termination reason
```

## Prohibited Shortcuts

- Do not prescribe target depth for this real trial.
- Do not add a downward force beyond gravity.
- Do not optimize contact center per material candidate.
- Do not infer density, Poisson ratio, contact friction, cohesion, compaction,
  or camera poses in the first calibration.
- Do not use unconstrained ICP over the deforming terrain.
- Do not replace the settled volumetric bed with surface-only splat particles.
- Do not tune loss weights after seeing which candidate looks best.
- Do not claim patch holdouts are independent validation.
- Do not claim a unique physical `E` or `phi` from one residual scan.
- Do not start MPM-to-Gaussian transfer before calibration diagnostics are done.

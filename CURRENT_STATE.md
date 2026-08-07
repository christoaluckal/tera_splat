# Tera Splat Current State

Last reviewed: 2026-08-07

This is the sole live engineering handoff for `tera_splat`. It replaces the
older phase plans, bridge notes, duplicated state documents, and external
instrumentation notes. Update this document whenever the experiment contract,
implemented behavior, validation evidence, or readiness gates change.

Generated reports in `reports/` are evidence for specific runs. They are not
the current plan. External source data remains outside this repository; the
paths below are the authoritative provenance records.

## Mission

Build a contact-conditioned terrain Gaussian-splat prototype that:

1. Starts from a stable, volumetric, splat-derived MPM sand bed.
2. Simulates a measured rigid-cylinder placement under gravity using Genesis
   MPM and two-way rigid-MPM coupling.
3. Compares the simulated terminal surface against RealSense pre/post DEMs.
4. Estimates an effective sand parameter region, initially over `log10_E` and
   `phi_deg` only.
5. Later transfers validated MPM displacement back to the visible splat.

This is effective-model calibration, not a claim of unique geotechnical
properties. Do not tune parameters against an animation alone.

## Repository And Runtime

```text
repository: /home/moog-2/christo/splatting_stuff/physical/tera_splat
environment: conda env tsplat
GPU: NVIDIA GeForce RTX 3060 Ti when CUDA is exposed to the shell
```

CUDA can be hidden by a managed sandbox. Use a CUDA-capable shell for Genesis
rollouts and record the backend/device in each output directory.

## Source Repositories And Provenance

```text
EDGS splat:
../EDGS/output/point_cloud/iteration_7000/point_cloud.ply

PhysGaussian reference implementation:
../PhysGaussian/

RealSense capture and DEM processor:
../lamp/ros2_ws/src/realsense_splat/
```

Do not modify `realsense_splat` while working in this repository unless the
task explicitly requires source-data processing changes. New interpretation,
trial-contract, and calibration decisions belong in this file.

### Coordinate Convention

```text
physical world frame: bed
camera frame: camera_color_optical_frame
depth scale: 0.001 m per raw depth unit
RealSense tag map: real3_tag_map.yaml
nominal tag centers: (+/-0.3048, +/-0.3048) m
```

Real3 and Real4/5/6 use the same approximate 24 x 24 inch tag-center map, so
their nominal bed-frame XY coordinates are compatible. The map is not yet an
independently validated absolute metrology reference. Never silently mix bed,
splat, camera, and solver coordinates: record the transform and validate a
surface/footprint overlay before any fit.

## Terrain And Solver Baseline

Use the settled splat-derived base, not a raw surface-only cloud:

```text
assets/base_settled_stiff_mid/particles_initial_mpm.ply
assets/base_settled_stiff_mid/ground_plane_metadata.json
configs/physgaussian_sand_stiff_mid.json
```

The accepted manual initializer is retained for provenance:

```text
outputs/splat_surface_regular_grid_subsurface_1x1_depth0p2_spacing0p025_layer0p0125_noise1p5/
```

Genesis sand currently uses the parameter/configuration surface established by
the PhysGaussian reference. PhysGaussian remains a comparison implementation;
the active calibration runner is Genesis. Do not change the constitutive law
while establishing the first effective `log10_E` / `phi_deg` fit.

The ground plane is a fixed rigid plane below the MPM particles. It prevents
particles from falling out of the domain; it is not a substitute for matching
the real pre-action bed geometry.

## Physical Action Contract

The real query is **mass-controlled gravitational loading**, never a prescribed
target-depth indentation.

For each trial:

1. Put the cylinder bottom face at a documented first-contact surface height.
2. Set initial linear and angular velocity to zero.
3. Release the dynamic cylinder under gravity with no prescribed downward pose,
   downward speed, target depth, or added downward force.
4. Treat penetration as a simulation output.
5. Detect loaded settling with a frozen, validated criterion.
6. Apply a documented fixed numerical vertical lift for removal.
7. Detect post-removal settling with a frozen criterion.
8. Save particle frames, rigid pose/state, metrics, resolved config, and final
   surface metrics.

The cylinder dimensions are fixed for current real trials:

```text
diameter: 0.14605 m
radius:   0.073025 m
height:   0.0508 m
```

`0.14605 m` is the diameter, not the radius. Using it as a radius quadruples
contact area and invalidates pressure/contact interpretation.

### Real3 Action

```text
mass: 1.5 kg
equivalent density: 1762.522 kg/m^3
inertia diagonal: [0.002322324, 0.002322324, 0.003999488] kg m^2
nominal center: [0.0, 0.0] m
```

The normalized contract is `data/single_trial_real3/action.yaml`.

### Real6 Action

```text
mass: 3.0 kg
equivalent density: 3525.044 kg/m^3
inertia diagonal: [0.004644648, 0.004644648, 0.007998976] kg m^2
nominal center: [0.0135730566, 0.0362158050] m
```

Real6 uses the same cylinder geometry and loading/unloading protocol as Real3,
with mass changed to `3.0 kg`. The Real6 center is inferred from the Real5
during-load feature, not directly measured, so it is a protocol-sensitivity
input. Test the `[-0.10, 0.00, +0.10] m` XY grid separately from material
fitting. Record the confirmed dwell, lift speed, and post-lift wait in the
future Real6 action file.

## RealSense Trial Inventory

| Trial | Source pair | Intended use | Status |
|---|---|---|---|
| Real3 | `real3` center 1 ft pre/post DEM | Historical 1.5 kg calibration target | Normalized; not sweep-ready |
| Real4 | `real4_pre -> real4_post` | Diagnostic only | Broad bias; do not calibrate |
| Real5 | `real5_pre -> during -> after` | Locate contact and inspect loading object | During view is object-contaminated |
| Real6 | `real6_pre -> real6_post` | Next 3 kg calibration target | Source analyzed; adapter not implemented |

### Real3 Artifacts

External source:

```text
../lamp/ros2_ws/src/realsense_splat/episodes/real3_compare_metrics_3tag/
```

Normalized products:

```text
data/single_trial_real3/manifest.yaml
data/single_trial_real3/action.yaml
data/single_trial_real3/processed/S0_height.npz
data/single_trial_real3/processed/S1_height.npz
data/single_trial_real3/processed/delta_h_real.npz
data/single_trial_real3/processed/delta_h_real_corrected.npz
data/single_trial_real3/processed/scan_correction.json
data/single_trial_real3/processed/scan_correction_footprint_diagnostic.png
reports/single_trial_real3_report.md
```

The Real3 static-border plane correction reduced the raw median change from
`+3.473 mm` to `+0.052 mm`. This correction is necessary but remains
provisional because static-border coverage is only `0.231` and final two-view
noise is unavailable.

### Real6 Artifacts

External source:

```text
../lamp/ros2_ws/src/realsense_splat/episodes/real456_static_metrics/
```

Use native bed-frame sources, not ICP visualization products, for the future
calibration target:

```text
real6_pre/dem_points_0.005m.ply
real6_post/dem_points_0.005m.ply
real6_pre/dem_0.005m.npy
real6_post/dem_0.005m.npy
comparisons/real6_post_minus_real6_pre_dem_0.005m.npy
comparisons/real6_post_minus_real6_pre_report.json
force_application_location_report.json
```

Initial read-only analysis used a force-centered 1 ft ROI, the Real6 nominal
center, a `73.025 mm` footprint radius, and a Real3-style static-border plane
fit: outer `25 mm` border, excluding the footprint plus `30 mm`.

```text
common pre/post cells:              57,295
force-centered ROI common cells:     2,645
footprint coverage:                  504 / about 670 cells (75.2%)
corrected footprint median dz:      -1.044 mm
corrected footprint mean dz:        -1.585 mm
corrected footprint p05 / p95:      -5.345 / +1.529 mm
covered-footprint net volume:       -1.997e-5 m^3
corrected annulus p05 / p95:        -0.692 / +0.771 mm
```

The source Real6 ICP crop has fitness `1.0` and final RMSE `1.413 mm`, which is
comparable to the measured signal. Never use an ICP transform fit through the
changed footprint as the calibration registration. Freeze a stable-region
registration/correction convention first.

Real4/5/6 contain mostly three-tag frames and use the approximate tag map.
They are useful static-view diagnostics, not independently validated absolute
bed geometry.

## Implemented Components

### Inspection And Particle Preparation

```text
scripts/view_iteration_7000.py
scripts/particle_io.py
scripts/test_ply_to_particles.py
scripts/view_particle_ply.py
scripts/run_ground_plane_solver.py
scripts/run_genesis_ground_plane_solver.py
```

### Genesis Contact And Visualization

```text
scripts/run_genesis_indenter_test.py
scripts/run_mass_controlled_bridge_checks.py
scripts/run_mass_controlled_terrain.py
scripts/view_solver_animation.py
scripts/render_solver_video.py
scripts/render_indenter_animation.py
scripts/transfer_mpm_to_gaussians.py
```

`run_mass_controlled_terrain.py` currently restores particle positions and
zero velocities from the saved PLY. It does **not** restore full MPM state such
as `C`, `F`, or `Jp`; a PLY alone is insufficient for deterministic calibrated
candidate rollouts.

### RealSense Processing

```text
scripts/preprocess_single_trial_real3.py
scripts/make_single_trial_report.py
```

The Real3 preprocessor is intentionally source-specific: it loads named NPY
products under `real3_compare_metrics_3tag/center_1ft_fine_dem/`. It cannot
consume a Real6 PLY pair without a separate adapter.

## Evidence Already Collected

All paths below are historical test evidence, not clearance to start a sweep.

### Rigid-Body Check

```text
outputs/mass_controlled_bridge_checks/free_fall_report.json
```

For the 1.5 kg Real3 cylinder, Genesis runtime mass/inertia matched the intended
uniform-cylinder approximation and fitted vertical acceleration was
`-9.80977783 m/s^2`.

### Short Contact Smoke

The existing gravity-contact path ran for `0.04 s` on CPU:

```text
0.75 kg -> 1.32497 mm sinkage
1.50 kg -> 2.42456 mm sinkage
3.00 kg -> 3.99621 mm sinkage
```

This demonstrates short-run mass-monotonic contact response only. It does not
demonstrate equilibrium, removal, drift control, or repeatability.

### Mass-Controlled Terrain Phase Machine

Outputs:

```text
outputs/mass_controlled_bridge_checks/mass_controlled_terrain_smoke_cpu_capped
outputs/mass_controlled_bridge_checks/mass_controlled_terrain_cuda_longer
outputs/mass_controlled_bridge_checks/mass_controlled_terrain_cuda_loaded1s
outputs/mass_controlled_bridge_checks/mass_controlled_terrain_cuda_settling_diagnostic_1s
```

The CUDA path completes an uncapped `5 mm/s` numerical lift and detects
post-removal equilibrium. At 1.5 kg, penetration was about `2.897 mm` after
both `0.25 s` and `1.0 s` loaded windows. The loaded phase still timed out:

```text
configured rule: cylinder speed <= 0.5 mm/s AND local p99 <= 0.5 mm/s
final cylinder speed: about 0.293 mm/s
final local p50 / p90 / p95 / p99:
0.052 / 0.106 / 0.195 / 0.692 mm/s
```

Penetration was stable over the final `0.1 s` at stored float32 precision.
P95 is a candidate settling diagnostic, but it is not an accepted replacement
for p99 until fixed-window tests cover the required mass cases.

## What Is Safe To Run Now

Read-only inspection, visualization, source checks, and the existing smoke
runners are safe. Useful entry points:

```bash
conda run -n tsplat python scripts/view_iteration_7000.py --align-ground-z
conda run -n tsplat python scripts/view_particle_ply.py \
  assets/base_settled_stiff_mid/particles_initial_mpm.ply --point-size 0.003
conda run -n tsplat python scripts/run_mass_controlled_terrain.py --help
conda run -n tsplat python scripts/run_mass_controlled_bridge_checks.py --help
```

The Real3 report can be regenerated with:

```bash
conda run -n tsplat python scripts/preprocess_single_trial_real3.py --copy-plys
conda run -n tsplat python scripts/make_single_trial_report.py \
  --output reports/single_trial_real3_report.md
```

Do not run a material sweep or call an output a calibrated result yet.

## Required Work Before The Real6 Sweep

Complete these in order. Do not skip a gate merely because the animation looks
plausible.

1. **Freeze Real6 metadata.** Create a Real6 action contract with 3 kg mass,
   same cylinder dimensions, nominal center, confirmed dwell/removal/post-settle
   timing, and the center-offset protocol.
2. **Implement a Real6 source adapter.** Prefer companion `dem_0.005m.npy`
   inputs, crop/rasterize a center-relative fixed grid, write the existing
   `S0/S1/delta/valid-mask` contract, and produce scan diagnostics.
3. **Freeze measurement registration and noise.** Use a documented stable
   region outside the footprint. Estimate noise from independent frame subsets
   or other defensible static data; annulus spread is only a proxy.
4. **Match the simulation initial state.** Register or construct the MPM bed
   from Real6 `S0`, project simulated `S0` onto the exact Real6 grid, and
   verify the footprint overlay before comparing terminal surfaces.
5. **Validate the 3 kg action.** Repeat mass/inertia/free-fall checks, then
   run 3 kg coupled terrain release, uncapped removal, and post-removal settle.
6. **Freeze settling logic.** Run the required fixed-window tests across
   `0.75`, `1.5`, and `3.0 kg`; choose the speed percentile/threshold based on
   evidence, not on the one 1.5 kg trace.
7. **Establish reproducibility.** Implement complete MPM state persistence or
   deterministic reconstruction, characterize no-cylinder drift, and repeat
   identical rollouts.
8. **Validate inference.** Project terminal surfaces to the Real6 DEM grid,
   implement the noise-aware loss, and recover known parameters in synthetic
   `3 x 3` experiments.
9. **Run real candidates.** Run a small nominal-center smoke grid, then the
   material grid. Run the `3 x 3` center grid as a separate protocol-sensitivity
   experiment, not as an unconstrained material optimization variable.

## Intended Calibration And Reporting

Initial material dimensions:

```text
log10_E in [4, 7]
phi_deg in [15, 45]
```

Keep density, Poisson ratio, particle/grid settings, friction, first-contact
rule, removal rule, and center convention fixed while fitting the first
material grid. Any alternative must be a named sensitivity experiment.

Each candidate must record:

```text
trial ID and source data revision
material config and resolved solver config
initial-state identifier and restoration method
rigid geometry, mass, density, inertia, and initial pose
first-contact and settling criteria
center offset and removal protocol
surface projection convention and valid-mask coverage
loss components, output metrics, runtime, backend/device, and seed
```

The final result is a loss landscape and plausible effective-material region.
It must state measurement noise, simulation uncertainty, action/registration
assumptions, center sensitivity, and all unresolved limitations.

## Guardrails

- Never reintroduce target-depth indentation as the real calibration action.
- Do not use a raw surface shell as a stable terrain base.
- Do not use the Real5 during view as a terminal sand residual; it contains the
  loading object.
- Do not let ICP register through the changed contact patch.
- Do not compare a terminal simulation surface to a real DEM before verifying
  initial-surface grid, frame, and footprint alignment.
- Do not claim equilibrium while the selected documented criterion times out.
- Do not infer deterministic reset from a positions-only PLY.
- Do not merge Real3 and Real6 as replicate observations.
- Keep generated PLYs/videos under `outputs/`; do not commit large artifacts.

## Documentation Policy

`CURRENT_STATE.md` is the only live planning and handoff document. Keep
generated measurements in `reports/` and outputs in `outputs/`. When a gate is
closed or invalidated, update the relevant section above in the same change as
the implementation or experiment result. Do not create parallel status, bridge,
or phase-plan documents.

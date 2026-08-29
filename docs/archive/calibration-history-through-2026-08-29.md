# Tera Splat Current State

Last reviewed: 2026-08-18

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
4. Estimates an effective sand/particle parameter region over `log10_E`,
   `phi_deg`, particle spacing, and particle size.
5. Later transfers validated MPM displacement back to the visible splat.

This is effective-model calibration, not a claim of unique geotechnical
properties. Do not tune parameters against an animation alone.

## Repository And Runtime

```text
repository: /home/moog-2/christo/splatting_stuff/physical/tera_splat
environment: conda env chrono_splat
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
scripts/run_chrono_genesis_bayesopt.py
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

### Chrono SCM Bridge Plumbing (2026-08-17)

The sibling `Chrono/tera_splat_sim` repository now exports a canonical
stationary-cylinder SCM episode through `run_cylinder_episode.py`.  Its output
contains initial/loaded/residual metric height maps, a one-cell boundary mask,
action geometry/mass/pose, pose history, metrics, and a `bed`-frame manifest.
`scripts/run_chrono_genesis_bridge.py` builds a new volumetric metre-frame MPM
bed from that initial map, runs the existing gravity-cylinder phase machine,
and projects Genesis initial/loaded/residual particle states back to the exact
Chrono grid.

The completed plumbing evidence is deliberately smoke-resolution only:

```text
Chrono source: Chrono/tera_splat_sim/validity_experiment/chrono_episodes/A0_cal_smoke
Genesis bridge: outputs/validity_experiment/A0_cal_smoke_genesis_fast_lift
comparison figure: ../Chrono/tera_splat_sim/validity_experiment/visualizations/A0_cal_smoke_chrono_genesis_states.png
grid: 31 x 31 at 40 mm; common valid cells: 841
Genesis bed: 3,844 particles, 0.10 m depth, 40 mm spacing, CUDA RTX 3060 Ti
shared maps: finite on every common valid cell
Chrono repeat: initial/loaded/residual maps and mask bitwise identical
loaded deformation RMSE: 34.859 mm
```

The `34.859 mm` value is a pre-fit plumbing measurement, **not** a calibration
result.  The smoke Chrono and Genesis loaded settle phases timed out, and the
bridge used a documented 0.1 m/s numerical lift to complete within the smoke
budget.  Reported validity results must instead use the configured 10 mm
Chrono grid, independently reviewed settling rules, and the normal uncapped
removal protocol.

The next initial-state gate was implemented in
`run_mass_controlled_terrain.py`: fixed rigid side walls plus a no-cylinder
pre-settle-only phase, with all-bed p99 speed and particle-state outputs.  It
failed for the raw 40 mm metric lattice, so no fitting was started:

```text
output: outputs/validity_experiment/A0_cal_smoke_genesis_presettle_only_1s
containment: 0.20 m walls, 0.02 m thickness
pre-settle window: 1.0 s, no cylinder contact
required / final all-bed p99 speed: 0.0005 / 0.08189 m/s
surface vertical drift RMS / maximum: 33.35 / 33.96 mm
```

The raw heightmap-to-particle initializer therefore compacts substantially
under gravity even with lateral containment.  Stop before material fitting.

### Complete-State Prepared-Bed Gate (2026-08-17)

`scripts/mpm_state_io.py` now persists and restores the complete single-bed
Genesis MPM state (`pos`, `vel`, `C`, `F`, `Jp`, and `active`).
`scripts/build_chrono_settled_bed.py` constructs a metric bed, assigns an
analytic depth-varying geostatic stress through `F` without moving the Chrono
`H0` surface, gravity-settles it in the contained tray, and writes an accepted
artifact only if both the all-bed p99-speed and frozen surface gates pass.
`scripts/run_chrono_genesis_bridge.py` now requires that accepted artifact and
restores its full MPM state; it refuses a rejected bed.

The first bounded smoke calibration sweep produced only rejected artifacts;
this is evidence, not material fitting:

```text
frozen surface gate: RMSE <= 5 mm and maximum absolute error <= 10 mm
equilibrium gate: all-bed p99 <= 0.0005 m/s for 0.02 s

scale 1, 0.25 s:  p99 0.34704 m/s; RMS / max 29.97 / 30.53 mm; rejected
scale 10, 0.25 s: p99 0.01058 m/s; RMS / max 12.22 / 12.86 mm; rejected
scale 14, 0.50 s: p99 0.003387 m/s; RMS / max 8.66 / 9.63 mm; rejected
artifact: outputs/validity_experiment/A0_cal_smoke_prepared_geostatic_scale14_050s
```

A short rebuild-and-restore round trip from the saved scale-1 MPM artifact
completed a further `0.01 s` step with the full state intact
(`outputs/validity_experiment/A0_cal_smoke_prepared_geostatic_restore_roundtrip`).
The bridge also rejects the known failed prepared-bed manifest before creating
any cylinder-run output.

At this point the complete-state restoration blocker was removed, but the
initial-state gate was still open.  The accepted preparation recorded below
supersedes this status.  Do not shift the settled particles vertically, loosen
the thresholds, or fit material parameters to compensate for a failed
settling-state gate.

### Settling Stage And BayesOpt Boundary (2026-08-17)

The frozen settling contract is now recorded in the sibling
`../../tera_splat_sim/docs/archive/sim-only-validity-plan-2026-08-17.md`.  It requires complete-state
restoration and, at smoke resolution, all-bed p99 `<= 0.0005 m/s` continuously
for `0.02 s`, initial-surface RMSE `<= 5 mm`, and initial-surface maximum error
`<= 10 mm` on the Chrono-valid mask.  Geostatic preparation, particle/grid
resolution, `dt`, bed geometry, constraints, contact settings, action, mask,
and surface extraction are frozen for a single optimization campaign.

The first accepted smoke prepared bed is:

```text
outputs/validity_experiment/A0_cal_smoke_prepared_geostatic_scale18_dt1ms_4s
Genesis dt: 1 ms
geostatic stress scale: 18
equilibrium reached: 1.741 s; final p99: 0.0004342 m/s
H0 RMSE / maximum error: 2.695 / 4.748 mm over 841 valid cells
complete state: prepared_bed/mpm_state.npz (pos, vel, C, F, Jp, active)
```

It was accepted without a post-settle height offset or added damping.  The
bridge restores this state and propagates its recorded `dt` into the cylinder
run.  A capped smoke bridge from this state completed end-to-end, but is only
a diagnostic: its `0.25 s` loaded and post-removal phases timed out and the
cylinder penetrated `170.5 mm`.  It is **not** a BayesOpt evaluation and must
not be used as a calibration loss observation.

This was the historical two-parameter boundary.  It is superseded below by the
implemented four-parameter campaign runner; its fixed settling and validity
gates remain mandatory.

### Loaded Contact Diagnostic (2026-08-17)

An uncapped, loaded-only `A0_cal` diagnostic was run from the accepted
prepared bed for `2.0 s` with the same `1.5 kg` cylinder, geometry, gravity,
clearance, containment, complete-state restoration, and `dt=1 ms`:

```text
output: outputs/validity_experiment/A0_cal_smoke_loaded_contact_diagnostic_2s
loaded termination: timeout after 2.0 s
initial / final cylinder-center z: +0.023960 / -0.134615 m
reported sinkage: 158.575 mm
ground plane: -0.160000 m; cylinder half-height: 25.4 mm
loaded local particle p99: 0.00558 m/s
```

The final center is the ground-plane height plus the cylinder half-height,
showing that the rigid floor, rather than the MPM bed, caught the cylinder.
This is a rigid--MPM coupling/contact failure.  Do **not** start BayesOpt over
`E` and `phi` yet: those parameters cannot repair a floor-supported contact.
First validate and fix rigid--MPM coupling with a minimal flat-bed contact
test that measures a nonzero MPM-supported load before repeating the normal
uncapped A0 baseline.

### Volume-Consistent Flat-Bed Contact Test (2026-08-17)

The immediate floor-catch cause was an under-massed smoke lattice: `3,844`
particles at `40 mm` spacing were assigned `12.5 mm` particle volume, implying
only about `7.5 kg` of MPM material.  CPIC alone did not alter that result.

The isolated replacement test uses `22,326` particles at `20 mm` lattice
spacing with `particle_size=20 mm`, CPIC enabled, the same `1.5 kg` cylinder,
gravity, floor, and lateral containment.  It passed the loaded-contact gate:

```text
output: outputs/validity_experiment/A0_cal_smoke_loaded_contact_density_20mm_cpic
loaded equilibrium: 0.227 s
sinkage: 2.328 mm
final local particle p99: 0.000233 m/s
minimum clearance above floor-supported center: 156.9 mm
```

The MPM bed, not the rigid floor, supports the cylinder in this test.  Future
prepared beds must record and replay `particle_spacing`, `particle_size`,
implied mass/volume check, and CPIC status.  Rebuild and settle this denser
bed under the frozen H0 gate before reopening the uncapped A0 baseline; only
then may the BayesOpt campaign begin.

### Accepted 20 mm Chrono-Terrain State (2026-08-18)

The volume-consistent (`20 mm` spacing and `particle_size=20 mm`), CPIC-enabled
Chrono terrain was rebuilt and accepted as a complete Genesis state:

```text
prepared bed: outputs/validity_experiment/A0_cal_smoke_prepared_20mm_cpic_scale1_1s
particles: 22,326; CPIC: enabled; dt: 1 ms; geostatic scale: 1
equilibrium: 0.274 s; all-bed p99: 0.0004288 m/s
H0 RMS / maximum error: 0.614 / 0.647 mm on 841 Chrono-valid cells
```

An uncapped loaded-only A0 release restored that state and reached Genesis
equilibrium at `0.106 s` with `0.763 mm` sinkage and p99 `0.000265 m/s`
(`outputs/validity_experiment/A0_cal_smoke_loaded_20mm_cpic_accepted`).
The cylinder is MPM-supported.  The Chrono smoke reference reports
`20.165 mm` sinkage, so the remaining loaded-response mismatch is now a
calibration target.  Before recording a BayesOpt observation, implement the
same removal semantics as Chrono (`remove_body`, not a numerical lift) and
produce the normal initial/loaded/residual A0 baseline from this state.

The normal smoke A0 baseline has now completed with `remove_body` semantics:

```text
bridge: outputs/validity_experiment/A0_cal_smoke_genesis_20mm_cpic_remove_body
loaded / post window: 0.25 / 0.25 s; both timeout (no cap used)
loaded sinkage: 6.078 mm; loaded local p99: 0.00223 m/s
shared H0 RMS / maximum: 0.614 / 0.647 mm
shared loaded / residual deformation RMS: 0.352 / 0.397 mm
```

This is a mechanically valid plumbing baseline, but not a BayesOpt datum: the
smoke Chrono pose metric reports `20.165 mm` sinkage while its 40 mm sampled
heightmap contains less than a millimetre of resolved deformation.  Generate a
deterministic full-resolution (`10 mm`) Chrono A0 episode and its matching
volume-consistent Genesis prepared bed before defining the BayesOpt loss.

### Full-Resolution Chrono-to-Genesis A0 (2026-08-18)

The required production-resolution A0 plumbing run is now complete.  The
Chrono SCM source is
`../tera_splat_sim/validity_experiment/chrono_episodes/A0_cal_full10mm`:

```text
SCM grid / timestep: 10 mm, 121 x 121 / 0.5 ms (not smoke)
loaded termination: equilibrium
Chrono body descent from its 20 mm starting clearance: 19.232 mm
loaded linear / angular speed: 0.237 mm/s / 0.00343 rad/s
```

The matching Genesis source state is accepted at
`outputs/validity_experiment/A0_cal_full10mm_prepared_20mm_cpic_scale1_1s`.
It is a 22,326-particle, 20 mm particle-size, CPIC-enabled volumetric bed,
restored as a complete MPM state.  Its pre-action settling reached equilibrium
at `0.274 s` with p99 particle speed `0.427 mm/s`; on the 10 mm Chrono grid
the initial-surface RMSE / maximum error is `0.615 / 0.654 mm`.

The corresponding bridge rollout is
`outputs/validity_experiment/A0_cal_full10mm_genesis_20mm_cpic_remove_body`.
It used the Chrono `remove_body` action (zero lift steps) and reached Genesis
equilibrium in both phases (693 loaded and 72 post-removal steps).  The
shared-grid H0 reconstruction is therefore acceptable, but loaded response is
not yet calibrated:

```text
common valid cells: 14,161
loaded deformation difference (Genesis - Chrono): 0.269 mm RMSE, 5.662 mm max
residual deformation difference:                 0.272 mm RMSE, 5.711 mm max
most-negative loaded deformation: Chrono -5.556 mm; Genesis -0.086 mm
```

Thus the integration, complete-state restoration, CPIC configuration, and
Chrono removal semantics all work on the production SCM grid.  The fixed
20 mm state is a pre-fit reference, not an optimization result: Genesis is
materially too stiff/weakly deforming for the resolved Chrono map.  The
implemented four-parameter runner below uses heightmap deformation rather than
the pose-descent convention as its loss.

In particular, the `19.232 mm` pose descent must not be called surface
sinkage: the action starts the cylinder bottom `20 mm` above the bed, so this
quantity mostly measures clearance closure.  The BayesOpt target is the masked
heightmap deformation (currently up to `5.556 mm` downward on the common
grid), not this pose-derived value.

The canonical visualization/export bundle for that fixed BayesOpt target is
`../tera_splat_sim/validity_experiment/bayesopt_target/A0_cal_full10mm`.
It contains a viridis initial/loaded/residual Chrono DEM (absolute elevation
and depression from initial), 14,161-point common-grid SCM and Genesis PCDs,
raw Genesis MPM-particle PCDs, and native 10 mm surface meshes.  The paired
5 mm meshes are display-only cubic interpolation, not additional simulation
resolution.  Use the native SCM `loaded` and `residual` PCD/mesh or the source
heightmaps as the objective data; the Genesis files in the same bundle are the
current pre-fit baseline for visual comparison only.

### Frozen-State W&B BayesOpt Runner (updated 2026-08-20)

Stage-1 prepared-bed failures, their evidence, and the corrective plan are
maintained in [Experiment Problems And Corrective Plan](experiment-problems-through-2026-08-18.md).
Resolve that document's mass/volume and surface-support diagnostics before
spending another response-optimization budget.

`scripts/run_chrono_genesis_bayesopt.py` implements a validity-gated W&B
Bayesian campaign for the canonical 1.5 kg, 10 mm A0 Chrono target. It now
requires one accepted `--prepared-bed` and restores that identical complete MPM
state for every material candidate.  It does
not run a campaign merely by being added; evaluating a study remains an
explicit command.  The dimensions are:

```text
log10_E:                continuous [4, 6]
phi_deg:                continuous [15, 45]
particle_spacing_m:     fixed by --prepared-bed
particle_size_ratio:    fixed by --prepared-bed
```

Particle geometry is no longer proposed inside a material-response study. Each
spacing/size family must first produce its own accepted, volume-consistent
prepared artifact; run a separate two-parameter study for each accepted family.
This prevents `E` and `phi` from changing H0 during objective evaluation.

For each candidate the runner writes a resolved material config, verifies the
frozen artifact belongs to the target Chrono episode and matches the recorded
particle geometry, restores its complete state, and requires loaded and
post-removal equilibrium.  It then minimizes the masked
deformation loss
`loaded_RMSE + 0.5 * residual_RMSE` on the common Chrono/Genesis grid.  A
rejected bed, non-equilibrium phase, missing support, or exception is logged as
`valid=0` and deliberately does **not** report `objective/m`, so W&B does not
treat it as a Bayesian observation.  The default loaded/post windows are
`1.0 / 1.0 s`: the earlier `0.25 s` smoke-oriented window is insufficient for
the established full-resolution loaded baseline (which settled at `0.693 s`).

Each `--count N` invocation creates **one** W&B study run, not W&B's native
agent/sweep child runs.  Its history uses `iteration` as the x-axis and logs
the sampled/derived parameters and metrics at that iteration.  After three
valid observations, a fixed-kernel Gaussian-process expected-improvement
proposal selects the next candidate; the first samples are deterministic and
start with the known accepted 20 mm baseline.  The study additionally records
frozen prepared-state speed/surface-match gates, phase reasons, common-mask fraction, and per-phase DEM difference RMSE, MAE,
signed mean, signed extrema, and p05/p95.  Every completed bridge persists
masked `loaded_dem_difference_m.npy`, `residual_dem_difference_m.npy`, and
`common_valid_mask.npy` beside its result; a non-equilibrium bridge logs those
diagnostics but has `valid=0` and no objective.  The runner never reads an API
key; `wandb.init()` uses the normal W&B environment lookup when launched in an
authenticated shell.

The requested heterogeneous lower-layer random XY noise is intentionally
excluded.  It would change the model family and must be introduced later as a
versioned, seeded additional parameter with a separate baseline.

Initialize the W&B connection only (no candidate and no sweep) with:

```bash
PYTHONNOUSERSITE=1 conda run -n chrono_splat python scripts/run_chrono_genesis_bayesopt.py \
  --prepared-bed outputs/validity_experiment/A0_cal_full10mm_prepared_20mm_cpic_frozen/prepared_bed \
  --wandb-init-only --project chrono-genesis-bayesopt
```

After reviewing that connection, create and run one sequential Bayesian study
with `--count N`; use `--run-one` with explicit material and matching frozen-geometry flags for a single
reproducible bracket point.  Outputs are isolated under
`outputs/validity_experiment/bayesopt/A0_cal_full10mm_frozen_2d/study_<wandb-run-id>`.

The first diagnostic-enabled campaign was launched on 2026-08-18.  Its first
completed bridge (`hehgf7cn`) used `log10_E=4.93262`, `phi=33.329 deg`,
`20 mm` spacing, and a `0.85` particle-size ratio (`17 mm`).  It had full
common-mask support (14,161 cells) and logged loaded/residual DEM RMSE of
`0.174 / 0.267 mm`, respectively, but the post-removal phase timed out.  It is
therefore a `valid=0` DEM diagnostic, not a Bayesian objective observation.

After the W&B credential was refreshed, a clean known-baseline verification
(`tspto9v2`) synced successfully.  The earlier native W&B agent sweep was
stopped and superseded because it created one remote run per candidate rather
than the required one-study iteration history.
It used the accepted 20 mm, `E=100 kPa`, `phi=45 deg` state, reached
equilibrium in loaded and post-removal phases, had all 14,161 common cells,
and reported `objective/m = 0.405 mm` (loaded/residual RMSE `0.269 / 0.272
mm`).  Its W&B run history contains the requested `dem/*` metrics and the
masked difference arrays live under
`outputs/validity_experiment/bayesopt/A0_cal_full10mm_4d_clean/trials/tspto9v2/bridge`.

The replacement single W&B study `dooqrbdl` completed its eight iterations,
with its candidate directories under
`outputs/validity_experiment/bayesopt/A0_cal_full10mm_4d_clean/study_dooqrbdl`.
Its one W&B run uses `iteration` as the history step; it does not create a
candidate-level W&B run for each directory.

Five of the eight candidates were fully valid.  The current best is iteration
2: `log10_E=5.5` (`316.228 kPa`), `phi=18.333 deg`, `20 mm` spacing, and a
`0.85` size ratio (`17 mm`).  Its objective is `0.2607 mm`, composed of
loaded/residual DEM RMSE `0.1496 / 0.2223 mm`; this improves on the accepted
baseline's `0.4055 mm` objective.  This is **not convergence**: three trials
were invalid and only two expected-improvement proposals followed the three
valid bootstrap observations.  Treat it as the incumbent for a longer
single-study continuation, not a final calibrated parameter estimate.

The study runner prints a flushed line at study start, every iteration start,
and every iteration completion (valid objective or invalid reason).  The live
study also has a `bayesopt:status` tmux window that refreshes the completed
iteration count every five seconds without reading credentials.

The first proper-continuation attempt, single W&B study `ulik6isa`, imported
the five pilot valid observations but exhausted its 50-new-attempt safety cap
with only three new valid candidates.  Its unconstrained proposal repeatedly
selected the 15 mm and 25 mm lattice pairs that fail the prepared-bed gate, so
it is feasibility evidence rather than the final calibration study.  Its data
is under
`outputs/validity_experiment/bayesopt/A0_cal_full10mm_4d_proper/study_ulik6isa`.
The active replacement proper study is single W&B run `899hahhc` under
`outputs/validity_experiment/bayesopt/A0_cal_full10mm_4d_proper_feasible/study_899hahhc`.
It imports all eight valid pilot/feasibility results and targets 30 valid
objectives using only the accepted particle family, with a 35-new-attempt cap.
It completed that cap with only two new valid candidates (10 valid total), so
it **stopped without convergence**.  The accepted particle pair alone is not
a sufficient feasibility constraint across all sampled `E`/`phi` values;
future work needs an explicit feasibility model or a separately validated
material--particle feasible region before spending another objective budget.
The incumbent remains the prior `0.25765 mm` objective at `E=361.942 kPa`,
`phi=17.787 deg`, 20 mm spacing, and 0.85 size ratio.

### Oracle-Only Drop Visualization (2026-08-18)

`../tera_splat_sim/validity_experiment/visualizations/A0_oracle_6kg_2mm_smoke_drop_dem.mp4`
is an 11.25 s side-by-side render of a 6 kg cylinder released from a 2 mm
clearance: captured Chrono cylinder motion/cross-section at left and the
measured SCM `current - initial` deformation at right.  It uses 45 actual SCM
heightmap captures from the associated episode, not interpolated DEM frames.

This is explicitly an **oracle visualization only**: it uses the 40 mm smoke
grid, and its 0.6 s loaded phase timed out rather than satisfying the
equilibrium gate.  Its masked loaded deformation reaches `13.634 mm` downward.
It is useful for communicating the altered synthetic action, but is not a
BayesOpt target or a physical-realism claim.

The completed production counterpart is
`../tera_splat_sim/validity_experiment/visualizations/A0_oracle_6kg_2mm_full10mm_drop_dem.mp4`.
It uses a 6 kg cylinder, 2 mm clearance, 10 mm SCM grid, 0.5 ms timestep, and
34 actual terrain captures.  Chrono reached loaded equilibrium at `0.300 s`
with linear / angular speed `0.080 mm/s / 0.00266 rad/s`; the video is 8.5 s
and its masked loaded deformation reaches `9.897 mm` downward.  Unlike the
smoke visualization, this is a candidate synthetic-oracle BayesOpt target,
but it still requires a deterministic repeat and a separately frozen oracle
action contract before it enters any optimization campaign.  It must remain
separate from the 1.5 kg real-protocol target.

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
conda run -n chrono_splat python scripts/view_iteration_7000.py --align-ground-z
conda run -n chrono_splat python scripts/view_particle_ply.py \
  assets/base_settled_stiff_mid/particles_initial_mpm.ply --point-size 0.003
conda run -n chrono_splat python scripts/run_mass_controlled_terrain.py --help
conda run -n chrono_splat python scripts/run_mass_controlled_bridge_checks.py --help
```

The Real3 report can be regenerated with:

```bash
conda run -n chrono_splat python scripts/preprocess_single_trial_real3.py --copy-plys
conda run -n chrono_splat python scripts/make_single_trial_report.py \
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

`docs/current-state.md` is the only live planning and handoff document. Keep
generated measurements in `reports/` and outputs in `outputs/`. When a gate is
closed or invalidated, update the relevant section above in the same change as
the implementation or experiment result. Do not create parallel status, bridge,
or phase-plan documents.


### Frozen-Initialization BayesOpt Boundary (2026-08-20)

The runner now requires `--prepared-bed` and reuses that accepted complete MPM
state for every candidate. Its manifest fixes particle spacing and size for the
study; proposals vary only `log10_E` and `phi_deg`. This prevents candidate
materials from rebuilding or corrupting H0. Run separate preparation studies
for particle families, then start one BayesOpt study per accepted artifact. All
instrumentation and commands use the `chrono_splat` Conda environment.


#### Verified Frozen-State Loop (2026-08-20)

Runtime: `chrono_splat` at `/data/christoa/conda/envs/chrono_splat`, Python
3.10, PyTorch 2.13.0+cu130, Genesis 1.3.3, CUDA visible. A fresh accepted state
was generated at
`outputs/validity_experiment/A0_cal_full10mm_prepared_20mm_cpic_frozen`:
equilibrium at 0.274 s, p99 speed 0.424 mm/s, H0 RMSE 0.615 mm, maximum
error 0.654 mm, and all 14,161 target-valid cells supported.

The offline study `outputs/validity_experiment/bayesopt/A0_cal_full10mm_frozen_loop/study_9656sgoj`
completed four attempts from that same state: three valid objectives and one
properly excluded post-removal timeout. The baseline objective was 0.406 mm.
A seeded continuation proposed the first GP expected-improvement candidate
(`log10_E=5.6202`, `phi=44.518 deg`); its loaded phase timed out and was
correctly excluded. This verifies proposal, restore, rollout, gating, DEM loss,
and W&B instrumentation without candidate-dependent H0 reconstruction.


#### Online Frozen-State Sweep (2026-08-20)

W&B run `christo12aluckal/chrono-genesis-bayesopt/61sldco9`
(`bright-mountain-20`) finished and synced online. It restored the same accepted
20 mm complete MPM state for every trial, so this campaign does not exhibit the
earlier candidate-dependent H0 initialization failure.

The study imported three valid seed observations and attempted 45 new candidates.
Only one new candidate was valid; 44 were excluded because a required response
phase did not reach equilibrium. The study therefore finished with four total
valid observations and did not reach its target of 30. Expected improvement
repeatedly proposed near `log10_E ~= 5.6`, `phi_deg ~= 44`, where the loaded
phase timed out. Invalid trials were correctly logged without `objective/m`, but
the objective-only GP cannot learn that this region is infeasible and repeatedly
returns to it.

Interpretation: frozen initialization is working, but this is not a calibrated
result. The next optimizer change must model response feasibility separately and
rank candidates using an acquisition such as expected improvement multiplied by
the predicted probability of equilibrium. A longer phase timeout may diagnose
borderline cases, but it does not replace feasibility-aware acquisition.

Remote run: <https://wandb.ai/christo12aluckal/chrono-genesis-bayesopt/runs/61sldco9>
Local evidence: `outputs/validity_experiment/bayesopt/A0_cal_full10mm_frozen_online/study_61sldco9`.


#### Candidate-Consistent Stress Initialization (2026-08-20)

The frozen-state campaign exposed a constitutive initialization error: it
restored `F` and `Jp` prepared at the reference `E=100 kPa`, then changed `E`
for contact. Because stress is computed from both the constitutive state and
material parameters, the same saved `F` implies a different initial stress at a
different `E`. The high-`E` timeout cluster in online run `61sldco9` must
therefore not be interpreted as a learned response-infeasible region.

The corrected bridge uses two initialization layers. The accepted prepared bed
still freezes particle count, positions, active mask, mass/discretization, H0,
solver settings, and containment. For each candidate it then preserves those
positions and active flags, zeros velocity and `C`, resets `Jp`, computes an
analytic depth-dependent geostatic `F` using the candidate `E`, density, and
`nu`, and runs a cylinder-free relaxation. Contact begins only after that state
passes the original all-bed p99 speed threshold and frozen H0 RMSE/maximum gates.
The candidate-specific complete state is persisted under
`bridge/candidate_prepare_raw/mpm_state.npz`; the bridge manifest and W&B history
record its H0 metrics.

This changes initialization preparation as follows:

1. Build and accept the geometric/discretization reference bed once.
2. Reconstruct candidate-consistent stress from its frozen geometry for every
   `E`/`phi` evaluation.
3. Allow only the small unconstrained relaxation admitted by the existing H0
   tolerances; do not vertically shift or otherwise repair the result.
4. Reject a candidate before cylinder contact if speed or H0 fails.

CUDA bracket validation passed for both the reference material and the formerly
failing high-`E` region. At `100 kPa, 45 deg`, candidate H0 RMSE/max were
`1.182/1.259 mm`; loaded and post-removal phases equilibrated and objective was
`0.456 mm`. At `log10_E=5.6360, phi=44.415 deg`, H0 RMSE/max were
`0.748/0.798 mm`; both phases equilibrated, cylinder depth was `1.217 mm`, and
objective was `0.419 mm`. The prior negative-depth rebound disappeared. Run a
new sweep with this corrected initialization; do not seed its objective model
with response outcomes from pre-fix campaigns.


#### Corrected Quick Online Sweep (2026-08-20)

Online W&B run `h2il8dg0` (`dainty-water-21`) evaluated 12 fresh candidates
without pre-fix seeds using candidate-consistent stress initialization. All 12
candidates passed cylinder-free preparation and all 12 loaded phases reached
equilibrium. Three also reached post-removal equilibrium, for a strict valid
objective rate of `3/12 = 25%`; the other nine were post-removal timeouts. This
is higher than the pre-fix campaign rate, while confirming that the remaining
invalidity is no longer H0 initialization or loaded rebound. The objective-only
GP clustered near `log10_E ~= 4.23`, `phi_deg ~= 30`, where post-removal did not
settle within 1 s. The best valid quick-sweep candidate was `log10_E=4.5`,
`phi_deg=35` with objective `0.372 mm`. Remote run:
<https://wandb.ai/christo12aluckal/chrono-genesis-bayesopt/runs/h2il8dg0>.


#### Post-Removal Settling Diagnostic Plan (2026-08-20)

The corrected quick sweep does not currently show a removal-mechanism failure.
Genesis uses the Chrono-matched `remove_body` semantics, all 12 candidate
preparations passed, all 12 loaded phases equilibrated, and three candidates
reached post-removal equilibrium with the same removal implementation. The nine
timeouts were borderline: their final local particle p99 speeds were
`0.557--0.587 mm/s` versus the frozen `0.500 mm/s` threshold, while one valid
candidate required `0.992 s` of the available `1.000 s`. The current evidence
therefore points first to an underspecified/borderline residual settling window,
not a demonstrated removal impulse or collision error.

Before another sweep, run a controlled post-removal-duration diagnostic at
`1.0, 1.5, 2.0, and 3.0 s` for: (1) one fast-settling valid candidate, (2) the
best valid `log10_E=4.5, phi_deg=35` candidate, and (3) two timed-out candidates
near `log10_E ~= 4.23, phi_deg ~= 30`. Record the first time local p99 remains
below `0.5 mm/s` for 20 ms, p99 at every observation time, residual DEM change
between observation times, and objective sensitivity to the selected time.

Freeze the protocol using these decision rules:

- If timed-out cases settle shortly after 1 s and residual DEM changes become
  negligible, extend the production post-removal limit, provisionally to 2 s.
- If they remain active through 3 s, classify that material region as genuinely
  non-equilibrating under the frozen action.
- If the residual DEM is stable while p99 remains slightly above threshold,
  review whether the p99 gate is overly conservative for the observable target;
  do not relax it without recording the DEM-based evidence.
- If removal produces a sudden spatially broad velocity spike, investigate the
  `remove_body` implementation before further optimization.

Chrono residual semantics must also be made explicit: compare at the same fixed
post-removal observation time if the oracle residual is time-defined, or require
matched equilibrium if it is settle-defined. Do not launch another calibration
sweep until this convention and the production post-removal window are frozen.


#### Post-Removal Settling Diagnostic Results (2026-08-24)

Implemented the fixed-time checkpoint path in
`run_mass_controlled_terrain.py` and threaded it through
`run_chrono_genesis_bridge.py`. When `--post-observation-times` is supplied,
the runner no longer exits at the first equilibrium window: it runs the full
requested horizon and writes particle checkpoints, p50/p90/p95/p99 speeds,
first equilibrium time, projected residual heightmaps, residual DEM changes,
and the BayesOpt-consistent objective at each observation time.

A CUDA diagnostic used the frozen 20 mm CPIC prepared bed, candidate-consistent
stress reconstruction, `remove_body`, 1 s loaded settling, and fixed
post-removal observations at 1.0, 1.5, 2.0, and 3.0 s. All four cases completed:

| candidate | first 20 ms equilibrium | p99 at 1.0 s | p99 at 2.0 s |
| --- | ---: | ---: | ---: |
| `log10_E=5.0, phi=45` | 0.091 s | 0.083 mm/s | 0.074 mm/s |
| `log10_E=4.5, phi=35` | 0.994 s | 0.475 mm/s | 0.111 mm/s |
| `log10_E=4.2223, phi=30.537` | 1.122 s | 0.583 mm/s | 0.167 mm/s |
| `log10_E=4.2436, phi=30.096` | 1.118 s | 0.591 mm/s | 0.150 mm/s |

The two former 1 s timeouts cross the original 0.5 mm/s p99 gate only about
0.12 s later. This rules out the removal mechanism as the explanation for
those failures: there was no broad velocity spike, all loaded phases had
already equilibrated, and both cases decay smoothly below the same gate. A
post-removal cap of at least 1.5 s admits all four representatives; 2 s is a
conservative **Genesis feasibility cap**, not yet an oracle-matching sample
time.

The residual is not perfectly time-invariant after the speed gate. Across the
1.5--2.0 s and 2.0--3.0 s intervals, residual DEM RMSE changes were about
23--63 micrometres for the three slower cases, and their objective changed by
roughly 12--23 micrometres between 2 and 3 s. Therefore do **not** mix residuals
sampled at arbitrary first-equilibrium times with a fixed-time Chrono oracle.

Inspection of the Chrono exporter confirms that it samples the residual after
a fixed `residual_settle_s` recovery loop following `system.Remove(cylinder)`;
it is not a first-equilibrium target. The `A0_cal_full10mm` manifest fails to
record that duration or post-removal snapshots. The exporter default is 0.5 s,
but this artifact may have been generated with an override, so the correct
oracle time cannot be inferred retrospectively. Before the next BayesOpt sweep,
re-export the canonical Chrono episode with `residual_settle_s` and the
post-removal sampling times stored in its manifest (and preferably snapshots at
those times), then evaluate every Genesis candidate at that same fixed time.
Do not use a 2 s Genesis residual against the present oracle merely because it
passes the Genesis speed gate.


A direct deterministic re-export probe was attempted in the mandated
`chrono_splat` environment to recover the current A0 oracle time. The
environment initially lacked PyChrono; installing Conda-forge `pychrono` 10.0
provided `pychrono.core` but not `pychrono.vehicle`, which this SCM exporter
imports. The probe is therefore blocked until a PyChrono build with vehicle
bindings is installed in `chrono_splat`; do not substitute a different
environment for this instrumentation.


#### Action-Footprint Residual Mismatch and Objective Correction (2026-08-24)

A fresh online W&B study (`9mo0cztm`) evaluated 45 candidates with the frozen
prepared bed, candidate-consistent stress initialization, no imported
pre-fix/1 s observations, and a 2 s post-removal cap. Nine candidates produced
strict valid objectives. This removes the old artificial 1 s post-removal
cutoff as the dominant invalidation path, but it does **not** establish a
physically correct residual surface.

The study-best valid candidate was iteration 007:
`E=53.424 kPa`, `phi=37.919 deg`, objective `0.330 mm`; it reached loaded and
post-removal equilibrium at `0.602 s` and `0.655 s`, respectively. Its
isometric comparison is at
`outputs/validity_experiment/bayesopt/A0_cal_candidate_stress_post2s_online/study_9mo0cztm/trials/iteration_007/bridge/chrono_genesis_residual_isometric.png`.

That comparison exposed a localized wrong-sign residual beneath the known
cylinder footprint: Chrono has a mean residual vertical displacement of
`-1.754 mm` (depression; minimum `-5.556 mm`) over 177 valid 10 mm cells,
whereas the actual Genesis residual surface-particle cloud has a mean
`+0.479 mm` (elevation; range `+0.150` to `+1.241 mm`) over its 45 footprint
particles. This is not a colormap reversal. The current objective nevertheless
ranked it best because it averages residual error over all 14,161 valid cells,
most of which are nearly unchanged and dilute the localized sign error.

Do not add a feasibility classifier or a new physical search parameter for
this. Correct the measurement definition first. For the residual objective,
compare deformation rather than absolute height, restricted to the action
footprint whose radius is already specified by `action.json`:

```text
DeltaH = H_residual - H0
L_residual = RMSE_{distance_to_action_center <= action_radius}(
    DeltaH_Genesis - DeltaH_Chrono
)
```

The radius is a fixed property of the prescribed Chrono action, not a new
hyperparameter. Retain whole-bed RMSE only as a diagnostic. First re-score the
45 completed candidates using this footprint loss. If any valid candidate
already creates a Chrono-signed depression, seed a new 2D (`E`, `phi`) BayesOpt
study with this corrected residual loss. If none does, the issue is not a
search initialization or a GP classifier: the current Genesis sand/contact
response cannot create the required permanent compaction, and the next change
must be to that physical response. A future time-matched Chrono residual is
still needed for formal calibration, but the unknown oracle time does not
justify accepting the opposite localized residual sign.


The nine valid results from the preceding 45-candidate study were re-scored
without rerunning physics. The action-footprint score selected iteration 003
(`E=16.685 kPa`, `phi=30.537 deg`) at `1.473 mm`, versus `1.610 mm` for the
prior global-RMSE best. Crucially, iteration 003 has a negative Genesis mean
residual deformation under the action footprint (`-0.164 mm`), so the frozen
2D material range can at least produce the required depression sign even though
it remains much shallower than Chrono. A fresh unseeded 45-candidate W&B study
`lmdf5fqe` now optimizes the action-footprint residual term with the same
frozen initialization and 2 s post-removal cap. Historical global-loss
observations are deliberately not imported.


The footprint-loss study completed all 45 attempts with 30 strict valid
objectives. Its best candidate was iteration 042,
`E=91.096 kPa`, `phi=15.053 deg`, with footprint-loss objective `0.867 mm`,
footprint residual RMSE `1.292 mm`, and whole-grid residual RMSE `0.157 mm`.
The isometric residual comparison is at
`outputs/validity_experiment/bayesopt/A0_cal_candidate_stress_footprint_online/study_lmdf5fqe/trials/iteration_042/bridge/chrono_genesis_residual_isometric.png`.

Most importantly, its actual Genesis surface-particle cloud now has a mean
residual displacement of `-1.426 mm` under the cylinder footprint (range
`-2.150` to `-0.668 mm`), compared with Chrono’s `-1.754 mm` mean and
`-5.556 mm` minimum. The corrected measurement therefore fixed the prior
wrong-sign selection: the 2D Genesis range can create a residual depression,
so a classifier or immediate constitutive-model expansion is not required.

The optimum lies at the lower friction boundary (`15 deg`) across the leading
candidates. Treat this as a boundary diagnostic, not proof that 15 degrees is
the calibrated value. The next decision is whether a lower friction range is
physically defensible for this Genesis representation; if so, extend only that
existing bound and repeat the footprint-loss study. Otherwise, freeze the
current bound and investigate the remaining spatial-shape/depth error at a
Chrono-matched residual time.


An expanded unseeded 45-candidate study (`zwz8qbj6`) then used friction
`5--45 deg` and added Poisson ratio `nu=0.10--0.35`; geometry, frozen H0,
stress preparation, footprint loss, and the 2 s cap were unchanged. It yielded
7 valid objectives. Its best candidate was iteration 002:
`E=316.228 kPa`, `phi=9.444 deg`, `nu=0.250`, objective `0.775 mm`, footprint
residual RMSE `1.178 mm`, and whole-grid residual RMSE `0.176 mm`. Relative to
the preceding 2D best, the footprint objective improved from `0.867` to
`0.775 mm` (about 11%) and footprint RMSE from `1.292` to `1.178 mm` (about
9%).

The improvement is physically meaningful, not only metric movement: the
Genesis surface-particle footprint mean is now `-1.681 mm`, within `0.073 mm`
of Chrono’s `-1.754 mm` mean. Its deepest point remains too shallow
(`-2.845 mm` versus Chrono `-5.556 mm`), so the remaining problem is the
localized shape/depth rather than residual sign or mean level. The leading
friction (`9.444 deg`) is no longer at the expanded lower bound, while `nu=0.25`
is interior; neither bound alone currently justifies another expansion. The
broader space sharply reduced strict validity (7/45 versus 30/45), mostly by
introducing material combinations that fail loaded settling. Treat the current
best as the evidence-backed starting point; before broadening again, inspect
its localized deformation profile and enforce the Chrono residual-time match.

### Candidate Initial-State Stability Gate (2026-08-25)

Every future Genesis bridge candidate now receives a separate no-action
initial-state test after its candidate-consistent geostatic preparation and
before cylinder placement. The test restores that prepared candidate state,
holds it under gravity for a fixed 0.25 s with the cylinder held away from the
bed, and compares projected start/end surfaces on the Chrono-valid 10 mm grid.
It records signed change (positive means upward rebound) plus RMSE and maximum
absolute change. Candidates are rejected if the drift exceeds 0.5 mm RMSE or
1.0 mm at any common cell. These are fixed validity gates, not BayesOpt
parameters. The raw hold-state PLYs and values are retained under
bridge/candidate_initial_hold_raw and bridge/manifest.json, and are logged
to W&B as candidate_init/no_action_stability_*.

The current expanded-study best (iteration 002, E=316.228 kPa, phi=9.444 deg,
nu=0.25) was checked with this exact 0.25 s no-action hold. It reached the
equilibrium speed condition and changed by 0.020 mm surface RMSE, 0.052 mm
maximum absolute change, and +0.020 mm mean signed change over all 14,161
Chrono-valid cells. Thus it has a very small upward drift, not a meaningful
initial-state rebound; it passes the 0.5 mm RMSE and 1.0 mm maximum gates.
The reproducible raw PLYs, projected difference, and metrics are at
outputs/validity_experiment/bayesopt/A0_cal_candidate_stress_footprint_phi5_nu_online/study_zwz8qbj6/trials/iteration_002/bridge/candidate_initial_hold_check_0p25s/.

### Best-Candidate Episode Video Hook (2026-08-25)

render_chrono_genesis_episode_video.py now renders a captured Chrono SCM
episode and the selected Genesis raw rollout side by side. It samples each
stored episode uniformly over the same display duration, labels the panels, and
writes the component MP4s plus a manifest that explicitly says the result is
phase-normalized rather than physical-time synchronized. BayesOpt exposes this
as --render-best-episode-video. It intentionally requires Chrono terrain
snapshots; recreate the otherwise identical Chrono episode with
run_cylinder_episode.py --capture-interval-s before enabling the hook. The
current A0 target has only initial, loaded, and residual maps, so creating an
episode video from it would be misleading.

Diagnostic artifacts are under
`outputs/validity_experiment/bayesopt/A0_cal_candidate_stress_postremoval_diagnostic/`.


### Initial-Stability Trust-Region Sweep (2026-08-25)

The broad seeded compact study was stopped after it repeatedly proposed a
post-removal-timeout corner: E about 0.56--0.98 MPa and friction about 5--7
degrees. Its no-action initial-state holds passed, and almost all loaded phases
reached equilibrium, so this is a proposal-policy failure rather than an H0 or
stress-initialization failure. The next online study therefore uses fixed
evidence-based trust-region bounds: log10(E/Pa)=5.114--5.653 (130--450 kPa),
friction=7--11 degrees, and nu=0.18--0.30. These are proposal bounds only; no
new physical parameter, loss weight, geometry, or initialization rule is added.

### Calibration Pipeline versus Oracle Fidelity (2026-08-25)

The current bridge is operational: it can prepare candidate-consistent Genesis
initial states, reject unstable preparations, evaluate loaded and residual
surfaces, optimize the existing material parameters, log online to W&B, and
render a selected replay. This establishes that the I/O and optimization loop
are runnable; it does **not** establish that the Chrono reference surface is a
physically faithful calibration target.

The current 10 mm Chrono SCM cylinder episode has an asymmetric loaded
deformation despite a centered, axisymmetric cylinder. Its maximum depression
is about 5.556 mm at `(x, y) = (+30, -10) mm`, rather than at the action
center. There is no material displacement outside the 73.025 mm cylinder
footprint and recorded lateral cylinder drift is only about 0.14 mm, so this
is not explained by contact travel. It is therefore treated as a possible SCM
grid/contact or terrain-export artifact.

BayesOpt correctly minimizes the loss against whichever Chrono maps it is
given. Consequently, improving Genesis parameters against this unvalidated
surface can improve the numerical objective while teaching Genesis to match an
artifact. Do not interpret the current best parameter set as a physical
calibration until the oracle is checked. The next change is deliberately on
the Chrono side only: repeat the identical centered cylinder episode with a
finer SCM grid (2--5 mm), capture time snapshots, and compare center location,
rotational symmetry, radial profile, and loaded-to-residual rebound. If that
target is sound, reuse the existing frozen-initialization BayesOpt loop
unchanged with the regenerated maps.

### Chrono SCM Runtime Build (2026-08-25)

`chrono_splat` originally contained the Conda-forge core-only PyChrono package,
which cannot import `pychrono.vehicle` and therefore cannot generate SCM
oracle episodes. A separate, pinned headless Chrono build now supplies the
required binding while retaining `chrono_splat` as the Python environment:
Chrono `10.0.0` source commit `9faf13dd8f1128dd75ed233a9627027b0422c3f7`,
compiled with Python, Vehicle, and Vehicle Models enabled, and demos, tests,
visualization, and vehicle co-simulation disabled. Source and build artifacts
live under `/data/christoa/Chrono/vendor/projectchrono-10.0.0` and
`/data/christoa/Chrono/build/projectchrono-10.0.0-vehicle-py310`.

Activation hooks in `chrono_splat/etc/conda/activate.d` place that build before
the Conda core-only package and add its library directory at runtime; matching
deactivation hooks restore the prior paths. A normal `conda run -n chrono_splat`
command has been verified to import `pychrono.vehicle` and construct a Bullet-
backed `veh.SCMTerrain`. `run_cylinder_episode.py` also now accepts
`--scm-grid-spacing-m`, so oracle-resolution experiments do not modify the
shared terrain configuration.

### Chrono SCM Translation/Phase Check Correction (2026-08-26)

The previous compact phase-check interpretation was incorrect: its centroid
calculation included the invalid SCM boundary ring. Recomputing the `t=0.1 s`
centroids with `valid_heightmap_mask.npy` shows that the early deformation does
move with the cylinder. The test reveals millimetre-scale coarse-grid phase
sensitivity in x, but it does **not** prove that the deformation is fixed to
the SCM grid or that the current target is invalid for that reason.

BayesOpt remains paused while the guided and finer-resolution tests are
reviewed, but the grid-lock claim is withdrawn. See
[Chrono SCM Oracle Diagnostics](chrono-oracle-diagnostics-through-2026-08-26.md) for corrected
measurements, visuals, and the current validation sequence.

### Oracle Target Decision and Legacy BayesOpt Policy (2026-08-26)

The completed `A0_cal_full10mm` BayesOpt campaigns are now **legacy pipeline
evidence**, not calibration observations for the next study. A fresh Chrono
replay matches the stored maps to `0.00076 mm`, so the maps themselves are not
stale. What is stale is the target contract: the artifact does not record its
fixed post-removal `residual_settle_s` or recovery snapshots, and it came from
an unqualified free centered drop. Its observations must remain on disk for
auditability but must not seed, warm-start, or be mixed into the new W&B study.

The R&D oracle protocol is a 1.5 kg vertically guided cylinder at `(0, +5) mm`
on a 10 mm, 0.6 m SCM screen. The guided offset has the cleaner visual
cross-section in the synchronized triplet at
`/data/christoa/Chrono/tera_splat_sim/validity_experiment/chrono_episodes/free_vs_guided_1p5kg_10mm_triplet/`.
It is an R&D repeatability choice, not a new BayesOpt parameter or a claim of
special physical significance for the offset. The 5 mm guided protocol is the
final high-fidelity validation/export resolution.

Neither current compact candidate can yet be used as an oracle because both
terminate at a fixed loading timeout. The selected 10 mm case still has
`1.142 mm/s` final linear speed; the 5 mm case is closer at `0.319 mm/s` but
also times out. Before the next run, the Chrono exporter must record a fixed
speed-and-hold convergence gate, capture the loaded map at that accepted state,
and record the fixed residual recovery duration. The existing Genesis
preparation, no-action stability gate, loss, and parameterization then remain
unchanged. The detailed run contract is
[Chrono Oracle Run Contract](chrono-oracle-run-contract-through-2026-08-29.md).

### Chrono Loading-Gate Revision (2026-08-26)

The Chrono oracle loading acceptance gate is relaxed from `0.5 mm/s` for
`0.25 s` to `6 mm/s` for `0.10 s` (angular limit remains `0.01 rad/s`). This
comes from rescoring the same 1 ms, 5 s guided 10 mm trace: no threshold up to
`5 mm/s` passed a 0.10 s hold, while `6 mm/s` first passes near `4.696 s`.
This changes only the Chrono loaded-state timing rule. The Genesis no-action
initial-state RMSE and maximum-drift gates remain `0.5 mm` and `1.0 mm`; no
Genesis physics, loss, or BayesOpt parameter changed.

### Accepted Chrono Low-Speed Target (2026-08-26)

The guided `(0, +5 mm)` 10 mm R&D episode
`A0_oracle_guided_offset_10mm_gate6mm_v1` passes the revised Chrono loading
rule at `4.696 s` (`6 mm/s` linear speed for `0.10 s`; angular speed effectively
zero), followed by fixed `0.25 s` recovery. This is an explicitly documented
low-speed sampling compromise, **not** a static-equilibrium claim. It changes no
Chrono physics and leaves the Genesis initial-state RMSE/max-drift gates at
`0.5/1.0 mm`. Its footprint state is near the 5.0 s strict diagnostic
(`0.350 mm` RMSE), but is materially deeper than the prior 0.75 s snapshot
(`4.236 mm` footprint RMSE). The episode is the R&D target candidate; the 5 mm
protocol remains final-validation-only.

### Fine-Resolution Oracle and Fixed-Time BayesOpt Status (2026-08-29)

The guided offset 5 mm oracle is now complete and accepted:
`A0_oracle_guided_offset_5mm_gate6mm_v1`. It uses the same 1.5 kg vertical
guide, `(0, +5 mm)` center, 0.6 m SCM patch, 1 ms Chrono timestep, `6 mm/s`
for `0.10 s` loading gate, and fixed `0.25 s` residual recovery as the 10 mm
R&D protocol. The 5 mm episode accepts loading at `3.595 s`, records
`34.270 mm` cylinder sinkage, and provides `14,161` valid interior cells on a
`121 x 121` map. Its initial H0 is exactly flat; the former 32 mm preparation
error was therefore not caused by the Chrono target.

Resolution controls isolate the Genesis behavior:

- 20 mm particles, 64-grid, 1 ms: accepted; H0 RMSE `0.618 mm`.
- 10 mm particles, 64-grid, 1 ms: accepted with 40,931 particles; H0 RMSE
  `0.862 mm`, maximum `0.881 mm`, and `14,161` valid cells.
- 10 mm particles, 128-grid, 0.5 ms: rejected; H0 RMSE `32.160 mm`.
- 10 mm particles, 128-grid, 0.25 ms: rejected; H0 RMSE `6.379 mm`.
- 10 mm particles, 128-grid, 0.125 ms: rejected; H0 RMSE `6.220 mm`.
- the same 128-grid/0.125 ms case with geostatic stress scale `1.25` remains
  rejected at `5.939 mm` H0 RMSE and `0.709 mm/s` p99 speed.

Thus the current accepted optimization bed is
`A0_oracle_guided_offset_5mm_gate6mm_prepared_10mm_n64_control`. The
remaining resolution blocker is the higher-density MPM grid interacting with
the approximate isotropic geostatic initialization, not invalid Chrono input.
The 128-grid must pass the unchanged H0 and no-action gates before promotion.

Controlled loading diagnostics on the accepted bed bracketed Young modulus
while keeping `phi=18.149 deg` and `nu=0.100004`: `31.77 kPa` under-indents
(`20.413 mm` cylinder sinkage), `15 kPa` over-indents and remains dynamic
(`50.041 mm`), and `20 kPa` nearly matches the Chrono cylinder motion
(`34.051 mm` versus `34.270 mm`). The 20 kPa surface remains too shallow near
the footprint edge: Genesis mean loaded deformation is `-12.152 mm` versus
Chrono `-19.008 mm`; loaded RMSE is `2.183 mm` and residual-footprint RMSE is
`12.729 mm`. Lowering `E` to 10 kPa or friction to 5 degrees fails the
unchanged frozen-H0 gate, so these are invalid initializations rather than
optimization observations.

BayesOpt now distinguishes raw equilibrium labels from fixed-time acceptance.
When `--loaded-run-full-duration` and requested post-removal observations are
present, complete maps at the target times are scoreable even if the raw phase
reason is `timeout`. H0 RMSE and the 0.25 s no-action drift gates are unchanged.
Online validation run `jg3b5v3s` accepts the 20 kPa candidate as
`fixed_duration` plus `fixed_observation`, with objective `8.548 mm`, loaded
RMSE `2.183 mm`, residual-footprint RMSE `12.729 mm`, and all 14,161 cells.
This improves the previous 10 mm-target best objective by `41.6%`, but is an
R&D baseline rather than the final high-resolution calibration.

The next study must be fresh: no legacy or 10 mm-target seeds. Use the accepted
10 mm-particle/64-grid bed and constrain proposals around the observed
transition (`E=18--32 kPa`, `phi=15--30 deg`, `nu=0.10--0.20`). After the
coarse-grid BayesOpt result is selected, fix the resolution-aware geostatic
initialization, require the 128-grid to pass the same gates, and replay the
best candidates there.

### Fresh Coarse-Grid BayesOpt Result (2026-08-29)

Online W&B study `e72xmaou` used the accepted 5 mm Chrono target and the
accepted 10 mm-particle/64-grid Genesis bed, with no imported observations.
It stopped at its requested target of 12 valid candidates after 12 attempts;
all candidates retained all 14,161 target cells and passed the unchanged gates.

Across the study, candidate H0 RMSE was `2.947--3.941 mm`, and 0.25 s
no-action drift RMSE was only `0.008--0.019 mm`. There were no initialization
failures. This establishes that the current coarse-bed optimization loop is
runnable without bad or rebounding initial states in the narrowed region.

A setup-only predecessor, W&B study `ysagrtcb`, was stopped and excluded after
its first bootstrap candidate inherited a legacy hard-coded 20 mm particle
spacing and disagreed with the frozen 10 mm bed. `bootstrap_candidate()` now
takes particle spacing and size ratio from the prepared-bed manifest-derived
`PARTICLE_CHOICES`; the corrected first candidate was verified at 10 mm.

The study winner is trial `iteration_007`: `E=23.807 kPa`,
`phi=15.532 deg`, and `nu=0.179623`, with objective `9.232 mm`, loaded RMSE
`2.562 mm`, and residual-footprint RMSE `13.339 mm`. It is useful but does not
beat the controlled `E=20 kPa`, `phi=18.149 deg`, `nu=0.100004` observation
at `8.548 mm`; it is `0.684 mm` (`8.0%`) worse. The fresh study never sampled
`nu<0.14`, despite a lower bound of 0.10, so this is an acquisition-coverage
limitation rather than evidence that the established low-nu baseline regressed.

The next calibration step should explicitly include the 20 kPa controlled point
as an anchor and run a compact region around `E=18--26 kPa`,
`phi=15--20 deg`, and `nu=0.10--0.18`. Carry both that anchored winner and
`iteration_007` into the resolution promotion. Before any 128-grid scoring, the
resolution-aware geostatic initializer must pass the same H0 and no-action gates;
then replay the two candidates without changing the target or loss.

### Anchored Trust-Region Result (2026-08-29)

Online W&B study `vrxqwoe2` imported only the validated 20 kPa observation
`jg3b5v3s` and added nine candidates in `E=18--26 kPa`,
`phi=15--20 deg`, and `nu=0.10--0.18`. It reached 10/10 total valid
observations with nine valid new attempts and no initialization rejection.
Every new result retained all 14,161 comparison cells.

The 20 kPa anchor remains best overall at objective `8.548 mm`. Two independent
new proposals confirm the same basin:

- `iteration_007`: `E=18.110 kPa`, `phi=18.984 deg`, `nu=0.103989`,
  objective `8.605 mm`, loaded RMSE `2.159 mm`, residual-footprint RMSE
  `12.892 mm`; only `0.057 mm` (`0.67%`) worse than the anchor.
- `iteration_006`: `E=20.186 kPa`, `phi=18.485 deg`, `nu=0.100693`,
  objective `8.643 mm`, loaded RMSE `2.268 mm`, residual-footprint RMSE
  `12.749 mm`; `0.095 mm` (`1.11%`) worse than the anchor.

The result resolves the prior acquisition-coverage caveat: useful candidates
cluster at `E` near 18--20 kPa, `phi` near 18.1--19.0 degrees, and `nu` at
the 0.10 lower boundary. Coarse-grid search is now sufficiently corroborated;
another broad coarse sweep is not the priority.

Promote the anchor plus `iteration_007` and `iteration_006` as a three-candidate
resolution replay set. The next engineering task is resolution-aware Genesis
geostatic initialization for n128. It must pass the unchanged H0 <= 5 mm and
no-action drift gates before any of these material candidates are scored. This
changes initialization preparation only, not the Chrono target, material model,
contact physics, or objective.

### Ratio-Matched n128 Promotion (2026-08-29)

The n128 initialization blocker is resolved without a stress multiplier or
physics change. The accepted n64 bed had `dx=31.25 mm` and 10 mm particles,
or 3.125 particle spacings per grid cell. The rejected n128 attempts retained
10 mm particles at `dx=15.625 mm`, reducing that ratio to 1.5625 and severely
under-sampling the MPM grid. The promoted bed restores the accepted ratio with
5 mm particles on n128:

`A0_oracle_guided_offset_5mm_gate6mm_prepared_5mm_n128_ratio_matched`

It contains 307,461 particles, uses `dt=0.5 ms`, CPIC, and the physical
geostatic stress scale 1.0. It reaches equilibrium at `1.1825 s` with p99
speed `0.492 mm/s`; H0 RMSE is `0.070 mm` and maximum error `0.237 mm` over
all 14,161 cells. This passes the original gates by a wide surface margin.

Candidate-material relaxation at this resolution needs slightly more than the
old 2 s cap: the three promoted candidates accept at `2.077--2.180 s` under
the unchanged `0.5 mm/s` threshold. Failed setup run `mv698mto` used the old
2 s cap and is excluded. The accepted runs use a 4 s cap, not a looser gate.

All replays use 7,190 loaded steps (`3.595 s`) and 500 residual steps
(`0.25 s`), retain all 14,161 cells, and pass H0/no-action stability:

- 20 kPa anchor, W&B `qgk3079l`: objective `9.626 mm`, loaded RMSE
  `2.142 mm`, residual-footprint RMSE `14.966 mm`, H0 RMSE `0.747 mm`,
  no-action drift RMSE `0.011 mm`.
- coarse `iteration_007`, W&B `nwvdm2h8`: objective `9.833 mm`, loaded
  RMSE `2.188 mm`, residual-footprint RMSE `15.290 mm`.
- coarse `iteration_006`, W&B `4mtb3fyp`: objective `10.041 mm`, loaded
  RMSE `2.316 mm`, residual-footprint RMSE `15.449 mm`.

The 20 kPa anchor remains the winner. Finer resolution improves its loaded RMSE
slightly (`2.183` to `2.142 mm`) but worsens residual-footprint RMSE
(`12.729` to `14.966 mm`). Its residual signed mean is `+14.308 mm`, so
Genesis is too high/too recovered after removal; this is no longer an
initialization or target-resolution error.

The next optimization should therefore run directly on this accepted n128 bed
using only the existing `E`, `phi`, and `nu` parameters, anchored at 20 kPa.
Use a small region such as `E=18--26 kPa`, `phi=16.5--18.5 deg`, and
`nu=0.10--0.13` to seek more retained plastic deformation while preserving
the loaded fit. If that cannot reduce residual error without spoiling loading,
the remaining limitation is the current Genesis Sand constitutive response,
not I/O, Chrono H0, or initialization.

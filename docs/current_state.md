# Current State

Last updated: 2026-08-06

## Repository

Repo root:

```text
/home/moog-2/christo/splatting_stuff/physical/tera_splat
```

Use conda environment:

```text
tsplat
```

CUDA is visible outside the managed sandbox on the host RTX 3060 Ti. Inside the
managed sandbox, CUDA may not be visible; use an unsandboxed shell for GPU
solver runs.

## Source Scene

Current EDGS checkpoint:

```text
../EDGS/output/point_cloud/iteration_7000/point_cloud.ply
```

The current loader uses:

- `opencv-to-zup` axis conversion by default.
- Optional dominant-plane alignment with `--align-ground-z`.
- The current retained splat count is about `256,210`.

Inspect:

```bash
conda run -n tsplat python scripts/view_iteration_7000.py --align-ground-z
```

## Implemented Script Groups

Scene and particles:

- `scripts/view_iteration_7000.py`
- `scripts/particle_io.py`
- `scripts/test_ply_to_particles.py`
- `scripts/view_particle_ply.py`

Solvers and experiments:

- `scripts/run_ground_plane_solver.py`: PhysGaussian/Warp baseline.
- `scripts/run_genesis_ground_plane_solver.py`: Genesis MPM ground-plane run.
- `scripts/run_genesis_indenter_test.py`: Genesis indenter run.
- `scripts/run_splat_matrix_experiments.py`: matrix over splat/subsurface initializers.
- `scripts/run_indenter_matrix_sweep.py`: indenter parameter sweeps.

Rendering and metrics:

- `scripts/check_solver_displacement.py`
- `scripts/render_solver_video.py`
- `scripts/render_indenter_animation.py`
- `scripts/render_indenter_representatives.py`
- `scripts/compute_indenter_sinkage_metrics.py`
- `scripts/compose_matrix_video.py`
- `scripts/compose_indenter_grid_video.py`
- `scripts/transfer_mpm_to_gaussians.py`

## Current Particle Initialization

The current useful initialization is not raw surface-only splats. Surface-only
MPM particles settle or explode under gravity/contact because there is no
volumetric support.

Current accepted initialization pattern:

1. Extract a local visible splat surface.
2. Add regular-grid subsurface layers below a robust local surface estimate.
3. Add a ground plane below the lowest support layer.
4. Gravity-settle the bed.
5. Use the settled base as input for indenter tests.

Accepted manual splat-slice initializer:

```text
outputs/splat_surface_regular_grid_subsurface_1x1_depth0p2_spacing0p025_layer0p0125_noise1p5/
```

Active settled base:

```text
assets/base_settled_stiff_mid/
```

Important files:

```text
assets/base_settled_stiff_mid/particles_initial_mpm.ply
assets/base_settled_stiff_mid/ground_plane_metadata.json
configs/physgaussian_sand_stiff_mid.json
```

Use this settled mid-stiff base for future tuning unless explicitly testing
initialization. Do not restart from the unrelaxed splat/subsurface PLY by
default.

## Genesis Material Notes

Genesis exposes `gs.materials.MPM.Sand(E, nu, rho, friction_angle)`. The local
Genesis sand material implements a Drucker-Prager-like projection in:

```text
/home/moog-2/miniconda3/envs/tsplat/lib/python3.10/site-packages/genesis/engine/materials/MPM/sand.py
```

Parameter-level changes are already wired through config files. Changing the
actual particle update law requires a custom Genesis material or patching the
installed material source.

## Indenter Direction

The real `real3` contact query is mass-controlled gravitational loading:

- Dynamic rigid cylinder with measured radius, height, mass, and inertia.
- Bottom face placed at first contact with the initial terrain.
- Zero initial linear and angular velocity.
- Release under gravity with no prescribed downward motion and no added force.
- Loaded settling stops from a documented equilibrium criterion.
- Removal uses a fixed documented kinematic vertical-lift protocol.
- Post-removal settling stops from a documented equilibrium criterion.
- Save particle frames, cylinder pose/state, metrics, config, and video.

The existing indenter scripts can be reused only after they support a genuine
`mass_controlled` mode and reject target depth, prescribed downward trajectories,
and added downward forces for the real action.

Avoid raw particle pressure as the main experiment. Use it only as a debug
baseline.

Representative indenter command entry points:

```bash
conda run -n tsplat python scripts/run_genesis_indenter_test.py --help
conda run -n tsplat python scripts/run_indenter_matrix_sweep.py --help
```

## Single-Trial real3 Calibration

The RealSense real3 preprocessing/report layer is implemented:

```bash
conda run -n tsplat python scripts/preprocess_single_trial_real3.py --copy-plys
conda run -n tsplat python scripts/make_single_trial_report.py \
  --output reports/single_trial_real3_report.md
```

Normalized data:

```text
data/single_trial_real3/
```

Current report:

```text
reports/single_trial_real3_report.md
```

The Genesis coarse-grid calibration search is intentionally not run yet. The
mass-controlled action path exists, but its loaded-settling criterion has not
been validated. Remaining gates include the contact-center/footprint review,
two-way rigid-MPM contact through loaded equilibrium and removal, settled mass
monotonicity, complete state restoration, and final scan-noise estimation.

Completed bridge steps:

- Static-border plane correction is implemented and saved in
  `data/single_trial_real3/processed/delta_h_real_corrected.npz`.
- Footprint/mask diagnostic is saved at
  `data/single_trial_real3/processed/scan_correction_footprint_diagnostic.png`.
- Raw median `delta_h` was `+0.00347291209 m`; plane-corrected median
  `delta_h` is `+0.0000524610803 m`.
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

Critical correction from the gap bridge: `0.14605 m` is the cylinder diameter,
not radius. The correct radius is `0.073025 m`; otherwise the contact area is
four times too large and nominal pressure is four times too small.

## Frame Sorting

Frame sorting must be numeric, not lexicographic. This matters for outputs with
more than `sim_9999.ply`. The current checker, video renderer, and Viser
animation path sort by numeric frame index.

## Large Outputs

Outputs are intentionally ignored by git. Some useful recent outputs are large:

- 10 s raised-ground surface-shell run: about `5.7G`.
- Matrix and indenter sweeps can produce many PLY frame folders and videos.

Before creating new long rollouts, check free disk:

```bash
df -h outputs
```

## Known Limitations

- Surface-only particle clouds are not physically meaningful sand beds.
- Low gravity is a visualization stabilizer, not a physical calibration.
- Real calibration should use a settled volumetric/subsurface-supported bed.
- Current single-trial calibration target should vary only `log10_E` and
  `phi_deg`; all other physics/configuration must be fixed and recorded.

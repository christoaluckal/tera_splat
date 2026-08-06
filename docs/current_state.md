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

The Genesis coarse-grid calibration search is intentionally not run yet because
the mass-controlled action path is not implemented and
`data/single_trial_real3/action.yaml` still has unresolved fields/protocols:
contact center, first-contact convention, loaded/post-removal equilibrium
checks, removal protocol assumptions, two-way rigid-MPM contact validation, and
final scan-noise estimate.

Current blockers:

1. Center footprint overlay is not visually verified. The current `[0.0, 0.0]`
   assumes the bed-frame origin is the physical center.
2. Static-border scan bias correction is not implemented. Current median
   `delta_h` is positive, which is suspicious for a removed cylinder.
3. Two localized views per surface are not exported separately for final
   two-view noise estimation.
4. Genesis mass-controlled action mode is not implemented. The current indenter
   scripts were originally built around prescribed indentation depth.
5. Cylinder mass/inertia application in Genesis is not verified.
6. Free-fall gravity behavior is not tested.
7. Two-way rigid-MPM contact for a released cylinder is not validated.
8. Mass monotonicity is not tested for `0.75`, `1.5`, and `3.0 kg`.
9. Loaded-settling termination logic is not implemented or validated.
10. Post-removal settling termination logic is not implemented or validated.
11. Initial simulated `S0` projection/footprint match is not verified.
12. Complete MPM state restore is not implemented or validated. A PLY with only
    positions is not enough state for calibrated rollouts.
13. No-cylinder drift is not characterized or subtracted.
14. Synthetic `3 x 3` parameter recovery is not complete.
15. Final scan-noise estimate is missing. The current Huber delta is only an ICP
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

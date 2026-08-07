# AGENTS.md

This file is the handoff entry point for coding agents working in `tera_splat`.

## Project Scope

Prototype contact-conditioned terrain Gaussian splatting:

1. Load a terrain Gaussian/splat scene.
2. Convert a local sand surface into MPM particles with subsurface support.
3. Run Genesis or PhysGaussian MPM terrain deformation.
4. Use mass-controlled gravitational circular-cylinder placement as the real physical query.
5. Calibrate effective Genesis sand parameters against one real RealSense trial.
6. Later transfer MPM deformation back to Gaussian splats.

## Repository And Environment

Repo:

```text
/home/moog-2/christo/splatting_stuff/physical/tera_splat
```

Related data/source repos:

```text
../EDGS/output/point_cloud/iteration_7000/point_cloud.ply
../PhysGaussian/
../lamp/ros2_ws/src/realsense_splat/
```

Use:

```text
conda env: tsplat
```

CUDA is available on the host but may be hidden inside the managed sandbox.
For CUDA solver jobs, use an unsandboxed execution path when required.

## Read These First

```text
README.md
docs/current_state.md
docs/single_trial_calibration.md
docs/realsense_instrumentation_real6.md
docs/mass_controlled_bridge_findings.md
docs/00_physgaussian_notes.md
EXTERNAL.md
```

`AGENTS.md` and `docs/` are the current handoff source of truth.

## Current Baseline

Do not tune from a raw surface-only particle cloud. It is not a stable sand bed.

Use a settled splat-derived terrain base by default:

```text
assets/base_settled_stiff_mid/
```

Key files:

```text
assets/base_settled_stiff_mid/particles_initial_mpm.ply
assets/base_settled_stiff_mid/ground_plane_metadata.json
configs/physgaussian_sand_stiff_mid.json
```

Current accepted manual splat-slice initializer:

```text
outputs/splat_surface_regular_grid_subsurface_1x1_depth0p2_spacing0p025_layer0p0125_noise1p5/
```

## Commands

Inspect the EDGS splat:

```bash
conda run -n tsplat python scripts/view_iteration_7000.py --align-ground-z
```

Validate PLY-to-particles:

```bash
conda run -n tsplat python scripts/test_ply_to_particles.py \
  --max-particles 25621 \
  --trim-quantile 0.005 \
  --output-dir outputs/ply_particle_test_10pct_trim005_min_ground
```

View a single PLY:

```bash
conda run -n tsplat python scripts/view_particle_ply.py \
  outputs/ply_particle_test_10pct_trim005_min_ground/particles_initial_mpm.ply \
  --point-size 0.003 \
  --port 8082
```

Run Genesis ground-plane baseline:

```bash
conda run -n tsplat python scripts/run_genesis_ground_plane_solver.py \
  --config configs/physgaussian_sand_soft.json \
  --max-particles 25621 \
  --trim-quantile 0.005 \
  --duration 2.0 \
  --dt 0.0005 \
  --n-grid 64 \
  --backend cuda \
  --gravity-scale 0.05 \
  --output-dir outputs/genesis_cuda_10pct_trim005_soft_g005_2s_dt0005
```

Render solver video without loading all PLYs in Viser:

```bash
conda run -n tsplat python scripts/render_solver_video.py \
  outputs/genesis_cuda_10pct_trim005_soft_g005_2s_dt0005 \
  --duration 4.0 \
  --fps 60 \
  --point-radius 1 \
  --output outputs/genesis_cuda_10pct_trim005_soft_g005_2s_dt0005/solver_animation_oblique_4s.mp4
```

Explore indenter scripts:

```bash
conda run -n tsplat python scripts/run_genesis_indenter_test.py --help
conda run -n tsplat python scripts/run_indenter_matrix_sweep.py --help
conda run -n tsplat python scripts/run_mass_controlled_terrain.py --help
```

## RealSense real3 Calibration Inputs

RealSense package:

```text
../lamp/ros2_ws/src/realsense_splat
```

Important artifacts:

```text
../lamp/ros2_ws/src/realsense_splat/episodes/real3_compare_metrics_3tag/real3_dem_report_3tag.json
../lamp/ros2_ws/src/realsense_splat/episodes/real3_compare_metrics_3tag/before_dem_3tag.npy
../lamp/ros2_ws/src/realsense_splat/episodes/real3_compare_metrics_3tag/after_dem_3tag.npy
../lamp/ros2_ws/src/realsense_splat/episodes/real3_compare_metrics_3tag/after_icp_aligned_dem_3tag.npy
../lamp/ros2_ws/src/realsense_splat/episodes/real3_compare_metrics_3tag/after_fused_points_icp_aligned.ply
../lamp/ros2_ws/src/realsense_splat/episodes/real3_pre_metrics_offline/
../lamp/ros2_ws/src/realsense_splat/episodes/real3_post_metrics_offline/
```

Coordinate convention from `realsense_splat`:

```text
world frame: bed
camera frame: camera_color_optical_frame
depth_scale_m_per_unit: 0.001
```

The real3 3-tag DEM report uses:

```text
cell_size_m: 0.01
bounds_xy_m: [-0.75, 0.75, -0.75, 0.75]
```

Normalized single-trial data and current report:

```text
data/single_trial_real3/
reports/single_trial_real3_report.md
```

Regenerate them with:

```bash
conda run -n tsplat python scripts/preprocess_single_trial_real3.py --copy-plys
conda run -n tsplat python scripts/make_single_trial_report.py \
  --output reports/single_trial_real3_report.md
```

## Single-Trial Calibration Direction

Use `docs/single_trial_calibration.md` for the integrated calibration plan.

First calibration should vary only:

```text
log10_E
phi_deg
```

Everything else must be fixed and recorded. Do not change Genesis update
equations for the initial calibration.

Required before running calibration:

- Correct cylinder geometry: diameter `0.14605 m`, radius `0.073025 m`, height
  `0.0508 m`, mass `1.5 kg`.
- Footprint overlay verification for center `[0.0, 0.0]`; this assumes the bed
  frame origin is the physical center.
- Static-border pre/post scan bias correction.
- Separate two-view exports and final two-view noise estimate for
  Huber/plausible-region thresholds.
- Fixed mass-controlled placement/removal protocol and first-contact convention.
- Choice of direct vs ICP-aligned real DEM target.

Completed bridge artifacts:

- Static-border plane correction and footprint diagnostic:
  `data/single_trial_real3/processed/scan_correction.json`
  `data/single_trial_real3/processed/scan_correction_footprint_diagnostic.png`
- Corrected residual:
  `data/single_trial_real3/processed/delta_h_real_corrected.npz`
- Free-fall/mass/inertia check:
  `outputs/mass_controlled_bridge_checks/free_fall_report.json`
- Short gravity terrain smokes:
  `outputs/mass_controlled_bridge_checks/gravity_terrain_smoke_m0p75`
  `outputs/mass_controlled_bridge_checks/gravity_terrain_smoke`
  `outputs/mass_controlled_bridge_checks/gravity_terrain_smoke_m3p0`
- Capped mass-controlled terrain phase smoke:
  `outputs/mass_controlled_bridge_checks/mass_controlled_terrain_smoke_cpu_capped`
- Longer CUDA mass-controlled rollout:
  `outputs/mass_controlled_bridge_checks/mass_controlled_terrain_cuda_longer`

Those terrain smokes show monotonic sinkage over `0.04 s`, but they do not
prove loaded equilibrium, complete removal, complete state restore, or
no-cylinder drift.

Action convention:

- The calibration action is mass-controlled gravitational loading.
- `mass_kg` is required; penetration is a simulation output.
- `0.14605 m` is cylinder diameter, not radius. Use `radius_m: 0.073025`.
- No target depth, prescribed downward speed, or added downward force should be
  present for the real action.
- Place the cylinder bottom face at the 99th-percentile first-contact height in
  the footprint, release with zero initial linear/angular velocity, settle,
  remove with a fixed numerical lift protocol, then settle again.
- Add/maintain tests for vertical sign, pose point, first-contact convention,
  free fall, mass/inertia application, two-way contact, mass monotonicity, and
  rejection of incompatible displacement controls.

Calibration execution order:

1. Verify center `[0.0, 0.0]` by footprint overlay.
2. Review the static-border scan correction and footprint diagnostic.
3. Export separate localized views and replace provisional noise with two-view
   noise.
4. Add mass-controlled mode to the Genesis runner.
5. Verify free fall, runtime mass/inertia, two-way contact, and mass
   monotonicity.
6. Verify real/sim axes, units, ROI, DEM grid, and cylinder footprint overlay.
7. Add complete state restore and no-cylinder drift handling.
8. Run one midrange candidate and duplicate determinism check.
9. Run synthetic `3 x 3` parameter recovery.
10. Run real `3 x 3` smoke grid.
11. Run full `8 x 8` grid.
12. Run protocol sensitivity: initial clearance, contact center, removal speed,
   equilibrium thresholds, and fixed contact-friction alternatives.
13. Generate final report.

## Development Rules

- Keep generated outputs under `outputs/`; they are ignored by git.
- Do not commit large PLY/video output artifacts.
- Use numeric frame sorting for `sim_*.ply`; lexicographic sort is wrong after
  `sim_9999.ply`.
- Do not overwrite user configs without reading them.
- Prefer `rg` for search.
- Use `apply_patch` for manual source/doc edits.

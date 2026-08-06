# Tera Splat

Prototype for contact-conditioned terrain Gaussian splatting.

Current focus:

1. Build a stable splat-derived sand bed with subsurface support.
2. Run Genesis/PhysGaussian MPM terrain deformation.
3. Use a mass-controlled gravitational circular-cylinder placement as the real contact query.
4. Calibrate effective Genesis sand parameters from one RealSense before/after
   terrain trial.
5. Later transfer MPM displacement back to renderable Gaussians.

## Handoff

Start here:

```text
AGENTS.md
docs/README.md
docs/current_state.md
docs/single_trial_calibration.md
```

The old phase-roadmap docs were removed because they were stale relative to the
implemented scripts and current Genesis/RealSense direction.

## Environment

Use:

```text
conda env: tsplat
```

CUDA is available on the host but may be hidden inside managed sandboxed
commands. Run CUDA solver jobs from an unsandboxed shell/session when needed.

## Main Inputs

EDGS splat:

```text
../EDGS/output/point_cloud/iteration_7000/point_cloud.ply
```

PhysGaussian:

```text
../PhysGaussian/
```

RealSense real3 data:

```text
../lamp/ros2_ws/src/realsense_splat/
```

Important RealSense calibration artifacts:

```text
../lamp/ros2_ws/src/realsense_splat/episodes/real3_compare_metrics_3tag/real3_dem_report_3tag.json
../lamp/ros2_ws/src/realsense_splat/episodes/real3_compare_metrics_3tag/before_dem_3tag.npy
../lamp/ros2_ws/src/realsense_splat/episodes/real3_compare_metrics_3tag/after_dem_3tag.npy
../lamp/ros2_ws/src/realsense_splat/episodes/real3_compare_metrics_3tag/after_icp_aligned_dem_3tag.npy
```

Normalized calibration data and report:

```text
data/single_trial_real3/
reports/single_trial_real3_report.md
```

## Useful Commands

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

View one particle PLY:

```bash
conda run -n tsplat python scripts/view_particle_ply.py \
  outputs/ply_particle_test_10pct_trim005_min_ground/particles_initial_mpm.ply \
  --point-size 0.003 \
  --port 8082
```

Run current Genesis ground-plane baseline:

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

Render solver output without loading all PLYs in Viser:

```bash
conda run -n tsplat python scripts/render_solver_video.py \
  outputs/genesis_cuda_10pct_trim005_soft_g005_2s_dt0005 \
  --duration 4.0 \
  --fps 60 \
  --point-radius 1 \
  --output outputs/genesis_cuda_10pct_trim005_soft_g005_2s_dt0005/solver_animation_oblique_4s.mp4
```

Check indenter entry points:

```bash
conda run -n tsplat python scripts/run_genesis_indenter_test.py --help
conda run -n tsplat python scripts/run_indenter_matrix_sweep.py --help
```

Prepare the real3 single-trial data contract and report:

```bash
conda run -n tsplat python scripts/preprocess_single_trial_real3.py --copy-plys
conda run -n tsplat python scripts/make_single_trial_report.py \
  --output reports/single_trial_real3_report.md
```

## Current Warnings

- Do not tune from raw surface-only particles; use a settled bed with subsurface
  support.
- Low-gravity surface-shell videos are visualization artifacts, not calibration.
- The first real calibration should vary only `log10_E` and `phi_deg`.
- Generated outputs under `outputs/` are ignored and can be very large.

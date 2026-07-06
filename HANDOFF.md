# Project Handoff

Last updated: 2026-07-06

## Project Goal

This repository is a prototype for contact-conditioned terrain Gaussian
splatting. The target query is:

```text
Given a Gaussian-splat terrain map, what would the sand terrain look like after
a localized shallow surface load is applied at location X?
```

The current milestone is not full robot-terrain contact. The immediate goal is
a stable, inspectable pipeline that can load a terrain splat scene, convert a
local sand surface into MPM particles, run a shallow deformation simulation, and
eventually transfer particle displacement back into renderable Gaussians.

Primary docs:

- `README.md`: current commands, run recipes, and long-form roadmap.
- `docs/README.md`: phase reading order and global success criteria.
- `docs/00_physgaussian_notes.md`: relevant PhysGaussian implementation notes.
- `docs/04_phase_mpm_pressure_patch.md`: current MPM pressure-patch phase.
- `docs/11_current_solver_status.md`: latest solver status and observed runs.

## Current Scene And Assumptions

- Working scene:

```text
../EDGS/output/point_cloud/iteration_7000/point_cloud.ply
```

- Use conda environment: `tsplat`.
- First-pass material assumption: every retained Gaussian is sand.
- The rigid pole is intentionally ignored until viewing, extraction, and
  baseline deformation are stable.
- Default axis transform is `opencv-to-zup`, mapping:

```text
(x, y, z) -> (x, z, -y)
```

- The retained splat count in the current scene is 256,210.
- A 1/10 sample is about 25,621 input particles; with
  `--trim-quantile 0.005`, the current sample keeps 24,921 particles.

## Environment Notes

- CUDA is visible outside the managed sandbox on an RTX 3060 Ti.
- Inside the managed sandbox, CUDA is not visible to `nvidia-smi`, PyTorch, or
  Warp.
- Run CUDA solver jobs from an unsandboxed shell/session.
- Genesis compile/cache paths are redirected under `outputs/.cache` by
  `scripts/run_genesis_ground_plane_solver.py`.

Useful checks:

```bash
nvidia-smi
conda run -n tsplat python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

## Working Pieces

- `scripts/view_iteration_7000.py` loads the EDGS iteration-7000 scene in Viser.
- `--align-ground-z` fits the dominant sand plane and rotates its normal to
  world `+Z`; the same rotation is applied to centers and covariances.
- `scripts/particle_io.py` is the shared PLY-to-particle path for both solver
  backends.
- `scripts/test_ply_to_particles.py` validates conversion, writes
  `particles_initial_mpm.ply`, round-trips it, and reports bounds/ground stats.
- `scripts/run_ground_plane_solver.py --dry-run` creates initial PhysGaussian
  MPM particles and ground-plane metadata.
- `scripts/run_genesis_ground_plane_solver.py` imports the same particles into
  Genesis MPM and writes `simulation_ply/sim_*.ply`.
- `scripts/check_solver_displacement.py` reports first-to-last frame motion.
- `scripts/view_particle_ply.py` opens a single particle PLY in Viser.
- `scripts/view_solver_animation.py` plays solver PLY output in Viser.
- `scripts/render_solver_video.py` renders solver PLY sequences to MP4 without
  loading thousands of frames into Viser.
- `scripts/generate_ground_plane_preview.py` is a non-MPM viewer/debug fallback.

## Basic Commands

Inspect the source scene:

```bash
conda run -n tsplat python scripts/view_iteration_7000.py
```

Open Viser:

```text
http://localhost:8080
```

Run a non-server load check:

```bash
conda run -n tsplat python scripts/view_iteration_7000.py --dry-run
```

Validate PLY-to-particle conversion:

```bash
conda run -n tsplat python scripts/test_ply_to_particles.py \
  --max-particles 1000 \
  --output-dir outputs/ply_particle_test_1k
```

Create a PhysGaussian/Warp MPM setup without running Warp:

```bash
conda run -n tsplat python scripts/run_ground_plane_solver.py --dry-run
```

Check displacement after a solver run:

```bash
conda run -n tsplat python scripts/check_solver_displacement.py \
  outputs/cuda_soft_1k_s10
```

View one particle PLY:

```bash
conda run -n tsplat python scripts/view_particle_ply.py \
  outputs/ply_particle_test_10pct_trim005_min_ground/particles_initial_mpm.ply \
  --point-size 0.003 \
  --port 8082
```

## Current PhysGaussian/Warp Solver Status

The real PhysGaussian/Warp MPM path initializes on CUDA outside the sandbox, but
it is not yet stable for longer simulations.

Known behavior:

- Tiny CPU MPM smoke tests can write a few frames.
- Longer CPU MPM runs have segfaulted in Warp.
- A hard-parameter CUDA probe initializes and writes a few frames, then fails in
  `p2g_apic_with_stress` with `CUDA error 700: illegal memory access`.
- The hard config uses `E = 5e7`, which appears too stiff for the normalized
  EDGS surface shell.

Known-good tiny CPU smoke:

```bash
conda run -n tsplat python scripts/run_ground_plane_solver.py \
  --max-particles 1000 \
  --steps 2 \
  --n-grid 32 \
  --device cpu \
  --output-dir outputs/ground_plane_solver_cpu_smoke
```

Soft CUDA stability ladder start:

```bash
conda run -n tsplat python scripts/run_ground_plane_solver.py \
  --config configs/physgaussian_sand_soft.json \
  --max-particles 1000 \
  --steps 10 \
  --dt 0.0001 \
  --n-grid 64 \
  --device cuda:0 \
  --output-dir outputs/cuda_soft_1k_s10
```

Observed result for `outputs/cuda_soft_1k_s10`:

```text
frames: 11
particles: 1000
status: completed on cuda:0
max_displacement: 7.69e-05
mean_displacement: 9.85e-07
z_delta_min: -7.69e-05
z_delta_max: 8.94e-08
```

Interpretation: the softened CUDA setup is stable for a small run, but the
motion is still very small. Increase step count before particle count, grid
resolution, or stiffness.

## Current Genesis Solver Status

Genesis is additive; it does not replace the PhysGaussian/Warp path. It uses
the same PLY extraction and output format.

Current usable visualization recipe:

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

Observed displacement:

```text
frames: 4001
particles: 24921
max_displacement: 0.40269309680361826
mean_displacement: 0.26032774047886686
median_displacement: 0.26421751242576297
z_delta_min: -0.4026811718940735
z_delta_max: -0.0025490671396255493
```

Render that run:

```bash
conda run -n tsplat python scripts/render_solver_video.py \
  outputs/genesis_cuda_10pct_trim005_soft_g005_2s_dt0005 \
  --duration 4.0 \
  --fps 60 \
  --point-radius 1 \
  --output outputs/genesis_cuda_10pct_trim005_soft_g005_2s_dt0005/solver_animation_oblique_4s.mp4
```

Raised-ground 10-second recipe:

```bash
conda run -n tsplat python scripts/run_genesis_ground_plane_solver.py \
  --config configs/physgaussian_sand_soft.json \
  --max-particles 25621 \
  --trim-quantile 0.005 \
  --ground-quantile 0.02 \
  --duration 10.0 \
  --dt 0.0005 \
  --n-grid 64 \
  --backend cuda \
  --gravity-scale 0.05 \
  --output-dir outputs/genesis_cuda_10pct_trim005_soft_g005_gq002_10s_dt0005
```

Observed output:

```text
frames: 20001
particles: 24921
max_displacement: 0.7995077414054058
mean_displacement: 0.21824543399833113
median_displacement: 0.2201822295129591
z_delta_min: -0.7936241924762726
z_delta_max: 0.02162608504295349
folder size: 5.7G
```

Important caveat: these Genesis runs still simulate a sparse surface shell, not
a filled sand volume. Low gravity is a visualization stabilizer. The correct
next physics step is volumetric particle fill/support and then a localized
load; otherwise gravity keeps settling the surface.

## Current Configs

- `configs/physgaussian_sand.json`: hard initial sand config; `E = 5e7`.
- `configs/physgaussian_sand_soft.json`: current soft stability config;
  `E = 2000`, `nu = 0.2`, `density = 200`, `g = [0, 0, -4]`,
  `friction_angle = 35`, `n_grid = 64`.

Prefer the soft config for Genesis and current CUDA stability work.

## Next Engineering Steps

1. Keep extending the soft PhysGaussian/Warp stability ladder:
   increase step count first, then particle count, grid resolution, or
   stiffness.
2. Add explicit particle/grid bounds checks around MPM stepping so illegal
   memory accesses can be tied to particles leaving the valid stencil.
3. Separate simulation substep `dt` from saved visual frame cadence so playback
   rate does not force unstable physics timesteps.
4. Implement shallow subsurface particle support/fill; the current surface shell
   is the main physics limitation.
5. Only after gravity + ground-plane runs are stable, add localized load/query
   controls for circular displacement or pressure.
6. Transfer particle displacement back to Gaussian centers first; defer
   covariance updates until center-only renders are clean.
7. Add deformation metrics: indentation depth, displaced-volume proxy, and
   local deformation radius.

## Avoid These Pitfalls

- Do not treat `generate_ground_plane_preview.py` output as a physics result;
  it is explicitly non-MPM viewer/debug output.
- Do not use the hard `E = 5e7` config for Genesis surface-shell runs unless the
  goal is to reproduce instability.
- Do not assume identical tiny MPM frames mean the viewer is broken; the current
  tiny real MPM smoke frames may advance too few very small substeps to show
  visible motion.
- Do not add contact loading before gravity-only ground-plane runs are stable.
- Do not run CUDA solver jobs inside the managed sandbox and expect the GPU to
  be visible.

## Worktree Snapshot At Handoff Creation

The worktree already had local modifications before this handoff file was
created. Treat these as in-progress project state:

```text
 M README.md
 M docs/11_current_solver_status.md
 M scripts/check_solver_displacement.py
 M scripts/run_ground_plane_solver.py
 M scripts/view_solver_animation.py
?? scripts/particle_io.py
?? scripts/render_solver_video.py
?? scripts/run_genesis_ground_plane_solver.py
?? scripts/test_ply_to_particles.py
?? scripts/view_particle_ply.py
```

This handoff file is additive and does not intentionally revert or overwrite
those changes.

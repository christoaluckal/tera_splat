# Current Solver Status

## Summary

The Viser and particle export paths work. The real PhysGaussian MPM path now
initializes on CUDA outside the sandbox, but longer simulations are not stable
yet.

## Environment

- Use conda environment: `tsplat`.
- Global CUDA toolkit is present: `nvcc 12.8`.
- Host GPU is visible outside the sandbox: RTX 3060 Ti.
- Inside the managed sandbox, CUDA is not visible; use an unsandboxed shell for
  GPU solver runs.

Useful checks:

```bash
nvidia-smi
conda run -n tsplat python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

## Working Pieces

- `scripts/view_iteration_7000.py` loads EDGS iteration 7000 in Viser.
- `--align-ground-z` analytically fits the sand plane and aligns its normal to
  `+Z`.
- `scripts/particle_io.py` is the shared PLY-to-particle path used by both MPM
  backends.
- `scripts/test_ply_to_particles.py` validates the conversion, writes
  `particles_initial_mpm.ply`, round-trips it, and reports bounds/ground stats.
- `scripts/run_ground_plane_solver.py --dry-run` creates initial MPM particles
  and ground-plane metadata.
- `scripts/run_genesis_ground_plane_solver.py` runs a Genesis MPM update from
  the same imported particles and writes the same `simulation_ply/sim_*.ply`
  format as the PhysGaussian/Warp runner.
- Tiny CPU MPM smoke tests can write a few PLY frames.
- `scripts/view_solver_animation.py` displays `simulation_ply/sim_*.ply`
  folders.
- `scripts/generate_ground_plane_preview.py` creates non-MPM kinematic preview
  frames for viewer debugging.

## Current Real MPM Error

CUDA run command used:

```bash
conda run -n tsplat python scripts/run_ground_plane_solver.py \
  --max-particles 1000 \
  --steps 100 \
  --dt 0.002 \
  --n-grid 64 \
  --device cuda:0 \
  --output-dir outputs/ground_plane_solver_cuda_smoke
```

Observed behavior:

- Warp initializes on `cuda:0`.
- Kernels compile.
- Frames `sim_0000000000.ply` through about `sim_0000000004.ply` are written.
- Then the run fails:

```text
Warp CUDA error 700: an illegal memory access was encountered
Error launching kernel: p2g_apic_with_stress on device cuda:0
RuntimeError: CUDA error detected: 700
```

CPU longer runs have also segfaulted in Warp. This indicates the next issue is
solver stability/API compatibility, not missing CUDA.

## Next Solver Steps

- Reduce stiffness first. The current config uses `E = 5e7`; test softer values
  near the PhysGaussian `run_sand.py` scale such as `E = 2000` or `E = 1e4`.
- Reduce `dt` before increasing frame count.
- Keep particle count and grid small while debugging, then scale up.
- Add explicit particle/grid bounds checks before each MPM step.
- Save every Nth step separately from solver substeps so visual frame rate does
  not force an unstable physics timestep.
- Only add contact loading after the gravity + ground-plane run moves without
  kernel errors.

The first soft config is:

```text
configs/physgaussian_sand_soft.json
```

Initial ladder command:

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

Displacement checker:

```bash
conda run -n tsplat python scripts/check_solver_displacement.py \
  outputs/cuda_soft_1k_s10
```

First ladder result:

```text
outputs/cuda_soft_1k_s10
frames: 11
particles: 1000
status: completed on cuda:0
max_displacement: 7.69e-05
mean_displacement: 9.85e-07
z_delta_min: -7.69e-05
z_delta_max: 8.94e-08
```

This confirms the softened CUDA setup is stable for a small run, but motion is
still very small. Next ladder step should increase step count before increasing
particle count, grid resolution, or stiffness.

## Genesis Backend

The Genesis path is additive; it does not replace the PhysGaussian/Warp solver.
Both runners now share the same PLY extraction and normalization code. Genesis
uses `gs.morphs.Nowhere(n_particles=...)` so it can receive exactly the
PLY-derived particle set, then explicitly sets positions, zero velocities, and
active flags before stepping.

PLY conversion tester:

```bash
conda run -n tsplat python scripts/test_ply_to_particles.py \
  --max-particles 25621 \
  --trim-quantile 0.005 \
  --output-dir outputs/ply_particle_test_10pct_trim005_min_ground
```

Observed tester result for the current 1/10 sample:

```text
particles: 24921
ground z: 0.1599999964237213
particles below ground tolerance: 0
round-trip max abs error: 0.0
```

The retained splat count is 256,210, so 1/10 is about 25,621 input particles.
`--trim-quantile 0.005` removes spatial outliers before normalization; the
trimmed sample keeps 24,921 particles. The default ground proxy is now the
minimum retained particle height. Avoid the older 1% quantile ground proxy for
baseline runs because it places some particles initially below the collider.

Genesis CPU movement smoke:

```bash
conda run -n tsplat python scripts/run_genesis_ground_plane_solver.py \
  --max-particles 200 \
  --steps 2 \
  --dt 0.01 \
  --n-grid 32 \
  --backend cpu \
  --output-dir outputs/genesis_cpu_smoke_200_dt001_active
```

Observed displacement:

```text
frames: 3
particles: 200
max_displacement: 0.7496389475643895
mean_displacement: 0.01818940725900377
median_displacement: 0.0029400750227672494
z_delta_min: -0.08946001529693604
z_delta_max: 0.7495687305927277
```

This larger `dt` is a movement smoke test, not a stable production setting;
Genesis warns that `0.01` is above its suggested step for this grid. Use smaller
`dt` for real runs, then save or resample frames for viewer playback.

Genesis CUDA smoke:

```bash
conda run -n tsplat python scripts/run_genesis_ground_plane_solver.py \
  --max-particles 200 \
  --steps 2 \
  --dt 0.001 \
  --n-grid 32 \
  --backend cuda \
  --output-dir outputs/genesis_cuda_smoke_200_dt0001
```

Observed displacement:

```text
frames: 3
particles: 200
max_displacement: 0.10602174967469935
mean_displacement: 0.004200364356073631
median_displacement: 2.9385089874267578e-05
z_delta_min: -0.08751952648162842
z_delta_max: 0.08750000596046448
```

Genesis cache note: the runner sets `XDG_CACHE_HOME`, `GS_CACHE_FILE_PATH`,
`NUMBA_CACHE_DIR`, and `MPLCONFIGDIR` under `outputs/.cache` before importing
Genesis. Without this, Quadrants may try to compile into
`/home/moog-2/.cache/quadrants`, which is read-only in the managed sandbox.

## Current Calmer Genesis Recipe

The hard material config (`E=5e7`) explodes on the sparse surface-only particle
shell. The current usable visualization recipe uses the soft sand config,
outlier trimming, minimum-height ground, and low gravity:

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

Render a still particle PLY in Viser without loading all frames:

```bash
conda run -n tsplat python scripts/view_particle_ply.py \
  outputs/ply_particle_test_10pct_trim005_min_ground/particles_initial_mpm.ply \
  --point-size 0.003 \
  --port 8082
```

Render a video without loading every PLY into Viser:

```bash
conda run -n tsplat python scripts/render_solver_video.py \
  outputs/genesis_cuda_10pct_trim005_soft_g005_2s_dt0005 \
  --duration 4.0 \
  --fps 60 \
  --point-radius 1 \
  --output outputs/genesis_cuda_10pct_trim005_soft_g005_2s_dt0005/solver_animation_oblique_4s.mp4
```

Remaining physics limitation: this is still a surface shell, not a filled sand
volume. Low gravity is a visualization stabilizer. The correct next physics step
is volumetric particle fill/support and then a localized load; otherwise gravity
will keep settling the surface.

## Raised-Ground 10s Run

To make particles contact the ground earlier, raise the ground from the minimum
height to the 2% height quantile:

```bash
conda run -n tsplat python scripts/test_ply_to_particles.py \
  --max-particles 25621 \
  --trim-quantile 0.005 \
  --ground-quantile 0.02 \
  --output-dir outputs/ply_particle_test_10pct_trim005_gq002
```

Observed conversion:

```text
particles: 24921
ground z: 0.3020949959754944
particles below ground tolerance: 499
```

10-second Genesis run:

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
first: sim_0000.ply
last: sim_20000.ply
max_displacement: 0.7995077414054058
mean_displacement: 0.21824543399833113
median_displacement: 0.2201822295129591
z_delta_min: -0.7936241924762726
z_delta_max: 0.02162608504295349
folder size: 5.7G
```

Render the 10-second MP4:

```bash
conda run -n tsplat python scripts/render_solver_video.py \
  outputs/genesis_cuda_10pct_trim005_soft_g005_gq002_10s_dt0005 \
  --duration 10.0 \
  --fps 60 \
  --point-radius 1 \
  --output outputs/genesis_cuda_10pct_trim005_soft_g005_gq002_10s_dt0005/solver_animation_oblique_10s.mp4
```

`view_solver_animation.py`, `render_solver_video.py`, and
`check_solver_displacement.py` now sort `sim_*.ply` frames by numeric frame
index so runs beyond `sim_9999.ply` use `sim_20000.ply` as the final frame.

## Viewer Caveat

If real MPM output frames are identical, the viewer is not broken. The current
tiny real MPM smoke frames have zero displacement because they advance too few
very small substeps. The gravity preview is intentionally labeled non-MPM and
should only be used to verify playback and ground-plane visualization.

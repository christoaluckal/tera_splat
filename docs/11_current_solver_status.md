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
- `scripts/run_ground_plane_solver.py --dry-run` creates initial MPM particles
  and ground-plane metadata.
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

## Viewer Caveat

If real MPM output frames are identical, the viewer is not broken. The current
tiny real MPM smoke frames have zero displacement because they advance too few
very small substeps. The gravity preview is intentionally labeled non-MPM and
should only be used to verify playback and ground-plane visualization.

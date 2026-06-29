# PhysGaussian Notes

## Goal

Capture the paper and implementation details that matter for the terrain
prototype, without restating the whole PhysGaussian project.

## Core Idea

PhysGaussian uses one representation for simulation and rendering: 3D Gaussian
kernels are treated as continuum particles, then rendered directly after
simulation. The paper frames this as "what you see is what you simulate."

For this project, that means the terrain splats should not be converted into a
mesh just to run physics. The local terrain patch should become the simulated
particle set, then the deformed particle state should update the renderable
Gaussian map.

## Relevant Pipeline

The local implementation entrypoint is `../../PhysGaussian/gs_simulation.py`.
Its useful stages are:

- load a Gaussian checkpoint from `point_cloud/iteration_*/point_cloud.ply`,
- compute positions, covariance, opacity, and spherical harmonics,
- filter low-opacity Gaussians,
- rotate, crop, scale, and center the selected simulation area,
- optionally fill particles inside the selected region,
- initialize the Warp MPM solver,
- apply configured boundary conditions,
- advance MPM with `p2g2p`,
- render simulated particles by exporting updated positions, covariance, and
  rotations.

## Config Surface To Reuse

The JSON configs under `../../PhysGaussian/config/` already support the major
knobs needed for early terrain tests:

- material parameters: `material`, `E`, `nu`, `density`, `g`,
  `friction_angle`, damping-related values, and other material-specific fields,
- preprocessing: `opacity_threshold`, `rotation_degree`, `rotation_axis`,
  `sim_area`, `scale`,
- particle filling: `particle_filling`,
- timing: `substep_dt`, `frame_dt`, `frame_num`,
- boundary conditions,
- camera and render view settings.

`../../PhysGaussian/config/wolf_config.json` is the closest existing sand-like
reference because it uses `material: "sand"` with a `friction_angle`.

## Existing Boundary Conditions

`../../PhysGaussian/utils/decode_param.py` currently decodes these boundary
condition types:

- `cuboid`,
- `particle_impulse`,
- `bounding_box`,
- `enforce_particle_translation`,
- `surface_collider`,
- `release_particles_sequentially`,
- `enforce_particle_velocity_rotation`.

A localized circular pressure query is not already a first-class CLI feature.
Early terrain work should either approximate it with existing particle velocity
or impulse modifiers, or add a small query wrapper later that maps radius,
location, duration, and displacement into the supported MPM controls.

## Gaussian Update Rule

The paper's key rendering update is:

```text
x_p(t) = phi(X_p, t)
Sigma_p(t) = F_p(t) Sigma_p(0) F_p(t)^T
```

For this project:

- start with center-only updates for stability and debugging,
- add covariance updates after center displacement renders cleanly,
- keep opacity and appearance coefficients unchanged at first,
- only revisit appearance changes after the geometry pipeline is stable.

## Terrain-Specific Gap

PhysGaussian was designed for general dynamic objects. Terrain contact needs
extra constraints:

- local patch extraction around a query point,
- shallow subsurface support below a surface-like splat map,
- sand-first material parameters,
- explicit pressure/displacement query semantics,
- metrics such as indentation depth, displaced volume proxy, and deformation
  radius.

## Current Compatibility Notes

The local `tsplat` environment uses a newer Warp API than the checked-in
PhysGaussian code expected. The prototype currently handles this with local
compatibility shims in `scripts/run_ground_plane_solver.py` plus one local
PhysGaussian API update:

- `warp.torch` is shimmed to the top-level `warp` module.
- `warp.types.float32` and `warp.types.array` are shimmed for older helper
  signatures.
- PhysGaussian tensor alias helpers are overridden to use `wp.from_torch`.
- `wp.mat33(vector rows)` in the MPM interpolation code was updated to
  `wp.matrix_from_rows(...)` for Warp 1.14 compatibility.

CUDA visibility depends on how commands are launched. Inside the managed
sandbox, `nvidia-smi`, PyTorch, and Warp cannot see the NVIDIA driver. Outside
the sandbox, the host sees an RTX 3060 Ti and PyTorch reports CUDA available.

## Current Solver Status

The ground-plane smoke test now initializes particles from the aligned EDGS
iteration-7000 splats and adds a sticky `surface_collider` at the extracted
ground plane height.

Observed status:

- Tiny CPU MPM smoke tests can initialize and write a few frames.
- Those tiny frames are effectively stationary because only a couple of tiny
  substeps are advanced.
- Longer CPU MPM runs segfault in Warp.
- CUDA runs initialize, compile, and write the first few frames, then fail in
  `p2g_apic_with_stress` with `CUDA error 700: illegal memory access`.

The current working hypothesis is numerical/scene setup instability, not missing
CUDA. Next solver work should soften the sand parameters, reduce timestep, keep
particle/grid counts small, and verify all particles stay inside the valid MPM
grid stencil before adding contact forces.

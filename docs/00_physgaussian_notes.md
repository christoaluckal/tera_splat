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


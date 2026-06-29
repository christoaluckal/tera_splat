# Phase 4: Surface Pressure MPM Patch

## Goal

Replace analytic deformation with a local MPM simulation while avoiding deep
rigid-body contact.

## Inputs

- Local terrain patch from Phase 2.
- Sand material parameters.
- Contact radius, duration, and either target displacement or pressure.
- Boundary conditions for floor/support and simulation bounds.

## Method

Start with displacement control, because it is easier to stabilize than raw
force control:

```text
surface particles inside contact radius receive downward target velocity
for N substeps
```

Then test pressure/impulse control:

```text
f_i = f_0 * exp(-||xy_i - xy_query||^2 / (2 r_contact^2)) * (-normal)
```

Keep the first MPM patch small and local. The point is to produce a stable,
inspectable shallow dent, not to solve full wheel or foot contact.

Before any contact loading, run a gravity-only ground-plane smoke test:

```text
1. align the extracted sand plane to +Z,
2. normalize particles into the PhysGaussian grid domain,
3. add a sticky surface collider at the extracted ground height,
4. advance a small number of MPM steps,
5. verify nonzero but bounded particle motion.
```

## PhysGaussian Reuse

Reuse the Warp MPM solver concepts from PhysGaussian:

- initialize particles from selected Gaussian centers or filled terrain volume,
- set material to `sand`,
- use `E`, `nu`, `density`, `friction_angle`, damping, `n_grid`, and timestep
  config fields,
- use existing boundary conditions where possible.

Existing controls such as `enforce_particle_translation` or `particle_impulse`
can approximate early displacement/force tests. A true circular query wrapper is
a later implementation task, because the current CLI does not expose
`query_xyz + radius + depth` directly.

Current local implementation notes:

- `scripts/run_ground_plane_solver.py` creates the first ground-plane MPM setup.
- `scripts/view_solver_animation.py` displays solver PLY output folders.
- `scripts/generate_ground_plane_preview.py` is only a non-MPM viewer/debug
  fallback; do not treat it as a physics result.

## Deliverables

- Local particles before/after simulation.
- Deformation field.
- Updated Gaussian centers from particle displacement.
- Before/after render.
- MPM run config and metrics.

## Success Criteria

- Simulation remains numerically stable.
- Deformation is local to the contact patch and nearby terrain.
- Particle displacement can be transferred back to splats.
- The MPM result differs meaningfully from the analytic baseline.

## Risks / Open Questions

- Surface-only particles can collapse or move unrealistically.
- Force control may require careful timestep and stiffness tuning.
- Patch boundary conditions can dominate the result if the patch is too small.
- Current real MPM runs are not yet stable beyond tiny smoke tests. CPU runs can
  segfault for longer simulations, while CUDA runs currently fail in
  `p2g_apic_with_stress` with `CUDA error 700`.
- Current sand stiffness copied from the existing PhysGaussian config
  (`E = 5e7`) is likely too aggressive for the normalized EDGS scene. Test much
  softer values first, e.g. the `run_sand.py` scale, before restoring stiffness.

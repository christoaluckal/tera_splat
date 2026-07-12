# Phase 4: Coupled Rigid MPM Contact

## Goal

Replace analytic deformation with a local MPM simulation using Genesis'
physically coupled rigid-MPM contact path. This is the accepted mechanism going
forward for any entity that should exert on the sand bed.

## Inputs

- Local terrain patch from Phase 2.
- Sand material parameters.
- Rigid contact entity shape, duration, and either commanded motion or load.
- Boundary conditions for floor/support and simulation bounds.

## Method

Use the same mechanism as Genesis' `examples/coupling/sand_wheel.py`:

```python
scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=..., substeps=10, gravity=(0, 0, -9.81)),
    coupler_options=gs.options.LegacyCouplerOptions(rigid_mpm=True),
    mpm_options=gs.options.MPMOptions(...),
)

scene.add_entity(
    gs.morphs.Cylinder(...),
    material=gs.materials.Rigid(
        needs_coup=True,
        coup_friction=...,
        coup_softness=0.0,
        coup_restitution=0.0,
    ),
)

sand = scene.add_entity(..., material=gs.materials.MPM.Sand(...))
```

Start with a displacement- or velocity-controlled rigid cylinder because it is
easier to inspect than raw force control. The cylinder itself must be a coupled
rigid entity; do not directly move particles for final physical results.

Debug-only alternatives:

```text
- analytic pressure patches,
- direct surface particle velocity edits,
- debug clamp/plastic particle edits,
- Genesis Tool-mode tests.
```

These may help isolate rendering or measurement issues, but they are not
physical evidence. Final runs should use coupled rigid MPM contact and
`--debug-contact-mode none`.

Keep the first MPM contact case small and local. The point is to produce a
stable, inspectable shallow dent, not to solve full wheel or foot contact.

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
can approximate early debugging tests, but they should not be used as final
physical contact results. The current physical query wrapper is
`scripts/run_genesis_indenter_test.py` with `--indenter-body-mode rigid` and
`--debug-contact-mode none`.

Current local implementation notes:

- `scripts/run_ground_plane_solver.py` creates the first ground-plane MPM setup.
- `scripts/run_genesis_indenter_test.py` runs the accepted coupled-rigid
  cylinder contact test.
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

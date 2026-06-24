# Phase 5: Subsurface Support

## Goal

Avoid simulating terrain as a hollow visual surface by adding shallow particles
below the visible sand layer.

## Inputs

- Local surface patch and normal from Phase 2.
- Scene scale.
- Desired support depth.
- Particle spacing and layer count.

## Method

For each selected surface point or resampled surface point, create a short
column of particles below the terrain:

```text
for each surface point p:
    for k in 1..K:
        particle = p - k * dz * normal
```

Start with 4-10 layers and 5-15 cm depth in real-world scale. Use denser
particles near the surface and coarser particles deeper down only after the
uniform version is stable.

## PhysGaussian Reuse

PhysGaussian includes optional particle filling based on reconstructed density
and ray tests. That is useful for closed objects, but terrain is usually an open
surface. The terrain prototype should document a terrain-specific shallow-column
filling method as the first version, while keeping PhysGaussian filling as a
reference for inheriting visual attributes and particle volumes.

Filled subsurface particles should participate in simulation. They do not need
to render in the first version unless exposed by deformation.

## Deliverables

- Surface plus subsurface particle visualization.
- Local terrain volume export.
- MPM run with and without subsurface support.
- Comparison metrics for surface-only versus supported terrain.

## Success Criteria

- Particles do not collapse immediately.
- Downward displacement produces compaction and some lateral motion.
- Results look more plausible than surface-only MPM.
- The support depth and layer count are recorded with each run.

## Risks / Open Questions

- Too few layers behave like a shell; too many layers increase runtime.
- Incorrect normals can place support particles above or beside the terrain.
- Subsurface particles need material parameters even if they are not rendered.


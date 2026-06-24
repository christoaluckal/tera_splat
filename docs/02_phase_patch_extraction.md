# Phase 2: Terrain Patch Extraction

## Goal

Given query location `X`, select only the local splats and derived particles
needed for a shallow deformation query.

## Inputs

- Loaded terrain Gaussian attributes from Phase 1.
- Query point `query_xyz` in scene/world coordinates.
- Patch radius `R_patch`.
- Contact radius `r_contact`.

## Method

Select Gaussian centers inside a local radius:

```text
local_ids = ||xyz_i - query_xyz|| < R_patch
```

Estimate a local ground normal from the selected centers, then define a local
frame centered at the query point. The first version should assume nearly flat
terrain and use a stable vertical axis if the normal estimate is noisy.

The selected patch must include enough margin beyond the contact radius to show
pile-up and lateral motion. A practical first default is:

```text
R_patch = 3x to 5x r_contact
```

## PhysGaussian Reuse

PhysGaussian already supports selecting a cuboid `sim_area` during preprocessing.
For terrain queries, the docs should treat that as a coarse scene crop, while the
query wrapper should eventually provide a more natural radius-based local patch.

The selected patch will be transformed into the normalized MPM coordinate space
used by PhysGaussian only after extraction and inspection are correct in world
space.

## Deliverables

- Local patch point/splat visualization.
- Local coordinate frame definition.
- Patch metadata: query point, radius, normal, scale, selected count.
- Local patch export for debugging.

## Success Criteria

- Selected splats contain the contact area plus surrounding deformation margin.
- The local patch can be visualized independently.
- The local normal is stable enough to define "downward."
- The patch has no obvious holes directly under the contact area.

## Risks / Open Questions

- A radius-only crop may include background splats if the scene is cluttered.
- Sparse patches may need densification or subsurface filling before MPM.
- Strong slopes should be deferred until flat terrain succeeds.


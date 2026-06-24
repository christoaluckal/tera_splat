# Phase 8: Query Interface

## Goal

Define a clean interface for counterfactual terrain deformation queries.

## Inputs

- Terrain Gaussian scene.
- Query location.
- Material label.
- Contact radius.
- Mode: displacement first, pressure later.
- Magnitude, duration, and simulation steps.

## Method

The desired CLI shape is:

```bash
python query_terrain.py \
  --scene terrain_initial.ply \
  --query_xyz 0.2 0.1 0.0 \
  --material sand \
  --radius 0.05 \
  --mode displacement \
  --depth 0.01 \
  --steps 100 \
  --out outputs/query_001
```

The matching Python API should expose the same concepts:

```python
result = terrain_model.query(
    location=x,
    material="sand",
    contact_radius=0.05,
    mode="displacement",
    displacement=0.01,
    steps=100,
)
```

## PhysGaussian Reuse

The query layer should eventually generate the PhysGaussian-compatible MPM
config and boundary controls underneath. It should not expose PhysGaussian's
whole config file to users for the common shallow-contact case.

Because PhysGaussian does not currently expose a circular terrain query as a
single command, this phase should be treated as a wrapper design, not a direct
reuse of the existing `gs_simulation.py` CLI.

## Deliverables

Expected output folder:

```text
outputs/query_001/
  before.png
  after.png
  before_depth.png
  after_depth.png
  terrain_deformed.ply
  metrics.json
  config.yaml
```

Also include optional debug outputs:

```text
patch_initial.ply
patch_deformed.ply
particles_initial.ply
particles_deformed.ply
```

## Success Criteria

- One query specification can run the whole pipeline.
- Outputs are reproducible from the saved config.
- The interface supports the analytic baseline and MPM path with the same query
  fields.
- Failure modes are explicit: invalid query point, too few splats, unstable
  simulation, or render failure.

## Risks / Open Questions

- Query coordinates are easy to confuse across world, local, and MPM spaces.
- A general API may hide necessary debug controls too early.
- Pressure units should be deferred until displacement mode is stable.


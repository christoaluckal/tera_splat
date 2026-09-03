# Legacy Settled Mid-Stiff Base State

This is a retained 12.5 mm-particle prototype asset. It is not the active
calibration bed and must not seed the current 5 mm/n128 workflow. See
[`docs/current-state.md`](../../docs/current-state.md) for the authoritative
prepared state and experiment contract.

It starts from the settled final frame of:

```text
outputs/base_clearance025_substeps10_coupled_layers16_depth0p2_ps0p0125/layers16_depth0p2_ps0p0125/simulation_ply/sim_4000.ply
```

and uses:

```text
config: configs/physgaussian_sand_stiff_mid.json
E: 100000
nu: 0.2
density/rho: 1000
friction_angle: 45
particle_size: 0.0125
substeps: 10
ground coupling: friction 0.2, softness 0.0, restitution 0.0
```

`particles_initial_mpm.ply` plus `ground_plane_metadata.json` reproduce this
historical prototype only.

Reference output:

```text
solver_animation.mp4
run_metrics.csv
```

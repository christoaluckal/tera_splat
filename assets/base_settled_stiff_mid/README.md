# Settled Mid-Stiff Base State

This is the active base state for the Genesis sand prototype.

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

Use `particles_initial_mpm.ply` plus `ground_plane_metadata.json` as the
starting state for the next base simulation.

Reference output:

```text
solver_animation.mp4
run_metrics.csv
```

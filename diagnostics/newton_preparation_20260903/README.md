# Newton Preparation Integration

Run date: 2026-09-03.

The Newton backend now consumes the original Chrono-derived 5 mm metric bed,
creates a fresh Newton constitutive state, applies static ground and four-wall
containment, and exports backend-labelled state, PLY, height-map, mask, CSV,
and manifest artifacts. It does not load the Genesis state archive.

Environment: Python 3.11.15, Newton 1.5.1, Warp 1.17.0, CUDA device 0.
The configuration is an uncalibrated engineering starting point with an
explicit Newton friction coefficient of 0.68.

## Full-bed 2 s result

- 307,461 particles, 5 mm spacing, 38.432625 kg represented mass;
- 15.625 mm sparse MPM voxels, APIC transfer, P0 strain basis;
- 0.5 ms timestep, 4,000 steps, 54.845 s solver wall time;
- full 14,161-cell target support;
- first accepted p99 hold at 1.6165 s;
- final p50/p95/p99: 0.031/0.129/0.168 mm/s;
- settled H0 RMSE/max: 1.186/1.288 mm;
- finite complete Newton state and accepted preparation gate.

The accepted large artifacts are under:

    /data/christoa/Chrono/tera_splat/outputs/validity_experiment/newton/A0_oracle_guided_offset_5mm_gate6mm_full_2s

This qualifies one Newton preparation setting only. It does not establish
timestep or solver-tolerance convergence, rigid-cylinder coupling, removal
behavior, response agreement, or calibration.

Later restart diagnosis found that the exported particle arrays do not include
the solver grid/warm-start history: reconstructing from them added about
1.157 mm of bulk settlement. They remain valid archival/raw output, but are not
restart-qualified checkpoints. See
`diagnostics/newton_convergence_coupling_20260906/` for the preparation matrix
and continuous-state cylinder result.

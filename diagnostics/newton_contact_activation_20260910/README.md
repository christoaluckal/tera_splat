# Newton full-volume contact-activation diagnosis

## Result

The full analytic cylinder now has a mechanics-qualified three-timestep
response matrix without a collision-bottom inset.  This does **not** yet
qualify the Newton forward model for calibration: the predeclared full matrix
is `not_demonstrated` because coarse-to-medium loaded sinkage differs by
`0.975 mm`, exceeding the unchanged `0.5 mm` gate.  Medium-to-fine passes all
map and sinkage gates (`0.480 mm` sinkage difference).

## Controlled mechanism

Newton 1.5.1's native S2 collider rasterizer activates contact grid nodes
`0.25` voxel outside a zero-SDF boundary.  The diagnostic installs a
process-local, cylinder-only adapter that changes this activation distance to
`-0.25` voxel.  It preserves the analytic cylinder dimensions, action pose,
mass/inertia, signed-distance geometry, zero collision-bottom inset, strict
particle-center penetration check, and the stock containment colliders.  It
does not change the external Chrono I/O, loss, mask, or acceptance gates.

The adapter uses Newton private APIs and is explicitly version-locked to
Newton 1.5.1.  It is diagnostic code, not a general solver patch or a
production promotion.

`-0.95` voxel was rejected in the full run: the cylinder fell `116.5 mm`,
reached `13.423 mm` center penetration, and failed the guide gate.  The
selected `-0.25` value was therefore tested through the unchanged complete
continuous preparation, `3.595 s` loading, and `0.25 s` residual protocol.

## Full-volume `-0.25` voxel matrix

| timestep | mechanics | center penetration | loaded bottom above initial surface | first significant contact gap |
| --- | --- | ---: | ---: | ---: |
| `0.5 ms` | pass | `0` | `0.735 mm` | `4.036 mm` |
| `0.25 ms` | pass | `0` | `1.710 mm` | `4.328 mm` |
| `0.125 ms` | pass | `0` | `2.190 mm` | `4.335 mm` |

All rows retain accepted PIC preparation, finite 14,161-cell output, and the
`1e-6` guide gate.  Adjacent loaded/residual response-map RMSE and maximum
error pass in both pairs.  Only coarse-to-medium sinkage fails:

| pair | loaded/residual RMSE | loaded/residual maximum | sinkage difference | matrix result |
| --- | ---: | ---: | ---: | --- |
| `0.5 -> 0.25 ms` | `0.149 / 0.130 mm` | `0.911 / 0.752 mm` | `0.975 mm` | fail (sinkage only) |
| `0.25 -> 0.125 ms` | `0.122 / 0.124 mm` | `0.781 / 0.730 mm` | `0.480 mm` | pass |

Chrono loaded/residual RMSE (`3.588--3.961 mm`) is reported only as
uncalibrated material-fit evidence and is not a convergence gate.  No material
calibration or large evaluation follows from this diagnostic.

## Evidence and reproduction

- `convergence/summary.json`, `cases.csv`, and `pairwise.csv` are the tracked
  lightweight matrix report.
- Raw arrays, maps, traces, PLYs, and manifests remain under
  `outputs/validity_experiment/newton/contact_activation_20260910/`.
- The runner is `scripts/run_newton_cylinder_diagnostic.py`; the version-locked
  adapter is `scripts/newton_collider_activation.py`; run
  `scripts/analyze_newton_response_convergence.py` on the three raw case paths
  to regenerate the compact report.

The next Newton action is to diagnose the remaining coarse-to-medium sinkage
sensitivity under the unchanged contract.  Do not relax the gate or begin
material calibration from this result.

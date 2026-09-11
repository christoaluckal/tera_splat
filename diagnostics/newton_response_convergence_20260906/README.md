# Newton Response Timestep Convergence

Run date: 2026-09-06. Forward-model source commit:
`73eb472028ef8492cf50c455273ed0088c81d4cc`. The analyzer verified that the
configuration and all forward-model files matched that commit.

This is the predeclared full-response matrix at `0.5`, `0.25`, and `0.125 ms`.
Each case performs fresh 2 s PIC preparation, the unchanged 3.595 s guided
1.5 kg cylinder load, instantaneous removal, and the 0.25 s residual phase in
one solver instance. Material, tolerance, geometry, contact construction,
action, projection, and valid mask are fixed.

## Result

The matrix is complete and every case is individually mechanics-qualified:
finite output, all 14,161 valid cells, accepted preparation, and zero analytic
particle-center penetration. Response convergence is nevertheless
`not_demonstrated`.

| timestep | loaded sinkage | loaded Chrono RMSE | residual Chrono RMSE |
| ---: | ---: | ---: | ---: |
| `0.5 ms` | `8.854 mm` | `2.396 mm` | `2.646 mm` |
| `0.25 ms` | `-0.578 mm` | `3.672 mm` | `3.949 mm` |
| `0.125 ms` | `-5.607 mm` | `3.759 mm` | `4.021 mm` |

The sign convention makes negative sinkage a cylinder bottom that remains
above the initial surface.

| adjacent pair | loaded response RMSE / max | residual response RMSE / max | sinkage difference | result |
| --- | ---: | ---: | ---: | ---: |
| `0.5 -> 0.25 ms` | `1.349 / 7.303 mm` | `1.373 / 7.347 mm` | `9.432 mm` | failed |
| `0.25 -> 0.125 ms` | `0.105 / 0.919 mm` | `0.084 / 0.677 mm` | `5.029 mm` | failed on sinkage |

The predeclared adjacent limits are `0.5 mm` map RMSE, `1.0 mm` maximum map
error, and `0.5 mm` loaded sinkage difference. Chrono RMSE is reported but does
not determine numerical acceptance.

## Diagnosis

The steady sampled upward impulses are proportional to timestep and yield
approximately `14.715 N` after division by `dt`, correctly balancing the
cylinder weight. However, loaded endpoint velocity is approximately `-g*dt`:
`-4.940`, `-2.486`, and `-1.259 mm/s`. The current forward-consistent guide
advances position with the pre-impulse velocity, so this one-step gravity lag
accumulates a first-order displacement near `g*T*dt`.

For adjacent levels, `g*T*delta_dt` predicts `8.817` and `4.409 mm` over the
3.595 s load, close to the measured sinkage differences of `9.432` and
`5.029 mm`; the remaining roughly `0.62 mm` is concentrated in the initial
impact transient. This identifies the explicit one-DOF guide update as the
dominant response-convergence blocker. The PIC preparation and external map
I/O remain qualified.

Large raw states, PLYs, heightmaps, masks, traces, and manifests are retained
at:

    /data/christoa/Chrono/tera_splat/outputs/validity_experiment/newton/response_convergence_73eb472_20260906

The next controlled change is a timestep-consistent guided-body update, tested
with the same collider guard and unchanged response matrix. Do not calibrate
the material or relax the gates before rerunning that matrix.

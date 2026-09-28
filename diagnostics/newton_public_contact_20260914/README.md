# Newton public contact and spatial-resolution diagnosis

This bundle supersedes the private S2 activation adapter as the active Newton
forward-model direction.  It uses stock Newton contact only; all changes below
are explicit solver/experiment settings.

At the original `15.625 mm` voxel size, stock contact with four proxy
iterations and eight rigid substeps is mechanics-qualified at `0.5` and
`0.25 ms`.  The pair passes map and sinkage gates (`0.053/0.053 mm` map RMSE,
`0.192 mm` sinkage difference), but the analytic cylinder bottom remains
`10.632/10.823 mm` above the initial surface.  It is timestep-consistent but
has an unacceptable contact-location bias for calibration.

Halving only the public voxel size to `7.8125 mm` yields an independently
passed PIC preparation matrix at `0.5/0.25/0.125 ms` and `0.25 ms` tolerance
refinement. The stock-contact `4/8` cylinder pair remains mechanics-qualified
and cuts the loaded bottom bias to `2.195/3.535 mm`. Its map pair passes
(`0.096/0.081 mm` RMSE; maxima below `0.583 mm`), but sinkage differs by
`1.339 mm`, failing the unchanged `0.5 mm` gate. It remains a rejected public
coupling setting.

## Qualified public fixed domain: refined grid, `8/16`

Increasing only public coupling effort to eight proxy iterations and sixteen
rigid substeps produces a complete three-level stock-contact response matrix.
No internal Newton contact/rasterizer computation or activation override is
used.

| Pair | loaded / residual RMSE | loaded / residual maximum | sinkage difference | result |
| --- | ---: | ---: | ---: | --- |
| `0.5 -> 0.25 ms` | `0.035 / 0.035 mm` | `0.218 / 0.213 mm` | `0.331 mm` | pass |
| `0.25 -> 0.125 ms` | `0.058 / 0.054 mm` | `0.304 / 0.310 mm` | `0.422 mm` | pass |

All three cases retain accepted preparation, finite `14,161`-cell I/O, guide
constraint, and strict zero analytic particle-center penetration. The
predeclared limits are `0.5 mm` RMSE, `1.0 mm` maximum error, and `0.5 mm`
sinkage difference. The analysis status is `passed`.

This qualifies a *numerical domain*, not a calibrated material: use the
`7.8125 mm` configuration, PIC/P0/S2/Q1, stock contact, `8/16` coupling, and
one fixed validated timestep per separate sim-only Newton study. The 100 kPa
smoke material remains uncalibrated; all-cell Chrono response RMSE is
`3.822--3.905 mm`, and significant contact starts `5.701--5.959 mm` above the
initial surface. Do not use the result to claim real-material prediction or
transfer across untested solver settings.

Raw preparation output remains under
`outputs/validity_experiment/newton/public_spatial_contact_20260913/`; raw
response output and the machine-readable convergence summary are under
`outputs/validity_experiment/newton/public_spatial_contact_20260914/voxel7p8125mm/stock_contact_8x16/`.


## Downstream local BayesOpt initialization

The qualified domain now has a 19-valid-observation local material study at
`0.25 ms` and `8/16`. Across 21 candidate evaluations, the two candidates near
`mu=0.273` were rejected by the strict zero particle-center penetration gate;
they are not observations. The best valid point is `E=70.46 kPa`,
`nu=0.237231507`, `mu=0.305497980`, with discovery objective `8.823 mm` versus
baseline `12.698 mm`. A fresh independent replay scored `8.815 mm`, only
`0.008 mm` different. This is repeatable local numerical evidence only; it is
not optimizer convergence, real-sand calibration, held-out action transfer, or
NVS validation. Raw study evidence is under
`outputs/validity_experiment/newton_bayesopt/`.

Raw manifests, maps, arrays, traces, and PLYs remain under
`outputs/validity_experiment/newton/public_coupling_ab_20260912/` and
`outputs/validity_experiment/newton/public_spatial_contact_20260913/`.

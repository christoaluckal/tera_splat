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
refinement.  The stock-contact cylinder remains mechanics-qualified and cuts
the loaded bottom bias to `2.195/3.535 mm`.  Its map pair still passes
(`0.096/0.081 mm` RMSE; maxima below `0.583 mm`), but sinkage differs by
`1.339 mm`, failing the unchanged `0.5 mm` gate.  Do not run its fine response
level or start Newton BayesOpt at this setting.

The next predeclared public-only test is `8` proxy iterations and `16` rigid
substeps at the `7.8125 mm` grid, first at `0.5/0.25 ms`.  Internal Newton
rasterization changes and private activation overrides are diagnostic only and
are not forward-model candidates.

Raw manifests, maps, arrays, traces, and PLYs remain under
`outputs/validity_experiment/newton/public_coupling_ab_20260912/` and
`outputs/validity_experiment/newton/public_spatial_contact_20260913/`.

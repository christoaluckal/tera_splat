# Newton native-proxy response convergence

The corrected forward model replaces the external explicit cylinder update
with Newton 1.5.1 `SolverCoupledProxy`: a Kamino rigid cylinder constrained by
a world-anchored vertical prismatic joint, coupled to the unchanged implicit
MPM solve using two lagged proxy iterations and four rigid substeps.

The complete `0.5/0.25/0.125 ms` matrix keeps preparation, PIC material,
collider, projection threshold, action, timing, surface projection, and frozen
gates unchanged. All cases are mechanics-qualified, finite, cover all `14,161`
cells, pass strict zero particle-center penetration, and pass the explicit
`1e-6` guide-constraint gate.

The native path removes the dominant explicit-integration drift: endpoint
vertical speeds are `-0.0019/-0.0024/-0.0096 mm/s`, rather than approximately
`-g*dt`. Both adjacent loaded/residual response-map pairs pass, with RMSE
`0.088/0.089 mm` and `0.082/0.082 mm`; maximum errors are below `0.745 mm`.

Full response convergence is nevertheless `not_demonstrated`. The coarse pair
passes the `0.5 mm` loaded-sinkage gate at `0.464 mm`, while the fine pair is
`0.586819 mm`, exceeding it by `0.086819 mm`. The corrected equilibrium also
exposes an approximately `9.8--10.8 mm` analytic surface gap, consistent with
the broad MPM collider support rather than physical cylinder penetration.
Do not loosen the gate or begin calibration. The next controlled diagnosis is
coupling/contact support sensitivity with material and external I/O fixed.

Large states, PLYs, height maps, masks, and traces remain under
`outputs/validity_experiment/newton/response_convergence_native_proxy_20260906/`.
This directory retains only the compact `cases.csv`, `pairwise.csv`, and
`summary.json` report.

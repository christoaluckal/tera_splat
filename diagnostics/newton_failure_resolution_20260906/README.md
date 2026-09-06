# Newton Failure-Mode Resolution

Run date: 2026-09-06.

This bundle records the controlled diagnosis and resolution of the two blockers
reported in `newton_convergence_coupling_20260906`.

## Preparation transfer

The rejected APIC `0.125 ms` state was an upward mode concentrated in the top
six source layers, not a wall-localized instability. Replacing only APIC with
PIC reduced `p99` speed from `1.133 mm/s` after 4 s to `0.00735 mm/s` after 2 s
at the same `0.125 ms` timestep, material, grid, containment, and tolerance.

The full PIC matrix at a common 2 s horizon passes:

- all `0.5`, `0.25`, and `0.125 ms` states pass the unchanged sustained
  `0.5 mm/s` p99 gate;
- adjacent timestep DEM RMSE is `0.0232` and `0.0312 mm`, below the declared
  `0.5 mm` limit;
- maximum adjacent DEM error is at most `0.0416 mm`, below the `1.0 mm` limit;
- `0.25 ms` results at solver tolerances `1e-4` and `1e-5` are identical.

The matrix analyzer status is `passed`. PIC is now the default transfer in the
uncalibrated Newton configuration; this is a numerical qualification, not a
material calibration.

## Cylinder contact

The original `0.508 mm` analytic penetration equals Newton's MPM collider
discretization: a 32-segment cylinder has a `0.352 mm` radial facet inset at
this radius, and Newton's default `0.01 voxel` projection threshold permits an
additional `0.156 mm`.

The qualified collider uses a public-API 128-segment mesh with its facets
circumscribed about the unchanged analytic cylinder, zero cylinder projection
threshold, forward-consistent guided-body position integration, and a declared
`10 um` outward numerical guard. The guard does not alter the analytic action
geometry or penetration scoring. The full `3.595 s` loading trace contains zero
particle centers inside the analytic cylinder.

## Qualified uncalibrated response

The full run is finite with all `14,161` map cells supported and no acceptance
blockers. At the loaded endpoint:

- sinkage below the initial surface: `8.854 mm`;
- cylinder vertical speed: `-4.940 mm/s`;
- particle p99 speed: `0.0551 mm/s`;
- zero interior particle centers and zero measured center penetration.

After `0.25 s` removal response, particle p99 speed is `0.231 mm/s`. The raw
all-cell Chrono error is `2.396 mm` loaded and `2.646 mm` residual. These values
are useful initial comparisons, but the engineering material remains
uncalibrated and is not a validated predictive model.

Large evidence:

    /data/christoa/Chrono/tera_splat/outputs/validity_experiment/newton/preparation_pic_convergence_20260906
    /data/christoa/Chrono/tera_splat/outputs/validity_experiment/newton/failure_mode_diagnosis_20260906
    /data/christoa/Chrono/tera_splat/outputs/validity_experiment/newton/cylinder_qualified_20260906/fixedtime_3p595s_residual0p25s

The next numerical gate is response convergence across timestep. Do that before
material calibration or a larger evaluation sweep. The gate is predeclared as
the unchanged full continuous path at `0.5`, `0.25`, and `0.125 ms`,
comparing loaded-minus-initial and residual-minus-initial DEMs on the common
mask. Every case must keep the existing mechanics gates, and every adjacent
pair must stay within `0.5 mm` map RMSE, `1.0 mm` maximum map error, and
`0.5 mm` loaded sinkage difference. Chrono error is reported separately and
is not used to decide numerical convergence.

# Newton Preparation and Coupling Diagnosis

Run date: 2026-09-06.

This bundle records the first controlled Newton preparation matrix and the
first full fixed-time, vertically guided cylinder loading/removal diagnostic.
All results use Newton 1.5.1, Warp 1.17.0, the original Chrono-derived metric
bed, and the uncalibrated engineering material configuration.

## Preparation matrix

At a common 4 s horizon and rheology tolerance 1e-4:

- 0.5 ms accepts at 1.6165 s and ends at p99 0.0004 mm/s;
- 0.25 ms accepts at 3.082 s and ends at p99 0.0623 mm/s;
- 0.125 ms does not accept and ends at p99 1.1334 mm/s.

The final DEMs are close: adjacent timestep RMSE differences are 0.0408 and
0.0538 mm, both within the predeclared 0.5 mm RMSE / 1.0 mm maximum gates.
Tightening solver tolerance from 1e-4 to 1e-5 at 0.25 ms changes neither the
reported DEM nor speed result. Preparation convergence is nevertheless not
demonstrated because the finest state fails the unchanged sustained-speed gate.

Large matrix evidence:

    /data/christoa/Chrono/tera_splat/outputs/validity_experiment/newton/preparation_convergence_20260906

## Cylinder diagnostic

The response runner prepares the full bed and loads it in one continuous
Newton solver instance. It enforces the Chrono action geometry and timing:
1.5 kg, 73.025 mm radius, 50.8 mm height, center (0, 5 mm), vertical guide,
3.595 s loading, instantaneous body relocation, and 0.25 s residual response.

The run is finite with full 14,161-cell support. At the loaded observation:

- sinkage below the initial surface is 10.109 mm;
- vertical cylinder speed is -4.417 mm/s;
- particle p99 speed is 0.514 mm/s;
- the steady support impulse is approximately 0.00738 N s per 0.5 ms step,
  or 14.76 N, consistent with the 14.715 N cylinder weight;
- 1,302 particle centers are inside the analytic cylinder by at most 0.508 mm,
  so the strict zero-center-penetration gate fails.

The all-valid-cell diagnostic response RMSE is 2.246 mm loaded and 2.583 mm
residual. These are raw uncalibrated comparisons, not an accepted objective.
Residual p99 particle speed at 0.25 s is 11.728 mm/s.

Large coupled evidence:

    /data/christoa/Chrono/tera_splat/outputs/validity_experiment/newton/cylinder_diagnostic_20260906/fixedtime_3p595s_residual0p25s

## I/O qualification

Initial, loaded, and residual arrays, PLYs, DEMs, masks, action, resolved
configuration, trace, and manifest are emitted consistently. Saved Newton
particle arrays are not restart-qualified: rebuilding a solver from them and
holding for 2 s adds 1.157 mm DEM RMSE relative to continuous preparation.
Response runs must therefore prepare in-process until solver grid/warm-start
history is serialized or an equilibrium-preserving reconstruction is proven.

The next admissible work is to diagnose the fine-timestep preparation motion
and the sub-millimetre collider penetration. Do not calibrate from this run.

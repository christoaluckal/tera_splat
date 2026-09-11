# Newton collider-support diagnosis

The native Kamino/implicit-MPM response originally stopped the analytic
cylinder about 9.8--10.8 mm above the prepared surface. Global collider-basis
changes were rejected: Q1 did not settle, and particle-PIC passed speed but
failed H0.

A cylinder-only 9.375 mm bottom inset was then tested as a support-location
diagnostic. It raises the collision proxy while leaving the action cylinder,
mass/inertia, reported pose, DEM projection, and analytic penetration check
unchanged. Kamino PADMM tolerance was tightened from 1e-5 to 1e-6 to match the
existing guide gate.

The resulting 0.5/0.25/0.125 ms matrix passes all preparation, finite-state,
guide, zero-center-penetration, invariant-setting, DEM, and sinkage gates at the
100 kPa smoke material. Adjacent loaded DEM RMSE is 0.130/0.107 mm; adjacent
residual DEM RMSE is 0.123/0.110 mm; sinkage differences are 0.130/0.032 mm.
The 0.5 ms shared A/B objective improves from 12.638 to 12.189 mm. Matched
Genesis remains 14.736 mm and the calibrated Genesis incumbent remains
8.705 mm.

This does not promote the inset as a general collision model. The follow-up
25 kPa calibration diagnostic shows why: once the cylinder sinks into the bed,
particles enter the lower analytic-cylinder slice omitted by the raised proxy.
Material calibration is therefore blocked pending a support correction that
retains full analytic collision coverage.

Tracked files:

- `analyze.py`: recomputes the corrected A/B summary and plots;
- `convergence/`: tracked three-level cases, pairwise metrics, and passed
  convergence summary;
- `summary.json`, `cases.csv`, `response_maps.png`, and
  `error_maps.png`: lightweight corrected A/B evidence;
- `newton_sand_q1.json` and `newton_sand_pic_collider.json`: rejected
  global collider-basis controls.

Large states, PLYs, maps, and traces remain under
`outputs/validity_experiment/newton/collider_support_*`.

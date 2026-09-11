# Corrected-Newton stiffness screen

This is the smallest Newton-specific calibration probe after the 100 kPa
support-correction matrix passed. Only Young's modulus changed, from 100 to
25 kPa; every other material, solver, action, collision, projection, and score
setting remained frozen.

The 25 kPa preparation is valid and timestep-consistent. All four preparation
cells pass speed and H0 gates. Adjacent H0 DEM RMSE is 0.179/0.148 mm and the
0.25 ms tolerance comparison is 0.000071 mm.

The 0.5 ms response is rejected. It contains as many as 1,330 particle centers
inside the analytic cylinder, with 5.950 mm maximum penetration, and also
misses the guide gate. Its DEM-only objective would improve from 12.189 to
11.207 mm, demonstrating that unconstrained calibration would optimize into
invalid geometry.

Conclusion: stop the material sweep. The raised collision proxy is useful for
diagnosing the S2 support offset at the stiff smoke point, but it leaves an
uncollided slice inside the analytic cylinder. The next change must correct
support location while preserving full analytic collision coverage.

Tracked files:

- `newton_sand_e25k.json`: stiffness-only candidate;
- `analyze.py`: reproducible scorer/plot generator;
- `summary.json`, `cases.csv`, `response_maps.png`, and
  `error_maps.png`: lightweight diagnostic evidence.

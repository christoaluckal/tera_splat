# A7 geometry-transfer holdout

A7 uses the same 1.625 kg guided action and center as A4, but reduces the
cylinder radius from 73.025 mm to 55 mm. Chrono accepted `converged_speed_hold`
at 0.456 s, with 24.386021 mm loaded sinkage. Support and initial terrain are
identical to A4; all Chrono maps are finite.

The frozen incumbent is **invalid** under the unchanged strict Newton gate:
four sampled particle centers entered the analytic cylinder, with maximum
center penetration 1.406 µm. Guide compliance passed, but the run receives no
objective and is not an optimizer observation.

The unchanged 100 kPa control is valid:

- objective: 2.643076 mm
- loaded RMSE: 0.574235 mm
- residual-footprint RMSE: 4.137683 mm
- zero center penetration and guide gate passed

This is a geometry-specific mechanics boundary for the frozen incumbent, not
evidence that the smaller-radius Chrono oracle is invalid.

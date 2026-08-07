# Mass-Controlled Calibration Analysis Context

Date: 2026-08-06

This bundle is a handoff for analysis of the `real3` mass-controlled sand
experiment. It is not evidence of a calibrated material fit and must not be
used to start the real `log10_E` / `phi_deg` sweep.

## Experiment Contract

- The observed action is gravitational placement of a rigid cylinder, not a
  prescribed-depth indentation.
- Cylinder: diameter `0.14605 m`, radius `0.073025 m`, height `0.0508 m`,
  mass `1.5 kg`.
- Initial center: `[0.0, 0.0]` in the bed/world XY frame. Center offsets in
  the `+-0.1 m` grid are a separate protocol-sensitivity study.
- The cylinder is placed at 99th-percentile first contact, released at zero
  velocity, then lifted at `5 mm/s` after loaded settling.
- Real target: static-border corrected residual DEM,
  `data/single_trial_real3/processed/delta_h_real_corrected.npz`.

## Validated Bridge Results

- Dynamic cylinder free fall reproduces gravity with the intended `1.5 kg`
  mass and uniform-cylinder inertia.
- Short `0.04 s` terrain smoke shows sinkage rises with `0.75`, `1.5`, and
  `3.0 kg`; this is not an equilibrium test.
- CUDA mass-controlled runs complete an uncapped lift and detect post-removal
  settling. The 1.5 kg cylinder reaches about `2.90 mm` penetration.
- The 1.5 kg penetration is stable over the final `0.1 s` at stored float32
  precision, but local p99 particle speed remains `0.670-0.720 mm/s`, above
  the current `0.5 mm/s` stop threshold. Local p95 is `0.188-0.205 mm/s`.

## Interpretation And Open Gates

The existing p99 criterion does not establish loaded equilibrium. P95 is only
a candidate sensitivity statistic until the same window, threshold, and
required-duration checks are run for all three masses. The real sweep remains
blocked by that validation, two-view scan noise, footprint/static-border review,
exact simulated-to-RealSense projection, deterministic MPM-state reconstruction,
no-cylinder drift, and synthetic recovery.

The detailed evidence and commands are in `docs/mass_controlled_bridge_findings.md`.

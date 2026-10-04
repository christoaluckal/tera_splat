# Newton 1.75 kg held-out action result — 2026-09-30

## Intent

This is the third frozen rigid-action transfer check for the fixed Newton
material-study domain and the first midpoint probe after the 2 kg failure. It
changes only cylinder mass from the fitted 1.5 kg A0 action to 1.75 kg. The
cylinder geometry, `(0, +5 mm)` location, SCM grid, guide, recovery duration,
and Newton numerical configuration (`7.8125 mm`, `0.25 ms`, stock contact,
`8/16`) remain fixed. Neither tested material setting is retuned.

The accepted Chrono episode is
`tera_splat_sim/validity_experiment/chrono_episodes/A3_oracle_mass1p75kg_guided_offset_5mm_gate6mm_v1`.
It passed `converged_speed_hold` at `1.403 s`, followed by the fixed `0.25 s`
recovery, with `32.860 mm` loaded sinkage. Its initial heightmap and valid mask
agree bitwise with A0 and A2 on all 14,161 valid cells.

## Time-aligned held-out result

| Fixed material setting | Mechanics | Result |
| --- | --- | --- |
| 1.5 kg-selected incumbent: `E=70.46 kPa`, `nu=0.237231507`, `mu=0.305497980` | **Rejected** | Fresh preparation and guide gates pass, but the trajectory-wide strict zero particle-center penetration gate fails (2 sampled centers; `0.041 um` maximum). The loaded endpoint has zero penetration, but the run has no valid objective. |
| unchanged baseline: `E=100 kPa`, `nu=0.2`, `mu=0.68` | **Accepted** | Zero sampled centers penetrate. Objective `11.353 mm` (`3.420 mm` loaded RMSE; `15.866 mm` residual-footprint RMSE). |

The fixed public Newton domain can execute A3, but the A0-selected incumbent
is not mechanically admissible across the complete 1.75 kg trajectory. The
strict result narrows its first observed load-transfer failure to between 1.5
and 1.75 kg. The very small penetration magnitude does not permit relaxing the
predeclared zero-penetration gate after seeing the result.

The rejected incumbent output is not a BayesOpt observation. This remains a
bounded transfer failure of one material point, not a broad failure of Newton,
material calibration, real-sand validation, or NVS/decision-use evidence.

## Next controlled action

Freeze the midpoint action at 1.625 kg with every other setting unchanged.
Generate and accept its Chrono episode first, then evaluate the unchanged
incumbent and 100 kPa control with manifest-derived timing and no retuning.

Raw outputs are under:

- `outputs/validity_experiment/newton_holdout/mass1p75kg_incumbent_timealigned_20260930/`
- `outputs/validity_experiment/newton_holdout/mass1p75kg_baseline_timealigned_20260930/`

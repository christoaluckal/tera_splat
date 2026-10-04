# Newton 2 kg held-out action result — 2026-09-30

## Intent

This is the second frozen rigid-action transfer check for the fixed Newton
material-study domain. It keeps the cylinder geometry, horizontal location
`(0, +5 mm)`, SCM grid, guide, recovery duration, and numerical configuration
(`7.8125 mm`, `0.25 ms`, stock contact, `8/16`) fixed while increasing mass
from the fitted 1.5 kg action to 2.0 kg. The tested material settings are the
unchanged 1.5 kg-selected incumbent and the unchanged 100 kPa smoke baseline;
neither is retuned.

The Chrono episode is
`tera_splat_sim/validity_experiment/chrono_episodes/A2_oracle_mass2kg_guided_offset_5mm_gate6mm_v1`.
It passed `converged_speed_hold` at `2.188 s`, followed by the fixed `0.25 s`
recovery. Chrono loaded sinkage is `35.804 mm`. Its initial heightmap and valid
mask agree exactly with A0 and A1 on all 14,161 valid cells (zero RMSE and
maximum), so the initial spatial I/O is unchanged.

## Time-aligned held-out result

Both Newton runs derive, record, and assert the A2 manifest timing: `2.188 s`
loaded and `0.25 s` residual.

| Fixed material setting | Mechanics | Result |
| --- | --- | --- |
| 1.5 kg-selected incumbent: `E=70.46 kPa`, `nu=0.237231507`, `mu=0.305497980` | **Rejected** | Fresh preparation and guide gates pass, but the trajectory-wide strict zero particle-center penetration gate fails (18 sampled centers; `0.875 um` maximum). The loaded endpoint has zero penetration, but the run has no valid objective. |
| unchanged baseline: `E=100 kPa`, `nu=0.2`, `mu=0.68` | **Accepted** | Zero sampled centers penetrate. Objective `13.211 mm` (`3.994 mm` loaded RMSE; `18.434 mm` residual-footprint RMSE). |

The fixed public Newton domain can therefore execute this 2 kg action, but the
material selected on A0 is not mechanically admissible across the complete A2
trajectory. Together with the aligned 3 kg result, this brackets the selected
incumbent's first observed load-transfer failure between 1.5 and 2.0 kg under
the frozen action family. It does not locate the exact boundary.

The rejected incumbent output is not a BayesOpt observation. This is a bounded
transfer failure of one selected material point, not a broad failure of Newton,
material calibration, real-sand validation, or NVS/decision-use evidence.

## Next controlled action

Freeze the midpoint action at 1.75 kg with every other A2 setting unchanged.
Generate and accept its Chrono episode first, then evaluate the unchanged
incumbent and 100 kPa control with manifest-derived timing and no retuning.
Interpret objective transfer only if both mechanics gates pass.

Raw outputs are under:

- `outputs/validity_experiment/newton_holdout/mass2kg_incumbent_timealigned_20260929/`
- `outputs/validity_experiment/newton_holdout/mass2kg_baseline_timealigned_20260929/`

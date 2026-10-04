# Newton 1.625 kg held-out action result — 2026-10-01

## Intent

This is the fourth frozen rigid-action transfer check for the fixed Newton
material-study domain and the midpoint of the previously bracketed transfer
boundary. It changes only cylinder mass from the fitted 1.5 kg A0 action to
1.625 kg. Geometry, `(0, +5 mm)` location, SCM grid, guide, recovery duration,
and Newton numerical configuration (`7.8125 mm`, `0.25 ms`, stock contact,
`8/16`) remain fixed. Neither material setting is retuned.

The accepted Chrono episode is
`tera_splat_sim/validity_experiment/chrono_episodes/A4_oracle_mass1p625kg_guided_offset_5mm_gate6mm_v1`.
It passed `converged_speed_hold` at `2.231 s`, followed by the fixed `0.25 s`
recovery, with `33.312 mm` loaded sinkage. Its initial heightmap and valid mask
agree bitwise with A0 and A3 on all 14,161 valid cells.

## Time-aligned held-out result

| Fixed material setting | Mechanics | Result |
| --- | --- | --- |
| 1.5 kg-selected incumbent: `E=70.46 kPa`, `nu=0.237231507`, `mu=0.305497980` | **Accepted** | Zero sampled centers penetrate and the guide gate passes. Objective `7.911 mm` (`2.368 mm` loaded RMSE; `11.087 mm` residual-footprint RMSE). |
| unchanged baseline: `E=100 kPa`, `nu=0.2`, `mu=0.68` | **Accepted** | Zero sampled centers penetrate. Objective `11.888 mm` (`3.592 mm` loaded RMSE; `16.591 mm` residual-footprint RMSE). |

This is the first mechanically admissible held-out transfer of the A0-selected
Newton material point. With no retuning, it improves the unchanged control by
`3.977 mm` (`33.5%`) on this A4 action. Together with the strict failures at
1.75 kg, 2 kg, and 3 kg, the selected point's observed mechanics-admissible
load-transfer boundary is narrowed to `1.625–1.75 kg` for this guided action
family. This does not establish the exact threshold or broad generalization.

The result remains sim-only forward-model evidence: it is not real-sand
calibration, optimizer convergence, Genesis material transfer, or NVS/
decision-use validation. Both valid runs are eligible comparisons; neither is
added to the original A0 BayesOpt observations.

Raw outputs are under:

- `outputs/validity_experiment/newton_holdout/mass1p625kg_incumbent_timealigned_20261001/`
- `outputs/validity_experiment/newton_holdout/mass1p625kg_baseline_timealigned_20261001/`

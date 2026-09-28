# Newton 3 kg held-out action result — 2026-09-28

## Intent

This is the first frozen rigid-action transfer check for the fixed Newton
material-study domain. It keeps the cylinder geometry, horizontal location
`(0, +5 mm)`, SCM grid, guide, residual duration, and numerical configuration
(`7.8125 mm`, `0.25 ms`, stock contact, `8/16`) fixed while increasing mass
from 1.5 kg to 3.0 kg. The tested material settings are the 1.5 kg-selected
incumbent and the unchanged 100 kPa smoke baseline; neither is retuned.

The Chrono episode is
`tera_splat_sim/validity_experiment/chrono_episodes/A1_oracle_mass3kg_guided_offset_5mm_gate6mm_v1`.
It passed `converged_speed_hold` at `2.417 s`. Its initial heightmap agrees
exactly with A0 on all 14,161 common valid cells (zero RMSE and maximum), so
the initial spatial I/O is unchanged.

## Corrected timing contract

The first diagnostic found that the runner used A0's old `3.595 s` loading
default against A1's `2.417 s` loaded map. That mismatched output remains
archival diagnostic evidence only and is not scored.

`run_newton_bayesopt.py` and `run_newton_cylinder_diagnostic.py` now derive
loaded and residual observation timing from the supplied Chrono manifest,
pass it explicitly, record both Chrono and Newton values, and reject any
mismatch. The aligned A1 runs record `2.417 s` loaded and `0.25 s` residual in
both systems.

## Time-aligned held-out result

| Fixed material setting | Mechanics | Result |
| --- | --- | --- |
| 1.5 kg-selected incumbent: `E=70.46 kPa`, `nu=0.237231507`, `mu=0.305497980` | **Rejected** | Fresh preparation passes; the response violates strict zero particle-center penetration (31 sampled centers; `1.332 um` maximum). It has no valid objective. |
| unchanged baseline: `E=100 kPa`, `nu=0.2`, `mu=0.68` | **Accepted** | Zero sampled centers penetrate. Objective `16.289 mm` (`4.884 mm` loaded RMSE; `22.810 mm` residual-footprint RMSE). |

The fixed public Newton domain can therefore execute this 3 kg action, but the
material selected on the 1.5 kg action is not mechanically admissible at 3 kg.
It is not a usable forward-model candidate for this higher-load action. This is
a bounded transfer failure of that selected material point, not a claim that
Newton cannot run 3 kg or that either setting is physically calibrated.

The rejected incumbent output is not a BayesOpt observation, and this one
baseline comparison is not optimizer convergence, broad material calibration,
real-sand validation, or NVS/decision-use evidence.

Raw outputs are under:

- `outputs/validity_experiment/newton_holdout/mass3kg_incumbent_timealigned_20260927/`
- `outputs/validity_experiment/newton_holdout/mass3kg_baseline_timealigned_20260927/`

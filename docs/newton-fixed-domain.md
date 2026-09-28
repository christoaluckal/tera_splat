# Newton Fixed-Domain Contract

Last verified: 2026-09-21

This document defines the Newton configuration qualified for a separate sim-only
BayesOpt-style study. It does not supersede the frozen Genesis baseline, transfer
Genesis material parameters, or claim real-sand validation.

## Qualified numerical domain

| Item | Fixed value |
| --- | --- |
| configuration | `configs/newton_sand_smoke_voxel7p8125mm.json` |
| voxel size | `7.8125 mm` |
| transfer / integration | PIC / PIC |
| MPM bases | P0 strain, S2 collider, Q1 velocity |
| contact | stock Newton contact; no activation-distance override |
| coupling | 8 proxy iterations; 16 rigid substeps |
| action | frozen guided 1.5 kg Chrono cylinder |
| timing | 3.595 s loaded; removal; 0.25 s residual |
| external support | 14,161-cell frozen Chrono interior mask |
| smoke material | density 1000 kg/m3; E 100 kPa; nu 0.2; friction coefficient 0.68 |

The validation envelope contains `0.5`, `0.25`, and `0.125 ms` timesteps. A
BayesOpt study must select and record one of those timesteps before its first
candidate, use it for every candidate, and not optimize timestep or coupling
settings as material parameters.

## Evidence

Every level passes fresh PIC preparation, finite/full-support output, the
prismatic-guide gate, and strict zero analytic particle-center penetration.
Adjacent response comparisons pass the predeclared `0.5 mm` RMSE, `1.0 mm`
maximum, and `0.5 mm` loaded-sinkage-difference limits:

| Pair | map RMSE (loaded / residual) | maximum (loaded / residual) | sinkage difference |
| --- | ---: | ---: | ---: |
| `0.5 -> 0.25 ms` | `0.035 / 0.035 mm` | `0.218 / 0.213 mm` | `0.331 mm` |
| `0.25 -> 0.125 ms` | `0.058 / 0.054 mm` | `0.304 / 0.310 mm` | `0.422 mm` |

The response convergence analyzer reports `status: passed` and its code
provenance matches commit `474bd12c07733bd7307635a8c43354c720124cf0`.
Lightweight interpretation is in `diagnostics/newton_public_contact_20260914/`;
raw states, PLYs, maps, and the machine-readable summary remain under
`outputs/validity_experiment/newton/public_spatial_contact_20260914/voxel7p8125mm/stock_contact_8x16/`.

## Permitted study scope

Only Newton material parameters with explicitly Newton-native semantics and
bounds, plus study seed/observation order, may vary. Every candidate needs fresh
continuous preparation. Keep the Chrono episode, cylinder geometry and guide,
mask, map projection, timing, score, validity gates, numerical configuration,
and chosen timestep fixed. Record complete configuration and forward-model file
hashes. Do not import Genesis candidates, prepared states, fields, observations,
or parameter bounds as Newton evidence.

## Boundaries and next implementation work

This is numerical consistency inside the listed domain, not material calibration:
the smoke material's all-cell Chrono response RMSE is `3.822--3.905 mm`, and
first significant cylinder contact is `5.701--5.959 mm` above the initial
surface. Newton state arrays remain archival output, not restart checkpoints.

## Local material-study campaign (through 2026-09-21)

`scripts/run_newton_bayesopt.py` implements the isolated local study path. It
writes a candidate configuration, runs a fresh full-bed preparation preflight,
then independently runs a fresh continuous preparation/loading/removal response
with the frozen action and external maps. The preflight is deliberately not a
restart shortcut; saved Newton state remains archival only.

The study executed 21 candidate evaluations: the 100 kPa baseline, four
initialization candidates, four refinement candidates, four lower-bound
extension candidates, and eight broad-continuation candidates. Nineteen passed
all candidate-preparation and response mechanics gates and are valid
observations. The two failures, both at `mu≈0.273`, failed strict zero
particle-center penetration and are excluded rather than converted into a loss.
The current bounded material-search domain is `log10(E)=[4.8,5.2]`,
`nu=[0.1,0.3]`, and `mu=[0.3,0.9]`; numerical settings and external I/O stayed
fixed throughout.

The best valid candidate from the broad continuation is `log10(E)=4.847943757`
(`E=70.46 kPa`), `nu=0.237231507`, `mu=0.305497980`. Its discovery objective is
`8.823 mm` (`2.643 mm` loaded RMSE and `12.360 mm` residual-footprint RMSE), an
improvement of `3.875 mm` over the `12.698 mm` 100 kPa baseline. A separate
fresh replay with exactly that candidate scored `8.815 mm` (`2.641 mm` loaded;
`12.348 mm` residual-footprint), a `0.008 mm` difference. The replay is
validation evidence, not a duplicate optimizer observation.

This establishes repeatable local objective improvement inside the fixed
simulator domain. It is not optimizer convergence, calibrated material
inference, real-sand validation, held-out action transfer, or NVS/decision-use
validation. The local runners now derive, record, and assert the supplied
Chrono episode's loaded/residual time. In the aligned 3 kg A1 action, the
unchanged 100 kPa baseline is mechanically valid and scores `16.289 mm`; the
1.5 kg-selected incumbent is mechanically invalid (31 sampled particle centers
inside the cylinder, `1.332 um` maximum) and therefore has no valid transfer
score. The fixed public domain supports this higher-load action, but the
selected material point does not transfer as an admissible 3 kg candidate. See
`diagnostics/newton_mass3kg_holdout_20260922/`.

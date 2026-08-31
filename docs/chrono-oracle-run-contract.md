# Chrono Oracle and BayesOpt Run Contract

Last verified: 2026-08-30

This document defines the active experiment contract. Historical contracts are
archived in
[chrono-oracle-run-contract-through-2026-08-29.md](archive/chrono-oracle-run-contract-through-2026-08-29.md).

## Active oracle

Use only:

`/data/christoa/Chrono/tera_splat_sim/validity_experiment/chrono_episodes/A0_oracle_guided_offset_5mm_gate6mm_v1`

| Item | Required value |
| --- | --- |
| cylinder | 1.5 kg; radius `73.025 mm`; height `50.8 mm` |
| center | `(x, y) = (0, +5 mm)` |
| constraint | vertical prismatic guide; lateral motion and rotation constrained |
| SCM patch | `0.6 x 0.6 m` |
| SCM spacing | `5 mm` |
| Chrono timestep | `1 ms` |
| loaded acceptance | linear speed below `6 mm/s` and angular speed below `0.01 rad/s` for `0.10 s` |
| loaded sample time | `3.595 s` |
| residual duration | exactly `0.25 s` after removal |
| valid cells | `14,161`; exclude the one-cell SCM boundary ring |
| cylinder sinkage | `34.270 mm` |

The loading rule is a documented low-speed timing convention, not a
static-equilibrium claim. Its thresholds are oracle protocol constants, never
BayesOpt parameters.

## Active Genesis bed

Use only the accepted promoted bed:

`/data/christoa/Chrono/tera_splat/outputs/validity_experiment/A0_oracle_guided_offset_5mm_gate6mm_prepared_5mm_n128_ratio_matched/prepared_bed`

Required discretization:

| Item | Required value |
| --- | ---: |
| particle spacing | `5 mm` |
| particle size | `5 mm` |
| particles | `307,461` |
| MPM grid | `n128` |
| MPM cell width | `15.625 mm` |
| timestep | `0.5 ms` |
| CPIC | enabled |
| geostatic stress scale | `1.0` |

Prepared-bed acceptance evidence is p99 `0.492 mm/s`, H0 RMSE
`0.070 mm`, and maximum H0 error `0.237 mm` over all 14,161 cells.

Do not substitute a 10 mm-particle/n128 bed. It under-samples the grid and was
the cause of the previous high-resolution initialization failures.

## Candidate initialization gate

For every material candidate:

1. restore the accepted particle positions and active mask;
2. zero velocity and affine velocity state, reset plastic state, and reconstruct
   analytic depth-dependent geostatic `F` for that candidate's `E` and `nu`;
3. relax without the cylinder for up to `4 s`;
4. require p99 particle speed at or below `0.5 mm/s` for `0.02 s`;
5. require candidate H0 RMSE at or below `5 mm` and maximum error at or below
   `10 mm`;
6. hold the candidate without action for `0.25 s`;
7. require no-action surface drift at or below `0.5 mm` RMSE and `1.0 mm`
   maximum error.

The 4 s cap is duration headroom, not a relaxed gate. The three promoted
candidates first accepted between `2.077` and `2.180 s`.

A failure at this stage is an invalid initialization and must not enter the
BayesOpt surrogate.

## Response timing and loss

Every valid response uses:

- exactly `3.595 s` / 7,190 Genesis loading steps;
- removal by deleting the cylinder body;
- exactly `0.25 s` / 500 residual steps;
- at least 95% common valid support;
- the same Chrono valid mask and footprint.

The objective is unchanged:

`loaded_RMSE + 0.5 * residual_footprint_RMSE`

A complete fixed-time map is scoreable even if the raw phase label is
`timeout`. Preserve both the raw label and fixed-time acceptance mode.

## Current incumbent and provenance

The active n128 incumbent is `E=20.432828 kPa`, `phi=14.727053 deg`,
`nu=0.101894536`, discovered in W&B study
[`yab3idti`](https://wandb.ai/christo12aluckal/chrono-genesis-bayesopt/runs/yab3idti)
and independently confirmed by
[`r2at0vvb`](https://wandb.ai/christo12aluckal/chrono-genesis-bayesopt/runs/r2at0vvb).

| Metric | Previous confirmed incumbent | Confirmed active incumbent |
| --- | ---: | ---: |
| objective | `9.124 mm` | `8.704 mm` |
| loaded RMSE | `2.036 mm` | `1.864 mm` |
| residual-footprint RMSE | `14.176 mm` | `13.678 mm` |
| cylinder sinkage | `35.436 mm` | `35.813 mm` |
| H0 RMSE | `0.787 mm` | `0.876 mm` |
| no-action drift RMSE | `0.015 mm` | `0.018 mm` |

The confirmed residual signed mean is `+12.941 mm`, meaning Genesis remains too high
and too recovered inside the footprint after removal.

The actions that produced this promoted result were:

1. validate the 20 kPa point at n64 (`jg3b5v3s`);
2. confirm the low-`nu` basin with `vrxqwoe2`;
3. restore the n64 particle-to-cell ratio using 5 mm particles on n128;
4. retain geostatic scale 1.0 and all physics/gates;
5. extend only the candidate preparation cap from 2 s to 4 s;
6. search the compact incumbent region, then extend only the lower-friction
   boundary using same-fidelity observations;
7. replay the full-precision boundary-study winner with identical fixed-time
   maps and pass the frozen map-level repeatability regression.

The other promoted results are:

- `nwvdm2h8`: 18.110 kPa / 18.984 deg / 0.103989,
  objective `9.833 mm`;
- `4mtb3fyp`: 20.186 kPa / 18.485 deg / 0.100693,
  objective `10.041 mm`.

## Observation policy

Eligible current evidence:

- `jg3b5v3s`, `e72xmaou`, and `vrxqwoe2` for coarse search provenance;
- `qgk3079l`, `nwvdm2h8`, and `4mtb3fyp` for n128 response ranking.
- all eight valid response observations from `9on0s14j` for the current n128
  search frontier.
- all seven valid new response observations from `yab3idti`; its one failed
  initialization is not an observation.

`l5odv99s`, `85cw5i1i`, and `r2at0vvb` are repeatability evidence and must not
be imported as duplicate optimizer observations. Retained-raw replay
`ykep3esa` is visualization evidence only: its aggregate score and p99 map
agreement were stable, but four residual projection cells exceeded the frozen
three-cell sparse-bin allowance. It is neither a seed nor replacement
confirmation evidence.

Explicitly excluded:

- every study against legacy `A0_cal_full10mm`;
- setup study `ysagrtcb`, which exposed the fixed bootstrap geometry bug;
- `mv698mto`, which failed before contact under the obsolete 2 s cap;
- rejected 10 mm-particle/n128 prepared beds;
- any trial failing initialization, support, or timing requirements.

Do not seed an n128 surrogate with coarse objectives unless the code explicitly
models resolution as a fidelity level. A future n128 study may seed valid
response observations from `qgk3079l`, `9on0s14j`, and `yab3idti`. When the
proposal box is narrower than those same-fidelity observations, use the
explicit `--allow-out-of-region-seeds` flag; particle geometry must still
match the accepted prepared bed.

## Next experiment

Boundary-extension study `yab3idti` completed seven of eight requested new
candidates; one failed the no-action initialization gate before contact. Its
iteration 011 winner passed exact replay `r2at0vvb` and is now the incumbent.

The incumbent's aligned isometric point-cloud and signed 2D DEM-error views are
now generated from retained-raw replay `ykep3esa`. Before another optimization
study, quantify the maps with footprint radial profiles, center cross-sections,
signed error, and loaded-to-residual recovery change. Use that evidence to
decide between a local refinement around `phi=14--15 deg` and a documented
constitutive-model limitation. Do not change the target, initial state, timing,
projection, objective, or acceptance gates during diagnosis.

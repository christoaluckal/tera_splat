# Current Chrono–Genesis Calibration State

Last verified: 2026-08-29

This is the authoritative live handoff for the cylinder calibration. Dated
investigation history is preserved in
[calibration-history-through-2026-08-29.md](archive/calibration-history-through-2026-08-29.md)
and is not a source of current next steps.

## Current outcome

The Chrono oracle, fixed-time bridge, W&B BayesOpt loop, candidate-specific
initialization, no-action stability test, and high-resolution Genesis bed are
all operational.

The current best known material candidate is:

| Parameter | Value |
| --- | ---: |
| Young modulus | `20,000 Pa` |
| friction angle | `18.149 deg` |
| Poisson ratio | `0.100004` |
| particle size and spacing | `5 mm` |
| Genesis MPM grid | `n128` |
| Genesis timestep | `0.5 ms` |

At n128 it has objective `9.626 mm`, loaded RMSE `2.142 mm`, and
residual-footprint RMSE `14.966 mm`. Initialization is not the remaining
blocker: H0 RMSE is `0.747 mm`, and the 0.25 s no-action drift RMSE is only
`0.011 mm`. The remaining mismatch is excessive Genesis recovery after
cylinder removal.

## Frozen experiment contract

### Chrono oracle

| Item | Active value |
| --- | --- |
| episode | `A0_oracle_guided_offset_5mm_gate6mm_v1` |
| path | `/data/christoa/Chrono/tera_splat_sim/validity_experiment/chrono_episodes/A0_oracle_guided_offset_5mm_gate6mm_v1` |
| cylinder | 1.5 kg; radius `73.025 mm`; height `50.8 mm` |
| center and constraint | `(0, +5 mm)`; vertical prismatic guide |
| SCM patch | `0.6 x 0.6 m`; `5 mm` spacing; `1 ms` Chrono step |
| loading acceptance | below `6 mm/s` linear and `0.01 rad/s` angular for `0.10 s` |
| loaded sample | accepted at `3.595 s` |
| residual sample | fixed `0.25 s` after removal |
| usable support | `14,161` cells; invalid SCM boundary ring excluded |
| Chrono cylinder sinkage | `34.270 mm` |

The loaded-state gate is an explicitly recorded low-speed convention, not a
claim of static equilibrium. Do not regenerate or retime the oracle during a
material study.

### Genesis prepared bed

The accepted promoted bed is:

`/data/christoa/Chrono/tera_splat/outputs/validity_experiment/A0_oracle_guided_offset_5mm_gate6mm_prepared_5mm_n128_ratio_matched/prepared_bed`

| Item | Value |
| --- | ---: |
| particles | `307,461` |
| particle spacing and size | `5 mm` |
| MPM grid | `n128`; cell width `15.625 mm` |
| particle spacings per grid cell | `3.125` |
| timestep | `0.5 ms` |
| coupling | CPIC enabled |
| geostatic stress scale | `1.0` |
| preparation acceptance time | `1.1825 s` |
| final p99 speed | `0.492 mm/s` |
| H0 RMSE / maximum | `0.070 / 0.237 mm` |
| supported target cells | `14,161` |

The earlier n128 attempts incorrectly retained 10 mm particles, leaving only
1.5625 particle spacings per grid cell. Matching the accepted n64
particle-to-cell ratio with 5 mm particles resolved the failure without a
stress multiplier or physics change.

### Candidate validity and scoring

A candidate is an observation only if all of the following hold:

1. candidate-specific analytic geostatic state is reconstructed from frozen
   positions using that candidate's material values;
2. cylinder-free relaxation reaches p99 speed at or below `0.5 mm/s` for
   `0.02 s`;
3. candidate H0 remains within `5 mm` RMSE and `10 mm` maximum error;
4. the separate 0.25 s no-action hold remains within `0.5 mm` RMSE and
   `1.0 mm` maximum drift;
5. all requested loaded and residual maps exist on at least 95% of the common
   valid support.

At n128, use a `4 s` candidate-preparation cap. The promoted candidates first
meet the unchanged speed gate at `2.077--2.180 s`; the old 2 s cap was too
short.

The fixed loss remains:

`objective = loaded_RMSE + 0.5 * residual_footprint_RMSE`

Loaded maps use exactly 7,190 Genesis steps (`3.595 s`), and residual maps
use exactly 500 steps (`0.25 s`). Raw equilibrium/timeout labels remain
recorded but do not invalidate a complete fixed-time map.

## Observation set

### Eligible evidence

| ID | Role | Resolution | Observations | Result |
| --- | --- | --- | ---: | --- |
| `jg3b5v3s` | controlled 20 kPa anchor | 10 mm particles, n64 | 1 | `8.548 mm` |
| `e72xmaou` | fresh unseeded coarse study | 10 mm particles, n64 | 12/12 valid | fresh best `9.232 mm`; did not sample `nu<0.14` |
| `vrxqwoe2` | anchor-inclusive trust region | 10 mm particles, n64 | anchor + 9/9 valid | anchor remained best; two low-nu confirmations |
| `qgk3079l` | n128 replay of anchor | 5 mm particles, n128 | 1 valid | current best `9.626 mm` |
| `nwvdm2h8` | n128 replay of coarse iteration 007 | 5 mm particles, n128 | 1 valid | `9.833 mm` |
| `4mtb3fyp` | n128 replay of coarse iteration 006 | 5 mm particles, n128 | 1 valid | `10.041 mm` |

Coarse observations establish the search basin but must not be mixed silently
with n128 observations in a resolution-specific surrogate model.

### Excluded evidence

- All `A0_cal_full10mm` studies use a legacy free-centered target with an
  incomplete residual-time contract. They demonstrate pipeline execution only.
- `ysagrtcb` was stopped after its first bootstrap candidate used a legacy
  hard-coded 20 mm particle spacing. It is not a seed source.
- `mv698mto` used the obsolete 2 s n128 candidate-preparation cap and failed
  before contact. It is not a response observation.
- Rejected 10 mm-particle/n128 prepared beds are initialization diagnostics,
  not material observations.
- Any candidate that fails H0, equilibrium, support, or no-action gates must
  remain outside BayesOpt training data.

## Previous best-known candidate: observations, actions, and results

Before resolution promotion, the 20 kPa candidate from `jg3b5v3s` was the
best known valid response at the stable 10 mm-particle/n64 resolution.

### Observations that selected it

- Chrono cylinder sinkage was `34.270 mm`; the coarse Genesis candidate
  reached `34.051 mm`.
- Coarse loaded RMSE was `2.183 mm`.
- Coarse residual-footprint RMSE was `12.729 mm`.
- The combined coarse objective was `8.548 mm`.
- Fresh study `e72xmaou` produced a `9.232 mm` best but missed the useful
  low-`nu` corner.
- Anchored study `vrxqwoe2` then produced independent nearby candidates at
  `8.605 mm` and `8.643 mm`, confirming rather than displacing the anchor.

### Actions taken

1. Kept the Chrono oracle, loss, contact physics, material model, and validity
   gates fixed.
2. Fixed the BayesOpt bootstrap so particle geometry comes from the accepted
   prepared-bed manifest.
3. Replaced the under-sampled 10 mm-particle/n128 preparation with a
   ratio-matched 5 mm-particle/n128 bed.
4. Kept geostatic stress scale at 1.0.
5. Increased only the candidate-preparation time cap from 2 s to 4 s; the
   equilibrium threshold remained `0.5 mm/s`.
6. Replayed the anchor and the two corroborating low-`nu` candidates with
   identical 3.595 s loading and 0.25 s residual timing.

### Results

| Candidate | Coarse objective | n128 objective | n128 loaded RMSE | n128 residual-footprint RMSE | n128 cylinder sinkage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 20.000 kPa, 18.149 deg, 0.100004 | **`8.548 mm`** | **`9.626 mm`** | **`2.142 mm`** | **`14.966 mm`** | `29.413 mm` |
| 18.110 kPa, 18.984 deg, 0.103989 | `8.605 mm` | `9.833 mm` | `2.188 mm` | `15.290 mm` | `29.072 mm` |
| 20.186 kPa, 18.485 deg, 0.100693 | `8.643 mm` | `10.041 mm` | `2.316 mm` | `15.449 mm` | `27.097 mm` |

The ordering is stable across resolutions. For the anchor, finer resolution
slightly improves loaded RMSE (`2.183 -> 2.142 mm`) but worsens residual
footprint RMSE (`12.729 -> 14.966 mm`). Its n128 residual signed mean is
`+14.308 mm`: Genesis is too high and retains too little deformation after
removal.

## Current interpretation

- The Chrono input is qualified and resolution-matched.
- Genesis initialization is stable and no longer rebounds.
- The BayesOpt I/O and fixed-time loop are working.
- The 20 kPa candidate is the current n128 incumbent.
- The remaining problem is response calibration: the current Genesis Sand
  response recovers too much after removal.
- The current evidence does not justify a classifier, an extra fit parameter,
  a stress multiplier, a relaxed initialization gate, or another target change.

## Next experiment

Run a small online BayesOpt study directly on the accepted n128 bed, seeded
only with `qgk3079l`, using the existing parameters:

- `E = 18--26 kPa`;
- `phi = 16.5--18.5 deg`;
- `nu = 0.10--0.13`.

The purpose is to reduce residual recovery without degrading the loaded fit.
If no valid candidate can improve residual error while preserving loading, the
next blocker is the constitutive response of the current Genesis Sand model,
not initialization, I/O, or Chrono H0.

## Operational paths

- BayesOpt driver:
  `tera_splat/scripts/run_chrono_genesis_bayesopt.py`
- bridge:
  `tera_splat/scripts/run_chrono_genesis_bridge.py`
- prepared-bed builder:
  `tera_splat/scripts/build_chrono_settled_bed.py`
- mass-controlled Genesis runner:
  `tera_splat/scripts/run_mass_controlled_terrain.py`
- active environment:
  `chrono_splat`
- generated calibration outputs:
  `/data/christoa/Chrono/tera_splat/outputs`
- Chrono oracle outputs:
  `/data/christoa/Chrono/tera_splat_sim/validity_experiment/chrono_episodes`

See [Chrono Oracle Run Contract](chrono-oracle-run-contract.md) for the exact
run rules and [Experiment Problems](experiment_problems.md) for the resolved
and current blockers.

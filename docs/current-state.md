# Current Chrono–Genesis Calibration State

Last verified: 2026-09-03

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
| Young modulus | `20,432.828 Pa` |
| friction angle | `14.727053 deg` |
| Poisson ratio | `0.101894536` |
| particle size and spacing | `5 mm` |
| Genesis MPM grid | `n128` |
| Genesis timestep | `0.5 ms` |

Its exact independent replay, W&B `r2at0vvb`, has objective `8.704 mm`,
loaded RMSE `1.864 mm`, and residual-footprint RMSE `13.678 mm`.
Initialization is not the remaining blocker: H0 RMSE is `0.876 mm`, and the
0.25 s no-action drift RMSE is only `0.018 mm`. Genesis still recovers too
much after cylinder removal, but a controlled numerical matrix now shows that
this response mismatch cannot yet be attributed purely to constitutive model
form.

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
| `qgk3079l` | n128 replay of previous anchor | 5 mm particles, n128 | 1 valid | `9.626 mm` |
| `nwvdm2h8` | n128 replay of coarse iteration 007 | 5 mm particles, n128 | 1 valid | `9.833 mm` |
| `4mtb3fyp` | n128 replay of coarse iteration 006 | 5 mm particles, n128 | 1 valid | `10.041 mm` |
| `l5odv99s` | independent incumbent repeatability replay | 5 mm particles, n128 | 1 valid | `9.621 mm`; validation evidence, not a duplicate optimizer seed |
| `9on0s14j` | compact incumbent-region study | 5 mm particles, n128 | seed + 8/8 valid | best `9.131 mm` at iteration 008 |
| `85cw5i1i` | exact replay of `9on0s14j` iteration 008 | 5 mm particles, n128 | 1 valid | confirmed at `9.124 mm`; validation evidence only |
| `yab3idti` | low-friction boundary extension | 5 mm particles, n128 | 9 seeds + 7/8 valid | best `8.707 mm` at iteration 011; one candidate failed initialization before contact |
| `r2at0vvb` | exact replay of `yab3idti` iteration 011 | 5 mm particles, n128 | 1 valid | confirmed at `8.704 mm`; validation evidence only |
| `ykep3esa` | retained-raw incumbent visualization replay | 5 mm particles, n128 | 1 valid | `8.705 mm`; raw PLY/state evidence only, not a seed or confirmation replacement |

Coarse observations establish the search basin but must not be mixed silently
with n128 observations in a resolution-specific surrogate model.

### I/O and forward-repeatability gate

Before starting the compact n128 study, the retained `qgk3079l` artifact was
used for an automated contract regression covering frame, units, geometry,
grid, mask, timing, prepared state, candidate, and score recomputation. A fresh
incumbent replay, W&B `l5odv99s`, then passed the same gates:

- objective changed by `-0.0047 mm`;
- loaded RMSE changed by `+0.00012 mm`;
- residual-footprint RMSE changed by `-0.0097 mm`;
- the 14,161-cell valid mask was identical;
- p99 absolute map disagreement was at most `0.010 mm`;
- three residual footprint cells changed by more than 1 mm because particles
  crossed bins in the discrete upper-envelope projection.

Future trials now persist the resolved n128 grid and `0.5 ms` timestep in both
`material_config.json` and the bridge manifest. The older `qgk3079l` material
file inherited a stale n64 display value even though its prepared-bed manifest
and executed solver command correctly used n128.

The new incumbent's exact replay `r2at0vvb` also passed the frozen regression:
candidate identity, phase acceptance, support mask, score tolerances, p99 map
agreement, and sparse projection-bin bounds all passed. Its objective differed
from discovery iteration 011 by only `-0.0034 mm`.

Retained-raw replay `ykep3esa` preserved 78 sampled rollout PLYs plus initial,
loaded, residual, candidate-preparation, and no-action states. Its objective
was within `+0.0015 mm` of `r2at0vvb`; p99 map disagreement remained below
`0.011 mm`. Four residual cells crossed the 1 mm discrete upper-envelope bin
threshold, however, while the frozen sparse-bin allowance is three. Therefore
use it for raw/visual evidence, not as a replacement confirmation, and do not
relax the gate after observing this run.

### Non-learned model-form diagnosis

`diagnose_chrono_genesis_model_form.py` now performs the proposed diagnosis
without adding a discrepancy network. It generated:

- a post-hoc loaded-versus-residual Pareto front from 16 unique valid n128
  candidates;
- loaded, residual, and loaded-to-residual recovery error maps, radial
  profiles, and center cross-sections;
- particle-level `F`, `Jp`, displacement, and radial internal-state summaries;
- a controlled `n64/n128` by `0.5/0.25 ms` end-to-end numerical matrix.

The Pareto front has four points. Moving from its best loaded point to its
best residual point worsens loaded RMSE from `1.864` to `1.997 mm` while
improving residual-footprint RMSE only from `13.682` to `13.533 mm`. The raw
incumbent's footprint recovery-error RMSE is `9.213 mm`; its final state has
8,481 particles with nonzero `Jp`, up from 1,243 initially. These observations
support a localized plastic/recovery mismatch rather than an I/O offset.

The numerical matrix is:

| particles / grid | timestep | loaded RMSE | residual-footprint RMSE |
| --- | ---: | ---: | ---: |
| 10 mm / n64 | `0.5 ms` | `2.298 mm` | `13.448 mm` |
| 10 mm / n64 | `0.25 ms` | `2.979 mm` | `15.773 mm` |
| 5 mm / n128 | `0.5 ms` | `1.864 mm` | `13.682 mm` |
| 5 mm / n128 | `0.25 ms` | `2.468 mm` | `15.207 mm` |

Halving the timestep changes residual-footprint RMSE by `+2.325 mm` at n64
and `+1.525 mm` at n128. Resolution changes at fixed timestep are smaller:
`+0.233 mm` at `0.5 ms` and `-0.566 mm` at `0.25 ms`. Two timestep levels
expose material end-to-end sensitivity but cannot establish an asymptotic
convergence rate. Therefore the current status is: constitutive/recovery
mismatch is strongly suggested, but it is not isolated from numerical
sensitivity.

Canonical report:

`tera_splat/diagnostics/model_form_2x2_20260901`

### Third n128 timestep experiment

The requested `0.125 ms` n128 refinement did not produce a valid response
observation. End-to-end prepared-bed attempts failed the unchanged p99-speed
gate at both 2 and 4 s:

| preparation cap | final p99 speed | H0 RMSE / maximum | result |
| ---: | ---: | ---: | --- |
| `2.0 s` | `0.590 mm/s` | `0.769 / 1.161 mm` | rejected timeout |
| `4.0 s` | `0.621 mm/s` | `1.833 / 2.450 mm` | rejected timeout |

Both surface gates passed, but the required `0.5 mm/s for 0.02 s` speed hold
did not. Reusing the accepted n128/0.25 ms state and running candidate
reconstruction at `0.125 ms` through the explicit run-one diagnostic override
also timed out before cylinder contact. Therefore there is no legitimate third
loaded/residual score and no three-level convergence estimate. The failed
trial is excluded from optimization evidence.

Lightweight evidence:

`tera_splat/diagnostics/n128_dt0p125_20260901`

### Same-state pre-settle localization

The requested follow-up is complete. Three full-duration 4.0 s traces start
from the exact same accepted 307,461-particle n128 state and change only
timestep:

| timestep | first accepted p99 window | final p50 / p95 / p99 | fastest 1% at 4 s | persistent median dz |
| ---: | ---: | ---: | --- | ---: |
| `0.5 ms` | `2.055 s` | `0.100 / 0.243 / 0.450 mm/s` | 98.4% wall; 76.7% ground | `-3.135 mm` |
| `0.25 ms` | `1.53025 s` | `0.170 / 0.360 / 0.516 mm/s` | 97.7% wall; 49.9% surface | `-1.968 mm` |
| `0.125 ms` | none | `0.291 / 0.764 / 0.986 mm/s` | 99.87% surface; 58.8% wall | `+2.555 mm` |

The accepted-window times record the first transient 0.02 s hold; because the
diagnostic deliberately continues to 4 s, the 0.25 ms p99 can finish above the
gate. Median speed is below 0.5 mm/s in every trace, excluding uniform
whole-bed motion. At 0.125 ms, however, p95 is also above 0.5 mm/s and the
fastest population is almost entirely at the free surface. The failed third
level is therefore a timestep-dependent shift from containment settling to
surface uplift/rebound, not merely a one-percent wall-tail artifact.

Canonical lightweight report:

`tera_splat/diagnostics/pre_settle_timestep_20260903`

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
- The confirmed 20.433 kPa / 14.727 deg / 0.101895 candidate is the current
  n128 incumbent.
- The current Genesis Sand response recovers too much after removal, and the
  loaded/residual Pareto trade-off plus `F`/`Jp` localization make model-form
  limitation plausible.
- End-to-end timestep convergence is not demonstrated, and the `0.125 ms`
  level cannot pass the frozen initialization gate. Same-state traces localize
  this to a timestep-dependent boundary/free-surface mode with net surface
  uplift at the fine step. This prevents a clean model-form-only diagnosis
  and blocks another material sweep.
- The current evidence does not justify a classifier, an extra fit parameter,
  a stress multiplier, a relaxed initialization gate, or another target change.

## Completed n128 studies and next experiment

Compact online n128 study `9on0s14j` imported only `qgk3079l` and completed
eight valid new candidates over:

- `E = 18--26 kPa`;
- `phi = 16.5--18.5 deg`;
- `nu = 0.10--0.13`.

Its iteration 008 winner scored `9.131 mm`: loaded RMSE `2.036 mm`,
residual-footprint RMSE `14.189 mm`, and residual signed mean `+13.519 mm`.
Exact-candidate replay `85cw5i1i` passed the automated repeatability gate at
`9.124 mm`, `2.036 mm`, `14.176 mm`, and `+13.502 mm`, respectively. The
loaded cylinder sinkage was `35.436 mm` versus Chrono `34.270 mm`.

That compact-study point lay on the lower friction-angle boundary and near the
lower Poisson-ratio boundary. It motivated a frozen-contract boundary
extension over:

- `E = 18--24 kPa`;
- `phi = 12--16.5 deg`;
- `nu = 0.10--0.115`;
- seed with valid n128 response observations from `qgk3079l` and `9on0s14j`;
- do not seed duplicate confirmation replays.

Boundary-extension study `yab3idti` then imported the nine same-resolution
observations, completed seven of eight new candidates, and rejected one during
the no-action initialization gate before contact. Iteration 011 improved both
phases at `E=20.432828 kPa`, `phi=14.727053 deg`, and `nu=0.101894536`:
objective `8.707 mm`, loaded RMSE `1.864 mm`, residual-footprint RMSE
`13.685 mm`, and residual signed mean `+12.949 mm`. Exact replay `r2at0vvb`
confirmed it at `8.704 mm`, `1.864 mm`, `13.678 mm`, and `+12.941 mm`.

The winner is not on the extended lower friction boundary, so another blind
boundary expansion is not the next step. The spatial, recovery, hidden-state,
Pareto, 2x2 numerical, and same-state pre-settle diagnostics are complete.
If work continues with Genesis, its next forward-model task is a controlled
containment/state-preparation correction or ablation that removes the
timestep-dependent wall/surface drift, followed by rerunning the unchanged
three-level preparation and response checks. Keep the oracle, material, action,
observation times, scoring, and acceptance rule frozen while changing one
numerical mechanism at a time. Do not add a learned discrepancy model or start
another BayesOpt study before preparation consistency and response convergence
are demonstrated.

## Forward-model branch decision

This working tree is the Genesis baseline and should be committed as such
before starting another solver. Newton is a viable candidate for a separate
MPM branch, not a drop-in replacement and not part of any result above. Its
implicit granular MPM solver exposes pressure-dependent yielding and rigid-MPM
coupling, but the coupling path is still described as experimental and moving
container boundaries require an explicit penetration test.

The Newton branch may reuse the qualified Chrono oracle, cylinder action and
timing, valid mask, map projection, score definition, visualization, diagnostic
layout, and external output contract. It must not reuse Genesis `F`/`C`/`Jp`
state, prepared-bed acceptance, material observations, optimizer seeds, or
calibrated parameters as if they were solver-independent. In particular,
Newton's friction coefficient is not silently interchangeable with the Genesis
friction angle.

The first Newton acceptance ladder is:

1. pin Newton and Warp in a separate environment and record exact versions;
2. reproduce the frozen geometry with a cylinder-free granular bed and static
   containment;
3. run the same three timestep/state-preparation diagnostics and qualify a new
   Newton initial state;
4. validate two-way cylinder loading and container removal without wall
   penetration;
5. emit the same externally visible maps, masks, timing, gates, and provenance;
6. compare one valid Newton response with the unchanged Chrono oracle;
7. begin a fresh Newton calibration only after those gates pass.

If work instead continues on the Genesis branch, the controlled numerical
correction described above remains its next experiment. Evidence from the two
backends must remain separately named and must never be pooled implicitly.

## Operational paths

- BayesOpt driver:
  `tera_splat/scripts/run_chrono_genesis_bayesopt.py`
- bridge:
  `tera_splat/scripts/run_chrono_genesis_bridge.py`
- prepared-bed builder:
  `tera_splat/scripts/build_chrono_settled_bed.py`
- mass-controlled Genesis runner:
  `tera_splat/scripts/run_mass_controlled_terrain.py`
- aligned point-cloud/DEM comparison renderer:
  `tera_splat/scripts/render_chrono_genesis_pointcloud_dem_comparison.py`
- non-learned model-form diagnostic:
  `tera_splat/scripts/diagnose_chrono_genesis_model_form.py`
- pre-settle timestep analyzer:
  `tera_splat/scripts/analyze_pre_settle_timestep_diagnostics.py`
- aligned and raw PCD exporter:
  `tera_splat_sim/export_scm_genesis_pcd.py`
- active environment:
  `chrono_splat`
- generated calibration outputs:
  `/data/christoa/Chrono/tera_splat/outputs`
- retained incumbent raw/visual evidence:
  `/data/christoa/Chrono/tera_splat/outputs/validity_experiment/bayesopt/A0_oracle_guided_offset_5mm_gate6mm_5mm_n128_incumbent_raw_20260830/study_ykep3esa`
- Chrono oracle outputs:
  `/data/christoa/Chrono/tera_splat_sim/validity_experiment/chrono_episodes`

See [Chrono Oracle Run Contract](chrono-oracle-run-contract.md) for the exact
run rules and [Experiment Problems](experiment_problems.md) for the resolved
and current blockers.

# Current Chrono-to-MPM State

Last verified: 2026-10-19

This is the authoritative live handoff for the cylinder calibration. Dated
investigation history is preserved in
[calibration-history-through-2026-08-29.md](archive/calibration-history-through-2026-08-29.md)
and is not a source of current next steps.

## 2026-10-17 fresh-only reset

The 2026-10-09/16 static-proxy outputs are quarantined as historical
diagnostics. They are not admissible for current qualification, training,
validation, or test claims because same-build determinism and complete
provenance were not established before reuse.

The active campaign is
[fresh hierarchical Phase 0](newton/fresh-hierarchical-phase0-20261017.md).
It now has 7/15 complete matrix Chrono and 7/15 usable matrix Newton cases; the sentinel
duplicates are qualification evidence, not training rows. Sequential fresh
repeats of Chrono, particle-bed generation, and Newton now characterize
same-build numerical variation. Matrix expansion is permitted. Exact equality
is reported but is not a gate. No old PLY, prepared state, response, or surface
map may enter the new output roots.

The active hierarchy keeps provenance and numerical integrity as hard gates.
Repeat variation is an uncertainty measurement. Particle overlap is recorded
as an interaction artifact unless it
is gross. Footprint and twice-radius skill relative to a no-deformation
baseline are the primary Phase 0 utility gates.

The centered 31 N fresh sentinel is complete. Chrono maps and the independently
generated beds match exactly. Newton is compatible but non-identical: loaded
repeat RMSE is 0.0083 mm in the footprint and 0.0050 mm within 2r; residual
footprint repeat RMSE is 0.0090 mm. One residual cell just outside the footprint
differs by 10.552 mm, raising raw 2r repeat RMSE to 0.426 mm even though 2r p95
absolute difference is 0.0117 mm and residual particle-position RMSE is only
0.00059 mm. Both responses have eight transient inside centers below 3.92
micrometers and zero at the loaded observation. The raw prior has positive
footprint and 2r skill against no deformation, so the next action is fresh
matrix generation rather than more sentinel optimization.

All three canonical 31 N training rows—center and ±100 mm x—are complete and
pass every numerical, artifact, and local positive-skill check. Loaded
footprint/2r skill is 0.889/0.724 at center, 0.833/0.629 at +x, and 0.828/0.625
at -x. Their physical post-unload states also retain positive local skill. The
off-center post-unload maps have 38.945/39.023 mm maximum-error tails, retained
instead of hidden by RMSE. The first learning rung is the full five-position
31 N slice (3 train / 1 validation / 1 test), now complete at 5/5. The small v1
residual code and fixed hyperparameters were written before holdout generation;
the fit is now frozen with model SHA-256
`242fa879c1d7eda443f4277d82a41dcfea5828cdb7b66ccae357b633d99a15af`.
The training record proves that both holdout summaries were absent and hashes
the learner plus all inputs. Training-only particle-lift RMSE is
1.446-1.838 mm in-foot and 1.034-1.173 mm within 2r, a fit sanity result only.
The model was not refit after either holdout. Higher loads remain the next
expansion rungs.

The +y validation action is now complete and was never available during fit.
The frozen particle correction improves loaded footprint/2r RMSE from
5.784/3.971 mm to 2.077/2.211 mm and post-unload RMSE from 5.665/3.820 mm to
2.267/2.335 mm. It beats raw Newton and no deformation on all four local
checks, while preserving 307,461 finite particle positions and the frozen
model/source hashes. The subsequent -y result below completes the rung.

The -y independent test is now complete. The same frozen model improves loaded
footprint/2r RMSE from 5.706/3.936 mm to 2.158/2.252 mm and post-unload from
5.601/3.791 mm to 2.359/2.382 mm. Validation and test both pass every local
improvement check; the joint held-out summary is true. Post-holdout fitting is
actively refused, 50 relevant tests pass, and corrected test particles retain
finite 307,461-particle states whose projected surfaces exactly match the
learned corrected fields. The 31 N spatial rung is therefore 5/5 and complete.
This is single-load spatial transfer; fresh 46 N evidence remains required for
the multiple-load Phase 0 goal. The protected 61 N rung is a robustness
decision after the two-load result, not an automatic prerequisite.

Multi-load v2 is prospectively fixed before the first 46 N result. It reuses
the tested v1 geometry/particle path without modifying v1, retains identical
hyperparameters, and will fit only the six center/±x actions at 31 N and 46 N.
Its fit lock protects both 46 N y-holdouts and all 61 N actions. The first
46 N center action is complete and usable: loaded footprint/2r RMSE is
13.340/8.226 mm with skill 0.608/0.419, and post-unload RMSE is
10.160/6.666 mm with skill 0.773/0.618. The +x 46 N training action is also
complete and usable: loaded footprint/2r RMSE is 13.912/8.659 mm with skill
0.580/0.370, and post-unload RMSE is 10.275/6.337 mm with skill 0.771/0.663.
It records 31 transient centers to 9.837 micrometers and seven at the loaded
state; that remains a contact artifact rather than a strict-mechanics pass,
but it is inside the frozen gross-artifact limits and passes every local
utility check. The 46 N rung is 2/5; only -x remains before v2 fitting,
followed by the untouched +y/-y holdouts.

## 2026-10-16 bounded static-prior update

The frozen 35 mm static proxy test began as a 15-case matrix over five
positions and 30.656, 45.984, and 61.313 N loads. Its lowest-load center case
was the expansion sentinel.

The centered 31 N timestep matrix is complete. Every row fails strict zero
penetration and the response is not timestep-converged, so the 35 mm domain is
not strictly mechanics-qualified. A separate policy,
`bounded_static_prior_v2_20261016`, permits offline residual-pilot data only
when preparation, finite state, guide, support, and loaded-state clearance
pass and trajectory-only overlap is at most 10 micrometers and 0.02% of
particles.

The centered 31 N and 46 N actions pass the bounded gate and fail strict
mechanics. Policy v2 was frozen after those two training actions and before
the 61 N and spatial cases. A later failure shrinks the pilot domain; the
limits must not move again. Residual training remains locked until all actions
in the final domain have accepted Chrono GT and bounded-admissible Newton
states. See the [strict report](newton/static-proxy-qualification-20261009.md)
and [bounded admission report](newton/coarse-prior-admission-20261016.md).

The frozen policy rejects centered 61.313 N because 38 centers remain inside
at the loaded observation. The initial domain is capped at 30.656--45.984 N
and reissued as 10 actions: six train (center and plus/minus x), two validation
(plus y), and two test (minus y). The rejected high load remains explicit
out-of-domain evidence.

## 2026-10-08 handoff update

The bounded Newton A10 stop/go set is complete. Broad parameter-only search of
the current Newton model form is stopped. Newton is retained as a
mechanics-gated physics prior for an offline Chrono-supervised residual model.

The current operational sources are:

- [Newton handoff](newton/handoff.md);
- [Newton running analysis](newton/running-analysis.md);
- [consolidated Newton report](newton/experiment-consolidated-20261008.md);
- [hybrid model design](hybrid-chrono-mpm-residual-gaussian-planning-20261008.md).

The 35 mm proxy foot lies outside the qualified historical Newton geometry and
must pass a new mechanics/load-domain qualification. Any material fit for that
domain is performed once across training actions and frozen for held-out
position and weight evaluation.

## Current outcome

The Chrono oracle and frozen Genesis baseline remain operational. On the
Newton branch, PIC preparation and native Kamino/prismatic coupling are
qualified. The historical 9.375 mm raised-proxy diagnostic passes a complete
`0.5/0.25/0.125 ms` response matrix at 100 kPa, but it omits a lower collision
slice and is not promotable.

The historical full-volume S2 contact-activation diagnosis leaves the analytic
cylinder and zero collision-bottom inset intact.  A Newton-1.5.1,
process-local, cylinder-only rasterizer adapter changes node activation from
the native `+0.25` to `-0.25` voxel without changing the signed-distance
geometry, action, strict particle-center test, external I/O, or gates.  Its
full three-level matrix is mechanics-qualified: every row has accepted
preparation, finite 14,161-cell I/O, zero center penetration, and a passed
guide gate.  Both adjacent map pairs pass.  The result remains
`not_demonstrated`, however, because coarse-to-medium sinkage is `0.975 mm`
against the frozen `0.5 mm` gate; medium-to-fine sinkage is `0.480 mm` and
passes.  Material calibration and large evaluation remain stopped.  Evidence
is `diagnostics/newton_contact_activation_20260910/`.

That private activation override is diagnostic only and is not a forward-model
candidate.  The active direction uses stock Newton contact and explicit public
settings.  At the original `15.625 mm` voxel size, `4` proxy iterations and
`8` rigid substeps pass the `0.5/0.25 ms` mechanics, map (`0.053/0.053 mm`
RMSE), and sinkage (`0.192 mm`) pairwise gates, but leave the analytic cylinder
bottom `10.632/10.823 mm` above the initial surface.  It is numerically stable
but has an unacceptable contact-location bias for calibration.

Halving only the public voxel size to `7.8125 mm` passes a fresh complete PIC
preparation/tolerance matrix. The original refined-grid `4/8` coupling pair
is mechanics-qualified but misses the sinkage gate by `1.339 mm`; that failed
configuration remains diagnostic evidence only.

Increasing only public coupling effort to `8` proxy iterations and `16` rigid
substeps produces the active stock-contact Newton domain. Its complete
`0.5/0.25/0.125 ms` response matrix passes all mechanics gates and both
adjacent numerical gates. Loaded/residual map RMSE is `0.035/0.035 mm` and
`0.058/0.054 mm`; maximum map differences are at most `0.218/0.310 mm`; and
sinkage differences are `0.331/0.422 mm`, all within the frozen
`0.5/1.0/0.5 mm` thresholds. The loaded cylinder bottom remains
`4.110/4.440/4.862 mm` above its initial surface level, with first significant
contact at `5.701/5.828/5.959 mm`; these are declared numerical-domain
properties, not claims of physical calibration.

No internal Newton computation or private rasterizer override is part of this
domain. A separate sim-only BayesOpt study may now be built using one fixed
validated timestep and this configuration for every candidate. It must keep
the Chrono I/O, action, mask, timing, score, and candidate validity gates
fixed; it cannot reuse Genesis observations, states, or material semantics.
Evidence is `diagnostics/newton_public_contact_20260914/` and
`docs/newton/fixed-domain.md`.


The isolated local Newton BayesOpt driver has now completed 21 candidate
evaluations in this fixed `0.25 ms`, `8/16` domain. Nineteen are
mechanics-valid observations: the 100 kPa baseline, four initialization points,
four refinement points, two lower-bound-extension points, and eight broad
continuation points. Two lower-bound candidates at `mu≈0.273` failed the strict
zero particle-center penetration gate and are explicitly excluded from the
surrogate observations.

The independently replayed Newton-native incumbent is `E=70.46 kPa`
(`log10(E)=4.847943757`), `nu=0.237231507`, and `mu=0.305497980`. Its discovery
objective was `8.823 mm` (`2.643 mm` loaded RMSE; `12.360 mm`
residual-footprint RMSE); its fresh replay scored `8.815 mm` (`2.641 mm` loaded;
`12.348 mm` residual-footprint), a `0.008 mm` difference. This is repeatable
local objective improvement of `3.875 mm` over the `12.698 mm` baseline, not
optimizer convergence, material calibration, or a predictive claim outside the
fixed domain. NVS geometry and pre-traversal decision utility remain untested.
Evidence is under `outputs/validity_experiment/newton_bayesopt/`.

### Time-aligned 3 kg held-out result

The runners now derive and assert loaded/residual timing from the supplied
Chrono manifest; A1 records `2.417 s` loaded and `0.25 s` residual in both
Chrono and Newton. The frozen 3 kg A1 episode has the same geometry, location,
SCM grid, guide, and initial map as A0 (exact equality on 14,161 valid cells).
The 1.5 kg-selected incumbent passes fresh preparation but is rejected by the
strict penetration gate (31 sampled centers; `1.332 um` maximum), so it has no
valid 3 kg objective. The unchanged 100 kPa / `nu=0.2` / `mu=0.68` baseline
passes all mechanics gates at the same aligned time and scores `16.289 mm`
(`4.884 mm` loaded RMSE; `22.810 mm` residual-footprint RMSE). Thus the public
Newton domain supports the 3 kg action, but the selected 1.5 kg material point
does not transfer as a mechanically usable high-load candidate. This is a
bounded transfer failure, not calibration or NVS evidence; see
`diagnostics/newton_mass3kg_holdout_20260922/`.

A controlled `0.5 ms` backend A/B now uses the same action, grid scale,
particle spacing, fixed times, support, and score. At the nominally matched
`E=100 kPa`, `nu=0.2`, density `1000 kg/m^3`, and friction pair
`mu=0.68`/`phi=atan(mu)=34.216 deg`, corrected Newton scores `12.189 mm`
versus Genesis `14.736 mm`. The correction improves Newton by `0.449 mm`
(`3.6%`). Genesis is about 16% faster in the original matched comparison.
The calibrated Genesis incumbent still has the best absolute score at
`8.705 mm`; Newton remains uncalibrated. A reverse transfer of that incumbent
to Newton failed preparation before contact with H0 RMSE/max
`9.809/10.241 mm`.

The first Newton-specific calibration probe changed only stiffness from 100 to
25 kPa. Its full preparation matrix passes, and its DEM-only objective improves
to `11.207 mm`, but the response is invalid: as many as `1,330` particle
centers enter the analytic cylinder by up to `5.950 mm`, and the guide gate
also fails. The raised proxy leaves an uncollided lower slice once a softer
cylinder actually sinks. Therefore the inset is a useful support-location
diagnostic, not a promotable forward model. Stop material calibration and
large evaluation until support is corrected without shrinking analytic
collision coverage. Exact evidence is in
`diagnostics/newton_collider_support_20260908/` and
`diagnostics/newton_calibration_20260910/`.

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

This working tree is the Newton branch. The Genesis results above remain the
frozen comparison baseline; they are not Newton observations. Newton 1.5.1 and
Warp 1.17.0 run in the isolated Python 3.11.15 environment at
`/data/christoa/conda/envs/newton_splat`.

The replacement full-bed PIC preparation matrix at a common 2 s horizon is:

| timestep | tolerance | final p99 speed | H0 RMSE / max | result |
| ---: | ---: | ---: | ---: | --- |
| `0.5 ms` | `1e-4` | `0.000853 mm/s` | `1.145 / 1.214 mm` | accepted |
| `0.25 ms` | `1e-4` | `0.00395 mm/s` | `1.123 / 1.177 mm` | accepted |
| `0.125 ms` | `1e-4` | `0.00735 mm/s` | `1.092 / 1.145 mm` | accepted |
| `0.25 ms` | `1e-5` | `0.00395 mm/s` | `1.123 / 1.177 mm` | accepted; identical to `1e-4` |

The adjacent-timestep DEM differences are `0.0232 mm` RMSE for
`0.5 -> 0.25 ms` and `0.0312 mm` for `0.25 -> 0.125 ms`, with at most
`0.0416 mm` maximum error. All predeclared preparation gates pass. The prior
APIC rejection was an upward top-layer mode; PIC is now the qualified default.

The corrected continuous-state cylinder run loads the exact guided 1.5 kg
action for `3.595 s`, removes it, and runs `0.25 s` residual. The original
`0.508 mm` penetration was explained by the default 32-facet collider inset
plus the `0.01 voxel` projection allowance. A 128-segment circumscribed mesh,
zero cylinder threshold, forward-consistent guide, and recorded `10 um` guard
produce zero analytic center penetration through the full trace. The loaded
sinkage is `8.854 mm`; raw all-cell Chrono RMSE is `2.396 mm` loaded and
`2.646 mm` residual. This run is mechanics-qualified but uncalibrated.
The fixed smoke material used for this qualification is `1000 kg/m^3`,
`E=100 kPa`, `nu=0.2`, and Newton friction coefficient `0.68`; these are
engineering diagnostic values, not transferred Genesis values.

The Newton particle arrays are archival/output artifacts, not restart
checkpoints: reconstituting a solver from the saved arrays caused another
`1.157 mm` signed bulk settlement. Preparation and response must remain in one
solver process until grid and warm-start state are either serialized or a
restart requalification is demonstrated.

Large qualified evidence is under
`outputs/validity_experiment/newton/preparation_pic_convergence_20260906/` and
`outputs/validity_experiment/newton/cylinder_qualified_20260906/`; the tracked
summary is `diagnostics/newton_failure_resolution_20260906/`.

The Newton branch may reuse the qualified Chrono oracle, cylinder action and
timing, valid mask, map projection, score definition, visualization, diagnostic
layout, and external output contract. It must not reuse Genesis `F`/`C`/`Jp`
state, prepared-bed acceptance, material observations, optimizer seeds, or
calibrated parameters as if they were solver-independent. In particular,
Newton's friction coefficient is not silently interchangeable with the Genesis
friction angle.

The Newton acceptance ladder is now:

1. complete: pin Newton and Warp separately and record exact versions;
2. complete: reproduce the frozen geometry and qualify fresh cylinder-free
   states with static containment;
3. complete: PIC preparation passes timestep, tolerance, speed, and DEM gates;
4. complete: full two-way loading/removal passes the strict penetration gate;
5. complete: loaded/residual maps, masks, timing, gates,
   traces, raw states, PLYs, and provenance are emitted externally;
6. complete: native coupling and the 100 kPa raised-proxy diagnostic pass the
   full response matrix and are compared with the unchanged Chrono oracle;
7. complete diagnostic: a 25 kPa stiffness probe passes preparation but fails
   analytic penetration and guide gates, proving the raised proxy is not
   promotable;
8. complete diagnostic: full-volume, cylinder-only `-0.25`-voxel S2 activation
   passes every mechanics gate, but its three-level response matrix is not
   demonstrated because coarse/medium sinkage is `0.975 mm`;
9. pending: diagnose that remaining sinkage sensitivity under the unchanged
   contract before calibration/evaluation.

The response-convergence experiment uses this frozen contract:

1. run the full continuous preparation, `3.595 s` guided load, instantaneous
   removal, and `0.25 s` residual at `0.5`, `0.25`, and `0.125 ms`;
2. change timestep only; keep the smoke material, PIC transfer, `1e-4` solver
   tolerance, geometry, 128-segment circumscribed collider, zero projection
   threshold, `10 um` guard, action, observation times, surface projection,
   and oracle valid mask unchanged;
3. require each case to preserve accepted preparation, finite values, all
   `14,161` valid cells, and zero analytic particle-center penetration;
4. compare `loaded - initial` and `residual - initial` DEM fields on the common
   valid mask, preventing the small accepted H0 offsets from contaminating the
   response comparison;
5. require every adjacent timestep pair to have at most `0.5 mm` response-map
   RMSE, `1.0 mm` maximum response-map error, and `0.5 mm` loaded cylinder
   sinkage difference. Record signed error, endpoint cylinder velocity,
   residual particle speed, contacts, impulses, and the fine/coarse trend, but
   do not use those reported diagnostics as post-hoc gates.

Chrono loaded/residual RMSE must be reported for every case, but it measures
uncalibrated material fit and cannot rescue or reject the numerical-convergence
decision.

The clean matrix from commit `73eb472` is complete. All cases retain accepted
preparation, finite output, all `14,161` cells, and zero penetration, but the
matrix status is `not_demonstrated`. Sinkage is `8.854`, `-0.578`, and
`-5.607 mm`. The coarse pair has loaded/residual response RMSE
`1.349/1.373 mm` and sinkage difference `9.432 mm`; the fine pair has
`0.105/0.084 mm` map RMSE but still differs by `5.029 mm` in sinkage.

At steady contact, collected impulse divided by timestep is approximately the
correct `14.715 N` weight at every level, while endpoint velocity is nearly
`-g*dt`. Advancing position with that pre-impulse velocity accumulates
approximately `g*T*dt`: predicted adjacent displacement is `8.817/4.409 mm`,
close to the measured `9.432/5.029 mm`. This localizes the blocker to the
explicit guide update rather than preparation or external DEM I/O. Make one
timestep-consistent guide-integration correction and rerun the unchanged
matrix. This paragraph records the superseded explicit-coupling diagnosis.

That controlled correction is complete. The native path uses a world-anchored
prismatic Kamino body, two lagged proxy iterations, four rigid substeps, and
the unchanged implicit MPM solve. All three rows pass preparation,
finite/full-support I/O, zero-center penetration, and the new `1e-6` guide
gate. The subsequent 9.375 mm raised-proxy diagnostic passes the complete
response matrix: adjacent loaded/residual RMSE is `0.130/0.123 mm` and
`0.107/0.110 mm`, and sinkage differences are `0.130/0.032 mm`.

The inset is not promotable. At 25 kPa, a qualified preparation leads to 1,330
particle centers inside the analytic cylinder by up to `5.950 mm` and a guide
failure.  The subsequent full-volume activation experiment retains collision
coverage and passes all individual mechanics gates, but its coarse/medium
sinkage difference is `0.975 mm`, above the frozen `0.5 mm` gate.  Freeze
material and external I/O until that sensitivity is diagnosed; do not relax
the gates.

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
- Newton preparation runner:
  `tera_splat/scripts/run_newton_prepared_bed.py`
- Newton preparation convergence analyzer:
  `tera_splat/scripts/analyze_newton_preparation_convergence.py`
- Newton guided-cylinder diagnostic:
  `tera_splat/scripts/run_newton_cylinder_diagnostic.py`
- Newton response convergence analyzer:
  `tera_splat/scripts/analyze_newton_response_convergence.py`
- aligned and raw PCD exporter:
  `tera_splat_sim/export_scm_genesis_pcd.py`
- Genesis / Newton environments:
  `chrono_splat` / `/data/christoa/conda/envs/newton_splat`
- Newton convergence/coupling evidence:
  `/data/christoa/Chrono/tera_splat/outputs/validity_experiment/newton/`
- generated calibration outputs:
  `/data/christoa/Chrono/tera_splat/outputs`
- retained incumbent raw/visual evidence:
  `/data/christoa/Chrono/tera_splat/outputs/validity_experiment/bayesopt/A0_oracle_guided_offset_5mm_gate6mm_5mm_n128_incumbent_raw_20260830/study_ykep3esa`
- Chrono oracle outputs:
  `/data/christoa/Chrono/tera_splat_sim/validity_experiment/chrono_episodes`

See [Chrono Oracle Run Contract](chrono-oracle-run-contract.md) for the exact
run rules and [Experiment Problems](experiment_problems.md) for the resolved
and current blockers.

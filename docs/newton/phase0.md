# Phase 0: fresh Chrono-to-Newton residual campaign

Last updated: 2026-10-22
Status: Phase 0 exit demonstrated; sole operational authority for Phase 0

## Comprehensive goal

Phase 0 must establish the smallest credible, leakage-free demonstration that
a mechanics-gated Newton MPM rollout can serve as a useful physical prior for
predicting Chrono-generated terrain deformation under a robot-foot-scale
action, and that one frozen learned displacement residual can improve that
prior on whole positions withheld across more than one training load.

The experiment uses Chrono SCM as reproducible synthetic ground truth and the
unchanged public Newton configuration as a bounded coarse prior. Chrono and
Newton must begin independently from the same freshly generated initial
terrain and receive the same action exactly once. Every admitted case must
retain complete provenance, accepted preparation, finite state, guide
compliance, full surface support, measured interaction artifacts, and positive
local geometric utility. A learned correction may improve an admitted prior;
it may not conceal failed numerical integrity, legalize a gross contact
failure, reuse quarantined state, or gain access to validation or test targets
during fitting or model selection.

The primary learned quantity is a bounded post-rollout particle-displacement
field supervised through Chrono-observable loaded and post-unload surfaces.
Training is performed on complete center/plus-x/minus-x actions, while plus-y
validation and minus-y test actions remain untouched until the corresponding
model is frozen. The final two-load test must show that the unchanged v2 model
improves both raw Newton and the no-deformation baseline in the contact
footprint and twice-foot-radius regions for both observation phases on every
held-out 46 N action. Corrected outputs must preserve all finite particles and
the declared particle-state invariants, reproduce the stored corrected surface,
and retain model, source, input, and split provenance.

Phase 0 exits successfully when all of the following are true:

1. the fresh same-build sentinel has characterized, rather than hidden,
   numerical variation;
2. all six 31/46 N training actions are fresh, usable, and locally informative;
3. v1 remains immutable evidence of held-out spatial transfer at 31 N;
4. v2 is fitted exactly once before either 46 N y holdout exists;
5. the unchanged v2 correction passes every declared local validation and test
   comparison at 46 N and sets
   `multiload_held_out_residual_exit_demonstrated` true;
6. corrected-particle preservation, hashes, fit locks, uncertainty/artifact
   metadata, and raw/robust error views are all auditable.

A successful Phase 0 supports only a bounded sim-to-sim claim: within the
fresh 35 mm, 31--46 N static action domain, a frozen Chrono-supervised residual
adds held-out geometric value to an admitted Newton prior. It does not establish
strict 35 mm mechanics qualification, timestep convergence, real-sand or
material identification, sequential terrain-state prediction, arbitrary load
or geometry transfer, Gaussian-scene accuracy, or planner benefit. The 61 N
rung is optional robustness evidence after the two-load result. Gaussian
updates, novel-view validation, and fixed open-loop planner evaluation are
separate later exits and must consume only Phase 0 states admitted with their
provenance and uncertainty intact.

## Purpose and authority

This is the first document every agent must read before working on the current
Chrono-to-Newton residual campaign. It owns:

- the live action ledger and completion counts;
- the exact next permitted work and ordering locks;
- the current interpretation and claim boundary;
- the chronological evidence added after the fresh-only reset;
- links to frozen protocols, detailed reports, code, and machine-readable
  artifacts.

Do not reconstruct current state from dated reports, output-directory names,
process lists, or older handoff text. When sources differ, use this order:

1. this file for operational status, interpretation, and next work;
2. machine-readable case, matrix, training, and evaluation summaries for
   measurements and completion state;
3. the frozen campaign JSON and runner code for executable behavior;
4. frozen protocols and dated reports for design rationale and provenance.

If a machine-readable artifact changes the current result, update this file in
the same change. No other document should maintain a duplicate live matrix
count or next-step list.

## Current decision

The campaign is a fresh-only, hierarchical Phase 0 test of whether a bounded
Newton MPM prior plus a frozen Chrono-supervised displacement residual improves
held-out local terrain geometry across position and load.

Current state:

- fresh matrix: **10/15 Chrono complete and 10/15 usable Newton**;
- 31 N spatial rung: **5/5 complete**;
- 46 N rung: **5/5 complete**;
- 61 N rung: **0/5 complete and protected**;
- same-build sentinel: complete and retained as variation evidence, not a
  duplicate training row;
- v1 single-load residual: fitted once, frozen, and successful on untouched
  +y validation and -y test actions;
- v2 multi-load residual: fitted exactly once on the six 31/46 N training
  actions before either 46 N y holdout existed, frozen, and successful on the
  untouched +y validation and -y test actions;
- Phase 0 residual exit: demonstrated, with all local held-out comparisons and
  all corrected-particle preservation checks passing;
- strict 35 mm mechanics qualification: not claimed;
- Gaussian update and planner benefit: not yet tested.

All required Phase 0 work is complete. Preserve the completed cases, frozen v1
and v2 models, and evaluation artifacts; do not rerun cases or refit either
model. Decide separately whether to execute the optional 61 N robustness rung.

## Live action ledger

All matrix rows belong to
`static_proxy_hierarchical_v3_20261017`. Sentinel repeats are outside this
15-row count.

| Load | Case | Split | State | Permitted use |
| --- | --- | --- | --- | --- |
| 31 N | `center_f031n` | train | complete, usable | v1 and v2 training |
| 31 N | `xplus100_f031n` | train | complete, usable | v1 and v2 training |
| 31 N | `xminus100_f031n` | train | complete, usable | v1 and v2 training |
| 31 N | `yplus100_f031n` | validation | complete, usable | frozen-v1 evaluation |
| 31 N | `yminus100_f031n` | test | complete, usable | frozen-v1 evaluation |
| 46 N | `center_f046n` | train | complete, usable | v2 training |
| 46 N | `xplus100_f046n` | train | complete, usable | v2 training |
| 46 N | `xminus100_f046n` | train | complete, usable | frozen-v2 training |
| 46 N | `yplus100_f046n` | validation | complete, usable | frozen-v2 evaluation |
| 46 N | `yminus100_f046n` | test | complete, usable | frozen-v2 evaluation |
| 61 N | `center_f061n` | train | protected, absent | later robustness decision |
| 61 N | `xplus100_f061n` | train | protected, absent | later robustness decision |
| 61 N | `xminus100_f061n` | train | protected, absent | later robustness decision |
| 61 N | `yplus100_f061n` | validation | protected, absent | later robustness decision |
| 61 N | `yminus100_f061n` | test | protected, absent | later robustness decision |

Canonical live ledger:

`outputs/validity_experiment/newton/static_proxy_hierarchical_v3_20261017/matrix/matrix_summary.json`

## Exact next work

Required Phase 0 execution is complete. Do not regenerate the 10 completed
matrix cases or retrain v1 or v2. Preserve the model hashes, pre-holdout fit
records, held-out evaluations, corrected states, and source/artifact hashes.

The active next-phase goal and sole Phase 1 exit contract is
[phase1.md](phase1.md). It defines bounded, parameter-conditioned neural
bed-state prediction and supersedes older roadmap phase numbering for new work.

### Optional 61 N robustness decision

The 61 N rung remains protected and absent. Execute it only under a new,
explicit robustness decision that preserves the unchanged v2 model and keeps
the 61 N result outside the already-complete two-load exit. Do not use 61 N
validation or test evidence to alter the frozen Phase 0 model.

### Later exits

Gaussian updates, novel-view evaluation, and fixed open-loop planner testing
are separate work. They must consume only admitted Phase 0 states with their
provenance and uncertainty intact and cannot retroactively change this exit.

## Frozen campaign contract

### Fresh-only evidence boundary

No pre-2026-10-17 Chrono episode, particle bed, Newton preparation, Newton
response, surface map, or saved state is admissible for current qualification,
training, validation, or test claims. Older artifacts are historical
failure-mode context only.

Every action starts independently from a fresh accepted Chrono H0, generates a
fresh 5 mm metric particle bed to 0.10 m depth, and performs fresh in-process
Newton preparation. Saved Newton particle arrays are archival/interchange
outputs, not restart checkpoints.

Frozen sources:

- protocol: [fresh-hierarchical-phase0-20261017.md](fresh-hierarchical-phase0-20261017.md);
- machine contract: `configs/static_proxy_hierarchical_v3_20261017.json`;
- matrix runner: `scripts/run_fresh_phase0_matrix.py`;
- v1 learner: `scripts/run_phase0_residual_pilot.py`;
- v2 wrapper: `scripts/run_phase0_multiload_residual_pilot.py`.

### Newton prior

| Item | Fixed value |
| --- | --- |
| proxy | vertically guided 35 mm-radius foot cylinder |
| material | unchanged 100 kPa baseline, `nu=0.2`, `mu=0.68` |
| voxel size | 7.8125 mm |
| transfer / integration | PIC / PIC |
| bases | P0 strain / S2 collider / Q1 velocity |
| contact | public stock Newton contact |
| coupling | 8 proxy iterations / 16 rigid substeps |
| timestep | 0.25 ms |
| support | 14,161-cell Chrono interior mask |
| observation | Chrono-accepted loaded state and 0.25 s post-removal state |

Do not delay the residual test for another broad material search. Historical
Newton A0 tuning is not transferable evidence for the 35 mm foot.

### Hierarchical gates

1. **Provenance and variation:** complete hashes, commands, revisions,
   environment, and device identity. Exact repeat equality is diagnostic, not
   required.
2. **Numerical integrity:** accepted preparation, finite arrays, guide pass,
   full 14,161-cell output, and adequate initial support. This is a hard gate.
3. **Interaction artifacts:** measure depth, affected fraction, persistence,
   and loaded-state overlap. Only the frozen gross-interaction guard blocks
   use; usable responses with smaller overlap remain explicitly not strictly
   mechanics-qualified.
4. **Geometric prior utility:** require positive MSE skill versus no
   deformation in both the footprint and twice-radius region for loaded and
   post-unload states.
5. **Residual exit:** on whole held-out validation and test actions, the frozen
   correction must improve over raw Newton and no deformation in both local
   regions.
6. **Gaussian and planner exit:** later work only; surface or particle results
   cannot satisfy it.

Historical `bounded_static_prior_v2_20261016` is not the current admission
policy. It remains useful provenance for why strict mechanics and coarse-prior
use must be reported separately.

## Established evidence

### Same-build sentinel

Two centered 31 N paths completed sequentially. Chrono maps and independently
generated beds matched exactly. Newton was compatible but non-bitwise:

| State / region | Repeat RMSE | Maximum difference |
| --- | ---: | ---: |
| loaded footprint | 0.0083 mm | 0.0262 mm |
| loaded local 2r | 0.0050 mm | 0.0293 mm |
| post-unload footprint | 0.0090 mm | 0.0216 mm |
| post-unload local 2r | 0.4262 mm | 10.5521 mm |

The last row is dominated by one highest-particle/raster-bin switch. Raw and
robust views are both retained. The sentinel shows same-build usability and
positive coarse-prior signal; it is not a training duplicate or a portability
claim.

Canonical evidence:

`outputs/validity_experiment/newton/static_proxy_hierarchical_v3_20261017/repeatability/repeatability_summary.json`

### Frozen v1 single-load result

V1 trained only on the three 31 N center/plus-x/minus-x actions before either
y holdout existed. Model SHA-256:

`242fa879c1d7eda443f4277d82a41dcfea5828cdb7b66ccae357b633d99a15af`

| Holdout | State | Raw footprint / 2r RMSE | Corrected footprint / 2r RMSE |
| --- | --- | ---: | ---: |
| +y validation | loaded | 5.784 / 3.971 mm | 2.077 / 2.211 mm |
| +y validation | post-unload | 5.665 / 3.820 mm | 2.267 / 2.335 mm |
| -y test | loaded | 5.706 / 3.936 mm | 2.158 / 2.252 mm |
| -y test | post-unload | 5.601 / 3.791 mm | 2.359 / 2.382 mm |

All four local checks pass on both holdouts. Corrected states retain all
307,461 finite particles, preserve x/y and velocity exactly, and reproject to
the learned field at stored precision. Post-holdout training refuses by
construction. This demonstrates single-load spatial transfer, not load
generalization, Gaussian fidelity, or planner benefit.

### Complete 46 N prior evidence

| Case | Loaded footprint / 2r RMSE | Loaded skill | Post-unload footprint / 2r RMSE | Post-unload skill |
| --- | ---: | ---: | ---: | ---: |
| center | 13.340 / 8.226 mm | 0.608 / 0.419 | 10.160 / 6.666 mm | 0.773 / 0.618 |
| +x | 13.912 / 8.659 mm | 0.580 / 0.370 | 10.275 / 6.337 mm | 0.771 / 0.663 |
| -x | 14.095 / 8.698 mm | 0.563 / 0.358 | 10.385 / 6.382 mm | 0.763 / 0.654 |
| +y validation | 13.628 / 7.999 mm | 0.603 / 0.519 | 10.325 / 6.136 mm | 0.772 / 0.717 |
| -y test | 13.852 / 8.083 mm | 0.584 / 0.492 | 10.252 / 6.078 mm | 0.772 / 0.713 |

All five cases pass numerical integrity and all four local positive-skill
checks. Recorded microscopic contact artifacts remain below the frozen gross
limits; these cases are usable but explicitly not strictly
mechanics-qualified.

### Frozen v2 multi-load result

V2 trained exactly once on 7,356 samples from the six complete 31/46 N
center/plus-x/minus-x actions. The training record proves that neither 46 N y
holdout nor any 61 N action existed at fit time and that no validation or test
target was used for fitting or selection. Model SHA-256:

`cc31209737d69a059f64627e19d9c9f76b2ba1e36be86f528802470d05b0c23f`

| Holdout | State | Raw footprint / 2r RMSE | Corrected footprint / 2r RMSE |
| --- | --- | ---: | ---: |
| +y validation | loaded | 13.628 / 7.999 mm | 1.263 / 1.876 mm |
| +y validation | post-unload | 10.325 / 6.136 mm | 1.284 / 2.077 mm |
| -y test | loaded | 13.852 / 8.083 mm | 1.226 / 1.736 mm |
| -y test | post-unload | 10.252 / 6.078 mm | 1.240 / 1.871 mm |

The unchanged model improves raw Newton and no deformation in both local
regions and both phases on both holdouts. The evaluation sets
`multiload_held_out_residual_exit_demonstrated` and
`all_corrected_particle_preservation_checks_pass` true. Each corrected state
retains all 307,461 finite particles, preserves x/y, velocity, and all declared
non-position particle arrays, reconstructs z within float32 precision, and
reprojects exactly to its stored surface. Model, training record, sources,
inputs, corrected outputs, and generated artifacts are hash-audited.

## Residual representation boundary

The Newton runner names position, velocity, velocity gradient, elastic
deformation gradient, plastic Jacobian, Cauchy stress, and total deformation
transform arrays. In the first three training actions, the non-kinematic
latent arrays were placeholders: stress and velocity gradient were zero,
elastic strain and transform were identity, and plastic Jacobian was one.

V1 and v2 therefore use observable initial alignment, Newton surface response,
particle positions, action-relative coordinates, force, and phase. Do not
present the placeholder result as evidence that physical latent features are
unhelpful. Latent-state ablation requires an informative export path first.

The learned output is a bounded vertical displacement field lifted to
particles with a depth taper. Corrected deformation for later Gaussian work
must be derived compatibly from the displacement gradient; do not invent an
independent particle orientation label.

## Claim boundary

Supported now:

- the fresh Chrono-to-Newton path is provenance-complete and numerically usable
  on 10 actions spanning all five positions at 31 N and 46 N;
- the unchanged Newton prior carries positive local geometric signal on those
  actions despite recorded microscopic contact artifacts;
- immutable v1 improves untouched spatial validation and test actions at 31 N;
- v2, frozen before the 46 N y holdouts existed, improves every declared local
  validation and test comparison at 46 N over both raw Newton and no
  deformation;
- corrected held-out particle states, fit locks, uncertainty/error views, and
  source/input/output provenance are auditable and pass their declared checks.

Not supported now:

- strict 35 mm Newton mechanics qualification or timestep convergence;
- correction outside the tested 31--46 N, 35 mm static-action domain;
- a valid 61 N action domain;
- real-sand fidelity or material identification;
- sequential terrain-state prediction;
- Gaussian/NVS improvement;
- planner improvement or safe locomotion.

Chrono is synthetic ground truth for this experiment. Newton particle state is
a privileged simulator input, not a Chrono label.

## Chronological evidence

Entries are append-only and ordered by evidence date. Detailed pre-reset
Newton history is indexed by
[experiment-consolidated-20261008.md](experiment-consolidated-20261008.md) and
[historical-evidence-20261004.md](historical-evidence-20261004.md).

### 2026-10-08 — Broad parameter-only Newton search stopped

- The A10 stop/go set found no prior A0 candidate that improved the
  incumbent's held-out multi-characteristic profile.
- Newton was retained as a bounded mechanics prior for a learned residual.
- Evidence: [experiment-consolidated-20261008.md](experiment-consolidated-20261008.md)
  and the [hybrid design](../hybrid-chrono-mpm-residual-gaussian-planning-20261008.md).

### 2026-10-09 — Historical 35 mm strict sentinel failed

- The centered 31 N proxy passed preparation, finite, guide, support, and
  loaded-state clearance but failed trajectory-wide strict zero penetration.
- This evidence is quarantined from the fresh campaign.
- Evidence: [static-proxy-qualification-20261009.md](static-proxy-qualification-20261009.md).

### 2026-10-16 — Historical bounded pilot defined and then quarantined

- A separate microscopic-overlap policy admitted historical centered 31/46 N
  data and rejected centered 61 N at the loaded observation.
- The policy established the reporting distinction between strict mechanics
  and coarse-prior use, but its data and thresholds are not current evidence.
- Evidence: [coarse-prior-admission-20261016.md](coarse-prior-admission-20261016.md).

### 2026-10-17 — Fresh-only reset and hierarchy frozen

- All earlier episodes, beds, preparations, and responses were excluded from
  current qualification and learning.
- The 15-action 9/3/3 whole-action split, fresh provenance contract, and
  Level 0-5 evidence hierarchy were fixed.
- Evidence: [fresh-hierarchical-phase0-20261017.md](fresh-hierarchical-phase0-20261017.md).

### 2026-10-17 — Exact equality changed from gate to diagnostic

- Before fresh execution, the protocol was corrected so non-bitwise but
  compatible repeats measure uncertainty rather than automatically blocking
  useful geometric evaluation.
- Incomplete, unaccepted, non-finite, environment-incompatible, and
  structurally incompatible results remain hard stops.

### 2026-10-17 — Sentinel completed and matrix expansion opened

- Chrono and bed repeats matched exactly; Newton showed small compatible
  variation plus one raw raster-cell outlier.
- Both Newton paths had microscopic transient overlap and positive local skill.
- Decision: preserve raw uncertainty, do not duplicate the sentinel in
  training, and begin the five-position 31 N rung.

### 2026-10-17 — Canonical 31 N center action completed

- `center_f031n` passed integrity and all four local positive-skill checks.
- Decision: continue the remaining training positions before fitting.

### 2026-10-18 — 31 N plus-x and minus-x training actions completed

- Both off-center actions retained positive local skill and explicit
  approximately 39 mm post-unload maximum-error tails.
- The three-action training slice completed; latent export placeholders were
  documented rather than used as features.

### 2026-10-18 — V1 was fixed and fit before holdouts

- A dependency-light, action-aligned one-hidden-layer residual was frozen and
  trained on 3,678 samples from center/plus-x/minus-x only.
- Training-only improvement was recorded as fit sanity, not generalization.

### 2026-10-18 — Untouched 31 N validation and test passed

- The unchanged v1 model improved raw Newton and no deformation in the
  footprint and twice-radius regions for loaded and post-unload states on +y
  validation and -y test.
- Decision: mark single-load spatial residual exit demonstrated and preserve
  v1 as immutable evidence.

### 2026-10-18 — V2 contract frozen before 46 N evidence

- V2 retained the v1 architecture, seed, bounds, optimizer, and particle lift.
- Its fit lock refuses training after either 46 N y holdout or any 61 N case
  exists.
- Decision: generate all three 46 N training actions, fit v2, then expose the
  two y holdouts.

### 2026-10-18 — Centered 46 N action completed

- `center_f046n` retained positive coarse-prior skill at the second load.
- Decision: continue off-center training without retuning Newton or v2.

### 2026-10-19 — Plus-x 46 N action completed

- `xplus100_f046n` passed integrity and local skill with a recorded loaded-state
  microscopic contact artifact.
- Decision: the ledger is 7/15; run only `xminus100_f046n`, then fit/freeze v2
  before either y holdout.

### 2026-10-19 — Final 46 N training action completed and v2 frozen

- `xminus100_f046n` passed integrity and all four local positive-skill checks,
  completing the six-action 31/46 N training set.
- V2 was fit exactly once on 7,356 training samples while both 46 N y holdouts
  and every 61 N action were absent. No validation or test target was used for
  fit or selection.
- The frozen model SHA-256 is
  `cc31209737d69a059f64627e19d9c9f76b2ba1e36be86f528802470d05b0c23f`.
- Decision: preserve v1, freeze v2, and expose the untouched 46 N y holdouts
  without retuning.

### 2026-10-21 — Untouched 46 N validation and test passed

- `yplus100_f046n` and `yminus100_f046n` completed fresh after the v2 fit;
  both retained positive raw-prior skill and passed every frozen admission
  gate.
- The unchanged v2 model improved raw Newton and no deformation for loaded and
  post-unload surfaces in the footprint and twice-radius regions on both
  holdouts.
- Corrected particle preservation, surface reproduction, fit locks, raw and
  robust error views, and model/source/input/output hashes pass their audits.
- Decision: set `multiload_held_out_residual_exit_demonstrated` true, record
  the matrix at 10/15, and declare the required Phase 0 exit complete. Keep the
  61 N rung optional and protected.

## Document and artifact routing

| Need | Source |
| --- | --- |
| live status, next work, chronology, claims | this file |
| active Phase 1 goal and exit contract | [phase1.md](phase1.md) |
| frozen fresh campaign design | [fresh-hierarchical-phase0-20261017.md](fresh-hierarchical-phase0-20261017.md) |
| live matrix completion | `.../matrix/matrix_summary.json` |
| sentinel variation | `.../repeatability/repeatability_summary.json` |
| v1 training/evaluation | `.../matrix/residual_pilot_v1/` |
| v2 training/evaluation | `.../matrix/residual_pilot_v2_multiload/` |
| frozen Phase 0 completion report | [phase0-completion-20261022.md](phase0-completion-20261022.md) |
| cross-backend repository context | [../current-state.md](../current-state.md) |
| Newton numerical domain | [fixed-domain.md](fixed-domain.md) |
| historical Newton campaign | [experiment-consolidated-20261008.md](experiment-consolidated-20261008.md) |
| hybrid/Gaussian/planner destination | [../hybrid-chrono-mpm-residual-gaussian-planning-20261008.md](../hybrid-chrono-mpm-residual-gaussian-planning-20261008.md) |
| Chrono/robot/RGB-D/planner repository | [tera_splat_sim docs](../../../tera_splat_sim/docs/README.md) |

The output paths in the table are rooted at:

`outputs/validity_experiment/newton/static_proxy_hierarchical_v3_20261017/`

## Maintenance contract

Whenever evidence changes Phase 0:

1. update the live ledger and counts here from machine-readable summaries;
2. update the exact next permitted work and locks;
3. append one chronological entry with question, frozen contract, evidence,
   decision, claim boundary, and canonical artifacts;
4. update the supported/not-supported claims if warranted;
5. keep frozen protocols and dated reports unchanged except for a forward
   pointer when necessary;
6. do not add live counts or competing next-step lists to another document.

Use the Newton environment:

`/data/christoa/conda/envs/newton_splat`

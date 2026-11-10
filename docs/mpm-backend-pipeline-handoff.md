# MPM-backbone experiment handoff

Last updated: 2026-11-10

Status: executable design and agent handoff; no alternate backend is qualified
by this document alone

The live branch-specific authority is now
[the alternate MPM goal](mpm/goal.md), and all running experiment evidence
belongs in [the alternate MPM running record](mpm/running.md). This document is
retained as the design handoff and provenance source.

## Purpose

This document tells a new agent how to evaluate another Material Point Method
(MPM) environment through the same leakage-safe, one-action terrain pipeline
used for the Newton Phase 1 study. The MPM rollout is mandatory. The two
eligible outcomes are:

1. a qualified raw MPM predictor; or
2. a qualified MPM predictor followed by an offline neural residual.

A direct neural predictor without an MPM rollout is a required fairness
baseline, but it is not an eligible final model for this work. Do not replace a
weak MPM result with the completed Newton-free D1 wrapper and describe the
result as an MPM-backed model.

This is an implementation contract, not evidence that Genesis, Warp MPM,
Taichi MPM, or any other environment is already qualified. Each backend must
earn its own numerical, preparation, contact, state-export, and predictive
admission.

## Read this first

The completed Newton result is summarized in
[the Phase 1 completion record](newton/phase1-completion-20261110.md). The full
scientific contract and chronology remain in [Phase 1](newton/phase1.md) and
[the implementation record](newton/phase1-running.md). The existing
cross-backend assessment is in
[the hybrid model design](hybrid-chrono-mpm-residual-gaussian-planning-20261008.md#backend-assessment).

The critical completed result is:

| Model | Uses an MPM rollout? | Earlier protected median RMSE: loaded footprint / 2r; post footprint / 2r, mm | Interpretation |
| --- | --- | ---: | --- |
| D0 | no | 1.825 / 1.856; 1.825 / 1.855 | strongest earlier model, but not eligible as the final model here |
| R0 | Newton surfaces | 3.161 / 2.859; 3.595 / 3.369 | no Newton added value |
| R1 | Newton surfaces plus robotics-facing fields | 3.309 / 2.964; 3.815 / 3.395 | no mechanics-field value |
| R2S | R1 plus stress | 3.304 / 2.949; 3.869 / 3.406 | no stress-field value |
| R2E | R1 plus elastic fields | 3.574 / 2.988; 4.045 / 3.492 | no elastic-field value |

The later direct-v4 D1 model passed all 25 fresh protected gates at about
1.83--1.93 mm median RMSE, but it consumes no Newton field. The lesson is not
to omit an MPM backbone. It is to require capacity-controlled direct and MPM
baselines so that a new backend cannot receive credit merely for being present.

## Non-negotiable scientific rules

- Every promotable candidate must run the selected MPM backend from the
  episode's initial bed and action. Cached MPM outputs are allowed only when
  their exact hashes are bound into the plan.
- The Chrono SCM episode is the synthetic target. It is not real-soil truth.
- Chrono loaded or post-unload target arrays must never enter MPM preparation,
  MPM time selection, normalization, fitting inputs, or model selection.
- The MPM observation times are fixed independently of the Chrono event time.
  Use 0.35 s loaded and 0.25 s after removal unless a new prospective contract
  freezes a different pair before targets are generated.
- The initial surface, action, units, axes, and observation checkpoints must be
  common across Chrono and the candidate backend.
- A neural residual may correct only an admitted MPM rollout. It may not rescue
  a nonfinite, nonconverged, unsupported, or grossly invalid MPM episode.
- Material parameters are backend-native. Do not copy a Newton friction
  coefficient into a friction-angle API, copy Genesis internal state into
  another solver, or call cross-backend parameters physically equivalent
  without a separate translation study.
- Preserve failed runs and superseded plans. Never overwrite them with a retry.
- Fit normalization on training episodes only. Select checkpoints and calibrate
  uncertainty on validation only. Open a fresh protected set only after all
  model and threshold choices are frozen.
- Existing Phase 1 protected targets have been revealed. They are diagnostic
  data for future design and cannot serve as unbiased confirmation again.

## Fixed one-action benchmark

Use the completed successor domain for the first backend comparison unless the
new environment cannot represent it:

| Quantity | Contract |
| --- | --- |
| action | single gravity-equivalent vertical load; no tangential motion or rotation |
| tool | vertically guided cylinder, radius and height 0.035 m |
| center | closed disk of radius 0.1 m around the bed origin |
| normal force | 30.65625--45.984375 N |
| bed | 0.6 x 0.6 x 0.1 m, smooth seeded surface, history-free |
| surface grid | 0.005 m spacing |
| surface relief | at most 0.005 m with local slope at most 10 degrees |
| Chrono control | bekker_kphi=1.5e6--2.0e6 N/m^(n+2); other successor SCM values fixed |
| checkpoints | initial, loaded at independently fixed 0.35 s, and post-unload after 0.25 s |
| primary regions | cylinder footprint and twice-radius neighborhood |
| primary target | Chrono loaded and post-unload height maps in metres |

The machine-readable source is
[phase1_one_action_successor_contract_v1.json](../configs/phase1_one_action_successor_contract_v1.json).
Treat its Newton section as the historical backend implementation, not as
universal MPM settings.

For an initial alternate-backend fit, the existing 48 training and 16
validation Chrono episodes may be reused. Generate new MPM responses for those
same episode identities. A clean claim then requires a newly frozen protected
design, recommended as 24 test episodes plus six parameter-sensitivity
episodes. Do not use the old 24+6 targets for authoritative confirmation.

## Backend starting points

Choose one backend per study. Never combine observations from different MPM
environments in one admission summary or pretend that their state variables
share semantics because they have similar names.

| Backend | Repository starting point | First unresolved task |
| --- | --- | --- |
| Newton | the reference scripts listed below and the completed Phase 1 evidence | use as the behavior/schema reference; do not rerun it as though it were a fresh alternate-backend claim |
| Genesis | [Chrono-Genesis bridge](../scripts/run_chrono_genesis_bridge.py), [prepared-ground solver](../scripts/run_genesis_ground_plane_solver.py), [BayesOpt driver](../scripts/run_chrono_genesis_bayesopt.py), and [state I/O](../scripts/mpm_state_io.py) | demonstrate preparation and loaded/post-unload response convergence under the one-action contract before training |
| custom Warp MPM | no qualified terrain adapter exists | implement bed preparation, rigid-tool contact, rollout, state export, and all numerical gates |
| Taichi MPM | no repository integration exists | implement the full adapter and qualification stack; autodiff availability is not qualification |
| another MPM | none unless separately documented | inventory its constitutive model, boundaries, contact, restart behavior, determinism, and export APIs before freezing a study |

Genesis is the shortest alternate-backend path because relevant code already
exists, but its historical post-removal response was numerically unresolved.
Do not train a residual until the new Genesis study passes the qualification
ladder below. A custom differentiable backend may eventually support an
in-rollout residual, but the first comparison should still use saved,
independently admitted rollouts so it remains comparable with Newton.

## Candidate ladder and selection policy

Use equal neural capacity, identical splits, train-only normalization, and the
same optimizer budget for learned variants.

| ID | Candidate | Eligible as final? | Question |
| --- | --- | --- | --- |
| N0 | no deformation; initial surface copied forward | no | does any dynamics model help? |
| D0 | direct U-Net from initial surface, action, force, and known Chrono control | no | does MPM conditioning add anything over a capacity-matched learner? |
| M0 | raw candidate-backend loaded and post-unload surfaces | yes | is the MPM backend useful without learning? |
| MR0 | M0 surfaces plus a bounded neural residual | yes | can the minimal MPM geometric prior be corrected? |
| MR1 | MR0 plus occupancy/mass, vertical velocity, contact count, and normal impulse | yes | do robotics-facing MPM fields help? |
| MR2S | MR1 plus qualified mean and von Mises stress | optional | does stress add held-out value? |
| MR2E | MR1 plus qualified elastic Jacobian and isochoric shear | optional | do elastic fields add held-out value? |

The promotion pool is M0, MR0, and MR1. MR2S or MR2E may be promoted only if
that individual field family was qualified before training and improves on MR1
without worsening the failure tail. Do not create one large mechanics bundle
and infer that every included field is useful.

The final selection must remain MPM-backed even if D0 wins. Report the D0
result prominently. If the selected MPM-backed candidate does not beat D0, the
permitted conclusion is "MPM-backed predictor selected by project constraint;
MPM added value not demonstrated." Do not claim MPM added value unless the
frozen protected comparison supports it.

### MPM-only parameter policy

Choose and freeze one of these routes before generating alternate-backend
responses:

- **Fixed backend material:** hold the MPM material and numerics constant, as
  the historical Newton successor did. M0 is then a geometric/action prior and
  cannot support a parameter-conditioned MPM claim. MR0/MR1 may still consume
  the known Chrono control through their neural conditioning.
- **Backend-native parameter schedule:** prospectively define how the known
  experimental control changes parameters with valid semantics in this MPM
  environment. Freeze the mapping using sources and train/validation evidence
  only. M0 may be tested for parameter sensitivity after the mapping and all
  numerical gates are fixed.

Do not pass Chrono `bekker_kphi` into an unrelated MPM parameter slot merely to
make M0 vary. If no defensible mapping exists, use the fixed-material route and
narrow the raw-MPM claim.

## Architecture seam

Keep the oracle, experiment-control, tensor, training, and evaluation layers
backend-neutral. Replace only preparation, rollout, and state export:

```text
frozen episode plan
  + qualified initial height map
  + action and backend-native material configuration
            |
            v
  candidate MPM adapter
    prepare -> settle/qualify -> load -> remove -> export
            |
            v
  canonical backend response
    surfaces + valid support + optional qualified fields + manifest
            |
            v
  canonical tensor bridge
    model_inputs.npz                 targets.npz
    (no Chrono target arrays)        (Chrono only)
            |                              |
            +---------------+--------------+
                            v
       N0 / D0 / M0 / MR0 / MR1 / optional ablations
                            |
                            v
       validation selection -> fresh protected report -> claim routing
```

Do not fork the entire Newton runner and rename strings. Extract or implement a
backend adapter with explicit identity. Newton-specific acceptance keys such as
Kamino, Warp, or SolverImplicitMPM do not belong in a generic interface.

## Backend adapter contract

### Required adapter entry points

Implement these operations, either as subcommands in one runner or as separate
scripts:

```text
plan       freeze source, environment, config, inputs, membership, and hashes
prepare    build a backend-native bed from the exact initial surface
settle     reach and record the backend's accepted no-action prepared state
rollout    apply the frozen cylinder action and remove it at the fixed times
export     write canonical surfaces, state fields, masks, and provenance
analyze    apply numerical, interaction, schema, and leakage gates
```

Each operation must be idempotent for complete hash-matching artifacts and must
fail closed on an incomplete output directory. A retry gets a new attempt
directory and an explicit qualification record.

### Adapter inputs

The adapter receives no Chrono loaded or post-unload array. Its permitted
inputs are:

- episode_id, split, and immutable input hash;
- initial height map and valid support;
- x/y axes, grid spacing, frame, and units;
- cylinder radius, height, center, guide mode, and normal force;
- fixed loaded and post-removal durations;
- backend-native material and numerical configuration;
- device, worker identity, environment lock, and random seed.

The Chrono episode directory may be supplied only to read the initial state,
action metadata, axes, and support. Prefer a sanitized adapter-input archive so
the process cannot accidentally read target filenames.

### Required response directory

Use a backend-specific namespace and this minimum layout:

```text
outputs/validity_experiment/mpm/<study_id>/
  experiment_plan.json
  preparations/surface_<seed>/attempt_<n>/
    backend_prepared_bed_manifest.json
    prepared_state.<backend-format>
    settle_trace.csv
  episodes/<episode_id>/attempt_<n>/
    backend_response_manifest.json
    resolved_backend_config.json
    action.json
    initial_heightmap_m.npy
    loaded_heightmap_m.npy
    post_unload_heightmap_m.npy
    valid_heightmap_mask.npy
    state_initial.npz
    state_loaded.npz
    state_post_unload.npz
    rollout_trace.csv
    logs/
  dataset_summary.json
```

Backend-native restart/checkpoint files may sit beside these files. The
canonical .npy and .npz exports are interchange evidence; they are not
automatically safe restart states.

### Required response manifest

backend_response_manifest.json must contain at least:

- schema version, backend name/version, adapter revision and SHA-256;
- environment lock hash, device identity, worker count, seed, and wall time;
- episode input hash and preparation-manifest hash;
- complete material, solver, grid/particle, contact, boundary, and coupling
  settings with units;
- coordinate frame, axis order, handedness, height datum, and array shapes;
- fixed observation durations and proof that Chrono target time did not control
  them;
- particle/grid counts and preparation convergence statistics;
- guide error, contact activation, impulse, penetration/overlap, and affected
  support statistics;
- finite-state checks and per-checkpoint surface coverage;
- state-field names, shapes, dtypes, units, frames, and semantics;
- exact output filenames and SHA-256 hashes;
- accepted, acceptance_eligible, mechanics_qualified, blockers, and the
  complete gate dictionary.

Do not overload accepted. Numerical admission, strict mechanics qualification,
and predictive success are separate decisions.

## Canonical tensor bridge

Write model_inputs.npz and targets.npz separately for every admitted episode.
The required backend-neutral inputs are:

```text
initial_height_m
mpm_loaded_displacement_m
mpm_post_unload_displacement_m
valid_support
action_relative_x_m
action_relative_y_m
action_signed_distance_m
action_footprint
action_phase                 # [2, 4]: x, y, force, checkpoint index
soil_parameters              # known Chrono control(s), not inferred MPM values
```

The only target fields are:

```text
chrono_loaded_height_m
chrono_post_unload_height_m
```

For MR1, export these fields at loaded and post-unload checkpoints:

```text
column_particle_count
column_mass_kg
column_mean_action_velocity_mps
contact_node_count
contact_normal_impulse_ns
```

Optional fields, only after qualification, are:

```text
column_mean_stress_mean_pa
column_mean_stress_von_mises_pa
column_mean_elastic_jacobian
column_mean_elastic_isochoric_shear
```

All spatial arrays must share the Chrono x/y grid and shape. Resampling must
publish its interpolation, conservation behavior, support rule, and frame
transform. Use column sums for conserved extensive quantities such as mass or
impulse and documented mass-weighted means for intensive particle fields.

The existing model code expects legacy names newton_loaded_displacement_m and
newton_post_unload_displacement_m. A thin compatibility loader may alias the
generic MPM fields at runtime. Do not write an alternate backend's artifacts
under a Newton namespace or record backend=newton merely to satisfy that loader.

## Backend qualification ladder

Complete these gates in order. Stop on failure and preserve the evidence.

### 1. Environment and identity

- Pin the backend, compiler/runtime, CUDA, Python, and key dependency versions.
- Record repository revision, dirty state, adapter hashes, device model, and
  command line before runtime.
- Give the backend a new study_id; do not place observations in a Newton or
  Genesis study directory.

### 2. Units, frame, and material translation

- Document length, time, mass, stress, density, force, and impulse units.
- Verify world up, grid indexing, particle coordinate frame, tool frame, and
  output height datum with a tiny deterministic fixture.
- Choose backend-native material values prospectively. Record which parameters
  are merely engineering controls and which, if any, have a justified
  translation.

### 3. Initial-bed construction

- Reproduce the exact 5 mm initial surface on a common flat base.
- Record particle mass, density, spacing, depth, side/bottom boundaries, and
  top-envelope error.
- Require a nonempty common support and freeze the rasterizer before fitting.

### 4. No-action preparation

- Demonstrate finite state, stable particle count/mass, acceptable surface
  drift, and a sustained low-speed settling window.
- Repeat preparation in fresh processes. Quantify variation; do not demand
  bitwise equality from a nondeterministic GPU solver.
- Prove that saved preparation reuse reproduces a fresh preparation within a
  prospectively frozen tolerance before using it to save runtime.

### 5. Contact and action

- Verify the vertical guide and tool geometry independently of the material fit.
- Record contact count activation, upward normal impulse, tool trajectory,
  guide error, and overlap/penetration.
- Reject unsupported free fall, missing interaction, nonfinite contact, gross
  tunneling, or movement outside the frozen action domain.

### 6. Time-step and response convergence

- Run at least a coarse/reference/fine timestep or resolution check on a fixed
  episode before bulk generation.
- Compare loaded and post-unload maps, tool motion, mass, and relevant state
  fields. Freeze a numerical setting only after response differences are below
  predeclared tolerances or explicitly bounded.
- Check the no-action prepared bed over the full rollout duration, not only the
  short settling window.

### 7. State export

- Require exact documented shapes, finite values, stable particle identity when
  claimed, and correct checkpoint semantics.
- A field must have nonzero action signal and acceptable fresh-process repeat
  variation before it enters a neural model.
- Qualify occupancy/mass, velocity, and contact first. Test stress and elastic
  families separately. Exclude plastic or constitutive fields until their
  semantics and numerical behavior are specifically qualified.

### 8. Twelve-episode engineering smoke

- Use eight training and four validation members only.
- Require every Chrono episode, MPM preparation, MPM response, tensor archive,
  and baseline loss to be complete and finite.
- Confirm target/input separation and memory bounds.
- Keep all protected identities and targets locked.

### 9. Full train/validation admission

- Complete exactly 48 training and 16 validation pairs.
- Bind every Chrono, MPM, tensor, manifest, source, and environment hash.
- Do not generate a new response for an admitted smoke member unless a
  prospective retry plan requires it.

## Training and evaluation

The existing neural reference is a capacity-controlled three-level 2D U-Net:
16 base channels, [1,2,4] channel multipliers, two residual blocks per scale,
GroupNorm, SiLU, feature-wise affine conditioning, and separate loaded and
post-unload mean/variance heads. Keep the same capacity across D0, MR0, MR1,
and optional ablations.

Reference optimization settings are batch size 4, at most 300 epochs, patience
35, learning rate 3e-4, weight decay 1e-5, gradient clip 1, three seeds, mixed
precision, and deterministic algorithms. These are starting identities, not
evidence that a backend is good.

The MPM residual is bounded around the backend prediction:

```text
predicted_height = mpm_height + scale * tanh(network_residual)
```

Fit spatial/global normalization and the correction bound on training only.
Select one seed per variant and calibrate nominal-90% uncertainty on validation
only. Freeze selected model hashes, thresholds, fresh protected identities,
and the evaluator before opening protected targets.

### Frozen gates to carry forward

For an MPM-plus-residual claim, retain the Phase 1 gates unless a new plan
prospectively changes them:

- median RMSE at most 0.003 m in loaded/post-unload footprint and twice-radius
  regions;
- at least 30% median RMSE reduction versus raw MPM;
- at least 90% of episodes better than both raw MPM and no deformation;
- no episode worse than raw MPM by more than 10% plus 0.001 m;
- nominal-90% interval coverage between 80% and 100%;
- parameter controls degrade paired performance by at least 2% with a paired
  bootstrap lower bound above zero;
- at least 90% correct protected parameter-sensitivity directions.

For an MPM-only M0 claim, freeze a separate prospective gate before running
the protected set. At minimum it must include absolute RMSE, improvement over
no deformation, a failure-tail limit, coverage/support, numerical admission,
and, only for a frozen backend-native parameter schedule, parameter-sensitivity
direction. A fixed-material M0 cannot support a parameter-conditioned claim.
Do not apply "30% better than raw MPM" to raw MPM itself.

For an MPM-added-value claim, the selected MPM-backed model must additionally
beat capacity-matched D0 by the predeclared protected margin. The historical
contract used 5% on the joint holdout group. If it does not, the model may
still be the project-selected MPM-backed implementation, but the added-value
claim is prohibited.

## Recommended command flow

There is not yet a generic alternate-backend runner. These are the commands an
implementing agent should expose; replace angle-bracket values with frozen
paths and do not run protected stages until the plan allows them:

```bash
python scripts/run_phase1_<backend>_adapter.py --config configs/<study>.json --stage plan
python scripts/run_phase1_<backend>_adapter.py --config configs/<study>.json --stage qualify
python scripts/run_phase1_<backend>_adapter.py --config configs/<study>.json --stage smoke
python scripts/run_phase1_<backend>_adapter.py --config configs/<study>.json --stage bulk

python scripts/train_phase1_mpm_successor.py --config configs/<training>.json --stage plan
python scripts/train_phase1_mpm_successor.py --config configs/<training>.json --stage train --model all
python scripts/train_phase1_mpm_successor.py --config configs/<training>.json --stage select

python scripts/evaluate_phase1_mpm_successor.py --config configs/<evaluation>.json --stage plan
python scripts/evaluate_phase1_mpm_successor.py --config configs/<evaluation>.json --stage unlock
python scripts/evaluate_phase1_mpm_successor.py --config configs/<evaluation>.json --stage open
python scripts/run_phase1_<backend>_adapter.py --config configs/<protected>.json --stage protected
python scripts/predict_phase1_mpm_successor.py --config configs/<evaluation>.json
python scripts/evaluate_phase1_mpm_successor.py --config configs/<evaluation>.json --stage report
```

Reference Newton entry points, useful for behavior and schema but not for
copying backend-specific assumptions, are:

| Purpose | File |
| --- | --- |
| initial metric bed | [phase1_metric_bed.py](../scripts/phase1_metric_bed.py) |
| Newton preparation | [run_newton_prepared_bed.py](../scripts/run_newton_prepared_bed.py) |
| Newton rollout/export | [run_newton_cylinder_diagnostic.py](../scripts/run_newton_cylinder_diagnostic.py) |
| paired episode/tensors | [run_phase1_dataset.py](../scripts/run_phase1_dataset.py) |
| successor smoke | [run_phase1_one_action_successor_smoke.py](../scripts/run_phase1_one_action_successor_smoke.py) |
| successor bulk | [run_phase1_one_action_successor_bulk.py](../scripts/run_phase1_one_action_successor_bulk.py) |
| shared model | [phase1_one_action_successor_model.py](../scripts/phase1_one_action_successor_model.py) |
| train/select | [train_phase1_one_action_successor.py](../scripts/train_phase1_one_action_successor.py) |
| predict | [predict_phase1_one_action_successor.py](../scripts/predict_phase1_one_action_successor.py) |
| report | [evaluate_phase1_one_action_successor.py](../scripts/evaluate_phase1_one_action_successor.py) |

## Runtime policy

Newton's completed response repeated about 10,400 implicit-MPM steps over
roughly 304,865 particles, including 8,000 pre-settle steps. Historical serial
runtime was about 43 minutes per response. Two processes sharing one RTX 5090
completed a pair in about 64.7 minutes, only 1.325x aggregate throughput.

For a new environment:

1. measure one complete serial episode, including preparation and export;
2. benchmark one and two workers on two nonprotected smoke episodes;
3. freeze the worker count that improves throughput without changing admitted
   numerical identity beyond tolerance;
4. qualify preparation reuse per surface seed before enabling it;
5. record stage-level wall time and peak device memory;
6. skip only artifacts whose manifest and hashes are complete and match the
   current plan.

Do not optimize throughput by reducing settling, changing observation times,
sharing unsafe mutable state, or weakening gates after seeing the targets.

## Failure and retry policy

- A failed numerical run has no model score.
- A crash, nonfinite state, missing file, guide failure, or schema failure is
  preserved as an attempt, not silently regenerated in place.
- Freeze retry scope and execution identity before retrying. Record whether the
  retry is serial, missing-only, or uses a changed numerical configuration.
- Mixed worker identities require an explicit qualification and remain visible
  in the final report.
- A source revision change after plan freeze fails closed. A continuation may
  be prospective only if it proves exactly what changed and binds all completed
  artifacts before downstream prediction.
- Never revise a model or threshold using a revealed protected failure and then
  report the same protected set as confirmation.

## Minimum tests

Before runtime, add tests for:

- plan determinism, source/config hashes, and dirty-revision recording;
- protected-target absence and refusal before unlock;
- adapter input sanitization and target-leakage refusal;
- units/frame fixture and height-map orientation;
- incomplete-output refusal and hash-matching idempotency;
- preparation and response manifest schemas;
- finite/shape/support/contact/guide admission;
- generic-to-legacy tensor aliasing without a false backend identity;
- train-only normalization and validation-only selection/calibration;
- equal learned capacity and active-channel masks;
- MPM-presence enforcement in the promotion pool;
- prediction refusal when dataset admission or model identity fails;
- report claim routing, including refusal of an MPM-added-value claim when the
  selected candidate does not beat D0;
- completion audit recomputation from immutable predictions and manifests.

Run focused unit tests first, then a two-episode integration fixture, the 12
episode smoke, and only then the 64 episode train/validation generation.

## Required deliverables

An alternate-backend experiment is not complete until it has:

- a versioned backend/domain contract and target-free episode plan;
- a pinned environment and source/device identity record;
- backend adapter, tests, and a schema document;
- numerical/preparation/contact/convergence qualification;
- a passing 8/4 smoke summary;
- 48/16 admitted train/validation MPM pairs;
- canonical tensor archives with target separation;
- raw MPM metrics and D0 fairness baseline;
- equal-capacity MR0/MR1 results and separately qualified optional ablations;
- a validation-only selection record;
- a prospectively frozen fresh protected plan and open-once marker;
- a locked report containing accuracy, failure tails, parameter controls,
  sensitivity, uncertainty, runtime, and every failed case;
- an explicit claim decision and an independent completion audit;
- an update to the repository documentation index and current state.

## Claim routing

| Evidence | Permitted conclusion |
| --- | --- |
| M0 passes its frozen predictive and numerical gates | qualified raw MPM predictor in the frozen synthetic one-action domain |
| MR0 or MR1 passes but does not beat D0 | MPM-backed neural predictor; MPM added value not demonstrated |
| MR0 or MR1 passes and beats both M0 and D0 by frozen margins | MPM-backed neural correction with demonstrated added value in the frozen synthetic domain |
| optional field variant beats MR1 after field qualification | that specific field family has incremental predictive value |
| only D0 passes | no eligible MPM-backed success; retain D0 as diagnostic evidence |
| numerical/admission gates fail | backend not qualified; no predictive claim regardless of target RMSE |

None of these outcomes establishes real-soil fidelity, constitutive validity,
material identification, sequential rollout closure, planner benefit, or
sim-to-real transfer.

## Agent completion checklist

The implementing agent should report this checklist verbatim with paths and
hashes filled in:

```text
[ ] backend and study_id chosen
[ ] environment/source/device identity frozen
[ ] material/unit/frame translation documented
[ ] adapter input contains no Chrono loaded/post target
[ ] exact initial-bed reproduction passed
[ ] no-action preparation and repeatability passed
[ ] contact/guide/interaction gates passed
[ ] timestep or resolution convergence passed/bounded
[ ] canonical response schema and state fields passed
[ ] 8 train + 4 validation smoke passed
[ ] 48 train + 16 validation pairs admitted
[ ] M0 raw-backbone metrics complete
[ ] D0 fairness baseline complete but excluded from promotion
[ ] MR0/MR1 equal-capacity training complete
[ ] optional fields qualified and ablated separately, or omitted
[ ] validation-only selection and uncertainty calibration frozen
[ ] fresh protected identities and gates frozen before open
[ ] protected MPM runtime and admission passed
[ ] locked prediction/report complete
[ ] claim route states whether MPM added value was demonstrated
[ ] completion audit passed
[ ] docs updated; failed and superseded evidence preserved
```

The next agent should begin with backend selection and a two-episode
qualification fixture. It should not launch the 64-episode MPM run until the
adapter, numerical contract, smoke plan, and protected-data lock are frozen.

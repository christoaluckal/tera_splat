# Alternate MPM backend goal and execution contract

Created: 2026-11-10

Last updated: 2026-11-10

Status: active pre-implementation contract; no alternate backend is qualified

## Authority

This document is the sole live authority for the alternate MPM backend study
on branch `mpm_test`. It defines the goal, scientific boundaries, backend
architecture, ordered qualification work, learned-model comparison, protected
evaluation, completion conditions, and claim routing.

Record all dated implementation and experiment evidence in
[running.md](running.md). The earlier
[MPM-backbone pipeline handoff](../mpm-backend-pipeline-handoff.md) is the
design source for this contract. If that handoff and this document differ for
new `mpm_test` work, this document controls. Completed Newton documents remain
immutable evidence and must not become a second live ledger for this study.

## Goal

Build a backend-neutral, leakage-safe terrain-response pipeline that can run
the same frozen one-action experiment through independently identified MPM
implementations, beginning with a modern Warp implementation derived from the
PhysGaussian solver design and followed by a Taichi implementation behind the
same external contract.

The scientific goal is to determine whether at least one numerically admitted
alternate MPM rollout can support either:

1. a qualified raw MPM surface predictor; or
2. a qualified MPM rollout followed by an offline bounded neural residual.

The engineering goal is a reusable adapter seam that makes preparation,
contact, rollout, state export, and numerical qualification replaceable while
keeping the oracle, experiment design, tensors, training, evaluation, and
claims backend-neutral.

The platform should ultimately support more than one MPM implementation. The
first backend must be qualified before bulk work begins. A second backend may
fail qualification without invalidating a passed first backend; failures are
scientific results and remain preserved. Conversely, having two runnable code
paths is not success if neither passes the numerical and predictive gates.

## Intended backend order

### 1. Warp PhysGaussian-derived MPM

Use the public PhysGaussian/warp-mpm implementation as a design and source
reference for an explicit APIC/MLS-MPM-style particle-grid-particle solver.
Port or adapt it to a pinned current Warp stack rather than silently depending
on its historical Python 3.9, CUDA 11.6, and Warp 0.10.1 environment.

Warp is first because this repository already contains PhysGaussian-derived
configuration, ground-plane, particle, and Gaussian-transfer code. That code
is historical infrastructure, not qualification evidence. The new adapter
must own and test volumetric bed construction, geostatic preparation, guided
rigid-cylinder contact, unload behavior, checkpoint export, and all admission
gates.

### 2. Taichi MPM

Implement a separate Taichi backend only after the canonical adapter and the
two-episode integration fixture are stable. It must use the same physical
episode inputs and canonical outputs but retain its own material, numerics,
contact implementation, environment identity, and qualification evidence.

Taichi is an implementation framework, not a qualified terrain solver by
itself. Autodiff availability, a sand demo, or a visually plausible collapse
does not admit the backend.

### Other backends

Genesis may later be wrapped behind the same adapter, but its historical
response convergence problem remains unresolved and its evidence cannot be
pooled with Warp or Taichi. Newton is the behavior/schema reference from the
completed study, not a fresh alternate-backend claim.

## PhysGaussian relationship

PhysGaussian motivates the particle representation and the eventual
simulation-to-Gaussian bridge. Its useful ideas include:

- a shared particle representation carrying position, velocity, deformation,
  stress, and material state;
- explicit particle-to-grid, grid update, and grid-to-particle evolution;
- optional internal filling so simulated material is volumetric rather than a
  hollow rendering shell;
- deformation-gradient-based updates of Gaussian centers and covariance;
- GPU execution and PyTorch interoperability through Warp.

This study does not inherit the following as established facts:

- visual plausibility is not numerical convergence;
- a reconstructed Gaussian cloud is not automatically a stable terrain bed;
- scene normalization is not the benchmark's metric coordinate frame;
- a plane or scripted boundary collider is not qualified guided-tool contact;
- manually selected graphics material parameters are not identified soil
  properties;
- deformation-gradient or stress availability is not proof that those fields
  are numerically stable or predictively useful;
- Gaussian rendering quality is not part of initial MPM admission.

Gaussian transfer remains downstream. The initial alternate-backend result is
judged on admitted metric surface and state exports before any rendering step.

Primary references:

- [PhysGaussian paper](https://arxiv.org/abs/2311.12198)
- [PhysGaussian implementation](https://github.com/XPandora/PhysGaussian)
- [standalone Warp MPM implementation](https://github.com/zeshunzong/warp-mpm)
- [NVIDIA Warp documentation](https://nvidia.github.io/warp/)
- [Taichi documentation](https://docs.taichi-lang.org/)

## Supported domain

The first comparison uses the completed successor one-action domain:

| Quantity | Contract |
| --- | --- |
| action | one gravity-equivalent vertical load; no tangential motion or rotation |
| tool | vertically guided cylinder with 0.035 m radius and height |
| center | closed disk of radius 0.1 m around bed origin |
| normal force | 30.65625--45.984375 N |
| bed | 0.6 x 0.6 x 0.1 m, smooth seeded surface, history-free |
| surface spacing | 0.005 m |
| surface relief | at most 0.005 m; local slope at most 10 degrees |
| Chrono control | `bekker_kphi=1.5e6--2.0e6`; other successor SCM values fixed |
| checkpoints | initial, loaded at fixed 0.35 s, post-unload after fixed 0.25 s |
| primary regions | cylinder footprint and twice-radius neighborhood |
| primary targets | Chrono loaded and post-unload height maps in metres |

The machine-readable domain source is
[`phase1_one_action_successor_contract_v1.json`](../../configs/phase1_one_action_successor_contract_v1.json).
Its Newton section is historical and must not be interpreted as a Warp or
Taichi configuration.

Use the existing 48 training and 16 validation Chrono episode identities for
initial fitting. Generate new backend responses for those identities. A clean
confirmation requires a newly frozen protected design, recommended as 24 test
episodes plus six parameter-sensitivity episodes. Previously revealed
protected targets are diagnosis-only and cannot confirm a new backend.

## Non-negotiable scientific rules

- Every promotable candidate must execute its named MPM backend from the
  episode's initial bed and action.
- Cached responses are usable only when exact source, environment, input,
  preparation, configuration, and output hashes match the frozen plan.
- Chrono is a reproducible synthetic target, not real-soil truth.
- Chrono loaded and post-unload arrays must never enter MPM preparation,
  settling, time selection, normalization, configuration selection, fitting
  inputs, or model selection.
- Observation times are fixed independently of target events: 0.35 s loaded
  and 0.25 s after removal unless a new prospective contract freezes a change
  before target generation.
- Chrono and each MPM backend share the exact initial surface, action, units,
  axes, and observation checkpoints.
- A neural residual may correct only an admitted MPM rollout. It cannot rescue
  a nonfinite, unsupported, unconverged, or grossly invalid episode.
- Material parameters are backend-native. Warp, Taichi, Genesis, Newton, and
  Chrono parameter names do not imply physical equivalence.
- Preserve failed runs, incomplete attempts, and superseded plans. A retry
  receives a new attempt directory and explicit qualification record.
- Fit normalization on training episodes only. Select models and calibrate
  uncertainty on validation only. Open a fresh protected set once, after all
  model, threshold, source, and environment choices are frozen.
- Report direct-model performance even though a direct model is not eligible
  as this project's final MPM-backed result.

## Backend-neutral architecture

```text
frozen target-free episode plan
  + exact initial height map and support
  + metric action and timing
  + backend-native material/numerical configuration
                  |
                  v
        explicit backend adapter identity
          plan -> prepare -> settle
          rollout -> remove -> export -> analyze
                  |
                  v
       canonical admitted backend response
       surfaces + masks + fields + manifest
                  |
                  v
       backend-neutral tensor bridge
       model_inputs.npz       targets.npz
       MPM and action only     Chrono only
                  |
                  v
       N0 / D0 / M0 / MR0 / MR1 / optional fields
                  |
                  v
       validation selection -> fresh protected report
```

Framework-specific types must not escape into training and evaluation. Warp
arrays, Taichi fields, solver grids, and native checkpoints remain inside the
adapter. Canonical NumPy artifacts and manifests are interchange evidence, not
automatically safe restart states.

## Required adapter operations

Each backend exposes the same logical stages, either as subcommands of one
runner or as focused scripts:

| Stage | Responsibility |
| --- | --- |
| `plan` | freeze source, environment, config, inputs, membership, hashes, and target locks |
| `prepare` | construct a backend-native volumetric bed from the exact initial surface |
| `settle` | reach and record an accepted no-action prepared state |
| `rollout` | apply the frozen guided-cylinder action and remove it at fixed times |
| `export` | write canonical surfaces, state fields, masks, traces, and provenance |
| `analyze` | apply identity, numerical, interaction, schema, convergence, and leakage gates |

Every stage is idempotent only for complete hash-matching output. It must fail
closed when a directory is incomplete, mismatched, or contains an unrecorded
retry.

### Permitted adapter inputs

- episode ID, split, immutable input hash, and random seed;
- initial height map and valid support;
- x/y axes, spacing, coordinate frame, units, and height datum;
- cylinder radius, height, center, guide mode, and normal force;
- fixed loaded and post-removal durations;
- backend-native material, grid, transfer, contact, and boundary settings;
- device, worker identity, source revision, and environment lock.

Prefer a sanitized input archive. If a Chrono episode directory is supplied,
the adapter may read only the initial state, axes, support, and action metadata.
It must reject target filenames and loaded/post-unload Chrono arrays.

## Artifact layout and identity

Use a backend-specific study namespace:

```text
outputs/validity_experiment/mpm/<study_id>/
  experiment_plan.json
  environment.json
  source_identity.json
  preparations/surface_<seed>/attempt_<n>/
    backend_prepared_bed_manifest.json
    prepared_state.<backend-format>
    settle_trace.csv
    logs/
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
  tensors/<episode_id>/
    model_inputs.npz
    targets.npz
    tensor_manifest.json
  dataset_summary.json
```

`study_id` includes the backend identity and prospective contract version.
Never place Warp or Taichi observations in a Newton or Genesis namespace.

The response manifest records at least:

- schema version, backend name/version, adapter revision, and SHA-256;
- repository revision and dirty state;
- complete environment lock hash;
- device, worker count, seed, command, start/end time, and wall time;
- episode input and preparation-manifest hashes;
- complete material, solver, grid/particle, transfer, contact, boundary, and
  coupling configuration with units;
- frame, handedness, axis order, height datum, array shapes, and dtypes;
- observation durations and proof that target timing did not control them;
- particle/grid counts and preparation convergence statistics;
- guide error, contact activation, normal impulse, overlap/penetration, and
  affected-support statistics;
- finite-state, mass/count, support, and surface-coverage checks;
- state-field names, shapes, units, frames, semantics, and aggregation rules;
- exact output filenames and SHA-256 hashes;
- separate `accepted`, `acceptance_eligible`, `mechanics_qualified`, and
  `predictive_qualified` values, blockers, and full gate dictionary.

## Canonical tensor bridge

Write `model_inputs.npz` and `targets.npz` separately. Required MPM-neutral
inputs are:

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
soil_parameters              # known Chrono controls, not inferred MPM values
```

The only target arrays are:

```text
chrono_loaded_height_m
chrono_post_unload_height_m
```

MR1 requires loaded and post-unload exports of:

```text
column_particle_count
column_mass_kg
column_mean_action_velocity_mps
contact_node_count
contact_normal_impulse_ns
```

Optional families may enter a model only after separate repeatability and
action-signal qualification:

```text
column_mean_stress_mean_pa
column_mean_stress_von_mises_pa
column_mean_elastic_jacobian
column_mean_elastic_isochoric_shear
```

All spatial arrays share the Chrono x/y grid and shape. Extensive quantities
use conservative sums. Intensive particle fields use documented mass-weighted
means. Every interpolation, support rule, frame transform, and empty-column
rule is frozen and published.

Legacy model code may alias generic MPM names to historical Newton input names
at runtime, but stored artifacts must retain the true backend identity.

## Material policy

The first backend qualification uses one prospectively selected fixed
backend-native material. This isolates geometry, action, numerics, and contact
without pretending that Chrono `bekker_kphi` maps directly to a granular MPM
parameter.

A backend-native parameter schedule is permitted only in a later prospective
study that documents parameter semantics and freezes the mapping using sources
and train/validation evidence before protected generation. Parameter transfer
between implementations requires its own translation study.

PhysGaussian scene parameters are engineering starting points, not calibrated
soil values. A passing synthetic prediction does not identify real material
properties.

## Ordered qualification ladder

Complete gates in order. Stop at a failed gate, preserve the evidence, and
record the decision in [running.md](running.md).

### Gate 1: environment and identity

- Pin Python, backend, compiler/runtime, CUDA, NumPy, PyTorch if used, and all
  solver dependencies.
- Record source revisions, dirty state, adapter hashes, GPU, driver, command,
  and kernel-cache policy.
- Run a deterministic device and array-interoperability smoke.
- Prove that backend identity cannot be confused with another adapter.

### Gate 2: units and coordinate frame

- Publish length, time, mass, density, force, stress, and impulse units.
- Verify world-up, grid indexing, particle frame, tool frame, handedness, and
  height datum with a tiny asymmetric fixture.
- Test round-trip surface orientation and action-center placement.

### Gate 3: initial volumetric bed

- Reproduce the exact 5 mm initial surface on a common flat base.
- Record spacing, depth, density, per-particle mass/volume, layer construction,
  side/bottom boundaries, and rasterizer identity.
- Require nonempty common support and prospectively freeze envelope-error gates.
- Reject hollow surface shells and unsupported undulating bottoms.

### Gate 4: no-action preparation

- Demonstrate finite state, stable particle count and mass, acceptable surface
  drift, bounded velocity, and a sustained settling window.
- Check the prepared bed over the full load-plus-unload horizon.
- Repeat in fresh processes and quantify nondeterminism.
- Qualify prepared-state reuse against a fresh preparation before enabling it.

### Gate 5: cylinder contact and guide

- Verify cylinder geometry and the vertical guide independently of material
  fitting.
- Record contact activation, upward normal impulse, trajectory, guide error,
  overlap/penetration, and affected support.
- Reject free fall, missing interaction, nonfinite contact, gross tunneling,
  action-domain escape, or an unrecorded kinematic depth target.

### Gate 6: timestep and resolution convergence

- Run at least coarse, reference, and fine checks on fixed nonprotected cases.
- Compare loaded and post-unload surfaces, tool motion, mass/count, preparation
  drift, and candidate state fields.
- Freeze the numerical setting only when prospectively declared differences
  pass or are explicitly bounded.
- Do not tune the convergence gate after viewing Chrono targets.

### Gate 7: state export

- Require exact shapes, finite values, stable identity where claimed, correct
  checkpoint semantics, and documented units.
- Qualify occupancy/mass, action-aligned velocity, and contact before optional
  stress or deformation fields.
- Require nonzero action signal and acceptable fresh-process variation.
- Exclude plastic or constitutive state until semantics and numerical behavior
  receive their own contract.

### Gate 8: two-episode integration fixture

- Run one training and one validation identity end to end.
- Verify sanitized input, preparation, rollout, export, tensor separation,
  idempotency, incomplete-output refusal, and manifest hashes.
- Measure peak memory and complete wall time.

### Gate 9: 12-episode engineering smoke

- Use exactly eight training and four validation members.
- Require complete finite Chrono, MPM, tensor, and baseline artifacts.
- Confirm target/input separation, memory bounds, runtime identity, and zero
  protected access.

### Gate 10: full train/validation admission

- Complete exactly 48 training and 16 validation pairs.
- Bind all source, environment, plan, Chrono, MPM, tensor, and manifest hashes.
- Do not regenerate admitted smoke responses unless a prospective retry plan
  explicitly requires it.

### Gate 11: training and validation-only selection

- Train the frozen equal-capacity candidate ladder.
- Fit normalization on training only.
- Select checkpoints and calibrate uncertainty on validation only.
- Freeze selected model hashes, evaluator, gates, and fresh protected design.

### Gate 12: protected confirmation and audit

- Open fresh protected targets once after all choices are frozen.
- Generate protected backend responses under the qualified execution identity.
- Run locked prediction and reporting without refit or threshold revision.
- Independently recompute completion checks from immutable predictions,
  manifests, and plans.

## Candidate ladder

Use the same neural capacity, split, optimizer budget, normalization rules, and
selection procedure across learned variants.

| ID | Candidate | Eligible final model? | Purpose |
| --- | --- | --- | --- |
| N0 | initial surface copied forward | no | no-deformation baseline |
| D0 | direct U-Net from initial surface, action, force, and known Chrono control | no | capacity-matched fairness baseline |
| M0 | raw backend loaded and post-unload surfaces | yes | raw MPM utility |
| MR0 | M0 surfaces plus bounded residual | yes | minimal MPM geometric prior |
| MR1 | MR0 plus occupancy/mass, velocity, and contact | yes | robotics-facing MPM fields |
| MR2S | MR1 plus separately qualified stress | optional | stress-field ablation |
| MR2E | MR1 plus separately qualified elastic invariants | optional | elastic-field ablation |

The promotion pool is M0, MR0, and MR1. MR2S or MR2E may be promoted only if
that individual family was qualified before training and improves on MR1
without worsening the failure tail.

The residual is bounded around the backend prediction:

```text
predicted_height = mpm_height + scale * tanh(network_residual)
```

Fit correction bounds and normalization from training only. The selected final
candidate must remain MPM-backed even if D0 wins. If no MPM-backed candidate
passes, the result is a failed alternate-backend study; D0 remains diagnostic.

## Predictive evaluation

Unless a new prospective plan changes them, carry forward these MPM-plus-
residual gates:

- median RMSE at most 0.003 m at both checkpoints in footprint and twice-radius
  regions;
- at least 30% median RMSE reduction versus raw MPM;
- at least 90% of episodes better than both raw MPM and no deformation;
- no episode worse than raw MPM by more than 10% plus 0.001 m;
- nominal-90% interval coverage between 80% and 100%;
- parameter controls degrade paired performance by at least 2%, with paired
  bootstrap lower bound above zero;
- at least 90% correct protected parameter-sensitivity directions.

Freeze a separate M0 gate before protected evaluation. It covers absolute
RMSE, improvement over no deformation, failure tail, support/coverage, and
numerical admission. Fixed-material M0 cannot claim parameter sensitivity.

An MPM-added-value claim additionally requires the selected MPM-backed model
to beat D0 by a predeclared protected margin. The historical margin was 5% on
the joint holdout group. If the MPM-backed model passes its own gates but does
not beat D0, it may be selected by the project constraint but cannot support an
MPM-added-value claim.

## Backend comparison policy

Compare backends only after each independently passes its qualification
ladder. Use common episode inputs, checkpoints, canonical grids, regions, and
metrics, while publishing backend-native material and numerical differences.

Do not call Warp and Taichi independent physics evidence if they are
line-for-line ports of the same equations, parameters, contact law, and bugs.
They remain useful implementation and repeatability comparisons, but a
cross-model-form claim requires genuinely different documented assumptions.

Never mix backend observations into one admission summary. A future
multi-backend learner requires a separately frozen contract and explicit
backend conditioning.

## Minimum tests before simulation

- deterministic plan construction and source/config hashing;
- dirty-revision recording;
- protected-target refusal before unlock;
- sanitized adapter-input construction and leakage refusal;
- units/frame/asymmetric height-map fixture;
- incomplete-output refusal and hash-matching idempotency;
- preparation and response manifest schema validation;
- finite/shape/support/mass/contact/guide admission;
- canonical tensor names and truthful backend identity;
- generic-to-legacy runtime aliasing without namespace falsification;
- train-only normalization and validation-only selection/calibration;
- equal capacity and active-channel masks;
- MPM-presence enforcement in the promotion pool;
- prediction refusal on failed dataset or model identity;
- report claim routing and MPM-added-value refusal when D0 wins;
- audit recomputation from immutable artifacts.

Run focused unit tests, then the two-episode fixture, then the 8/4 smoke. Do not
start 48/16 generation before all earlier gates pass.

## Runtime and retry policy

- Measure one complete serial preparation/episode/export before concurrency.
- Benchmark one and two workers on nonprotected smoke inputs.
- Freeze worker count only after throughput and numerical identity checks.
- Record wall time and peak memory per stage.
- Skip only complete hash-matching artifacts.
- A crash, nonfinite state, missing file, guide failure, convergence failure,
  or schema failure is a preserved attempt with no predictive score.
- Freeze retry scope and execution identity before retrying.
- Mixed worker identities require explicit qualification and remain visible.
- Source changes after plan freeze fail closed unless a prospective continuation
  binds completed artifacts and proves exactly what changed.

## Required deliverables

The study is complete only when it has:

- this versioned goal and a target-free machine-readable experiment plan;
- a pinned environment and source/device identity record per backend;
- canonical adapter interface, at least one implementation, schema, and tests;
- numerical, preparation, contact, convergence, and state-export evidence;
- a passing two-episode integration fixture;
- a passing 8/4 engineering smoke;
- 48/16 admitted train/validation pairs for a qualified backend;
- separated canonical model-input and target archives;
- raw MPM metrics and capacity-matched D0 fairness baseline;
- equal-capacity MR0/MR1 results and separately qualified optional ablations;
- validation-only model selection and uncertainty calibration;
- a prospectively frozen fresh protected plan and open-once marker;
- a locked report covering accuracy, failure tails, controls, sensitivity,
  uncertainty, runtime, and all failed cases;
- explicit claim routing and an independent completion audit;
- a final update to this file, [running.md](running.md), and the repository
  documentation index.

Multi-backend platform completion additionally requires a second adapter to
pass through the two-episode fixture and publish its own qualification result.
It does not require both backends to achieve predictive success.

## Claim routing

| Evidence | Permitted conclusion |
| --- | --- |
| M0 passes frozen numerical and predictive gates | qualified raw named-backend MPM predictor in the frozen synthetic domain |
| MR0/MR1 passes but does not beat D0 | MPM-backed neural predictor; MPM added value not demonstrated |
| MR0/MR1 passes and beats M0 and D0 by frozen margins | MPM-backed neural correction with demonstrated added value in the frozen synthetic domain |
| optional field variant beats MR1 after field qualification | that named field family has incremental predictive value for that backend |
| only D0 passes | no eligible MPM-backed success; retain D0 as diagnostic evidence |
| numerical or admission gates fail | named backend not qualified; no predictive claim |
| Warp and Taichi adapters both pass qualification | portable canonical pipeline across two implementations; not automatically cross-backend physical agreement |

No outcome establishes real-soil fidelity, constitutive truth, material
identification, sequential rollout closure, planner benefit, Gaussian-rendering
accuracy, or sim-to-real transfer.

## Explicit exclusions from the first study

- fitting to real soil or naming a real soil type;
- sequential multi-contact rollout;
- tangential tool motion, rotation, impact, or variable tool geometry;
- in-rollout neural stress or constitutive correction;
- jointly training across backend observations;
- treating automatic differentiation as a qualification result;
- modifying Chrono to make a backend look better;
- protected-set iteration;
- Gaussian rendering or planner success as a substitute for MPM admission.

These may become later prospective studies only after the one-action MPM
pipeline has a clear numerical and predictive result.


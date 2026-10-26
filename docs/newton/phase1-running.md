# Phase 1 chronological implementation and evidence record

Last updated: 2026-10-26

Status: active append-only evidence record

The authoritative goal, scope, ordering, and exit gates remain in
[phase1.md](phase1.md). This file records what was attempted, the frozen
contract used, measured evidence, decisions, blockers, and the next gate. It
must not redefine Phase 1 or maintain a competing success criterion.

## Current snapshot

| Gate | State | Evidence |
| --- | --- | --- |
| goal and fresh-session handoff | complete | [phase1.md](phase1.md) |
| machine-readable pre-screening contract | complete and frozen | [contract](../../configs/phase1_bed_state_v1.json) |
| prospective target-free 48/16/24 plan | complete and frozen | phase1_bed_state_v1/dataset_plan.json |
| parameter-box physical screening | complete at bounded coarse-prior level | surfaces 6/6, Chrono 5/5, and common-base v2 Newton pairings 5/5 pass; strict mechanics remains false |
| initial-surface generator and qualification | complete | all six analytic and native SCM checks pass |
| informative Newton latent export | complete for model inputs | corrected v3 passes three fresh repeats; stress and elastic admitted to H2, plastic excluded |
| neural-training environment | candidate verified, not frozen | conda `test`: Python 3.11.15, NumPy 2.4.6, PyTorch 2.13.0+cu130, CUDA 13.0, RTX 5090 |
| 12-episode engineering smoke set | complete and passed | 12/12 admitted: 8 train/4 validation/0 test; protected test targets unopened; full-dataset permission true |
| 88-episode admitted dataset | train/validation generation active | immutable 48/16/24 input manifest retained; Chrono 40/64 accepted and episode 040 active; 24 test targets absent and locked |
| U-Net model ladder | implementation preflight complete; fitting blocked by dataset | B3/H0/H1/H2 share 289,172 parameters; trainer, validation calibration, and particle lift implemented; 19 focused tests pass |
| locked evaluator | partial preflight implementation; not frozen | prospective config and selection-before-unlock, target-generation, and admission routes exist; prediction/report routes remain unimplemented; 7 focused tests pass; no evaluation plan or unlock marker exists |
| locked test evaluation | protected | targets unopened |
| Phase 1 exit | not demonstrated | later gates remain |

The physical screen, corrected v3 latent-input qualification, and 12-episode
engineering smoke set have passed. The smoke aggregate now permits generation
of the already frozen 88-episode dataset. V2's generated pass remains
audit-rejected; v3 supersedes it with three fresh repeats and enforcement of
every required family. Stress and elastic channels are admitted to H2, while
plastic is excluded. Predictive usefulness is deliberately unresolved until
H2 is compared with H1 on the frozen splits.

## Chronology

### 2026-10-22 — Phase 1 goal and fresh-session routing established

Question:

- define one authoritative Phase 1 goal that predicts loaded and post-unload
  bed state for one bounded action;
- move beyond the Phase 0 independent-cell MLP toward a modest neural physical
  model;
- condition the residual on geometry, load, and varied physical parameters;
- preserve explicit Phase 2 deferrals and leakage-safe success gates;
- make a fresh session able to recover all relevant evidence.

Decision:

- use a small parameter-conditioned 2D U-Net over the common grid as the
  primary H1 model;
- retain the frozen Newton rollout as the physics prior;
- vary action position, force, initial surface, Chrono bekker_kphi, and Chrono
  friction within the declared box;
- use qualified Newton mechanics latents only after semantic export checks;
- reserve sequential and dynamically consistent latent-state prediction for
  Phase 2.

Documentation evidence:

- [phase1.md](phase1.md) is the sole Phase 1 goal and exit authority;
- it links the completion report, Phase 0 authority and protocol, Chrono
  contract, current state, executable entry points, output roots, environments,
  and planned Phase 1 routes;
- every direct local Markdown link in the handoff resolved when checked.

Claim boundary:

- this establishes a prospective research contract only;
- it does not establish a Phase 1 model, dataset, parameter transfer, or latent
  mechanics result.

### 2026-10-22 — Pre-screening contract and prospective split frozen

Question:

- can the Phase 1 bounds be represented in an executable contract and expanded
  into a deterministic, target-free whole-episode plan before any simulation?

Frozen contract:

- identity: phase1_bed_state_v1;
- action: one vertical 35 mm cylinder, center radius at most 0.10 m, normal
  force 30.65625--45.984375 N;
- initial state: six disjoint seeded smooth surfaces, four for training and one
  each reserved for validation and test;
- varied Chrono parameters: bekker_kphi=640000--960000 and
  mohr_friction_deg=24--32;
- frozen Newton prior: Phase 0 material, timestep, resolution, contact, and
  admission semantics;
- dataset: 48 train, 16 validation, and 24 locked test episodes;
- test groups: five unseen-position, five unseen-force, five
  unseen-material-combination, four unseen-initial-surface, and five joint
  combinations;
- physical screening: four material corners plus center and all six surface
  seeds before bulk generation.

Implementation:

- [machine contract](../../configs/phase1_bed_state_v1.json);
- [contract planner](../../scripts/run_phase1_contract_screen.py);
- [contract tests](../../tests/test_phase1_contract_screen.py).

The planner uses a deterministic five-dimensional Halton design, derives
pressure and equivalent mass from the frozen action, assigns whole episodes,
hashes every input payload, locks the test identities, and emits no Chrono
loaded or post-unload target path or value. It refuses to replace an existing
plan whose contract, planner, episode manifest, or test lock differs.

Verification:

- focused contract suite: 7 tests passed;
- planner and tests passed Python bytecode compilation;
- git diff whitespace check passed;
- generated counts: 48 train, 16 validation, 24 test;
- material screening cases: 5;
- surface screening cases: 6;
- bulk dataset permitted: false.

Frozen identities:

| Artifact | SHA-256 |
| --- | --- |
| Phase 1 contract | abd4aff8d5970f8596292139af94c4518494510b40b7b347bf4e6da0aba68c0b |
| contract planner | ab433a9b8fc31bcedd7692440b5e573c5d77b1a023b211eb209aad3c9a9b9f49 |
| 88-episode input manifest | a821d191edbdaa7e2dda3c5cfef89f2c20eaf7ba9ce080c2bd78c67b7047a45c |
| protected test identity lock | 277bdcd63b9539723a1cd0f5059c8169314f55ba70566236138d8f7d54433e0c |

Canonical plan:

    outputs/validity_experiment/newton/phase1_bed_state_v1/dataset_plan.json

The plan records repository revision
7f91a707fe29461398691b6ff4222b8c01e9dcfc; the working tree was intentionally
dirty with the new Phase 1 sources when the plan was frozen. Source identities
are therefore established by the recorded contract and planner hashes, not by
claiming a clean revision.

Decision:

- the contract/split gate passes;
- test identities are protected before any target generation;
- physical screening and bulk data generation remain locked;
- next implement and qualify the initial-surface path, then execute the five
  material screening cases through both Chrono and Newton admission.

Claim boundary:

- the deterministic plan proves prospective input coverage and leakage locks;
- it does not prove that the proposed surfaces or material box are physically
  accepted, that Newton latents are informative, or that any neural model
  learns the requested mapping.

### 2026-10-22 — Six-seed initial-surface family qualified

Question:

- can the declared history-free surface family produce six distinct bounded
  beds and survive native Chrono SCM initialization without silently changing
  their geometry?

Implementation:

- added [phase1_surface.py](../../scripts/phase1_surface.py), a deterministic
  12-mode, random-phase cosine generator with exact zero-mean construction,
  a flat datum boundary, and joint relief/slope rescaling;
- made the 50 mm correlation requirement operational and auditable as the
  conservative positive-correlation quarter wavelength of every constituent
  mode, so every sampled mode has wavelength at least 200 mm;
- added exact metric-heightfield and SCM soil-override inputs to the Chrono
  cylinder episode interface;
- added a native SCM round-trip checker and the frozen
  [screening orchestrator](../../scripts/run_phase1_screening.py);
- froze source, environment, contract, dataset-plan, episode-manifest, and
  protected-test identities before canonical screening.

Verification:

- focused Phase 1 suite: 12 tests passed;
- Chrono terrain unittest suite: 8 tests passed through the activated
  `chrono_splat` environment;
- all six surfaces are finite, zero mean, distinct, and remain within the
  5 mm relief, 10 degree slope, and 50 mm spectral-correlation floor;
- all six native SCM initialization round-trips pass the 10 micrometer limit;
- maximum observed round-trip error: 7.462203 micrometers;
- observed maximum surface slope: 8.055716 degrees;
- observed maximum absolute relief: 4.750000 mm;
- minimum observed spectral-correlation floor: 50.285806 mm.

Surface identities:

| Seed | Partition | Surface SHA-256 | SCM max error, micrometers |
| ---: | --- | --- | ---: |
| 1101 | train | 072b7b97227ed7083b2a245d9d2ca5bb92a89bae656b5c5020eabbd8bbdbab20 | 5.174439 |
| 1102 | train | 43cfd10f97af0ce809d5726f585b94bda6ec636273928912934009818b0bdb43 | 2.622460 |
| 1103 | train | c29578916aff9c2c5950ee5d194f02e0b5e2d169312bf3ed5c9c73410f0b972b | 3.185778 |
| 1104 | train | 1839d33de2f3b8a73da42b39fc58bb020c5a7db6ea94c6b93b0728cbcf923596 | 1.194223 |
| 2101 | validation reserved | 7aae99a906e9f5988b28336acb760cb3248d1b2b7b95f0ced6af4eccd49d448d | 7.462203 |
| 3101 | test reserved | 4c1a146099fcf869d20dc3f59198063cdbbc0f82bf6ac550d799a6893d30d195 | 2.874035 |

Frozen screening identities:

| Artifact | SHA-256 |
| --- | --- |
| screening plan | 958cba65978106e1664a0531b14cf8a520a0e629bd8fd413068de4851b1637ca |
| screening runner | 71b9324aaa383045e94c17493822d35de1244dcf9f21a7c14d18b7558fd55e08 |
| surface generator | 789f617996a4b85b63014fc41e681376e2e672d62af81b3f7260758dff29903e |
| Chrono episode CLI | e0d425a79b74ec3d41bd2d5f84c4035cfdc6c301a1f7237eaf596309420dab18 |
| Chrono episode implementation | e6cdca3e052fb4c5780155c8635642146222313f0b9909929c753dc971a825bd |
| native SCM checker | 4ba8036bd70d4e4b152fa1ebdbde4cf6670ef01d1d6fed54aa3f35bd3e7c1e1e |

Recorded environment:

- Chrono: Python 3.10.20 with the vehicle binding available;
- Newton: Python 3.11.15, Newton 1.5.1, Warp 1.17.0, NumPy 2.4.6;
- GPU: NVIDIA GeForce RTX 5090, driver 580.196.07.

Decision:

- the six-seed surface qualification gate passes;
- the material-box gate remains open while its five frozen Chrono/Newton cases
  execute;
- bulk smoke/data generation remains prohibited.

Claim boundary:

- this proves deterministic bounded geometry and native SCM initialization for
  the six declared seeds;
- it does not yet prove that every material corner is Chrono-accepted or
  Newton-admitted, that mechanics latents are informative, or that any learned
  predictor meets a Phase 1 accuracy gate.

### 2026-10-22 — Fresh-session experiment recovery map completed

Question:

- can a new session recover the live Phase 1 gate, inherited experiment
  provenance, exact code paths, generated evidence, and safe resume procedure
  from the goal document without relying on conversation history?

Implementation:

- expanded the [Phase 1 fresh-session handoff](phase1.md#fresh-session-handoff)
  to link the complete Newton report index, tracked diagnostics index, and
  adjacent Chrono documentation;
- recorded both repository roles and the revisions captured by the frozen
  screening plan, while stating that source hashes identify the intentional
  uncommitted Phase 1 implementation;
- added direct routing for every tracked Phase 1 source and test, both frozen
  plans, the aggregate screen decision, per-surface and per-material evidence,
  paired Chrono episodes, and data-volume availability semantics;
- added exact validation and staged-screen commands, the Chrono environment
  command, single-case selection, duplicate-process protection, and the
  evidence-preserving interrupted-run procedure;
- corrected the routing table to distinguish the existing plan/screening
  output root from the still-absent bulk dataset and model outputs.

Verification:

- all 46 direct local Markdown links in `phase1.md` resolve in the current
  workspace;
- `git diff --check` passes after the documentation change;
- no frozen screening source, contract, plan, output, or simulator artifact
  was changed by this documentation-only audit.

Decision:

- `phase1.md` is now sufficient as the fresh-session root index;
- measured chronological detail remains in this file, machine decisions remain
  in generated JSON summaries, and historical documents remain provenance;
- the active physical material screen and all downstream gates are unchanged.

Claim boundary:

- this closes a documentation-recovery gap only;
- it does not advance the material, latent, dataset, model, or evaluation
  gates.

### 2026-10-22 — First material corner accepted by Chrono

Question:

- does the lowest-`kphi`, lowest-friction corner remain a valid Chrono oracle
  episode on the qualified non-flat initial surface?

Frozen input:

- case: `screen_material_klo_flo`;
- initial surface seed: 1101;
- normal force: 45.984375 N, represented by 4.6875 kg under 9.81 m/s2;
- center: `(0, 0)` m; cylinder radius and height: 35 mm;
- `bekker_kphi=640000`, `mohr_friction_deg=24`;
- Chrono timestep: 1 ms; SCM grid: 5 mm; vertical guide enabled.

Measured evidence:

- Chrono loading convergence accepted: true;
- termination: `converged_speed_hold`;
- accepted loaded checkpoint: 0.34900000000000025 s;
- the manifest records the requested seed-1101 surface hash
  `072b7b97227ed7083b2a245d9d2ca5bb92a89bae656b5c5020eabbd8bbdbab20`;
- native sampled initial-surface maximum absolute error:
  5.174438683752669 micrometers;
- the manifest records the requested varied and fixed SCM soil values exactly.

Artifacts:

- Chrono episode:
  `../tera_splat_sim/validity_experiment/chrono_episodes/phase1_bed_state_v1/screening/material/screen_material_klo_flo/`;
- execution log:
  `outputs/validity_experiment/newton/phase1_bed_state_v1/screening/material/screen_material_klo_flo/logs/chrono.log`.

Decision:

- this individual Chrono case passes its oracle/interface checks;
- the canonical orchestrator advanced to `screen_material_klo_fhi`;
- retain the material-box gate as executing until all five cases complete the
  Chrono and frozen Newton admission path.

Claim boundary:

- 1/5 Chrono material cases is accepted and 0/5 is Newton-admitted;
- this is not a material-box pass, does not open bulk generation, and does not
  qualify mechanics latents.

### 2026-10-22 — Newton latent-export source isolated

Question:

- were Newton stress, elastic strain, plastic Jacobian, and velocity-gradient
  placeholders because the implicit MPM solver did not compute them, or because
  the response exporter read the wrong coupled state?

Source-level evidence:

- Newton 1.5.1 registers `particle_qd_grad`, `particle_elastic_strain`,
  `particle_Jp`, `particle_stress`, and `particle_transform` as MPM state
  attributes;
- `SolverImplicitMPM._update_particles` advances velocity gradient, elastic
  strain, plastic Jacobian, and Cauchy stress;
- `SolverCoupledProxy` reconciles public particle position and velocity into
  the parent state, but its normal reconciliation path does not copy custom
  namespaced MPM history into that parent state;
- the package exposes the current solver-owned values through the public
  `entry_state("mpm", phase="current")` API;
- the Phase 0/initial Phase 1 response writer called `state_arrays(parent)` and
  therefore serialized the parent's initialized placeholder mechanics arrays.

Implementation:

- added [phase1_latent_fields.py](../../scripts/phase1_latent_fields.py), which
  deliberately takes reconciled kinematics from the parent state and mechanics
  history from the public MPM entry state;
- added shape/finiteness validation, a versioned state-archive writer, field
  units/frame semantics, and rotation-invariant stress, elastic, plastic, and
  velocity-gradient reductions;
- added [focused synthetic tests](../../tests/test_phase1_latent_fields.py)
  proving that parent kinematics and entry-local mechanics are selected and
  that known tensor invariants and archive validation are correct.

Verification:

- focused latent-field suite: 3 tests passed;
- both new Python files pass bytecode compilation;
- `git diff --check` passes;
- no source listed in the active frozen screening plan was modified.

Decision:

- treat this as an export-path defect, not evidence that Newton lacks the
  candidate mechanics state;
- do not change `run_newton_cylinder_diagnostic.py` until the five-case frozen
  material screen has completed every Chrono, Newton, and analysis stage;
- after that screen closes, integrate the entry-state extractor, produce a new
  source-hashed latent qualification plan, and require runtime field and repeat
  evidence before admitting any mechanics channel to H2.

Claim boundary:

- the source path and synthetic extractor behavior are established;
- no runtime mechanics field is yet qualified as finite, informative,
  repeat-stable, or useful for prediction.

### 2026-10-22 — Latent runtime/repeat qualification contract frozen

Question:

- can the mechanics export be judged against prospective field-semantic,
  signal, and repeatability thresholds rather than thresholds chosen after
  seeing the repaired runtime values?

Frozen contract:

- [phase1_latent_export_v1.json](../../configs/phase1_latent_export_v1.json);
- qualification case: the material-box reference center
  `screen_material_kref_fref` on initial surface seed 1101 at 45.984375 N;
- three independent fresh-process Newton repeats;
- local mechanics scope: particles within two foot radii, with at least 100
  particles;
- required kinematic/grid families: occupancy/mass, velocity, and contact;
- candidate non-kinematic families: stress invariants, elastic invariants, and
  plastic Jacobian;
- repeat gate: RMS variation no more than 25% of the action signal and Pearson
  correlation at least 0.95;
- H2 requires at least one non-kinematic family to pass, while any field that
  fails remains excluded;
- an H2 usefulness claim still requires the later controlled H2-versus-H1
  predictive comparison.

Frozen identity:

| Artifact | SHA-256 |
| --- | --- |
| latent qualification contract | 4db6c5bd799076ca5f108dc370b43005f3728d46d2ce36c2d98b7774c4c9c0dc |

Verification:

- the JSON contract parses successfully;
- its source case and execution environment agree with the Phase 1 contract;
- the plastic family is allowed to fail: the frozen Newton prior has an
  effectively elastic `yield_pressure_pa=1e12`, so only measured evidence may
  promote stress, elastic, or plastic fields.

Decision:

- freeze these thresholds before generating any repaired latent runtime;
- defer the three repeats until the canonical material screen releases the
  frozen response source;
- do not infer qualification from source inspection or synthetic tests.

Claim boundary:

- the qualification decision rule is now prospective and hash-identified;
- no runtime field or family has passed it yet.

### 2026-10-22 — Latent qualification pipeline implemented before runtime

Implementation:

- extended [phase1_latent_fields.py](../../scripts/phase1_latent_fields.py) with
  deterministic particle-to-5 mm column reductions for occupancy, mass,
  velocity, and invariant mechanics fields;
- added active cylinder-contact selection and contact-node-to-grid count and
  impulse reductions;
- added action-centered persistent-particle selection, checkpoint signal
  metrics, stress-symmetry and positive-Jacobian checks, pairwise repeat RMS
  and correlation, and family-level admission against the frozen contract;
- added
  [run_phase1_latent_qualification.py](../../scripts/run_phase1_latent_qualification.py),
  which refuses to plan before the material screen passes, freezes source,
  input, simulator, environment, and device identities, runs three independent
  reference responses, validates repaired state archives, and emits JSON, CSV,
  and Markdown evidence;
- added [runner contract tests](../../tests/test_phase1_latent_qualification.py)
  binding the qualification to the frozen reference case and Newton numerical
  settings.

Verification:

- complete focused Phase 1 suite: 21 tests passed;
- focused latent extraction, gridding, contact, signal, repeat, and runner
  subset: 9 tests passed;
- new and modified Python sources pass bytecode compilation;
- `git diff --check` passes;
- the active screening runner's frozen source set remains unchanged.

Decision:

- the pre-runtime latent qualification path is ready;
- its plan cannot be frozen and its three repeats cannot start until all five
  material cases are Chrono-accepted and Newton-admitted;
- integrate schema-v2 entry-state/contact export only after the canonical
  material screen has completed, then freeze and execute this runner.

Claim boundary:

- this establishes tested qualification machinery, not a qualified field;
- no latent is admissible to H2 until the measured three-repeat report passes.

### 2026-10-22 — Second material corner accepted by Chrono

Frozen input:

- case: `screen_material_klo_fhi`;
- initial surface seed: 1101;
- normal force: 45.984375 N at `(0, 0)` m with the fixed 35 mm cylinder;
- `bekker_kphi=640000`, `mohr_friction_deg=32`;
- Chrono timestep: 1 ms; SCM grid: 5 mm; vertical guide enabled.

Measured evidence:

- Chrono loading convergence accepted: true;
- termination: `converged_speed_hold`;
- accepted loaded checkpoint: 0.34900000000000025 s;
- final linear speed: 0.00016947959882633525 m/s;
- requested seed-1101 surface identity is preserved;
- native sampled initial-surface maximum absolute error:
  5.174438683752669 micrometers;
- the requested varied and fixed SCM soil values are recorded exactly.

Artifacts:

- Chrono episode:
  `../tera_splat_sim/validity_experiment/chrono_episodes/phase1_bed_state_v1/screening/material/screen_material_klo_fhi/`;
- execution log:
  `outputs/validity_experiment/newton/phase1_bed_state_v1/screening/material/screen_material_klo_fhi/logs/chrono.log`.

Decision:

- both low-`kphi` friction endpoints pass the individual Chrono oracle checks;
- the canonical orchestrator advanced to `screen_material_khi_flo`;
- retain the material-box gate as executing until all five cases complete both
  Chrono and Newton admission.

Claim boundary:

- 2/5 Chrono material cases are accepted and 0/5 is Newton-admitted;
- this does not yet establish acceptance of the parameter rectangle or permit
  bulk target generation.

### 2026-10-22 — Fresh-session recovery details completed

Question:

- can a new session recover every current Phase 1 experiment identity,
  environment, data route, sentinel, and next command without relying on chat
  history?

Documentation added to [phase1.md](phase1.md):

- the complete Phase 1 contract, planner, dataset-plan, input-manifest,
  protected-test, screening-plan, screening-runner, surface-generator, and
  latent-contract hashes;
- the distinction between the full dataset-plan hash and its canonical
  episode-manifest payload hash;
- raw and tracked latent-qualification output routes and the ordered latent
  qualification commands;
- per-case Chrono, metric-bed, Newton preparation, Newton response, log, and
  analysis sentinels used to resume or audit screening;
- the aggregate-summary authority, interruption rule, `outputs` data-volume
  symlink, and repository-relative path requirement.

Verified neural-training candidate:

| Property | Value |
| --- | --- |
| conda environment | `test` |
| Python | 3.11.15 |
| NumPy | 2.4.6 |
| PyTorch | 2.13.0+cu130 |
| CUDA runtime reported by PyTorch | 13.0 |
| CUDA available | true |
| device | NVIDIA GeForce RTX 5090 |

Decision:

- the candidate environment is suitable for implementing the neural code path,
  but remains unfrozen until a prospective training plan records its package
  lock, exact probe, source hashes, and device identity before the first fit;
- simulator environments remain unchanged and separate;
- live measured state continues to come from machine summaries and this
  chronological record, not from immutable `status` fields embedded in frozen
  intent contracts.

Verification:

- the environment probe imported NumPy and PyTorch and reported CUDA available;
- documentation link and whitespace checks are rerun after this entry;
- no frozen screening source was modified.

Claim boundary:

- this closes documentation and recovery omissions only;
- it does not freeze a training run, qualify a latent field, admit a material
  case, or change the Phase 1 gate state.

### 2026-10-22 — Chrono material rectangle accepted

Question:

- do the four declared `bekker_kphi`/friction corners and their center preserve
  the exact seed-1101 initial surface and satisfy the frozen Chrono oracle?

Measured evidence:

| Case | `bekker_kphi` | Friction, deg | Loaded time, s | Final linear speed, m/s | Accepted |
| --- | ---: | ---: | ---: | ---: | --- |
| `screen_material_klo_flo` | 640000 | 24 | 0.349 | 1.395463e-4 | yes |
| `screen_material_klo_fhi` | 640000 | 32 | 0.349 | 1.694796e-4 | yes |
| `screen_material_khi_flo` | 960000 | 24 | 0.355 | 1.259651e-5 | yes |
| `screen_material_khi_fhi` | 960000 | 32 | 0.349 | 1.795061e-4 | yes |
| `screen_material_kref_fref` | 800000 | 28 | 0.349 | 5.480902e-5 | yes |

For every case:

- all eleven frozen identity, action, parameter, initial-surface, loading, and
  finiteness checks pass;
- the initial SCM round-trip error is 5.174439 micrometers;
- 14,161 Chrono cells are valid;
- the 35 mm cylinder is vertically guided at 45.984375 N on seed 1101.

Decision:

- the full proposed Chrono material rectangle passes its oracle-side screen;
- retain all five episodes as immutable inputs to the repaired Newton screen;
- this result does not admit the end-to-end material pipeline because Newton
  admission is separately required.

Artifacts:

- `../tera_splat_sim/validity_experiment/chrono_episodes/phase1_bed_state_v1/screening/material/<case_id>/`;
- `outputs/validity_experiment/newton/phase1_bed_state_v1/screening/material/<case_id>/logs/chrono.log`.

### 2026-10-22 — Original Newton varying-surface preparation rejected

Question:

- can the frozen Phase 0 Newton preparation accept the qualified seed-1101
  varying surface without changing material, numerics, or surface gates?

Frozen input:

- case `screen_material_klo_flo`, whose pre-action bed is shared by all five
  material cases;
- 307,461 particles at 5 mm spacing, including 14,641 top-surface particles;
- 100 kPa, `nu=0.2`, `mu=0.68`, PIC, 7.8125 mm voxels, 0.25 ms timestep;
- 2 s preparation with the unchanged 0.5 mm/s equilibrium hold;
- acceptance limits: at most 5 mm settled-surface RMSE and 10 mm maximum
  absolute error relative to the exact Chrono initial state.

Measured evidence:

- state remained finite and reached equilibrium at 0.81175 s;
- final particle speed p99: 6.758690e-5 m/s;
- settled surface support: 14,161/14,161 cells;
- settled initial-state RMSE: 6.071992 mm, so acceptance is false;
- maximum absolute error: 7.630891 mm;
- mean vertical surface shift: -6.056625 mm;
- after removing only the best constant shift, residual RMSE is 0.431715 mm
  and maximum absolute residual is 1.574266 mm;
- initial/settled surface Pearson correlation is 0.949007.

Root cause:

- the inherited metric-bed builder creates the same 100 mm particle-column
  depth beneath every varying top-surface point;
- that also creates an undulating bottom, while Newton uses one flat sticky
  ground plane below the lowest column;
- higher-bottom columns begin partly unsupported and fall during gravity
  preparation, producing the dominant near-uniform vertical offset;
- Phase 0's flat bed did not expose this interface error: its twelve accepted
  preparations had 1.863558 mm RMSE and 1.915472 mm maximum error.

Decision:

- the response runner correctly refused the unaccepted preparation before
  contact; no response state or material-performance result exists;
- do not relax the frozen 5 mm gate, relabel the preparation, delete the
  failure, or launch four equivalent preparations with the same defective bed;
- preserve the original screen as failed and create a prospectively hashed
  common-flat-base bed builder and screening identity;
- qualify the reference preparation/response first, then reuse the five
  accepted Chrono episodes for the complete Newton screen.

Artifacts:

- preparation manifest:
  `outputs/validity_experiment/newton/phase1_bed_state_v1/screening/material/screen_material_klo_flo/preparation/newton_prepared_bed_manifest.json`;
- preparation and refusal logs:
  `outputs/validity_experiment/newton/phase1_bed_state_v1/screening/material/screen_material_klo_flo/logs/`;
- aggregate decision:
  `outputs/validity_experiment/newton/phase1_bed_state_v1/screening/screening_summary.json`.

Claim boundary:

- the Chrono parameter box passed, but the original end-to-end material screen
  failed at the common Newton initial-state interface;
- this is not evidence that any corner's Newton response is good or bad;
- bulk target generation and latent runtime qualification remain prohibited.

### 2026-10-23 — Common-base repair v1 stopped at legacy validator

Question:

- does the prospectively frozen exact-top/common-flat-base builder pass the
  unchanged Newton preparation interface?

Frozen v1 identity:

| Artifact | SHA-256 |
| --- | --- |
| common-base v1 plan | 1cb525484206d989d97e962d4978ab6e29868289535c5eaa6e5f2367baeddc9d |
| repair contract | e66dcfbe96792b0a0ac6911b01ab6433d2657816901b68e273fc47ada594ccd2 |
| common-base builder | e29ec917aa9f4e4c488753844ddc8e7cf519b94425d5b0a43c1b4306715d6462 |
| rescreen runner | fff058e387f9257ca9ad0a865fd842e8eccd6b7c9f6ced265d56bdf421566e3c |

Static bed evidence:

- 303,829 particles over 14,641 x-y columns;
- exact seed-1101 top particles;
- common base z: -0.0999999947 m;
- one-spacing ground z: -0.1049999947 m;
- 20--21 particles per column according to local surface height.

Measured result:

- Newton simulation did not start;
- the dependency-light validator rejected the bed because it required the total
  particle count to be divisible by the number of surface columns;
- that equal-layer invariant is valid for the legacy flat/fixed-depth format
  but incompatible with a variable-volume bed over a common base.

Decision:

- preserve v1 and its log as a pre-simulation validation failure;
- retain the legacy equal-layer branch for old metadata;
- add a separate strict common-base branch requiring one unique surface
  particle per column, exact top envelope, identical declared base, declared
  column-count range, and one-spacing ground clearance;
- freeze a new v2 plan before retrying runtime.

Artifacts:

- `outputs/validity_experiment/newton/phase1_bed_state_v1/newton_common_base_v1/`.

### 2026-10-23 — Common-base v2 physical screen passed

Question:

- does the strictly validated common-base repair preserve the varying initial
  surface and produce one admissible inference-safe Newton prior for all five
  accepted material targets?

Frozen identity:

| Artifact | SHA-256 |
| --- | --- |
| v2 repair contract | c1fae68557727d7f4dc34bbd3554c36f9ed9185c3dd3b30863d84d4d2f41bf1f |
| common-base builder | e29ec917aa9f4e4c488753844ddc8e7cf519b94425d5b0a43c1b4306715d6462 |
| v2 rescreen runner | 9190aa96e3bc900c87fa30a2558b76dd32aafb54d4c5c10f5dca3b7f8bf4ed4f |
| strict bed validator | 280fa4f198057823c18adc1e0772d466d07232beb44c61936cd0752ef347795b |
| fixed-time response source | 83d7fa40aacd8aa695a19ce5b0c37b0593439d5cddfc2c7927b4aa86fb91904b |
| v2 qualification plan | 57c108ac063d36e255f1721a95ae996c3b8bb0f53abcbe5c4561343a590e37c5 |
| v2 qualification summary | 60990f1004623593197844a49ced397b94b8e898a481311ca01f107820ca57ef |

Verification before runtime:

- 47 focused Phase 1/Newton tests passed;
- the actual 303,829-particle bed passed strict common-base validation;
- legacy beds without a base contract retain the equal-layer validation rule;
- Python bytecode compilation and `git diff --check` passed.

Standalone preparation evidence:

- accepted: true; equilibrium: true;
- first equilibrium: 0.6775 s;
- final p99 speed: 2.388064e-5 m/s;
- valid support: 14,161/14,161;
- settled initial-state RMSE: 2.105972 mm;
- settled maximum absolute error: 4.472049 mm;
- unchanged limits: 5 mm RMSE and 10 mm maximum.

Response evidence:

- the response independently repeated preparation, reaching equilibrium at
  0.2885 s with final p99 speed 1.717390e-6 m/s;
- Newton loading was fixed at 0.350 s and post-unload recovery at 0.250 s;
- the manifest records `chrono_target_time_controls_newton=false`;
- response initial-state RMSE: 0.227810 mm; maximum error: 0.979776 mm;
- all output arrays are finite, all 14,161 cells are supported, and the
  vertical guide passes;
- 20/303,829 particle centers were inside the analytic proxy at any sampled
  time, a fraction of 6.582650e-5;
- maximum center penetration: 6.284565 micrometers, below the inherited
  0.5 mm gross-depth limit;
- wall time for the response: 2570.646 s.

Per-target geometric context:

| Case | Loaded footprint RMSE, mm | Loaded skill vs no deformation | Post footprint RMSE, mm | Post skill |
| --- | ---: | ---: | ---: | ---: |
| `klo_flo` | 14.452 | 0.654 | 11.232 | 0.791 |
| `klo_fhi` | 14.575 | 0.644 | 11.345 | 0.784 |
| `khi_flo` | 17.391 | 0.350 | 14.123 | 0.571 |
| `khi_fhi` | 17.262 | 0.366 | 13.994 | 0.584 |
| `kref_fref` | 16.031 | 0.512 | 12.773 | 0.690 |

Decision:

- all five Chrono/Newton pairings pass numerical and gross-interaction
  admission; the physical screen and its later bulk-permission flag pass;
- one Newton response is shared legitimately because initial bed, action,
  frozen Newton material, and fixed observation times are identical across the
  five cases; soil parameters affect the Chrono targets and later neural
  conditioning, not the frozen Newton prior;
- raw Newton has positive geometric skill over no deformation in every listed
  footprint comparison, but these five screen cases are not model evaluation;
- strict mechanics remains false because the zero-center-penetration sentinel
  failed. Continue to describe Newton as a bounded coarse prior.

Artifacts:

- `outputs/validity_experiment/newton/phase1_bed_state_v1/newton_common_base_v2/qualification_summary.json`;
- `outputs/validity_experiment/newton/phase1_bed_state_v1/newton_common_base_v2/shared_newton_prior/`;
- `outputs/validity_experiment/newton/phase1_bed_state_v1/newton_common_base_v2/cases/<case_id>/case_summary.json`.

Claim boundary:

- this validates the physical input/output pipeline across the proposed
  material rectangle at coarse-prior level;
- it does not qualify stress/strain/plastic inputs, train a neural model, open
  the locked test set, or establish parameter-conditioned predictive value.

### 2026-10-23 — Schema-v2 latent export integrated and v2 route staged

Question:

- can the previously tested coupled-state extractor and cylinder-contact
  selection be integrated into the Newton response without changing the
  completed common-base v2 evidence, and can latent qualification be rerouted
  prospectively to its passing shared preparation?

Implementation:

- the response writer now saves schema-v2 initial, loaded, and post-unload
  archives containing parent-particle kinematics plus coupled solver-entry
  stress, elastic deformation, and plastic state;
- loaded state now includes only active impulses associated with the cylinder
  collider, while initial and post-removal contact arrays are explicitly empty;
- the response manifest publishes field semantics, mechanics sources, and the
  active contact count;
- [phase1_latent_export_v2.json](../../configs/phase1_latent_export_v2.json)
  supersedes the never-run v1 route and binds the passing common-base v2 plan,
  summary, reference pairing, and shared preparation;
- Newton observation timing is independently fixed at 0.350 s loaded and
  0.250 s post-unload, so the Chrono target time cannot control the prior;
- the qualification runner and its tests now require the passing physical
  screen, common-base preparation, independent timing arguments, schema-v2
  archives, three fresh-process repeats, and a final aggregate decision.

Verified pre-plan identities:

| Artifact | SHA-256 |
| --- | --- |
| active latent v2 contract | 2ad312c67d99b78a7f8b9323497801819d52297669f8d192e4d67265537a6b9d |
| qualification runner | c319e0f2dadfa475ff8b7251c9d6f15ce3bbb2d5e08934b7c343f32b8826dcd8 |
| schema-v2 Newton response writer | df7176babca225bc50ceab08cc9bc69e8ce69a9be9e23d85474a0858c6c5c783 |
| latent field extraction/reduction | 0bad419682d322ee718150a4922bb53a6242f2185f6c091c561cb74749f48d8f |
| Newton archive/bed validator | 280fa4f198057823c18adc1e0772d466d07232beb44c61936cd0752ef347795b |

Verification:

- 49 focused Newton and Phase 1 tests pass, including coupled mechanics-state
  selection, active cylinder-contact filtering, archive semantics, common-base
  validation, and v2 command routing;
- `git diff --check` passes;
- the original common-base v2 plan and summary remain immutable and continue
  to identify the response source used for that completed physical screen;
- the latent v2 plan was then frozen before runtime at SHA-256
  `b948bbfb5c40c5c3ac3730e9be624fab409b7be74da34b1961f8786ef37993ad`;
  it binds the passing physical screen, shared preparation, reference Chrono
  arrays, all executable sources, Python 3.11.15, NumPy 2.4.6, Newton 1.5.1,
  Warp 1.17.0, and `cuda:0`;
- no repeat directory or repaired field result exists yet.

Decision:

- schema-v2 integration is complete and the active route is v2;
- preserve `phase1_latent_export_v2/qualification_plan.json`, execute repeats
  1--3 as distinct processes, and analyze only after all three integrity checks
  pass;
- do not start the 12-episode smoke set and do not admit any mechanics channel
  to H2 before the aggregate qualification summary passes.

Claim boundary:

- source integration and prospective routing are validated;
- no stress, elastic, plastic, or contact signal has yet been shown finite,
  informative, repeat-stable, or predictively useful at runtime.

### 2026-10-23 — V2 runtime completed; generated pass rejected by contract audit

Question:

- do three independent schema-v2 responses establish finite, informative, and
  repeat-stable occupancy/mass, velocity, contact, and non-kinematic mechanics
  channels under the written Phase 1 gate?

Frozen v2 identity:

| Artifact | SHA-256 |
| --- | --- |
| v2 qualification plan | b948bbfb5c40c5c3ac3730e9be624fab409b7be74da34b1961f8786ef37993ad |
| v2 generated summary | 2849aa933922d7072e8dd0fa99ad67094dde87c01af8123cfb5bc840a18e037e |

Runtime evidence:

| Repeat | Wall time, s | Initial RMSE, mm | Max center penetration, micrometers |
| --- | ---: | ---: | ---: |
| 1 | 2590.529 | 0.228 | 6.333 |
| 2 | 2556.654 | 0.228 | 6.234 |
| 3 | 2576.997 | 0.228 | 5.526 |

- all three manifests are finite and pass preparation and guide checks;
- each repeat contains complete initial, loaded, and post-unload schema-v2
  archives;
- initial and post-removal contact arrays are empty as declared;
- repeat 1 loaded contact has 367 active nodes and 0.010632 N s total upward
  impulse;
- fixed observation timing and the bounded coarse-prior penetration boundary
  remain unchanged.

Measured field evidence:

- stress passes the frozen particle signal/repeat gates: mean-stress repeat
  ratio 0.0378 with minimum correlation 0.9989; von-Mises ratio 0.0479 with
  minimum correlation 0.9983;
- elastic invariants pass: determinant ratio 0.1111/correlation 0.9810 and
  isochoric-shear ratio 0.0988/correlation 0.9837;
- contact grids pass when audited explicitly: node-count ratio
  0.1474/correlation 0.9874 and normal-impulse ratio 0.0851/correlation 0.9957;
- required velocity does not pass the frozen repeat gate: 5 mm column RMS
  speed has repeat/action ratio 0.3885 and minimum correlation 0.7432;
- action-aligned unsmoothed column-mean velocity improves the ratio to 0.1880
  but still misses correlation at 0.9131;
- plastic `J_p` is numerically finite and repeatable but physically implausible
  for the selected effectively elastic material: its median remains 1 while
  maxima reach 46,664 loaded and 47,682 post-unload.

Audit finding:

- the v2 analyzer applied the 0.25 ratio and 0.95 correlation gates only to
  non-kinematic particle invariants;
- it checked required velocity and contact for single-run signal/presence but
  omitted their repeat checks;
- therefore its machine-generated `status=passed` contradicts
  [phase1.md](phase1.md), which requires occupancy/mass, velocity, contact, and
  a non-kinematic family to qualify;
- preserve the v2 summary verbatim, but treat the Phase 1 latent gate as failed
  under audit. Do not admit channels to H2 or start smoke generation from v2.

### 2026-10-23 — Corrected v3 latent gate implemented before fresh runtime

Question:

- can the enforcement gap be corrected without relaxing the frozen 0.25
  repeat/action and 0.95 correlation thresholds or reusing observed v2 runtime
  as confirmatory evidence?

Prospective v3 contract:

- [phase1_latent_export_v3.json](../../configs/phase1_latent_export_v3.json);
- v2 response directories are prohibited from reuse; v3 requires three new
  fresh-process responses under a new source/input/environment plan;
- the required velocity channel is the action-aligned z component of the 5 mm
  column mean followed by one fixed 3x3/15 mm box mean, a support-scale
  reduction chosen to suppress sub-voxel APIC jitter while retaining the
  indentation field;
- velocity, contact-node count, and normal impulse must each pass the unchanged
  repeat ratio and correlation gates;
- plastic state additionally requires maximum absolute `log(J_p) <= 0.05`, a
  generous constitutive plausibility limit for `yield_pressure_pa=1e12`;
- stress and elastic gates are unchanged.

Verified pre-plan identity:

| Artifact | SHA-256 |
| --- | --- |
| v3 contract | 51385b1e904b9553ce279ec2ad60f47c41dbc4171cfa289b979b89965af1e9b2 |
| corrected qualification runner | b4db1577e6f3162ac2bd79cb60cd77672761eba1a9a25633a82de260ec336632 |
| v3 runner tests | e745ebf295779adfe56d2aeec9cc4a73bbb48fd6bf3da3fcae351bcb91c96bfe |

Verification:

- 52 focused Newton/Phase 1 tests pass;
- tests cover fixed 3x3 averaging, stable/unstable grid repeat detection,
  plastic plausibility rejection, schema-v2 extraction, contact selection,
  common-base validation, and command routing;
- Python compilation and `git diff --check` pass;
- as a diagnostic only, applying the declared 3x3 velocity representation to
  preserved v2 arrays gives ratio 0.0619 and minimum correlation 0.9850. This
  motivated no threshold change and is not accepted as v3 confirmation.

Decision and next gate:

- the v3 plan is frozen at SHA-256
  `355bf9bcbe73f2eb365095e1c4ad30fd58bc28f0c2ec27d1dcfcbe5b3d047b13`;
  it binds the corrected runner, unchanged physical-screen inputs, Python
  3.11.15, NumPy 2.4.6, Newton 1.5.1, Warp 1.17.0, and `cuda:0`;
- execute three new repeats and use only its aggregate summary to decide
  admission;
- plastic remains excluded unless it passes both numerical and constitutive
  gates; even a v3 pass only qualifies solver inputs, not predictive value;
- smoke generation remains prohibited until v3 passes.

### 2026-10-24 — Corrected v3 latent qualification passes

Question:

- do three fresh fixed-time responses satisfy every prospective v3
  occupancy/mass, action-aligned velocity, contact, non-kinematic repeat, and
  constitutive-plausibility gate without relaxing thresholds?

Frozen identity and execution:

| Artifact | SHA-256 |
| --- | --- |
| v3 contract | 51385b1e904b9553ce279ec2ad60f47c41dbc4171cfa289b979b89965af1e9b2 |
| qualification runner | b4db1577e6f3162ac2bd79cb60cd77672761eba1a9a25633a82de260ec336632 |
| v3 qualification plan | 355bf9bcbe73f2eb365095e1c4ad30fd58bc28f0c2ec27d1dcfcbe5b3d047b13 |
| aggregate summary and tracked summary | 72af2a69495f525c6dcc8df248e82a3eb5667ff41f74b399072d82635d0d9243 |
| tracked field metrics | 5ff70aed9d7c1054fe19b570d718163daf0058725cf6f47bd0cd83caf1b0bc38 |

- repeat 1 completed in 2,583.308 s with 5.923 micrometers maximum analytic
  penetration and 0.227810 mm initial surface RMSE;
- repeat 2 completed in 2,590.948 s with 6.165 micrometers maximum analytic
  penetration and 0.227810 mm initial surface RMSE;
- repeat 3 completed in 2,601.329 s with 6.819 micrometers maximum analytic
  penetration and 0.227810 mm initial surface RMSE;
- all repeats pass finite-state, preparation, guide, and schema-v2 checks.

Measured aggregate evidence:

| Required field | Repeat/action RMS ratio | Minimum pairwise correlation | Decision |
| --- | ---: | ---: | --- |
| 3x3/15 mm action-aligned z velocity | 0.159950 | 0.964290 | pass |
| active contact-node count | 0.143963 | 0.987627 | pass |
| normal contact impulse | 0.090433 | 0.995151 | pass |
| stress mean | 0.028491 | 0.999385 | pass |
| stress von Mises | 0.038340 | 0.998884 | pass |
| elastic Jacobian | 0.100775 | 0.984266 | pass |
| elastic isochoric shear | 0.095120 | 0.984845 | pass |

- every required occupancy, mass, velocity, and contact check is true;
- maximum mass relative error is `3.742e-16`;
- stress and elastic are the qualified non-kinematic families;
- plastic is not qualified even though it is repeatable: maximum absolute
  `log(J_p)` is 10.747924 versus the frozen 0.05 plausibility limit.

Decision and claim boundary:

- the corrected v3 machine decision is `status=passed`;
- H2 may consume occupancy/mass, the declared action-aligned velocity and
  contact fields, and qualified stress and elastic invariants;
- plastic state must not enter H2 under this contract;
- this establishes stable, semantically checked model inputs only. It does not
  establish their predictive value, strict Newton contact mechanics, a trained
  model, or any Phase 1 score. Only the controlled H2-versus-H1 evaluation can
  support a mechanics-latent value claim;
- the next permitted gate is implementation and validation of the 12-episode
  engineering smoke set. The 88-episode dataset remains blocked by that exit.

Artifacts:

- raw plan, three response trees, logs, and aggregate summary:
  `outputs/validity_experiment/newton/phase1_bed_state_v1/latent_qualification/phase1_latent_export_v3/`;
- tracked summary, field metrics, and generated report:
  `diagnostics/phase1_latent_export_v3/`.

### 2026-10-24 — Engineering smoke contract implemented and plan frozen

Question:

- can the 12-episode engineering gate be made prospective, leakage-safe, and
  restartable before generating any new Chrono target or Newton response?

Implementation:

- added [phase1_dataset_smoke_v1.json](../../configs/phase1_dataset_smoke_v1.json)
  with 8 frozen train IDs, 4 frozen validation IDs, and no test IDs;
- the membership covers all four training surfaces and reserved validation
  surface 2101. Two validation episodes exercise that unseen-surface route;
- added [run_phase1_dataset.py](../../scripts/run_phase1_dataset.py), with
  separately resumable `plan`, `chrono`, `bed`, `newton`, and `analyze`
  stages;
- one fresh common-flat-base Newton preparation is shared only among episodes
  with the same initial-surface seed. Chrono targets and Newton responses are
  never shared between episode identities;
- fixed Newton observations remain target-independent at 0.350 s loaded and
  0.250 s post-unload;
- H2 tensors include occupancy/mass, fixed 3x3 action-axis velocity, contact,
  stress, and elastic fields. Plastic is prohibited;
- model inputs and Chrono targets are written to separate archives. The
  per-episode validator checks shapes, finiteness, action signal, memory,
  baseline loss finiteness, inherited admission, fixed timing, and schema v2;
- added [focused tests](../../tests/test_phase1_dataset.py) for membership,
  target locking, field admission, target separation, smoothing, prerequisites,
  and fixed-time behavior.

Verification before freeze:

- 17 focused smoke/common-base/latent tests pass;
- Python compilation and repository whitespace validation pass;
- both prerequisite machine summaries pass; only stress and elastic are
  admitted as non-kinematic fields;
- the frozen plan records Python 3.10.20 for Chrono, Python 3.11.15, NumPy
  2.4.6, Newton 1.5.1, Warp 1.17.0 for Newton, the RTX 5090 identity, and
  `cuda:0`;
- `test_targets_opened=false` at plan freeze.

Frozen identities:

| Artifact | SHA-256 |
| --- | --- |
| smoke contract | d963f0dcd58a4e6c502ab74c7b741bf17d388b2cfdfbbc81dfafeaaf58dccff9 |
| smoke runner | db579bdc06e43d72c60868fe56a7c3a1315034f2b266ea059dbe70a805c3faf2 |
| focused tests | 9f6e9efcd94e941183fa49a9a74c096a80dd43154c5f85f43f2a7f661a94ffe3 |
| frozen smoke plan | 760592caa36f5ca3552192c1cb24a03409a8fa8603c0c4fcf3fdefc2be473ca0 |
| selected 12-episode membership | 5bbfc312f0bfd4f0edd027fb5b11dd2293e62398f78d6b68af5b9acb1cb90db8 |

Decision and claim boundary:

- the smoke runtime may begin without opening the locked test set;
- this freezes executable schema and routing, not successful episode
  generation. No smoke episode is yet complete and the 88-episode dataset
  remains prohibited;
- only a passing aggregate `smoke_summary.json` may advance the work to full
  dataset generation.

### 2026-10-24 — All smoke Chrono targets accepted; Newton runtime started

Measured progress under the frozen smoke plan:

- all 12 selected Chrono episodes completed and passed action, soil-parameter,
  initial-surface identity, native round-trip, convergence, support, and
  finite-state checks;
- every episode has 14,161 valid cells;
- accepted Chrono loaded event times range from 0.349 to 0.356 s. These times
  are recorded as target metadata and do not control the Newton rollout;
- all five seed-specific common-flat-base metric beds were built from the
  corresponding Chrono initial state only. No loaded or post-unload target was
  consumed by bed construction;
- the surface-1101 Newton preparation completed with 303,829 particles,
  equilibrium first reached at 0.6775 s, and 140.181 s wall time;
- its settled-surface RMSE is 2.105972 mm and maximum absolute error is
  4.472049 mm, passing the inherited 5 mm and 10 mm gates;
- the first episode-specific fixed-time Newton response is active on `cuda:0`.

Decision and claim boundary:

- Chrono smoke generation and metric-bed construction pass their current
  checks, and the first preparation is accepted;
- the aggregate smoke gate remains incomplete. No episode is admitted until
  its Newton response and separated tensor archives pass analysis, and the
  full 88-episode dataset remains prohibited.

### 2026-10-24 — First four smoke Newton responses complete

Runtime progress:

- preparations for surfaces 1101, 1102, 1103, and 1104 are accepted;
- their equilibrium times are 0.6775--0.7060 s and wall times are
  140.181--143.204 s;
- their settled-surface RMSE range is 2.105972--2.172294 mm and maximum
  absolute-error range is 4.360292--4.594764 mm, within the frozen preparation
  gates;
- train episodes 000--003 have complete fixed-time schema-v2 responses;
- all four responses are finite and pass the vertical-guide check;
- response wall times are 2,565.678--2,586.562 s;
- initial-state surface RMSE is 0.222380--0.227810 mm;
- maximum analytic particle-center penetration is 6.957--11.737 micrometers,
  well inside the inherited 0.5 mm coarse-prior limit;
- train episode 004 is active and reuses only the already accepted
  surface-1101 preparation.

Claim boundary:

- completion of a response is not episode admission. Tensor export and every
  per-episode numerical, interaction, schema, memory, signal, and loss check
  remain pending until the ordered analysis stage.

### 2026-10-24 — First smoke episode passes complete admission

Early analyzer exercise on completed train episode 000:

- the frozen analyzer produced physically separate `model_inputs.npz` and
  `targets.npz` archives on the 121 by 121, 5 mm grid;
- 28 model-input fields include geometry, action maps/vectors, soil parameters,
  raw Newton displacements, occupancy/mass, smoothed action-axis velocity,
  contact, stress, and elastic invariants for both checkpoints;
- no plastic field is present;
- the combined uncompressed tensor footprint is 1,551,986 bytes, below the
  frozen 512 MiB per-episode limit;
- every numerical, interaction, fixed-timing, schema-v2, shape, finiteness,
  support, action-signal, memory, target-separation, and baseline-loss check
  passes;
- the Chrono local action signal is 11.333 mm RMS at both reported checkpoints;
- loaded local RMSE is 11.333 mm for no deformation and 8.791 mm for raw
  Newton; post-unload values are 11.333 mm and 7.168 mm, respectively;
- model-input SHA-256 is
  `d739533264894102e20368bbd37613e6d29b01c76da19860bd999e17f371c1c6`;
  target SHA-256 is
  `74527931012f7cc7b146af52a7a1b3e0b8578dbbc7e160e0f38f938ed31757cc`.

Decision and claim boundary:

- episode 000 is admitted as a bounded coarse-prior training sample;
- this validates the executable tensor route on one real episode, not the
  12-episode aggregate, a trained model, or any predictive success criterion.

### 2026-10-24 — First four smoke episodes admitted

- train episodes 001--003 also pass every frozen admission and tensor check;
- all first four archives are 1,551,986 uncompressed bytes with identical
  field structure and no plastic input;
- their Chrono local action-signal RMS spans 8.499--12.019 mm;
- raw Newton local RMSE spans 6.038--8.800 mm loaded and 4.974--7.168 mm
  post-unload, and is lower than no deformation for all eight comparisons;
- the completed/admitted count is now 4/12. This remains engineering evidence
  only; no model has been fit and the aggregate smoke gate remains open.

### 2026-10-24 — Fifth smoke episode admitted

- train episode 004 completes in 2,573.907 s and passes every numerical,
  interaction, tensor, and loss-behavior check;
- maximum analytic particle-center penetration is 7.002 micrometers;
- its tensor footprint remains 1,551,986 uncompressed bytes with plastic
  excluded;
- Chrono local action-signal RMS is 9.580 mm;
- raw Newton reduces local RMSE from 9.580 to 7.771 mm loaded and to 6.388 mm
  post-unload;
- the completed/admitted count is 5/12. Train episode 005 is active using the
  accepted surface-1102 preparation; the aggregate gate remains open.

### 2026-10-24 — Sixth smoke episode admitted

- train episode 005 completes in 2,558.274 s and passes every frozen check;
- maximum analytic particle-center penetration is 10.809 micrometers and the
  tensor footprint remains 1,551,986 uncompressed bytes;
- Chrono local action-signal RMS is 9.859 mm;
- raw Newton reduces local RMSE from 9.859 to 8.505 mm loaded and to 6.495 mm
  post-unload;
- the completed/admitted count is 6/12. Train episode 006 is active using the
  accepted surface-1103 preparation; aggregate permission remains false.

### 2026-10-24 — Seventh smoke episode admitted

- train episode 006 completes in 2,578.009 s and passes every frozen check;
- maximum analytic particle-center penetration is 5.258 micrometers and the
  tensor footprint remains 1,551,986 uncompressed bytes;
- Chrono local action-signal RMS is 12.221 mm;
- raw Newton reduces local RMSE from 12.221 to 7.741 mm loaded and to 5.939 mm
  post-unload;
- the completed/admitted count is 7/12. Train episode 007 is active using the
  accepted surface-1104 preparation; aggregate permission remains false.

### 2026-10-25 — Eighth training episode admitted

- train episode 007 completes in 2,583.771 s and passes every frozen check;
- maximum analytic particle-center penetration is 8.538 micrometers and the
  tensor footprint remains 1,551,986 uncompressed bytes;
- Chrono local action-signal RMS is 9.167 mm;
- raw Newton reduces local RMSE from 9.167 to 5.978 mm loaded and to 4.691 mm
  post-unload;
- the completed/admitted count reaches 8/12, completing the training portion
  of the smoke set without opening a test target.

### 2026-10-25 — Four validation smoke episodes admitted

The two joint-design and two reserved-initial-surface validation episodes all
pass the same frozen numerical, interaction, schema-v2, tensor, memory,
signal, and loss checks:

| Episode | Response wall time (s) | Penetration (um) | Signal (mm RMS) | Raw Newton loaded RMSE (mm) | Raw Newton post RMSE (mm) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `p1_validation_joint-design_000` | 2,591.611 | 11.468 | 11.852 | 6.906 | 5.129 |
| `p1_validation_joint-design_001` | 2,588.362 | 3.185 | 12.318 | 6.899 | 4.976 |
| `p1_validation_unseen-initial-surface_008` | 2,602.385 | 4.897 | 9.414 | 6.043 | 5.155 |
| `p1_validation_unseen-initial-surface_009` | 2,570.663 | 7.430 | 10.221 | 7.950 | 6.471 |

Reserved surface 2101 receives one fresh common-flat-base Newton preparation
before its two responses. It is accepted after reaching equilibrium at 0.705 s
in 144.221 s wall time; all 14,161 cells are valid, with 2.093 mm settled
height RMSE and 4.584 mm maximum error. Its preparation-manifest SHA-256 is
`aa8e38c7a369cc3796ccca9fa820de19c0b4e67f35b45a2f077aecbf511fc91b`.

Decision and claim boundary:

- all four validation episodes are admitted and the completed count reaches
  12/12;
- this validates the engineering data path on frozen train and validation
  membership, including an unseen initial surface; it is not model-selection
  or predictive-generalization evidence.

### 2026-10-25 — Frozen 12-episode smoke gate passes

Independent rerun of the analyzer produces:

- `status=passed` and `full_dataset_permitted=true`;
- exact counts of 8 train, 4 validation, and 0 test episodes;
- all episode-count, split-count, completion, admission, surface-coverage, and
  protected-test checks true;
- protected test targets unopened;
- every episode stored as separate `model_inputs.npz` and `targets.npz`
  archives of 1,551,986 uncompressed bytes;
- action-signal RMS range 8.499--12.318 mm;
- analytic particle-center penetration range 3.185--11.737 micrometers;
- raw Newton local RMSE range 5.978--8.800 mm loaded and 4.691--7.168 mm
  post-unload, lower than no deformation at both checkpoints for all 12
  episodes;
- stress and elastic inputs included, plastic state excluded.

Frozen identity and reproduced evidence:

- smoke plan SHA-256:
  `760592caa36f5ca3552192c1cb24a03409a8fa8603c0c4fcf3fdefc2be473ca0`;
- selected membership SHA-256:
  `5bbfc312f0bfd4f0edd027fb5b11dd2293e62398f78d6b68af5b9acb1cb90db8`;
- canonical 88-input manifest SHA-256:
  `a821d191edbdaa7e2dda3c5cfef89f2c20eaf7ba9ce080c2bd78c67b7047a45c`;
- protected test-lock SHA-256:
  `277bdcd63b9539723a1cd0f5059c8169314f55ba70566236138d8f7d54433e0c`;
- reproduced `smoke_summary.json` SHA-256:
  `c473e4b79a5c615f88c52cdb2f5f74860848eaf6102a1a751fda45e6eedc24c0`.

Decision and next gate:

- the smoke exit is satisfied and full 88-episode data generation is now
  permitted;
- the 88 identities and 48/16/24 whole-episode splits were frozen before any
  Phase 1 targets and must not be revised after seeing smoke results;
- next implement and verify a resumable bulk route that preserves the smoke
  schema, per-surface preparation reuse, identity checks, separate input/target
  storage, and locked-test boundary, then generate the accepted pairs;
- no U-Net has been trained and no Phase 1 predictive-success claim is yet
  supported.

### 2026-10-25 — Train/validation bulk route frozen before targets

Question:

- how should bulk generation proceed without violating the requirement to
  select the final model on validation before opening the locked test set?

Decision:

- retain the immutable 88-input manifest and 48/16/24 whole-episode split;
- generate and admit the 48 training and 16 validation targets now;
- keep all 24 test identities frozen but prohibit their target generation,
  inspection, tensor export, or analysis in this runner;
- defer test-target generation to the one-shot locked evaluator after model,
  normalization, calibration, and all selection choices are frozen.

Implementation:

- [bulk contract](../../configs/phase1_dataset_bulk_v1.json);
- [bulk runner](../../scripts/run_phase1_dataset_bulk.py);
- [focused tests](../../tests/test_phase1_dataset_bulk.py);
- the runner imports the completed smoke tensor/admission logic but does not
  modify the source-hashed smoke runner;
- it selects all and only the frozen train/validation episodes, creates one
  fresh preparation per non-test surface seed, preserves separate input and
  target archives, and refuses any locked test identity or artifact;
- 23 focused bulk, smoke, metric-bed, and latent-field tests pass; the runner
  also passes Python compilation and `git diff --check`.

Frozen identity before the first bulk target:

- bulk contract SHA-256:
  `dcd2717629c441132b8f978e6c981876a396b5891979f63f61a05f465926b35f`;
- bulk runner SHA-256:
  `381c3fcbd65d9d14401a950e2265bff3c61a0724235400a3b059815e80e06b4e`;
- bulk tests SHA-256:
  `3bad3072facb067db84ae3ac7a4f9a5e3708f61882c45f18e1c693c71607ef2d`;
- frozen `bulk_plan.json` SHA-256:
  `a42db0a6a49142620cf276cb8337ffff4c8b804ad0d0a73af71569e883e4cb18`;
- selected 48/16/0 membership SHA-256:
  `37e5f1cc405bc92a72a0644848e6b08a4d8709931486b22cb54efe3069097e26`;
- original 88-input manifest SHA-256 remains
  `a821d191edbdaa7e2dda3c5cfef89f2c20eaf7ba9ce080c2bd78c67b7047a45c`;
- protected 24-identity test lock remains
  `277bdcd63b9539723a1cd0f5059c8169314f55ba70566236138d8f7d54433e0c`.

The plan records Python 3.10.20/PyChrono vehicle availability for Chrono,
Python 3.11.15/Newton 1.5.1/Warp 1.17.0/NumPy 2.4.6 for Newton, and RTX 5090
device UUID `GPU-2e7af1ff-fd32-5ae7-246e-fbc03cf1f50a` on `cuda:0`.

Claim boundary and next gate:

- this freezes a resumable, leakage-safe generation route; no bulk target has
  yet been generated and no training dataset is yet admitted;
- next run Chrono for the 64 selected inputs, build five surface-specific
  priors, run the 64 Newton responses, and admit the tensor pairs;
- test results remain unopened and no predictive model claim is supported.

### 2026-10-25 — First 14 bulk Chrono targets accepted

- the single frozen bulk supervisor advances sequentially through train
  episodes 000--013 and validates each completed manifest before launch of the
  next target;
- all 14 completed episodes are accepted by the frozen Chrono checks;
- every episode contains 14,161 valid finite surface cells;
- accepted loading-event times span 0.349--0.356 s;
- train episode 014 is active as the fifteenth target;
- no bulk Newton prior, response, or tensor has been generated yet, and all 24
  locked test targets remain absent.

This is a resumability checkpoint, not a dataset admission or model result.

### 2026-10-25 — Shared U-Net and training preflight implemented

Question:

- can Phase 1 use a modest spatial neural model that has enough capacity to
  encode geometry, action parameters, and qualified mechanics fields while
  preserving a fair direct-versus-hybrid comparison?

Implementation:

- added [the prospective training contract](../../configs/phase1_training_v1.json),
  [the shared model](../../scripts/phase1_bed_state_model.py), and
  [the training/selection runner](../../scripts/train_phase1_bed_state.py);
- B3, H0, H1, and H2 all use the same three-level 2D U-Net and immutable input
  masks, so every variant has exactly 289,172 trainable parameters;
- two conditioned residual blocks are used at every encoder, bottleneck, and
  decoder scale, with GroupNorm, SiLU, and feature-wise affine conditioning;
- the shared decoder has separate loaded and post-unload mean and log-variance
  heads. Zero-initialized mean heads reproduce the declared initial or Newton
  base state before fitting, and corrections are bounded and boundary tapered;
- the prospective trainer declares train-only normalization, three seeds
  (`20261022`, `20261023`, and `20261024`), AdamW, validation early stopping,
  heteroscedastic and geometric losses, and model selection before any test
  target can be unlocked;
- added focused [model tests](../../tests/test_phase1_bed_state_model.py) and
  [trainer tests](../../tests/test_train_phase1_bed_state.py).

Verification:

- all 6 model tests and all 5 trainer tests pass in the separate `test`
  environment;
- both Python sources compile and `git diff --check` passes;
- current, not-yet-frozen source identities are:
  - training contract: `59a522e914c9494c10b8bc7c9c16c842028cde016646a666dc5acba76bb4f89b`;
  - model: `c68f21a7bfb953311e8fe36dbc90fb75002800476d818a92f4c8c6e1157e2d46`;
  - trainer: `11ff2507e596563301b6268a2878bda01f21d34ba5c4b1226972dfeb4ed0bb56`;
  - model tests: `edab22e827417f04ae2498c540b7e7d093475a7269dc0cb0829b56be85b46a94`;
  - trainer tests: `15ed50d914266660efee477912505daaae117ddd7f7f1f669894f0b969c53787`.

Concurrent bulk checkpoint:

- 25 of 64 train/validation Chrono targets are complete and all 25 pass the
  frozen acceptance checks;
- every completed target has 14,161 valid cells and accepted loading-event
  times span 0.349--0.364 s;
- train episode 025 is active as the next target; the same single frozen bulk
  supervisor remains responsible for the sequence.

Decision and claim boundary:

- the model now has materially more capacity than the 241-parameter Phase 0
  residual and can spatially condition on geometry, action, soil parameters,
  and qualified mechanics inputs without changing capacity across ablations;
- this is code and preflight evidence only. No training plan is frozen, no
  weights have been fit, and there is no predictive score;
- the trainer must remain gated until all 64 train/validation pairs are
  admitted. A deterministic, preservation-checked particle lift and the locked
  evaluator still have to be implemented before the Phase 1 state and test
  gates can pass;
- all 24 protected test targets remain absent and unopened.

### 2026-10-26 — Trainer semantics and particle-state contract hardened

Questions:

- does the no-action identity term represent a physical zero-force action after
  normalization, rather than an accidental mean-field action?
- are training-plan and model-card hashes unambiguous and sufficient to refuse
  drift before test unlock?
- can a predicted surface be lifted onto the real Newton particle archive while
  changing only z and preserving every other source field exactly?

Corrections and implementation:

- the no-action spatial tensor is now constructed in physical units first:
  initial geometry, support, and action-relative coordinates are retained,
  while footprint, Newton response, contact, velocity, stress, and elastic
  response channels are set to physical zero before train-fitted normalization;
- normalization now records separate canonical-payload and exact serialized-file
  SHA-256 values. Checkpoints, model cards, and selection summaries use the
  same two meanings consistently;
- model selection now rechecks all checkpoint, history, plan, normalization,
  variant, seed, capacity, and test-lock identities before accepting any card;
- selected models receive separate loaded/post-unload conformal multipliers fit
  only on the 16 validation episodes; test targets remain unavailable during
  calibration;
- added [phase1_particle_lift.py](../../scripts/phase1_particle_lift.py) and
  [its focused tests](../../tests/test_phase1_particle_lift.py). The frozen
  columnwise linear depth taper is 0.1 m, refuses a downward correction large
  enough to invert particle ordering, changes only `position_m[:,2]`, and
  preserves particles outside valid support.

Verification:

- 6 model, 8 trainer, and 5 particle-lift tests pass in the separate `test`
  environment; all three sources compile and `git diff --check` passes;
- an admitted loaded state with 303,829 particles and 14,161 valid cells passes
  every particle count, source-field, finite-state, x/y, z-reconstruction,
  unsupported-particle, model-identity, and reprojection check;
- the requested perturbed surface is reproduced to a maximum 2.329e-10 m;
- direct particle reprojection differs from the stored Newton tensor surface by
  as much as 0.980 mm, so the lift correctly computes its displacement from the
  particle-projected source surface rather than assuming both representations
  are identical;
- current, not-yet-frozen identities are:
  - training contract: `190b5f959c865dafeda612d797984563c768e4d458ea60e7fcaf331a2912942b`;
  - shared model: `c68f21a7bfb953311e8fe36dbc90fb75002800476d818a92f4c8c6e1157e2d46`;
  - trainer: `6030b9e17658f70566c59381e6f9fc3e1aaab93962cf1ac72299f36c53ef2baf`;
  - particle lift: `ece4ed4838666eb206f7217749c7c509614018758c0ee217b657eff068c06b80`;
  - model tests: `edab22e827417f04ae2498c540b7e7d093475a7269dc0cb0829b56be85b46a94`;
  - trainer tests: `909db90895162e2e4cc24db4941002545d395ccbec10dba3a2d44895da440b12`;
  - particle-lift tests: `20c9e03939b65a1962993b9f37a90ab5fec225f951f16f9627506a6ff36c01ec`.

Bulk checkpoint:

- the same frozen supervisor has completed 39/64 Chrono train/validation
  targets and all 39 pass acceptance;
- every completed target retains 14,161 finite valid cells; accepted loading
  times currently span 0.349--0.382 s;
- episode 039 is active, no bulk Newton response or tensor pair exists yet,
  and all 24 protected test targets remain absent.

Matched-sensitivity audit and decision:

- the frozen 88-input design contains no repeated initial-surface/action/force
  identity with only soil parameters changed, so it cannot alone evaluate the
  required direction-of-change gate;
- the already-frozen five-case physical material rectangle does provide a true
  matched sweep: one common initial bed and action with the four parameter-box
  corners and center;
- the final evaluator will use those five cases only for directional
  sensitivity. Their targets are prohibited from fitting, normalization,
  uncertainty calibration, model selection, and locked-test accuracy;
- this resolves the evidence route without changing the immutable 88 inputs or
  opening any protected target.

Claim boundary and next gate:

- these results validate implementation semantics and particle-state integrity,
  not predictive accuracy;
- next finish and test the evaluator that binds model selection before the
  one-shot test opener, includes B0--B3/H0--H2 and parameter controls, and emits
  the complete gate report. Training remains blocked until the 64 train/
  validation pairs are admitted.

### 2026-10-26 — Fresh-session handoff reconciled with evaluator preflight and live bulk state

Question:

- what is the newest verified implementation and campaign state that a fresh
  session must inherit before continuing Phase 1?

Verified implementation state:

- the prospective evaluator configuration and partial evaluator source now
  encode the exact 24 locked-test identities and group counts, require model
  selection before unlock, define deterministic soil-parameter shuffle and
  constant-parameter controls, bind the five-case matched sensitivity suite,
  and predeclare metrics, bootstrap intervals, uncertainty coverage, particle
  integrity, and Phase 1 thresholds;
- evaluator stages for prerequisite validation, immutable plan construction,
  explicit unlock/open markers, protected Chrono generation, test-bed reuse,
  Newton execution, tensor admission, surface metrics, and whole-episode
  bootstrap intervals are implemented;
- prediction, particle-lift evaluation, baseline aggregation, sensitivity
  scoring, and the final gate report are not yet implemented. The evaluator is
  therefore partial, has not been frozen, and cannot open the test set;
- 6 model, 8 trainer, 5 particle-lift, and 7 evaluator tests pass as standalone
  unittest files in the `test` environment: 26 focused tests total. All eight
  source/test files compile, and `git diff --check` passes;
- current, not-yet-frozen evaluator identities are:
  - evaluation contract: `919aeb97c4be25fdaf4c436d3fa3613497b408f956b9e4ab5e9390e4f98f5724`;
  - evaluator source: `970411ec350a90841d729f0663045cb4bd7ea29061c2606528fa6f00c172db59`;
  - evaluator tests: `1611a21c9218f0aa7cde7f595922daadf9c4d974675a90ac63dd172cfe4305e4`.

Live campaign reconciliation:

- the original single frozen bulk supervisor remains active;
- 40/64 train/validation Chrono targets are complete and all 40 pass the
  frozen acceptance checks;
- every completed target has 14,161 valid cells and accepted loaded times span
  0.349--0.382 s;
- `p1_train_joint-design_039` is the latest complete target and episode 040 is
  active;
- no bulk Newton response or tensor pair exists yet;
- filesystem inspection found no protected test-target directory, evaluation
  plan, unlock marker, or opened marker. All 24 test targets remain absent and
  locked.

Decision and next gate:

- this entry supersedes the earlier live counters but does not rewrite their
  historical observations;
- finish and test the evaluator's prediction, controls, baselines, particle
  lift, sensitivity, uncertainty, aggregation, and report stages while the
  frozen Chrono campaign continues;
- do not freeze a training plan or fit models until all 64 train/validation
  pairs are admitted, and do not construct an evaluation plan or unlock the
  test targets until validation-only selection is complete.

Claim boundary:

- the new evidence establishes evaluator preflight structure and lock
  preservation, not trained-model correctness or predictive performance;
- Phase 1 remains active and no exit gate has yet been claimed.

## Maintenance contract

For every subsequent experiment:

1. append a dated entry containing the question, frozen inputs, commands or
   implementation, measured evidence, decision, claim boundary, and artifacts;
2. update the current snapshot from machine-readable evidence;
3. update [phase1.md](phase1.md) in the same change if the permitted next work,
   domain, routing, or exit status changes;
4. never rewrite a failed result into a pass or delete a superseded result;
5. keep validation and test targets locked according to the frozen plan.

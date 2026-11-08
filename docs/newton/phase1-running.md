# Phase 1 chronological implementation and evidence record

Last updated: 2026-11-07

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
| parameter-box operational screening | complete at bounded coarse-prior level | surfaces 6/6, Chrono 5/5, and common-base v2 Newton pairings 5/5 pass; strict mechanics remains false; real-soil realism was not established |
| initial-surface generator and qualification | complete | all six analytic and native SCM checks pass |
| Newton field export | repeat-qualified for v1/v2 H2; predictive value failed | corrected v3 passes three fresh repeats; stress and elastic entered H2, plastic was excluded; H2 is worse than H1 |
| neural-training environment | frozen in training plan | conda `test`: Python 3.11.15, NumPy 2.4.6, PyTorch 2.13.0+cu130, CUDA 13.0, RTX 5090 |
| 12-episode engineering smoke set | complete and passed | 12/12 admitted: 8 train/4 validation/0 test; protected test targets unopened; full-dataset permission true |
| 88-episode admitted dataset | train/validation subset complete and passed | 64/64 train/validation Chrono/Newton/tensor pairs admitted, five preparations accepted, all aggregate checks true; bulk SHA-256 `d8090a35...`; protected test remained unopened through this gate |
| U-Net model ladder | fit and selected on validation | 12 models completed; B3/H0/H1/H2 share 289,172 parameters; selected seeds are 20261024/20261023/20261023/20261023; calibration fit on validation only |
| v1 locked evaluator | preserved failed | evaluation plan SHA-256 `789720e5...`; 24/24 responses complete; 23/24 admitted; episode 009 alone fails the frozen guide guard; prediction correctly refused |
| v2 recovery contract | conditional evaluation complete; prospective identity deviation preserved | numerical admission passes 24/24; all predictions and audits exist; the episode-012 serial retry and post-lock JSON compatibility shim remain explicit qualifications |
| Phase 1 exit | evaluated and failed, not demonstrated | conditional v2 report passes 33/49 checks and fails 16; H1 improves raw Newton but fails joint, material-use, parameter-control, and sensitivity gates; H2 is worse than H1 |
| post-v2 research boundary | documented; next contract remains prospective | first prove one-action prediction over a justified plausible simulator domain; sequential world model follows; deeper terramechanics triggers claim/expertise review |
| successor engineering smoke | complete and passed | 12/12 complete and admitted at 8 train/4 validation/0 test/0 sensitivity; summary SHA-256 `8c66e79f513ef40f1e680efad719500713f57523c9013c4907fa880060919989`; remaining train/validation permitted; protected denied |
| successor bulk train/validation | complete; legacy failure preserved; artifact-only recovery passed | 64/64 Chrono/Newton/tensor pairs complete; v1 summary `f80c9f...8955` fails only member 019's legacy guide check; recovery plan `aedca2...5ab6` binds 384 artifacts and passing summary `dfacb7...1d81`; no rerun or protected access |
| successor training | complete and selected on validation | plan `2b3b71...0426` and train-only normalization `969a33...9d6` frozen; 15/15 equal-capacity fits complete; selection/calibration summary `3a2ffe...e08e` used only 16 validation episodes |
| successor protected evaluation | complete and closed failed | 30/30 admitted after preserved serial and artifact-only qualifications; prediction `b825bd...a2dc3` passes sensitivity direction for all five models; final report `c5995e...c3f9` permits no claim; qualification `9205c2...1570` records `phase1_goal_achieved=false` |
| successor model-type result | direct D0 strongest; Newton-conditioned variants add no demonstrated value | protected median RMSE, loaded footprint / loaded twice-radius / post footprint / post twice-radius: D0 1.825/1.856/1.825/1.855 mm; R0 3.161/2.859/3.595/3.369; R1 3.309/2.964/3.815/3.395; R2S 3.304/2.949/3.869/3.406; R2E 3.574/2.988/4.045/3.492 |
| direct-v4 D1 validation | authoritative validation passed | no-refit D0 sensitivity wrapper; confirmation plan `a6d3dc...d4428` preceded validation; summary `ed23f6...a22` passes 20/20 on 16 validation episodes with zero v1 test use |
| direct-v4 protected confirmation | Chrono generation active | surfaces 5101--5106 qualified; joint unlock/open completed once; protected plan `7385bb...63ab`; at 20:19 EST on 2026-11-07, 14/30 Chrono manifests complete and members 014/015 active; downstream bed/Newton/admission/prediction/report pending |

The operational simulator screen, corrected v3 latent-input qualification, and
12-episode engineering smoke set have passed. The smoke aggregate now permits
generation
of the already frozen 88-episode dataset. V2's generated pass remains
audit-rejected; v3 supersedes it with three fresh repeats and enforcement of
every required family. Stress and elastic channels are admitted to H2, while
plastic is excluded. Predictive usefulness is now measured: H1 improves
substantially on raw Newton, but the complete conditional v2 report fails the
Phase 1 exit; H2 is worse than H1. V3 remains the prospective branch for any
revised model or protocol rather than a retroactive requirement for closing v2.

The next branch does not inherit a claim that the current parameter box is
realistic or that more internal soil state is desirable. Its parameter domain
must be justified prospectively as engineering-plausible, its inputs should
remain robotics-defensible or directly exported by MPM, and any need for new
constitutive soil theory pauses execution for a claim/expertise review.

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

### 2026-10-26 — Locked evaluator implementation preflight completed and bulk supervisor resumed

Questions:

- can the prospective locked evaluator execute every Phase 1 accuracy,
  parameter-use, uncertainty, particle-state, and latent-mechanics gate without
  opening a test target before validation-only selection?
- can the stopped frozen bulk Chrono campaign resume from episode 040 without
  deleting evidence or changing its source/input/environment identities?

Implementation:

- completed the evaluator's selected-checkpoint loading and hash checks,
  B0--B3/H0--H2 prediction paths, frozen Phase 0 MLP application, H1 shuffled
  and constant-soil controls, and validation-calibrated uncertainty intervals;
- hardened the constant-soil control after a requirement audit: both the
  seeded soil-vector derangement and the train-mean soil substitution now
  require a strictly positive paired whole-episode bootstrap lower bound in
  every loaded/post-unload local region;
- added per-episode footprint, twice-radius, valid-bed, recovery, and
  uncertainty metrics plus whole-episode bootstrap aggregation for every
  required baseline, ablation, failure-tail, and holdout-group gate;
- connected every selected neural prediction to the deterministic particle
  lift and its bitwise state-preservation/surface-reproduction audit;
- implemented H2-versus-H1 evidence classification. H2 is named final only
  when it improves prediction or is neutral without a worse failure tail, and
  a positive latent-value claim remains restricted to demonstrated
  improvement;
- bound the already-frozen five-case common-action material rectangle to an
  evaluation-only H1 directional-sensitivity diagnostic. The exact Chrono
  repeatability result supplies a zero oracle floor; four rectangle edges,
  sinkage, displaced volume, peak recovery, prediction saturation, and center
  smoothness are checked without using those cases for fitting,
  normalization, calibration, selection, or locked accuracy;
- added explicit inference rejection for out-of-box center, radius, force,
  bekker_kphi, and friction values;
- enabled resumable predict and report stages while retaining refusal of
  incomplete outputs and the selection-before-unlock plan gate;
- hardened final reporting to recompute the plan, rehash every selected model
  artifact, revalidate every locked target and prediction/lift artifact, prove
  the qualified H2 latent families are present, and embed aggregate, baseline,
  control, uncertainty, sensitivity, latent, and explicit failure-case evidence
  rather than reporting gate booleans alone.

Verification:

- 6 model, 8 trainer, 5 particle-lift, and 12 evaluator tests pass as
  standalone unittest files in the test environment: 31 focused tests total;
- the added end-to-end integrity test constructs a coherent locked artifact
  tree, verifies every final-report integrity check, mutates a prediction
  archive, and proves that the final reporter rejects the changed hash;
- all four implementation sources and the evaluator test compile;
- git diff --check passes;
- a real admitted smoke artifact produces a finite Phase 0 baseline with
  shape (2, 121, 121) and value range -0.020930--0.035932 m;
- the real frozen screen_material_klo_flo sensitivity adapter produces all
  26 declared spatial channels, 14,161 valid cells, and two finite 121-by-121
  targets;
- no evaluation plan, unlock marker, opened marker, evaluation Chrono target,
  training plan, model fit, or model score was created.

Current prospective evaluator identities:

| Artifact | SHA-256 |
| --- | --- |
| evaluation contract | 6be5ee960f9933829d13dd52156e71d53741e597604c412d999d494de45841a9 |
| evaluator source | 11f8ed8dc58a455ad429f96e7753d3855418fd7d588ddb2355fa13deeacc77d1 |
| evaluator tests | d99f9cf7cd6333aa478599fe1ac6c7a128a77ad2f564c1e88e6b4a66df64dea2 |

Bulk recovery evidence:

- the previously documented supervisor was no longer running after the Phase 1
  implementation commit;
- episodes 000--039 remained accepted. Episode 040 contained only a zero-byte
  local execution log, while its paired Chrono target directory was absent;
- the frozen runner overwrites that log at launch and refuses an existing
  incomplete target directory, so episode 040 could be retried without
  deleting or replacing simulation evidence;
- the same frozen bulk_plan.json and source hashes now supervise episode 040.
  The Chrono subprocess was observed healthy at 99.9% CPU; the accepted count
  remains 40/64 until its manifest passes the frozen checks.

Decision and next gate:

- evaluator implementation preflight is complete but remains unfrozen until
  the admitted bulk dataset permits training and validation-only model
  selection supplies the selected artifacts;
- continue the single frozen bulk supervisor through all 64 Chrono targets,
  then build five priors, run and admit 64 Newton/tensor pairs, freeze the
  training plan, fit the declared seeds, and select on validation;
- only after selection may the evaluator plan, unlock marker, or protected
  test targets be created.

Claim boundary:

- this establishes complete prospective evaluation machinery and a safe bulk
  resume, not predictive accuracy, useful mechanics latents, or Phase 1 exit.

### 2026-10-27 — Bulk Chrono generation completed and first Newton pairs admitted

Question:

- can the frozen bulk route advance from completed Chrono targets through fresh
  per-surface Newton preparation, fixed-time response, schema-v2 tensor export,
  and bounded coarse-prior admission without relaxing the strict-mechanics
  claim boundary or opening protected test targets?

Execution and verified evidence:

- the single resumed supervisor completed all 64/64 train/validation Chrono
  targets under the frozen 48/16/24 plan; the 24 test targets remain absent;
- all five metric particle beds were built from Chrono initial states only.
  Loaded/post-unload targets were not consumed by bed construction;
- surface-1101 through surface-1104 preparations are accepted. Their
  first-equilibrium times are 0.677500, 0.680750, 0.679250, and 0.706000 s;
  settled-surface RMSE values are 2.105972, 2.133287, 2.172294, and 2.124932 mm;
  maximum errors are 4.472049, 4.485341, 4.594764, and 4.360292 mm. All remain
  below the unchanged 5 mm RMSE and 10 mm maximum-error gates;
- responses `p1_train_joint-design_000` and `_001` completed with finite
  schema-v2 states, accepted guides/support/timing, and gross-interaction checks.
  Their observed maximum particle-center penetrations are 4.986 and 6.976
  micrometers, involving at most 24/303,829 and 11/304,940 particles,
  respectively, against the inherited 0.5 mm gross-depth limit;
- `python3 scripts/run_phase1_dataset_bulk.py --config
  configs/phase1_dataset_bulk_v1.json --stage analyze` exported separate input
  and target archives and marked both episodes `complete: true` and `admitted:
  true`. Every tensor check passes, stress and elastic remain the qualified H2
  families, and plastic remains excluded;
- response `p1_train_joint-design_002` subsequently completed in 2,580.927 s
  with seven affected centers and 8.879 micrometers maximum penetration. The
  same analyzer exported finite schema-v2 tensors and admitted the episode;
- response `p1_train_joint-design_003` completed in 2,577.062 s with
  18/304,707 affected particle centers and 11.766 micrometers maximum
  penetration. Its analyzer-produced summary is complete and admitted; every
  numerical, interaction, tensor, memory, signal, and baseline-loss check
  passes, with stress and elastic retained and plastic excluded;
- response `p1_train_joint-design_004` completed in 2,577.972 s with
  6/303,829 affected particle centers and 7.043 micrometers maximum
  penetration. Its analyzer-produced summary is likewise complete and
  admitted with every declared numerical, interaction, and tensor check true;
- the response manifests correctly retain `accepted: false` and
  `mechanics_qualified: false` because a few particle centers cross the strict
  analytic zero-penetration boundary. Phase 1 admission does not rewrite that
  failed strict claim: it applies the prospectively frozen bounded coarse-prior
  numerical and gross-interaction policy;
- the aggregate bulk summary remains `failed_or_incomplete`, with
  `training_dataset_ready: false`, because only 5/64 Newton/tensor pairs are
  complete. Response 005 is active from the accepted surface-1102 prior.

Decision and next gate:

- continue the same supervisor through the remaining preparation and 59
  responses, then run one complete frozen analyzer pass after generation
  finishes and require all 64 episode admissions before freezing normalization
  or a training plan. Per-episode analysis is not a generation dependency;
- a guarded waiter is attached to supervisor PID 1615782. After that supervisor
  exits it counts completed `newton_cylinder_manifest.json` artifacts, refuses
  analysis unless the count is exactly 64, and otherwise invokes the frozen
  bulk analyzer once. It does not launch or alter any simulation;
- a second fail-closed waiter is attached behind the analyzer. It first
  requires the resulting bulk summary to be `passed`, training-ready, and all
  checks true; only then may it freeze normalization/training, fit all declared
  variants and seeds, and perform validation-only selection. The locked
  evaluator plan, explicit unlock, 24-test Chrono/Newton generation, admission,
  prediction, sensitivity diagnostic, and final report follow in that order
  under `set -e`, so any failed prerequisite stops all later stages. At queue
  time no evaluation plan, unlock marker, or protected target existed;
- do not alter source, inputs, solver settings, split membership, or gates in
  response to runtime duration, and do not unlock test targets.

Claim boundary:

- this demonstrates five admitted bulk training pairs and four accepted
  per-surface priors, not a passed bulk dataset, trained model, predictive
  result, strict Newton mechanics result, or Phase 1 exit.

### 2026-10-27 — Bulk response generation passed its midpoint

Question:

- is the unchanged frozen supervisor continuing through the response set while
  the requested end-of-generation analysis boundary and protected-test lock
  remain intact?

Execution and verified evidence:

- supervisor PID 1615782 remains live and unchanged;
- 33/64 `newton_cylinder_manifest.json` response artifacts are complete;
- `p1_train_joint-design_033`, the 34th response, is active from the accepted
  surface-1102 prior;
- four preparation manifests remain present and accepted. Reserved validation
  surface 2101 has not yet reached its preparation point;
- the analyzer has not run since the explicit generation-first decision, so
  the machine aggregate correctly remains at the previously analyzed 5/64
  admitted tensor pairs rather than overstating unexamined responses;
- the guarded analyzer and fail-closed post-bulk pipeline waiters remain live.
  No evaluation plan, test-unlock marker, or protected target has been created.

Decision and next gate:

- leave the single supervisor uninterrupted through the remaining 31 response
  manifests and the final validation-surface preparation;
- after exactly 64 response manifests exist, run the one queued analyzer pass;
  only a passing 64/64 bulk summary may release training and subsequent locked
  evaluation stages.

Claim boundary:

- this is response-generation progress only. The 28 newly generated but
  unanalyzed responses are not yet claimed as admitted data.

### 2026-10-28 — All 48 training responses generated

Question:

- can the unchanged supervisor complete the training-response partition and
  cross into validation while preserving the generation-first analysis
  boundary and every downstream lock?

Execution and verified evidence:

- all 48 `p1_train_joint-design_<NNN>` response manifests are complete;
- the supervisor advanced without intervention to
  `p1_validation_joint-design_000`, the first of 16 validation responses;
- 48/64 total response manifests and four accepted preparation manifests are
  present. The fifth preparation remains correctly deferred until reserved
  validation surface 2101 is first encountered;
- no intermediate analyzer pass was run: the aggregate still truthfully
  records only the five pairs analyzed before the generation-first decision;
- supervisor PID 1615782, the exactly-64 guarded analyzer, and the fail-closed
  training/evaluation pipeline remain live. No protected target or evaluation
  unlock artifact exists.

Decision and next gate:

- continue serially through the 16 validation responses and the surface-2101
  preparation, then allow the guarded analyzer to evaluate all 64 pairs once;
- do not freeze normalization or release model fitting unless the resulting
  bulk summary passes every admission check.

Claim boundary:

- completing raw training responses does not admit them, fit a model, or open
  validation/test evidence for model selection or final accuracy claims.

### 2026-10-28 — Bulk admitted, validation selection frozen, and test opened in order

Questions:

- does the one deferred analyzer pass admit every train/validation pair before
  normalization or model fitting?
- do all declared model seeds complete and selection/calibration remain
  validation-only before the protected test set is opened exactly once?

Bulk admission evidence:

- `bulk_summary.json` reports `status=passed`,
  `training_dataset_ready=true`, 48/16/0 train/validation/test counts, and all
  eight aggregate checks true;
- all 64 train/validation episodes are complete and admitted, all five
  surface-specific preparations are accepted, stress and elastic remain the
  qualified H2 families, and plastic remains excluded;
- bulk-summary SHA-256:
  `d8090a355d1d0bcee75fc0bf383e29dae3cb11cdaccd14c57fffc980e25dd731`.

Training and validation-only selection evidence:

- the frozen training plan records Python 3.11.15, NumPy 2.4.6, PyTorch
  2.13.0+cu130, CUDA 13.0, RTX 5090 capability 12.0, train-only
  normalization, and equal 289,172-parameter B3/H0/H1/H2 models;
- all four variants completed all three declared seeds: 12 model cards,
  checkpoints, and histories are hash-bound;
- selected validation results are:

| Variant | Seed | Best epoch | Epochs run | Validation twice-radius RMSE, mm |
| --- | ---: | ---: | ---: | ---: |
| B3 | 20261024 | 144 | 180 | 1.926194 |
| H0 | 20261023 | 16 | 52 | 3.091343 |
| H1 | 20261023 | 234 | 270 | 2.991279 |
| H2 | 20261023 | 289 | 300 | 3.126597 |

- the nominal-90% validation conformal multipliers for loaded/post-unload are
  B3 1.223013/1.219725, H0 1.488343/1.458998, H1 1.779016/1.735759, and H2
  1.595651/1.776142;
- training-plan, normalization-file, and selection-summary SHA-256 values are
  `c5054641d72645de0a7f3f24be31f507b8cbb6de82965c15a09f14d17d46da21`,
  `42e0d5b264215c87300fc162c328fa17b52122ebeb74c2c3859054321b945bb0`,
  and `bc2b77f3ca66b2a9eaffac681e6180dc12c4ad200db37909624924d7850e8b79`.

Ordered test opening evidence:

- only after selection, the evaluator froze the 24-episode plan with SHA-256
  `789720e5b58922d8a860e06c73b9abfa96910415e55709bc714e0e9333d001c4`;
- the explicit unlock marker has SHA-256
  `1927e11750b8b7ff6f37d458893c734a5b3b6e31770cf01f0c824729216b4f4c`
  and binds the frozen selection, test manifest, and original test lock;
- the open-once marker has SHA-256
  `f806643a6b8665123f619dd784531a5f17fa3ad1a44e4eee98ed56502b5cf593`
  and records `targets_opened=true` for exactly 24 identities;
- three test Chrono targets are accepted and
  `p1_test_unseen-position_003` is active at 99.9% CPU. Test Newton generation
  has not started.

Decision and next gate:

- continue the single fail-closed locked-evaluation chain through all 24
  Chrono targets, per-surface preparations, 24 Newton responses, admission,
  prediction, sensitivity, and final report;
- make no Phase 1 success claim from validation metrics. Only the predeclared
  locked report may decide accuracy, parameter use, uncertainty, particle
  integrity, latent value, and Phase 1 exit.

Claim boundary:

- this proves leakage-safe bulk admission, fitting, validation selection, and
  ordered test opening. It does not yet prove any locked-test performance gate.

### 2026-10-29 — Locked test Chrono generation completed and Newton evaluation started

Question and frozen execution:

- can the single post-selection evaluation chain generate every protected
  Chrono target and advance into Newton without reopening selection, changing
  the domain, or bypassing a failed episode;
- the active chain remains bound to evaluation-plan SHA-256
  `789720e5b58922d8a860e06c73b9abfa96910415e55709bc714e0e9333d001c4`,
  unlock SHA-256
  `1927e11750b8b7ff6f37d458893c734a5b3b6e31770cf01f0c824729216b4f4c`,
  and open-once SHA-256
  `f806643a6b8665123f619dd784531a5f17fa3ad1a44e4eee98ed56502b5cf593`;
- the shell supervisor retains `set -e`, so bed preparation, Newton response,
  admission, prediction, sensitivity, and reporting cannot run after a failed
  prerequisite.

Measured evidence:

- all 24 locked Chrono directories contain accepted manifests, covering the
  five frozen holdout groups and every planned test identity;
- the completed bed stage produced metric-bed metadata for all five test
  surface seeds: 1101, 1102, 1103, 1104, and 3101;
- the surface-1101 Newton preparation manifest records `status=accepted` and
  `accepted=true`;
- no Newton response manifest exists yet; response
  `p1_test_unseen-position_000` is active at 100% process utilization;
- no admission, prediction, sensitivity, or final-report artifact exists yet.

Decision and next gate:

- continue the same fail-closed chain through all 24 Newton responses, then
  require the aggregate test admission summary before inference;
- keep every final accuracy, parameter-use, uncertainty, latent-value, and
  Phase 1 exit claim closed until the locked report exists.

Claim boundary:

- this proves complete locked-test Chrono generation and ordered entry into
  Newton evaluation. It does not prove Newton admission or any predictive gate.

### 2026-10-29 — Newton responses reached 21/24 and exposed one guide failure

Question and frozen execution:

- can the locked Newton stage complete the five reusable surface preparations
  and advance through the 24 responses without changing the already opened
  evaluation contract;
- the original supervisor and frozen evaluator remain in control, with no
  duplicate response generation or early admission run.

Measured evidence:

- all five surface preparation manifests record `accepted=true`;
- response manifests exist for the first 21 planned identities, indices
  000--020, and response 021 is active;
- all 21 completed responses are finite, preparation-converged, schema-v2,
  independently timed, and record that Chrono target time does not control the
  Newton observation time;
- 20/21 completed responses pass the vertical-guide guard;
- `p1_test_unseen-force_009` records horizontal speed
  `1.0746966052822614e-6` m/s against the frozen `1.0e-6` m/s guide tolerance,
  so `guide_constraint_passed=false` despite passing the other inspected raw
  response checks;
- the locked admission implementation requires every numerical check,
  including `guide`, to pass. No admission summary exists yet.

Decision and next gate:

- preserve the observed guide failure and continue the same chain through the
  remaining three Newton responses and aggregate admission;
- do not loosen the tolerance, regenerate episode 009, or permit prediction
  after a failed admission, because any such post-test change would violate the
  frozen evaluation contract;
- use the generated aggregate summary as the authoritative admission result.

Claim boundary:

- this establishes raw Newton progress and one prospective numerical-integrity
  failure. It does not yet establish the aggregate test-admission result or any
  predictive-performance gate.

### 2026-10-30 — Locked test admission failed 23/24 and prediction was refused

Question and frozen execution:

- after all 24 Newton responses complete, does the prospectively frozen
  aggregate admit every episode and permit the locked prediction stage;
- the original `set -e` supervisor ran Newton, admission, and then attempted
  prediction without any rule, source, threshold, or episode regeneration.

Measured evidence:

- 24/24 Chrono targets, 5/5 reusable preparations, and 24/24 Newton response
  manifests are complete;
- all 24 responses are finite, preparation-converged, schema-v2, independently
  timed, and pass support, duration, gross-interaction, and tensor checks;
- the aggregate admits 23/24 episodes. `p1_test_unseen-force_009` is the only
  rejected episode and `numerical_checks.guide=false` is its only failed check;
- episode 009 records horizontal guide speed
  `1.0746966052822614e-6` m/s against the frozen `1.0e-6` m/s tolerance;
- `test_dataset_summary.json` records `status=failed_or_incomplete`,
  `prediction_permitted=false`, `all_complete=true`, and
  `all_admitted=false`; its SHA-256 is
  `b44f9852faf9d90d849e5e3b2cf6ef5bcb3295f3a4d5fe37fc36a28a31aacb06`;
- its evaluation-plan, unlock, open, selected-test-manifest, and test-lock
  identities match the frozen values;
- all 24 episode summaries and locked tensor manifests exist. Every tensor
  check passes for all 24 episodes;
- the frozen evaluation plan binds the Newton response source SHA-256
  `df7176babca225bc50ceab08cc9bc69e8ce69a9be9e23d85474a0858c6c5c783`;
- the prediction stage raised `RuntimeError: locked test admission does not
  permit prediction`, the supervisor exited with status 1, and no prediction,
  sensitivity, or final-evaluation report exists.

Decision and next gate:

- preserve the failed admission as the authoritative outcome of evaluation v1;
- do not relax the guide threshold, alter the hash-bound response source,
  regenerate episode 009, exclude it, or bypass `prediction_permitted` after
  seeing the test result;
- the current evaluation cannot satisfy the Phase 1 exit contract. Any further
  attempt would require a separately authorized, prospectively frozen recovery
  design with new protected test evidence rather than rewriting v1.

Claim boundary:

- this proves the complete ordered v1 execution and its integrity-gate failure.
  It does not establish predictive accuracy, parameter use, uncertainty,
  particle-lift integrity on predictions, latent value, or Phase 1 success.

### 2026-10-30 — Prospective v2 recovery feasibility checked without opening targets

Question:

- if separately authorized, can a new evaluation correct the dimensional guide
  tolerance prospectively, retain the frozen selected models, and use entirely
  new protected test inputs rather than rewriting the failed v1 result.

Read-only numerical evidence:

- all 64 admitted train/validation Newton responses pass the original guide
  guard. Their maximum horizontal guide speed is
  `4.86764403939447e-7` m/s, with p95 `3.084474765634814e-7` m/s;
- across 83 available non-test Phase 1 response manifests, all pass the guide
  guard and the maximum horizontal guide speed is
  `5.484218449073836e-7` m/s;
- a candidate v2 rule would keep the original `1.0e-6` tolerances for
  horizontal position, angular speed, and orientation error, while declaring
  a separate horizontal-speed tolerance of `5.0e-6` m/s. That value is a
  rounded 10x envelope over the canonical 64 train/validation maximum and is
  still roughly 9x the broader non-test maximum;
- this is a prospective design proposal, not a reinterpretation of v1. The v1
  episode-009 failure and aggregate remain unchanged.

Read-only split feasibility:

- an in-memory candidate construction produced 24 unique inputs with the same
  required 5/5/5/4/5 holdout-group counts;
- none of the 24 physical input tuples overlaps any train, validation, or v1
  test tuple in the frozen 88-episode plan;
- the unseen-position centers, unseen-force values, and unseen-material pairs
  have zero exact overlap with train/validation, and the proposed reserved
  surface seed 3102 is absent from all existing episodes;
- no candidate manifest, contract, unlock marker, target, preparation, response,
  or prediction was written by this feasibility check.

Required authorization boundary:

- a valid v2 would need a new versioned contract, explicit component-specific
  guide tolerances, source/tests, output roots, qualified surface seed 3102,
  and a frozen target-free 24-input manifest before generating any target;
- the v1-selected checkpoints, normalization, calibration, architecture, and
  selection SHA-256 must remain fixed, so v1 test observations cannot influence
  training or model selection;
- only a new one-shot unlock/open sequence may release the new protected test
  targets. The failed v1 artifacts remain immutable provenance;
- this is a meaningful expansion beyond the frozen v1 evaluation and therefore
  awaits explicit user authorization before implementation or simulation.

Claim boundary:

- this establishes that a leakage-safe recovery design appears technically
  feasible. It does not authorize v2, qualify seed 3102, freeze a replacement
  test set, or change the failed Phase 1 status.

### 2026-10-30 — Dual-Newton quick throughput preflight passed

Question and isolation:

- can two independent Newton responses share the single RTX 5090 with useful
  aggregate speedup, bounded resources, and no material change to outputs;
- the benchmark used two admitted train episodes, their existing accepted
  preparations, the frozen Newton source/configuration, shortened fixed
  durations, distinct fresh `/tmp` outputs, and no locked-test artifacts.

Frozen workload:

- cases: `p1_train_joint-design_000` on surface 1101 and
  `p1_train_joint-design_001` on surface 1102;
- timestep 0.25 ms, pre-settle 0.35 s with a required 0.02 s speed hold,
  loaded duration 0.05 s, and residual duration 0.05 s;
- source SHA-256
  `df7176babca225bc50ceab08cc9bc69e8ce69a9be9e23d85474a0858c6c5c783`;
- configuration SHA-256
  `8808c41c64d2e70c966d1c8ba527e1a02f0e08b68551e13acee184d81040cefa`;
- reproducible harness and machine-readable result are in
  `diagnostics/phase1_newton_dual_benchmark_20261030/`.

Measured throughput and resources:

- serial case times were 451.67 s and 450.37 s; serial batch wall time was
  902.064498 s;
- concurrent case times were 675.33 s and 675.09 s; dual batch wall time was
  675.337420 s;
- dual execution therefore gives 1.3357x aggregate throughput, a 33.57%
  throughput increase and 25.13% batch-wall reduction, while each individual
  case slows by about 49.7%;
- median/peak GPU utilization rose from 44%/49% serial to 92%/93% dual;
- peak GPU memory rose from 1,827 MiB to 3,682 MiB, peak power from 218.15 W to
  278.8 W, and peak temperature from 66 C to 70 C. All remain bounded on the
  32,607 MiB RTX 5090.

Numerical and gate comparison:

- all four runs exited zero, remained finite, converged their preparations,
  passed the guide guard, and recorded zero maximum inside particle centers;
- case A state arrays and heightmaps are bitwise equal between serial and dual;
- case B's largest height difference is `7.450580596923828e-9` m, largest
  particle-position difference is `3.5390257835388184e-8` m, largest velocity
  difference is `8.756751412875019e-7` m/s, and largest stress difference is
  `0.3330078125` Pa;
- both cases preserve exact sinkage and every admission-relevant Boolean
  outcome. The observed floating-point drift is negligible at the surface
  metric scale but proves concurrency is not universally bitwise deterministic.

Decision and next gate:

- the quick dual-worker preflight passes and supports two Newton workers as the
  provisional v2 execution setting;
- before freezing v2 device/execution identity, run one full-duration dual pair
  on non-test episodes and compare it with their existing serial bulk responses;
- do not infer support for three or more workers, and do not change the failed
  v1 result or its artifacts.

Claim boundary:

- this establishes a bounded two-case throughput and stability result. It does
  not yet qualify dual execution for the full v2 test campaign or authorize v2.

### 2026-10-30 — Full-duration dual-Newton qualification passed with measured drift

Question and isolation:

- does the two-worker result persist at the complete frozen Newton durations,
  without touching any locked test input, target, response, or prediction;
- the qualification reran the same two admitted train episodes used by the
  quick preflight in distinct fresh `/tmp` outputs and compared them with their
  existing serial bulk responses produced by the identical source and config.

Frozen workload and identity:

- cases: `p1_train_joint-design_000` on surface 1101 and
  `p1_train_joint-design_001` on surface 1102;
- timestep 0.25 ms, pre-settle 2.0 s with a required 0.02 s speed hold, loaded
  duration 0.35 s, and residual duration 0.25 s;
- source SHA-256
  `df7176babca225bc50ceab08cc9bc69e8ce69a9be9e23d85474a0858c6c5c783`;
- configuration SHA-256
  `8808c41c64d2e70c966d1c8ba527e1a02f0e08b68551e13acee184d81040cefa`;
- full-duration harness SHA-256
  `897742e407f818791756a264f55108b66db527f9740d4dfa127ae3c6457f5115`;
- reproducible harness and machine-readable result are in
  `diagnostics/phase1_newton_dual_benchmark_20261030/`.

Measured throughput and resources:

- existing serial case times were 2,577.92 s and 2,563.22 s, for a summed
  serial baseline of 5,141.145235 s (85.69 min);
- concurrent case times were 3,879.67 s and 3,874.67 s, with a dual batch wall
  time of 3,879.682623 s (64.66 min);
- dual execution therefore gives 1.3251x aggregate throughput, a 32.51%
  throughput increase and 24.54% batch-wall reduction;
- over 1,911 telemetry samples, median/peak GPU utilization was 92%/93%, peak
  GPU memory was 3,810 MiB of 32,607 MiB, peak power was 279.72 W, and peak
  temperature was 69 C;
- if the complete 24-response Newton stage scales by the measured factor, its
  historical approximately 17.4 h serial duration projects to approximately
  13.1 h with two workers, saving about 4.3 h. This is a projection, not a
  measured end-to-end v2 duration.

Numerical and gate comparison:

- both concurrent jobs exited zero, remained finite, converged preparation,
  passed the guide constraint, and preserved all compared admission-relevant
  Boolean outcomes from the serial baselines;
- concurrency is not bitwise deterministic at full duration. The largest
  particle-position difference was `1.853369176387787e-4` m (maximum RMSE
  `2.5300840678935122e-6` m), and the largest sinkage differences were
  `9.909272193908691e-7` m and `1.341104507446289e-6` m;
- the largest heightmap difference was `0.02243602555245161` m at an individual
  cell, while the maximum heightmap RMSE was `1.929494808520769e-4` m. Loaded
  contact counts changed from 326/403 serial to 331/401 dual;
- the largest particle-velocity difference was `0.016404508613049984` m/s
  (maximum RMSE `9.590996489925675e-5` m/s), and the largest stress difference
  was 17,758.484375 Pa (maximum RMSE 69.63468 Pa);
- guide horizontal speeds remained well below the proposed prospective v2
  `5.0e-6` m/s threshold: dual values were `1.1913311715136694e-7` and
  `2.3580015287581918e-8` m/s.

Decision and execution freeze:

- the full-duration two-worker operational qualification passes: the speedup
  persists, resource use is bounded, both runs complete, and gate outcomes are
  stable on these representative non-test cases;
- use exactly two Newton workers as the recommended prospective v2 execution
  identity, and freeze that identity before producing any new protected target;
- the measured numerical drift must remain part of the provenance. Do not
  claim bitwise equivalence to serial execution, and do not mix serial and dual
  target generation within one frozen evaluation;
- do not infer support for three or more workers. No v2 simulation is authorized
  by this benchmark, and the failed v1 result remains unchanged.

Claim boundary:

- this qualifies the two-worker execution mode operationally on two full-length
  non-test responses. It does not prove deterministic equivalence, qualify
  three-worker execution, authorize v2, or establish Phase 1 success.

### 2026-10-30 — Authorized v2 recovery frozen before target generation

Authorization and invariant:

- the user explicitly authorized resuming the Phase 1 goal through evaluation
  v2;
- v1 remains immutable failed evidence. Its evaluation-plan SHA-256 is
  `789720e5b58922d8a860e06c73b9abfa96910415e55709bc714e0e9333d001c4`
  and its failed dataset-summary SHA-256 is
  `b44f9852faf9d90d849e5e3b2cf6ef5bcb3295f3a4d5fe37fc36a28a31aacb06`;
- v2 reuses the exact v1 validation-selected checkpoints, normalization, and
  uncertainty calibration without fitting or selection. The bound selection
  summary remains
  `bc2b77f3ca66b2a9eaffac681e6180dc12c4ad200db37909624924d7850e8b79`.

Prospective contract and tests:

- the new versioned contract is
  `configs/phase1_evaluation_v2.json`, SHA-256
  `c06c75f587dc1af868a48eeb6651f3a5b51a23fd9247f84a1415c4b9537d21cf`;
- it declares component-specific guide tolerances before any v2 target:
  1 micrometer horizontal position error, 5 micrometers/second horizontal
  speed, 1 microradian/second angular speed, and 1e-6 quaternion error;
- it freezes exactly two independent Newton processes on `cuda:0`, matching
  the passed full-duration throughput qualification. Serial and dual target
  generation may not be mixed inside v2, and three workers remain unqualified;
- the target-free planner SHA-256 is
  `eb6d71561431a43cc3258e1a0cb29f225638dcb02a006c172e8db06f0c97bff8`;
  the component-aware evaluator SHA-256 is
  `d8e18b80112090dc1d1cb8d792e4931f2b090d6107690c2d6d82a47004551201`;
- 45 relevant contract, surface, dataset, bulk, lift, evaluator, and v2 tests
  pass. The five v2-specific tests cover recovery identity, split disjointness,
  guide dimensions, surface routing, and target-absence refusal.

Target-free manifest:

- the frozen manifest contains 24 unique v2 identities with the required
  5 unseen-position, 5 unseen-force, 5 unseen-material-combination, 4
  unseen-initial-surface, and 5 joint-combination counts;
- all physical inputs are unique and have zero exact overlap with any train,
  validation, or v1 test input in the original 88-episode plan;
- the holdout-specific position centers, force values, and material pairs have
  zero exact overlap with train/validation, and reserved seed 3102 is absent
  from all v1 episodes;
- manifest SHA-256:
  `c419accc02799134d169993f6adf0b43a68050bba5416f1bf9a3b34b1cdace30`;
  test-lock SHA-256:
  `569a5fc323ee3c82039e1504cb6172bc51d47904a73277bf2a23ec02aa85a520`;
  selected-test payload SHA-256:
  `5cebc673f4be6c9e80167a85f378455a0d4f9102e9399d95c1090c5177469c27`.

Reserved-surface qualification:

- deterministic surface 3102 passes shape, finiteness, zero-mean, relief,
  slope, correlation-floor, and flat-boundary checks;
- its maximum relief is 4.75 mm, maximum local slope is 4.861 degrees, and
  spectral correlation floor is 51.702 mm;
- native Chrono SCM round-trip maximum error is 4.612 micrometers, below the
  prospective 10-micrometer gate;
- qualification-summary SHA-256:
  `2307c45de630f192a1e1b218a6135e034737dbb6f10d293f46dab9d86c4b3d8b`.

Frozen evaluator plan and next gate:

- evaluator-plan SHA-256:
  `3c5c92d52aa915178da908df999791ac1ce793690182e36e4073dd70d1b96f62`;
- it hashes the v2 config and sources, all five heightmaps/generator records/
  qualification records, the unchanged selection summary and model artifacts,
  the v1 failure evidence, and the new target-free manifest;
- the Chrono v2 output root, per-episode v2 output directory, unlock marker,
  and open-once marker were all absent at plan freeze;
- the next permitted action is the explicit v2 unlock followed by one-shot
  Chrono generation. No target existed or was opened by the work above.

Claim boundary:

- this establishes a prospectively frozen, leakage-safe recovery evaluation and
  qualifies its reserved surface. It does not establish v2 target admission,
  predictive accuracy, parameter use, uncertainty validity, latent value, or
  Phase 1 success.

### 2026-10-31 — V2 unlocked; responses complete with retry identity deviation

Unlock and protected-target generation:

- the already frozen v2 plan was unlocked exactly once against the unchanged
  validation selection; unlock SHA-256 is
  `94770f15eb6abd6ef06a36848863419a6d2d116084f580a33c177a445612ebbc`
  and open-once marker SHA-256 is
  `61c0bb96d581e97fe6248bf589640f87a3c1f8e9bbffb6ad1f04cec2aaafb336`;
- all 24 locked Chrono episodes completed and passed the oracle contract. The
  minimum valid-cell count is 14,161; loaded observation times span
  0.349--0.379 s; no episode failed validation;
- four independent Chrono lanes were used. Near the end, the sequential lane
  began a duplicate episode 012 immediately before the independently running
  authoritative 012 published. The duplicate was interrupted before
  publication; process inspection confirmed only one authoritative process
  remained for episodes 012, 016, and 020, and those original runs completed.
  No destination had two live writers after the intervention, and the final
  24 artifacts validate individually. This operational race is retained here
  rather than hidden by the aggregate pass.

Newton preparation and execution:

- metric beds were built for surface seeds 1101, 1102, 1103, 1104, and 3102;
- all five serial prior preparations completed and the evaluator then launched
  exactly two response workers on `cuda:0`, as prospectively frozen;
- the first pair, `p1_v2_test_unseen-position_000` and
  `p1_v2_test_unseen-position_001`, completed in 3,875.943 s and 3,873.916 s.
  The evaluator immediately advanced to episodes 002 and 003;
- both completed responses are finite, their fresh in-process preparations
  converged, their independent fixed durations are 0.35 s loaded and 0.25 s
  post-unload, and both expose state schema v2 with 14,161 valid surface cells;
- all four prospective guide components pass. Maximum values across the pair
  are `1.5947939246040944e-9` m horizontal-position error,
  `6.903726521288223e-8` m/s horizontal speed,
  `3.409574201234187e-8` rad/s angular speed, and
  `2.365264897151059e-9` quaternion error;
- the diagnostic manifests mark strict zero-center mechanics false because
  transient maxima are 18 and 12 inside particle centers, with maximum depths
  `1.2209638953208923e-5` m and `5.461275577545166e-6` m. This is not silently
  relabeled as strict mechanics success. The prospectively frozen Phase 1
  evaluator instead applies the inherited gross-interaction depth and affected-
  fraction bounds; both completed cases are inside those test-admission bounds.
- by 05:42 EDT, responses 000--009 were complete and exactly two workers were
  active on 010/011. Across the first 10 responses, wall times span
  3,866.590--3,875.943 s; every response is finite, preparation-converged,
  independently timed, schema v2, and has at least 14,161 valid cells;
- no prospective guide component fails in the first 10. Their maxima are
  `3.1389341566924633e-9` m horizontal-position error,
  `2.3989860168501543e-7` m/s horizontal speed,
  `1.1858849027373984e-7` rad/s angular speed, and
  `2.700738133969118e-9` quaternion error. The maximum transient inside count
  is 23 and maximum center depth is `1.2977048754692078e-5` m; strict mechanics
  remains false where declared, while the prospective gross-interaction checks
  remain within their frozen bounds.

Episode-012 failure and retry provenance:

- the original two-worker queue produced 23 complete manifests. Episode
  `p1_v2_test_unseen-material-combination_012` failed after the loaded solve
  when schema-v2 export rejected a non-finite `plastic_jacobian`; it published
  no response manifest, and the enclosing Newton stage exited nonzero after
  the remaining already-queued episodes completed;
- the failed log SHA-256 is
  `3326fc283565293ab619ac6fdb33b2daa4bd88bb574a2c131e2e535cd881650a`.
  Its 32 MiB partial initial-state artifacts and log were moved, not deleted,
  to the episode-local
  `failed_attempts/attempt_1_nonfinite_plastic_jacobian/` archive;
- after the user explicitly authorized a retry, the unchanged frozen Newton
  stage skipped the 23 existing manifests and ran only missing episode 012.
  The retry completed in 2,597.432 s, is finite, preparation-converged,
  independently timed, schema v2, and has 14,161 valid cells. Its response-
  manifest SHA-256 is
  `c6caddb5d25ac91478aacefb8d3024c707e3a1359ca7958c5d425a6c9cb596ea`;
- all 24 response manifests now exist. Every response is finite, preparation-
  converged, independently timed, schema v2, and has at least 14,161 valid
  cells. There are no prospective guide failures; maxima are
  `3.741965133550808e-9` m horizontal-position error,
  `2.3989860168501543e-7` m/s horizontal speed,
  `1.1858849027373984e-7` rad/s angular speed, and
  `2.700738133969118e-9` quaternion error. The maximum transient inside count
  is 25 and maximum center depth is `1.3265758752822876e-5` m;
- numerical completeness does not repair provenance. Although the frozen
  configuration still declared `newton_workers=2`, only episode 012 was
  missing, so its successful retry ran with one live Newton process. This
  mixes a serial response with the 23 dual-worker responses and directly
  violates the prospective statement that exactly two independent processes
  would be used and serial/dual target generation would not be mixed.

Decision and next gate:

- Chrono target generation, Newton-prior preparation, and 24 response artifacts
  are complete;
- do not run aggregate admission or prediction as if v2 were a clean pass. The
  current evaluator checks configured worker count but does not prove per-run
  concurrent occupancy, so a machine-green admission would not cure the
  execution-identity violation;
- preserve v1 and v2 evidence. Any further recovery must be prospective and
  must define failure/retry semantics and a consistent execution identity
  before producing another protected response set.

Claim boundary:

- the evidence above proves target completeness and numerical response-contract
  checks for all 24 artifacts. It also disproves compliance with v2's frozen
  execution identity. It does not prove aggregate v2 admission, predictive
  accuracy, parameter use, calibrated uncertainty, H2 value, or Phase 1 exit.

### 2026-10-31 — Conditional v2 analysis completed; predictive exit failed

Question and authorization:

- advance from complete numerical artifacts into admission and prediction,
  while preserving the serial episode-012 retry as a qualification and keeping
  v3 as the prospective branch instead of repeatedly moving the current exit;
- treat v2 as an engineering/conditional analysis, not as a clean prospective
  confirmation and not as permission to erase either the v1 or v2 failures.

Admission and implementation evidence:

- the five v2 contract tests and twelve frozen evaluator tests pass before
  admission;
- `test_dataset_summary.json` passes all seven aggregate checks, admits 24/24
  episodes, and sets `prediction_permitted=true`; its SHA-256 is
  `786f88be0a047a1bd28d6849ab3c1b4d674a87399070cdec01902cca4e313c96`;
- all 24 episode predictions and particle-lift audits completed. The original
  prediction process then reached matched sensitivity and failed while writing
  a NumPy scalar Boolean through Python's standard JSON encoder. This was a
  serialization boundary defect after inference, not a numerical-model or
  artifact failure;
- the frozen evaluator and evaluator-test SHA-256 values were restored and
  verified against the locked plan as
  `d8e18b80112090dc1d1cb8d792e4931f2b090d6107690c2d6d82a47004551201`
  and
  `d99f9cf7cd6333aa478599fe1ac6c7a128a77ad2f564c1e88e6b4a66df64dea2`;
- `scripts/continue_phase1_evaluation_v2.py`, SHA-256
  `db0b7e0812699e37cfb724492f5da17d1b52caecafe06b070bc71dc41a01df9b`,
  is a separate post-lock compatibility wrapper. It recursively converts NumPy
  JSON scalars to value-equivalent built-ins and delegates every computation to
  the unchanged evaluator. Its focused regression test passes. This shim is
  part of the conditional-analysis qualification and is not represented as a
  prospectively frozen v2 source;
- resumed prediction wrote `prediction_summary.json`, SHA-256
  `bb5bdfc24a9b7f4fbe43129804ff62a7be66bf7bb2f2888697c9009dc37e85af`,
  and `sensitivity_summary.json`, SHA-256
  `e1c5a42c6a0c6f08148f92bae5ea601b9b9d692450f8d3d1384c9e99c91e0cbd`;
- final reporting revalidated all ten artifact-integrity checks and wrote
  `final_evaluation_report.json`, SHA-256
  `0182a02015051d6c58e78323a306eb4e5f133fbab27fe73726403868777f00be`.

Measured predictive evidence:

- H1 median RMSE reduction versus raw Newton is 74.23% loaded/footprint,
  63.18% loaded/twice-radius, 60.52% post-unload/footprint, and 46.13%
  post-unload/twice-radius. All 24 episodes improve over both raw Newton and the
  no-deformation baseline in every local checkpoint/region combination; no
  episode is worse than raw Newton or exceeds the 1 mm failure-tail allowance;
- H1 reduction versus the Phase 0 MLP is 23.21%, 11.56%, 14.73%, and 4.06% in
  those same four combinations. The post-unload/twice-radius comparison misses
  the frozen 10% threshold and its paired-bootstrap interval crosses zero;
- B3 is better than H1 on all four five-episode joint-holdout comparisons, so
  every frozen H1-versus-B3 joint gate fails;
- H1 improves on H0 by only 1.58--5.97% on material holdouts, below the frozen
  10% requirement in all four comparisons. Shuffling soil parameters degrades
  H1 significantly in three of four comparisons, but the loaded/twice-radius
  lower bound crosses zero. Replacing parameters with the train mean fails to
  degrade H1 significantly in all four comparisons. The report therefore does
  not support strong parameter use;
- matched sensitivity is nonsaturated and smooth inside the material box, but
  direction agreement is 6/8 eligible comparisons, or 0.75 versus the frozen
  0.90 gate. Both mismatches occur on the low-`bekker_kphi` friction edge for
  loaded peak sinkage and loaded displaced volume. The report's
  `sensitivity:identity` composite is false because sensitivity status failed;
  the stored evaluation-plan hash itself still matches;
- nominal-90% uncertainty coverage estimates span 0.892--0.924 and all
  uncertainty checks pass;
- H2 is worse than H1 in every local checkpoint/region aggregate, so latent
  status is `worse_or_solver_artifact`, positive latent-value claims are not
  permitted, and H1 is retained only as the report's fallback final model.

Decision and next branch:

- the conditional final report passes 33/49 checks and fails 16. It records
  `status=failed`, `phase1_exit_demonstrated=false`, and
  `supported_claim_permitted=false`;
- v2 is complete as a measured, informative failed evaluation. It is no longer
  an unfinished execution blocker, and no additional rerun is required merely
  to close or report it;
- if pursued, v3 must be frozen prospectively after deciding what model or
  protocol changes address the measured joint-generalization, parameter-use,
  sensitivity, and H2 failures. Its goal is confirmation of a specific repair,
  not automatic regeneration of another test set until a pass appears.

Claim boundary:

- the evidence establishes conditional v2 admission, inference behavior,
  uncertainty, sensitivity, particle-artifact integrity, and a failed Phase 1
  exit under explicit provenance qualifications. It does not establish a clean
  prospective v2 confirmation, strong parameter-conditioned generalization,
  useful H2 latent mechanics, or Phase 1 success.

### 2026-10-31 — World-model destination and expertise-aware boundary recorded

Question:

- what longer-term capability should the one-action predictor support;
- how can the experiment vary meaningful parameters without claiming soil
  expertise or calibrated terramechanics; and
- when should increasing mechanics complexity trigger a claim review instead
  of another routine model revision?

Decision:

- the eventual goal is an action-conditioned world model that predicts bed
  state across a proposed footprint sequence so a cost planner can score it;
- the immediate research question remains one action: characterize where the
  frozen Newton prior does not generalize and test whether a learned direct or
  Newton-conditioned predictor supplies a reliable observable-state estimate;
- sequential training follows only after a satisfactory one-action mapping is
  demonstrated. Independent endpoint accuracy is not sequential-world-model
  evidence;
- the v1/v2 parameter rectangle is operationally qualified inside Chrono and
  Newton, but it has not been established as realistic for a named soil. A
  successor that calls its range realistic or engineering-plausible must cite
  the range basis, units, coupled fixed values, and applicable soil class
  before target generation;
- the preferred inputs are quantities defensible in robotics: geometry,
  displacement, velocity or momentum, load, contact, and support. Qualified
  MPM stress and deformation may be evaluated as simulator-native features,
  but their use does not validate the MPM constitutive law or real-soil
  interpretation;
- new soil-specific constitutive descriptors, hand-built higher-order soil
  features, fitted material laws, and claims about real-soil properties remain
  outside the default scope;
- the simplest model that passes the prospective generalization contract
  should be selected. Improvement over raw Newton supports a neural-correction
  claim; added value from Newton requires the hybrid also to beat the
  capacity-controlled direct model.

Complexity stop/review gate:

Before adding a new soil parameter, internal field, constitutive relation, or
derived soil feature, the next prospective plan must answer:

1. Which measured held-out failure requires it?
2. Is it already a semantically qualified simulator state, or does it require
   new soil theory?
3. Can its range and meaning be justified without implying unsupported
   calibration or material identification?
4. Can a controlled ablation isolate its predictive value?

If these questions cannot be answered inside the robotics-facing boundary,
pause the pipeline and revisit the claim, data source, and need for
terramechanics collaboration. Do not treat deeper soil theory as an automatic
consequence of model underperformance.

Interpretation of completed v2:

- H1's large improvement over raw Newton shows that neural supplementation is
  plausible in the bounded one-action task;
- B3 beating H1 on every joint holdout means the present experiment did not
  demonstrate added generalization value from the Newton prior;
- H2 being worse than H1 means the bundled stress/elastic expansion did not
  demonstrate predictive value and does not justify adding more mechanics
  channels;
- the next model revision should use separate low-complexity ablations rather
  than broaden the terramechanical representation.

Documentation changes:

- [phase1.md](phase1.md) now records the world-model destination, parameter
  plausibility policy, robotics-facing representation boundary, prospective
  direct-versus-hybrid decision rule, and explicit complexity stop gate;
- the completed v1/v2 contracts, metrics, failures, and historical chronology
  remain unchanged.

Claim boundary:

- this is a research-order and scope decision. It does not prove that the
  current parameter box is realistic, validate any constitutive model, reopen
  v2, establish one-action success, or demonstrate sequential planning.

### 2026-10-31 — Source-backed one-action successor draft started

Question:

- can the post-v2 experiment begin inside a defensible parameter domain without
  expanding into soil identification or deeper terramechanics; and
- what minimum model ladder distinguishes neural correction, Newton-added
  value, and individual MPM field value?

Source audit:

- official Chrono documentation defines the SCM parameter semantics and supplies
  a cohesionless reference at `Kphi=2e6`, `Kc=0`, `n=1.1`, cohesion `0 Pa`,
  friction `30 degrees`, and Janosi shear `0.01 m`;
- Lim et al. report a dry-sand point at `n=1.1` and
  `Kphi=1528.43 kN/m^(n+2)`, with test-condition dependence;
- Gallina et al. report approximately zero cohesion, `30 degree` friction, and
  `n=1.1` for dry quartz sand and warn about cross-test parameter transfer.

Draft domain and precheck:

- engineering-plausible, cohesionless dry-sand-like synthetic SCM; explicitly
  not a named-soil calibration;
- vary only `bekker_kphi=1.5e6--2.0e6 N/m^(n+2)`; fix `Kc=0`, `n=1.1`,
  cohesion `0 Pa`, friction `30 degrees`, Janosi `0.01 m`, elastic stiffness
  `2e8 Pa/m`, and damping `3e4 Pa s/m`;
- retain the existing 35 mm-radius vertical action and frozen Newton prior for
  screening; no tangential motion or rotation is introduced;
- only `Kphi` varies because this action directly excites vertical
  pressure-sinkage; varying friction would repeat a weakly excited control;
- the force endpoints imply 7.966/11.949 kPa nominal pressure, and the elementary
  `Kc=0` relation gives 6.58--12.36 mm sinkage. This is a sanity check only.

Draft model ladder and decision rules:

- `B0` no deformation; `B1` raw Newton; `D0` direct prediction from initial
  surface, action, force, and `Kphi`;
- `R0` adds raw Newton surface displacement; `R1` separately adds occupancy,
  mass, vertical velocity, contact count, and normal impulse;
- `R2S` and `R2E` separately test stress and elastic deformation; plastic and a
  bundled stress-plus-elastic variant are excluded;
- beating `B1` supports neural correction; beating both `B1` and
  capacity-controlled `D0` on joint holdouts supports Newton-added value;
- a solver field has value only if its isolated ablation beats `R1` without a
  worse failure tail.

Input-plan freeze:

- six explicit identities reuse qualified surface seed `1101` and centered
  action geometry while requiring entirely fresh response artifacts;
- every canonical case hash and the draft-contract source binding recompute;
- [screening_plan.json](../../diagnostics/phase1_one_action_successor_v1/screening_plan.json)
  has SHA-256
  `5878257631bd0099afae3ce0c0792dd5f90c301515855a9de2292e8ad8bde2c4`
  and status `input_only_frozen_no_execution`.

Next permitted gate:

- execute the six fresh engineering-screen cases; do not generate bulk,
  training, validation, or protected targets;
- test response validity, direction above repeatability, endpoint separation,
  and Newton admission before freezing a successor data/evaluation contract.

Artifact and claim boundary:

- [phase1_one_action_successor_v1.json](../../configs/phase1_one_action_successor_v1.json)
  records sources, domain, precheck, screen, ladder, and data policy with status
  `draft_precontract_no_target_generation` and `frozen=false`;
- this starts successor design but does not qualify its range, authorize bulk
  or protected target generation, demonstrate Newton failure or neural
  correction, or support a real-soil claim.

### 2026-10-31 — Six-case successor engineering screen launched

Implementation and preflight:

- added explicit Chrono CLI overrides for `Kc`, `n`, cohesion, Janosi shear,
  elastic stiffness, and damping so the successor cannot inherit the historical
  v1 fixed soil values;
- added `run_phase1_one_action_successor_screen.py`, an isolated runner that
  binds the frozen six identities to fresh Chrono and Newton artifacts while
  refusing bulk or protected target generation;
- syntax, CLI, case-hash, contract-binding, fixed-Newton, and clean-output-root
  preflights pass;
- the reused input is qualified surface seed `1101`; no prior Chrono or Newton
  response artifact is reused.

Frozen execution:

- execution plan:
  `outputs/validity_experiment/newton/phase1_one_action_successor_v1/screening/successor_screen_execution_plan.json`;
- execution-plan SHA-256:
  `f9347f18b7dc3c1f09b6fe2425f4c341c91abecb3b54f5c5037eb5ea527bb0b1`;
- command: `python3 scripts/run_phase1_one_action_successor_screen.py --stage all --workers 2`;
- supervisor PID: `1908840`;
- run log:
  `outputs/validity_experiment/newton/phase1_one_action_successor_v1/screening/run.log`.

Launch status:

- two Chrono workers are active on the `Kphi=1.5e6` force endpoints;
- all six Chrono cases are queued, followed by metric-bed construction, six
  fresh Newton responses, and admission analysis;
- status is running; no screen result or successor qualification is claimed
  until the final summary exists and is checked.

### 2026-11-01 — Common-flat-base successor recovery frozen and launched

Measured antecedent result:

- all six successor Chrono episodes completed and are accepted;
- all six legacy metric beds and Newton preparation computations completed;
- every preparation reached equilibrium but was rejected by the frozen surface
  gate: settled-surface RMSE is 6.072 mm versus the 5 mm limit, while maximum
  absolute error is 7.631 mm versus the 10 mm limit;
- all six failures reproduce the preserved fixed-depth/undulating-bottom bed
  defect, so no Newton response from the original screen is admissible;
- this is not a non-finite-state or dual-worker collision failure.

Recovery identity and procedure:

- the six accepted Chrono episodes and all six rejected preparations are
  preserved; Chrono is not rerun;
- the recovery verifies that all six Chrono episodes share the same initial
  state, constructs one fresh exact-surface/global-lattice/common-flat-base
  metric bed, and runs one fresh shared preparation;
- after preparation admission it schedules six fresh responses, one against
  each case's Chrono target, with independent fixed Newton timing of 0.35 s
  loaded plus 0.25 s post-unload and exactly two workers;
- recovery runner:
  `scripts/recover_phase1_one_action_successor_common_base.py`;
- frozen plan:
  `outputs/validity_experiment/newton/phase1_one_action_successor_v1/common_base_recovery_v1/recovery_plan.json`;
- recovery-plan SHA-256:
  `927941694b8d73b24d8063a8f65a6dd629aa435a6b9477f02097974c9ab6d91f`;
- command:
  `python3 scripts/recover_phase1_one_action_successor_common_base.py --stage newton --workers 2`;
- detached supervisor PID at launch: `1940032`;
- run log:
  `outputs/validity_experiment/newton/phase1_one_action_successor_v1/common_base_recovery_v1/run.log`.

Launch status and claim boundary:

- the common-base metric bed exists and the fresh shared preparation is active
  on `cuda:0`; response workers begin only if that preparation is accepted;
- bulk, training, validation, and protected-target generation remain prohibited;
- this launch does not establish response validity, directional signal,
  endpoint separation, Newton generalization failure, or neural-correction
  value. Those decisions require the completed recovery and subsequent
  prospective analysis.


### 2026-11-01 — Successor recovery and directional screen passed

Recovery admission:

- the common-flat-base preparation is accepted and all six fresh Newton
  responses completed;
- all six pairings pass Chrono acceptance, preparation acceptance and
  convergence, finite-state, guide, surface-support, independent-fixed-timing,
  gross penetration-depth, and affected-particle-fraction checks;
- strict mechanics remains unqualified because 19--20 particle centers enter
  the analytic cylinder by 5.646--11.278 micrometers, but this is far inside
  the inherited 0.5 mm coarse-prior limit;
- `recovery_summary.json` records
  `pipeline_passed_directional_analysis_pending` and 6/6 admission; it is not
  rewritten after the separate directional decision.

Frozen directional analysis:

- analyzer: `scripts/analyze_phase1_one_action_successor_direction.py`;
- plan:
  `outputs/validity_experiment/newton/phase1_one_action_successor_v1/common_base_recovery_v1/directional_analysis_plan.json`;
- plan SHA-256:
  `ac2e98fb3cab966c22ac8ae47cc4e11829fe25eae66d773b3bc80daafcfd838f`;
- summary:
  `outputs/validity_experiment/newton/phase1_one_action_successor_v1/common_base_recovery_v1/directional_analysis_summary.json`;
- summary SHA-256:
  `a58d86a5f7b581f1bd3ee3aef936d68992bc7d587f2d255d9d87081277a06e1b`.

Measured decision:

- every adjacent `Kphi` comparison is monotone in the expected direction for
  footprint peak depression, mean depression, and positive displaced volume at
  loaded and post-unload checkpoints and both force levels;
- endpoint mean-depression separation is 5.725 mm at 30.65625 N and 6.974 mm
  at 45.984375 N; peak-depression separation is 5.750 and 6.915 mm;
- the applicable same-build Chrono heightmaps are bitwise identical, so their
  metric repeatability floor is zero and every endpoint separation exceeds it;
- deformation increases with force for all `Kphi`, phases, and metrics;
- the aggregate status is
  `screen_passed_successor_contract_freeze_permitted`.

Decision and claim boundary:

- the next permitted action is to freeze a prospective successor data and
  evaluation contract;
- bulk, training, validation, test, and protected-target generation remain
  prohibited until that separate contract is frozen;
- this screen establishes usable numerical pairings and a resolvable synthetic
  parameter signal. It does not demonstrate Newton generalization failure,
  neural correction, sequential rollout accuracy, real-soil fidelity, or
  planner benefit.

### 2026-11-01 — Successor contract frozen and 12-episode smoke launched

Prospective contract and target-free split:

- froze
  [phase1_one_action_successor_contract_v1.json](../../configs/phase1_one_action_successor_contract_v1.json)
  at SHA-256
  `834db42409fd48dfb2136b93192dd5fd22233733ac09dfaf8d7e5bcaf6aef4fd`;
- froze 48 training, 16 validation, 24 protected test, and six protected
  matched-sensitivity inputs before any new response target was generated;
- the target-free dataset plan, physical manifest, test lock, and sensitivity
  lock have SHA-256 values
  `b326a96bbbcd82e863984eef016e0d320c479f5ec1b7ff937ec4da031d1070ef`,
  `2df4ced81aa85a88536b72bd28c8a736e8dabf898ffeb891891678b9e7682725`,
  `0390d46bfd5860b08518f3b99ab116084f24138939c04435f29582c3feedf713`,
  and `a003ec52f2fb43c94d5d760e06a924c3b49809a0ddf415a6abbb718ff18a4139`;
- all 94 physical input hashes are unique; split and holdout labels are not
  allowed to hide a duplicate physical condition;
- only `bekker_kphi` varies and enters the global parameter vector. Fixed SCM
  and Newton values are explicit. Plastic state remains excluded, while stress
  and elastic fields are separately optional R2S/R2E ablations.

Fresh-surface qualification:

- generated and qualified surface seeds 4101, 4102, 4103, 4104, 4201, and
  4301 using analytic checks and an exact native Chrono SCM initialization;
- qualification plan SHA-256:
  `1fc635c1ed468b00316fcce62a32d98012e524c0f4c6ef5ed1bf2b32b99e9a9e`;
- passing summary SHA-256:
  `a3935396fa99362c1a94aa4fa960408cd0efedc158b3dbf0649e2645ec13d7f1`;
- no Chrono response target was generated during surface qualification.

Smoke implementation and preflight:

- added an isolated runner that adapts the proven Phase 1 data pipeline while
  binding every fixed SCM parameter, preserving the common-flat-base Newton
  prior, and reducing the model parameter vector to `bekker_kphi` alone;
- an initial no-target preflight exposed a recursive base-result binding and a
  missing config argument in source-manifest construction. Both were repaired
  before a runtime plan or response target existed, and regression coverage was
  added;
- eight focused smoke-runner tests and seven target-free planner tests pass;
- froze exactly train members 000--007 and validation members 000--003, with
  zero test and zero protected-sensitivity members;
- frozen smoke-plan SHA-256:
  `3d861da58edaf697ca7b5b494589fce99b926a7a3c13c19dec19026eedbafee7`;
- selected-membership SHA-256:
  `9eee6ab977f499a475debc94e589d031a4657a7e3b68cd59a9e5ee5a7f38a042`;
- rerunning `--stage plan --workers 2` reproduces the identical plan and hash.

Launch and current evidence:

- command:
  `python3 scripts/run_phase1_one_action_successor_smoke.py --stage all --workers 2`;
- detached supervisor PID at launch: `1955843`;
- run log:
  `outputs/validity_experiment/newton/phase1_one_action_successor_contract_v1/dataset_smoke_v1/run.log`;
- exactly two Chrono workers are active on the first two authorized training
  members; their live commands include every frozen soil override;
- the remaining ten smoke members are queued by the two-worker executor;
- remaining train/validation generation, all protected test and sensitivity
  targets, and all model training remain prohibited until the completed smoke
  summary passes its aggregate gate.

Claim boundary:

- freezing and launching the smoke set does not demonstrate Newton
  generalization failure, neural correction, Newton-added value, sequential
  rollout accuracy, real-soil fidelity, or planner benefit;
- the immediate next decision is solely whether the 12 engineering episodes
  pass numerical, tensor, routing, and signal checks strongly enough to permit
  the remaining unprotected train/validation dataset.

### 2026-11-01 — Successor bulk handoff prepared behind the smoke gate

Question:

- can the next stage be prepared without polling the active smoke set,
  changing its frozen identity, rerunning its 12 members, or weakening either
  protected-target lock?

Prepared implementation:

- config:
  [phase1_one_action_successor_bulk_v1.json](../../configs/phase1_one_action_successor_bulk_v1.json),
  SHA-256
  `9fabff0b6a22d5858b33afb129dc1fe4d2dd87717e242309d239752ec99a3935`;
- runner:
  [run_phase1_one_action_successor_bulk.py](../../scripts/run_phase1_one_action_successor_bulk.py),
  SHA-256
  `1f69d5ddb02de88129f429eef90ec19bcb31f8d1fa70a5f8b4137bbc63e3b21b`;
- focused tests:
  [test_phase1_one_action_successor_bulk.py](../../tests/test_phase1_one_action_successor_bulk.py),
  SHA-256
  `5a3cbef2c78845a968934f284abd4e77a2733956bd65734480634e5d91bc09ee`.

Frozen behavior:

- the bulk campaign shares the smoke local and Chrono output roots so admitted
  smoke targets become dataset members rather than being regenerated;
- after a passing smoke result, bulk-plan freeze will bind the exact hashes of
  every reused episode summary, tensor manifest, input archive, target archive,
  Newton manifest, and Chrono manifest;
- the execution selector excludes the eight smoke train and four smoke
  validation identities, leaving exactly 40 new train and 12 new validation
  episodes;
- requesting a smoke identity raises a regeneration error; requesting a test,
  sensitivity, or unknown identity raises a protected/unknown error;
- the 24 test and six protected-sensitivity locks are independently recomputed
  from the target-free dataset plan before planning;
- the reserved validation surface 4201 is already qualified, but its first
  response remains prohibited until the smoke gate passes and the bulk plan is
  frozen.

Gate and verification:

- `require_smoke_pass` requires the exact smoke config and plan hashes, a
  passing 12-member summary bound to that plan, 12/12 complete and admitted,
  explicit remaining-train/validation permission, and explicit denial of
  test/sensitivity permission;
- the future bulk plan will additionally bind source, environment, dataset,
  surface, smoke-summary, and reused-artifact hashes before the first remaining
  target;
- eight focused bulk tests pass, and the combined successor planner, smoke,
  and bulk suites pass 23/23;
- the test suite caught and corrected a copied test-lock typo in the human
  documentation and new wrapper. The authoritative dataset and smoke plans
  were unchanged; the correct lock ends in `...feedf713`.

Current boundary:

- no smoke status was polled during this work;
- no bulk plan was frozen and no bulk, test, sensitivity, or training target
  was generated;
- on the next user-requested recheck, the smoke summary must be evaluated first.
  Only a verified pass can permit freezing the bulk plan, which still opens
  only the remaining unprotected train/validation members.

### 2026-11-01 — Successor model and training layer prepared behind the bulk gate

Question:

- can the frozen successor ladder be implemented now without polling smoke,
  weakening the first/second-order representation boundary, opening protected
  targets, or fitting against an incomplete dataset?

Prepared sources:

- training contract:
  [phase1_one_action_successor_training_v1.json](../../configs/phase1_one_action_successor_training_v1.json),
  SHA-256
  `eabe4e5d689a6d8fbf698ac64a3c5a46c3e96f818281446c21e2140de28185f3`;
- successor model:
  [phase1_one_action_successor_model.py](../../scripts/phase1_one_action_successor_model.py),
  SHA-256
  `ed1d865f4592adb834fd9bb61280c07df88615acd97a2db843e9f6fb85c9c4cf`;
- isolated trainer adapter:
  [train_phase1_one_action_successor.py](../../scripts/train_phase1_one_action_successor.py),
  SHA-256
  `790dc3ac1c4222638634e454053bb5f6602b8b4f080da7451e0d8935071a0470`;
- focused tests:
  [test_phase1_one_action_successor_training.py](../../tests/test_phase1_one_action_successor_training.py),
  SHA-256
  `d2d81c1196337ad8d4eb05015df7dc4657a067bbbb154f0c84758ac5bd39500b`.

Model I/O and ablations:

- one shared three-level U-Net retains identical trainable capacity for D0,
  R0, R1, R2S, and R2E through immutable input masks;
- D0 receives initial geometry, action geometry, force, and `Kphi` and predicts
  a bounded correction around the initial surface;
- R0 adds loaded/post-unload Newton displacement and predicts around the raw
  Newton surfaces;
- R1 separately adds column occupancy/count, mass, action-aligned vertical
  velocity, contact count, and normal impulse at both checkpoints;
- R2S adds mean and von Mises stress to R1; R2E instead adds elastic Jacobian
  and isochoric shear. No combined R2 model is present;
- plastic state is absent from the channel schema;
- the global condition is exactly center x/y, normal force, and `Kphi`.
  Friction is fixed by the experiment and is not passed as a model feature.

Training and selection boundary:

- three seeds are frozen prospectively: 20261101, 20261102, and 20261103;
- normalization and correction bounds fit the 48 training episodes only;
- early stopping, per-variant seed selection, conformal calibration, and any
  optional-ablation promotion use the 16 validation episodes only;
- D0/R0/R1 are the core selection pool. R2S/R2E are separate optional
  ablations and may be promoted only by the later frozen margin/failure-tail
  rules;
- the selection artifact explicitly records both pools and keeps test and
  sensitivity targets unopened;
- the existing loss, bounded residual, uncertainty, particle-lift, and
  preservation machinery is reused through an isolated adapter; historical
  B3/H0/H1/H2 sources and evidence are not rewritten.

Gate and verification:

- training-plan freeze requires a passing 64-member bulk summary, 48/16/0/0
  counts, all episodes complete and admitted, the exact test and sensitivity
  locks, and explicit denial of protected-target permission;
- nine focused successor model/training tests pass in the declared PyTorch
  environment;
- the six historical model tests and eight historical trainer tests also pass,
  proving the adapter did not alter their implementation path;
- the default system Python lacks Torch and the declared PyTorch environment
  lacks Pytest, so the repository-consistent direct `unittest` entry points
  were used. This is an environment fact, not a model failure.

Current boundary:

- no smoke status was polled, no bulk or training plan was frozen, no model was
  fit, and no validation, test, or sensitivity prediction was inspected;
- the immediate runtime order is unchanged: verify smoke on user request,
  freeze and complete the remaining unprotected bulk dataset only after a
  pass, then freeze training before the first fit.

### 2026-11-01 — Successor evaluation and protected runtime prepared behind selection

Question:

- can the final one-action evaluation path be implemented prospectively without
  polling the active smoke set, freezing an evaluation plan before validation
  selection, opening either protected set, or weakening the frozen claim
  boundary?

Prepared sources:

- evaluation contract:
  [phase1_one_action_successor_evaluation_v1.json](../../configs/phase1_one_action_successor_evaluation_v1.json),
  SHA-256
  `2c86c607c0c9839a3b806345a76e41a76e61e1e2501d23a0e37056ce2261dd5f`;
- evaluator, integrity checks, statistical gates, and claim router:
  [evaluate_phase1_one_action_successor.py](../../scripts/evaluate_phase1_one_action_successor.py),
  SHA-256
  `8b9b91dc717dc69621152ddf9f798db786fe846c0b43e0dd0b15f7f9633df367`;
- jointly unlocked protected-data runtime bridge:
  [run_phase1_one_action_successor_protected.py](../../scripts/run_phase1_one_action_successor_protected.py),
  SHA-256
  `03360908d485073df020b1966ccd42a3f59c796c3a7cc2696b56d6544d7f16d8`;
- selected-model protected prediction adapter:
  [predict_phase1_one_action_successor.py](../../scripts/predict_phase1_one_action_successor.py),
  SHA-256
  `33ae2cac1af1ceaa98380a87ab67d7ae4971376633c816c820d4345ab75eea54`;
- evaluator tests:
  [test_phase1_one_action_successor_evaluation.py](../../tests/test_phase1_one_action_successor_evaluation.py),
  SHA-256
  `c131ebd2a72f232395f342c2e89a9e7f5b375959e7f951560b7e1bf90b42eaac`;
- protected-runtime tests:
  [test_phase1_one_action_successor_protected.py](../../tests/test_phase1_one_action_successor_protected.py),
  SHA-256
  `c320b79320804adbf1d4f08e41f4a6b77ad5ce49412617b881d8227db93342bc`;
- prediction-adapter tests:
  [test_predict_phase1_one_action_successor.py](../../tests/test_predict_phase1_one_action_successor.py),
  SHA-256
  `eed73c1bc8fdcf12d91490d3335ea226dfb045d9425f688489a301b119fc09af`.

Frozen evaluation behavior:

- the plan gate requires a passing 48/16 bulk summary, the frozen dataset,
  test, and sensitivity identities, the training plan, train-only
  normalization, all five selected D0/R0/R1/R2S/R2E cards and checkpoints,
  and all five validation-only uncertainty calibrations;
- plan freeze binds source, input, selection, model-card, checkpoint, history,
  normalization, calibration, exact 24-test membership, exact six-case
  matched-sensitivity grid, and every threshold before the first protected
  target;
- test and sensitivity generation share one explicit unlock and one open-once
  marker. The open marker is written immediately before the first protected
  Chrono target, matching the proven historical evaluation ordering;
- the runtime bridge reuses the qualified two-worker Chrono, common-flat-base
  Newton, analysis, tensor-export, and admission path. It selects only the 24
  test and six sensitivity identities and refuses unknown identities or any
  worker count other than two;
- prediction remains prohibited until all 30 protected episodes are complete
  and admitted. The final report rehashes every episode summary, model-input
  archive, target archive, Newton response manifest, and Chrono manifest.
- the prediction adapter loads only the validation-selected model identities;
  evaluates no deformation, raw Newton, D0/R0/R1/R2S/R2E, deterministic
  shuffled-`Kphi`, and train-mean constant-`Kphi` conditions; applies only the
  frozen validation calibration; and writes immutable per-episode prediction
  summaries and archives for all 30 protected members;
- the six protected sensitivity episodes produce 24 adjacent-`Kphi`
  direction comparisons per model: two force levels, two adjacent edges,
  loaded/post-unload, and peak depression, mean depression, and displaced
  volume. They remain excluded from fitting, normalization, calibration, and
  selection;
- report generation verifies the exact 30-member prediction artifact manifest
  in addition to the protected simulator/tensor manifest and refuses a changed
  or partial prediction payload.
- the final audit additionally reconstructs each of the 24 test rows and all
  24 eligible sensitivity comparisons per model from the hashed per-episode
  summaries. A coherent aggregate-file edit cannot bypass those records;
- incomplete sensitivity evidence, including 23/24 eligible comparisons,
  fails the model gate. Newton-added-value and R2S/R2E optional-field-value
  status also require the candidate to pass every general accuracy, control,
  coverage, failure-tail, and sensitivity gate;
- R0 and R1 remain separately prespecified hypotheses. The protected test does
  not choose a deployment model; the report lists every passing correction
  and every passing Newton-added-value hypothesis.

Metrics and claim routing:

- every learned model is scored at loaded and post-unload checkpoints in the
  footprint and twice-radius regions with whole episodes as the bootstrap
  unit;
- the frozen gates include median RMSE no greater than 3 mm, at least 30%
  median reduction from raw Newton, at least 90% episode improvement against
  both raw Newton and no deformation, the 10%/1 mm per-episode regression
  tolerance, both `Kphi` controls, 80--100% accepted calibrated coverage, and
  at least 90% protected sensitivity direction agreement;
- R0/R1 can support `neural_correction_with_newton_added_value` only if a
  passing correction also beats equal-capacity D0 by at least 5% on every
  joint-holdout checkpoint/region with a positive paired-bootstrap lower
  bound. Otherwise a passing correction routes to
  `neural_correction_without_newton_added_value`;
- if neither correction passes but D0 does, the only positive route is
  `learned_direct_surrogate`. R2S/R2E value is reported separately against R1
  at the frozen 5% margin and cannot silently redefine the core claim;
- the claim remains one-action, synthetic, and observable-state only. It does
  not establish sequential rollout, planner benefit, constitutive validation,
  named-soil calibration, or sim-to-real transfer.

Verification and current boundary:

- 47 successor planning, smoke, bulk, evaluation, protected-runtime, and
  prediction tests pass together under system Python;
- nine Torch-dependent successor model/training tests pass in the declared
  PyTorch environment, and the 12 historical evaluator tests remain green;
- no smoke status was polled during this work;
- no bulk, training, or evaluation plan was frozen; no model was fit; no
  unlock/open marker, protected target, prediction payload, or successor final
  report was created;
- the runtime order remains smoke verification on user request, remaining
  unprotected bulk generation, training and validation selection, evaluation
  plan freeze, explicit joint unlock, 30 protected episodes, prediction, and
  the locked report.

### 2026-11-02 — Live successor handoff reconciled with the running smoke

Requested handoff update:

- recheck the active successor smoke once, record its authoritative state in
  the Phase 1 goal and handoff documents, and leave the experiment running;
- do not open protected targets, freeze a downstream plan, start another
  supervisor, or infer aggregate admission from partial episode output.

Observed runtime state at 00:05 EST:

- the original supervisor PID `1955843` is alive under
  `python3 scripts/run_phase1_one_action_successor_smoke.py --stage all --workers 2`;
- two live `chrono_splat` workers are executing
  `p1s_train_joint-design_002` and `p1s_train_joint-design_003` with the frozen
  action, surface, and SCM arguments;
- Chrono members `p1s_train_joint-design_000` and `001` have complete manifests,
  maps, metrics, and accepted `converged_speed_hold` termination records;
- members `002` and `003` have not yet written complete Chrono destinations,
  and the other eight smoke members remain queued by the same two-worker
  supervisor;
- `run.log` last records completion of 000 and 001 and launch of 002 and 003;
  no `smoke_summary.json` exists;
- no bulk plan, bulk target, training plan, fit, selection artifact,
  evaluation plan, unlock/open marker, protected target, prediction payload,
  or successor final report exists.

Decision and continuation guard:

- the smoke is **running**, not stalled, passed, or failed. Partial Chrono
  completion does not admit an episode or satisfy the 12-member aggregate
  gate;
- leave PID `1955843` and its workers alone. Do not launch a duplicate smoke
  command while they are active;
- the user requested manual rechecks rather than automatic polling. On the next
  explicit status request, inspect the supervisor, worker commands, `run.log`,
  and aggregate summary once;
- if the supervisor is still active, continue waiting. If it exits without a
  summary, preserve partial artifacts and diagnose the exact incomplete member
  before any restart; do not delete or overwrite a partial Chrono destination;
- only a summary bound to smoke-plan SHA-256
  `3d861da58edaf697ca7b5b494589fce99b926a7a3c13c19dec19026eedbafee7`,
  with 12/12 complete and admitted members, explicit remaining
  train/validation permission, and explicit protected denial may permit the
  bulk-plan freeze.

Downstream handoff after a verified smoke pass:

1. freeze the bulk plan, then generate only the remaining 40 training and 12
   validation members with two workers; the 12 smoke members must be reused;
2. require a passing 48/16 bulk summary, then freeze the training plan and fit
   all three declared seeds for D0/R0/R1/R2S/R2E;
3. select checkpoints and calibrate uncertainty using validation only;
4. freeze the evaluation plan from the selected artifacts before any protected
   target exists;
5. perform the explicit joint unlock/open transition, run exactly 24 protected
   test plus six protected sensitivity episodes, predict with only the selected
   checkpoints, and generate the locked report.

The successor source/config hashes recorded in the preceding entries were
rechecked and are unchanged. The smoke, bulk, training, and evaluation gates
therefore remain bound to their documented implementations.

### 2026-11-02 — Successor smoke passed and unprotected bulk launched

Question:

- determine whether the frozen successor smoke passed its aggregate gate, then
  freeze and run only the permitted unprotected train/validation continuation
  without opening either protected set.

Measured smoke evidence:

- the original two-worker run completed all 12 Chrono episodes, four required
  bed preparations, all 12 Newton responses, tensor conversion, analysis, and
  aggregate summary generation;
- all 12/12 members are complete and admitted at 8 training, 4 validation,
  0 test, and 0 protected sensitivity, and every aggregate check is true;
- `remaining_train_validation_permitted` is true while
  `test_or_protected_sensitivity_permitted` is false;
- the passing summary is bound to smoke-plan SHA-256
  `3d861da58edaf697ca7b5b494589fce99b926a7a3c13c19dec19026eedbafee7` and
  has SHA-256
  `8c66e79f513ef40f1e680efad719500713f57523c9013c4907fa880060919989`.

Frozen bulk continuation and runtime state:

- `phase1_one_action_successor_contract_v1/dataset_smoke_v1/bulk_plan.json`
  has SHA-256
  `5e56f58570666c81e73e06ee34ee3f4e4193c9917d81cae74d11f66fb0de8b49`;
- the plan totals 48 training and 16 validation members, hash-binds and reuses
  all 12 admitted smoke members, and selects exactly 52 new members: 40 training
  plus 12 validation;
- the plan contains zero test and zero protected-sensitivity members and keeps
  protected generation explicitly denied;
- the original bulk supervisor is active as PID `1981098` under
  `python3 scripts/run_phase1_one_action_successor_bulk.py --stage all --workers 2`;
  at 10:59 EST its two workers were executing training members 008 and 009;
- no `bulk_summary.json` exists yet.

Decision and continuation guard:

- the smoke gate has passed and the unprotected bulk run is active;
- do not launch a duplicate supervisor or infer bulk admission from partial
  outputs;
- training, evaluation-plan freeze, joint protected unlock, all protected
  generation, prediction, and reporting remain prohibited;
- only a passing 48/16 bulk summary with all 64 members complete and admitted,
  explicit training permission, and explicit protected denial may permit the
  training-plan freeze.

Claim boundary:

- the passing smoke demonstrates only that the frozen small pipeline completed
  and met its engineering admission checks; it does not demonstrate predictive
  accuracy, Newton added value, parameter sensitivity, or real-soil validity;
- launching the bulk continuation creates no protected target and changes no
  successor scientific claim.

### 2026-11-03 — Unprotected bulk progress checkpoint

Question:

- reconcile the original two-worker bulk supervisor after the date boundary,
  record material forward progress, and preserve every downstream lock.

Measured evidence at 01:23 EST:

- the original supervisor PID `1981098` remains active under the frozen bulk
  command;
- new training members 008--038 completed in order without an emitted error;
- workers advanced to new training members 039 and 040, so 31/40 new training
  members are complete;
- nine new training members, all 12 new validation members, Newton response and
  tensor generation, and the aggregate bulk summary remain unfinished;
- no protected worker or protected target was created.

Decision and claim boundary:

- continue the original supervisor without a duplicate or restart;
- do not infer episode admission or training permission from the 31 partial
  Chrono completions;
- training, evaluation-plan freeze, protected unlock, prediction, and reporting
  remain prohibited until their documented gates pass;
- this checkpoint records runtime progress only and changes no scientific
  claim.

### 2026-11-03 — Chrono generation complete and Newton responses active

Question:

- reconcile the single frozen bulk supervisor after completion of target
  generation, record the response-stage boundary, and preserve every later
  gate.

Measured evidence at 19:04 EST:

- the original supervisor PID `1981098` remains active under the frozen bulk
  command with exactly two Newton response workers;
- all 40 new training and 12 new validation Chrono episodes are complete, so
  the plan's 48/16 Chrono membership is complete after reusing the 12 smoke
  members;
- all five reusable Newton beds and preparations for surface seeds 4101--4104
  and 4201 are complete;
- new training responses 008--023 are durable, for 16/52 new responses and
  28/64 response manifests after including the 12 reused smoke responses;
- workers are executing new training responses 024 and 025 on `cuda:0`;
- no protected worker or target was created, and no new tensor admission or
  `bulk_summary.json` exists yet.

Decision and claim boundary:

- continue the original supervisor without a duplicate or restart through all
  remaining responses, tensor conversion, analysis, and aggregate admission;
- do not infer member admission or training permission from Chrono or response
  completion alone;
- training-plan freeze, model fitting, evaluation-plan freeze, protected
  unlock, prediction, and reporting remain prohibited until their documented
  gates pass;
- this checkpoint records runtime progress only and changes no scientific
  claim.

### 2026-11-05 — Bulk failure preserved, artifact-only recovery passed, training launched

Question:

- determine whether the completed 48/16 bulk set permits training without
  erasing a frozen failure, rerunning a simulator, replacing an artifact, or
  weakening either protected lock.

Completed bulk evidence:

- all 64 Chrono, Newton, tensor, and episode-summary artifacts are complete at
  48 training, 16 validation, zero test, and zero protected sensitivity;
- the original `bulk_summary.json` has SHA-256
  `f80c9f018758438ecac0300cfc35c51e828af08a3268ba5fc791a2501f748955`
  and remains `failed_or_incomplete`;
- member `p1s_train_joint-design_019` alone is rejected: horizontal guide
  speed is `1.3220210438912167e-6` m/s against the legacy unified `1e-6`
  tolerance. Every other numerical, interaction, tensor, count, surface, and
  protected-lock check passes;
- the v1 summary and all simulator/tensor artifacts remain unchanged.

Prospective basis and frozen recovery:

- the component-specific guide contract was selected before this successor
  failure in `phase1_evaluation_v2.json`: horizontal speed `5e-6` m/s,
  with horizontal position, angular speed, and orientation each `1e-6`;
- the independent full-duration dual-worker qualification records
  `passed_full_duration_qualification_with_non_bitwise_drift`;
- the recovery config, runner, and focused tests were added as a distinct v2
  analysis path. Four recovery tests, nine updated successor training tests,
  syntax checks, and whitespace checks pass;
- the recovery plan was frozen before reanalysis at SHA-256
  `aedca2736bbe8fbf5b2543d9d41d470c5243834acfb7945201eccd821bb85ab6`.
  It binds six files for each of 64 members, all 384 artifact hashes, the exact
  failed v1 summary, sources, train/validation manifest, and both protected
  locks. It prohibits simulation reruns and artifact replacement;
- the separate recovery summary has SHA-256
  `dfacb7ed29b61c061dff01314e3035530db7a89d81617e4c117db7e90acc1d81`,
  passes 64/64 under the frozen component contract, records only member 019 as
  recovered, permits training-plan freeze, and continues to deny protected
  generation.

Training freeze and launch:

- training-plan SHA-256:
  `2b3b71023c908b1c2c953e558edf4e1dae28c7af775b7f091f16aff5190a0426`;
- train-only normalization SHA-256:
  `969a3378dab6de540eed912a30c613ead129a43e7e6d8d0df49712c2f04269d6`;
- D0, R0, R1, R2S, and R2E each have 288,532 parameters and use the three
  already declared seeds 20261101--20261103;
- the full 15-fit command is active as PID `2328423`. At 01:01 EST, D0 seed
  20261101 was the sole complete model card.

Decision and claim boundary:

- continue the single training process through all 15 fits, then perform
  validation-only selection and uncertainty calibration;
- do not freeze evaluation, unlock protected targets, or inspect protected
  outcomes before selection is complete;
- the recovery fixes an inherited numerical-contract mismatch using an
  independently prospective threshold; it does not establish predictive
  accuracy, Newton added value, parameter sensitivity, or real-soil validity.

### 2026-11-05 — Validation selection complete and protected evaluation opened once

Question:

- can validation-only selection, recovery-bound evaluation freeze, and the
  single joint protected unlock/open transition complete without target
  leakage or a duplicate execution chain?

Training and selection evidence:

- all 15 equal-capacity D0/R0/R1/R2S/R2E fits completed for seeds
  20261101--20261103, with 15 model cards, histories, and checkpoints;
- selection and uncertainty calibration used only the 16 validation episodes;
- selected seeds are D0 `20261102`, R0 `20261101`, R1 `20261103`, R2S
  `20261103`, and R2E `20261102`;
- `selection_summary.json` has SHA-256
  `3a2ffef309fc36a6018698182dec626f187e8b94894c41e0f76c5cbe46fbe08e`
  and status `models_selected_before_protected_unlock`;
- protected targets remained absent throughout fitting, selection, and
  calibration.

Recovery-bound evaluation freeze:

- the evaluator now requires the passed recovery ID, all recovery checks, the
  immutable legacy bulk-summary SHA-256, exact recovered-member identity, no
  simulator rerun, no artifact replacement, and no protected access;
- 13 focused evaluation, five protected-runner, six prediction, four recovery,
  and nine training tests pass; syntax and whitespace checks also pass;
- `evaluation_plan.json` has SHA-256
  `5b9f1062bcc54c55696addb54b3f5c0fea953335281ee08d0c5dfe3ddd9cc02c`
  and status `frozen_after_validation_selection_before_first_protected_target`;
- the plan binds exactly 24 test and six protected-sensitivity episodes, all
  selected model-card/checkpoint/history hashes, the validation-only
  calibration, both target locks, and the recovery sources. It records
  `protected_targets_opened: false` at freeze.

Unlock and active execution:

- the explicit joint unlock marker binds evaluation plan
  `5b9f1062...cc02c`, selection `3a2ffef3...e08e`, test lock
  `0390d46b...f713`, and sensitivity lock `a003ec52...4139`, with 24/6 counts
  and `targets_opened: false`;
- the qualified command
  `/eng/home/christoa/miniconda3/envs/test/bin/python scripts/run_phase1_one_action_successor_protected.py --stage all --workers 2`
  launched once as session `33604`;
- its Chrono stage wrote the sole open-once marker immediately before starting
  the first two protected episodes. At 02:38 EST both Chrono workers were
  active; no duplicate protected process was launched.

Decision and claim boundary:

- continue session `33604` through all 30 Chrono targets, reusable-bed
  preparation, Newton responses, tensor conversion, and aggregate admission;
- prediction remains prohibited until `protected_dataset_summary.json` passes
  all 30 members. The final report remains prohibited until prediction
  completes under the frozen selected artifacts;
- this checkpoint proves ordering and identity only. It does not establish any
  accuracy, uncertainty, sensitivity, Newton-added-value, or Phase 1 exit gate.

### 2026-11-05 — Protected Chrono generation reached 14/30

Measured evidence at 08:39 EST:

- the original protected supervisor PID `2340298` and session `33604` remain
  active after six hours with exactly two Chrono workers;
- 14/30 protected Chrono manifests are durable in frozen membership order;
- episodes `p1s_test_unseen-kphi_014` and
  `p1s_test_unseen-initial-surface_015` are active, both CPU-bound normally;
- no protected-generation error, second supervisor, prediction artifact, or
  report exists.

Fail-closed continuation:

- temporary watcher session `82982` polls only the exact protected supervisor
  PID and command. After it exits, the watcher invokes the existing predictor,
  followed by the report only if prediction succeeds;
- this does not bypass a gate: prediction independently requires the protected
  summary to be `passed`, `prediction_permitted: true`, and bound to the frozen
  evaluation plan. The report independently revalidates the prediction and all
  protected artifacts;
- if protected admission fails, the predictor refuses and the watcher exits
  before reporting.

Decision and claim boundary:

- preserve both sessions and do not launch another protected, prediction, or
  report process;
- 14 Chrono manifests prove generation progress only. All predictive and Phase
  1 exit claims remain prohibited until admission, prediction, and the locked
  report complete and are audited.

### 2026-11-05 — All 24 protected-test Chrono targets complete

Measured evidence at 12:37 EST:

- all 24 frozen protected-test Chrono manifests are durable under the original
  supervisor PID `2340298` and its exact two-worker queue;
- sensitivity members `p1s_protected_sensitivity_matched-kphi-sweep_000` and
  `_001` are active, so the six-member sensitivity block is the only remaining
  Chrono work;
- no protected-generation error, duplicate supervisor, prediction artifact,
  or report exists. Watcher session `82982` remains dormant behind aggregate
  admission.

Decision and claim boundary:

- continue the same supervisor through six sensitivity targets, bed/prior
  reuse, all 30 Newton responses, tensor conversion, and admission;
- 24/24 test Chrono completion establishes target-generation progress only. It
  does not permit prediction or establish any accuracy, sensitivity,
  uncertainty, Newton-added-value, or Phase 1 exit claim.

### 2026-11-06 — Protected Newton failed closed; missing-only recovery frozen

Failure evidence:

- the original session `33604` completed all 30 Chrono targets, all five bed
  builds and preparations, and 29/30 protected Newton responses;
- `p1s_test_joint-combination_019` alone exited during residual-state export
  because `plastic_jacobian` contained non-finite values. It produced no
  response manifest. Its log SHA-256 is
  `452151089d7bdcafa0c4754e71f154635f4a0b6686971da59fe06a1bab81c71f`;
- the protected supervisor exited nonzero. The continuation watcher attempted
  prediction, but the predictor independently rejected the incomplete
  protected artifact set before inference; no report was produced;
- the other 29 official response-manifest identities remain complete and are
  now bound by the recovery plan. No failed file has been deleted or replaced.

Prospective recovery frozen before retry:

- [recovery config](../../configs/phase1_one_action_successor_protected_recovery_v1.json),
  [runner](../../scripts/recover_phase1_one_action_successor_protected_v1.py),
  and [focused tests](../../tests/test_recover_phase1_one_action_successor_protected_v1.py)
  define a separate recovery identity;
- three focused tests, bytecode compilation, and whitespace checks pass;
- recovery-plan SHA-256 is
  `d48f40ecb05fa194b21cb5f7cab4acc75006513d898d292c398a7c1c17035f89`.
  It binds the unchanged evaluation plan/open marker, exact failed files, all
  29 completed official manifests, source identities, and the exact retry and
  companion inputs;
- runtime must move the failed partial response and log into the episode-local
  `failed_attempts/attempt_1_nonfinite_plastic_jacobian/` archive, generate
  only missing official member 019, and concurrently run member 020 into a
  recovery-only companion directory. The companion is execution evidence and
  cannot enter evaluation membership or replace member 020's official data;
- a second retry is prohibited without another prospective plan. Even a
  passing recovery summary cannot permit prediction: the original 30-member
  protected analyzer must still admit every test and sensitivity member.

Decision and claim boundary:

- execute the one frozen two-process recovery attempt, then run the original
  protected analyzer only if both recovery manifests pass finite, guide, and
  preparation checks and all 29 prior manifests remain hash-identical;
- this recovery plan preserves the failed attempt and execution identity. It
  does not establish protected admission, predictive accuracy, sensitivity,
  uncertainty, Newton-added-value, or the Phase 1 exit.

### 2026-11-07 — Dual-process recovery failed; qualified serial recovery frozen

Measured v1 recovery result:

- the frozen two-process recovery ran member 019 and the recovery-only member
  020 companion concurrently for about 64 minutes;
- the companion passed all finite, guide, and preparation checks with manifest
  SHA-256 `9df3e15e22298a113028e2847c6d83977cdb8d237ec926ec514300b4fabe8955`;
- official member 019 again failed at residual export on a non-finite
  `plastic_jacobian`; its second failed log SHA-256 is
  `bf8bab4cd6af778fa09050b1ef84d45a2ee52a8035d7e59d0d0187dde5a61777`;
- recovery summary SHA-256 is
  `6f46e5350a87579d66937e0fbc5e0942f357fdb0f82449d89dd7768ba38a3f6e`.
  It records `status=failed`, preserves the first attempt, confirms all 29
  completed manifests unchanged, and keeps `prediction_permitted=false`;
- the fail-closed continuation stopped on that failed recovery summary. It did
  not invoke protected admission, prediction, or reporting.

Prospective serial v2 recovery:

- [v2 config](../../configs/phase1_one_action_successor_protected_recovery_v2.json),
  [runner](../../scripts/recover_phase1_one_action_successor_protected_v2.py),
  and [focused tests](../../tests/test_recover_phase1_one_action_successor_protected_v2.py)
  define one serial missing-only retry after the two dual-process failures;
- two focused tests, bytecode compilation, and whitespace checks pass;
- plan SHA-256 is
  `4da69d0c61f9e3bf65083febd2c45432806ea56ed17d25a2b207d7b96cb7bd9f`.
  It binds both failed attempts, the v1 recovery plan and failed summary, all
  29 completed official manifests, unchanged source identities, and the exact
  member-019 input before the serial retry;
- the plan explicitly records that a successful member-019 response is a
  serial execution-identity qualification and may not be represented as a
  clean two-worker protected response set. It permits no further unplanned
  retry and cannot itself permit prediction.

Decision and claim boundary:

- execute the one frozen serial attempt, preserve the second failed response
  before runtime, then require the v2 summary and original 30-member protected
  admission in sequence;
- even if numerically complete, the final report must retain the member-019
  execution qualification. This checkpoint establishes neither admission nor
  any positive predictive or Phase 1 claim.

Serial completion and analyzer mismatch:

- the unchanged serial member-019 response completed. Recovery-v2 summary
  SHA-256 is
  `d18ad7f01780628d13ba7822de8649450a0e00dbc726e8beb799bfa678cf23d8`;
  all six recovery checks pass, both failed attempts remain hash-preserved,
  all 30 official manifests exist, and the execution qualification is explicit;
- the original protected analyzer then completed all 30 tensor exports but
  emitted failed summary SHA-256
  `b47c316faa8635ae348c155d30105ac4a2d9dceb7c1b3d7a25e1ba38dbd2a086`;
- exactly the 24 test members are marked unadmitted. Every one passes all
  numerical, interaction, tensor-shape, finite, signal, and memory checks and
  fails only `no_test_target`. All six protected-sensitivity members admit;
- `no_test_target` is the engineering-smoke sentinel that correctly prevents
  test export before unlock. Reusing it after the frozen joint unlock/open is
  a protected-bridge context error, not a scientific or numerical failure.

Artifact-only admission recovery frozen before correction:

- [config](../../configs/phase1_one_action_successor_protected_admission_recovery_v3.json),
  [runner](../../scripts/recover_phase1_one_action_successor_protected_admission_v3.py),
  and [tests](../../tests/test_recover_phase1_one_action_successor_protected_admission_v3.py)
  define a no-simulation, no-tensor-array recovery;
- two focused tests, bytecode compilation, and whitespace checks pass;
- plan SHA-256 is
  `e5576d39a4ab46365ccc18a902f784570f2490e5dfbbc1189ff40b5c3cb40693`.
  It binds the failed summary, serial recovery, unlock/open identities, sources,
  and all 180 protected artifact hashes before correction;
- runtime must archive the failed aggregate and all 60 original per-episode
  JSONs, leave every Chrono/Newton/NPZ artifact unchanged, and replace only
  the 24 false smoke sentinels with a true
  `protected_target_opened_after_joint_unlock` check. The recovered summary
  must retain the serial execution qualification and independently rehash all
  protected artifacts before permitting prediction.

### 2026-11-07 — Protected admission and prediction complete; successor hypothesis fails

Question:

- does the fully qualified successor evaluation satisfy every frozen predictive
  gate and therefore achieve the Phase 1 goal?

Measured recovery and prediction evidence:

- artifact-only admission recovery summary SHA-256 is
  `785694d82628973a446dfe11dbfac617d5a459abb4f51b4ebef7cc520b25307b`;
  all recovery checks pass, no simulator or tensor array was rerun or replaced,
  and the original failed aggregate plus all 60 per-episode JSONs are archived;
- recovered protected-summary SHA-256 is
  `fb9f71ea3af06f6acea13bbe33762b9bfb9481ae3fa02eea733563f9c427facc`.
  It admits all 24 test and six sensitivity members and preserves the member-019
  serial-retry qualification;
- protected-prediction SHA-256 is
  `b825bd2cbf2c7bfcbec020fd776a1895b8b7a7c3fa1c522bb1bc6c88986a2dc3`.
  It contains 24 test predictions; D0, R0, R1, R2S, and R2E each achieve the
  required sensitivity direction in all 24 eligible comparisons.

Frozen final result:

- final-report SHA-256 is
  `c5995e619d602a092aa784ef54ba697d4482b5712c9913a87c8b7c011e49c3f9`;
  it records `status=failed`, `supported_claim_permitted=false`, and
  `claim_route=no_positive_successor_claim`;
- D0, R0, R1, R2S, and R2E all fail at least one required gate. There is no
  passing correction model and no model demonstrates Newton added value;
- D0 is the strongest absolute predictor: median RMSE is about 1.82--1.86 mm
  across the four checkpoint/region pairs and median raw-Newton reduction is
  55.7--76.1%. It still fails one post-unload footprint failure-tail case and
  the twice-radius `kphi` constant/shuffled controls, so it cannot support the
  frozen claim;
- the immutable qualification record, SHA-256
  `9205c2ee0bb9eefeb08d5e9cf758046ac3c071891bda6f260b8efebbb55b1570`,
  binds the report to prediction, the recovered admission, the serial Newton
  recovery, and the preserved original failed analysis. All 11 provenance and
  result checks pass; it records `phase1_goal_achieved=false`.

Decision and claim boundary:

- close this successor evaluation as an informative, provenance-qualified
  failed hypothesis. Do not relabel it as Phase 1 completion and do not create
  a Phase 1 completion report;
- the result concerns one held-out vertical action in the frozen synthetic
  domain. It does not establish sequential rollout, planner benefit,
  constitutive validation, named-soil calibration, or sim-to-real transfer;
- any continuation must freeze a new prospective model or protocol branch
  before using the now-revealed test evidence. The current test set may inform
  diagnosis but cannot be reused as an unbiased confirmation set.

### 2026-11-07 — Direct-v4 validation passed; fresh protected confirmation active

Question:

- can the strongest direct predictor be repaired prospectively for material
  sensitivity and confirmed on fresh protected identities without retraining,
  using the revealed successor test only for diagnosis and branch design;
- what does the completed model ladder say about direct versus
  Newton-conditioned prediction; and
- what exactly is running now?

Antecedent model evidence:

- all 15 equal-capacity three-level U-Net fits completed from 48 training
  episodes, with seed selection and calibration using only 16 validation
  episodes;
- D0 consumes initial geometry, action geometry, force, and `Kphi`, with no
  Newton input; R0 adds raw Newton loaded/post displacement; R1 adds occupancy,
  mass, action-aligned vertical velocity, contact count, and normal impulse;
  R2S and R2E separately add stress and elastic state;
- the completed 24-test protected report gives the following median RMSE
  values in millimetres:

| Model | Loaded footprint | Loaded twice-radius | Post footprint | Post twice-radius | Outcome |
| --- | ---: | ---: | ---: | ---: | --- |
| D0 | 1.825 | 1.856 | 1.825 | 1.855 | strongest; failed one failure-tail and twice-radius parameter controls |
| R0 | 3.161 | 2.859 | 3.595 | 3.369 | no Newton added value |
| R1 | 3.309 | 2.964 | 3.815 | 3.395 | no Newton added value |
| R2S | 3.304 | 2.949 | 3.869 | 3.406 | no stress-field value |
| R2E | 3.574 | 2.988 | 4.045 | 3.492 | no elastic-field value |

- all models passed 24/24 protected sensitivity-direction comparisons, but all
  failed at least one mandatory predictive gate. D0's median reduction from
  raw Newton was 76.1%, 64.8%, 66.3%, and 55.7% in the same order. The
  Newton-conditioned models were worse than D0 and failed every
  Newton-added-value region;
- this evidence shows that the tested fusion did not use Newton productively.
  It does not by itself prove whether the Newton prior lacks incremental signal
  or the equal-capacity early/residual fusion and training design failed to
  extract it.

Prospective branch ordering:

- direct-v2 validation failed and remains preserved at SHA-256
  `d27590cdc8a05f52194dd91bdd78be54a0708c3bfa39a2888ebf2115ac48db96`;
- direct-v3 preflight validation passed at SHA-256
  `3d266422651920d860070d1c17066a3de18427cbc4ef9de30597270c6bb98af5`,
  but its confirmation lock followed validation, so it is not authoritative;
- direct-v4 corrected the ordering. Confirmation plan SHA-256
  `a6d3dcc5872f5b0398bc51cf7ef800e8c66a577d2eeec08d731345bed80d4428`
  froze the model, fresh 24-test lock, six-case sensitivity lock, episode
  manifest, thresholds, and forbidden use of v1 test identities before
  authoritative validation.

Candidate and authoritative validation:

- D1 is a deterministic
  `frozen_D0_reference_differenced_kphi_sensitivity_wrapper` around
  `D0_seed_20261102`; its formula is
  `initial + ((D0(Kphi) + (D0(Kphi) - D0(train_mean_Kphi))) - initial)`;
- reference, gain, and residual scale are frozen. There is no fitting, gradient
  update, new normalization, or protected-target use;
- authoritative validation-summary SHA-256 is
  `ed23f62cea6137daea91ea8a259b9edd947f4bd202294a9e9d511b6702d27a22`.
  It uses the original 16 validation episodes, uses zero v1 test episodes, and
  passes all 20 frozen checks;
- validation median RMSE is 2.266/2.035/2.266/2.033 mm for loaded footprint,
  loaded twice-radius, post footprint, and post twice-radius. Corresponding
  median reduction from raw Newton is 69.8%/59.0%/56.5%/51.3%, and improvement
  fractions are 100%/100%/93.75%/100%;
- constant-reference `Kphi` increases paired mean footprint RMSE by 2.66% at
  both checkpoints, and shuffled `Kphi` increases it by 4.11%; all four
  control lower bounds are above zero.

Surface, unlock, and reporting identities:

- all six fresh surface seeds 5101--5106 pass analytic and native SCM
  round-trip qualification; plan and summary SHA-256 values are
  `c13026d2ed02ebeacfced01cf4d0ceec47c1ad63ca1ab2c11409d56671946704`
  and
  `a73f71b25347d8cac62f771d6e7f6238a24d08a4bb55475a82644841519310c3`;
- joint unlock
  `588e8efc693838249b9eb0a26af2cdda0bf93083690b935dadbc1a7cff419837`
  occurred only after authoritative validation and all-surface qualification;
  target-open marker
  `4ff1265799d430ef00900a0a03e8d3e0d4c72aa769455e2fbe2f54fd9cf2be57`
  then opened the two protected sets together;
- protected execution-plan SHA-256 is
  `7385bba039c90a3a172c122bce270702c44c2bd0655030742687ec0c0cc363ab`
  and requires exactly two workers;
- reporting plan SHA-256 is
  `b89417e6d7e7a3942ceb131446841a20555e88d88191076d8ef9dfb682abf60f`.
  It froze after seven Chrono manifests existed, but before target inspection,
  tensor target export, prediction, or scoring. Scientific thresholds and D1
  identity were already frozen before unlock. This ordering fact remains an
  explicit provenance qualification.

Live protected execution at 20:19 EST:

- the original supervisor PID `2589639` is healthy under
  `run_phase1_one_action_successor_direct_v4_protected.py --stage chrono`;
- 14/30 Chrono manifests are complete. Members 000--013 are complete; members
  014 and 015 are the active workers;
- no direct-v4 bed preparation, Newton response, tensor admission, protected
  prediction, or final report exists yet;
- the guarded continuation order is Chrono 30/30, six bed preparations, 30
  Newton responses, protected analysis/admission 30/30, locked D1 prediction,
  then the 25-gate final report. Do not launch a duplicate supervisor or change
  the frozen two-worker execution identity.

Measured runtime analysis:

- a Newton response operates on roughly 304,865 particles at a 0.25 ms
  timestep. It repeats a 2.0 s/8,000-step pre-settle, then 1,400 loaded and
  1,000 post-unload steps, about 10,400 MPM steps per episode;
- the implicit MPM configuration permits 50 solver iterations, eight coupled
  proxy iterations, and 16 rigid substeps;
- historical full-duration cases took about 2,570 seconds each serially.
  Running two on the single RTX 5090 took about 3,880 seconds per pair, with
  median GPU utilization 92% and only 1.325x aggregate throughput;
- settled-state restoration, persistent batching, altered numerics, or a
  different worker count could accelerate a future branch, but none may be
  inserted silently into the frozen direct-v4 confirmation.

Decision and claim boundary:

- continue the existing protected run without retraining or changing its
  execution identity;
- the current 30 targets are test/sensitivity evidence, not additional
  training data;
- a full direct-v4 pass could support only a one-action learned direct-surrogate
  claim in the frozen synthetic domain. D1 consumes no Newton field and cannot
  demonstrate Newton+neural added value;
- a redesigned gated/late-fusion Newton+neural model may reuse the 48 training
  and 16 validation targets, but it would require a separately frozen model and
  fresh protected confirmation. The old 24 and current 30 protected targets
  cannot be used for fitting or unbiased model selection.

## Maintenance contract


For every subsequent experiment:

1. append a dated entry containing the question, frozen inputs, commands or
   implementation, measured evidence, decision, claim boundary, and artifacts;
2. update the current snapshot from machine-readable evidence;
3. update [phase1.md](phase1.md) in the same change if the permitted next work,
   domain, routing, or exit status changes;
4. never rewrite a failed result into a pass or delete a superseded result;
5. keep validation and test targets locked according to the frozen plan.

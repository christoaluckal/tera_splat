# Phase 1 goal: parameter-conditioned neural bed-state prediction

Created: 2026-10-23

Last updated: 2026-11-10

Status: complete; direct-v4 D1 passed 25/25 protected gates and final audit

## Authority

This document is the sole operational authority for Phase 1. It preserves the
frozen v1/v2 domain, model/data contract, exit gates, and failed result, and it
defines the research and claim boundary for a prospective successor. The
successor now has a source-backed draft in
[phase1_one_action_successor_v1.json](../../configs/phase1_one_action_successor_v1.json)
and a frozen data/evaluation contract in
[phase1_one_action_successor_contract_v1.json](../../configs/phase1_one_action_successor_contract_v1.json).
Its target-free 48/16/24 plan, completed training, and failed protected result
remain frozen. A separate prospective direct-v4 branch now evaluates a fixed
no-refit `D1` wrapper around the selected `D0` checkpoint on 24 fresh test and
six fresh sensitivity episodes. Its confirmation identity was frozen before
authoritative validation, validation passed, all six fresh surfaces qualified,
and the joint protected unlock/open occurred once in order. Protected Chrono
generation is complete at 30/30. A separately frozen revision-only
continuation preserves the original protected identity after the first bed
invocation failed closed on a repository revision mismatch. Six metric beds,
six prepared Newton states, and all 30 Newton responses are complete. The
protected analyzer admits 30/30. Locked D1 prediction, the 25-gate report,
outcome-neutral final qualification, and the completion audit all pass. Phase
1 is complete under the narrow learned one-action direct-surrogate claim. Work
deferred to the sequential stage remains explicit below.

[Phase 0](phase0.md) remains the authority for the completed proof and its
artifacts. The phase numbering in the older
[hybrid roadmap](../hybrid-chrono-mpm-residual-gaussian-planning-20261008.md)
is historical; where it conflicts with this document, this document wins for
all new work.

## Fresh-session handoff

This section is the entry point for a new agent or session. Read the sources in
the order below before changing code or launching simulations:

1. this document for the completed Phase 1 result, research ordering, and claim
   boundary;
2. the [Phase 1 chronological record](phase1-running.md) for dated
   implementation evidence, frozen hashes, decisions, and blockers;
3. the [Phase 1 completion report](phase1-completion-20261110.md) for the
   protected metrics, final identities, completion audit, and claim boundary;
4. the [Phase 0 completion report](phase0-completion-20261022.md) for the
   frozen result, implementation changes, verification, hashes, and claim
   boundary;
5. the [Phase 0 authority](phase0.md) for the completed action ledger, frozen
   numerical contract, chronology, and artifact routing;
6. the [fresh Phase 0 protocol](fresh-hierarchical-phase0-20261017.md) for the
   prospective split and evidence hierarchy inherited by Phase 1;
7. the [Chrono oracle contract](../chrono-oracle-run-contract.md) for action,
   timing, mask, support, and acceptance semantics;
8. the [current repository state](../current-state.md) for cross-backend
   context and known limitations;
9. the [hybrid roadmap](../hybrid-chrono-mpm-residual-gaussian-planning-20261008.md)
   for design background only; this document overrides its phase numbering;
10. the [contributor guidance](../contributor-guidance.md) before modifying
   experiments, claims, or evidence documents;
11. the [Newton documentation index](README.md) for the complete dated report
    and action-specific experiment index;
12. the [tracked diagnostics index](../../diagnostics/README.md) for the
    lightweight JSON, CSV, and Markdown evidence that led to the inherited
    Newton prior; and
13. the [Chrono simulator documentation](../../../tera_splat_sim/docs/README.md)
    for the adjacent oracle repository and its environment contract.

The first three documents are sufficient to recover the completed goal,
evidence, and claim boundary. Items 4--13 recover why the inherited baseline
exists and where its evidence lives. Dated historical reports are provenance,
not alternative live instructions.

### Live successor checkpoint and continuation guard

All 64 frozen train/validation members are complete at 48 training and 16
validation, with zero test and zero protected-sensitivity targets. The original
`bulk_summary.json`, SHA-256
`f80c9f018758438ecac0300cfc35c51e828af08a3268ba5fc791a2501f748955`,
is immutable and remains `failed_or_incomplete`: member
`p1s_train_joint-design_019` alone failed the legacy unified guide check
because horizontal speed was `1.3220210438912167e-6` m/s against `1e-6`.
Every other numerical, interaction, tensor, membership, surface, and protected-
lock check passed.

Before training, a separate recovery plan froze an artifact-only reanalysis at
SHA-256
`aedca2736bbe8fbf5b2543d9d41d470c5243834acfb7945201eccd821bb85ab6`.
It imports the independently prospective component contract already qualified
before the earlier v2 protected run: `5e-6` m/s for horizontal speed and
`1e-6` for horizontal position, angular speed, and orientation. It hash-binds
all 384 episode summary, tensor, response, and Chrono artifacts; prohibits
simulation reruns, replacement, and protected access; and preserves the failed
v1 summary. The recovered summary has SHA-256
`dfacb7ed29b61c061dff01314e3035530db7a89d81617e4c117db7e90acc1d81`,
passes all 64 members, and permits training-plan freeze while continuing to
deny protected generation.

The training plan and train-only normalization are frozen at SHA-256
`2b3b71023c908b1c2c953e558edf4e1dae28c7af775b7f091f16aff5190a0426`
and `969a3378dab6de540eed912a30c613ead129a43e7e6d8d0df49712c2f04269d6`.
All five D0/R0/R1/R2S/R2E variants have equal 288,532-parameter capacity and
all 15 frozen-seed fits completed. Validation-only selection chose D0 seed
20261102, R0 seed 20261101, R1 seed 20261103, R2S seed 20261103, and R2E seed
20261102. The selection-summary SHA-256 is
`3a2ffef309fc36a6018698182dec626f187e8b94894c41e0f76c5cbe46fbe08e`;
all calibration fit IDs are the 16 validation episodes.

The evaluation plan then froze at SHA-256
`5b9f1062bcc54c55696addb54b3f5c0fea953335281ee08d0c5dfe3ddd9cc02c`,
binding the exact 24 test plus six protected-sensitivity inputs, selected
artifacts, calibration, locks, recovery provenance, and still-closed targets.
The explicit joint unlock and open-once marker followed. All 30 Chrono targets,
five preparations, and 29 original two-worker Newton responses completed.
Member 019 failed twice under the preserved dual-process identity on a
non-finite plastic Jacobian; its prospectively frozen serial retry completed,
so the response set is permanently execution-qualified rather than a clean
two-worker result. The first protected analysis then failed all 24 test rows
only because it reused the pre-unlock smoke sentinel after the joint unlock.
An artifact-only recovery archived that failed analysis, changed no simulator
or tensor array, and admitted 30/30. Its passing summary has SHA-256
`785694d82628973a446dfe11dbfac617d5a459abb4f51b4ebef7cc520b25307b`;
the recovered protected summary has SHA-256
`fb9f71ea3af06f6acea13bbe33762b9bfb9481ae3fa02eea733563f9c427facc`.

Locked prediction and reporting are complete. Prediction SHA-256 is
`b825bd2cbf2c7bfcbec020fd776a1895b8b7a7c3fa1c522bb1bc6c88986a2dc3`;
all five models pass the protected sensitivity-direction check. Final-report
SHA-256 is
`c5995e619d602a092aa784ef54ba697d4482b5712c9913a87c8b7c011e49c3f9`.
It is `failed`: D0, R0, R1, R2S, and R2E all fail at least one required gate,
there is no passing correction model, no demonstrated Newton added value, and
no positive successor claim. A separate immutable qualification record,
SHA-256
`9205c2ee0bb9eefeb08d5e9cf758046ac3c071891bda6f260b8efebbb55b1570`,
binds the report to the serial retry and artifact-only admission provenance.
The successor evaluation closed as an informative failed experiment and did
not complete Phase 1. Direct-v4 therefore froze a new prospective model and
fresh protected protocol before using any new confirmation evidence.

### Direct-v4 completion checkpoint

The permitted continuation is
`phase1_one_action_successor_direct_v4`. It does not retrain a model and it is
not a Newton-conditioned correction. `D1` is a deterministic wrapper around
the validation-selected `D0` seed `20261102`:

    initial + ((D0(Kphi) + (D0(Kphi) - D0(train_mean_Kphi))) - initial)

The gain and residual scale are both fixed at one. There are no fitting or
gradient updates. The original 48 training and 16 validation episodes remain
the only fitting/selection data; the fresh 24 test and six sensitivity targets
are protected confirmation evidence and must never become training data.

The earlier protected successor result establishes the following model-type
performance. Values are median RMSE in millimetres for loaded footprint,
loaded twice-radius, post-unload footprint, and post-unload twice-radius:

| Model | Model type | Protected-test median RMSE, mm | Result |
| --- | --- | --- | --- |
| D0 | direct U-Net from initial geometry, action, force, and `Kphi`; no Newton input | 1.825 / 1.856 / 1.825 / 1.855 | strongest model, but failed one post-unload failure-tail gate and twice-radius `Kphi` controls |
| R0 | D0 inputs plus raw Newton loaded/post-unload displacement; residual around Newton | 3.161 / 2.859 / 3.595 / 3.369 | failed absolute, control, raw-reduction, and all Newton-added-value gates |
| R1 | R0 plus occupancy, mass, vertical velocity, contact count, and normal impulse | 3.309 / 2.964 / 3.815 / 3.395 | failed absolute, control, raw-reduction, and all Newton-added-value gates |
| R2S | R1 plus mean and von Mises stress | 3.304 / 2.949 / 3.869 / 3.406 | no optional stress-field value; failed mandatory gates |
| R2E | R1 plus elastic Jacobian and isochoric shear | 3.574 / 2.988 / 4.045 / 3.492 | no optional elastic-field value; failed mandatory gates |

All five models passed 24/24 protected sensitivity-direction comparisons, but
none passed every required predictive gate. In particular, adding Newton
surface, contact, stress, or elastic inputs did not beat D0, so the result does
not demonstrate Newton added value. It does not distinguish conclusively
between an unhelpful Newton prior and an ineffective neural fusion design.

Direct-v4 confirmation-plan SHA-256 is
`a6d3dcc5872f5b0398bc51cf7ef800e8c66a577d2eeec08d731345bed80d4428`.
Authoritative validation used only the original 16 validation episodes and
zero revealed v1 test episodes. Its summary SHA-256 is
`ed23f62cea6137daea91ea8a259b9edd947f4bd202294a9e9d511b6702d27a22`
and all 20 validation checks pass. D1 validation median RMSE is 2.266, 2.035,
2.266, and 2.033 mm across the same four checkpoint/region combinations;
median reduction versus raw Newton is 69.8%, 59.0%, 56.5%, and 51.3%; and the
episode improvement fractions are 100%, 100%, 93.75%, and 100%. Both constant
and shuffled `Kphi` footprint controls pass at loaded and post-unload states.
These are validation results, not protected-test results.

All six fresh surface seeds 5101--5106 passed analytic and native Chrono SCM
round-trip qualification. The joint unlock marker SHA-256 is
`588e8efc693838249b9eb0a26af2cdda0bf93083690b935dadbc1a7cff419837`;
the protected execution plan SHA-256 is
`7385bba039c90a3a172c122bce270702c44c2bd0655030742687ec0c0cc363ab`;
and the open-once marker SHA-256 is
`4ff1265799d430ef00900a0a03e8d3e0d4c72aa769455e2fbe2f54fd9cf2be57`.

All 30 protected Chrono manifests are complete and accepted. The original
Chrono supervisor exited successfully.

The first bed-stage invocation failed closed before writing a downstream
artifact. The protected execution plan binds `tera_splat` revision
`e80203483879dcbae3bbac274ebf25314d97427b`, but committing the already-frozen
direct-v4 implementation and documentation moved the repository to
`20cb535cbefb719bcb392cc06f24fc290d1ff955`. The runtime found exactly one
changed stable identity key, `repository_revisions`; `tera_splat_sim` remains
at `14b3fce4a0d57b3cbc531226faa0e27c890c7526`, and the source, input,
environment, membership, thresholds, worker count, and model identities remain
unchanged. The revision-only recovery config, runner, and tests are
[phase1_one_action_successor_direct_v4_revision_rebind_v1.json](../../configs/phase1_one_action_successor_direct_v4_revision_rebind_v1.json),
[recover_phase1_one_action_successor_direct_v4_revision.py](../../scripts/recover_phase1_one_action_successor_direct_v4_revision.py),
and
[test_recover_phase1_one_action_successor_direct_v4_revision.py](../../tests/test_recover_phase1_one_action_successor_direct_v4_revision.py).
Five focused recovery tests and three protected-runtime regression tests pass.
The prospective revision-only recovery plan froze before any downstream
artifact at SHA-256
`0b37fb917c0ee95135b4971c348ee41ae07b19fd486f93fcaaf341b9318c5d54`.
It binds all completed Chrono files, records 30/30 machine-accepted episodes,
proves that `repository_revisions` is the sole changed stable key, preserves
two workers, and keeps prediction prohibited until the protected analyzer
passes. All six metric beds, all six Newton prepared states, and all 30 Newton
responses subsequently completed. Every response is finite and
`acceptance_eligible=true`; response manifests retain the pre-admission
diagnostic convention `status=diagnostic_only` and `accepted=false`.

The protected analyzer passes all aggregate checks and admits 30/30: 24 test
and six protected-sensitivity episodes. Its summary SHA-256 is
`32d4768e87d1ece6d7b7c4f46bf2c362e6a9698906ef4cf9e400ae3c46ab7e06`,
with `status=passed` and `prediction_permitted=true`. The two-worker supervisor
exited successfully; no direct-v4 simulator, terrain, or Newton-response
process is currently running. The outcome-neutral final-qualification plan
froze before protected admission/prediction/report at SHA-256
`687131c6e1f3367d5b549c0d808ce9b3cea72d7ce4ea86ccadec10efa76ff259`.
The reporting-only revision continuation froze after admission and before
prediction/report at SHA-256
`9dd7f3728e8279af4566624018f5e7d099ef3d54e63094225dad2cc7fbdd3856`.

Locked prediction SHA-256 is
`9403c434a20d254b924378a361e7cf7fda0aec415f723580350e75105dda3a62`.
All 24 eligible protected sensitivity comparisons have the correct direction.
Final-report SHA-256 is
`a73067698b08de907915f2db877a2667f7ec862eee0c29a2cc3a2192bb80a2e8`:
all 25 precommitted hypothesis checks pass, no failed check is recorded, and
`phase1_goal_achieved=true`. D1 protected median RMSE is 1.827, 1.933,
1.827, and 1.933 mm for loaded footprint, loaded twice-radius, post-unload
footprint, and post-unload twice-radius. Median reductions from raw Newton are
78.29%, 64.31%, 67.97%, and 55.19%; episode improvement fractions against both
raw Newton and no deformation are 100%, 100%, 95.83%, and 100%.

Final qualification SHA-256
`eece4dc223903bbfa177cda22eea597a3497ecb1b9d59bd7d956a5904728544c`
records `qualified_passed_result`. Independent completion-audit SHA-256
`d6535856a73edc1bf29c51cfd2b63f32e8855e244498fdf1f988a376e5f436cd`
revalidates every prediction artifact, recomputes the qualifier, and passes.
The supported route is `learned_one_action_direct_surrogate`; D1 consumes no
Newton fields and cannot support a Newton+neural added-value claim. The full
result is in the [Phase 1 completion report](phase1-completion-20261110.md).

Newton dominated the completed protected-runtime wall time. Each response
rebuilt roughly 304,865 particles and repeated a 2.0 s pre-settle at 0.25 ms
before the 0.35 s loaded and 0.25 s post-unload windows: about 10,400 MPM steps
per episode. The implicit solver permits 50 iterations, with eight proxy
iterations and 16 rigid substeps. Historical full-duration measurement was about 43
minutes serial per response; two responses sharing one RTX 5090 required about
64.7 minutes per pair and improved aggregate throughput by only 1.325x. The
completed frozen runtime did not adopt checkpoint reuse or a different worker
count; either optimization remains a separately qualified prospective branch.

### Frozen baseline inherited from Phase 0

Phase 1 begins from the following immutable evidence:

| Item | Frozen value or source |
| --- | --- |
| campaign | `static_proxy_hierarchical_v3_20261017` |
| completed matrix | 10/15 actions: all 31 N and 46 N cases |
| protected boundary | all five 61 N actions remain absent |
| proxy | vertically guided, 35 mm-radius cylinder |
| Newton material | 100 kPa, `nu=0.2`, `mu=0.68` |
| Newton timestep | 0.25 ms |
| Newton voxel size | 7.8125 mm |
| support | 14,161 valid Chrono cells at 5 mm spacing |
| frozen v1 SHA-256 | `242fa879c1d7eda443f4277d82a41dcfea5828cdb7b66ccae357b633d99a15af` |
| frozen v2 SHA-256 | `cc31209737d69a059f64627e19d9c9f76b2ba1e36be86f528802470d05b0c23f` |
| v2 training-summary SHA-256 | `5109b4266451751898f9e42b50fbbe8b7610587a65ee9f9d5a4193452a2a3c11` |
| strict mechanics status | not qualified; bounded coarse-prior use only |

Do not regenerate the 10 actions, refit v1 or v2, alter their split membership,
or use the protected 61 N targets to revise them. Phase 1 may evaluate the
frozen models as baselines, but it must build a prospective Phase 1 dataset.

### Existing executable entry points

| Purpose | Source |
| --- | --- |
| frozen Phase 0 machine contract | [static_proxy_hierarchical_v3_20261017.json](../../configs/static_proxy_hierarchical_v3_20261017.json) |
| fresh matrix orchestration and admission | [run_fresh_phase0_matrix.py](../../scripts/run_fresh_phase0_matrix.py) |
| Newton preparation | [run_newton_prepared_bed.py](../../scripts/run_newton_prepared_bed.py) |
| Newton response diagnostic | [run_newton_cylinder_diagnostic.py](../../scripts/run_newton_cylinder_diagnostic.py) |
| Phase 0 base residual and particle lift | [run_phase0_residual_pilot.py](../../scripts/run_phase0_residual_pilot.py) |
| frozen multi-load v2 wrapper | [run_phase0_multiload_residual_pilot.py](../../scripts/run_phase0_multiload_residual_pilot.py) |
| residual integrity tests | [test_phase0_residual_pilot.py](../../tests/test_phase0_residual_pilot.py) |
| Chrono cylinder oracle CLI | [run_cylinder_episode.py](../../../tera_splat_sim/run_cylinder_episode.py) |
| Chrono SCM implementation | [cylinder_episode.py](../../../tera_splat_sim/quick_support_demo/chrono_demo/cylinder_episode.py) |
| optional local PCD rendering | [render_phase0_pcd_isometric.py](../../scripts/render_phase0_pcd_isometric.py) |

Reuse the contracts, schemas, admission logic, provenance, and tests where they
remain applicable. Do not silently convert a Phase 0 script into the Phase 1
authority; Phase 1 receives new versioned files so the completed evidence stays
reproducible.

### Canonical Phase 0 artifacts

The Phase 0 output root is:

`outputs/validity_experiment/newton/static_proxy_hierarchical_v3_20261017/`

| Evidence | Path below the output root |
| --- | --- |
| live matrix summary | `matrix/matrix_summary.json` |
| admitted per-action states | `matrix/cases/<case_id>/` |
| same-build repeatability | `repeatability/repeatability_summary.json` |
| v1 model and evaluation | `matrix/residual_pilot_v1/` |
| frozen v2 model | `matrix/residual_pilot_v2_multiload/model.npz` |
| frozen v2 training record | `matrix/residual_pilot_v2_multiload/training_summary.json` |
| locked v2 held-out result | `matrix/residual_pilot_v2_multiload/evaluation_summary.json` |
| v2 corrected states | `matrix/residual_pilot_v2_multiload/cases/<case_id>/` |

The paired Chrono episodes are rooted at:

`../tera_splat_sim/validity_experiment/chrono_episodes/static_proxy_hierarchical_v3_20261017/`

Large outputs are data-volume artifacts and are not assumed to be present in a
fresh Git clone. The optional Phase 0 PNG views are derived local files,
ignored by Git, and can be regenerated with the rendering script; they are not
required evidence.

### Environments

- Run Newton generation and Phase 0 compatibility checks with
  `/data/christoa/conda/envs/newton_splat/bin/python`.
- Run the Chrono oracle in the existing `chrono_splat` conda environment; its
  setup and pinned PyChrono requirement are documented in
  [getting started](../../../tera_splat_sim/docs/getting-started.md).
- The available neural-training candidate is conda environment `test`, verified
  on 2026-10-22 as Python 3.11.15, NumPy 2.4.6, PyTorch 2.13.0+cu130, CUDA
  runtime 13.0, with CUDA available on an NVIDIA GeForce RTX 5090. This is a
  discovered environment, not yet a frozen training identity. Its exact probe,
  package lock, source hashes, and device identity must be copied into the
  future training plan before the first fit.
- Do not silently mutate either simulator environment to add neural-training
  dependencies. Training must remain a separate invocation from Chrono and
  Newton data generation.

### Experiment recovery map

Phase 1 spans two sibling repositories on branch `neural`:

| Repository | Role | Revision recorded at screening-plan freeze |
| --- | --- | --- |
| `tera_splat` | contracts, Newton bridge, screening, dataset, models, evaluation, and documentation | `7f91a707fe29461398691b6ff4222b8c01e9dcfc` |
| `tera_splat_sim` | Chrono SCM oracle and exact heightfield initialization | `164023bc0d2147da177cba864a297cd2abc8e28d` |

Both working trees intentionally contain the new Phase 1 implementation on top
of those revisions. A fresh session must use the hashes in the frozen plans,
not assume that the recorded revisions alone identify the uncommitted source.
Do not modify a source named in `screening_plan.json` while the canonical
screen is running: the runner checks its SHA-256 before every stage.

The currently frozen Phase 1 identities are:

| Artifact | SHA-256 |
| --- | --- |
| machine contract | `abd4aff8d5970f8596292139af94c4518494510b40b7b347bf4e6da0aba68c0b` |
| contract planner | `ab433a9b8fc31bcedd7692440b5e573c5d77b1a023b211eb209aad3c9a9b9f49` |
| complete target-free dataset-plan file | `0c7971813bbde427694a207f06234ce780ad827bbb28b8e3025c17fe8529880c` |
| canonical 88-input manifest payload | `a821d191edbdaa7e2dda3c5cfef89f2c20eaf7ba9ce080c2bd78c67b7047a45c` |
| protected test-identity lock | `277bdcd63b9539723a1cd0f5059c8169314f55ba70566236138d8f7d54433e0c` |
| complete screening plan | `958cba65978106e1664a0531b14cf8a520a0e629bd8fd413068de4851b1637ca` |
| screening runner | `71b9324aaa383045e94c17493822d35de1244dcf9f21a7c14d18b7558fd55e08` |
| surface generator | `789f617996a4b85b63014fc41e681376e2e672d62af81b3f7260758dff29903e` |
| superseded latent v1 contract (never run) | `4db6c5bd799076ca5f108dc370b43005f3728d46d2ce36c2d98b7774c4c9c0dc` |
| common-base v2 contract | `c1fae68557727d7f4dc34bbd3554c36f9ed9185c3dd3b30863d84d4d2f41bf1f` |
| common-base v2 qualification plan | `57c108ac063d36e255f1721a95ae996c3b8bb0f53abcbe5c4561343a590e37c5` |
| common-base v2 qualification summary | `60990f1004623593197844a49ced397b94b8e898a481311ca01f107820ca57ef` |
| completed latent v2 contract | `2ad312c67d99b78a7f8b9323497801819d52297669f8d192e4d67265537a6b9d` |
| latent v2 qualification plan | `b948bbfb5c40c5c3ac3730e9be624fab409b7be74da34b1961f8786ef37993ad` |
| latent v2 generated summary, rejected by audit | `2849aa933922d7072e8dd0fa99ad67094dde87c01af8123cfb5bc840a18e037e` |
| active latent v3 contract, before plan freeze | `51385b1e904b9553ce279ec2ad60f47c41dbc4171cfa289b979b89965af1e9b2` |
| active v3 qualification runner, before plan freeze | `b4db1577e6f3162ac2bd79cb60cd77672761eba1a9a25633a82de260ec336632` |
| active latent v3 qualification plan | `355bf9bcbe73f2eb365095e1c4ad30fd58bc28f0c2ec27d1dcfcbe5b3d047b13` |
| completed latent v3 qualification summary | `72af2a69495f525c6dcc8df248e82a3eb5667ff41f74b399072d82635d0d9243` |
| latent v3 field-metrics table | `5ff70aed9d7c1054fe19b570d718163daf0058725cf6f47bd0cd83caf1b0bc38` |
| smoke dataset contract, before plan freeze | `d963f0dcd58a4e6c502ab74c7b741bf17d388b2cfdfbbc81dfafeaaf58dccff9` |
| smoke dataset runner, before plan freeze | `db579bdc06e43d72c60868fe56a7c3a1315034f2b266ea059dbe70a805c3faf2` |
| smoke dataset focused tests, before plan freeze | `9f6e9efcd94e941183fa49a9a74c096a80dd43154c5f85f43f2a7f661a94ffe3` |
| frozen smoke plan | `760592caa36f5ca3552192c1cb24a03409a8fa8603c0c4fcf3fdefc2be473ca0` |
| selected 12-episode smoke membership | `5bbfc312f0bfd4f0edd027fb5b11dd2293e62398f78d6b68af5b9acb1cb90db8` |
| completed smoke aggregate summary | `c473e4b79a5c615f88c52cdb2f5f74860848eaf6102a1a751fda45e6eedc24c0` |
| reserved-surface-2101 Newton preparation | `aa8e38c7a369cc3796ccca9fa820de19c0b4e67f35b45a2f077aecbf511fc91b` |
| bulk train/validation contract, before plan freeze | `dcd2717629c441132b8f978e6c981876a396b5891979f63f61a05f465926b35f` |
| bulk train/validation runner, before plan freeze | `381c3fcbd65d9d14401a950e2265bff3c61a0724235400a3b059815e80e06b4e` |
| bulk train/validation tests, before plan freeze | `3bad3072facb067db84ae3ac7a4f9a5e3708f61882c45f18e1c693c71607ef2d` |
| frozen 64-target bulk plan | `a42db0a6a49142620cf276cb8337ffff4c8b804ad0d0a73af71569e883e4cb18` |
| selected 48/16/0 bulk membership | `37e5f1cc405bc92a72a0644848e6b08a4d8709931486b22cb54efe3069097e26` |
| successor data/evaluation contract | `834db42409fd48dfb2136b93192dd5fd22233733ac09dfaf8d7e5bcaf6aef4fd` |
| successor target-free dataset plan | `b326a96bbbcd82e863984eef016e0d320c479f5ec1b7ff937ec4da031d1070ef` |
| successor 94-input physical manifest | `2df4ced81aa85a88536b72bd28c8a736e8dabf898ffeb891891678b9e7682725` |
| successor protected test lock | `0390d46bfd5860b08518f3b99ab116084f24138939c04435f29582c3feedf713` |
| successor protected sensitivity lock | `a003ec52f2fb43c94d5d760e06a924c3b49809a0ddf415a6abbb718ff18a4139` |
| successor surface-qualification plan | `1fc635c1ed468b00316fcce62a32d98012e524c0f4c6ef5ed1bf2b32b99e9a9e` |
| successor surface-qualification summary | `a3935396fa99362c1a94aa4fa960408cd0efedc158b3dbf0649e2645ec13d7f1` |
| successor smoke config | `d81c099c39ecedf6901c84c72e0d825a50a95b9855ec0ac927fb6f7656906c55` |
| successor smoke runner at plan freeze | `992ee513562a50ba62e76c5481f393c88530a838dfe0c10d4d7c54cac73e0bd8` |
| successor smoke focused tests at plan freeze | `cb29192f03f4b2ebd0bad4636182d0574b3be0327c722d99dd725d8318e42e48` |
| frozen successor 8/4 smoke plan | `3d861da58edaf697ca7b5b494589fce99b926a7a3c13c19dec19026eedbafee7` |
| selected successor 12-episode membership | `9eee6ab977f499a475debc94e589d031a4657a7e3b68cd59a9e5ee5a7f38a042` |
| prepared successor bulk config, smoke-gate locked | `9fabff0b6a22d5858b33afb129dc1fe4d2dd87717e242309d239752ec99a3935` |
| prepared successor bulk runner, smoke-gate locked | `1f69d5ddb02de88129f429eef90ec19bcb31f8d1fa70a5f8b4137bbc63e3b21b` |
| successor bulk focused tests | `5a3cbef2c78845a968934f284abd4e77a2733956bd65734480634e5d91bc09ee` |
| prepared successor training config, bulk-gate locked | `eabe4e5d689a6d8fbf698ac64a3c5a46c3e96f818281446c21e2140de28185f3` |
| successor D0/R0/R1/R2S/R2E model | `ed1d865f4592adb834fd9bb61280c07df88615acd97a2db843e9f6fb85c9c4cf` |
| prepared successor trainer adapter, bulk-gate locked | `790dc3ac1c4222638634e454053bb5f6602b8b4f080da7451e0d8935071a0470` |
| successor model/training focused tests | `d2d81c1196337ad8d4eb05015df7dc4657a067bbbb154f0c84758ac5bd39500b` |
| prepared successor evaluation config, selection-gate locked | `2c86c607c0c9839a3b806345a76e41a76e61e1e2501d23a0e37056ce2261dd5f` |
| prepared successor evaluator and claim router | `8b9b91dc717dc69621152ddf9f798db786fe846c0b43e0dd0b15f7f9633df367` |
| prepared protected-data runtime bridge | `03360908d485073df020b1966ccd42a3f59c796c3a7cc2696b56d6544d7f16d8` |
| prepared protected prediction adapter | `33ae2cac1af1ceaa98380a87ab67d7ae4971376633c816c820d4345ab75eea54` |
| successor evaluation focused tests | `c131ebd2a72f232395f342c2e89a9e7f5b375959e7f951560b7e1bf90b42eaac` |
| successor protected-runtime focused tests | `c320b79320804adbf1d4f08e41f4a6b77ad5ce49412617b881d8227db93342bc` |
| successor protected-prediction focused tests | `eed73c1bc8fdcf12d91490d3335ea226dfb045d9425f688489a301b119fc09af` |

The dataset-plan file hash covers provenance and plan metadata; the manifest
payload hash covers the canonical episode identities only. They are expected
to differ. The screening plan contains the remaining per-source hashes,
repository status snapshots, simulator environment probes, material-case
input hashes, and surface-case input hashes and is the authority for resuming
that screen.

Tracked Phase 1 sources and checks are:

| Evidence or implementation | Canonical source |
| --- | --- |
| goal and exit contract | this document |
| chronological measurements and decisions | [phase1-running.md](phase1-running.md) |
| machine-readable domain and gates | [phase1_bed_state_v1.json](../../configs/phase1_bed_state_v1.json) |
| deterministic 88-input planner and lock | [run_phase1_contract_screen.py](../../scripts/run_phase1_contract_screen.py) |
| deterministic surface family | [phase1_surface.py](../../scripts/phase1_surface.py) |
| surface/material screening pipeline | [run_phase1_screening.py](../../scripts/run_phase1_screening.py) |
| contract, split, surface, and screen tests | [test_phase1_contract_screen.py](../../tests/test_phase1_contract_screen.py), [test_phase1_surface.py](../../tests/test_phase1_surface.py), and [test_phase1_screening.py](../../tests/test_phase1_screening.py) |
| superseded, never-run latent contract | [phase1_latent_export_v1.json](../../configs/phase1_latent_export_v1.json) |
| completed but audit-rejected latent contract | [phase1_latent_export_v2.json](../../configs/phase1_latent_export_v2.json) |
| active corrected latent contract | [phase1_latent_export_v3.json](../../configs/phase1_latent_export_v3.json) |
| coupled MPM latent extraction and invariants | [phase1_latent_fields.py](../../scripts/phase1_latent_fields.py) and [test_phase1_latent_fields.py](../../tests/test_phase1_latent_fields.py) |
| source-hashed latent qualification runner | [run_phase1_latent_qualification.py](../../scripts/run_phase1_latent_qualification.py) and [test_phase1_latent_qualification.py](../../tests/test_phase1_latent_qualification.py) |
| prospective smoke contract and dataset pipeline | [phase1_dataset_smoke_v1.json](../../configs/phase1_dataset_smoke_v1.json), [run_phase1_dataset.py](../../scripts/run_phase1_dataset.py), and [test_phase1_dataset.py](../../tests/test_phase1_dataset.py) |
| locked train/validation bulk pipeline | [phase1_dataset_bulk_v1.json](../../configs/phase1_dataset_bulk_v1.json), [run_phase1_dataset_bulk.py](../../scripts/run_phase1_dataset_bulk.py), and [test_phase1_dataset_bulk.py](../../tests/test_phase1_dataset_bulk.py) |
| prospective neural-training contract | [phase1_training_v1.json](../../configs/phase1_training_v1.json) |
| shared capacity-controlled B3/H0/H1/H2 U-Net | [phase1_bed_state_model.py](../../scripts/phase1_bed_state_model.py) and [test_phase1_bed_state_model.py](../../tests/test_phase1_bed_state_model.py) |
| train-only normalization, loss, fitting, and validation selection | [train_phase1_bed_state.py](../../scripts/train_phase1_bed_state.py) and [test_train_phase1_bed_state.py](../../tests/test_train_phase1_bed_state.py) |
| deterministic surface-to-particle lift and invariant audit | [phase1_particle_lift.py](../../scripts/phase1_particle_lift.py) and [test_phase1_particle_lift.py](../../tests/test_phase1_particle_lift.py) |
| prospective selection-locked final evaluation | [phase1_evaluation_v1.json](../../configs/phase1_evaluation_v1.json), [evaluate_phase1_bed_state.py](../../scripts/evaluate_phase1_bed_state.py), and [test_evaluate_phase1_bed_state.py](../../tests/test_evaluate_phase1_bed_state.py) |
| frozen one-action successor data/evaluation contract and planner | [phase1_one_action_successor_contract_v1.json](../../configs/phase1_one_action_successor_contract_v1.json), [plan_phase1_one_action_successor.py](../../scripts/plan_phase1_one_action_successor.py), and [test_phase1_one_action_successor_plan.py](../../tests/test_phase1_one_action_successor_plan.py) |
| successor surface qualification | [qualify_phase1_one_action_successor_surfaces.py](../../scripts/qualify_phase1_one_action_successor_surfaces.py) |
| frozen successor engineering smoke | [phase1_one_action_successor_smoke_v1.json](../../configs/phase1_one_action_successor_smoke_v1.json), [run_phase1_one_action_successor_smoke.py](../../scripts/run_phase1_one_action_successor_smoke.py), and [test_phase1_one_action_successor_smoke.py](../../tests/test_phase1_one_action_successor_smoke.py) |
| smoke-gated successor bulk continuation | [phase1_one_action_successor_bulk_v1.json](../../configs/phase1_one_action_successor_bulk_v1.json), [run_phase1_one_action_successor_bulk.py](../../scripts/run_phase1_one_action_successor_bulk.py), and [test_phase1_one_action_successor_bulk.py](../../tests/test_phase1_one_action_successor_bulk.py) |
| bulk-gated successor model and training | [phase1_one_action_successor_training_v1.json](../../configs/phase1_one_action_successor_training_v1.json), [phase1_one_action_successor_model.py](../../scripts/phase1_one_action_successor_model.py), [train_phase1_one_action_successor.py](../../scripts/train_phase1_one_action_successor.py), and [test_phase1_one_action_successor_training.py](../../tests/test_phase1_one_action_successor_training.py) |
| selection-gated successor evaluation and protected runtime | [phase1_one_action_successor_evaluation_v1.json](../../configs/phase1_one_action_successor_evaluation_v1.json), [evaluate_phase1_one_action_successor.py](../../scripts/evaluate_phase1_one_action_successor.py), [run_phase1_one_action_successor_protected.py](../../scripts/run_phase1_one_action_successor_protected.py), [predict_phase1_one_action_successor.py](../../scripts/predict_phase1_one_action_successor.py), [test_phase1_one_action_successor_evaluation.py](../../tests/test_phase1_one_action_successor_evaluation.py), [test_phase1_one_action_successor_protected.py](../../tests/test_phase1_one_action_successor_protected.py), and [test_predict_phase1_one_action_successor.py](../../tests/test_predict_phase1_one_action_successor.py) |
| preserved, validator-rejected common-base v1 contract | [phase1_newton_common_base_v1.json](../../configs/phase1_newton_common_base_v1.json) |
| passing common-flat-base Newton repair contract | [phase1_newton_common_base_v2.json](../../configs/phase1_newton_common_base_v2.json) |
| common-base builder and rescreen | [phase1_metric_bed.py](../../scripts/phase1_metric_bed.py), [run_phase1_newton_common_base.py](../../scripts/run_phase1_newton_common_base.py), [test_phase1_metric_bed.py](../../tests/test_phase1_metric_bed.py), and [test_phase1_newton_common_base.py](../../tests/test_phase1_newton_common_base.py) |
| tracked v2 audit-rejected latent report | [README](../../diagnostics/phase1_latent_export_v2/README.md), [field metrics](../../diagnostics/phase1_latent_export_v2/field_metrics.csv), and [summary](../../diagnostics/phase1_latent_export_v2/summary.json) |
| tracked v3 passing latent report | [README](../../diagnostics/phase1_latent_export_v3/README.md), [field metrics](../../diagnostics/phase1_latent_export_v3/field_metrics.csv), and [summary](../../diagnostics/phase1_latent_export_v3/summary.json) |
| Chrono exact-array SCM course | [build_scm_pit.py](../../../tera_splat_sim/quick_support_demo/chrono_demo/build_scm_pit.py) |
| Chrono episode implementation and CLI | [cylinder_episode.py](../../../tera_splat_sim/quick_support_demo/chrono_demo/cylinder_episode.py) and [run_cylinder_episode.py](../../../tera_splat_sim/run_cylinder_episode.py) |
| native SCM round-trip check | [check_scm_initial_heightmap.py](../../../tera_splat_sim/check_scm_initial_heightmap.py) |
| Chrono terrain interface tests | [test_difficult_terrain.py](../../../tera_splat_sim/quick_support_demo/tests/test_difficult_terrain.py) |

Generated evidence is intentionally ignored by Git and lives on the data
volume. Relative to `tera_splat`, recover it in this order:

| Generated evidence | Canonical path |
| --- | --- |
| frozen 88-input plan and protected test lock | `outputs/validity_experiment/newton/phase1_bed_state_v1/dataset_plan.json` |
| frozen source/environment screening plan | `outputs/validity_experiment/newton/phase1_bed_state_v1/screening/screening_plan.json` |
| aggregate screening decision | `outputs/validity_experiment/newton/phase1_bed_state_v1/screening/screening_summary.json` |
| per-surface array, generator metrics, native check, and qualification | `outputs/validity_experiment/newton/phase1_bed_state_v1/screening/surfaces/surface_<seed>/` |
| per-material logs, metric bed, Newton states, and admission summary | `outputs/validity_experiment/newton/phase1_bed_state_v1/screening/material/<case_id>/` |
| paired Chrono material episodes | `../tera_splat_sim/validity_experiment/chrono_episodes/phase1_bed_state_v1/screening/material/<case_id>/` |
| preserved failed common-base v1 validator attempt | `outputs/validity_experiment/newton/phase1_bed_state_v1/newton_common_base_v1/` |
| passing common-base v2 plan, shared prior, pairings, and summary | `outputs/validity_experiment/newton/phase1_bed_state_v1/newton_common_base_v2/` |
| completed v2 plan, three raw repeats, logs, and audit-rejected summary | `outputs/validity_experiment/newton/phase1_bed_state_v1/latent_qualification/phase1_latent_export_v2/` |
| preserved v2 generated report | `diagnostics/phase1_latent_export_v2/` |
| passing v3 plan, three fresh repeats, logs, and summary | `outputs/validity_experiment/newton/phase1_bed_state_v1/latent_qualification/phase1_latent_export_v3/` |
| passing v3 tracked field report | `diagnostics/phase1_latent_export_v3/` |
| frozen smoke plan, per-surface priors, episode outputs, tensors, and aggregate decision | `outputs/validity_experiment/newton/phase1_bed_state_v1/dataset_smoke_v1/` |
| paired smoke Chrono targets | `../tera_splat_sim/validity_experiment/chrono_episodes/phase1_bed_state_v1/dataset_smoke_v1/` |
| frozen bulk plan, train/validation priors, responses, tensors, and aggregate decision | `outputs/validity_experiment/newton/phase1_bed_state_v1/dataset_bulk_v1/` |
| paired bulk train/validation Chrono targets | `../tera_splat_sim/validity_experiment/chrono_episodes/phase1_bed_state_v1/dataset_bulk_v1/` |
| future frozen training plan, train-only normalization, checkpoints, histories, and model cards | `outputs/validity_experiment/newton/phase1_bed_state_v1/training_v1/` |

The aggregate summary is the machine decision; `phase1-running.md` is its
human-readable interpretation. The contract expresses immutable intent, so
its embedded `not_started` fields are not live status indicators. If the large
output volume is unavailable, the tracked sources and frozen hashes still
recover the contract, but completed simulation evidence must be treated as
unavailable rather than regenerated silently.

From `tera_splat`, the exact validation and staged-screen commands are:

```bash
python3 scripts/run_phase1_contract_screen.py --check-only
python3 -m pytest tests/test_phase1_contract_screen.py tests/test_phase1_surface.py tests/test_phase1_screening.py -q
python3 scripts/run_phase1_screening.py --stage plan
python3 scripts/run_phase1_screening.py --stage surfaces
python3 scripts/run_phase1_screening.py --stage chrono
python3 scripts/run_phase1_screening.py --stage bed
python3 scripts/run_phase1_screening.py --stage newton
python3 scripts/run_phase1_screening.py --stage analyze
```

The material screen has passed and the response writer has the tested
schema-v2 mechanics/contact export. Run the active corrected v3 qualification with the
Newton environment, one independently logged process per repeat:

```bash
/data/christoa/conda/envs/newton_splat/bin/python -m pytest tests/test_newton_contract.py tests/test_phase1_latent_fields.py tests/test_phase1_latent_qualification.py -q
python3 scripts/run_phase1_latent_qualification.py --config configs/phase1_latent_export_v3.json --stage plan
python3 scripts/run_phase1_latent_qualification.py --config configs/phase1_latent_export_v3.json --stage run --repeat 1
python3 scripts/run_phase1_latent_qualification.py --config configs/phase1_latent_export_v3.json --stage run --repeat 2
python3 scripts/run_phase1_latent_qualification.py --config configs/phase1_latent_export_v3.json --stage run --repeat 3
python3 scripts/run_phase1_latent_qualification.py --config configs/phase1_latent_export_v3.json --stage analyze
```

The latent runner refuses to freeze a plan before the material screen passes.
Its plan binds the screening summary, reference-case inputs, source files,
Newton environment, device, and three independent response repeats. A passing
field-semantic report only admits channels to H2; it does not establish that H2
improves prediction.

The corrected v3 gate and the subsequent 12-episode smoke gate have passed.
These are the exact smoke commands that produced and independently reproduced
the passing aggregate without opening a test target:

```bash
/data/christoa/conda/envs/newton_splat/bin/python -m pytest tests/test_phase1_dataset.py tests/test_phase1_metric_bed.py tests/test_phase1_latent_fields.py -q
python3 scripts/run_phase1_dataset.py --config configs/phase1_dataset_smoke_v1.json --stage plan
python3 scripts/run_phase1_dataset.py --config configs/phase1_dataset_smoke_v1.json --stage chrono
python3 scripts/run_phase1_dataset.py --config configs/phase1_dataset_smoke_v1.json --stage bed
python3 scripts/run_phase1_dataset.py --config configs/phase1_dataset_smoke_v1.json --stage newton
python3 scripts/run_phase1_dataset.py --config configs/phase1_dataset_smoke_v1.json --stage analyze
```

The smoke runner refuses source, input, environment, GPU, device, membership,
or protected-test-lock drift after `smoke_plan.json` is frozen. It creates one
fresh common-flat-base preparation per initial-surface seed, an independent
Chrono target and Newton response per episode, and physically separate
`model_inputs.npz` and `targets.npz` archives. An incomplete episode directory
is preserved and refused. Only `smoke_summary.json` may permit the full
88-episode dataset. That summary now records `status=passed`, 12/12 admitted,
8/4/0 train/validation/test counts, all aggregate checks true, and
`full_dataset_permitted=true`. Do not regenerate the smoke set unless a new
versioned contract is prospectively frozen.

These are the exact bulk commands. The plan, Chrono, and bed stages are now
complete; the Newton stage is active and the analyzer may be rerun as responses
finish. The bulk runner cannot select, generate, analyze, or summarize any of
the 24 locked test identities:

```bash
python3 -m pytest tests/test_phase1_dataset_bulk.py tests/test_phase1_dataset.py tests/test_phase1_metric_bed.py tests/test_phase1_latent_fields.py -q
python3 scripts/run_phase1_dataset_bulk.py --config configs/phase1_dataset_bulk_v1.json --stage plan
python3 scripts/run_phase1_dataset_bulk.py --config configs/phase1_dataset_bulk_v1.json --stage chrono
python3 scripts/run_phase1_dataset_bulk.py --config configs/phase1_dataset_bulk_v1.json --stage bed
python3 scripts/run_phase1_dataset_bulk.py --config configs/phase1_dataset_bulk_v1.json --stage newton
python3 scripts/run_phase1_dataset_bulk.py --config configs/phase1_dataset_bulk_v1.json --stage analyze
```

The 64-target plan is frozen and binds the original 88-input manifest and
24-identity test lock, all sources and prerequisites, both simulator
environments, GPU/device identity, and five qualified non-test surfaces. The
test identities remain part of the immutable 88-input design, but their target
generation is deferred to the one-shot locked evaluation after model selection.

The shared neural architecture and training preflight can be verified in the
separate `test` environment without opening any protected target:

```bash
/eng/home/christoa/miniconda3/envs/test/bin/python -m unittest discover -s tests -p 'test_phase1_bed_state_model.py' -v
/eng/home/christoa/miniconda3/envs/test/bin/python -m unittest discover -s tests -p 'test_train_phase1_bed_state.py' -v
/eng/home/christoa/miniconda3/envs/test/bin/python -m unittest discover -s tests -p 'test_phase1_particle_lift.py' -v
/eng/home/christoa/miniconda3/envs/test/bin/python -m unittest discover -s tests -p 'test_evaluate_phase1_bed_state.py' -v
/eng/home/christoa/miniconda3/envs/test/bin/python -m py_compile scripts/phase1_bed_state_model.py scripts/train_phase1_bed_state.py scripts/phase1_particle_lift.py scripts/evaluate_phase1_bed_state.py
```

All B3, H0, H1, and H2 variants retain the same 289,172 trainable parameters
through fixed input masks. The tests cover the 121-by-121 odd grid, finite
forward/backward execution, bounded and boundary-tapered corrections, exact
base-state reproduction at initialization, parameter/latent ablation masks,
FiLM conditioning at every scale, the declared training contract, train-only
normalization helpers, physical-zero no-action construction, unambiguous
normalization hashes, validation-only conformal uncertainty calibration,
differentiable multi-term loss, and refusal to freeze a training plan before
the admitted bulk summary exists. The deterministic grid-to-particle lift is
also implemented and tested: its linear depth taper changes only particle z,
preserves every other archived field bitwise, preserves unsupported particles,
and reproduces the requested valid surface. The training plan and train-only
normalization are now frozen, all 12 variant/seed fits are complete, and
per-variant checkpoint selection plus uncertainty calibration used validation
only. No locked-test model score exists yet. The locked evaluator implements
selection-before-unlock planning, protected
target generation and admission, selected-model inference, B0--B3/H0--H2
baselines and ablations, shuffled and constant-parameter controls, calibrated
uncertainty, invariant-preserving particle lift, the five-case matched
sensitivity diagnostic, whole-episode bootstrap aggregation, explicit failure
cases, artifact revalidation, and evidence-complete final gate reporting. Its
plan was frozen after validation-only model selection; the explicit unlock and
open-once markers then released the currently active test Chrono stage.

For latent qualification, resume only after checking these sentinels in order:

1. `qualification_plan.json` exists and its source, input, environment, and
   device hashes still match the active tree;
2. each `repeat_<NN>/newton_response.log` belongs to a distinct completed
   process;
3. each repeat response contains `newton_cylinder_manifest.json` and the three
   schema-v2 archives `newton_state_initial.npz`, `newton_state_loaded.npz`, and
   `newton_state_residual.npz`;
4. each manifest passes finite, guide, and preparation checks and publishes the
   mechanics/contact field semantics; and
5. only `qualification_summary.json`, generated after all three repeats, may
   admit a latent family. Directory existence or one successful repeat is not
   qualification.

The v1 latent contract was frozen against the original failed material-screen
route and was never executed. V2 completed three repeats, but its analyzer
applied repeat gates only to non-kinematic particle invariants; the generated
`passed` label therefore contradicted this document's requirement that velocity
and contact also qualify. The raw v2 evidence and generated report are
preserved, but v2 does not pass the Phase 1 latent gate. The active v3 contract
keeps the thresholds, requires repeat-stable action-aligned velocity and both
contact grids, rejects plastic volume change inconsistent with the effectively
elastic material, consumes the passing common-base v2 preparation, and uses
target-independent 0.350 s loaded and 0.250 s post-unload timing.

The Chrono interface test must be run from `tera_splat_sim` with its activated
environment semantics:

```bash
conda run -n chrono_splat python -m unittest quick_support_demo.tests.test_difficult_terrain
```

`--case <case_id>` restricts any material stage to one frozen case. Before
launching a stage, check for an already-running screen and read its log under
`screening/material/<case_id>/logs/`; do not start a duplicate. Completed
artifacts are reused only after identity checks. An incomplete directory is
deliberately refused, so preserve it, diagnose and record the interruption in
`phase1-running.md`, then make an explicit recovery decision instead of
deleting evidence ad hoc.

For one material case, recovery proceeds through these concrete sentinels:

1. the Chrono episode `manifest.yaml` and every file it names;
2. `logs/chrono.log` plus successful Chrono qualification on analysis;
3. `metric_bed/particles_initial_mpm.ply` and
   `metric_bed/ground_plane_metadata.json`;
4. `preparation/newton_prepared_bed_manifest.json` and
   `logs/newton_preparation.log`;
5. `response/newton_cylinder_manifest.json`, its named state archives, and
   `logs/newton_response.log`; and
6. the analyzed `case_summary.json`.

Only `screening_summary.json` decides the aggregate gate. Directory existence,
a completed subprocess, or an individual Chrono acceptance is not equivalent
to Newton admission or permission for bulk generation. The repository-relative
`outputs` path is a symlink to `/data/christoa/Chrono/tera_splat/outputs` on the
current machine; preserve repository-relative paths in contracts so the data
volume can be relocated.

### Current Phase 1 completion state

The original machine-readable Phase 1 contract and target-free prospective
48/16/24 episode plan remain frozen. The plan fixes all 88 input
identities, assigns whole episodes, reserves disjoint initial-surface seeds,
defines five protected test groups, and records per-input, manifest, source,
and test-lock hashes before any Phase 1 target is generated. Seven focused
contract tests pass. Exact hashes and commands are recorded in the
[Phase 1 chronological record](phase1-running.md).

All six declared Phase 1 surface seeds now pass the analytic generator checks
and an exact native Chrono SCM initialization round-trip at 5 mm resolution.
The maximum observed round-trip height error is 7.463 micrometers. All five
material-box episodes are individually Chrono-accepted, so the proposed Chrono
parameter rectangle passes its oracle-side screen.

The first Newton preparation was deliberately rejected before contact:
equilibrium was reached, but its settled surface differed from the common
initial state by 6.072 mm RMSE, above the frozen 5 mm gate. The original
metric-bed builder placed a fixed-depth particle column below each varying
surface point, creating an undulating, partly unsupported bottom over a flat
ground plane. That failed screen remains preserved.

The prospectively frozen common-flat-base v2 repair passes. Its standalone
preparation reaches equilibrium with 2.106 mm settled-surface RMSE and 4.472 mm
maximum error. One independent, fixed-time Newton response is validly shared
across the five cases because they have the same initial bed, action, and
frozen Newton material; only their Chrono soil parameters and targets differ.
All five pairings pass inherited numerical and gross-interaction admission, so
the operational simulator screen permits later bulk generation. Strict
mechanics remains
unqualified: 20 of 303,829 particle centers briefly entered the analytic
cylinder, by at most 6.285 micrometers, within the declared 0.5 mm coarse
limit. This is a bounded coarse prior, not a strict-contact result.

The common-base screen's saved mechanics fields remain unqualified legacy
placeholders; that completed evidence is immutable. The response writer was
upgraded prospectively to export schema-v2 coupled solver entry state and
active cylinder-contact impulses. V2 completed three valid responses, but its
generated pass is audit-rejected because required velocity repeatability was
not enforced. The corrected v3 gate then completed three fresh responses and
passed. Occupancy and mass are conserved; the fixed 3x3/15 mm action-aligned
velocity field passes with repeat/action ratio 0.160 and minimum correlation
0.964; contact-node count passes at 0.144/0.988; and normal impulse passes at
0.090/0.995. Stress and elastic invariants pass and are the only admitted
non-kinematic H2 families. Plastic state is excluded: maximum absolute
`log(J_p)` is 10.748, far above the frozen 0.05 plausibility limit for the
effectively elastic material. These are qualified solver inputs, not evidence
that H2 improves prediction.

The prospectively frozen engineering smoke set is also complete. All 12
episodes pass every numerical, interaction, fixed-timing, schema-v2, tensor,
memory, signal, and baseline-loss check: eight training episodes and four
validation episodes, including two validation episodes on reserved initial
surface 2101. The test count is zero and the protected test targets remain
unopened. Every tensor pair uses a separate `model_inputs.npz` and
`targets.npz`, is 1,551,986 uncompressed bytes, includes stress and elastic
inputs, and excludes plastic state. Chrono local action-signal RMS spans
8.499--12.318 mm; maximum coarse-prior penetration spans 3.185--11.737
micrometers; raw Newton beats no deformation at both checkpoints in every
episode. The reproduced aggregate hash is
`c473e4b79a5c615f88c52cdb2f5f74860848eaf6102a1a751fda45e6eedc24c0`
and explicitly permits full-dataset generation.

The shared capacity-controlled B3/H0/H1/H2 U-Net, training orchestration, and
deterministic particle lift are implemented and pass 19 focused tests. The
complete prospective locked-evaluator preflight adds 12 passing tests, for 31
focused tests across the four components. Each
variant has exactly 289,172
trainable parameters, with immutable masks preserving capacity across direct,
parameter, and latent ablations. The prospective contract declares three
training seeds, train-only normalization, heteroscedastic loaded/post-unload
heads, bounded residual corrections, validation-only conformal calibration and
selection, and refusal to plan or fit before the bulk dataset passes. That gate
has now passed: the frozen training plan binds all 64 admitted train/validation
pairs and train-only normalization, all 12 declared variant/seed fits are
complete, and validation-only selection chose B3 seed 20261024 and H0/H1/H2
seed 20261023. The lift
passes a real admitted-state preflight on 303,829 particles and all 14,161 valid
cells, reproducing a perturbed requested surface to 2.329e-10 m while preserving
all declared state invariants. No locked-test model score exists. The evaluator
implementation covers inference, all required
baselines and controls, particle-state audits, parameter sensitivity,
uncertainty, aggregation, and the final report. After model selection it froze
the original 24-episode v1 evaluation plan, wrote the explicit unlock and
open-once markers, and completed all 24 one-shot v1 targets. V1 then failed
closed at admission: episode 009 alone exceeded the prospectively frozen
single guide tolerance, so prediction was correctly refused.

The separately authorized v2 recovery was frozen before target generation. It
reuses the exact v1-selected models, normalization, and calibration without
refitting or reselection; declares dimensionally explicit component guide
tolerances; freezes the qualified two-worker Newton identity; and contains 24
new physical inputs with zero exact overlap with all 88 v1 inputs. Reserved
surface 3102 passes analytic generation and native SCM round-trip qualification
with 4.612 micrometers maximum error. The target-free manifest, model/source/
surface-hashed evaluator plan, and selection identity were frozen before the
explicit unlock. V2 has now opened once: all 24 Chrono targets pass, all five
Newton priors are prepared, and 24 response manifests exist. The original
two-worker queue produced 23 manifests; episode 012 failed on a non-finite
plastic Jacobian, then succeeded only when retried alone after the other 23
were skipped. All 24 numerical response checks and prospective guide limits
pass, but the successful serial retry violates v2's frozen requirement to use
exactly two independent Newton processes without mixing serial and dual target
generation. This deviation remains part of the provenance and prevents v2
from being relabeled as a clean prospective confirmation.

After explicit authorization to advance the experiment while retaining v3 as
the prospective branch, v2 continued as a qualified engineering analysis. The
machine admission passes all seven checks and admits 24/24 episodes. All 24
predictions, particle lifts, matched sensitivity results, and the integrity-
checked final report now exist. Prediction exposed a NumPy-Boolean JSON
serialization defect only after the 24 episode artifacts completed. The
frozen evaluator and test hashes were restored unchanged, and a separate
[v2 continuation wrapper](../../scripts/continue_phase1_evaluation_v2.py)
converted only NumPy JSON scalars before resuming aggregation. The final report
passes 33/49 checks and fails 16, so `phase1_exit_demonstrated=false`: H1
strongly improves on raw Newton without a bad failure tail, but does not beat
B3 on joint holdouts, does not reach the frozen H0 material-ablation margin,
shows weak parameter-control dependence, and matches only 6/8 eligible
sensitivity directions. H2 is worse than H1. V2 is therefore a completed,
informative failed evaluation rather than an unfinished blocker; v3 is the
prospective branch for any model or protocol revision. Exact surface, material,
preparation-failure, export-diagnosis,
qualification, smoke, and contract evidence is recorded in the
[Phase 1 chronological record](phase1-running.md).

The post-v2 direction produced the successful direct-v4 result: reliable
one-action prediction is established over the prospectively frozen synthetic
parameter domain. The completed parameter box remains operationally qualified
but is not realistic calibration for a named soil. Inputs should remain
robotics-defensible or directly exported by MPM; deeper soil constitutive
modeling is not an implicit next step. Sequential world-model work is now the
next research stage and requires its own prospective contract and fresh
protected evidence.

The first successor draft is now machine-readable and source-backed. It narrows
the candidate terrain to a cohesionless, dry-sand-like synthetic SCM family,
varies only `bekker_kphi=1.5e6--2.0e6 N/m^(n+2)`, and fixes `Kc=0`, `n=1.1`,
cohesion `0 Pa`, friction `30 degrees`, Janosi shear `0.01 m`, elastic stiffness
`2e8 Pa/m`, and damping `3e4 Pa s/m`. This is an engineering-plausible
simulator family, not a calibrated named soil. Friction is fixed because the
declared action has no tangential motion or rotation.

The candidate ladder contains no-deformation and raw-Newton baselines; a
capacity-controlled direct predictor (`D0`); a minimal Newton-surface residual
(`R0`); a robotics-facing occupancy, mass, vertical-velocity, and contact
ablation (`R1`); then stress (`R2S`) and elastic deformation (`R2E`) as separate
optional ablations. Plastic state and a bundled stress-plus-elastic variant are
excluded. A Newton-added-value claim requires a residual to beat both raw
Newton and `D0` on joint holdouts.

The six input identities are now frozen in the source-hashed
[screening plan](../../diagnostics/phase1_one_action_successor_v1/screening_plan.json),
SHA-256 `5878257631bd0099afae3ce0c0792dd5f90c301515855a9de2292e8ad8bde2c4`.
Execution began on 2026-10-31 with two workers under the frozen
[execution plan](../../outputs/validity_experiment/newton/phase1_one_action_successor_v1/screening/successor_screen_execution_plan.json),
SHA-256 `f9347f18b7dc3c1f09b6fe2425f4c341c91abecb3b54f5c5037eb5ea527bb0b1`.
All six fresh Chrono episodes pass. The six legacy fixed-depth metric beds also
completed, but all six Newton preparations were correctly rejected at the
surface gate with the already known 6.072 mm RMSE; therefore no response was
admitted from that path. The rejected preparations and execution log remain
preserved.

On 2026-11-01 a separate common-flat-base recovery was frozen before runtime at
`outputs/validity_experiment/newton/phase1_one_action_successor_v1/common_base_recovery_v1/recovery_plan.json`,
SHA-256 `927941694b8d73b24d8063a8f65a6dd629aa435a6b9477f02097974c9ab6d91f`.
It reuses the six accepted Chrono episodes, verifies their common initial-state
identity, generates one fresh shared common-base preparation, and schedules six
fresh fixed-time Newton responses with two workers. It does not rerun Chrono or
delete the rejected evidence. No bulk, training, validation, or protected
target may be generated from this draft. Only after this recovery establishes
valid responses, directional behavior above the repeatability floor, endpoint
separation, and numerical admission can the successor data/evaluation contract
and its exit gates be frozen prospectively.

That recovery and its separately frozen directional analysis are now complete.
The common-flat-base preparation is accepted, all six fresh responses pass
numerical and coarse-interaction admission, and every declared `Kphi`
comparison is monotone for footprint peak depression, mean depression, and
displaced volume at loaded and post-unload checkpoints. Mean-depression
endpoint separation is 5.725 mm at 30.65625 N and 6.974 mm at 45.984375 N;
the inherited same-build Chrono repeatability floor is exactly zero. All three
`Kphi` cases also show greater deformation at the higher force. The directional
analysis plan has SHA-256
`ac2e98fb3cab966c22ac8ae47cc4e11829fe25eae66d773b3bc80daafcfd838f`
and its summary has SHA-256
`a58d86a5f7b581f1bd3ee3aef936d68992bc7d587f2d255d9d87081277a06e1b`.
The engineering screen therefore passes and permits freezing a prospective
successor data/evaluation contract. It does not itself permit bulk or protected
target generation, establish neural correction, or validate a real-soil model.

The successor data/evaluation contract is prospectively frozen at SHA-256
`834db42409fd48dfb2136b93192dd5fd22233733ac09dfaf8d7e5bcaf6aef4fd`.
Its target-free plan fixes 48 training, 16 validation, 24 protected test, and
six protected matched-sensitivity episodes. The 94 physical input identities
are unique; the physical manifest, test lock, and sensitivity lock have
SHA-256 values
`2df4ced81aa85a88536b72bd28c8a736e8dabf898ffeb891891678b9e7682725`,
`0390d46bfd5860b08518f3b99ab116084f24138939c04435f29582c3feedf713`,
and `a003ec52f2fb43c94d5d760e06a924c3b49809a0ddf415a6abbb718ff18a4139`.
Only `bekker_kphi` varies or enters the global parameter vector. The contract
freezes the D0/R0/R1 ladder, separate optional R2S/R2E ablations, explicit
Newton-added-value gates, and the exclusion of plastic state.

All six fresh surface seeds 4101--4104, 4201, and 4301 pass analytic and native
Chrono SCM initialization qualification. No response target was generated by
that qualification. The separately frozen successor smoke plan has SHA-256
`3d861da58edaf697ca7b5b494589fce99b926a7a3c13c19dec19026eedbafee7`;
it selects exactly eight training and four validation episodes on seeds
4101--4104, with zero test and zero protected-sensitivity members. The completed
smoke summary has SHA-256
`8c66e79f513ef40f1e680efad719500713f57523c9013c4907fa880060919989` and
admits all 12/12 members at 8/4/0/0. Every aggregate check is true, remaining
train/validation generation is permitted, and protected generation is denied.

The train/validation continuation is complete. Its bulk plan has
SHA-256 `5e56f58570666c81e73e06ee34ee3f4e4193c9917d81cae74d11f66fb0de8b49`,
shares the smoke output roots, and binds the exact hashes of all 12 admitted
smoke episode summaries, tensors, Newton manifests, and Chrono manifests. It
refuses to regenerate those members and selects only the remaining 40 training
and 12 validation targets. Both the 24-test and six-case protected-sensitivity
target sets stay inaccessible. All 64 Chrono/Newton/tensor pairs and all five
preparations completed. The legacy aggregate remains preserved as failed at
SHA-256
`f80c9f018758438ecac0300cfc35c51e828af08a3268ba5fc791a2501f748955`
because member 019 alone fails the legacy unified guide tolerance. The
artifact-only v2 plan and passing summary at
`aedca2736bbe8fbf5b2543d9d41d470c5243834acfb7945201eccd821bb85ab6`
and `dfacb7ed29b61c061dff01314e3035530db7a89d81617e4c117db7e90acc1d81`
apply the independently prospective component tolerances, bind all 384
artifacts, perform no simulation rerun or replacement, admit 64/64, permit
training, and continue to deny protected work.

The successor model/training layer implements equal-capacity D0, R0, R1, R2S,
and R2E variants through
immutable masks over one three-level U-Net. The global condition is exactly
`[center_x, center_y, normal_force, bekker_kphi]`; fixed friction is not a
feature. D0 uses the initial surface as its base, while every R variant uses
raw Newton. R1 adds only robotics-facing occupancy, mass, vertical velocity,
contact count, and normal impulse; R2S and R2E add stress and elastic fields
separately. There is no combined R2 variant and no plastic channel. D0/R0/R1
form the core selection pool, while R2S/R2E remain optional individual
ablations. Three seeds, train-only normalization, validation-only early
stopping and calibration, source/tensor hashes, and protected-lock checks are
declared. Nine focused successor tests and all 14 historical model/trainer
regression tests pass. The plan and train-only normalization are frozen at
SHA-256 values
`2b3b71023c908b1c2c953e558edf4e1dae28c7af775b7f091f16aff5190a0426`
and `969a3378dab6de540eed912a30c613ead129a43e7e6d8d0df49712c2f04269d6`.
All 15 fits, validation-only selection, and validation-only uncertainty
calibration are complete. Selected seeds are D0/R2E `20261102`, R0 `20261101`,
and R1/R2S `20261103`; selection-summary SHA-256 is `3a2ffef...e08e`.

The successor evaluation layer is complete and closed failed. Its frozen
evaluation plan `5b9f10...cc02c` opened exactly 24 test plus six sensitivity
targets. After the preserved serial Newton retry and artifact-only admission
repair, all 30 episodes admitted and prediction/reporting completed.
Prediction `b825bd...a2dc3` shows 24/24 sensitivity-direction agreement for
every model, but final report `c5995e...c3f9` records
`no_positive_successor_claim`. D0 is the strongest model at approximately
1.82--1.86 mm median RMSE. R0/R1/R2S/R2E are approximately 2.86--4.05 mm
across checkpoint/region combinations and do not beat D0; no Newton-added-value
or optional-field-value claim passes. Qualification `9205c2...1570` records
`phase1_goal_achieved=false`.

The separate direct-v4 branch is complete under its own fresh identities.
Its fixed D1 wrapper performs no fitting and consumes no Newton fields. The
confirmation plan was frozen before authoritative validation; validation then
passed all 20 gates on the original 16 validation episodes without using any
v1 test member. All six new surfaces qualified, the joint unlock/open occurred
once, and all 24 fresh test plus six fresh sensitivity Chrono targets are now
complete. The revision-only continuation is frozen at `0b37fb...5d54`; six
metric beds, six prepared Newton states, and 30/30 finite responses pass. The
protected dataset summary `32d476...7e06` admits all 30 and permits prediction.
No simulator worker is active. Locked prediction `9403c4...a62`, final report
`a73067...a2e8`, qualification `eece4d...544c`, and completion audit
`d65358...436cd` all pass. The report passes 25/25 checks and closes Phase 1
under the direct-surrogate claim. It cannot establish Newton+neural added
value.

The bulk route is complete and passed: all five preparations and all 64
train/validation Chrono/Newton/tensor pairs are admitted, with stress and
elastic retained for H2 and plastic excluded. Every aggregate check is true.
The training plan, 12 model fits, per-variant validation selection, and
validation-only uncertainty calibration then completed before the test unlock.
The v1 test set was legitimately opened once under its frozen evaluator plan
and its failed admission remains immutable. The v2 test set has now been
opened once under its separate prospective plan, after the unchanged selection
identity was rebound and verified. The bulk route retains per-surface
preparation reuse, separate input and target archives, schema-v2 H2 fields,
resumable identity checks, and the protected ordering proven by the recorded
plan, selection, unlock, and open-marker hashes.

The frozen 88-input manifest contains no pair of episodes with identical
initial-surface seed, action position, and force while varying only soil
parameters. Therefore it cannot by itself supply the matched sweeps required by
the parameter-direction gate. The already prospectively frozen five-case
material rectangle is the canonical matched-sweep sensitivity suite: all five
cases share one initial bed and action while varying the declared soil
parameters. Those targets remain excluded from fitting, normalization,
calibration, model selection, and locked-test accuracy. They may be used only
by the predeclared final evaluator for the directional sensitivity diagnostic.

### Phase 1 artifact routing

These are the canonical locations and their current evidence state:

| Artifact | Canonical location | Current state |
| --- | --- | --- |
| machine contract | [phase1_bed_state_v1.json](../../configs/phase1_bed_state_v1.json) | frozen pre-screening contract |
| chronological evidence | [phase1-running.md](phase1-running.md) | complete through direct-v4 freeze/validation/unlock, 30/30 protected runtime/admission, 25/25 report, final qualification, and completion audit |
| dataset plan | `.../phase1_bed_state_v1/dataset_plan.json` | frozen locally; 48/16/24 inputs; test identities opened once only after selection |
| contract planner | [run_phase1_contract_screen.py](../../scripts/run_phase1_contract_screen.py) | frozen target-free plan complete |
| surface/material screening | [run_phase1_screening.py](../../scripts/run_phase1_screening.py) and [run_phase1_newton_common_base.py](../../scripts/run_phase1_newton_common_base.py) | six surfaces and Chrono 5/5 pass; original Newton screen preserved failed; common-base v2 admits all 5 pairings as a bounded coarse prior |
| surface generator | [phase1_surface.py](../../scripts/phase1_surface.py) | six declared seeds qualified |
| screening plan | `.../phase1_bed_state_v1/screening/screening_plan.json` | frozen source/environment identity |
| original screening summary | `.../phase1_bed_state_v1/screening/screening_summary.json` | surfaces pass; original fixed-depth Newton route failed and is preserved |
| repaired operational-screen summary | `.../phase1_bed_state_v1/newton_common_base_v2/qualification_summary.json` | all five pairings admitted; bulk permission true at bounded coarse-prior level; no real-soil realism claim |
| smoke contract and dataset generator | [phase1_dataset_smoke_v1.json](../../configs/phase1_dataset_smoke_v1.json) and [run_phase1_dataset.py](../../scripts/run_phase1_dataset.py) | complete; frozen 8/4/0 set passes 12/12, test targets unopened, full-dataset permission true |
| bulk train/validation generator | [phase1_dataset_bulk_v1.json](../../configs/phase1_dataset_bulk_v1.json) and [run_phase1_dataset_bulk.py](../../scripts/run_phase1_dataset_bulk.py) | complete and passed for 48/16/0: five preparations and 64/64 Chrono/Newton/tensor pairs admitted; all aggregate checks true |
| latent qualification | [phase1_latent_export_v3.json](../../configs/phase1_latent_export_v3.json), [run_phase1_latent_qualification.py](../../scripts/run_phase1_latent_qualification.py), and `diagnostics/phase1_latent_export_v3/` | v2 preserved and audit-rejected; corrected v3 passes three fresh repeats; stress and elastic admitted, plastic excluded |
| shared direct/hybrid architecture | [phase1_bed_state_model.py](../../scripts/phase1_bed_state_model.py) | B3/H0/H1/H2 implemented, tested, and fit for three seeds each with equal 289,172-parameter capacity |
| shared direct/hybrid trainer | [phase1_training_v1.json](../../configs/phase1_training_v1.json) and [train_phase1_bed_state.py](../../scripts/train_phase1_bed_state.py) | training plan and train-only normalization frozen; 12 fits complete; per-variant selection and uncertainty calibration completed on validation only |
| deterministic particle lift | [phase1_particle_lift.py](../../scripts/phase1_particle_lift.py) and [test_phase1_particle_lift.py](../../tests/test_phase1_particle_lift.py) | implemented; synthetic suite and one admitted 303,829-particle state pass surface-reproduction and preservation audit |
| locked evaluator | [phase1_evaluation_v1.json](../../configs/phase1_evaluation_v1.json), [evaluate_phase1_bed_state.py](../../scripts/evaluate_phase1_bed_state.py), and [test_evaluate_phase1_bed_state.py](../../tests/test_evaluate_phase1_bed_state.py) | frozen after selection; 24/24 test Chrono targets, 5/5 preparations, and 24/24 Newton responses complete; aggregate admission is `failed_or_incomplete` because episode 009 alone fails the guide guard; prediction correctly refused |
| v2 recovery contract and planner | [phase1_evaluation_v2.json](../../configs/phase1_evaluation_v2.json), [plan_phase1_evaluation_v2.py](../../scripts/plan_phase1_evaluation_v2.py), [test_phase1_evaluation_v2.py](../../tests/test_phase1_evaluation_v2.py), and [continue_phase1_evaluation_v2.py](../../scripts/continue_phase1_evaluation_v2.py) | numerical admission passes 24/24; the serial episode-012 retry remains a prospective-identity deviation; conditional prediction/reporting is complete and the final gate fails 16/49 checks |
| successor contract and target-free planner | [phase1_one_action_successor_contract_v1.json](../../configs/phase1_one_action_successor_contract_v1.json), [plan_phase1_one_action_successor.py](../../scripts/plan_phase1_one_action_successor.py), and [test_phase1_one_action_successor_plan.py](../../tests/test_phase1_one_action_successor_plan.py) | frozen 48/16/24 plus six protected sensitivity inputs; physical identities unique; test and sensitivity locks closed; seven planner tests pass |
| successor surface qualification | [qualify_phase1_one_action_successor_surfaces.py](../../scripts/qualify_phase1_one_action_successor_surfaces.py) and `.../phase1_one_action_successor_contract_v1/surface_qualification/` | all six fresh surface identities pass analytic and native SCM initialization qualification; no response targets generated |
| successor engineering smoke | [phase1_one_action_successor_smoke_v1.json](../../configs/phase1_one_action_successor_smoke_v1.json), [run_phase1_one_action_successor_smoke.py](../../scripts/run_phase1_one_action_successor_smoke.py), and [test_phase1_one_action_successor_smoke.py](../../tests/test_phase1_one_action_successor_smoke.py) | passed 12/12 at 8/4/0 plus zero protected sensitivity members; plan hash `3d861d...fee7`; summary hash `8c66e7...9989`; remaining train/validation permitted and protected denied |
| successor bulk continuation | [phase1_one_action_successor_bulk_v1.json](../../configs/phase1_one_action_successor_bulk_v1.json), [run_phase1_one_action_successor_bulk.py](../../scripts/run_phase1_one_action_successor_bulk.py), and [test_phase1_one_action_successor_bulk.py](../../tests/test_phase1_one_action_successor_bulk.py) | complete 48/16/0/0; all 64 Chrono/Newton/tensor pairs and five preparations exist; immutable v1 aggregate `f80c9f...8955` fails only member 019's legacy unified guide check; protected targets absent |
| successor bulk recovery | [phase1_one_action_successor_bulk_recovery_v2.json](../../configs/phase1_one_action_successor_bulk_recovery_v2.json), [recover_phase1_one_action_successor_bulk_v2.py](../../scripts/recover_phase1_one_action_successor_bulk_v2.py), and [test_recover_phase1_one_action_successor_bulk_v2.py](../../tests/test_recover_phase1_one_action_successor_bulk_v2.py) | artifact-only plan `aedca2...5ab6` binds all 384 files and the failed v1 summary; independently prospective component guide contract passes 64/64 in summary `dfacb7...1d81`; no rerun, replacement, or protected access; training permitted |
| successor model and training | [phase1_one_action_successor_training_v1.json](../../configs/phase1_one_action_successor_training_v1.json), [phase1_one_action_successor_model.py](../../scripts/phase1_one_action_successor_model.py), [train_phase1_one_action_successor.py](../../scripts/train_phase1_one_action_successor.py), and [test_phase1_one_action_successor_training.py](../../tests/test_phase1_one_action_successor_training.py) | training plan `2b3b71...0426` and train-only normalization `969a33...9d6` frozen; all 15 equal-capacity fits complete; validation-only selection/calibration summary `3a2ffe...e08e` chose D0/R2E seed 20261102, R0 seed 20261101, and R1/R2S seed 20261103 |
| successor locked evaluation | [phase1_one_action_successor_evaluation_v1.json](../../configs/phase1_one_action_successor_evaluation_v1.json), [evaluate_phase1_one_action_successor.py](../../scripts/evaluate_phase1_one_action_successor.py), [run_phase1_one_action_successor_protected.py](../../scripts/run_phase1_one_action_successor_protected.py), [predict_phase1_one_action_successor.py](../../scripts/predict_phase1_one_action_successor.py), [test_phase1_one_action_successor_evaluation.py](../../tests/test_phase1_one_action_successor_evaluation.py), [test_phase1_one_action_successor_protected.py](../../tests/test_phase1_one_action_successor_protected.py), and [test_predict_phase1_one_action_successor.py](../../tests/test_predict_phase1_one_action_successor.py) | evaluation plan `5b9f10...cc02c` froze exact 24+6 membership before joint unlock/open; protected prediction `b825bd...a2dc3` and final report `c5995e...c3f9` are complete; all five models pass sensitivity direction but fail at least one required predictive gate, so no supported claim is permitted |
| successor protected Newton recovery v1 | [phase1_one_action_successor_protected_recovery_v1.json](../../configs/phase1_one_action_successor_protected_recovery_v1.json), [recover_phase1_one_action_successor_protected_v1.py](../../scripts/recover_phase1_one_action_successor_protected_v1.py), and [test_recover_phase1_one_action_successor_protected_v1.py](../../tests/test_recover_phase1_one_action_successor_protected_v1.py) | plan `d48f40...35f89` preserved the first failure and 29 completed manifests; its dual-process retry failed identically on member 019 while the companion passed; summary `6f46e5...a3f6e` is failed and prediction remained prohibited |
| successor protected Newton recovery v2 | [phase1_one_action_successor_protected_recovery_v2.json](../../configs/phase1_one_action_successor_protected_recovery_v2.json), [recover_phase1_one_action_successor_protected_v2.py](../../scripts/recover_phase1_one_action_successor_protected_v2.py), and [test_recover_phase1_one_action_successor_protected_v2.py](../../tests/test_recover_phase1_one_action_successor_protected_v2.py) | serial missing-only plan `4da69d...bd9f` froze after two preserved dual-process failures; summary `d18ad7...23d8` passes all recovery checks and supplies the missing response, while permanently qualifying member 019 as a serial retry rather than clean two-worker evidence |
| successor protected admission recovery v3 | [phase1_one_action_successor_protected_admission_recovery_v3.json](../../configs/phase1_one_action_successor_protected_admission_recovery_v3.json), [recover_phase1_one_action_successor_protected_admission_v3.py](../../scripts/recover_phase1_one_action_successor_protected_admission_v3.py), and [test_recover_phase1_one_action_successor_protected_admission_v3.py](../../tests/test_recover_phase1_one_action_successor_protected_admission_v3.py) | artifact-only plan `e5576d...0693` archived the failed 24-row smoke-sentinel analysis and changed no simulator/tensor array; summary `785694...07b` and protected aggregate `fb9f71...acc` pass 30/30 and preserve the serial qualification |
| successor final qualification | [phase1_one_action_successor_final_qualification_v1.json](../../configs/phase1_one_action_successor_final_qualification_v1.json), [qualify_phase1_one_action_successor_final.py](../../scripts/qualify_phase1_one_action_successor_final.py), and [test_qualify_phase1_one_action_successor_final.py](../../tests/test_qualify_phase1_one_action_successor_final.py) | qualification `9205c2...1570` binds the immutable failed report, prediction, recovered admission, serial recovery, and archived original failure; it records `phase1_goal_achieved=false` and requires a new prospective branch |
| direct-v4 candidate and authoritative validation | [phase1_one_action_successor_direct_v4.json](../../configs/phase1_one_action_successor_direct_v4.json), [plan_phase1_one_action_successor_direct_v4.py](../../scripts/plan_phase1_one_action_successor_direct_v4.py), and [validate_phase1_one_action_successor_direct_v4.py](../../scripts/validate_phase1_one_action_successor_direct_v4.py) | confirmation plan `a6d3dc...d4428` froze before validation; D1 is a no-refit D0 sensitivity wrapper; validation `ed23f6...a22` passes all 20 checks on 16 validation episodes and uses zero v1 test episodes |
| direct-v4 surface qualification and joint unlock | [qualify_phase1_one_action_successor_direct_v4_surfaces.py](../../scripts/qualify_phase1_one_action_successor_direct_v4_surfaces.py) and [unlock_phase1_one_action_successor_direct_v4.py](../../scripts/unlock_phase1_one_action_successor_direct_v4.py) | seeds 5101--5106 pass analytic/native-SCM checks; joint unlock `588e8e...9837` and target-open marker `4ff126...be57` occurred once after validation and qualification |
| direct-v4 protected confirmation | [run_phase1_one_action_successor_direct_v4_protected.py](../../scripts/run_phase1_one_action_successor_direct_v4_protected.py) and [evaluate_phase1_one_action_successor_direct_v4.py](../../scripts/evaluate_phase1_one_action_successor_direct_v4.py) | protected plan `7385bb...63ab` and reporting plan `b89417...f60f` are frozen; protected summary `32d476...7e06` admits 30/30; prediction `9403c4...a62` and report `a73067...a2e8` pass all 25 gates |
| direct-v4 revision-only continuation | [phase1_one_action_successor_direct_v4_revision_rebind_v1.json](../../configs/phase1_one_action_successor_direct_v4_revision_rebind_v1.json), [recover_phase1_one_action_successor_direct_v4_revision.py](../../scripts/recover_phase1_one_action_successor_direct_v4_revision.py), and [test_recover_phase1_one_action_successor_direct_v4_revision.py](../../tests/test_recover_phase1_one_action_successor_direct_v4_revision.py) | plan `0b37fb...5d54` froze before downstream runtime, binds 30/30 accepted Chrono payloads, proves revision-only identity change, preserves two workers, and prohibits prediction; 5 recovery plus 3 runtime tests pass |
| direct-v4 reporting continuation | [phase1_one_action_successor_direct_v4_reporting_rebind_v1.json](../../configs/phase1_one_action_successor_direct_v4_reporting_rebind_v1.json), [run_phase1_one_action_successor_direct_v4_reporting_rebind.py](../../scripts/run_phase1_one_action_successor_direct_v4_reporting_rebind.py), and [test_run_phase1_one_action_successor_direct_v4_reporting_rebind.py](../../tests/test_run_phase1_one_action_successor_direct_v4_reporting_rebind.py) | plan `9dd7f3...3856` froze after 30/30 admission and before prediction/report; it delegates unchanged prediction/reporting through the qualified revision-only execution plan |
| direct-v4 final qualification | [phase1_one_action_successor_direct_v4_final_qualification_v1.json](../../configs/phase1_one_action_successor_direct_v4_final_qualification_v1.json), [qualify_phase1_one_action_successor_direct_v4_final.py](../../scripts/qualify_phase1_one_action_successor_direct_v4_final.py), and [test_qualify_phase1_one_action_successor_direct_v4_final.py](../../tests/test_qualify_phase1_one_action_successor_direct_v4_final.py) | outcome-neutral plan `687131...f259` preceded the outcome; qualification `eece4d...544c` passes all provenance/coherence checks and records `phase1_goal_achieved=true` |
| direct-v4 completion audit | [phase1_one_action_successor_direct_v4_completion_audit_v1.json](../../configs/phase1_one_action_successor_direct_v4_completion_audit_v1.json), [audit_phase1_one_action_successor_direct_v4_completion.py](../../scripts/audit_phase1_one_action_successor_direct_v4_completion.py), and [test_audit_phase1_one_action_successor_direct_v4_completion.py](../../tests/test_audit_phase1_one_action_successor_direct_v4_completion.py) | audit `d65358...436cd` revalidates all prediction artifacts and qualifier checks, passes, and closes Phase 1 under the bounded direct-surrogate claim |
| Phase 1 output root | `outputs/validity_experiment/newton/phase1_bed_state_v1/` | bulk and training/selection passed; v1 admission failed 23/24; v2 conditional admission passed 24/24 and its complete report records `phase1_exit_demonstrated=false` |
| final report | `outputs/validity_experiment/newton/phase1_bed_state_v1/evaluation_v2/final_evaluation_report.json` | conditional v2 report complete and failed; no Phase 1 completion report is created |

Whenever Phase 1 evidence changes, update the current-state paragraph and this
routing table in the same change. Record measurements in machine-readable
summaries first, then reflect their interpretation here. Do not create a second
document with a competing live goal, next-step list, or completion status.

## Goal

Given a valid pre-action bed state, one bounded robot-foot action, and declared
action and bed parameters, predict the observable state of the bed at the
loaded and post-unload checkpoints:

\[
(\widehat B_{loaded},\widehat B_{post}) =
\mathcal F_\theta(B_0,a,p;N(B_0,a)).
\]

Here `B0` is the pre-action bed, `a` is the action, `p` is the known
conditioning vector, and `N` is the frozen Newton MPM prior. In the frozen
v1/v2 contract, the primary model learns a bounded correction to the Newton
state. It must make a prediction without access to the Chrono loaded or
post-unload target at inference.

The frozen v1/v2 contract defined success as one neural model predicting whole
held-out bed states across unseen combinations of position, normal force,
initial surface, and two explicitly varied simulator bed controls inside the
declared domain.
It must outperform raw Newton, no deformation, the Phase 0 residual, and a
same-capacity direct neural baseline under the locked tests below.

This is intentionally a richer spatial predictor than the Phase 0
241-parameter MLP. The hybrid operates on a structured spatial state, mixes
information across neighboring cells, is conditioned on action and declared
simulator controls, may consume qualified MPM fields, and predicts an entire
state field. It remains a modest one-step model, not a general learned
simulator or a validated terramechanics model.

That v1/v2 exit failed and remains immutable. A successor contract must be
frozen prospectively and may select either a direct or Newton-conditioned
predictor according to held-out evidence. It may claim that a network corrects
Newton when it reliably improves raw Newton; it may claim added value from the
Newton prior only when the hybrid also beats the capacity-controlled direct
model.

### Relationship to NeuralMPM-style models

Phase 1 borrows the useful structure of current neural physical models: it
represents state on a grid, performs learned spatial message passing through a
U-Net, conditions the update on the action and physical parameters, and
predicts a whole field instead of independent cells.

It is not a reproduction of NeuralMPM. NeuralMPM learns particle-grid velocity
evolution from corresponding trajectories and rolls that state forward.
Chrono SCM provides surfaces, not particle trajectories or subsurface
correspondence, so Phase 1 learns an observable endpoint residual around
Newton. The direct U-Net baseline tests how much can be learned without that
physics prior; autoregressive particle-grid evolution remains Phase 2 work.

### Long-term destination and disciplinary boundary

The eventual system goal is an action-conditioned world model for footprint
planning: a planner proposes a sequence of contacts, the model predicts the
bed state after each contact, and those states feed the planner's accumulated
cost. That destination does not change the present research order. First
establish, for one bounded action, where the frozen Newton prior fails to
generalize and whether a learned predictor can reliably correct or replace its
observable bed response. Only after a satisfactory one-action mapping exists
should a prospective sequential contract train and test repeated application
from already deformed beds.

This is an empirical comparison, not a premise that Newton must fail or that a
hybrid must win. Raw Newton, a direct network, and Newton-conditioned hybrids
must be compared on held-out combinations. If a direct model generalizes
better than a hybrid, the evidence may support a learned surrogate, but it
does not support a claim that the present Newton representation adds value.

The representation should remain within quantities that can be defended and
validated from a robotics perspective. Geometry, displacement, velocity,
momentum, contact, load, and MPM-provided stress or deformation state are in
scope as simulator-native features. Consuming an MPM stress field does not
assert that its constitutive law is correct for real soil or make a new
terramechanical claim. Soil-specific constitutive descriptors, hand-built
higher-order features, or interpretations that require specialized
terramechanics are outside the default scope. If satisfactory prediction or a
sequential restart cannot be achieved without them, stop and revisit the claim
boundary and expertise requirements before expanding the pipeline.

## What "bed state" means in Phase 1

The required observable state at each checkpoint is:

- a metric height or vertical-displacement field on the accepted 5 mm Chrono
  grid;
- the valid-support mask and a derived deformation-support mask;
- the corrected Newton particle positions used to reproduce that surface;
- derived sinkage, peak, displaced-volume, footprint, centroid, and recovery
  characteristics;
- a spatial uncertainty estimate for the predicted correction.

The required checkpoints are the accepted loaded state and the state 0.25 s
after removal. Predicting both is one action-to-state query, not two unrelated
models.

Newton velocity, occupancy, contact, stress, deformation, and plastic fields
may be tested as candidate *inputs* to the residual. Chrono SCM supplies no
corresponding subsurface truth, so repeatability inside Newton makes a field a
usable solver feature, not validated soil truth. Phase 1 does not claim that
Newton stress, deformation, or plastic state is correct for real soil, and it
does not predict corrected versions of those fields. "Bed state" in the Phase
1 claim therefore means observable geometry and its audited particle
realization, not a complete constitutive restart state. A future sequential
model must define and validate its restart state separately.

## Fixed prediction domain

### Action domain

The main claim is restricted to:

| Quantity | Phase 1 bound |
| --- | --- |
| contact body | vertically guided cylindrical proxy |
| radius | fixed at 35 mm |
| center | `sqrt(x^2 + y^2) <= 0.10 m` in the bed frame |
| normal force | 30.65625--45.984375 N |
| load type | one static gravity-equivalent vertical load |
| loaded observation | Chrono-accepted settled checkpoint |
| recovery observation | 0.25 s after removal |
| tangential motion / rotation | excluded |

Pressure is derived from force and the fixed contact area; it is recorded as a
feature but is not an independent degree of freedom. The 61 N rung is outside
the Phase 1 domain and remains robustness or later-domain-expansion evidence.

### Initial surface domain

`B0` must be supplied on the common metric grid. Phase 1 must include more than
one initial surface so the network cannot reduce the problem to a lookup from
action alone. The initial-surface family is limited to fresh, history-free beds
with:

- relief within +/-5 mm of the local datum;
- maximum local slope of 10 degrees;
- spatial correlation length of at least 50 mm;
- the same bed footprint, depth, wall, and base contract as Phase 0.

At least four accepted surface seeds are used by training and at least two
accepted seeds are reserved for validation/test. A bed deformed by a previous
contact is not in this domain.

### Historical v1/v2 parameter domain

The conditioning vector must represent more than spatial geometry. At minimum
it contains:

```text
a = [center_x_m, center_y_m, normal_force_n, phase]
p = [bekker_kphi, mohr_friction_deg]
```

The initial Chrono screening box is:

| Parameter | Range | Phase 0 reference |
| --- | ---: | ---: |
| `bekker_kphi` | 640,000--960,000, in Chrono-native units | 800,000 |
| `mohr_friction_deg` | 24--32 degrees | 28 degrees |

All other Chrono SCM values remain fixed at the Phase 0 values during the first
Phase 1 experiment. The Newton material and numerical configuration also stay
frozen at the Phase 0 baseline. Thus `p` describes a known synthetic bed
condition that the residual must account for; it is not a fitted Newton
material and not an inferred real-soil property.

### Parameter plausibility policy

The completed v1/v2 screen demonstrates that the declared box is numerically
usable and produces accepted simulator responses. It does **not** demonstrate
that the box is a realistic domain for a named soil. The repository's Chrono
configuration explicitly records that its values were selected for visible
deformation and were not calibrated from a soil test.

Any successor experiment that describes its domain as realistic or
engineering-plausible must justify each varied range before target generation
using a cited source, a simulator-provided reference case, or direct
measurement that is interpretable without new constitutive modeling. The
justification, units, coupled fixed parameters, and applicable soil class must
be recorded in the prospective contract. Operational acceptance by Chrono and
Newton is necessary, but it is not a realism certificate.

The intended near-term claim is therefore performance over a bounded,
plausibly chosen simulator domain, not recovery of physical soil properties.
It may support robust prediction across declared controls; it may not support
soil identification, calibrated terramechanics, or transfer to real terrain.
If establishing a useful range requires selecting or fitting additional
constitutive laws beyond this boundary, pause the pipeline and revise the
claim with appropriate terramechanics expertise instead of silently adding
complexity.

### Prospective successor draft domain

The candidate domain is recorded in
[phase1_one_action_successor_v1.json](../../configs/phase1_one_action_successor_v1.json)
with its source URLs and units. It is deliberately a one-dimensional vertical
response family:

| Quantity | Candidate value | Status and rationale |
| --- | ---: | --- |
| `bekker_kphi` | `1.5e6--2.0e6 N/m^(n+2)` | only varied control; brackets published and official Chrono references |
| `bekker_kc` | `0` | fixed cohesionless reference |
| `bekker_n` | `1.1` | fixed common dry-sand/reference exponent |
| cohesion | `0 Pa` | fixed cohesionless reference |
| friction | `30 degrees` | fixed; vertical no-slip action weakly excites shear |
| Janosi shear | `0.01 m` | fixed official reference |
| elastic stiffness | `2e8 Pa/m` | fixed official reference and greater than `Kphi` |
| damping | `3e4 Pa s/m` | fixed official reference |

The source basis is the official Chrono
[SCMTerrain API](https://api.projectchrono.org/classchrono_1_1vehicle_1_1_s_c_m_terrain.html)
for parameter semantics and units, the official
[wheel-rig terrain schema](https://api.projectchrono.org/_y_a_m_l_schema_wheel_rig_terrain.html)
for the cohesionless reference case, Lim et al.'s
[dry-sand pressure-sinkage parameters](https://doi.org/10.5140/JASS.2021.38.4.237),
and Gallina et al.'s
[SCM identification and transfer analysis](https://elib.dlr.de/104615/1/jrf_paper.pdf).
These sources justify a synthetic bracket, not named-soil calibration.

For the 35 mm-radius cylinder, the two declared forces produce nominal average
pressures of 7.966 and 11.949 kPa. The elementary Bekker relation with `Kc=0`
predicts roughly 6.58--12.36 mm sinkage across the candidate corners. This is a
scale sanity check only, not simulator evidence or a replacement for screening.

The draft is not frozen. Its six-case screen crosses
`Kphi={1.5e6,1.75e6,2.0e6}` with
`force={30.65625,45.984375} N` on one qualified action identity. It must show
accepted Chrono responses, directional separation above repeatability, and
admitted Newton priors. Screening artifacts are engineering evidence and must
not be reused as protected evaluation targets.

For historical v1/v2, before bulk generation, the four corners and center of
this parameter box must
pass the Chrono oracle contract and the Newton prior admission checks. The
admitted rectangle and every fixed parameter must then be written to a
versioned machine-readable Phase 1 contract. If screening forces a smaller
box, update this document and freeze the new bounds before generating training
targets. Do not silently train with constant parameters and retain a
parameter-conditioned claim.

## What Phase 0 has already validated

Phase 0 established the starting point, not the Phase 1 result:

- a fresh, provenance-complete Chrono-to-Newton path works for 10 independent
  35 mm actions at 31 N and 46 N;
- raw Newton is a useful bounded geometric prior on those actions despite not
  being strictly mechanics-qualified;
- one frozen 8-24-1 MLP with 241 trainable parameters improves untouched +y
  validation and -y test positions at 46 N for loaded and post-unload states;
- the held-out corrected footprint RMSE is about 1.23--1.28 mm, versus
  10.25--13.85 mm for raw Newton, with all declared local comparisons passing;
- the fit locks, source/model hashes, surface reproduction, and particle
  preservation audits are reproducible.

Phase 0 did **not** validate continuous load interpolation, varied soil
parameters, varied initial beds, sequential actions, corrected mechanics
latents, uncertainty calibration, or a spatial neural operator. Its stress and
velocity-gradient exports were zero, its elastic/deformation tensors were
identity, and its plastic Jacobian was one. Those placeholders were correctly
excluded from the Phase 0 learner.

## What must be built

### 1. A prospective Phase 1 episode contract

Create a versioned contract and generator that jointly sample initial surface,
position, force, and the two simulator bed controls inside the bounds above. Each
episode must independently generate accepted Chrono truth and an admitted
Newton rollout from the same `B0` and action.

Every episode records full simulator configuration, source revision, initial,
loaded, and post-unload maps, action and parameter vectors, masks, event times,
Newton particle/grid states, gate results, and hashes. No loaded or post-unload
Chrono target may be consumed by the Newton preparation path.

### 2. Informative mechanics-field export

Repair or replace the placeholder Newton export before calling the model
stress-, strain-, or plastic-conditioned. Each candidate field must be:

- finite, correctly shaped, unit- and frame-documented;
- nonconstant where the action creates a response;
- meaningfully different between initial, loaded, and post-unload states;
- stable enough under same-build repeats to distinguish signal from numerical
  variation;
- reducible to rotation-aware scalar invariants or expressed in the
  action-aligned frame.

The frozen v1/v2 contract required occupancy/mass, velocity, contact, and one
non-kinematic family. That completed qualification evidence remains historical.
A successor must not automatically carry the non-kinematic requirement
forward. Occupancy/mass, velocity or momentum, and contact are the preferred
robotics-facing state. Stress and deformation may be tested as separate,
qualified MPM-feature ablations, not bundled prerequisites. Plastic state,
new constitutive descriptors, and soil-theory-derived features require an
explicit claim-boundary review before inclusion. Unqualified fields remain
absent from the model and from all claims.

### 3. A modest parameter-conditioned U-Net

The primary residual is a 2D U-Net over the common surface grid. The starting
architecture is deliberately small:

- three resolution levels;
- 16 base channels, doubled at each downsampling level;
- residual convolution blocks with GroupNorm and SiLU;
- a shared encoder/decoder for both observation phases;
- zero-initialized bounded residual heads for loaded and post-unload mean;
- matching log-variance heads for heteroscedastic uncertainty;
- between 100,000 and 1,000,000 trainable parameters, with the exact count
  logged before training.

Spatial input channels include `B0`, raw Newton loaded and post-unload
displacement, valid support, occupancy/mass, contact, action-relative x/y and
radius, signed foot distance, and only the qualified MPM fields selected for a
declared ablation. Global action and simulator bed controls are normalized and
injected by feature-wise affine conditioning at every U-Net scale, not appended
only to the final layer.

For checkpoint `tau`, the prediction remains a bounded physics residual:

\[
\widehat H_\tau = H^N_\tau + s_\tau\tanh(R_\theta(X,a,p,\tau)).
\]

The correction scale, boundary taper, and no-action identity penalty are fixed
from training data only. The model may correct an admitted Newton response; it
may not turn a mechanics-invalid episode into usable data.

This capacity is large enough to form a spatial latent representation and
condition it on several parameters, while still being small enough for the
available synthetic dataset and meaningful ablations. Parameter count alone
is not evidence of adequacy; held-out results and learning curves decide that.

### 4. Baselines and ablations

Train and evaluate the following under the same episode splits and metrics:

| ID | Model | Purpose |
| --- | --- | --- |
| B0 | no deformation | establishes whether any dynamics help |
| B1 | frozen raw Newton | establishes residual value |
| B2 | frozen Phase 0 MLP | measures improvement over the 241-parameter model |
| B3 | direct U-Net: `B0 + a + p -> B` | direct learned-state baseline without Newton |
| H0 | hybrid U-Net without soil `p` | isolates parameter conditioning |
| H1 | hybrid U-Net with geometry, action, and `p` | required Phase 1 model |
| H2 | H1 plus qualified mechanics latents | tests incremental value of solver-native fields |

Under the frozen v1/v2 contract, H1 was the minimum deliverable. H2 could
become the named final model only if its held-out evidence was better than or
statistically indistinguishable from H1 without a worse failure tail. Shuffle
and constant-parameter controls had to show that H1 used `p`, rather than
merely accepting unused input slots.

A successor must ablate robotics-facing kinematics/contact and optional
stress/deformation features separately. A single expanded mechanics bundle
cannot establish that any individual field is useful, and adding more soil
state is not the default response to a generalization failure.

The successor draft instead uses the following capacity-controlled comparison:

| ID | Model input | Question |
| --- | --- | --- |
| B0 | initial surface only; no update | is any predicted deformation useful? |
| B1 | raw Newton loaded/post surfaces | how good is the uncorrected prior? |
| D0 | initial surface, action geometry, force, `Kphi` | can a direct model generalize without Newton? |
| R0 | D0 inputs plus raw Newton loaded/post displacement | does the minimal Newton geometric prior help? |
| R1 | R0 plus occupancy, mass, vertical velocity, contact count, normal impulse | do robotics-facing solver fields help? |
| R2S | R1 plus mean and von Mises stress | does qualified stress add predictive value? |
| R2E | R1 plus elastic Jacobian and isochoric shear | does qualified deformation add predictive value? |

All learned variants use the same capacity and training/evaluation split.
Selection is among `D0`, `R0`, and `R1`; `R2S` or `R2E` may be promoted only
if it individually improves on `R1` without worsening the failure tail.
Qualification of a field is necessary but does not establish predictive value.
Plastic state, new constitutive descriptors, and combined higher-complexity
variants are prohibited in the initial successor contract.

A particle GNN is an optional comparison after H1. It is not required for the
Phase 1 exit because Chrono SCM supplies no particle correspondence and the
supervision is a heightfield. A classical PINN is also not required: there is
no agreed differentiable PDE residual connecting Chrono SCM and Newton. The
U-Net may use physics-informed regularizers, but it must not be called a PINN
unless governing-equation residuals are explicitly enforced.

### 5. Training objective

Train through the observable surface with separate loaded and post-unload
terms. The objective includes:

- robust surface error in the footprint, twice-radius crop, and valid bed;
- peak, mean, displaced-volume, footprint, centroid, and recovery errors;
- residual-magnitude and spatial-smoothness penalties;
- no-action identity and boundary-taper penalties;
- uncertainty negative log likelihood with a variance floor;
- corrected-particle surface-reproduction and preservation constraints.

No single weighted training loss replaces the reported metric table.

## Dataset and leakage contract

The initial full target is 88 independent episodes:

| Split | Episodes | Use |
| --- | ---: | --- |
| train | 48 | fitting weights and normalization only |
| validation | 16 | architecture choice, early stopping, uncertainty calibration |
| test | 24 | one locked final evaluation |

Freeze the complete episode manifest and split assignment before bulk target
generation. Use a low-discrepancy joint design over surface seed, x/y, force,
`bekker_kphi`, and friction. The locked test set must contain:

1. unseen positions at interpolated forces and soil parameters;
2. unseen force values in familiar spatial regions;
3. unseen in-range combinations of the two soil parameters;
4. unseen accepted initial-surface seeds;
5. joint combinations not present in train or validation.

All test coordinates and parameter values remain inside the declared bounds;
this is interpolation/generalization within a box, not zero-shot extrapolation.
Split whole episodes. Cells, particles, phases, frames, and render views from
one episode never cross splits. Fit normalization, taper, correction bounds,
and calibration using train/validation only. Run at least three declared
training seeds for H1 and the selected comparator; select by validation before
opening the test results.

Start with a 12-episode engineering smoke set to validate schemas, tensor
semantics, memory, and loss behavior. It cannot satisfy the Phase 1 claim.
Scale beyond 88 only if the predeclared action-level learning curve is still
improving and the test set remains unopened.

## Phase 1 success criteria

The following are the frozen v1/v2 gates. They remain authoritative for that
failed result and may not be retroactively relaxed or reinterpreted. A
prospective successor must freeze its own domain and model-selection gates
before new protected targets are generated. Under v1/v2, Phase 1 could exit
only when all gates passed.

### Contract and integrity

- The action, surface, and soil-parameter bounds are frozen before training.
- Every admitted episode passes the Chrono contract and Phase 0 numerical,
  guide, support, and gross-interaction guards.
- The split is prospective and hash-audited, with no episode-level leakage.
- The final model, normalization, source, configuration, and evaluation inputs
  have recorded hashes and reproduce from a clean invocation.

### Predictive accuracy

On the locked 24-episode test set, separately for loaded and post-unload:

- H1 reduces median footprint and twice-radius RMSE by at least 30% versus raw
  Newton;
- H1 improves both raw Newton and no deformation on at least 90% of test
  episodes in both local regions;
- no admitted test episode is worse than raw Newton by more than 10% or 1 mm,
  whichever tolerance is larger;
- H1 improves median local RMSE by at least 10% over the frozen Phase 0 MLP;
- H1 beats the same-capacity direct U-Net B3 on the joint-combination test
  group, demonstrating value from the Newton prior rather than capacity alone.

Report bootstrap confidence intervals over whole episodes. Dense cells do not
count as independent samples.

### Parameter use

- H1 improves median local RMSE by at least 10% over H0 on the soil-parameter
  holdout group;
- shuffling `p` across test episodes causes a measurable and statistically
  reported loss of accuracy;
- across matched sweeps, predicted changes in sinkage, volume, and recovery
  have the same direction as Chrono for at least 90% of comparisons where the
  Chrono change exceeds the repeatability floor;
- sensitivity is smooth inside the box and discontinuities or saturation are
  reported as failures, not hidden by aggregate RMSE.

Passing these gates supports the statement that the residual accounts for
geometry, action load, and declared soil parameters. Merely including `p` in
the input vector does not.

### State and uncertainty validity

- All outputs are finite, remain on the valid support, respect the frozen
  correction bound, and reproduce the stored corrected surfaces;
- corrected particles preserve count and every state field not explicitly
  corrected;
- uncertainty is calibrated on validation only, and the nominal 90% interval
  covers 80--100% of test surface targets when aggregated by whole episode;
- out-of-domain actions or parameters are rejected before inference; the model
  must not silently extrapolate beyond the Phase 1 box.

### Latent-mechanics evidence

- At least one non-kinematic Newton latent family passes the export checks and
  is included in H2;
- H2 is evaluated against H1 with identical capacity controls and splits;
- the report states whether the latent improves prediction, is neutral, or
  encodes a solver artifact. Only a demonstrated improvement supports a claim
  that stress/strain/plastic information is useful.

Failure of H2 to beat H1 does not permit a positive latent-value claim. It also
does not erase an otherwise valid parameter-conditioned result. It argues
against automatically adding more mechanics channels. The next prospective
ablation should first test geometry/displacement, then velocity or momentum
and contact, then stress and deformation separately if needed.

If acceptable one-step accuracy or sequential state closure requires new soil
constitutive laws, soil-specific hidden variables, or interpretations beyond
simulator-native fields, the project must pause and revisit the claim boundary,
data source, and need for terramechanics expertise rather than treating greater

## Ordered implementation plan

1. Freeze the machine-readable Phase 1 action, surface, and parameter contract.
   **Complete 2026-10-22:** the contract, 48/16/24 input manifest, and protected
   test identity lock are frozen; see [the running record](phase1-running.md).
2. Qualify the material-box corners and the initial-surface generator.
   **Complete 2026-10-23:** all six surfaces and all five Chrono corner/center
   cases pass. The original Newton screen failed and remains preserved; the
   prospectively frozen common-base v2 repair passes preparation and all five
   numerical/gross-interaction pairings with inference-safe fixed timing.
3. Fix the Newton latent export and publish field-semantic diagnostics.
   **Complete 2026-10-24:** coupled-state and active-contact schema-v2 export
   is integrated and tested. V2 exposed a required-velocity enforcement gap
   and remains audit-rejected. Corrected v3 passes three fresh repeats with
   occupancy/mass, action-aligned velocity, contact, stress, and elastic
   evidence. Stress and elastic are admitted to H2; implausible plastic state
   is excluded. Predictive value remains to be tested by H2 versus H1.
4. Generate and validate the 12-episode engineering smoke set.
   **Complete 2026-10-25:** all 12 frozen episodes are admitted, including all
   four validation episodes; every aggregate check passes, protected test
   targets remain unopened, and the reproduced summary permits full-dataset
   generation.
5. Freeze the 88-episode manifest and whole-episode splits.
   **Complete 2026-10-22:** this was frozen prospectively with step 1, before
   any Phase 1 target generation. It remains immutable after the smoke pass.
6. Generate accepted Chrono/Newton pairs without changing the domain or gates.
   **Complete 2026-10-28:** all five preparations and all 64 train/validation
   Chrono/Newton/tensor pairs are admitted; the aggregate passes every check
   and permitted training while recording that test targets were still closed.
7. Implement B3, H0, H1, and H2 from one shared U-Net code path.
   **Architecture/trainer/lift preflight complete 2026-10-26:** all four
   variants share an exact 289,172-parameter architecture, validation-only
   uncertainty calibration and strict artifact locks are implemented, the
   deterministic particle lift passes synthetic and real-state audits, and 19
   focused tests pass. All four variants subsequently completed the three
   declared training seeds with identical capacity.
8. Finish the locked evaluator.
   **Implementation preflight complete 2026-10-26:** selection-before-unlock
   planning, protected target generation and admission, selected-model
   inference, B0--B3/H0--H2 comparisons, parameter controls, particle lift,
   matched sensitivity, calibrated uncertainty, whole-episode bootstrap
   aggregation, explicit failure cases, artifact revalidation, and final
   reporting are implemented. Twelve evaluator tests pass. The plan was frozen
   only after validation-only model selection, followed by explicit unlock and
   open-once markers.
9. Train the three declared seeds, select on validation, and freeze all choices.
   **Complete 2026-10-28:** 12 fits completed; per-variant checkpoint selection
   and nominal-90% uncertainty calibration used only the 16 validation episodes.
10. Open the test set once and publish the complete baseline, ablation,
    sensitivity, uncertainty, and integrity report.
   **Failed at admission 2026-10-30:** the test set opened once after selection;
   all 24 Chrono targets, five preparations, and 24 Newton responses completed.
   The aggregate admits 23/24 episodes and records `failed_or_incomplete`
   because episode 009 alone exceeds the frozen guide horizontal-speed
   tolerance. The fail-closed chain refused prediction, so sensitivity and
   final reporting remain absent and Phase 1 cannot claim any predictive gate.
   **Recovery frozen 2026-10-30:** after explicit authorization, evaluation v2
   froze 24 entirely new protected inputs, component-specific guide tolerances,
   unchanged v1-selected model identities, reserved surface 3102, and exactly
   two Newton workers. All pre-unlock identity and target-absence checks pass;
   no v2 target was open at freeze.
   **Recovery execution failed 2026-10-31:** the explicit unlock/open completed against
   the unchanged selection identity; all 24 Chrono targets and all five prior
   preparations pass. The original dual-worker queue produced 23 response
   manifests; episode 012 failed on a non-finite plastic Jacobian. Its
   user-authorized retry succeeded alone after the other 23 were skipped, so
   all 24 numerical contracts now pass but the response set mixes dual and
   serial execution in violation of the frozen v2 identity. Aggregate admission
   was initially withheld.
   **Conditional evaluation complete 2026-10-31:** after explicit authorization
   to continue while retaining v3 as a prospective branch, the machine
   admission passed 24/24 and all seven admission checks. The frozen evaluator
   and test hashes remained unchanged; a separate JSON-scalar compatibility
   wrapper resumed aggregation after the original evaluator encountered a
   NumPy-Boolean serialization error. All 24 predictions, particle audits,
   sensitivity diagnostics, and the final integrity report completed. The
   report passes 33/49 checks and fails 16, records
   `phase1_exit_demonstrated=false`, and selects H1 only as the less-bad neural
   variant because H2 is worse. V2 is closed as an informative failed,
   provenance-qualified evaluation. Any v3 work is a prospective model/
   protocol branch, not a prerequisite for recording or moving beyond v2.
   **Successor evaluation complete but failed 2026-11-07:** the new 24-test
   plus six-sensitivity contract completed under the preserved serial-member
   execution qualification and artifact-only admission correction. All five
   selected models pass sensitivity direction, but every model fails at least
   one required predictive gate. Report `c5995e...c3f9` therefore records
   `no_positive_successor_claim`; qualification `9205c2...1570` binds the
   recovery provenance and records `phase1_goal_achieved=false`. This
   successor branch is closed. Further work requires a new prospective branch.
   **Direct-v4 completed and passed 2026-11-10:** the no-refit D1 candidate,
   fresh 24-test lock, six-case sensitivity lock, thresholds, and confirmation
   protocol froze before authoritative validation. Validation passed 20/20;
   the protected runtime and admission passed 30/30; the reporting continuation
   froze before prediction/report. The final report passes all 25 hypothesis
   checks, final qualification records `qualified_passed_result`, and the
   independent completion audit revalidates all prediction artifacts and
   qualifier checks. This supports only the bounded learned one-action direct
   surrogate claim, not Newton+neural added value.
11. Mark Phase 1 complete only if every required gate above passes.
    **Complete 2026-11-10:** direct-v4 report `a73067...a2e8`, qualification
    `eece4d...544c`, and completion audit `d65358...436cd` all pass and record
    `phase1_goal_achieved=true`.

## Kept for Phase 2

Phase 1 deliberately stops after a single bounded action. Phase 2 owns:

- the prospective world-model objective: autoregressive multi-action
  prediction from an already deformed bed for footprint-sequence cost
  evaluation;
- definition and validation of the smallest restart state that supports those
  rollouts, preferring observable and robotics-facing quantities;
- dynamically consistent velocity or momentum and contact state when required;
- stress, deformation, plastic state, or a learned constitutive/contact update
  only after ablation evidence and an explicit claim/expertise review;
- a residual inserted inside the MPM rollout when the one-step evidence shows
  that Newton remains useful;
- a sparse 3D U-Net, particle GNN, or particle-grid neural simulator if the
  Phase 1 evidence justifies its cost;
- varying foot radius or shape, tangential motion, rotation, impact, and gait
  dynamics;
- the 61 N and broader load domain, extrapolation, and automatic OOD handling;
- real-sand system identification and sim-to-real validation.

Phase 2 is not a commitment to build a learned terramechanics model. It should
begin from the successful one-step representation and add only the state needed
for measured rollout closure. If it cannot do so inside the disciplinary
boundary above, its scientific claim and required collaboration must be reset.

Gaussian deformation, novel-view rendering, and planner evaluation also remain
downstream integration work. They may consume frozen Phase 1 predictions, but
they are not substitutes for the Phase 1 state-prediction exit. Their exact
phase assignment should be frozen in the next roadmap after this model passes.

## Historical v1/v2 claim boundary

Had every frozen v1/v2 gate passed, the allowed statement would have been:

> Within the frozen 35 mm, 30.65625--45.984375 N, single-static-action domain,
> a parameter-conditioned neural residual over a frozen Newton MPM prior
> predicts held-out Chrono bed geometry at loaded and post-unload checkpoints
> across unseen positions, initial surfaces, loads, and in-range synthetic
> simulator-control combinations, outperforming raw physics and direct neural
> baselines.

It still does not establish real-soil fidelity, recovered material properties,
full latent-state truth, sequential rollout accuracy, arbitrary geometry,
dynamic locomotion, Gaussian-scene accuracy, or planner benefit.

Those gates did not all pass, so the quoted v1/v2 claim is not supported.

A successor should target a narrower statement: within a predeclared,
engineering-plausible simulator domain, the selected predictor estimates
observable bed geometry for held-out robot contacts. The terms "realistic,"
"soil property," and "terramechanical" require separate evidence and may not
be inferred from predictive success on synthetic targets.

## Required deliverables

- a versioned Phase 1 machine contract and frozen episode manifest;
- accepted train/validation/test summaries with hashes;
- latent-export qualification report;
- shared direct/hybrid U-Net implementation and tests;
- frozen model cards with parameter counts, inputs, normalization, and hashes;
- one locked evaluation report containing every required baseline, ablation,
  parameter sweep, uncertainty result, failure case, and claim decision;
- a final update to this file marking each exit gate pass or fail.

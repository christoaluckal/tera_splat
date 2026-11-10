# Newton handoff

Status: Phase 1 complete; direct-v4 D1 passed 25/25 protected gates

The completed Phase 1 result, claim boundary, and Phase 2 handoff are in the
[Fresh-session handoff in `phase1.md`](phase1.md#fresh-session-handoff) and the
[dated completion report](phase1-completion-20261110.md).
The append-only runtime evidence is in
[`phase1-running.md`](phase1-running.md). The latest dated entry records the
closed successor result, direct-v4 freeze/validation/unlock, model performance,
protected runtime/admission, reporting, qualification, and completion audit.

The original 64-point neural training is complete: 48 episodes were used for
training and 16 for validation. Chrono generation is now complete for all 30
direct-v4 members: 24 fresh locked tests plus six protected sensitivity cases.
They are not additional training data and must never enter fitting,
normalization, calibration, or selection.

The completed protected successor comparison used equal-capacity three-level
U-Nets:

| Model | Inputs | Median RMSE across loaded/post regions, mm | Scientific result |
| --- | --- | --- | --- |
| D0 | initial surface, action geometry, force, and `Kphi`; no Newton | 1.825 / 1.856 / 1.825 / 1.855 | strongest, but failed one failure-tail and twice-radius parameter-control gates |
| R0 | D0 inputs plus raw Newton surfaces | 3.161 / 2.859 / 3.595 / 3.369 | no Newton added value |
| R1 | R0 plus occupancy, mass, vertical velocity, contact count, and normal impulse | 3.309 / 2.964 / 3.815 / 3.395 | no Newton added value |
| R2S | R1 plus mean/von Mises stress | 3.304 / 2.949 / 3.869 / 3.406 | no stress-field value |
| R2E | R1 plus elastic Jacobian/isochoric shear | 3.574 / 2.988 / 4.045 / 3.492 | no elastic-field value |

The four values are loaded footprint, loaded twice-radius, post-unload
footprint, and post-unload twice-radius. All five models passed 24/24 protected
sensitivity-direction comparisons, but all failed at least one mandatory gate.
The result shows that the tested Newton-conditioned neural integration is worse
than D0; it does not prove whether the primary cause is the Newton prior or the
fusion/training design.

The successful direct-v4 candidate is D1, a deterministic, no-refit
reference-differenced `Kphi`-sensitivity wrapper around selected
`D0_seed_20261102`. It consumes no Newton field and cannot establish a
Newton+neural added-value claim. Confirmation plan
`a6d3dcc5872f5b0398bc51cf7ef800e8c66a577d2eeec08d731345bed80d4428`
was frozen before authoritative validation. Validation summary
`ed23f62cea6137daea91ea8a259b9edd947f4bd202294a9e9d511b6702d27a22`
passes all 20 checks on the original 16 validation episodes and uses zero v1
test episodes. D1 validation median RMSE is 2.266 / 2.035 / 2.266 / 2.033 mm,
with 69.8% / 59.0% / 56.5% / 51.3% median reduction from raw Newton.

On the fresh protected set, D1 median RMSE is 1.827 / 1.933 / 1.827 / 1.933
mm for loaded footprint, loaded twice-radius, post-unload footprint, and
post-unload twice-radius. Median reductions from raw Newton are 78.29% /
64.31% / 67.97% / 55.19%; the corresponding episode improvement fractions
against both raw Newton and no deformation are 100% / 100% / 95.83% / 100%.
All four failure-tail and coverage gates pass, both constant and shuffled
`Kphi` controls pass, and all 24 eligible protected sensitivity comparisons
have the correct direction.

All six fresh surfaces 5101--5106 qualified before joint unlock. Protected
execution plan
`7385bba039c90a3a172c122bce270702c44c2bd0655030742687ec0c0cc363ab`
requires exactly two workers. All 30 Chrono manifests are complete and
accepted.

The first bed-stage invocation failed closed before producing any downstream
artifact because the protected plan recorded `tera_splat` revision
`e80203483879dcbae3bbac274ebf25314d97427b`, while the subsequently committed
documentation/direct-v4 sources moved `HEAD` to
`20cb535cbefb719bcb392cc06f24fc290d1ff955`. Runtime comparison reported only
`repository_revisions` as changed; the sibling `tera_splat_sim` revision and
all non-revision protected-plan identities remained unchanged. The separate
prospective revision-only continuation plan is now frozen at SHA-256
`0b37fb917c0ee95135b4971c348ee41ae07b19fd486f93fcaaf341b9318c5d54`.
It binds every completed Chrono file, records all 30 episodes accepted, proves
that `repository_revisions` is the sole changed execution key, records
downstream absence at freeze, preserves exactly two workers, and prohibits
prediction. Five focused recovery tests and three protected-runtime regression
tests pass.

All six deterministic metric beds, all six Newton preparations, and all 30
Newton responses are complete. Every response is finite and
`acceptance_eligible=true`; the response-level `accepted=false` value remains
the frozen pre-admission diagnostic convention rather than a rejection. The
two-worker supervisor exited successfully, and no direct-v4 simulator,
terrain, or Newton-response worker is currently running.

The protected analyzer admitted all 30 episodes: 24 fresh tests
and six protected sensitivity cases. The protected dataset summary is
`passed`, permits prediction, and has SHA-256
`32d4768e87d1ece6d7b7c4f46bf2c362e6a9698906ef4cf9e400ae3c46ab7e06`.
It binds all 30 Chrono manifests, Newton manifests, model-input archives,
target archives, tensor manifests, and episode summaries. The outcome-neutral
final-qualification plan was frozen before admission/prediction/report at
SHA-256
`687131c6e1f3367d5b549c0d808ce9b3cea72d7ce4ea86ccadec10efa76ff259`.
The reporting-only continuation then froze before prediction/report at
`9dd7f3728e8279af4566624018f5e7d099ef3d54e63094225dad2cc7fbdd3856`.

Locked prediction
`9403c434a20d254b924378a361e7cf7fda0aec415f723580350e75105dda3a62`
and final report
`a73067698b08de907915f2db877a2667f7ec862eee0c29a2cc3a2192bb80a2e8`
are complete. The report passes all 25 checks with no failure, records
`phase1_goal_achieved=true`, and permits only the
`learned_one_action_direct_surrogate` claim. Final qualification
`eece4dc223903bbfa177cda22eea597a3497ecb1b9d59bd7d956a5904728544c`
and completion audit
`d6535856a73edc1bf29c51cfd2b63f32e8855e244498fdf1f988a376e5f436cd`
both pass. Phase 1 is complete. The next scientific gate is a new prospective
Phase 2 sequential/world-model contract; no Phase 1 protected target may be
reused as unbiased confirmation.

Newton dominated the completed protected-runtime wall time. Each response
repeated about 10,400 implicit-MPM steps over roughly 304,865 particles,
including an 8,000-step pre-settle. Historical measurement was about 43
minutes serial per response; two workers sharing the RTX 5090 completed a pair
in about 64.7 minutes, only 1.325x aggregate throughput. Settled-state reuse or
a different worker count remains a future-branch optimization and was not
introduced into this frozen run.

All 64 successor train/validation
Chrono, Newton, and tensor pairs are complete. The immutable v1 bulk summary,
SHA-256 `f80c9f018758438ecac0300cfc35c51e828af08a3268ba5fc791a2501f748955`,
fails only because training member 019 has horizontal guide speed
`1.3220210438912167e-6` m/s against the legacy unified `1e-6` tolerance.
It remains preserved as failed. A separately frozen, artifact-only recovery
uses the independently prospective component contract of `5e-6` m/s for
horizontal speed and `1e-6` for the other guide components. Its plan and
passing summary have SHA-256 values
`aedca2736bbe8fbf5b2543d9d41d470c5243834acfb7945201eccd821bb85ab6`
and `dfacb7ed29b61c061dff01314e3035530db7a89d81617e4c117db7e90acc1d81`.
No simulator was rerun, all 384 artifacts remained hash-identical, and
protected targets remained absent at that train/validation gate.

The training plan and train-only normalization are frozen at SHA-256
`2b3b71023c908b1c2c953e558edf4e1dae28c7af775b7f091f16aff5190a0426`
and `969a3378dab6de540eed912a30c613ead129a43e7e6d8d0df49712c2f04269d6`.
All 15 D0/R0/R1/R2S/R2E fits completed. Validation-only selection chose seeds
D0/R2E `20261102`, R0 `20261101`, and R1/R2S `20261103`; selection-summary
SHA-256 is
`3a2ffef309fc36a6018698182dec626f187e8b94894c41e0f76c5cbe46fbe08e`.
The evaluation plan was then frozen at SHA-256
`5b9f1062bcc54c55696addb54b3f5c0fea953335281ee08d0c5dfe3ddd9cc02c`
with exactly 24 test and six protected-sensitivity members. The explicit joint
unlock and sole open-once marker followed. All 30 Chrono targets, five bed
preparations, and 29 original two-worker Newton responses completed. Member
`p1s_test_joint-combination_019` failed twice under dual-process execution on a
non-finite plastic Jacobian. Both failures remain preserved. Prospectively
frozen serial recovery plan
`4da69d0c61f9e3bf65083febd2c45432806ea56ed17d25a2b207d7b96cb7bd9f`
then supplied the missing response. Recovery summary
`d18ad7f01780628d13ba7822de8649450a0e00dbc726e8beb799bfa678cf23d8`
passes but permanently qualifies member 019 as a serial retry rather than a
clean two-worker result.

The original protected analyzer next failed all 24 test rows solely because it
reused the pre-unlock smoke sentinel `no_test_target`; all numerical and
interaction checks passed, and all six sensitivity rows admitted. Failed
summary SHA-256
`b47c316faa8635ae348c155d30105ac4a2d9dceb7c1b3d7a25e1ba38dbd2a086`
and all original per-episode JSONs remain archived. Artifact-only admission
recovery plan
`e5576d39a4ab46365ccc18a902f784570f2490e5dfbbc1189ff40b5c3cb40693`
changed no Chrono, Newton, model-input, or target array. It passed with summary
SHA-256
`785694d82628973a446dfe11dbfac617d5a459abb4f51b4ebef7cc520b25307b`;
the recovered 30/30 protected summary has SHA-256
`fb9f71ea3af06f6acea13bbe33762b9bfb9481ae3fa02eea733563f9c427facc`.

Locked prediction completed at SHA-256
`b825bd2cbf2c7bfcbec020fd776a1895b8b7a7c3fa1c522bb1bc6c88986a2dc3`.
All D0/R0/R1/R2S/R2E sensitivity directions pass 24/24. The final report,
SHA-256
`c5995e619d602a092aa784ef54ba697d4482b5712c9913a87c8b7c011e49c3f9`,
is nevertheless `failed`: all five models fail one or more required predictive
gates, no correction model passes, no Newton added value is demonstrated, and
no supported claim is permitted. Qualification record SHA-256
`9205c2ee0bb9eefeb08d5e9cf758046ac3c071891bda6f260b8efebbb55b1570`
binds that report to the serial retry, artifact-only correction, and archived
failure. That successor evaluation closed without completing Phase 1.
Direct-v4 was the separately frozen prospective continuation and later passed;
it does not retroactively change the v1 outcome or reuse the revealed v1 test
as confirmation.

[Phase 0](phase0.md) remains the immutable authority for the completed Phase 0
campaign and its artifacts. This filename is retained so older reports and
external notes still reach the completed handoff without creating a competing
operational ledger.

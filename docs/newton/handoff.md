# Newton handoff

Status: direct-v4 protected confirmation active; successor v1 closed failed

The live handoff, current gate, claim boundary, and guarded continuation order
are the [Fresh-session handoff in `phase1.md`](phase1.md#fresh-session-handoff).
The append-only runtime evidence is in
[`phase1-running.md`](phase1-running.md). The latest dated entry records the
closed successor result, direct-v4 freeze/validation/unlock, model performance,
and the live protected runtime.

The original 64-point neural training is complete: 48 episodes were used for
training and 16 for validation. The 30 direct-v4 members now being generated
are 24 fresh locked tests plus six protected sensitivity cases. They are not
additional training data and must never enter fitting, normalization,
calibration, or selection.

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

The active direct-v4 candidate is D1, a deterministic, no-refit
reference-differenced `Kphi`-sensitivity wrapper around selected
`D0_seed_20261102`. It consumes no Newton field and cannot establish a
Newton+neural added-value claim. Confirmation plan
`a6d3dcc5872f5b0398bc51cf7ef800e8c66a577d2eeec08d731345bed80d4428`
was frozen before authoritative validation. Validation summary
`ed23f62cea6137daea91ea8a259b9edd947f4bd202294a9e9d511b6702d27a22`
passes all 20 checks on the original 16 validation episodes and uses zero v1
test episodes. D1 validation median RMSE is 2.266 / 2.035 / 2.266 / 2.033 mm,
with 69.8% / 59.0% / 56.5% / 51.3% median reduction from raw Newton.

All six fresh surfaces 5101--5106 qualified before joint unlock. Protected
execution plan
`7385bba039c90a3a172c122bce270702c44c2bd0655030742687ec0c0cc363ab`
requires exactly two workers. At 20:19 EST on 2026-11-07, the original
supervisor is healthy with 14/30 Chrono manifests complete; members 014 and 015
are active. Do not launch a duplicate supervisor or change the execution
identity. The continuation order is: finish Chrono 30/30, run six bed
preparations, run 30 Newton responses, analyze/admit all 30, run locked D1
prediction, then generate the 25-gate report.

Newton will likely dominate the remaining wall time. Each response repeats
about 10,400 implicit-MPM steps over roughly 304,865 particles, including an
8,000-step pre-settle. Historical measurement is about 43 minutes serial per
response; two workers sharing the RTX 5090 complete a pair in about 64.7
minutes, only 1.325x aggregate throughput. Settled-state reuse or a different
worker count would require a new prospective execution qualification and must
not be introduced into this frozen run.

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
failure. This successor evaluation is closed, but Phase 1 is not complete.
Direct-v4 is the separately frozen prospective continuation of that failed
result; it does not retroactively change the v1 outcome or reuse the revealed
v1 test as confirmation.

[Phase 0](phase0.md) remains the immutable authority for the completed Phase 0
campaign and its artifacts. This filename is retained so older reports and
external notes still reach the active handoff without creating a competing
operational ledger.

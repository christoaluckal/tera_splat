# Phase 1 completion record: parameter-conditioned one-action prediction

Date: 2026-11-10

Status: frozen completion report; not a source of live next steps

The operational authority remains [phase1.md](phase1.md). This report records
the protected direct-v4 result, final qualification, completion audit, and
claim boundary that close the Phase 1 exit.

## Outcome

Phase 1 is complete. The prospectively frozen direct-v4 candidate `D1` passed
all 25 protected hypothesis checks on 24 fresh test episodes plus six fresh
protected sensitivity episodes. The outcome-neutral final qualifier and a
separate completion audit both record `phase1_goal_achieved=true`.

`D1` is a deterministic, no-refit wrapper around the validation-selected
three-level direct U-Net `D0_seed_20261102`:

```text
initial + ((D0(Kphi) + (D0(Kphi) - D0(train_mean_Kphi))) - initial)
```

It uses the initial surface, action geometry, force, and `Kphi`. It consumes no
Newton response or Newton mechanics field. The supported result is therefore a
parameter-conditioned learned one-action direct surrogate in the frozen
synthetic domain, not a Newton+neural added-value result.

## Leakage-safe ordering

The completed sequence was:

1. fit the original model ladder on 48 training episodes and select/calibrate
   using only 16 validation episodes;
2. freeze the D1 candidate, 24 fresh test identities, six fresh sensitivity
   identities, thresholds, and confirmation protocol before authoritative
   validation;
3. pass all 20 validation checks without using any earlier protected test;
4. qualify six fresh surfaces, then execute the joint unlock/open once;
5. complete and admit 30/30 Chrono/Newton/tensor episode bundles;
6. freeze the outcome-neutral final qualifier before admission, prediction,
   or reporting;
7. freeze the reporting-only revision continuation after admission but before
   prediction or reporting;
8. run locked D1 prediction, the unchanged 25-gate report, final
   qualification, and the independent completion audit.

The 24 test and six sensitivity targets were never used for fitting,
normalization, calibration, model selection, or candidate revision.

## Protected D1 performance

Values are medians across the 24 fresh test episodes.

| Region/checkpoint | RMSE, mm | Reduction vs raw Newton | Episode fraction better than raw Newton and no deformation | Nominal-90% coverage |
| --- | ---: | ---: | ---: | ---: |
| loaded footprint | 1.827 | 78.29% | 100.00% | 90.36% |
| loaded twice-radius | 1.933 | 64.31% | 100.00% | 91.89% |
| post-unload footprint | 1.827 | 67.97% | 95.83% | 89.98% |
| post-unload twice-radius | 1.933 | 55.19% | 100.00% | 92.00% |

No test episode exceeded the frozen raw-Newton regression tolerance in any of
the four checkpoint/region combinations. All absolute-accuracy, raw-reduction,
episode-fraction, failure-tail, and uncertainty-coverage gates pass.

The parameter controls also pass. Replacing the episode `Kphi` with the fixed
training-mean reference increases paired mean footprint RMSE by 2.44% at both
checkpoints, with bootstrap lower bounds above zero. Shuffling `Kphi` increases
it by 5.69%, again with lower bounds above zero. D1 matches all 24 eligible
protected sensitivity directions.

## Model-type conclusion

The earlier protected successor comparison used a different protected set and
remains immutable:

| Model | Type | Loaded footprint / 2r, mm | Post footprint / 2r, mm | Result |
| --- | --- | ---: | ---: | --- |
| D0 | direct U-Net; no Newton input | 1.825 / 1.856 | 1.825 / 1.855 | strongest earlier model, but failed one tail gate and twice-radius parameter controls |
| R0 | raw-Newton residual U-Net | 3.161 / 2.859 | 3.595 / 3.369 | no Newton added value |
| R1 | Newton mechanics-field residual U-Net | 3.309 / 2.964 | 3.815 / 3.395 | no Newton added value |
| R2S | R1 plus stress | 3.304 / 2.949 | 3.869 / 3.406 | no stress-field value |
| R2E | R1 plus elastic fields | 3.574 / 2.988 | 4.045 / 3.492 | no elastic-field value |

All five earlier models passed sensitivity direction but failed at least one
mandatory gate. The result does not demonstrate Newton-added value and does
not identify conclusively whether the Newton prior or the tested fusion/training
design is the main cause. Direct-v4 establishes the direct-surrogate route
only; its fresh protected set must not be used to revise or rank new models.

## Frozen evidence

| Artifact | SHA-256 |
| --- | --- |
| D1 confirmation plan | `a6d3dcc5872f5b0398bc51cf7ef800e8c66a577d2eeec08d731345bed80d4428` |
| authoritative validation | `ed23f62cea6137daea91ea8a259b9edd947f4bd202294a9e9d511b6702d27a22` |
| protected execution plan | `7385bba039c90a3a172c122bce270702c44c2bd0655030742687ec0c0cc363ab` |
| target-open marker | `4ff1265799d430ef00900a0a03e8d3e0d4c72aa769455e2fbe2f54fd9cf2be57` |
| revision-only runtime continuation | `0b37fb917c0ee95135b4971c348ee41ae07b19fd486f93fcaaf341b9318c5d54` |
| frozen reporting plan | `b89417e6d7e7a3942ceb131446841a20555e88d88191076d8ef9dfb682abf60f` |
| protected dataset summary | `32d4768e87d1ece6d7b7c4f46bf2c362e6a9698906ef4cf9e400ae3c46ab7e06` |
| final-qualification plan | `687131c6e1f3367d5b549c0d808ce9b3cea72d7ce4ea86ccadec10efa76ff259` |
| reporting-only continuation | `9dd7f3728e8279af4566624018f5e7d099ef3d54e63094225dad2cc7fbdd3856` |
| protected prediction | `9403c434a20d254b924378a361e7cf7fda0aec415f723580350e75105dda3a62` |
| 25-gate final report | `a73067698b08de907915f2db877a2667f7ec862eee0c29a2cc3a2192bb80a2e8` |
| final qualification | `eece4dc223903bbfa177cda22eea597a3497ecb1b9d59bd7d956a5904728544c` |
| completion audit | `d6535856a73edc1bf29c51cfd2b63f32e8855e244498fdf1f988a376e5f436cd` |

The completion audit revalidated every prediction archive and summary,
recomputed all qualifier checks, verified both prospective plans preceded the
outcome, and passed every completion check.

## Verification

- the reporting continuation, final qualifier, completion auditor, and their
  tests pass Python bytecode compilation;
- 28 applicable focused direct-v4 tests pass across planning, validation,
  surface qualification, unlock identity, protected runtime, revision
  recovery, reporting, final qualification, and completion audit;
- one historical unlock test intentionally asserts that protected targets are
  absent before unlock. It correctly refuses the completed post-unlock
  filesystem and is not a rerunnable final-state test; its source and original
  pre-unlock evidence remain unchanged;
- the final-state runtime/recovery/reporter/reporting/qualification/audit subset
  passes 21/21 tests;
- `git diff --check` passes, and the completion auditor is idempotent against
  the frozen final artifacts.

## Claim boundary

Supported:

- within the frozen synthetic one-action domain, D1 predicts loaded and
  post-unload surface state while using action load and `Kphi`;
- D1 passes the prospectively frozen accuracy, failure-tail, parameter-use,
  sensitivity, uncertainty, and integrity gates;
- a learned direct surrogate is the successful Phase 1 representation.

Not supported:

- Newton+neural added value or usefulness of stress/elastic channels;
- sequential rollout or world-model closure;
- planner benefit, constitutive validation, named-soil calibration, real-soil
  parameter identification, or sim-to-real transfer;
- extrapolation outside the frozen action and parameter domain.

Sequential action-conditioned prediction belongs to Phase 2 and requires a new
prospective contract and protected evidence. The completed Phase 1 protected
sets are diagnosis-only for any future model design and may not be reused as
unbiased confirmation.

# Newton running analysis

Last updated: 2026-10-19  
Status: chronological decision ledger; the active operational source is
[handoff.md](handoff.md)

This file records how the Newton conclusion changed over time. It is an index
to evidence, not a replacement for detailed dated reports or machine-readable
artifacts.

## Timeline

### 2026-09-03 — Preparation contract

- Established explicit preparation gates and retained full particle state.
- Confirmed that particle spacing, particle volume, grid resolution, and
  timestep cannot be changed independently.
- Evidence: [preparation diagnostic](../../diagnostics/newton_preparation_20260903/README.md).

### 2026-09-06 — Coupling and fine-step failures

- PIC preparation replaced the rejected fine-step APIC top-layer mode.
- The explicit guide exposed timestep-dependent gravity lag and analytic
  cylinder penetration.
- Native proxy coupling removed the dominant guide drift but did not yet
  qualify the full response matrix.
- Evidence:
  [coupling](../../diagnostics/newton_convergence_coupling_20260906/README.md),
  [failure resolution](../../diagnostics/newton_failure_resolution_20260906/README.md),
  [response](../../diagnostics/newton_response_convergence_20260906/README.md),
  and [native proxy](../../diagnostics/newton_response_convergence_native_proxy_20260906/README.md).

### 2026-09-08 — Collider-support diagnostic

- A raised proxy passed the numerical response matrix at the smoke material.
- It was not promoted because the geometry omitted part of the analytic
  cylinder and later admitted deep particle penetration at lower stiffness.
- Evidence: [collider support](../../diagnostics/newton_collider_support_20260908/README.md).

### 2026-09-10 — Contact activation remained diagnostic

- The private full-volume activation path restored coverage and passed
  individual mechanics gates.
- The complete timestep matrix still failed the coarse adjacent sinkage gate.
- Decision: private contact changes remain diagnostic; calibration stayed
  stopped.
- Evidence:
  [contact activation](../../diagnostics/newton_contact_activation_20260910/README.md)
  and [calibration diagnostic](../../diagnostics/newton_calibration_20260910/README.md).

### 2026-09-14 — Public fixed domain qualified

- Public stock contact at 7.8125 mm with PIC/PIC, P0/S2/Q1 and 8/16 coupling
  passed the 0.5/0.25/0.125 ms response matrix.
- Decision: select 0.25 ms for a separate local material study.
- Evidence: [public contact](../../diagnostics/newton_public_contact_20260914/README.md)
  and [fixed-domain contract](fixed-domain.md).

### 2026-09-21 — Local A0 material study

- Nineteen of 21 candidates passed mechanics gates.
- The selected point improved the A0 objective from 12.698 to 8.823 mm and
  replayed at 8.815 mm.
- Decision: claim repeatable local objective improvement only.

### 2026-09-22 — Three-kilogram transfer boundary

- The unchanged control remained mechanics-valid.
- The selected A0 material failed strict center penetration.
- Decision: the fitted material point is not an admissible high-load model.
- Evidence: [3 kg holdout](../../diagnostics/newton_mass3kg_holdout_20260922/README.md).

### 2026-09-30 — Mass boundary refined

- Incumbent failures at 1.75 and 2.0 kg showed that the high-load boundary was
  not isolated to 3 kg.
- Evidence:
  [1.75 kg](../../diagnostics/newton_mass1p75kg_holdout_20260930/README.md)
  and [2 kg](../../diagnostics/newton_mass2kg_holdout_20260930/README.md).

### 2026-10-01 — Admissible spatial transfer

- A4-A6 established mechanics-valid 1.625 kg transfers.
- A5 and A6 produced different scalar rankings between incumbent and control.
- Decision: action-level map error and spatial characteristics must be reported
  separately.
- Evidence:
  [A5](a5-spatial-transfer-20261002.md),
  [A6](a6-spatial-transfer-20261002.md), and
  [1.625 kg diagnostics](../../diagnostics/newton_mass1p625kg_holdout_20261001/README.md).

### 2026-10-02 — Multi-characteristic audit

- Peak depression, displaced volume, footprint, and centroid were added to the
  interpretation.
- The A0 incumbent remained the best archived A0 point, but valid transfers
  retained large peak and volume error.
- Decision: scalar surface RMSE is not a sufficient forward-model objective.
- Evidence:
  [calibration protocol](calibration-protocol-20261002.md),
  [calibration result](calibration-result-20261002.md), and
  [transfer audit](transfer-audit-20261002.md).

### 2026-10-03 — Radius boundary

- The incumbent failed strict mechanics at 55 and 65 mm cylinder radii.
- Decision: geometry belongs to the mechanics-valid domain contract; the
  canonical-radius material cannot be transferred to smaller feet by default.
- Evidence:
  [A7](a7-geometry-boundary-20261003.md) and
  [radius boundary](radius-boundary-20261003.md).

### 2026-10-04 — A9 and A10 mixed fidelity

- A9 showed accurate centroid location with a 14.730 mm peak error and
  178.812 cm3 volume error.
- Prospective A10 remained mechanics-valid and scalar-improving but had a
  10.624 mm peak error and 171.121 cm3 volume error.
- Decision: valid Newton is a bounded prior, not a characteristic-faithful
  terrain predictor.
- Evidence:
  [A9](a9-validation-20261004.md),
  [A10](a10-protocol-and-result-20261004.md), and
  [historical ledger](historical-evidence-20261004.md).

### 2026-10-06 — Model direction changed

- The accumulated evidence favored a mechanics-gated physics prior followed by
  learned discrepancy and uncertainty.
- Decision: perform a bounded stop/go test before ending broad parameter-only
  search.
- Evidence: [forward-model direction](../forward-model-direction-20261006.md).

### 2026-10-08 — Stop/go completed

- Two additional prior-A0 candidates passed A10 mechanics gates but did not
  improve the incumbent's held-out multi-characteristic score.
- Decision: stop broad parameter-only refinement of the current Newton model
  form.
- Retain Newton as the first offline physics prior because its numerical
  contract and particle-state export are already qualified.
- The new 35 mm proxy-foot action requires a fresh geometry/load qualification;
  the historical incumbent is not transferable evidence.
- Evidence:
  [consolidated experiment report](experiment-consolidated-20261008.md),
  [current handoff](handoff.md), and
  [hybrid model design](../hybrid-chrono-mpm-residual-gaussian-planning-20261008.md).

### 2026-10-09 — Static 35 mm sentinel rejected the inherited domain

- Question: can the unchanged public Newton domain serve as a mechanics-valid
  prior for the lowest static Go1 foot load?
- Frozen contract: 35 mm radius, center position, 30.656 N static load,
  7.8125 mm PIC/PIC P0/S2/Q1 Newton, 0.25 ms, stock contact, and 8/16 coupling.
- New evidence: Chrono accepted at 0.349 s. Newton passed preparation, finite,
  guide, support, and final loaded penetration checks, but eight particle
  centers transiently penetrated by at most 3.759 micrometers.
- Decision: mark the initial 35 mm domain not qualified and stop expansion of
  the 15-case position/load matrix.
- Claim boundary: one static, lowest-load, center-position sentinel; no claim
  about other actions, dynamic loads, calibrated response, or planning.
- Canonical artifacts:
  [static proxy report](static-proxy-qualification-20261009.md) and
  `outputs/validity_experiment/newton/static_proxy_35mm_20261009/`.

### 2026-10-16 — Strict failure retained; bounded residual pilot restarted

- Question: can the micrometer-scale strict failure be carried as numerical
  uncertainty so the project tests a residual network before more solver
  tuning?
- Frozen contract: unchanged 35 mm proxy, 100 kPa baseline, public stock
  contact, 7.8125 mm grid, PIC/PIC P0/S2/Q1, 0.25 ms, and 8/16 coupling.
- New evidence: the 31 N timestep matrix fails strict zero penetration at all
  levels and is not response-converged. At 0.25 ms, the centered 31 N and 46 N
  actions have only 3.759/4.871 micrometer maximum overlap, affect at most
  0.00260/0.01171% of particles, end with zero overlap, and retain finite,
  guided, full-support states. Their loaded/residual Chrono RMSE is
  0.835/0.683 mm and 1.719/1.411 mm.
- Decision: keep strict mechanics status failed. Freeze bounded policy v2 at
  10 micrometers and 0.02% affected particles after the two centered
  calibration actions. Permit prospective data generation but not residual
  training until every retained action passes v2. Do not relax v2 again;
  shrink the load/position domain on a later failure.
- Boundary result: centered 61 N stays within the depth/fraction limits but
  retains 38 centers inside at the loaded observation. Reject that load,
  preserve it as out-of-domain evidence, and reissue a 10-action split over
  31/46 N before inspecting any spatial Newton result.
- Claim boundary: engineering admission for an offline coarse-prior residual
  pilot only; no timestep convergence, strict mechanics, material, Gaussian,
  or planning claim.
- Canonical artifacts:
  [bounded admission report](coarse-prior-admission-20261016.md),
  `configs/static_proxy_35mm_qualification.json`, and
  `outputs/validity_experiment/newton/static_proxy_35mm_20261009/`.
- Verification checkpoint: the reissued contract has exactly 10 actions with
  a complete 6/2/2 whole-position split. The live summary is
  `coarse_prior_incomplete` at 2/10 Chrono and 2/10 Newton cases; both attempted
  coarse screens pass, H0 is exactly equal, and residual training remains
  locked. Focused tests pass 10/10, the Newton/bridge split passes 37/37, and
  the general model-form split passes 9/9.

### 2026-10-17 — Prior outputs quarantined; fresh hierarchical campaign issued

- Question: can Phase 0 prioritize geometric usefulness without relying on
  potentially shaky artifacts from the earlier execution routine?
- Frozen contract: no prior episode, particle bed, preparation, or response is
  admissible. The replacement has 15 static actions, a 9/3/3 whole-position
  split, fresh output roots, and a mandatory sequential exact-repeat stage.
- New evidence: code inspection found no explicit randomness in the Chrono
  cylinder path, but the old manifests lack sufficient source/input hashes,
  thread policy, and exact-repeat qualification. Newton records versions and
  device but also lacks a campaign-level exact duplicate gate.
- Decision: do not infer determinism from code shape. Start current evidence at
  zero, generate a fresh particle bed from fresh Chrono H0, and stop before
  matrix expansion if either backend fails exact same-build repetition.
- Gate hierarchy: provenance/repeatability and numerical integrity are hard;
  contact overlap is an artifact classification unless gross; footprint and
  twice-radius skill are the primary physics-utility gates; held-out residual,
  Gaussian, and planner gates follow.
- Claim boundary: no current Phase 0 physics or residual result yet.
- Canonical artifacts:
  [fresh hierarchical protocol](fresh-hierarchical-phase0-20261017.md) and
  `configs/static_proxy_hierarchical_v3_20261017.json`.

### 2026-10-17 — Exact-repeat stop gate removed before execution

- Question: does requiring bitwise identity over-constrain Phase 0 before the
  residual pipeline has been tested?
- Frozen contract: the fresh-only evidence boundary, 35 mm static foot,
  15-action matrix, whole-position 9/3/3 split, and local geometry metrics are
  unchanged.
- New evidence: no fresh Chrono or Newton case had completed under the earlier
  exact-repeat wording; only a campaign plan and an empty log existed. The
  Phase 0 objective explicitly treats run-to-run variation and small overlap
  as measured uncertainty rather than automatic rejection.
- Decision: retain a two-run same-build sentinel, but report acceptance-time,
  surface, and particle-state differences instead of requiring equality.
  Bitwise identity is diagnostic. Block only incomplete, unaccepted,
  non-finite, environment-incompatible, or structurally incompatible runs.
  Matrix expansion may proceed without exact equality.
- Claim boundary: the sentinel characterizes one build/device/action; it does
  not establish deterministic portability or validate the residual.
- Canonical artifacts:
  [fresh hierarchical protocol](fresh-hierarchical-phase0-20261017.md),
  `configs/static_proxy_hierarchical_v3_20261017.json`, and
  `scripts/run_fresh_phase0_repeatability.py`.

### 2026-10-17 — Fresh sentinel characterizes variation and clears expansion

- Question: is the current fresh Chrono-to-Newton path numerically usable and
  locally informative enough to begin multi-action data generation?
- Frozen contract: centered 30.656 N static action, 35 mm radius, Chrono at
  1 ms, H0-derived 5 mm particle bed, stock Newton contact at 0.25 ms,
  PIC/PIC P0/S2/Q1, 8/16 coupling, unchanged 100 kPa material baseline, and
  two fully independent sequential paths.
- New evidence: both Chrono runs accept at 0.349 s and all Chrono maps/metric
  beds match. Newton arrays are compatible but not identical. Loaded repeat
  RMSE is 0.0083 mm in the footprint and 0.0050 mm within 2r. Residual
  footprint repeat RMSE is 0.0090 mm. One cell at `(35, 10) mm` differs by
  10.552 mm, producing 0.426 mm raw residual 2r RMSE; it is the only cell above
  0.1 mm, 2r p95 is 0.0117 mm, and residual particle-position RMSE/max are
  0.00059/0.0404 mm. Both responses are finite, guided, full-support, and have
  eight transient inside centers below 3.92 micrometers with none inside at the
  loaded state. Footprint MSE skill is about 0.889 loaded/0.959 residual; 2r
  skill is 0.723-0.724 loaded/0.816-0.824 residual.
- Decision: classify the repeats as usable with a microscopic contact artifact
  and a one-cell residual rasterization outlier. Preserve raw and robust
  variation views. Permit matrix expansion; do not add the duplicate sentinel
  twice to training and do not unlock residual training yet.
- Claim boundary: one centered low-load static action shows same-build pipeline
  usability and positive coarse-prior signal. It does not establish held-out
  generalization, a learned residual, strict mechanics, or Gaussian/planner
  benefit.
- Canonical artifacts:
  `outputs/validity_experiment/newton/static_proxy_hierarchical_v3_20261017/repeatability/repeatability_summary.json`
  and the paired Chrono/Newton subdirectories beside it.

### 2026-10-17 — Canonical matrix begins with a five-position spatial rung

- Question: what is the smallest fresh matrix slice that can exercise a
  whole-action residual split without making all 15 expensive cases a
  prerequisite?
- Frozen contract: the full 15-action 9/3/3 split is unchanged. Execution is
  progressive: first all five 30.656 N positions (3 train / 1 validation /
  1 test), then the corresponding 45.984 N and 61.313 N slices.
- New evidence: canonical training case `center_f031n` completed from a third
  fresh Chrono episode and fresh H0-derived bed. It is finite, guided,
  full-support, and usable with 8/307,461 transient inside centers to 3.779
  micrometers and zero inside at loaded time. Loaded footprint/2r RMSE is
  5.113/4.041 mm with skill 0.889/0.724; residual is 3.085/3.227 mm with skill
  0.960/0.824. All four local skill checks pass.
- Decision: count the matrix at 1/15 and the spatial rung at 1/5. Complete the
  other two training positions and both whole-position holdouts before fitting
  even the smallest residual. Do not require the higher-load rungs first.
- Claim boundary: one canonical training action confirms the fresh matrix path
  and coarse-prior signal only. Residual training and held-out improvement are
  not yet demonstrated.
- Canonical artifacts:
  `outputs/validity_experiment/newton/static_proxy_hierarchical_v3_20261017/matrix/matrix_summary.json`,
  its `cases/center_f031n/case_summary.json`, and
  `scripts/run_fresh_phase0_matrix.py`.

### 2026-10-18 — Second spatial training action preserves coarse-prior signal

- Question: does the fresh coarse Newton prior remain useful when the same
  30.656 N foot action moves 100 mm off center, without imposing strict
  mechanics qualification as a prerequisite for learning?
- Frozen contract: third independent canonical action path, +100 mm x center,
  35 mm radius, fresh Chrono GT and H0-derived metric bed, unchanged 100 kPa
  Newton baseline, local footprint/2r metrics, and the predeclared training
  split.
- New evidence: `xplus100_f031n` is accepted, finite, guided, full-support,
  and pipeline-usable. Ten of 307,461 centers enter transiently by at most
  7.575 micrometers and none remain inside at the loaded observation. Loaded
  footprint/2r RMSE is 6.237/4.660 mm with MSE skill 0.833/0.629 against no
  deformation. Physical post-unload RMSE is 5.971/4.388 mm with skill
  0.847/0.671. The post-unload map also contains a 38.945 mm maximum error;
  this tail remains reported and is not obscured by whole-bed averaging.
- Decision: count the matrix at 2/15 and the spatial rung at 2/5. Treat strict
  mechanics failure and microscopic overlap as metadata, not a veto. Continue
  to the third training action, then generate both whole-position holdouts
  before fitting the residual.
- Claim boundary: two training positions demonstrate useful coarse signal,
  not learned correction or held-out generalization. `residual` in the current
  artifact names means the physical post-unload observation, not a neural
  residual prediction.
- Canonical artifacts:
  `outputs/validity_experiment/newton/static_proxy_hierarchical_v3_20261017/matrix/cases/xplus100_f031n/case_summary.json`
  and the encompassing `matrix/matrix_summary.json`.

### 2026-10-18 — Training slice complete; minimal residual fixed before holdouts

- Question: do all three declared training positions carry useful coarse
  signal, and what is the smallest residual that can test whole-position
  generalization without making uninformative latent arrays a prerequisite?
- Frozen contract: same 30.656 N/35 mm action and fresh per-action path; center
  and ±100 mm x are the only training actions. Validation +y and test -y remain
  ungenerated and unavailable to fitting or model selection.
- New evidence: `xminus100_f031n` is accepted, finite, guided, full-support,
  and usable. Ten of 307,461 centers enter transiently by at most 7.574
  micrometers, with none inside at the loaded observation. Loaded footprint/2r
  RMSE is 6.308/4.676 mm with skill 0.828/0.625; physical post-unload RMSE is
  6.020/4.402 mm with skill 0.843/0.668. Its post-unload maximum is 39.023 mm.
  Across all nine saved states for the three training actions, stress and
  velocity gradient are all zero, strain/transform are identity, and plastic
  Jacobian is one.
- Decision: count the matrix at 3/15 and the spatial rung at 3/5. Freeze a
  dependency-light, action-aligned, one-hidden-layer MLP before holdout
  generation. It predicts a bounded vertical field from observable geometry,
  Newton response, force, and phase, then lifts it onto particles with a depth
  taper. Fit only on the three x-axis actions; never refit after seeing +y/-y.
  The resulting 3,678-sample fit is frozen at model SHA-256
  `242fa879c1d7eda443f4277d82a41dcfea5828cdb7b66ccae357b633d99a15af`
  and learner SHA-256
  `0df18d2fa433359da5cb32f8223cb7abce74f83b7ffd47368c9fdd1d13e58878`.
  Its particle-lift training RMSE is 1.446-1.838 mm in-foot and
  1.034-1.173 mm within 2r; this is a fit check only.
- Claim boundary: the training slice demonstrates coarse prior signal but no
  held-out residual improvement. The zero/identity latent tensors diagnose an
  uninformative export path, not a lack of value in physical latent state.
- Canonical artifacts:
  `outputs/validity_experiment/newton/static_proxy_hierarchical_v3_20261017/matrix/cases/xminus100_f031n/case_summary.json`,
  `outputs/validity_experiment/newton/static_proxy_hierarchical_v3_20261017/matrix/residual_pilot_v1/training_summary.json`,
  `scripts/run_phase0_residual_pilot.py`, and
  `tests/test_phase0_residual_pilot.py`.

### 2026-10-18 — Frozen particle residual improves untouched +y validation

- Question: does the pre-holdout residual improve a whole unseen action after
  correction is lifted from the learned field onto Newton particles?
- Frozen contract: `yplus100_f031n` is validation only; model SHA-256
  `242fa879c1d7eda443f4277d82a41dcfea5828cdb7b66ccae357b633d99a15af`
  and learner SHA-256 `0df18d2f...8878` were fixed while its case summary was
  absent. No fit, selection, or hyperparameter change is permitted afterward.
- New evidence: the fresh +y case is accepted, finite, guided, full-support,
  and usable, with 10/307,461 transient inside centers to 7.719 micrometers and
  none at the loaded observation. Raw loaded footprint/2r RMSE is
  5.784/3.971 mm; particle-corrected RMSE is 2.077/2.211 mm. Raw physical
  post-unload RMSE is 5.665/3.820 mm; corrected is 2.267/2.335 mm. Corrected
  skill versus no deformation is 0.982/0.929 loaded and 0.979/0.921
  post-unload. All 307,461 corrected positions are retained, and field and
  reprojected-particle surfaces agree to stored precision.
- Decision: validation passes all four local improvement checks. Preserve the
  frozen model unchanged and run the independent -y test; do not promote the
  validation result alone to a completed Phase 0 residual claim.
- Claim boundary: one untouched position demonstrates promising spatial
  transfer at one load. The test action and load-generalization rungs remain.
- Canonical artifacts:
  `outputs/validity_experiment/newton/static_proxy_hierarchical_v3_20261017/matrix/cases/yplus100_f031n/case_summary.json` and
  `outputs/validity_experiment/newton/static_proxy_hierarchical_v3_20261017/matrix/residual_pilot_v1/cases/yplus100_f031n/evaluation_summary.json`.

### 2026-10-18 — Independent -y test confirms single-load spatial residual

- Question: does the frozen residual retain its validation improvement on the
  separately held-out test position, with corrected particles preserved for a
  later Gaussian update?
- Frozen contract: `yminus100_f031n` is test only. The same pre-holdout model
  and learner hashes must match; no refit or selection follows validation.
- New evidence: all five 31 N actions are fresh, complete, pipeline-usable,
  and locally better than no deformation. The test has 10/307,461 transient
  inside centers to 7.862 micrometers and none at the loaded observation. Raw
  loaded footprint/2r RMSE is 5.706/3.936 mm and corrected is
  2.158/2.252 mm. Raw post-unload RMSE is 5.601/3.791 mm and corrected is
  2.359/2.382 mm. Corrected skill is 0.981/0.927 loaded and 0.977/0.919
  post-unload. Both validation and test pass all four local improvement checks.
  Corrected held-out states retain 307,461 finite particles, preserve x/y and
  velocity exactly, and reproject to the learned field at stored precision.
  Post-holdout training refuses by construction, and 50 relevant tests pass.
- Decision: mark the 31 N spatial residual exit demonstrated. Preserve v1 and
  its outputs as immutable evidence. Advance to fresh load expansion with a
  separately versioned model rather than modifying or refitting v1.
- Claim boundary: this demonstrates spatial generalization at one load. It
  does not yet demonstrate load generalization, Gaussian/NVS improvement, or
  planner benefit, so the full Phase 0 objective remains active.
- Canonical artifacts:
  `outputs/validity_experiment/newton/static_proxy_hierarchical_v3_20261017/matrix/matrix_summary.json`,
  `outputs/validity_experiment/newton/static_proxy_hierarchical_v3_20261017/matrix/residual_pilot_v1/evaluation_summary.json`, and
  its `cases/yminus100_f031n/` corrected particle/state artifacts.

### 2026-10-18 — Multi-load v2 contract fixed before 46 N evidence

- Question: how can load coverage be added without altering the successful v1
  evidence or tuning on future holdouts?
- Frozen contract: v2 uses the same one-hidden-layer architecture, optimizer,
  seed, 50 mm bound, 2r support, and particle lift as v1. The only intended
  learning change is six center/±x training actions spanning 31 N and 46 N.
- New evidence: the separate v2 wrapper and three focused contract tests exist
  and pass before `center_f046n` completes. Its training stage refuses to run
  after either 46 N y-holdout or any 61 N case summary exists. It owns a
  distinct model id/output root and hashes both its source and the immutable
  v1 base source.
- Decision: generate the three fresh 46 N training actions, then fit/freeze v2
  before generating 46 N +y validation or -y test. Preserve v1 unchanged.
- Claim boundary: this is a prospective model contract, not multi-load result.
- Canonical artifacts: `scripts/run_phase0_multiload_residual_pilot.py` and
  `tests/test_phase0_multiload_residual_pilot.py`.

### 2026-10-18 — Coarse prior remains useful at centered 46 N

- Question: does the unchanged Newton prior retain useful geometry signal at a
  second load before multi-load residual fitting?
- Frozen contract: centered 45.984 N/35 mm action, fresh Chrono/bed/Newton
  path, unchanged 100 kPa material prior, and the already fixed v2 contract.
- New evidence: `center_f046n` is accepted, finite, guided, full-support, and
  usable. Thirty-six of 307,461 centers enter transiently by at most 4.662
  micrometers, with none inside at observation. Loaded footprint/2r RMSE is
  13.340/8.226 mm with skill 0.608/0.419; physical post-unload RMSE is
  10.160/6.666 mm with skill 0.773/0.618. All four local coarse-prior checks
  remain positive despite the larger model discrepancy.
- Decision: count the matrix at 6/15 and the 46 N rung at 1/5. Continue the two
  off-center 46 N training actions without retuning Newton or v2.
- Claim boundary: this is useful second-load coarse signal, not a fitted or
  held-out multi-load residual result. The 61 N rung remains future robustness
  evidence and is not required before attempting the two-load test.
- Canonical artifacts:
  `outputs/validity_experiment/newton/static_proxy_hierarchical_v3_20261017/matrix/cases/center_f046n/case_summary.json`.

### 2026-10-19 — Second 46 N training position remains usable

- Question: does the unmodified coarse Newton prior retain local geometric
  utility at a second position of the higher retained load?
- Frozen contract: +100 mm x, 45.984 N, 35 mm static proxy, fresh
  Chrono-to-bed-to-Newton path, unchanged 100 kPa prior, and v2 fixed before
  any 46 N result.
- New evidence: `xplus100_f046n` is complete, accepted, finite, guided, and
  full-support. It has 31 transient inside centers to 9.837 micrometers and
  seven at the loaded observation; this remains inside the gross-artifact
  limits but is not strict mechanics qualification. Loaded footprint/2r RMSE
  is 13.912/8.659 mm with skill 0.580/0.370; physical post-unload is
  10.275/6.337 mm with skill 0.771/0.663. All four local prior-utility checks
  pass.
- Decision: count the matrix at 7/15 and the 46 N rung at 2/5. Run only the
  remaining -x training case, then fit/freeze v2 before generating either
  46 N y holdout.
- Claim boundary: two higher-load training positions demonstrate useful coarse
  signal only. They do not establish multi-load learned correction, held-out
  transfer, Gaussian update, or planner value.
- Canonical artifacts:
  `outputs/validity_experiment/newton/static_proxy_hierarchical_v3_20261017/matrix/cases/xplus100_f046n/case_summary.json` and
  [handoff.md](handoff.md).

## Required format for future entries

Append entries in ascending date order:

    ## YYYY-MM-DD — Short decision title

    - Question:
    - Frozen contract:
    - New evidence:
    - Decision:
    - Claim boundary:
    - Canonical artifacts:

When an entry changes the current contract, conclusion, or next permitted work,
update [handoff.md](handoff.md) in the same change.

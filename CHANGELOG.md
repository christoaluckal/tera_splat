# Changelog

This file records material changes relative to named Git commits. Generated
simulation outputs and external environments are listed for reproducibility but
are not part of the Git diff unless explicitly stated.

## Unreleased — changes since `0f30de26bdd151f822a2e691924b15e98e20b09d`

### Newton 3 kg held-out action timing diagnosis — 2026-09-22

- Generated the frozen guided 3 kg A1 Chrono episode. Its initial heightmap
  exactly matches A0 on the 14,161 valid cells; Chrono accepted loading at
  `2.417 s`.
- The no-retuning incumbent response passed preparation but failed strict
  zero-center penetration (31 centers; `1.326 um` maximum). It is diagnostic
  only: the local Newton runner still used A0's `3.595 s` loading default while
  comparing to A1's `2.417 s` loaded map.
- Paused the matching 100 kPa control and any transfer claim. The runner must
  propagate and validate per-episode loaded time before the action can be
  requalified and scored. Compact evidence:
  `diagnostics/newton_mass3kg_holdout_20260922/`.

### Time-aligned 3 kg held-out action result — 2026-09-28

- Changed the local Newton runners to derive loaded/residual observation time
  from the supplied Chrono manifest, pass and record it explicitly, and reject
  any mismatch. This changes I/O orchestration only, not Newton physics.
- The corrected 3 kg A1 comparison uses `2.417 s` loaded and `0.25 s` residual
  in both backends. The 100 kPa baseline passes all mechanics gates and scores
  `16.289 mm`; the 1.5 kg-selected incumbent fails strict zero-center
  penetration (31 centers; `1.332 um` maximum) and has no valid score.
- The fixed domain supports the 3 kg action, but that selected material point
  is not an admissible higher-load forward-model candidate. This is bounded
  transfer evidence, not calibration or NVS/decision validation.

### Newton fixed-domain material-study expansion — 2026-09-21

- Expanded the local, validity-gated study to 21 Newton candidate evaluations
  in the fixed public `7.8125 mm`, `0.25 ms`, stock-contact `8/16` domain.
  Nineteen are mechanics-valid observations; two candidates at `mu≈0.273`
  failed strict zero particle-center penetration and remain excluded.
- The broad-continuation incumbent is `E=70.46 kPa`, `nu=0.237231507`, and
  `mu=0.305497980`, objective `8.823 mm` versus the `12.698 mm` baseline.
  Its fresh independent replay scored `8.815 mm`, a `0.008 mm` difference.
- This records repeatable local objective improvement only. It does not claim
  optimizer convergence, calibrated material inference, held-out action
  transfer, real-sand validation, or NVS/decision use.

### Newton fixed-domain BayesOpt initialization — 2026-09-15

- Added `scripts/run_newton_bayesopt.py`, an isolated local study driver. Each
  Newton-native material candidate receives a fresh full-bed preflight and a
  separate fresh in-process preparation/loading/removal response; no Newton
  state or Genesis observation is reused.
- A baseline smoke and a four-candidate sequential study complete with five
  valid observations in the fixed `7.8125 mm`, `0.25 ms`, stock-contact `8/16`
  domain. At that initialization milestone, the best point was `E=116.7 kPa`,
  `nu=0.1955`, `mu=0.4409`, objective `11.610 mm`, versus the `12.698 mm`
  baseline.
- This was local BayesOpt initialization, not an optimizer-converged material
  calibration. The subsequent expansion and independent replay are recorded
  above; NVS/decision-use validation remains separate.

### Newton public contact and spatial resolution — 2026-09-14

- Reclassified private S2 activation overrides as diagnostic-only; no internal
  Newton contact computation is a forward-model candidate.
- Stock contact at public `4/8` proxy/substep coupling passes its `0.5/0.25 ms`
  mechanics and response pair (`0.053/0.053 mm` map RMSE; `0.192 mm` sinkage),
  but has a 10--11 mm analytic contact-location bias.
- Added the public `7.8125 mm` voxel configuration and qualified its fresh
  preparation/tolerance matrix. It reduces stock-contact bias to 2.2--3.5 mm,
  but its response pair fails sinkage convergence (`1.339 mm`).
- Public `8/16` coupling at the refined grid now passes the complete
  `0.5/0.25/0.125 ms` response matrix. Every case passes preparation, guide,
  finite/full-support, and zero-center-penetration gates. Adjacent response
  RMSE is `0.035/0.058 mm`, maxima are `0.218/0.310 mm`, and sinkage
  differences are `0.331/0.422 mm`.
- This qualifies a fixed, stock-contact Newton numerical domain for a separate
  sim-only BayesOpt study; it does not calibrate the 100 kPa smoke material or
  validate transfer outside that domain. Compact interpretation:
  `diagnostics/newton_public_contact_20260914/`.

### Newton full-volume contact activation — 2026-09-11

- Added a process-local, cylinder-only, Newton-1.5.1-locked S2 rasterizer
  adapter.  It changes collider-node activation from the native `+0.25` to
  `-0.25` voxel without changing analytic cylinder geometry, action pose,
  inertia, strict center-penetration test, external I/O, or gates.
- Rejected a full-volume `-0.95`-voxel screen: the cylinder fell `116.5 mm`,
  reached `13.423 mm` center penetration, and failed the guide gate.
- Completed the full-volume `-0.25`-voxel `0.5/0.25/0.125 ms` matrix at
  100 kPa.  Every row passes preparation, finite/full-support I/O, guide, and
  zero-center-penetration gates; both adjacent response-map comparisons pass.
- The matrix remains `not_demonstrated`: coarse/medium sinkage is `0.975 mm`,
  above the unchanged `0.5 mm` limit, although medium/fine sinkage is
  `0.480 mm` and passes.  Material calibration and large evaluation remain
  stopped; no gate was relaxed.
- Retained compact evidence in
  `diagnostics/newton_contact_activation_20260910/`; raw states, PLYs, maps,
  and traces remain under `outputs/`.

### Newton support correction and calibration stop — 2026-09-10

- Added an explicit cylinder collision-bottom inset while preserving analytic
  action geometry, inertia, pose reporting, DEM scoring, and penetration checks.
- Rejected global Q1 and particle-PIC collider-basis substitutions on
  preparation speed/H0 evidence.
- Tightened Kamino PADMM tolerance from `1e-5` to `1e-6`, matching the
  existing guide gate, and recorded it in solver provenance.
- Completed a strict `0.5/0.25/0.125 ms` matrix at a 9.375 mm inset and
  100 kPa. All mechanics and response gates pass; adjacent loaded/residual DEM
  RMSE is `0.130/0.123` and `0.107/0.110 mm`, with sinkage differences
  `0.130/0.032 mm`.
- Recomputed the shared A/B: corrected Newton scores `12.189 mm`, improved
  from `12.638 mm`, versus matched Genesis `14.736 mm`; the calibrated
  Genesis incumbent remains best at `8.705 mm`.
- Ran a stiffness-only 25 kPa Newton calibration probe. Its preparation matrix
  passes and its DEM-only score improves to `11.207 mm`, but the response is
  rejected: up to 1,330 particle centers enter the analytic cylinder by
  `5.950 mm`, and the guide gate fails.
- Stopped material calibration. The raised proxy is a support-location
  diagnostic, not a promotable collision model, because it omits analytic
  collision coverage once the cylinder sinks.
- Retained lightweight evidence in
  `diagnostics/newton_collider_support_20260908/` and
  `diagnostics/newton_calibration_20260910/`; raw outputs remain under
  `outputs/`.

### Newton/Genesis backend A/B — 2026-09-08

- Ran Genesis at the nominal Newton 100 kPa smoke material with the frozen
  `0.5 ms` action and recomputed both backends through one shared scorer.
- Newton scores `12.638 mm` versus matched Genesis `14.736 mm`; Genesis is
  about 16% faster in this single matched execution.
- The calibrated Genesis incumbent remains the best absolute fit at
  `8.705 mm`, so the A/B favors Newton's numerical foundation rather than
  proving better prediction.
- The reverse Genesis-incumbent-to-Newton transfer was rejected before contact:
  Newton preparation reached the speed gate but failed H0 at
  `9.809/10.241 mm` RMSE/max.
- Retained lightweight configurations, shared metrics, plots, and analysis in
  `diagnostics/backend_ab_20260906/`; raw states remain under `outputs/`.
Baseline commit: `0f30de2` — `fixing bayesopt` — 2026-08-20 15:01:39 -04:00.
### Newton native guided coupling — 2026-09-06

- Replaced the diagnostic runner's external explicit guide update with an
  optional native Newton path: a Kamino rigid cylinder, world-to-body
  prismatic joint, and `SolverCoupledProxy` connection to implicit MPM. The
  historical explicit path remains selectable as a control.
- Added a `1e-6` gate for forbidden horizontal/rotational guide motion and
  required that gate in response analysis. All 18 focused Newton tests pass.
- Ran the unchanged full `0.5/0.25/0.125 ms` response matrix with two lagged
  proxy iterations and four Kamino substeps. All cases pass preparation,
  finite/full-support I/O, zero-center penetration, and guide constraints.
- Removed the dominant `g*T*dt` drift: endpoint vertical speed is now below
  `0.010 mm/s`, and both loaded/residual DEM pairs pass at `0.082--0.089 mm`
  RMSE and at most `0.745 mm` maximum error.
- Full response convergence remains `not_demonstrated`: sinkage differences
  are `0.464/0.586819 mm`, so the fine pair misses the frozen `0.5 mm` gate by
  `0.086819 mm`. The corrected equilibrium also exposes a `9.8--10.8 mm`
  analytic surface gap. Diagnose native coupling/contact support next; do not
  loosen gates or start calibration.
- Retained compact evidence in
  `diagnostics/newton_response_convergence_native_proxy_20260906/`; large raw
  outputs remain under repository-root `outputs/`.


### Newton response convergence diagnosis — 2026-09-06

- Added a predeclared response-matrix analyzer and focused tests; all 17 Newton
  tests pass.
- Ran clean full continuous-state responses from commit `73eb472` at `0.5`,
  `0.25`, and `0.125 ms`. Every case is finite, has all `14,161` valid cells,
  passes preparation, and has zero analytic particle-center penetration.
- Response convergence is not demonstrated. Loaded sinkage changes from
  `8.854` to `-0.578` to `-5.607 mm`. The coarse pair also exceeds loaded and
  residual map gates; the fine pair passes both map gates but misses the
  `0.5 mm` sinkage gate by an order of magnitude.
- Diagnosed the dominant error as the explicit guide's pre-impulse position
  update: steady endpoint speed is approximately `-g*dt`, accumulating a
  first-order displacement near `g*T*dt`. The next controlled change is a
  timestep-consistent guide update, not material calibration.
- Retained compact evidence in
  `diagnostics/newton_response_convergence_20260906/`; raw states and PLYs
  remain under repository-root `outputs/`.

### Newton failure resolution and qualified mechanics — 2026-09-06

- Localized the fine-step APIC failure to an upward top-layer mode and promoted
  PIC transfer after a complete `0.5/0.25/0.125 ms` plus tolerance matrix
  passed all speed, H0, and pairwise DEM gates.
- Explained the `0.508 mm` cylinder penetration as the 32-facet mesh inset plus
  Newton's default `0.01 voxel` projection allowance.
- Added a 128-segment circumscribed collider, zero cylinder projection
  threshold, forward-consistent guide update, and recorded `10 um` guard. The
  unchanged analytic zero-center gate passes throughout the full response.
- Completed a mechanics-qualified, uncalibrated fixed-time run with full
  `14,161`-cell support, `8.854 mm` sinkage, zero penetration, and raw Chrono
  RMSE of `2.396 mm` loaded / `2.646 mm` residual.
- Retained the compact evidence in
  `diagnostics/newton_failure_resolution_20260906/`. Response timestep
  convergence is the next gate before calibration or larger evaluation.

### Newton convergence and coupling diagnosis — 2026-09-06

- Added a reproducible preparation-matrix analyzer and ran `0.5`, `0.25`, and
  `0.125 ms` timesteps plus a `1e-5` tolerance check. Adjacent initial DEMs
  agree within `0.054 mm` RMSE, but the `0.125 ms` state fails the sustained
  speed gate at 4 s, so preparation convergence is not demonstrated.
- Added a continuous-state, vertically guided two-way cylinder diagnostic with
  exact Chrono action/timing, collider impulse feedback, removal, penetration
  checks, raw particle arrays, PLYs, DEMs, masks, traces, and provenance.
- Ran the full fixed-time diagnostic. Coupling is finite and supports the
  cylinder weight, but `1,302` particle centers remain inside the loaded
  cylinder at up to `0.508 mm` depth; the strict zero-penetration gate fails.
- Determined that saved Newton particle arrays are archival output rather than
  restart-qualified state: reconstruction adds about `1.157 mm` of bulk
  settlement. Preparation and response now run in one solver instance.
- Retained lightweight evidence in
  `diagnostics/newton_convergence_coupling_20260906/`; large states and PLYs
  remain under repository-root `outputs/`.

### Newton branch integration — 2026-09-03

- Added a strict Newton configuration/contract layer, isolated dependency
  pins, unit tests, and a headless preparation runner that never imports a
  Genesis prepared state.
- Pinned Python 3.11.15, Newton 1.5.1, and Warp 1.17.0 in the external
  `/data/christoa/conda/envs/newton_splat` environment.
- Added backend-labelled initial/final state arrays, PLYs, DEM maps, masks,
  speed traces, metrics, configuration, and provenance manifests under the
  repository-root `outputs/` namespace.
- Accepted a fresh 307,461-particle full-bed preparation at 0.5 ms over 2 s:
  full 14,161-cell support, first speed hold at 1.6165 s, final p99 speed
  0.168 mm/s, and H0 RMSE/max 1.186/1.288 mm.
- Retained the compact result in `diagnostics/newton_preparation_20260903/`.
  Preparation convergence, rigid coupling/removal, response comparison, and
  Newton calibration remain pending.

### Genesis baseline handoff through 2026-09-03

- Qualified and froze Chrono oracle
  `A0_oracle_guided_offset_5mm_gate6mm_v1`, including its guided cylinder,
  fixed loaded/residual observation times, valid mask, and scoring contract.
- Promoted the ratio-matched 307,461-particle, 5 mm/n128 Genesis bed and
  confirmed incumbent `20.432828 kPa / 14.727053 deg / 0.101894536` in exact
  replay `r2at0vvb`: objective `8.704 mm`, loaded RMSE `1.864 mm`, and
  residual-footprint RMSE `13.678 mm`.
- Retained raw replay `ykep3esa` for visualization and state evidence. It is
  not a replacement confirmation because four residual projection cells
  exceeded the frozen three-cell sparse-bin allowance.
- Completed the non-learned Pareto, spatial, recovery, `F`/`Jp`, and 2x2
  resolution/timestep diagnosis. A third n128 `0.125 ms` response was rejected
  before contact because it could not pass the unchanged preparation gate.
- Completed controlled 4 s same-state pre-settle traces at `0.5`, `0.25`, and
  `0.125 ms`. They identify timestep-dependent boundary/free-surface drift,
  preventing a clean constitutive-only diagnosis or another material sweep.
- Added tracked lightweight diagnostics at repository-root `diagnostics/`;
  large beds, states, PLY/PCD sequences, videos, and evaluation runs remain in
  `outputs/`.
- Froze this work as the Genesis baseline before Newton integration.

### Current next work

- Keep Genesis evidence immutable across backend work.
- Retain the native Kamino/prismatic proxy correction and diagnose the
  remaining collider-support/coupling sensitivity. Keep PIC preparation,
  material, action, mask, observation times, and frozen gates unchanged. The
  fine sinkage pair still exceeds its gate by `0.086819 mm`.
- Do not begin Newton calibration or larger evaluation until both adjacent
  response pairs pass without changing the declared gates.
- If Genesis work continues instead, correct or ablate one containment/state-
  preparation mechanism and rerun the frozen three-level checks.

### Runtime and documentation

- Standardized commands and contributor documentation on the `chrono_splat`
  Conda environment instead of `tsplat`.
- Relocated `chrono_splat` to `/data/christoa/conda/envs/chrono_splat` and
  installed the runtime used for validation: Python 3.10, PyTorch 2.13.0+cu130,
  Genesis 1.3.3, W&B, NumPy, SciPy, Viser, and PLY support. The environment is
  external to Git.
- Expanded `docs/current-state.md` with the frozen-state contract, online/offline
  sweep evidence, corrected stress initialization, and the post-removal
  diagnostic plan.

### BayesOpt initialization boundary

- Changed `run_chrono_genesis_bayesopt.py` from rebuilding a candidate-dependent
  bed to requiring one accepted `--prepared-bed`.
- Froze particle spacing and size per study; the active optimization dimensions
  are `log10_E` and `phi_deg`.
- Added prepared-bed episode, acceptance, and particle-geometry validation.
- Persisted `result.json` for non-equilibrium trials instead of returning before
  the diagnostic record was written.
- Added candidate-initialization H0 metrics to W&B and persisted trial results.

### Candidate-consistent constitutive state

- Added `--reinitialize-geostatic-stress-from-state` to
  `run_mass_controlled_terrain.py`.
- Preserved frozen particle positions and active flags while rebuilding velocity,
  `C`, `F`, and `Jp` for each candidate material.
- Recomputed depth-dependent geostatic `F` from the candidate `E`, density, and
  Poisson ratio before contact.
- Added a cylinder-free candidate relaxation stage to
  `run_chrono_genesis_bridge.py`.
- Required candidate preparation to re-pass the original particle-speed and
  Chrono-oracle H0 RMSE/maximum-error gates before cylinder release.
- Persisted each accepted candidate state under
  `bridge/candidate_prepare_raw/mpm_state.npz` and recorded its metrics in the
  bridge manifest.

### Validation evidence

- Generated a fresh accepted 20 mm CPIC reference bed: equilibrium at 0.274 s,
  p99 speed 0.424 mm/s, H0 RMSE 0.615 mm, maximum H0 error 0.654 mm, with all
  14,161 target-valid cells supported.
- Verified the corrected reference candidate (`100 kPa`, `45 deg`) and formerly
  failing high-E candidate (`log10_E=5.636`, `phi=44.415 deg`) both pass H0,
  loaded equilibrium, and post-removal equilibrium.
- Confirmed the high-E negative-depth rebound disappeared after constitutive
  stress reconstruction.
- Completed online W&B run `61sldco9` using the pre-fix constitutive restore; its
  response feasibility interpretation is superseded by the stress fix.
- Completed corrected online W&B run `h2il8dg0`: 12/12 candidate preparations
  and loaded phases passed, while 3/12 post-removal phases reached equilibrium
  within 1 s. Best valid objective was 0.372 mm at `log10_E=4.5`,
  `phi_deg=35`.

### Superseded August 20 follow-up

The items below record the next steps as of August 20. They were completed or
superseded by the current handoff above and are not active instructions.

- Run the documented 1.0/1.5/2.0/3.0 s post-removal diagnostic before another
  calibration sweep.
- Freeze whether the Chrono residual target is defined by observation time or by
  equilibrium.
- Freeze the production post-removal window from the diagnostic evidence.

### Tracked files at the August 20 checkpoint

- `docs/README.md`
- `docs/contributor-guidance.md`
- `docs/current-state.md`
- `scripts/run_chrono_genesis_bayesopt.py`
- `scripts/run_chrono_genesis_bridge.py`
- `scripts/run_mass_controlled_terrain.py`
- `CHANGELOG.md` (new)

### Generated evidence at the August 20 checkpoint

- `outputs/validity_experiment/A0_cal_full10mm_prepared_20mm_cpic_frozen/`
- `outputs/validity_experiment/bayesopt/A0_cal_full10mm_frozen_online/`
- `outputs/validity_experiment/bayesopt/A0_cal_candidate_stress_quick_online/`
- Local W&B run directories under `wandb/`; online runs are linked from
  `docs/current-state.md`.

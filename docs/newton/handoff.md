# Newton handoff

Last updated: 2026-10-19  
Status: active operational handoff

## Current decision

The current Phase 0 campaign starts from zero admissible data. No earlier
Chrono episode, particle bed, Newton preparation, or response may be reused for
qualification, training, validation, or test claims. The earlier material
below is retained only as historical failure-mode context.

The operational source is the
[fresh hierarchical Phase 0 protocol](fresh-hierarchical-phase0-20261017.md).
The first execution is a sequential two-run sentinel, followed by independent
fresh metric-bed generation and two fresh Newton preparation/response runs.
These runs quantify numerical variation. Exact equality is diagnostic rather
than a matrix-expansion gate; incomplete, unaccepted, non-finite,
environment-incompatible, or structurally incompatible output still blocks
use. Residual training remains prohibited until enough fresh whole actions
exist for the frozen split and local geometric-utility evaluation.

Stop broad parameter-only refinement of the current Newton model form. Retain
Newton as a mechanics-gated, bounded MPM physics prior for the proposed
Chrono-supervised residual model.

The completed A10 stop/go set found no prior A0 candidate that improved the
incumbent's held-out multi-characteristic profile. This does not prove that
Newton cannot improve under a different constitutive model, state
representation, or numerical domain. It does show that further global tuning
of the current three-parameter material point is not the highest-value next
step.

Read the [consolidated experiment report](experiment-consolidated-20261008.md)
for the evidence and the
[hybrid design](../hybrid-chrono-mpm-residual-gaussian-planning-20261008.md)
for the next model.

The 35 mm centered timestep matrix is complete. Every row fails strict zero
penetration, with maximum transient overlap between 0.523 and 4.407
micrometers, and the response is not timestep-converged. Strict mechanics
qualification therefore remains failed.

The initial residual pilot now uses a separate frozen bounded coarse-prior
gate. It permits at most 10 micrometers of transient center overlap affecting
at most 0.02% of particles, while still requiring accepted preparation,
finite state, the guide, full support, and zero overlap at the loaded
observation. The centered 30.656 and 45.984 N training actions pass this
bounded gate and fail the strict gate. This distinction must remain visible.
See the [bounded admission report](coarse-prior-admission-20261016.md).

The frozen gate rejects the centered 61.313 N boundary because 38 centers
remain inside at the loaded observation. The pilot is therefore capped at the
two lower loads: 10 actions over five positions. The rejected high-load state
is retained as out-of-domain evidence.

## Qualified Newton contract

| Item | Fixed value |
| --- | --- |
| voxel size | 7.8125 mm |
| transfer / integration | PIC / PIC |
| bases | P0 strain / S2 collider / Q1 velocity |
| contact | public stock Newton contact |
| coupling | 8 proxy iterations / 16 rigid substeps |
| selected timestep | 0.25 ms |
| preparation | fresh full-bed preparation for every evaluation |
| response | continuous preparation, loading, removal, and recovery |
| external support | 14,161-cell Chrono interior mask |
| validity | finite/full-support I/O, timing, guide, and zero center penetration |

The table above remains the strict mechanics contract. For offline residual
data only, policy `bounded_static_prior_v2_20261016` admits microscopic,
trajectory-only overlap within its declared limits. It does not change
Newton's `accepted` or `mechanics_qualified` fields.

Saved Newton particle arrays are archival and interchange outputs. They are not
qualified restart checkpoints.

## Frozen historical material point

The A0 local study selected:

| Parameter | Value |
| --- | ---: |
| Young's modulus | 70.46 kPa |
| Poisson ratio | 0.237231507 |
| friction coefficient | 0.305497980 |
| discovery / replay objective | 8.823 / 8.815 mm |

This is a repeatable local sim-to-sim objective improvement over the unchanged
100 kPa control. It is not real material identification.

The point is mechanically invalid at the tested 1.75, 2.0, and 3.0 kg actions
and at 55 and 65 mm cylinder radii. Valid A9 and A10 responses still miss peak
depression by approximately 10-15 mm and displaced volume by approximately
171-179 cm3. Mechanics validity and a lower map RMSE therefore do not establish
characteristic fidelity.

## New 35 mm proxy-foot boundary

The intended robot proxy has a 35 mm foot radius. That geometry lies outside
the qualified incumbent domain and is more severe than the failed 55 and
65 mm radius tests.

For the 12.5 kg Go1 proxy:

- four equal supports imply 3.125 kg or about 8 kPa per foot;
- two stance feet imply 6.25 kg or about 16 kPa per foot;
- the historical A0 cylinder is approximately 0.88 kPa.

Do not transfer the historical incumbent directly to the proxy foot. The
unchanged 100 kPa control fails strict trajectory-wide penetration but is being
screened as a bounded fixed coarse prior before any material fit. See the
[static proxy report](static-proxy-qualification-20261009.md) and
[bounded admission report](coarse-prior-admission-20261016.md).

## Material-calibration rule for the hybrid model

Newton may tune material parameters to match Chrono response, but only as a
single training-stage calibration:

1. qualify the numerical/contact domain for the proxy geometry;
2. fit one global material setting across multiple training actions;
3. freeze that setting;
4. train the residual correction on the remaining discrepancy;
5. evaluate held-out positions and weights without any material refit.

Per-action parameter tuning would let the material point encode the test action
and would invalidate the intended generalization result.

## State available to the residual

The Newton runner exports:

- particle position and velocity;
- velocity gradient;
- elastic deformation gradient;
- plastic Jacobian;
- Cauchy stress;
- overall deformation transform for rendering.

Chrono does not provide particle correspondence or subsurface state. These
Newton quantities are privileged simulator features, not Chrono labels. The
residual must be supervised through Chrono-observable surfaces, renders, and
rigid-body outcomes.

The fresh 31 N training audit found that the current exporter names all of
these arrays but does not yet provide informative latent values: across all
nine initial/loaded/post-unload states, stress and velocity gradient are
identically zero, elastic strain and deformation transform are identity, and
plastic Jacobian is exactly one. The first residual therefore uses positions,
observable initial alignment, Newton surface response, action-relative
coordinates, force, and phase. Latent-state contribution remains a later
ablation after the export path is made informative; zero/identity placeholders
must not be presented as a negative scientific result about latent features.

## Execution handoff — 2026-10-19

This is the current run ledger.  The two sentinel repeats are qualification
evidence, not duplicate training rows.  All entries below are fresh campaign
artifacts; no quarantined historical result is used as current evidence.

### Completed and preserved

- Same-build sentinel: complete. It characterizes non-bitwise Newton variation
  without blocking the campaign.
- 31 N spatial rung: all five positions are complete. The v1 correction was
  fitted only on center/+x/-x, then improved both untouched +y validation and
  -y test. Its model and outputs are immutable evidence of *single-load*
  spatial transfer.
- 46 N training actions: `center_f046n` and `xplus100_f046n` are complete,
  usable, and pass all four local raw-prior skill checks. The current matrix is
  **7/15 Chrono complete and 7/15 usable Newton**, or 2/5 on the 46 N rung.
  The +x case has loaded footprint/2r RMSE of 13.912/8.659 mm (skill
  0.580/0.370) and physical post-unload RMSE of 10.275/6.337 mm (skill
  0.771/0.663). It has a microscopic contact artifact (31 transient centers,
  9.837 micrometers maximum); seven centers remain inside at the loaded state,
  so it remains strictly mechanics-unqualified but is usable under the frozen
  gross-artifact policy.

### Still to run, in order

1. Generate only the remaining 46 N training action
   `xminus100_f046n`. Do not rerun the completed +x case.
2. With all six center/+x/-x cases at 31 N and 46 N present, fit and freeze
   v2 once. It must happen before either 46 N y holdout exists:

       /data/christoa/conda/envs/newton_splat/bin/python scripts/run_phase0_multiload_residual_pilot.py --stage train

3. Generate fresh untouched 46 N `yplus100_f046n` validation and
   `yminus100_f046n` test cases, then evaluate that unchanged v2 model across
   both cases:

       /data/christoa/conda/envs/newton_splat/bin/python scripts/run_phase0_multiload_residual_pilot.py --stage evaluate --case yplus100_f046n --case yminus100_f046n

4. Audit `multiload_held_out_residual_exit_demonstrated` together with
   corrected-particle preservation and the local footprint/2r comparisons.
   A passing result completes the smallest credible two-load Phase 0
   demonstration. The 61 N rung is a subsequent robustness decision, not a
   hidden prerequisite. Gaussian update and open-loop planner evaluation remain
   later Level-5 work.

Run a matrix case only with:

    /data/christoa/conda/envs/newton_splat/bin/python scripts/run_fresh_phase0_matrix.py --stage all --case <case-id>

## Next permitted work

All three canonical training actions are complete and pass all four local
positive-skill checks. The -x action's loaded footprint/2r skill is
0.828/0.625 and post-unload skill is 0.843/0.668, closely matching +x. The two
off-center post-unload maps retain explicit 38.945/39.023 mm maximum-error
tails despite positive RMSE skill. The training slice was 3/5 when the model
was fit. Fit and freeze
the v1 residual on these three actions before generating validation
`yplus100_f031n` and test `yminus100_f031n`; never refit from their results.
That fit is complete. Model SHA-256 is
`242fa879c1d7eda443f4277d82a41dcfea5828cdb7b66ccae357b633d99a15af`,
and the training command now refuses to run once either holdout summary
exists. Training-only particle-projected RMSE improves to 1.446-1.838 mm in
the footprint and 1.034-1.173 mm within 2r; do not call this held-out evidence.

Untouched validation `yplus100_f031n` subsequently completed as usable. The
frozen particle correction improves loaded footprint/2r RMSE from
5.784/3.971 mm to 2.077/2.211 mm and post-unload from 5.665/3.820 mm to
2.267/2.335 mm. All four local checks beat both raw Newton and no deformation,
with the pre-holdout model/source hashes unchanged. The independent test result
below subsequently completes the rung.

Independent test `yminus100_f031n` is now complete. The unchanged model
improves loaded footprint/2r RMSE from 5.706/3.936 mm to 2.158/2.252 mm and
post-unload from 5.601/3.791 mm to 2.359/2.382 mm. Both validation and test
pass all four local checks, and the joint summary sets
`held_out_residual_exit_demonstrated` true. Post-holdout training is verified
to refuse, 50 relevant tests pass, and corrected held-out states retain all
307,461 finite particles with exact x/y and velocity preservation.

1. Preserve the completed sentinel summary and its raw one-cell residual-map
   outlier; do not replace untrimmed metrics with the robust diagnostic.
2. Preserve the frozen single-load v1 model and begin the fresh 46 N expansion
   rung; do not reinterpret single-load spatial transfer as load
   generalization.
   The separately versioned v2 contract is already fixed and tested; it trains
   on center/±x at 31 N and 46 N, rejects fitting after either 46 N y-holdout
   or any 61 N case exists, and does not modify v1.
   `center_f046n` and `xplus100_f046n` are complete. Complete only
   `xminus100_f046n`, then fit/freeze v2 before either 46 N y-holdout.
3. Compute footprint and 2r error/skill for every action before whole-bed
   summaries, while also reporting max and robust map differences.
4. Stop only for incomplete, unaccepted, non-finite, environment-incompatible,
   or structurally incompatible results. Carry smaller variation and contact
   overlap as measured uncertainty/artifacts.
5. Use the unchanged 100 kPa baseline for the first residual test after the
   3/1/1 whole-position slice is complete; do not delay
   it for another broad material search.
6. Train an offline post-rollout displacement residual and derive deformation
   from the residual gradient.
7. Validate held-out local geometry before Gaussian or planner claims.
8. Transfer only hierarchically admitted corrected states to terrain Gaussians and
   preserve uncertainty/strict-status metadata.
9. Evaluate the fixed open-loop planner against static, heuristic, MPM-only,
   hybrid, and Chrono-oracle baselines.

## Prohibited shortcuts

- Do not tune Newton parameters on validation or test actions.
- Do not copy or reference an old episode, PLY, preparation, response, or map
  as current campaign evidence.
- Do not infer determinism from absence of explicit randomness, and do not
  require bitwise determinism as a substitute for testing geometric utility.
- Do not report a coarse-admissible response as strictly mechanics-qualified.
- Do not admit a response that fails preparation, finite state, guide, support,
  or the fresh campaign's gross-interaction guard. Smaller overlap is reported
  as an artifact/uncertainty rather than silently removed.
- Do not call Newton particle position, stress, or deformation Chrono ground
  truth.
- Do not initialize MPM from an already deformed Chrono surface and replay the
  same action.
- Do not claim sequential terrain-state transfer from a heightfield alone.
- Do not let the neural correction repair a failed coarse-prior gate. The
  declared microscopic transient overlap is input uncertainty, not a learned
  collision repair target.
- Do not use archived particle arrays as restart states.

## Where to resume

- [Newton documentation index](README.md)
- [Running analysis](running-analysis.md)
- [Static 35 mm proxy qualification](static-proxy-qualification-20261009.md)
- [Bounded coarse-prior admission](coarse-prior-admission-20261016.md)
- [Fixed-domain contract](fixed-domain.md)
- [Consolidated experiment report](experiment-consolidated-20261008.md)
- [Cross-backend direction](../forward-model-direction-20261006.md)
- [Hybrid design](../hybrid-chrono-mpm-residual-gaussian-planning-20261008.md)
- [Chrono oracle contract](../chrono-oracle-run-contract.md)
- [Repository current state](../current-state.md)

Use the Newton environment:

    /data/christoa/conda/envs/newton_splat

The primary runners and analyzers remain:

    scripts/run_newton_prepared_bed.py
    scripts/run_newton_cylinder_diagnostic.py
    scripts/analyze_newton_preparation_convergence.py
    scripts/analyze_newton_response_convergence.py
    scripts/analyze_forward_model_transfer_v3.py
    scripts/run_static_proxy_qualification.py

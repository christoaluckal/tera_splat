# Phase 1 goal: parameter-conditioned neural bed-state prediction

Date: 2026-10-22

Status: active Phase 1 goal and exit contract

## Authority

This document is the sole operational definition of Phase 1. It states the
result Phase 1 must deliver, the permitted domain, the model and data contract,
the evidence required for success, and the work deferred to Phase 2.

[Phase 0](phase0.md) remains the authority for the completed proof and its
artifacts. The phase numbering in the older
[hybrid roadmap](../hybrid-chrono-mpm-residual-gaussian-planning-20261008.md)
is historical; where it conflicts with this document, this document wins for
all new work.

## Goal

Given a valid pre-action bed state, one bounded robot-foot action, and declared
action and bed parameters, predict the observable state of the bed at the
loaded and post-unload checkpoints:

\[
(\widehat B_{loaded},\widehat B_{post}) =
\mathcal F_\theta(B_0,a,p;N(B_0,a)).
\]

Here `B0` is the pre-action bed, `a` is the action, `p` is the known
conditioning vector, and `N` is the frozen Newton MPM prior. The primary model
learns a bounded correction to the Newton state. It must make a prediction
without access to the Chrono loaded or post-unload target at inference.

Phase 1 is successful when one frozen neural model predicts whole held-out bed
states across unseen combinations of position, normal force, initial surface,
and at least two explicitly varied soil parameters inside the declared domain.
It must outperform raw Newton, no deformation, the Phase 0 residual, and a
same-capacity direct neural baseline under the locked tests below.

This is intentionally closer to a neural physical model than the Phase 0
241-parameter MLP. The model operates on a structured spatial state, mixes
information across neighboring cells, is conditioned on action and material
parameters, consumes qualified MPM mechanics fields, and predicts an entire
state field. It remains a modest one-step hybrid model, not a general learned
simulator.

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

Newton stress, strain, plastic state, velocity, occupancy, and contact fields
are candidate *inputs* to the residual. Chrono SCM supplies no corresponding
subsurface truth, so Phase 1 does not claim that corrected stress or plastic
state is ground truth. "Bed state" in the Phase 1 claim therefore means the
observable geometry and its audited particle realization, not a complete
constitutive restart state.

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

### Parameter domain

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

Before bulk generation, the four corners and center of this parameter box must
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
position, force, and the two soil parameters inside the bounds above. Each
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

At minimum, qualify occupancy/mass, velocity, contact, and one non-kinematic
family: stress invariants, deformation/strain invariants, or plastic Jacobian.
Unqualified fields remain absent from the model and from all claims.

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
radius, signed foot distance, and every qualified latent invariant. Global
action and soil parameters are normalized and injected by feature-wise affine
conditioning at every U-Net scale, not appended only to the final layer.

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
| H2 | H1 plus qualified mechanics latents | tests stress/strain/plastic value |

H1 is the minimum deliverable. H2 becomes the named final model only if its
held-out evidence is better than or statistically indistinguishable from H1
without a worse failure tail. Shuffle and constant-parameter controls must
show that H1 is actually using `p`, rather than merely accepting unused input
slots.

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

Phase 1 exits only when all gates pass.

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
does not erase an otherwise valid H1 parameter-conditioned result; it triggers
redesign of the latent representation before Phase 2.

## Ordered implementation plan

1. Freeze the machine-readable Phase 1 action, surface, and parameter contract.
2. Qualify the material-box corners and the initial-surface generator.
3. Fix the Newton latent export and publish field-semantic diagnostics.
4. Generate and validate the 12-episode engineering smoke set.
5. Freeze the 88-episode manifest and whole-episode splits.
6. Generate accepted Chrono/Newton pairs without changing the domain or gates.
7. Implement B3, H0, H1, and H2 from one shared U-Net code path.
8. Train the three declared seeds, select on validation, and freeze all choices.
9. Open the test set once and publish the complete baseline, ablation,
   sensitivity, uncertainty, and integrity report.
10. Mark Phase 1 complete only if every required gate above passes.

## Kept for Phase 2

Phase 1 deliberately stops after a single bounded action. Phase 2 owns:

- autoregressive multi-action prediction from an already deformed bed;
- dynamically consistent updates to velocity, stress, deformation gradient,
  plastic state, and other restart variables;
- a residual inserted inside the MPM rollout or a learned constitutive/contact
  update;
- a sparse 3D U-Net, particle GNN, or particle-grid neural simulator if the
  Phase 1 evidence justifies its cost;
- varying foot radius or shape, tangential motion, rotation, impact, and gait
  dynamics;
- the 61 N and broader load domain, extrapolation, and automatic OOD handling;
- real-sand system identification and sim-to-real validation.

Gaussian deformation, novel-view rendering, and planner evaluation also remain
downstream integration work. They may consume frozen Phase 1 predictions, but
they are not substitutes for the Phase 1 state-prediction exit. Their exact
phase assignment should be frozen in the next roadmap after this model passes.

## Supported claim after a successful exit

If every required gate passes, the allowed statement is:

> Within the frozen 35 mm, 30.65625--45.984375 N, single-static-action domain,
> a parameter-conditioned neural residual over a frozen Newton MPM prior
> predicts held-out Chrono bed geometry at loaded and post-unload checkpoints
> across unseen positions, initial surfaces, loads, and in-range synthetic soil
> parameter combinations, outperforming raw physics and direct neural
> baselines.

It still does not establish real-soil fidelity, recovered material properties,
full latent-state truth, sequential rollout accuracy, arbitrary geometry,
dynamic locomotion, Gaussian-scene accuracy, or planner benefit.

## Required deliverables

- a versioned Phase 1 machine contract and frozen episode manifest;
- accepted train/validation/test summaries with hashes;
- latent-export qualification report;
- shared direct/hybrid U-Net implementation and tests;
- frozen model cards with parameter counts, inputs, normalization, and hashes;
- one locked evaluation report containing every required baseline, ablation,
  parameter sweep, uncertainty result, failure case, and claim decision;
- a final update to this file marking each exit gate pass or fail.

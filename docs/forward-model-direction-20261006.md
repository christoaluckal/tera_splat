# Forward-model direction: Chrono, Genesis, Newton, and Gaussian planning

Last updated: 2026-10-07. This is a decision summary; the dated evidence
ledgers remain authoritative.

## Executive summary

The project has established a reproducible sim-to-sim terrain-deformation
benchmark, not a generally validated soil model. Chrono SCM is the synthetic
ground-truth generator. Genesis and Newton are alternative MPM backends whose
preparation, contact, timing, and response behavior must be qualified
separately. Gaussian transfer and planning are downstream hypotheses, not yet
validated results.

The proposed direction is a planning-oriented, initialization-aware hybrid:

```text
Chrono GT + prepared-terrain state
        -> mechanics-gated MPM prior (Newton or Genesis)
        -> learned discrepancy and uncertainty
        -> Gaussian terrain update
        -> conservative deformation-aware planner
```

This is narrower than rigorous terramechanics: the target is planning-relevant
geometry and contact affordances with explicit validity and uncertainty bounds.

## Evidence by backend

### Chrono

Chrono supplies the qualified synthetic oracle: 5 mm SCM maps, 1 ms timestep,
accepted loaded time, fixed 0.25 s residual observation, and 14,161 valid
support cells. Chrono is a reproducible teacher, not real-sand measurement or
material identification. The A4--A10 cases provide mass, radius, and spatial
holdouts. They show that centroid/location agreement does not establish peak,
volume, or recovery fidelity.

### Genesis

Genesis has an accepted 5 mm-particle/n128 prepared bed with 307,461 particles,
candidate-specific preparation, fixed-time scoring, and map-level replay
repeatability. Its confirmed incumbent is approximately `E=20.433 kPa`,
`phi=14.727 deg`, `nu=0.101895`, with 1.864 mm loaded RMSE and 13.678 mm
residual-footprint RMSE.

Genesis is not exhausted numerically. Residual recovery is still about
12.941 mm too high, and the timestep matrix is sensitive to preparation and
free-surface/wall motion. A converged three-level response has not been
demonstrated. Until that is corrected or bounded, residual error cannot be
cleanly attributed to the constitutive model. A learned discrepancy should not
be trained on this backend as though it were converged ground truth.

### Newton

Stock Newton has a fixed, mechanics-qualified public-contact domain. The local
A0 study found 19 valid observations from 21 candidates; the incumbent
(`E=70.46 kPa`, `nu=0.237231507`, `mu=0.305497980`) improved the scalar map
objective from 12.698 to 8.823 mm and replayed at 8.815 mm.

This is repeatable local map improvement, not material calibration. The
incumbent is invalid at tested 1.75--3 kg actions and 55/65 mm radii. A9 and
A10 independently show the model-form limitation: valid, map-improving
responses still overpredict peak depression by about 10--15 mm and
underpredict displaced volume by about 171--179 cm3. A10 also shows that the
control can have a better centroid error, so the incumbent is not uniformly
characteristic-better.

## Why terrain needs initialization and instrumentation

Nominal `E`, `nu`, and friction do not fully specify granular terrain. Relevant
latent state includes packing density/porosity, fabric, layering,
moisture/cohesion, preparation and settling history, boundary geometry, tool
pose and loading history, and material transport. Initialization is therefore
part of the forward model, not just data plumbing.

Each episode should preserve bed geometry and ownership, preparation protocol
and convergence statistics, tool pose/force/contact history, accepted event
times, loaded/residual maps, displaced volume, redistribution, and quality or
uncertainty indicators.

## Relationship to nearby work

The broad combination of Gaussian scenes, physics, and planning is not
unprecedented. Closest comparison families are:

* [Path Planning in Physically Viable World Models](https://huggingface.co/papers/2607.00673): 3DGS plus physics-based terrain changes and terrain-aware long-horizon planning, demonstrated with simulated flooding.
* [Physically Embodied Gaussian Splatting](https://proceedings.mlr.press/v270/abou-chakra25a): Gaussian-particle predictive simulation with visual correction for robotics.
* [SceneAgent](https://computationalrobotics.seas.harvard.edu/SceneAgent/): conversion of 3D captures into simulator-ready scenes with predictive per-Gaussian physics properties.
* [PhysReal](https://arxiv.org/pdf/2609.07532v1) and [PIDG](https://ojs.aaai.org/index.php/AAAI/article/view/42474): hybrid or constitutive neural physics for deformable visual representations.

The potentially distinctive part here is narrower: Chrono-grounded,
preparation-aware granular-terrain deformation, explicit mechanics gates, and
prospective measurement of whether linked Gaussian terrain improves planning.
The novelty is not simply Gaussian splatting plus physics.

## Is Newton/Genesis exhausted?

No. Genesis remains numerically unresolved. Newton remains capable of local
numerical and objective-level improvement. What is increasingly unlikely is a
large, globally valid improvement in all deformation characteristics from only
retuning the current global Newton parameters. A9/A10 provide evidence for a
model-form or state-representation ceiling, but not a proof of impossibility.

The appropriate final stop/go test is:

1. freeze one qualified numerical contract;
2. use a prospectively designed Chrono set in the admissible mass/radius/
   position neighborhood;
3. fit with a declared multi-characteristic Pareto rule;
4. compare map, peak, volume, footprint, centroid, timing, and validity on
   held-out cases;
5. stop parameter-only refinement if no candidate dominates the incumbent
   without losing mechanics validity.

The bounded A10 stop/go set is complete. In addition to the incumbent and
unchanged control, it evaluated two candidates selected from the prior A0
search under the same fixed contract. Both were mechanics-valid, but neither
dominated the incumbent:

| candidate | objective (mm) | loaded multi-score | residual multi-score |
| --- | ---: | ---: | ---: |
| incumbent | 8.146 | 3.154 | 11.997 |
| added C2: `log10(E)=4.812`, `nu=0.200`, `mu=0.326` | 9.097 | 3.226 | 13.303 |
| added C7: `log10(E)=5.092`, `nu=0.155`, `mu=0.411` | 10.375 | 3.956 | 15.342 |
| unchanged control | 12.244 | 4.900 | 18.292 |

C2 improves over the unchanged control but is worse than the incumbent on the
aggregate loaded and residual scores. C7 is worse still. The incumbent also
remains mixed-fidelity in absolute terms (A10: +10.624 mm peak and -171.121
cm3 volume). This is sufficient to stop broad, parameter-only Newton search
for the present direction: additional global-parameter tuning may move the
tradeoff, but no tested alternative improves the incumbent's held-out
multi-characteristic profile.

## Recommended direction after the stop/go test

1. Record the Newton stop/go result as a bounded negative result for further
   broad parameter-only search.
2. Resolve or explicitly bound Genesis preparation/response convergence.
3. Start with a characteristic-level Chrono discrepancy model conditioned on
   preparation state, action history, time, and MPM outputs. Predict corrections
   and uncertainty for peak, volume, footprint, centroid, and recovery.
4. Reject failed mechanics gates; do not let a network repair invalid physics.
5. Only after trajectory-level evidence supports it, move the correction inside
   the MPM rollout as a constitutive/contact/compaction residual.
6. Link validated deformation to camera-calibrated Gaussians, update position
   and covariance consistently, and evaluate a fixed planner against static,
   heuristic, physics-only, and hybrid baselines.

Planning metrics should include route success, clearance/collision violations,
traversability and endpoint error, replanning behavior, runtime, and uncertainty
calibration. Peak and volume remain diagnostics and safety bounds.

## Current claim boundary

Supported:

> Chrono provides a reproducible synthetic terrain oracle; qualified Genesis
> and Newton runs provide bounded MPM responses; Newton improves a map-level
> objective in part of the tested domain under strict mechanics gates.

Not supported:

* general terrain-deformation prediction;
* real-sand or material identification;
* calibrated cross-backend agreement;
* validated Gaussian deformation transfer;
* demonstrated planning gains from predicted deformation.

## Authoritative records

* [Historical Chrono-to-Newton evidence](historical-forward-model-evidence-20261004.md)
* [Current Newton state](forward-model-current-state-20261004.md)
* [A10 protocol](forward-model-a10-protocol-20261004.md)
* [Chrono overview and Genesis status](../../tera_splat_sim/docs/overview-and-status.md)
* [Chrono limitations and claims](../../tera_splat_sim/docs/limitations-and-claims.md)
* [Chrono-to-MPM roadmap](../../tera_splat_sim/docs/roadmap-and-extensions.md)

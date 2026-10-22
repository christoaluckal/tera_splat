# Phase 0 completion record: hybrid Newton residual

Date: 2026-10-22
Status: frozen completion report; not a source of live next steps

The live operational authority remains [phase0.md](phase0.md). This report
records the implementation, execution, evidence, and verification that closed
the required Phase 0 exit.

## Outcome

Phase 0 demonstrated a bounded sim-to-sim hybrid forward model:

```text
fresh initial terrain + action
    -> unchanged Newton MPM rollout
    -> bounded learned vertical residual
    -> corrected surface and corrected Newton particles
```

The required 31 N and 46 N rungs completed with 10 fresh, pipeline-usable
actions. The optional 61 N robustness rung remained absent. V1 retained the
31 N held-out spatial result. V2 was fitted once on the six 31/46 N training
actions before either 46 N y holdout existed, then passed every declared
comparison on untouched +y validation and -y test actions.

This is a post-rollout geometric correction, not a replacement constitutive
model and not a force correction inside Newton.

## Execution and leakage lock

The completion sequence was:

1. generate and admit `xminus100_f046n`, completing the six-action training
   set;
2. fit and freeze v2 exactly once;
3. generate `yplus100_f046n` and `yminus100_f046n` only after the model and
   training record existed;
4. evaluate both holdouts together with the unchanged v2 model;
5. rerun evaluation, without retraining, after adding provenance and
   corrected-particle audits.

The training set was:

- 31 N: center, +x, and -x;
- 46 N: center, +x, and -x;
- loaded and post-unload observations for every action.

The training record contains 7,356 samples and declares:

- no validation or test target used for fitting or selection;
- both 46 N y holdouts absent at fit;
- all five 61 N actions absent at fit;
- fixed architecture, optimizer settings, correction bound, and seed.

## Residual target and inputs

For phase `p`, the supervised target at each local surface cell is:

```text
target residual = Chrono surface[p] - Newton surface[p]
hybrid surface  = Newton surface[p] + predicted residual
```

The eight cell features are:

1. foot-relative x divided by foot radius;
2. foot-relative y divided by foot radius;
3. radial distance divided by foot radius;
4. signed foot distance, `r / radius - 1`;
5. phase code, -1 loaded and +1 post-unload;
6. Newton response, `Newton[p] - Newton[initial]`;
7. initial alignment error, `Chrono[initial] - Newton[initial]`;
8. normal force divided by 30.65625 N.

The deformed Chrono target is used only for training and scoring. The current
sim-to-sim implementation does consume the Chrono initial surface for initial
alignment; a real deployment would require the corresponding observed initial
terrain map.

## Network and optimization

V2 is a deterministic NumPy one-hidden-layer MLP:

```text
x_normalized = (x - training_mean) / training_std
h            = tanh(x_normalized @ W1 + b1)
raw          = tanh(h @ W2 + b2)
correction   = 0.05 m * radial_taper * raw
```

The frozen configuration is:

| Item | Value |
| --- | --- |
| topology | 8 inputs -> 24 tanh units -> 1 tanh output |
| trainable parameters | 241 |
| output bound | +/-50 mm before the radial taper |
| initialization | random first layer, zero output layer |
| optimizer | full-batch Adam |
| epochs | 3,000 |
| learning rate | 0.01 |
| L2 coefficient | 1e-5 on weight matrices |
| seed | 20261018 |
| support | full to 1.5 foot radii, cosine taper to zero at 2 radii |
| sample weights | 2 inside the footprint, 1 in the surrounding 2r crop |

The zero output layer starts optimization from an unchanged-Newton prediction.
The recorded training RMSE decreased from 6.141 mm at epoch 1 to 0.814 mm at
epoch 3,000. This value is fit evidence, not a generalization claim.

The model is not a CNN, GNN, neural operator, temporal model, or learned
simulator. Cells are evaluated independently from their coordinates and local
scalar features; spatial structure comes from the shared coordinate function
and radial taper.

## Particle lift

The learned surface correction is lifted onto saved Newton particles using:

```text
particle_delta_z =
    cell_surface_correction * exp(-depth_below_surface / 0.02 m)
```

The correction is set to zero deeper than six depth scales, or 0.12 m. Only
particle z is changed. Particle x/y, velocity, stress, velocity gradient,
elastic strain, plastic Jacobian, and deformation transform are preserved.

Each corrected state is audited for:

- equal source and corrected particle counts;
- finite source and corrected numeric arrays;
- exact x/y and zero x/y correction;
- z reconstruction within float32 precision;
- exact velocity and non-position state preservation;
- expected backend and residual model identity;
- exact reproduction of the stored corrected surface;
- source-state, corrected-state, surface, and generated-artifact SHA-256.

## 46 N held-out result

| Holdout | Phase | Raw Newton footprint / 2r RMSE | Corrected footprint / 2r RMSE |
| --- | --- | ---: | ---: |
| +y validation | loaded | 13.628 / 7.999 mm | 1.263 / 1.876 mm |
| +y validation | post-unload | 10.325 / 6.136 mm | 1.284 / 2.077 mm |
| -y test | loaded | 13.852 / 8.083 mm | 1.226 / 1.736 mm |
| -y test | post-unload | 10.252 / 6.078 mm | 1.240 / 1.871 mm |

The unchanged v2 model improved both raw Newton and the no-deformation baseline
in the footprint and twice-radius regions for both phases on both holdouts:
16 of 16 declared baseline comparisons passed. All four held-out
case/phase corrected-particle audits passed with 307,461 particles each and
zero corrected-surface reprojection error.

## Frozen identities

| Artifact | SHA-256 |
| --- | --- |
| immutable v1 model | `242fa879c1d7eda443f4277d82a41dcfea5828cdb7b66ccae357b633d99a15af` |
| frozen v2 model | `cc31209737d69a059f64627e19d9c9f76b2ba1e36be86f528802470d05b0c23f` |
| v2 training summary used by evaluation | `5109b4266451751898f9e42b50fbbe8b7610587a65ee9f9d5a4193452a2a3c11` |

The final evaluation also records and verifies the evaluator sources, case
summaries, Chrono surfaces, Newton surfaces, source particle states, corrected
states, corrected surfaces, predicted corrections, and PLY outputs.

## Implementation changes

### Base residual evaluator

`scripts/run_phase0_residual_pilot.py` now:

- snapshots admission and raw/robust error-view metadata into each evaluation;
- audits corrected particle-state invariants and stored-surface reproduction;
- hashes source states and all generated corrected artifacts;
- emits a per-case `corrected_particle_preservation_pass` result.

### Multi-load wrapper

`scripts/run_phase0_multiload_residual_pilot.py` now:

- includes loaded and post-unload Newton states in source provenance;
- refuses evaluation if the frozen model hash differs from its training record;
- records the training-summary, model, evaluator, base evaluator, case, and
  source hashes;
- serializes the pre-holdout fit-lock evidence;
- requires both local comparison success and corrected-particle preservation
  before setting `multiload_held_out_residual_exit_demonstrated`.

### Tests and authority

`tests/test_phase0_residual_pilot.py` includes a synthetic corrected-state
audit covering particle counts, x/y preservation, velocity preservation, and
surface reproduction.

`docs/newton/phase0.md` now records the 10-action frozen snapshot, completed
31 N and 46 N ledgers, v2 metrics and hash, successful exit, optional 61 N
boundary, and the appended evidence chronology.

## Verification

- focused residual modules: 8 tests passed;
- compatible repository suite: 54 tests passed;
- modified Python modules passed bytecode compilation;
- independent completion audit passed the sentinel quarantine, matrix gates,
  v1 identity, v2 split lock, model/source hashes, all local comparisons, and
  all particle invariants;
- a separate artifact audit matched 32 recorded source/output hashes.

An unscoped repository-wide pytest collection still imports executable scripts
and an unrelated diagnostic requiring optional `torch`, `viser`, and
`matplotlib` packages that are not installed in the Newton environment. This
does not affect the Phase 0 tests or evidence.

## Claim boundary

Supported:

- a fresh, provenance-complete Newton prior is locally informative over the
  tested 35 mm, 31--46 N static action domain;
- immutable v1 demonstrates held-out spatial improvement at 31 N;
- v2, trained across 31 N and 46 N, demonstrates held-out spatial improvement
  at 46 N without validation/test leakage;
- the bounded learned correction produces audited surfaces and particle states.

Not supported:

- strict Newton mechanics qualification or timestep convergence;
- interpolation or extrapolation to unseen loads, including 61 N;
- other foot geometry, dynamic locomotion, or sequential terrain accumulation;
- real-sand or material-identification claims;
- dynamically consistent corrected stress or constitutive state;
- Gaussian novel-view improvement or planner benefit.

## Isometric surface-PCD views

`scripts/render_phase0_pcd_isometric.py` renders matched surface point clouds
for the untouched 46 N holdouts. Chrono provides a surface height map rather
than a volumetric particle dump, so these figures compare like-for-like surface
PCDs: Chrono truth, raw Newton's projected particle surface, and the Hybrid's
projected corrected-particle surface.

Every panel uses the same valid cells, 240 mm action-centered crop, z bounds,
and -50 to +5 mm displacement color scale. Color encodes vertical displacement
from each method's own initial surface; geometry uses a shared world-frame
local datum. The dashed circle marks the 35 mm foot radius.

| Held-out case | Northeast view | Southwest view |
| --- | --- | --- |
| +y validation, 46 N | [PNG](figures/phase0_pcd_isometric/yplus100_f046n_isometric_ne.png) | [PNG](figures/phase0_pcd_isometric/yplus100_f046n_isometric_sw.png) |
| -y test, 46 N | [PNG](figures/phase0_pcd_isometric/yminus100_f046n_isometric_ne.png) | [PNG](figures/phase0_pcd_isometric/yminus100_f046n_isometric_sw.png) |

## Canonical artifacts

All paths below are rooted at:

`outputs/validity_experiment/newton/static_proxy_hierarchical_v3_20261017/`

- matrix state: `matrix/matrix_summary.json`;
- sentinel: `repeatability/repeatability_summary.json`;
- v1 evidence: `matrix/residual_pilot_v1/`;
- v2 model and training record:
  `matrix/residual_pilot_v2_multiload/model.npz` and
  `matrix/residual_pilot_v2_multiload/training_summary.json`;
- v2 held-out result:
  `matrix/residual_pilot_v2_multiload/evaluation_summary.json`;
- per-case corrected states and surfaces:
  `matrix/residual_pilot_v2_multiload/cases/<case_id>/`.


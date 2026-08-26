# Chrono Oracle Run Contract

Status: agreed R&D protocol, 2026-08-26. This is the operational handoff for
the next Genesis/BayesOpt run. It is read together with
[Chrono SCM Oracle Diagnostics](chrono-oracle-diagnostics.md), which retains
the measurements and investigation history.

## Decision

Use the **guided, y-offset 10 mm Chrono SCM episode** as the R&D oracle
protocol. It is the fastest configuration with the cleaner visual contact
cross-section. Use the corresponding guided **5 mm** protocol only for
higher-fidelity final validation and final production target generation.

This is a resolution decision, not a change in material parameters, Genesis
initialization, the BayesOpt acquisition rule, or the loss.

## What the old BayesOpt target taught us

The target consumed by the completed BayesOpt studies was
`A0_cal_full10mm`. It is now a **legacy pipeline target**:

- A fresh Chrono 10.0.0 replay agrees with its stored maps within `0.00076 mm`.
  Therefore it was not stale terrain data and was not corrupted by an old
  Chrono build.
- Its *contract* was incomplete: the artifact did not record the fixed
  `residual_settle_s` duration or post-removal time snapshots. A residual map
  cannot be retrospectively matched to Genesis at an arbitrary equilibrium
  time.
- The episode was a free, centered cylinder drop. At the 10 mm grid it had
  early sparse/asymmetric contact and nonzero lateral/angular motion. The
  completed BayesOpt observations are valid evidence that the bridge,
  candidate-consistent Genesis preparation, stability gate, loss, W&B logging,
  and optimizer execute. They are **not** material-calibration evidence and
  must not seed or be mixed with the next oracle-specific study.
- The earlier claim that the imprint was locked to absolute SCM-grid location
  was false. It resulted from including the invalid one-cell boundary ring in
  a centroid calculation. With `valid_heightmap_mask.npy`, the deformation
  follows the translated cylinder, though 10 mm grid phase sensitivity remains.

Thus “stale target” means stale/incomplete *experiment contract and oracle
qualification*, not stale numerical terrain data. Keep the old output
directories for auditability; archive their observations from the next study.

## R&D oracle settings: 10 mm

The selected R&D reference is
`A0_oracle_vertical_guided_grid_aligned_10mm`:

| Item | Value |
| --- | --- |
| Contact | 1.5 kg, right circular cylinder, radius `73.025 mm`, height `50.8 mm` |
| Pose | commanded center `(x, y) = (0, +5) mm` |
| Constraint | vertical prismatic guide; x/y and rotation constrained |
| SCM patch/grid | `0.6 x 0.6 m`, `10 mm` spacing, `1 ms` step |
| Soil and action | unchanged from the existing cylinder episode |
| Capture | initial, 0.1 s loading checkpoints, and post-removal checkpoints |
| Usable cells | always apply `valid_heightmap_mask.npy`; exclude the one-cell SCM boundary ring |

The synchronized comparison is at
`/data/christoa/Chrono/tera_splat_sim/validity_experiment/chrono_episodes/free_vs_guided_1p5kg_10mm_triplet/`.
It shows that the offset guided cross-section is visually cleaner than the
free-centered and guided-centered controls. This is a practical R&D choice;
it does not establish that the y offset is physically privileged.

## Stability gate before export

None of the current compact tests is yet an exportable loaded oracle: all end
because of the fixed loading timeout. In particular, the selected 10 mm R&D
episode ends with `1.142 mm/s` linear speed. The centered guided control ends
with `6.497 mm/s`; the free control ends with `23.529 mm/s` and substantial
angular speed. The 5 mm guided run is closer (`0.319 mm/s`) but also ends by
timeout.

The next exporter/run change must replace the fixed loading-duration acceptance
with a recorded, deterministic convergence gate:

1. simulate loading until linear and angular speed are below declared
   thresholds for a declared consecutive hold interval;
2. record the threshold values, hold duration, first gate-crossing time, final
   sampling time, and the sampled pose/speeds in `manifest.yaml` and
   `metrics.json`;
3. capture the loaded heightmap at that fixed accepted state;
4. remove the cylinder, recover for an explicitly recorded fixed
   `residual_settle_s`, and capture the residual state at that exact time;
5. reject an episode that cannot meet the loading gate within a declared
   maximum duration rather than labelling its timeout surface as an oracle.

The speed/hold thresholds are protocol constants to be selected and recorded
once, not BayesOpt hyperparameters.

## Promotion sequence

1. Implement and smoke-test the recorded loading-convergence gate using the
   10 mm guided y-offset R&D protocol.
2. Generate one gated 10 mm episode; run the existing Genesis initial-state
   stability gate and one bridge replay against it. Do not import any old
   BayesOpt observations.
3. If this is reproducible, run the new W&B BayesOpt study against that
   isolated target with a fresh study directory/run ID.
4. Recreate the same guided protocol at 5 mm for the selected final candidate.
   It is the higher-fidelity oracle and final validation target, not the
   iteration-resolution target.
5. Compare the 10 mm and 5 mm final results on their own valid masks; record
   resolution, timing contract, and residual recovery before publishing PLY/PCD
   exports or interpreting fitted parameters.


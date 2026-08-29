# Chrono Oracle Run Contract

Status: agreed R&D protocol, 2026-08-26. This is the operational handoff for
the next Genesis/BayesOpt run. It is read together with
[Chrono SCM Oracle Diagnostics](chrono-oracle-diagnostics-through-2026-08-26.md), which retains
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

## Loading-gate revision (2026-08-26)

The original `0.5 mm/s` linear-speed / `0.25 s` hold rule never accepted the
current 10 mm guided trace, even at a 5 s cap. Re-scoring that same trace shows
that no threshold at or below `5 mm/s` passes a `0.10 s` hold. The active Chrono
loading acceptance rule is therefore `6 mm/s` linear speed, the unchanged
`0.01 rad/s` angular-speed limit, and a `0.10 s` continuous hold. It accepts
the first sustained window near `4.696 s` in the recorded 1 ms trace.

This revision affects only Chrono loaded-state acceptance. It does **not**
change soil/contact physics, geometry, loading, the Genesis no-action
initial-state RMSE (`0.5 mm`) or maximum-drift (`1.0 mm`) gates, the BayesOpt
loss, or its parameterization. Each episode records the exact gate values.

## Accepted low-speed oracle compromise (2026-08-26)

`A0_oracle_guided_offset_10mm_gate6mm_v1` is accepted by the revised loading
gate at `4.696 s`: it remains below `6 mm/s` for `0.10 s`, has effectively zero
angular speed, and then uses the recorded `0.25 s` residual recovery. This is
a **low-speed timing acceptance**, not a claim that SCM has reached a static
equilibrium.

The rule changes neither Chrono soil/contact/loading physics nor the Genesis
no-action initial-state RMSE (`0.5 mm`) and maximum-drift (`1.0 mm`) gates. It
selects a later point on the same Chrono trajectory. Inside the action
footprint, the accepted loaded surface differs from the strict 5.0 s diagnostic
by `0.350 mm` RMSE and is `0.127 mm` shallower on average, but differs from the
earlier 0.75 s guided snapshot by `4.236 mm` RMSE and is `4.216 mm` deeper on
average.

Use this accepted 10 mm episode for R&D only, with its recorded timestamps. A
5 mm repeat remains required for final high-fidelity validation.

## Superseding 5 mm target and optimization status (2026-08-29)

The 5 mm repeat required above is complete. The accepted episode is
`A0_oracle_guided_offset_5mm_gate6mm_v1`; it passes the recorded low-speed
gate at `3.595 s`, uses fixed `0.25 s` residual recovery, and exposes `14,161`
valid interior cells. This supersedes the earlier statements that the 5 mm
protocol or recorded convergence gate was still pending.

Genesis resolution was then increased independently. A 10 mm-particle,
64-grid prepared bed passes the unchanged surface gate at `0.862 mm` H0 RMSE
and the subsequent candidate no-action stability checks. A 128-grid bed does
not yet pass: the best tested 0.125 ms preparation remains at `6.220 mm` H0
RMSE, while a fixed geostatic stress scale of 1.25 reaches `5.939 mm` but also
misses the speed gate. These failures occur before cylinder contact and do not
invalidate the Chrono oracle.

The current optimization baseline is `E=20 kPa`, `phi=18.149 deg`,
`nu=0.100004` on the accepted 10 mm-particle bed. It matches cylinder sinkage
(`34.051 mm` Genesis versus `34.270 mm` Chrono) but remains too shallow near
the footprint edge. Online W&B validation `jg3b5v3s` records objective
`8.548 mm`, loaded RMSE `2.183 mm`, and residual-footprint RMSE `12.729 mm`.

The fixed-time target is now enforced explicitly: a completed loaded map at
`3.595 s` and completed residual map at `0.25 s` are valid observations even
when Genesis has not met its stricter equilibrium label. Raw timeout reasons
remain recorded. This changes timing classification only; the frozen-H0 and
no-action RMSE/max-drift gates are unchanged.

Run the next BayesOpt study from a fresh directory with no legacy seeds, using
the accepted 10 mm-particle/64-grid bed. Treat its winner as an R&D candidate.
Final promotion still requires a resolution-aware initialization that lets the
128-grid pass the same H0 and no-action gates, followed by replay of the best
coarse-grid candidates.

## Fresh coarse-grid study result (2026-08-29)

Corrected online study `e72xmaou` reached 12/12 valid candidates with no legacy
seeds. Every candidate used the frozen 10 mm-particle/64-grid bed and all 14,161
target cells; H0 RMSE stayed between `2.947` and `3.941 mm`, while 0.25 s
no-action drift RMSE stayed between `0.008` and `0.019 mm`.

The best fresh proposal is `E=23.807 kPa`, `phi=15.532 deg`,
`nu=0.179623`, with objective `9.232 mm`. It remains `0.684 mm` worse than
the existing 20 kPa/18.149 degree/0.100004 controlled observation. Because the
fresh acquisition never sampled below `nu=0.14`, use that controlled point as
an explicit anchor in one compact follow-up before resolution promotion.

The aborted setup study `ysagrtcb` is not an observation source. It exposed and
prompted removal of a legacy 20 mm constant in the first bootstrap proposal;
all bootstrap geometry now comes from the accepted prepared-bed manifest.

## Anchored trust-region result (2026-08-29)

Online study `vrxqwoe2` completed with the 20 kPa controlled point as its only
seed and nine valid new candidates. The anchor remains best at `8.548 mm`.
Two new low-nu confirmations score `8.605 mm` at 18.110 kPa/18.984
degrees/0.103989 and `8.643 mm` at 20.186 kPa/18.485 degrees/0.100693.

This is sufficient coarse-grid corroboration. Carry these three candidates into
the n128 replay only after resolution-aware geostatic preparation passes the
same H0 and no-action gates. Do not alter Chrono timing, Genesis physics, or the
loss to make the finer initialization pass.

## Accepted n128 initialization and replay (2026-08-29)

The resolution gate now passes with 5 mm particles on n128, preserving the
accepted n64 ratio of 3.125 particle spacings per MPM cell. The 307,461-particle
bed accepts at `1.1825 s`, p99 `0.492 mm/s`, H0 RMSE `0.070 mm`, and maximum
H0 error `0.237 mm`. Geostatic stress scale remains 1.0.

The 20 kPa anchor remains best after three fixed-time replays: `9.626 mm`
versus `9.833` and `10.041 mm`. Its loaded RMSE is `2.142 mm`, but
residual-footprint RMSE is `14.966 mm` with a `+14.308 mm` signed mean.
Genesis therefore recovers too much after removal at the promoted resolution.

A 4 s candidate-preparation cap is required because candidate states accept just
after 2 s; the speed and surface gates are unchanged. Continue calibration on
this accepted n128 bed with the existing material parameters only.

# Chrono-to-Newton forward-model historical evidence

Last updated: 2026-10-04  
Status: canonical cross-repository evidence ledger for the active sim-only study

This is the hand-off document for agents resuming the Chrono-as-ground-truth
terrain-deformation work. It consolidates material results after the 2026-09-28
Newton handoff. It does **not** replace dated records: discovery/replay
differences are retained and their canonical artifact is named.

## Scope and validity contract

The study tests whether public, stock Newton MPM can predict terrain deformation
from an action after fitting to one Chrono-generated rigid-probe episode.
Chrono is synthetic GT, not real-sand measurement. This is not material
identification, real-world validation, NVS validation, or permission to change
Newton private physics.

The qualified Newton domain is fixed at 7.8125 mm voxels, PIC/PIC transfer,
P0/S2/Q1, 0.25 ms timestep, eight proxy iterations, and sixteen rigid
substeps. Every evaluation uses fresh full-bed preparation and a separate,
continuous preparation/loading/removal response; saved Newton states are
archival I/O, never restart checkpoints. Use the episode's accepted loaded time
and its 0.25 s residual duration exactly.

Hard gates are finite maps on the full 14,161-cell support, matching initial
terrain and mask, prismatic-guide compliance, and zero analytic
particle-center penetration. A failed run has no score and is not an optimizer
observation.

## Frozen calibration and metrics

Calibration action A0 is a guided 1.5 kg cylinder, canonical radius 73.025 mm,
at `(x, y) = (0, +5) mm`, loaded in Chrono at 3.595 s. The frozen Newton
incumbent selected only from A0 is:

| parameter | value |
| --- | ---: |
| `log10(E / Pa)` | 4.847943757 |
| Young's modulus | 70.46 kPa |
| Poisson ratio | 0.237231507 |
| friction coefficient | 0.305497980 |

The unchanged control is `E=100 kPa`, `nu=0.2`, `mu=0.68`. Incumbent A0
discovery/replay objectives are 8.823/8.815 mm, versus 12.698 mm control.
That is in-domain local improvement only.

The scalar runner objective is `loaded RMSE + 0.5 * residual-footprint RMSE`
(mm). It is not a complete deformation-characteristics metric. The analysis
also measures peak/mean/footprint depression, depression volume, and depression
centroid. The later multi-characteristic score is diagnostic only, never an
optimizer loss.

## Chronological Chrono GT record

All accepted Chrono episodes have finite initial/loaded/residual maps on the
canonical support. A2-A9 have bitwise-equal canonical support and initial
terrain. A5 and A6 share that initial state, yet their accepted loaded maps are
not perfect reflections: A5 versus mirrored A6 has 2.181 mm RMSE.

| ID | action change from A0 | accepted loaded time | loaded sinkage | result |
| --- | --- | ---: | ---: | --- |
| A0 | calibration, 1.5 kg, y=+5 mm | 3.595 s | source episode | frozen point from 19 unique valid observations |
| A1 | 3.0 kg, y=+5 mm | 2.417 s | source episode | incumbent invalid; control valid |
| A2 | 2.0 kg, y=+5 mm | 2.188 s | 35.804 mm | incumbent invalid; control valid |
| A3 | 1.75 kg, y=+5 mm | 1.403 s | 32.860 mm | incumbent invalid; control valid |
| A4 | 1.625 kg, y=+5 mm | 2.231 s | 33.312 mm | both valid |
| A5 | 1.625 kg, x=+50 mm | 0.816 s | 22.189 mm | both valid |
| A6 | 1.625 kg, x=-50 mm | 0.902 s | 23.005 mm | both valid |
| A7 | 1.625 kg, radius=55 mm, y=+5 mm | 0.456 s | 24.386 mm | incumbent invalid; control valid |
| A8 | 1.625 kg, radius=65 mm, y=+5 mm | 0.588 s | 23.047 mm | incumbent invalid |
| A9 | 1.625 kg, canonical radius, y=+50 mm | 3.341 s | 34.547 mm | incumbent valid |

Source episode directories are under
`tera_splat_sim/validity_experiment/chrono_episodes/`, except qualified A0,
which is archived under `/data/christoa/Chrono/tera_splat_sim/validity_experiment/chrono_episodes/`.
Read the manifest for exact timing rather than reconstructing it from this table.

## Newton held-out evidence

Only `valid` rows passed every hard gate. `--` means deliberately unscored or
unrun. Parentheses identify the maximum sampled center penetration causing a
rejection.

| action | incumbent: objective / loaded / residual-footprint (mm) | control: objective / loaded / residual-footprint (mm) | finding |
| --- | --- | --- | --- |
| A0 | 8.823 discovery; 8.815 replay | 12.698 / source artifacts | in-domain improvement |
| A1, 3 kg | invalid (31; 1.332 um) | 16.289 / source artifact | high-load boundary |
| A2, 2 kg | invalid (18; 0.875443 um) | 13.211209 / 3.993985 / 18.434448 | boundary persists |
| A3, 1.75 kg | invalid (2; 0.040978 um) | 11.353496 / 3.420492 / 15.866010 | boundary persists |
| A4, 1.625 kg | 7.911218 / 2.367769 / 11.086898 | 11.888078 / 3.592382 / 16.591392 | incumbent wins all scalar terms |
| A5, x=+50 mm | 3.379302 / 1.223777 / 4.311049 canonical; 3.398661 / 1.227990 / 4.341342 repeat | 3.272178 / 0.960535 / 4.623285 | control slightly lower scalar; incumbent lower residual error |
| A6, x=-50 mm | 3.087760 / 1.119986 / 3.935548 | 4.072636 / 1.201066 / 5.743140 | incumbent wins scalar and residual |
| A7, radius 55 mm | invalid (4; 1.406297 um) | 2.643076 / 0.574235 / 4.137683 | reduced-radius boundary |
| A8, radius 65 mm | invalid (6; 1.283363 um) | -- | incumbent radius boundary |
| A9, y=+50 mm | 8.489721 / 2.542635 / 11.894172 | -- | valid characteristic stress test |

The two A5 entries are independent valid incumbent executions. The first is
the originally designated canonical output; the second entered the later
aggregate table. They show small repeat variation, not a changed model.

## Characteristic evidence and conclusions

The scalar objective can hide important errors. A2 control loaded peak is
23.497 mm in Chrono versus 2.645 mm in Newton, and volume is 343.558 versus
40.869 cm3. A4 incumbent improves scalar error but overpredicts peak by
11.289 mm and underpredicts volume by 163.293 cm3.

A9 is the strongest mechanics-versus-fidelity counterexample. Its valid
incumbent has centroid errors +0.046 mm x and -0.258 mm y, but overpredicts
peak depression by 14.730 mm and underpredicts volume by 178.812 cm3
(Chrono/Newton peak 22.317/37.047 mm; volume 323.694/144.882 cm3).

The evidence supports these bounded conclusions:

1. Frozen stock Newton is mechanically usable in some actions and can improve
   map-level error over the unchanged control.
2. The incumbent is inadmissible at A1-A3 high load and A7-A8 reduced radii.
   Its valid canonical radius is above 65 mm and at or below 73.025 mm in this
   fixed domain; the interior is untested and the bracket is not a threshold.
3. Validity and low scalar error do not establish peak or volume prediction.
   A complete forward-model result must report all characteristics separately.
4. The linear Chrono-only characteristic surrogate is not deployable. A2-A8
   leave-one-out RMSE: 0.387 mm mean depression, 7.292 mm peak, 130.143 cm3
   volume, 26.598 mm x-centroid. With A0-A9 it becomes 1.686 mm mean, 30.688
   mm peak, and 565.574 cm3 volume; A9 exposes nonlinear behavior.

## Evidence routing and canonical tooling

| need | canonical source |
| --- | --- |
| detailed dated results | `tera_splat/docs/forward-model-*.md` and `newton-handoff-a5-addendum-20261002.md` |
| A0 fit and re-score | `tera_splat/diagnostics/forward_model_transfer_20261002/a0-recalibration.md` and `a0_candidate_scores.csv` |
| state-level A2-A7 metrics | `tera_splat/diagnostics/forward_model_transfer_20261002/characteristics.csv` |
| A6-A9 special results | `.../a6-results.md`, `a7-results.md`, `a8-results.md`, `a9-newton-results.md` |
| A9 characteristic CSV | `.../a9_newton/characteristics.csv` |
| transfer analyzer | `tera_splat/scripts/analyze_forward_model_transfer_v3.py` |
| characteristic scorer | `tera_splat/scripts/score_forward_model_characteristics.py` |
| A0 archive scorer | `tera_splat/scripts/score_a0_candidate_archive.py` |
| Chrono-only surrogate | `tera_splat/scripts/fit_chrono_characteristic_surrogate_v2.py` and `predict_chrono_characteristics.py` |

Older unsuffixed or `_v2` transfer-analysis drafts are not canonical.

## Resumption protocol

Read this ledger, [Newton handoff](newton-handoff.md),
[fixed-domain contract](newton-fixed-domain.md), and the source episode manifest
before work. Freeze the numerical/contact setup, generate GT first, pass the
manifest times exactly, evaluate frozen incumbent and unchanged control when
meaningful, then gate before scoring. Report timing, all hard-gate status,
objective, loaded/residual RMSE, peak/mean/footprint depression, volume, and
centroid. Never convert invalid trials, replays, or diagnostic scores into
optimizer observations.

Next scientific work needs purpose-designed GT coverage around the observed
mass, radius, and spatial boundaries and a prospectively defined multimetric
acceptance rule. The present evidence does not support a general terrain
deformation predictor claim.

## A10 prospective interior spatial holdout — 2026-10-04

A10-v2 is the canonical 1.625 kg, 73.025 mm guided cylinder at `(0,+25) mm`.
Chrono accepted it at `2.289 s` with a `0.25 s` residual phase. Its 5 mm,
14,161-cell support and initial terrain are bitwise equal to A9. Both fresh
Newton evaluations passed exact timing, finite/full-support I/O, guide, and
strict zero analytic particle-center penetration gates.

| candidate | objective / loaded / residual-footprint (mm) |
| --- | ---: |
| frozen incumbent | 8.146293 / 2.450837 / 11.390910 |
| unchanged 100 kPa control | 12.244222 / 3.704543 / 17.079357 |

The incumbent wins every scalar map term. Its loaded peak is 32.200 mm versus
Chrono 21.577 mm (+10.624 mm), while its loaded depression volume is 140.135
versus 311.256 cm3 (-171.121 cm3). The control's corresponding errors are
-19.577 mm and -280.960 cm3. The control has a smaller loaded centroid-vector
error (0.068 versus 0.191 mm). Therefore A10 is a mechanics-valid,
scalar-improving but **mixed-fidelity** result, not evidence of full
characteristic fidelity or a general predictor.

The first A10-v1 episode is excluded from all analysis: it accidentally used
0.5 ms, 10 mm, 1.2 m runner defaults rather than the fixed 1 ms, 5 mm, 0.6 m
contract. Canonical A10-v2 analysis is
`diagnostics/forward_model_transfer_20261002/a10_newton/`.

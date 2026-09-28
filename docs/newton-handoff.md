# Newton Sim-Only Handoff

Last updated: 2026-09-28

Use this note to resume the active Newton work without treating historical
Genesis results, old diagnostics, or large output trees as current instruction.
Detailed evidence is linked below; this is the operational summary.

## Scope and current conclusion

The goal is a sim-only, externally consistent Chrono-to-Newton forward-model
study for rigid probing. It is not real-sand calibration, NVS integration, or
robot-trajectory optimization. Do not alter Newton internal physics
computations; material parameters and declared experiment settings may vary.

The qualified numerical/I/O domain is public stock Newton contact at `7.8125 mm`
with PIC/PIC, P0/S2/Q1, `0.25 ms`, 8 proxy iterations, and 16 rigid substeps.
The frozen fitting action is A0: a guided 1.5 kg cylinder at `(0, +5 mm)`,
loaded at `3.595 s` then removed for `0.25 s` residual recovery.

Nineteen mechanics-valid 1.5 kg observations were collected from 21 attempted
candidates. The independently replayed in-domain incumbent is:

| Parameter | Value |
| --- | ---: |
| Young's modulus | `70.46 kPa` (`log10(E)=4.847943757`) |
| Poisson ratio | `0.237231507` |
| friction coefficient | `0.305497980` |
| discovery / replay objective | `8.823 / 8.815 mm` |

This is repeatable local objective improvement over the 100 kPa baseline
(`12.698 mm`), but it is neither optimizer convergence nor calibrated material
inference.

## Held-out result and current boundary

A frozen A1 action doubles only the cylinder mass to 3 kg. Its initial Chrono
map is exactly equal to A0's on all 14,161 valid cells and its accepted loaded
map is at `2.417 s`. Both runners now derive loaded/residual timing from the
supplied episode manifest, pass it explicitly, record it, and reject a mismatch.

At the aligned `2.417 s` / `0.25 s` A1 timing:

| Setting | Mechanics | Score |
| --- | --- | --- |
| selected 1.5 kg incumbent | rejected: 31 particle centers, `1.332 um` maximum penetration | no valid objective |
| fixed 100 kPa baseline (`nu=0.2`, `mu=0.68`) | accepted: zero sampled centers penetrate | `16.289 mm` |

Therefore the qualified public configuration can execute the 3 kg action, but
the selected 1.5 kg material is not an admissible high-load forward-model
candidate. This is a bounded transfer failure of that parameter point; do not
use the rejected run as a BayesOpt observation or claim broad material/NVS
transfer.

## Non-negotiable contract

- Keep the Chrono episode, geometry, guide, map projection, valid mask,
  scoring rule, numerical configuration, and chosen timestep fixed within a
  study.
- Every candidate requires fresh full-bed candidate preparation and a separate
  fresh continuous preparation/loading/removal response. Newton states are
  archival; never restart from them.
- Read `chrono.loading_convergence.final_sample_time_s` and
  `chrono.residual_recovery.fixed_duration_s` from the supplied episode. The
  Newton requested and recorded times must agree exactly (within the runner's
  `1e-12 s` assertion).
- Require finite/full-support I/O, prismatic-guide compliance, and strict zero
  analytic particle-center penetration. Invalid trials and confirmation replays
  are not BayesOpt observations.
- Do not import Genesis parameters, states, observations, or material semantics
  as Newton evidence. Private contact/rasterizer overrides remain diagnostic
  only.

## Canonical artifacts

| Purpose | Location |
| --- | --- |
| fixed-domain contract | `tera_splat/docs/newton-fixed-domain.md` |
| detailed 3 kg result | `tera_splat/diagnostics/newton_mass3kg_holdout_20260922/README.md` |
| A0 fitted Chrono episode | `/data/christoa/Chrono/tera_splat_sim/validity_experiment/chrono_episodes/A0_oracle_guided_offset_5mm_gate6mm_v1` |
| A1 3 kg episode | `tera_splat_sim/validity_experiment/chrono_episodes/A1_oracle_mass3kg_guided_offset_5mm_gate6mm_v1` |
| selected incumbent replay | `tera_splat/outputs/validity_experiment/newton_bayesopt/broad_best_replay_20260921/` |
| aligned A1 incumbent output | `tera_splat/outputs/validity_experiment/newton_holdout/mass3kg_incumbent_timealigned_20260927/` |
| aligned A1 baseline output | `tera_splat/outputs/validity_experiment/newton_holdout/mass3kg_baseline_timealigned_20260927/` |

Run Newton tooling with `/data/christoa/conda/envs/newton_splat/bin/python`.
Generate Chrono SCM episodes with `conda run -n chrono_splat python
run_cylinder_episode.py` from `tera_splat_sim`.

## Next permitted experiment

Freeze a less severe or otherwise alternate rigid action that remains within
the incumbent's mechanics-admissible domain. First generate and accept its
Chrono episode. Then evaluate the incumbent and unchanged 100 kPa control with
no retuning, using the episode-specific timing contract. Interpret transfer only
if both mechanics gates pass; otherwise report the action/material boundary and
do not turn it into an optimizer datum.

## Read next

- [Newton fixed-domain contract](newton-fixed-domain.md)
- [3 kg held-out diagnostic](../diagnostics/newton_mass3kg_holdout_20260922/README.md)
- [Current state](current-state.md)
- [Companion simulator validation](../../tera_splat_sim/docs/validation-and-results.md)

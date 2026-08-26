# Chrono SCM Oracle Diagnostics

Status: R&D protocol selected; stability-gated export still required,
2026-08-26. This note is the source of truth for whether a Chrono cylinder
episode is suitable as a Genesis/BayesOpt target. See
[Chrono Oracle Run Contract](chrono-oracle-run-contract.md) for the next-run
decision and legacy-observation policy.

## Scope

The BayesOpt bridge, frozen Genesis initialization, validity gates, objective,
and W&B instrumentation are operational. This investigation changes neither
the Genesis parameterization nor the BayesOpt loss. It checks whether the
Chrono SCM heightmap supplied to that pipeline is a suitable oracle.

The original full 10 mm target was replayed from a fresh Chrono build. Its maps
matched the stored maps to within 0.00076 mm, so it is not stale terrain data
or an old Chrono build. It is nevertheless retired as a calibration target:
its residual-time contract was not recorded and its free centered loading
protocol was not qualified. A visual screen that appeared circular at `t=1.0
s` was a **post-removal** state after a forced loading timeout; it is not
comparable to the loaded target used by the sweep.

## Completed translation/phase check (corrected 2026-08-26)

A compact, time-captured SCM screen was used before changing the load protocol:

- 0.6 m x 0.6 m patch; 10 mm SCM spacing; 1 ms time step.
- Same cylinder, mass, soil, clearance, capture interval, and loading schedule
  for every run.
- Only the commanded cylinder x/y center changed.
- Early deformation was measured at `t=0.1 s` using the
  depression-weighted centroid **inside `valid_heightmap_mask.npy`**. The
  one-cell SCM boundary ring must be excluded.

| Episode | Commanded center (mm) | Cylinder center at 0.1 s (mm) | Valid-interior centroid, absolute (mm) | Centroid relative to commanded center (mm) |
| --- | ---: | ---: | ---: | ---: |
| centered baseline | (0, 0) | (-0.120, 0.000) | (0.426, 0.000) | (0.426, 0.000) |
| x half-cell | (5, 0) | (4.867, 0.000) | (7.723, 0.000) | (2.723, 0.000) |
| x/y half-cell | (5, 5) | (4.849, 5.000) | (6.829, 5.000) | (1.829, 0.000) |

This **does not demonstrate a grid-locked deformation**. The valid-interior
centroid moves with the cylinder: from the baseline it moves about `+7.30 mm`
in x for the `+5 mm` x shift, and about `(+6.40, +5.00) mm` for the diagonal
shift. It does show coarse-grid phase sensitivity in x: the centroid is
roughly 1.4--2.3 mm to the right of the commanded cylinder center in the two
shifted cases. That is a resolution/protocol question to quantify, not proof
that the deformation remains fixed in world coordinates.

Earlier values in this note incorrectly included the invalid boundary ring and
therefore created a false grid-lock conclusion. The comparison images and
manifest were regenerated with the valid mask on 2026-08-26.

Artifacts:

- baseline: `/data/christoa/Chrono/tera_splat_sim/validity_experiment/chrono_episodes/A0_oracle_screen_10mm`
- x half-cell: `/data/christoa/Chrono/tera_splat_sim/validity_experiment/chrono_episodes/A0_oracle_phase_xhalf_10mm`
- x/y half-cell: `/data/christoa/Chrono/tera_splat_sim/validity_experiment/chrono_episodes/A0_oracle_phase_xyhalf_10mm`
- corrected visual comparison: `/data/christoa/Chrono/tera_splat_sim/validity_experiment/chrono_episodes/grid_phase_discrepancy_visualization`

## Consequence

The phase test alone does not invalidate a 10 mm target. It establishes that
coarse-grid phase can produce millimetre-scale centering differences. The
legacy BayesOpt target is retired for its incomplete timing contract and
unqualified free-load protocol, not because this test proves a fixed-grid
artifact. The next study uses a fresh isolated target and no old observations.

This remains an oracle discretization/protocol investigation, not a need for
a classifier, a new Genesis material parameter, or a different BayesOpt
acquisition policy.

## Current protocol change

`run_cylinder_episode.py` now has `--vertical-guide`. It uses a Chrono
prismatic guide tied to a fixed, non-colliding reference body. The cylinder
remains loaded by its existing mass and gravity, but x/y translation and all
rotation are constrained. Thus the change removes lateral drift and spin
without adding a calibration variable or changing the soil model.

The selected 10 mm R&D protocol uses center `(0, 5 mm)` because its
cross-section is visually cleaner than the free-centered and guided-centered
controls:

`/data/christoa/Chrono/tera_splat_sim/validity_experiment/chrono_episodes/A0_oracle_vertical_guided_grid_aligned_10mm`

The earlier rationale that this was a uniquely grid-native alignment was based
on the invalid-boundary centroid and is withdrawn. It is a practical R&D
reference, not a claim that the y offset is physically privileged. It still
ends at the fixed loading timeout (`1.142 mm/s` linear speed), so it cannot
yet replace the full target. The synchronized free/guided comparison is at
`/data/christoa/Chrono/tera_splat_sim/validity_experiment/chrono_episodes/free_vs_guided_1p5kg_10mm_triplet/`.

## Fresh-build export contract

The fresh Chrono 10.0.0 Vehicle/Python build writes a canonical episode bundle,
not PLY/PCD files directly. A completed episode contains:

- `initial_heightmap_m.npy`, `loaded_heightmap_m.npy`, and
  `residual_heightmap_m.npy`: native float32 SCM heightmaps in metres.
- `valid_heightmap_mask.npy`: the usable common-grid mask; the one-cell SCM
  boundary ring is excluded.
- `action.json`: cylinder geometry, mass, commanded center, clearance, and
  gravity.
- `object_pose.csv`: time-resolved cylinder pose/speeds during loading.
- `metrics.json`: termination reason, sinkage, final speeds, and peak
  depression.
- `manifest.yaml`: heightmap frame, origin, spacing, shape, soil values,
  timestep, and protocol flags such as `vertical_guide`.
- When `--capture-interval-s` is supplied, `terrain_snapshots/manifest.json`
  plus timestamped heightmaps for video or time-resolved inspection.

The fresh full-bed replay is at
`/data/christoa/Chrono/tera_splat_sim/validity_experiment/chrono_episodes/A0_replay_full10mm_chrono10`.
It is the replay used to establish the 0.00076 mm maximum map difference from
the prior stored target.

PLY and PCD files remain **derived exports**: generate them from the episode
bundle only after the oracle has passed validation, using the existing SCM
export utilities. This avoids representing an unvalidated raw grid artifact as
a canonical mesh or point cloud. Any derived export must retain the episode ID,
state (`initial`, `loaded`, or `residual`), spacing, valid-mask policy, and
source manifest path.

## Explicit next steps

1. Implement a recorded speed-and-hold loading convergence gate. A timeout map
   is diagnostic evidence, never an exportable loaded oracle.
2. Smoke-test that gate with the guided 10 mm y-offset R&D protocol; retain the
   same valid-mask, loading and residual timing contract in its bundle.
3. Run the unchanged Genesis initialization/stability gate and a fresh bridge
   replay against the new 10 mm target. Do not import legacy observations.
4. Start a fresh online W&B study only after that isolated target passes.
5. Re-run the same protocol at 5 mm for final-candidate validation and final
   high-fidelity export. The 5 mm run is higher fidelity; 10 mm remains the
   R&D iteration resolution.

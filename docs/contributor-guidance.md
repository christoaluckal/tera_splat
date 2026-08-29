# Agent and Contributor Handoff

Read [current-state.md](current-state.md) and
[chrono-oracle-run-contract.md](chrono-oracle-run-contract.md) before editing
calibration code, configurations, or reports.

## Working rules

- Work from `/eng/home/christoa/Workspace/splatting/Chrono/tera_splat`.
- Use the `chrono_splat` conda environment for all instrumentation.
- Write generated calibration outputs under
  `/data/christoa/Chrono/tera_splat/outputs`.
- Preserve user changes and generated evidence. Do not reset or delete outputs
  unless explicitly asked.
- Use `rg` for discovery and `apply_patch` for source edits when available.
- Run focused verification after code changes.
- Update the active status and run contract when a result changes the incumbent,
  observation policy, validity gates, or next experiment.
- Treat files in `docs/archive/` as immutable historical provenance.

## Source boundaries

```text
EDGS splat:       ../EDGS/
PhysGaussian:     ../PhysGaussian/
RealSense source: ../lamp/ros2_ws/src/realsense_splat/
Chrono oracle:   ../tera_splat_sim/
```

Calibration decisions and Genesis evidence belong in this repository. Chrono
episode-generation details also need a synchronized status update in
`../tera_splat_sim/docs/`.

## Non-negotiable physics and validity rules

- The action is a mass-controlled gravitational cylinder placement.
- Penetration is a simulation output; do not substitute target-depth loading.
- `0.14605 m` is cylinder diameter; radius is `0.073025 m`.
- Use a settled volumetric bed, not a surface-only particle shell.
- Keep the active Chrono episode, timing, valid mask, and loss frozen during a
  material study.
- Require candidate-specific geostatic reconstruction, H0 acceptance, and the
  no-action stability gate before cylinder contact.
- Do not add failed initialization trials to BayesOpt observations.
- Do not mix n64 and n128 objectives in one surrogate without an explicit
  multi-fidelity model.
- Do not loosen RMSE/speed gates or fit a stress multiplier to make a candidate
  valid.

## Active calibration baseline

- Oracle: `A0_oracle_guided_offset_5mm_gate6mm_v1`.
- Prepared bed:
  `A0_oracle_guided_offset_5mm_gate6mm_prepared_5mm_n128_ratio_matched`.
- Incumbent: `E=20 kPa`, `phi=18.149 deg`, `nu=0.100004`.
- W&B run: `qgk3079l`.
- Result: objective `9.626 mm`, loaded RMSE `2.142 mm`,
  residual-footprint RMSE `14.966 mm`.
- Remaining issue: excessive post-removal recovery.

## Current entry points

```bash
conda run -n chrono_splat python scripts/build_chrono_settled_bed.py --help
conda run -n chrono_splat python scripts/run_chrono_genesis_bridge.py --help
conda run -n chrono_splat python scripts/run_chrono_genesis_bayesopt.py --help
conda run -n chrono_splat python scripts/run_mass_controlled_terrain.py --help
```

Do not create another live status document. Update `docs/current-state.md`;
put chronological or superseded material in `docs/archive/`.

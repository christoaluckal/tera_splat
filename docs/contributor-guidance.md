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
- Incumbent: `E=20.432828 kPa`, `phi=14.727053 deg`, `nu=0.101894536`.
- Discovery / exact replay: W&B `yab3idti` / `r2at0vvb`.
- Confirmed result: objective `8.704 mm`, loaded RMSE `1.864 mm`,
  residual-footprint RMSE `13.678 mm`.
- Retained raw/visual replay: W&B `ykep3esa`, under
  `A0_oracle_guided_offset_5mm_gate6mm_5mm_n128_incumbent_raw_20260830`.
  It is visualization evidence only because four residual projection cells
  exceeded the frozen three-cell sparse-bin bound; never seed from it or use
  it to replace `r2at0vvb`.
- Remaining Genesis issue: excessive post-removal recovery is entangled with
  timestep-dependent boundary/free-surface preparation drift.

## Forward-model branch rules

- Treat this working tree and every active result above as the Genesis
  baseline. Newton is assessed but is not installed or implemented here.
- Develop Newton on a separate branch and in a separately pinned environment.
- Reuse the qualified Chrono oracle and external comparison contract, not the
  Genesis prepared state or optimizer observations.
- Give every generated study, manifest, diagnostic, and W&B run an explicit
  backend identity. Never merge Genesis and Newton observations into one
  surrogate unless a documented multi-backend model is introduced.
- Translate and validate material conventions explicitly. Newton's friction
  coefficient is not automatically the Genesis friction angle.
- Update both repositories' active docs when a backend reaches or fails an
  acceptance gate.

## Current entry points

```bash
conda run -n chrono_splat python scripts/build_chrono_settled_bed.py --help
conda run -n chrono_splat python scripts/run_chrono_genesis_bridge.py --help
conda run -n chrono_splat python scripts/run_chrono_genesis_bayesopt.py --help
conda run -n chrono_splat python scripts/run_mass_controlled_terrain.py --help
conda run -n chrono_splat python scripts/render_chrono_genesis_pointcloud_dem_comparison.py --help
```

Do not create another live status document. Update `docs/current-state.md`;
put chronological or superseded material in `docs/archive/`.

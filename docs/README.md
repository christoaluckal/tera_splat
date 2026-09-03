# Tera Splat

Chrono-to-Genesis terrain calibration for a mass-controlled rigid-cylinder
experiment. The active workflow uses a qualified 5 mm Chrono SCM oracle, an
accepted 5 mm-particle/n128 Genesis MPM bed, fixed-time loaded/residual maps,
validity-gated candidate initialization, and online W&B BayesOpt.

## Start here

1. [Current state](current-state.md) — authoritative result, incumbent,
   observation set, actions, and next experiment.
2. [Chrono Oracle and BayesOpt Run Contract](chrono-oracle-run-contract.md) —
   frozen target, preparation, gates, timing, loss, and observation policy.
3. [Chrono SCM Oracle Diagnostics](chrono-oracle-diagnostics.md) — evidence
   that qualifies the target.
4. [Calibration Problems](experiment_problems.md) — resolved failures and the
   current residual-response blocker.
5. [Contributor Guidance](contributor-guidance.md) — workspace and editing
   rules.

Files under [archive/](archive/) are dated provenance. They are not active
instructions and intentionally retain superseded hypotheses and next steps.

## Current status

- Active oracle: `A0_oracle_guided_offset_5mm_gate6mm_v1`.
- Active Genesis bed: 307,461 particles at 5 mm on n128.
- Current incumbent: `E=20.433 kPa`, `phi=14.727 deg`, `nu=0.101895`.
- Confirmed n128 result: objective `8.704 mm`, loaded RMSE `1.864 mm`,
  residual-footprint RMSE `13.678 mm`.
- Retained raw/visual replay: W&B `ykep3esa`; 78 sampled rollout PLYs,
  initial/loaded/residual MPM states, aligned surface PCDs, comparison arrays,
  and loaded/residual point-cloud plus DEM-error figures.
- Non-learned diagnosis complete: four-point loaded/residual Pareto front,
  recovery and `F`/`Jp` localization, and a 2x2 resolution/timestep matrix.
- Current blocker: Genesis recovers too much after removal, but halving the
  timestep changes residual-footprint RMSE by `1.525--2.325 mm`; numerical
  convergence is not demonstrated, so model-form failure is not yet isolated.
- Third n128 level: `0.125 ms` preparations with 2 and 4 s caps both failed
  the unchanged speed gate; accepted-state reuse also failed candidate
  relaxation before contact. No third score is eligible.
- Same-state 4 s traces explain that failure: the fast mode shifts from
  wall/ground at `0.5 ms`, through wall/surface at `0.25 ms`, to
  free-surface uplift at `0.125 ms`. Fine-step p50/p95/p99 are
  `0.291/0.764/0.986 mm/s`; this is timestep-dependent preparation, not
  uniform bulk compaction or a one-percent wall artifact.
- Lightweight reports are tracked under `diagnostics/`; large beds, states,
  PLY/PCD sequences, and evaluation runs remain under `outputs/`.
- Forward-model decision: the current branch remains the frozen Genesis
  baseline. Newton v1.5.1 has been assessed as a viable alternate MPM backend,
  but no Newton implementation, prepared state, calibration, or result exists
  yet. It belongs on a separate branch with solver-specific evidence.

The raw visualization replay is not a replacement confirmation: aggregate
metrics and p99 map agreement were stable, but four residual cells exceeded
the frozen three-cell sparse projection-bin allowance. The authoritative
confirmation remains `r2at0vvb`.

## Environment

Use the existing environment for all instrumentation:

`conda env: chrono_splat`

CUDA Genesis runs require a shell where the host GPU is visible. Generated
calibration outputs belong under
`/data/christoa/Chrono/tera_splat/outputs`, not the home-workspace quota.

## Repository boundaries

```text
EDGS input:       ../EDGS/output/point_cloud/iteration_7000/point_cloud.ply
PhysGaussian ref: ../PhysGaussian/
RealSense source: ../lamp/ros2_ws/src/realsense_splat/
Chrono oracle:   ../tera_splat_sim/
```

`tera_splat` owns forward-model preparation, calibration interpretation,
response scoring, W&B studies, and handoff documentation. The present
implementation and all current results are Genesis-specific. `tera_splat_sim`
owns Chrono oracle generation and qualification artifacts.

## Current entry points

```bash
conda run -n chrono_splat python scripts/build_chrono_settled_bed.py --help
conda run -n chrono_splat python scripts/run_chrono_genesis_bridge.py --help
conda run -n chrono_splat python scripts/run_chrono_genesis_bayesopt.py --help
conda run -n chrono_splat python scripts/run_mass_controlled_terrain.py --help
conda run -n chrono_splat python scripts/render_chrono_genesis_pointcloud_dem_comparison.py --help
conda run -n chrono_splat python scripts/diagnose_chrono_genesis_model_form.py --help
```

Do not launch a new study until its target, prepared bed, resolution, seed
policy, and gates match the active run contract.

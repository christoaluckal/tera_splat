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
- Current incumbent: `E=20 kPa`, `phi=18.149 deg`, `nu=0.100004`.
- n128 incumbent result: objective `9.626 mm`, loaded RMSE `2.142 mm`,
  residual-footprint RMSE `14.966 mm`.
- Current blocker: Genesis recovers too much after removal; initialization,
  I/O, timing, and resolution gates pass.

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

`tera_splat` owns Genesis preparation, calibration interpretation, response
scoring, W&B studies, and handoff documentation. `tera_splat_sim` owns Chrono
oracle generation and qualification artifacts.

## Current entry points

```bash
conda run -n chrono_splat python scripts/build_chrono_settled_bed.py --help
conda run -n chrono_splat python scripts/run_chrono_genesis_bridge.py --help
conda run -n chrono_splat python scripts/run_chrono_genesis_bayesopt.py --help
conda run -n chrono_splat python scripts/run_mass_controlled_terrain.py --help
```

Do not launch a new study until its target, prepared bed, resolution, seed
policy, and gates match the active run contract.

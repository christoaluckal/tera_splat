# Tera Splat

Chrono-to-MPM terrain calibration for a mass-controlled rigid-cylinder
experiment. Genesis remains the frozen calibration baseline. The active Newton
direction uses stock contact and public solver settings only. At a `7.8125 mm`
voxel size, `8/16` proxy/substep coupling passes the complete
`0.5/0.25/0.125 ms` response matrix. It defines an uncalibrated, fixed
simulator domain that is eligible for a separate sim-only BayesOpt study.

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
6. [Newton Fixed-Domain Contract](newton-fixed-domain.md) — qualified public
   Newton configuration, numerical evidence, permitted scope, and next work.

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
- Newton preparation is now qualified with PIC transfer at `0.5`, `0.25`, and
  `0.125 ms` over a common 2 s horizon. All speed/H0 gates pass; adjacent DEM
  RMSE is `0.023/0.031 mm`, and the `1e-4 -> 1e-5` tolerance result is
  identical. The rejected APIC fine-step state was a top-layer transfer mode.
- Newton mechanics are qualified at the frozen action: continuous in-process
  preparation, guided 1.5 kg cylinder loading for `3.595 s`, instantaneous
  removal, and `0.25 s` residual output are finite with full I/O and zero
  analytic particle-center penetration. Native coupling additionally passes a
  `1e-6` prismatic-guide constraint gate. The material is still uncalibrated.
- A 9.375 mm raised-proxy diagnostic at the fixed 100 kPa smoke material passes
  the complete response matrix after Kamino tolerance is aligned with the
  `1e-6` guide gate. Adjacent loaded/residual DEM RMSE is `0.130/0.123` and
  `0.107/0.110 mm`; sinkage differences are `0.130/0.032 mm`.
- The corrected shared A/B objective is `12.189 mm`, versus `14.736 mm` for
  matched Genesis and `8.705 mm` for the calibrated Genesis incumbent.
- The inset is diagnostic, not promotable: a qualified 25 kPa preparation
  improves DEM-only score to `11.207 mm`, but its response puts up to 1,330
  particle centers inside the analytic cylinder by `5.950 mm` and fails the
  guide gate. Stop calibration until support can be corrected without removing
  analytic collision coverage.
- The full-volume `-0.25`-voxel contact-activation diagnostic restores that
  coverage and passes every individual mechanics gate, but only its
  `0.25 -> 0.125 ms` pair passes all convergence gates.  Its
  `0.5 -> 0.25 ms` sinkage difference is `0.975 mm`; calibration remains
  stopped.  See `diagnostics/newton_contact_activation_20260910/`.
- The public stock-contact `7.8125 mm`, `8/16` Newton configuration passes the
  full `0.5/0.25/0.125 ms` response matrix. Its local five-observation study
  currently improves the 100 kPa baseline from `12.698` to `11.610 mm`; this is
  uncalibrated initialization pending an independent best-point replay. See
  [Newton Fixed-Domain Contract](newton-fixed-domain.md).
- Newton state arrays are archival I/O, not qualified restart checkpoints.
  Reconstructing the solver adds `1.157 mm` DEM RMSE; coupled runs therefore
  prepare continuously in-process.

The raw visualization replay is not a replacement confirmation: aggregate
metrics and p99 map agreement were stable, but four residual cells exceeded
the frozen three-cell sparse projection-bin allowance. The authoritative
confirmation remains `r2at0vvb`.

## Environment

Use the existing environment for Genesis instrumentation:

`conda env: chrono_splat`

Use the separately pinned Newton environment for the Newton runner:

`/data/christoa/conda/envs/newton_splat`

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
implementation keeps backend state and evidence separate. `tera_splat_sim`
owns Chrono oracle generation and qualification artifacts.

## Current entry points

```bash
conda run -n chrono_splat python scripts/build_chrono_settled_bed.py --help
conda run -n chrono_splat python scripts/run_chrono_genesis_bridge.py --help
conda run -n chrono_splat python scripts/run_chrono_genesis_bayesopt.py --help
conda run -n chrono_splat python scripts/run_mass_controlled_terrain.py --help
conda run -n chrono_splat python scripts/render_chrono_genesis_pointcloud_dem_comparison.py --help
conda run -n chrono_splat python scripts/diagnose_chrono_genesis_model_form.py --help
/data/christoa/conda/envs/newton_splat/bin/python scripts/run_newton_prepared_bed.py --help
/data/christoa/conda/envs/newton_splat/bin/python scripts/analyze_newton_preparation_convergence.py --help
/data/christoa/conda/envs/newton_splat/bin/python scripts/run_newton_cylinder_diagnostic.py --help
/data/christoa/conda/envs/newton_splat/bin/python scripts/analyze_newton_response_convergence.py --help
```

Do not launch a new study until its target, prepared bed, resolution, seed
policy, and gates match the active run contract.

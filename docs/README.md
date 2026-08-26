# Tera Splat

Prototype for physically grounded terrain Gaussian splatting. The current work
uses Genesis MPM to model mass-controlled rigid-cylinder placement in a
splat-derived sand bed, then compares the result against RealSense terrain DEMs.

## Start Here

Read [Current state](current-state.md) for experiment history and
[Chrono Oracle Run Contract](chrono-oracle-run-contract.md) before starting a
new Chrono-to-Genesis BayesOpt study. The run contract defines the active
oracle, legacy-observation policy, and required stability gate.

## Environment

```text
conda env: chrono_splat
```

CUDA Genesis runs require a shell where the host GPU is visible.

## Repository Boundaries

```text
EDGS input:       ../EDGS/output/point_cloud/iteration_7000/point_cloud.ply
PhysGaussian ref: ../PhysGaussian/
RealSense source: ../lamp/ros2_ws/src/realsense_splat/
```

`tera_splat` owns calibration interpretation, trial contracts, simulation, and
handoff documentation. Keep external capture processing read-only unless a task
explicitly changes it.

## Key Commands

```bash
conda run -n chrono_splat python scripts/view_iteration_7000.py --align-ground-z
conda run -n chrono_splat python scripts/run_mass_controlled_terrain.py --help
conda run -n chrono_splat python scripts/run_mass_controlled_bridge_checks.py --help
```

Generated run evidence belongs in `outputs/`; generated human-readable evidence
belongs in `reports/`.

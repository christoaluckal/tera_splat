# Single-Trial real3 Calibration Report

## Summary

- Trial directory: `/home/moog-2/christo/splatting_stuff/physical/tera_splat/data/single_trial_real3`
- Primary target: center 1 ft DEM at `0.005` m/cell.
- ROI bounds XY: `[-0.1524, 0.1524, -0.1524, 0.1524]` m in the RealSense `bed` frame.
- DEM shape: `[61, 61]`.
- Valid overlap cells: `1038`.
- Calibration rollouts ready: `no`.

The real-data preprocessing layer is implemented. Full Genesis parameter search is blocked until footprint/static-border review, final two-view noise, and the mass-controlled Genesis terrain-runner gates are complete.

## Real Deformation Target

| Metric | Value | Unit |
|---|---:|---|
| `valid_cells` | 1038 | count |
| `valid_area_m2` | 0.02595 | m^2 |
| `mean_change_m` | 0.00313604613 | m |
| `median_change_m` | 0.00347291209 | m |
| `p05_m` | -0.00668277459 | m |
| `p95_m` | 0.012975668 | m |
| `cut_volume_m3` | -3.94610965e-05 | m^3 |
| `fill_volume_m3` | 0.000120841494 | m^3 |
| `net_volume_m3` | 8.13803971e-05 | m^3 |

The normalized files are:

```text
data/single_trial_real3/manifest.yaml
data/single_trial_real3/action.yaml
data/single_trial_real3/processed/S0_height.npz
data/single_trial_real3/processed/S1_height.npz
data/single_trial_real3/processed/delta_h_real.npz
data/single_trial_real3/processed/delta_h_real_corrected.npz
data/single_trial_real3/processed/valid_mask.npz
data/single_trial_real3/processed/noise_stats.json
data/single_trial_real3/processed/scan_correction.json
data/single_trial_real3/processed/scan_correction_footprint_diagnostic.png
```

## Static-Border Scan Correction

A provisional plane bias was fit using only an assumed undeformed outer border. This closes the mechanical preprocessing step, but the static-border assumption still needs visual review before real calibration.

Raw delta stats:

| Metric | Value | Unit |
|---|---:|---|
| `valid_cells` | 1038 | count |
| `valid_area_m2` | 0.02595 | m^2 |
| `mean_change_m` | 0.00313604613 | m |
| `median_change_m` | 0.00347291209 | m |
| `p05_m` | -0.00668277459 | m |
| `p95_m` | 0.012975668 | m |
| `cut_volume_m3` | -3.94610965e-05 | m^3 |
| `fill_volume_m3` | 0.000120841494 | m^3 |
| `net_volume_m3` | 8.13803971e-05 | m^3 |

Plane-corrected delta stats:

| Metric | Value | Unit |
|---|---:|---|
| `valid_cells` | 1038 | count |
| `valid_area_m2` | 0.02595 | m^2 |
| `mean_change_m` | -8.8638169e-05 | m |
| `median_change_m` | 5.24610803e-05 | m |
| `p05_m` | -0.00974401387 | m |
| `p95_m` | 0.00914273364 | m |
| `cut_volume_m3` | -6.48615666e-05 | m^3 |
| `fill_volume_m3` | 6.25614061e-05 | m^3 |
| `net_volume_m3` | -2.30016048e-06 | m^3 |

Coverage:

- Footprint valid fraction: `0.275`.
- Radial-region valid fraction: `0.297`.
- Static-border valid fraction: `0.231`.
- First-contact height, 99th percentile in footprint: `0.0464380514` m.
- Zero-clearance cylinder center z: `0.0718380514` m.
- Diagnostic PNG: `data/single_trial_real3/processed/scan_correction_footprint_diagnostic.png`.

## Mass-Controlled Genesis Checks

- Free-fall status: `pass`.
- Runtime mass after override: `1.5` kg.
- Fitted vertical acceleration: `-9.80977783` m/s^2.
- Gravity relative error: `2.26e-05`.
- Runtime inertia diagonal: `[0.002322323984375, 0.002322323984375, 0.003999487968750001]` kg m^2.
- Check artifact: `outputs/mass_controlled_bridge_checks/free_fall_report.json`.

This validates a dynamic cylinder under gravity and runtime mass/inertia setup. It does not validate two-way rigid-MPM terrain contact.

## Short Terrain Gravity Smoke

| Mass kg | Sinkage m | Under-disk mean dz m | Duration s | Output |
|---:|---:|---:|---:|---|
| 0.75 | 0.00132496872 | -0.000905926281 | 0.04 | `outputs/mass_controlled_bridge_checks/gravity_terrain_smoke_m0p75` |
| 1.5 | 0.00242455521 | -0.00137576309 | 0.04 | `outputs/mass_controlled_bridge_checks/gravity_terrain_smoke` |
| 3 | 0.00399621048 | -0.00202284451 | 0.04 | `outputs/mass_controlled_bridge_checks/gravity_terrain_smoke_m3p0` |

- Short-run mass monotonicity: `pass`.

This is only a short `0.04 s` smoke using the existing gravity control path. It shows mass affects sinkage and terrain particles move, but it does not prove loaded equilibrium, removal, no-cylinder drift, or complete state restoration.

## Mass-Controlled Terrain Runner Smoke

- Output: `outputs/mass_controlled_bridge_checks/mass_controlled_terrain_smoke_cpu_capped`.
- Loaded termination: `timeout` after `0.02` s.
- Loaded depth: `0.00160224953` m.
- Removal capped: `True`.
- Post-removal termination: `timeout` after `0.01` s.
- Final depth relative to initial center: `0.00140221634` m.

This validates the load/remove/post-settle phase machine and artifact writing. It is intentionally short and capped, so it does not close the equilibrium/removal validation gate.

## Longer CUDA Mass-Controlled Rollout

- Output: `outputs/mass_controlled_bridge_checks/mass_controlled_terrain_cuda_longer`.
- Loaded termination: `timeout` after `0.25` s.
- Loaded depth: `0.00289781609` m.
- Removal capped: `False`.
- Post-removal termination: `equilibrium` after `0.02` s.
- Final under-disk mean dz: `-0.00130574871` m.
- Total wall time: `55.933` s.

This proves the uncapped physical lift path runs on CUDA. Loaded equilibrium still timed out under the current `0.25 s` limit.

## Extended CUDA Loaded-Settling Check

- Output: `outputs/mass_controlled_bridge_checks/mass_controlled_terrain_cuda_loaded1s`.
- Loaded termination: `timeout` after `1.0` s.
- Loaded depth: `0.00289662399` m.
- Final loaded cylinder speed: `0.000292996793` m/s.
- Final local p99 particle speed: `0.000672453374` m/s.
- Removal capped: `False`.
- Post-removal termination: `equilibrium` after `0.02` s.
- Final under-disk mean dz: `-0.00130561076` m.
- Total wall time: `66.307` s.

The extra loaded time did not materially change penetration, but the local p99 particle-speed criterion remained above its `0.0005 m/s` threshold. The runner therefore cannot yet claim loaded equilibrium; threshold sensitivity and a settled mass-monotonicity check remain required.

## Loaded-Settling Percentile Diagnostic

- Output: `outputs/mass_controlled_bridge_checks/mass_controlled_terrain_cuda_settling_diagnostic_1s`.
- Trailing depth window: `0.1` s.
- Penetration drift in that window: `0` m.
- Final local p50/p90/p95/p99 particle speeds: `5.21588663e-05`, `0.000105686333`, `0.000195137123`, `0.000691926922` m/s.

The p95 statistic and cylinder speed satisfy the current `0.0005 m/s` threshold in the stable-depth tail, while p99 does not. This is evidence for a threshold-sensitivity study across masses, not a basis for changing the protocol from this single run.

## Scan/Registration Noise Proxy

- ICP final RMSE: `0.00880404522` m.
- Direct-vs-ICP delta median abs difference: `0.000597045818` m.
- Direct-vs-ICP delta p95 abs difference: `0.00166503993` m.
- Provisional Huber delta: `0.00880404522` m.

This is only a proxy. Replace it with two-view disagreement and static-border residuals before final calibration.

## Distribution Diagnostics

- Minimum observed delta: `-0.0389720528` m.
- Maximum observed delta: `0.0395353757` m.
- 1st percentile: `-0.0305483876` m.
- 99th percentile: `0.0314183758` m.

## Calibration Status

Implemented now:

- Real3 DEM normalization into the planned single-trial data contract.
- Real deformation target `delta_h_real` and valid mask generation.
- Static-border plane correction and footprint coverage diagnostics.
- Provisional noise statistics.
- Report generation.
- Corrected cylinder action template: `0.14605 m` is diameter and `0.073025 m` is radius.

Blocked before Genesis search:

- `two-view height exports/noise estimate`
- `two-way rigid-MPM contact check`
- `settled/equilibrium mass monotonicity check`
- `loaded settling termination check`
- `post-removal settling termination check`
- `initial simulated S0 projection/footprint check`
- `complete MPM state restore check`
- `no-cylinder drift check`
- `synthetic 3x3 recovery check`

Once those gates pass, the next implementation step is a coarse `8 x 8` grid over:

```text
log10_E in [4, 7]
phi_deg in [15, 45]
```

The forward model must use mass-controlled gravitational cylinder release, not prescribed target-depth indentation, and restore the same settled base before every candidate.

## Source RealSense Artifacts

```text
../lamp/ros2_ws/src/realsense_splat/episodes/real3_compare_metrics_3tag/center_1ft_fine_dem/
../lamp/ros2_ws/src/realsense_splat/episodes/real3_compare_metrics_3tag/real3_dem_report_3tag.json
```

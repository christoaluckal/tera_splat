# Single-Trial real3 Calibration Report

## Summary

- Trial directory: `/home/moog-2/christo/splatting_stuff/physical/tera_splat/data/single_trial_real3`
- Primary target: center 1 ft DEM at `0.005` m/cell.
- ROI bounds XY: `[-0.1524, 0.1524, -0.1524, 0.1524]` m in the RealSense `bed` frame.
- DEM shape: `[61, 61]`.
- Valid overlap cells: `1038`.
- Calibration rollouts ready: `no`.

The real-data preprocessing layer is implemented. Full Genesis parameter search is blocked until scan correction, footprint verification, and the mass-controlled Genesis runner gates are complete.

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
data/single_trial_real3/processed/valid_mask.npz
data/single_trial_real3/processed/noise_stats.json
```

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
- Provisional noise statistics.
- Report generation.
- Corrected cylinder action template: `0.14605 m` is diameter and `0.073025 m` is radius.

Blocked before Genesis search:

- `center footprint overlay verification`
- `static-border scan bias correction`
- `two-view height exports/noise estimate`
- `Genesis mass-controlled action mode`
- `mass/inertia application check`
- `free-fall gravity check`
- `two-way rigid-MPM contact check`
- `mass monotonicity check`
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

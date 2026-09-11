# Newton versus Genesis backend A/B

Run date: 2026-09-06; report regenerated 2026-09-08.

## Result

The controlled same-material comparison favors Newton on the frozen DEM
objective, while the best currently calibrated end-to-end pipeline remains
Genesis. This is not contradictory: Newton has better numerical evidence but
has not yet had a backend-specific material calibration.

All scored cases use the same Chrono episode, `0.5 ms` MPM timestep, `5 mm`
particles, `15.625 mm` grid/voxel scale, `3.595 s` loaded sample, `0.25 s`
fixed residual sample, 14,161-cell mask, and 673-cell analytic cylinder
footprint. The common objective is

`loaded all-cell RMSE + 0.5 * residual footprint RMSE`.

| case | H0 RMSE | loaded RMSE | residual footprint RMSE | objective |
| --- | ---: | ---: | ---: | ---: |
| Newton, 100 kPa smoke material | 0.603 mm | 3.778 mm | 17.721 mm | **12.638 mm** |
| Genesis, nominally matched 100 kPa material | 0.131 mm | 4.316 mm | 20.840 mm | 14.736 mm |
| Genesis calibrated incumbent, 20.43 kPa | 0.876 mm | **1.864 mm** | **13.682 mm** | **8.705 mm** |

At the matched 100 kPa point Newton improves the objective by 2.098 mm
(14.2%) relative to Genesis. Genesis completes the comparable three-stage
pipeline in 315.83 s external wall time versus 376.33 s for Newton, about
16.1% faster. These are single deterministic executions on the same GPU, not
a runtime benchmark with repeated confidence intervals.

The cylinder and transient evidence is mixed. Newton ends loading nearly
stationary and its 0.25 s residual particle p99 speed is 0.163 mm/s, versus
6.434 mm/s for matched Genesis. Genesis produces more cylinder descent at the
same material point (14.148 mm versus Newton's 10.205 mm center drop), but both
underpredict the 34.270 mm Chrono sinkage. Newton's cylinder bottom remains
9.795 mm above the analytic initial surface, the already diagnosed broad-S2
collider support gap, so its better map objective is not yet a physical-contact
validation.

The reverse crossover was attempted by transferring the Genesis incumbent
values to Newton: `E=20,432.828 Pa`, `nu=0.101894536`, density `1000 kg/m^3`,
and explicit Newton friction `tan(14.727053 deg)=0.262849811`. Newton's full
2 s preparation reached the speed gate but failed the frozen H0 gate at
9.809 mm RMSE and 10.241 mm maximum error, versus limits of 5 and 10 mm. It
was therefore correctly rejected before cylinder contact. The Genesis optimum
cannot be copied into Newton as if the two sand laws were parameter-identical.

## Interpretation

- **Best solver foundation:** Newton. Its native coupled response maps are
  much more timestep-consistent, its matched-material score is better, and
  its endpoint dynamics are quieter.
- **Best result available today:** Genesis. Its calibrated incumbent is still
  substantially closer to the Chrono target under the frozen objective.
- **Decision:** continue the Newton branch, but diagnose the collider-support
  gap before calibrating Newton. Do not claim Newton predictive superiority
  from this A/B, and do not transfer Genesis parameters directly.

`response_maps.png` compares the Chrono target and all three simulation
responses. `error_maps.png` shows simulation-minus-Chrono errors on one shared
color scale. Exact values and paths are in `cases.csv` and `summary.json`;
`analyze.py` regenerates all four artifacts.

Raw crossover outputs are under
`outputs/validity_experiment/backend_ab_20260906/`. The retained Newton smoke
response and Genesis incumbent remain in their original canonical output
directories referenced by `summary.json`.

# RealSense Instrumentation And Real6 Trial

Last reviewed: 2026-08-07

This is the canonical `tera_splat` handoff for RealSense-derived calibration
inputs. `../lamp/ros2_ws/src/realsense_splat` remains the source package, but
new analysis and trial-contract decisions belong here.

## Coordinate And Capture Convention

```text
world frame: bed
camera frame: camera_color_optical_frame
depth scale: 0.001 m per unit
tag map: ../lamp/ros2_ws/src/realsense_splat/config/real3_tag_map.yaml
tag centers: (+/-0.3048, +/-0.3048) m
```

The tag map is an approximate 24 x 24 inch layout. Real3 and Real4/5/6 were
processed with that same map, so their nominal XY coordinates are compatible.
Treat absolute registration as provisional until the physical tag geometry is
independently measured and validated.

## Source Dataset Inventory

### Real3

Current normalized trial:

```text
data/single_trial_real3/
reports/single_trial_real3_report.md
```

External source:

```text
../lamp/ros2_ws/src/realsense_splat/episodes/real3_compare_metrics_3tag/
```

Real3 has the current `1.5 kg`, `0.14605 m` diameter cylinder action contract.
Its primary calibration target is the static-border corrected center 1 ft DEM.

### Real4/5/6 Static-Pose Set

External source root:

```text
../lamp/ros2_ws/src/realsense_splat/episodes/real456_static_metrics/
```

Each source PLY is an ASCII, metric `x,y,z,rgb` rasterized median-height DEM at
`0.005 m` cells. Available raw pairs are:

```text
real4_pre  -> real4_post
real5_pre  -> real5_during -> real5_after
real6_pre  -> real6_post
```

Relevant source evidence:

```text
README.md, section "Real4/Real5/Real6 Static-Pose DEMs"
real456_static_metrics_report.json
force_application_location_report.json
force_centered_comparisons/
icp_registered_crops/
```

The static-pose outputs use mostly three-tag frames. They are useful
tag-frame/static-view measurements, but not independently validated absolute
bed geometry.

## Real6 Trial Contract

Use the following contract for all new Real6 work:

```text
initial surface S0: real6_pre/dem_points_0.005m.ply
terminal surface S1: real6_post/dem_points_0.005m.ply
real target sign: S1 - S0; negative means depression
tool: same cylinder geometry as Real3
diameter: 0.14605 m
radius: 0.073025 m
height: 0.0508 m
mass: 3.0 kg
nominal center: [0.0135730566, 0.0362158050] m in bed XY
```

The nominal center was inferred from the Real5 during-load height-change
feature. It is a protocol-sensitivity input, not known ground truth. Run the
planned `[-0.10, 0.00, +0.10] m` XY offsets separately from material fitting.

Derived rigid-body values for the same cylinder at `3.0 kg`:

```text
equivalent uniform density: 3525.044 kg/m^3
Ixx = Iyy: 0.004644648 kg m^2
Izz:       0.007998976 kg m^2
```

The Real6 source has pre/post views only. Its action configuration must still
record confirmed dwell, lift speed, and post-lift wait. Do not use the `5 kg`,
`0.10 m` example in `realsense_splat/plan.md` as Real6 metadata.

## Initial Real6 Measurement Analysis

The initial analysis used the raw bed-frame Real6 PLY pair, a force-centered
1 ft ROI, cylinder radius `0.073025 m`, and a Real3-style correction: fit a
plane in the outer `25 mm` border while excluding the cylinder footprint plus
`30 mm`.

```text
common pre/post cells:              57,295
force-centered ROI common cells:     2,645
footprint coverage:                  504 / about 670 cells (75.2%)
corrected footprint median dz:      -1.044 mm
corrected footprint mean dz:        -1.585 mm
corrected footprint p05 / p95:      -5.345 / +1.529 mm
covered-footprint net volume:       -1.997e-5 m^3
corrected annulus p05 / p95:        -0.692 / +0.771 mm
```

The observed depression is plausible for the stated 3 kg action but only
modestly separated from the measurement scale. It is a provisional target,
not yet a defensible material-fit observation.

The source package's Real6 ICP crop reports `1.0` fitness and `1.413 mm` final
RMSE. Do not use an ICP transform fit through the changed footprint as the
calibration registration; use a documented stable-region convention.

## Integration Boundary

The current `scripts/preprocess_single_trial_real3.py` is source-specific. It
loads precomputed Real3 NPY products from
`real3_compare_metrics_3tag/center_1ft_fine_dem/`, so it cannot directly
consume an arbitrary Real6 PLY pair.

Implement a separate Real6 adapter that:

1. Reads the Real6 pre/post PLYs or their companion `dem_0.005m.npy` arrays.
2. Rasterizes/crops a center-relative ROI on the fixed 5 mm grid.
3. Writes `S0_height.npz`, `S1_height.npz`, `delta_h_real.npz`, valid masks,
   scan-correction metadata, and diagnostics in the existing single-trial
   contract.
4. Keeps native bed-frame/static-region registration separate from optional ICP
   visualization products.
5. Encodes the 3 kg action and center-offset protocol in a Real6 action file.

Prefer the companion DEM arrays for reproducible raster values. Keep the PLYs
for inspection and source provenance.

## Gates Before A Real6 Full Sweep

1. Confirm the Real6 dwell/removal/post-settle protocol and record it in the
   action contract.
2. Implement and validate the Real6 source adapter and stable-region
   registration convention.
3. Estimate Real6 noise from independent frame subsets or static regions;
   annulus spread alone is only a provisional proxy.
4. Register or construct the MPM initial bed against Real6 `S0`, then project
   simulated `S0` onto the exact Real6 grid and verify the footprint overlay.
5. Repeat dynamic rigid-body mass/inertia/free-fall checks at `3.0 kg`.
6. Validate the mass-controlled 3 kg terrain release, loaded-equilibrium rule,
   uncapped lift, post-removal settle, no-cylinder drift, and deterministic
   state reconstruction.
7. Run synthetic recovery with the Real6 target grid and loss.
8. Run the material grid at the nominal center, then the 3 x 3 center grid as
   a separate protocol-sensitivity study.

Do not merge Real3 and Real6 measurements as replicate trials. They have
different mass, source capture pair, and unresolved registration/noise behavior.

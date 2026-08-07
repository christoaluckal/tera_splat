# Mass-Controlled Bridge Findings

Last updated: 2026-08-06

This document records the bridge tests run after adopting the mass-controlled
cylinder interpretation for `real3`.

## Corrected Real Target

The calibration target is now the static-border corrected residual:

```text
data/single_trial_real3/processed/delta_h_real_corrected.npz
```

Supporting artifacts:

```text
data/single_trial_real3/processed/scan_correction.json
data/single_trial_real3/processed/scan_correction_footprint_diagnostic.png
```

Key scan-correction results:

```text
raw median delta_h:              +0.00347291209 m
plane-corrected median delta_h: +0.0000524610803 m
plane-corrected net volume:     -2.30016048e-06 m^3
footprint valid fraction:        0.275
radial valid fraction:           0.297
static-border valid fraction:    0.231
```

Interpretation: the raw pre/post DEM had a broad vertical/tilt bias. The
static-border plane correction removes most of that global offset. The corrected
target is suitable for runner development, but the low footprint/static-border
coverage means final calibration still needs review and a better two-view noise
estimate.

## Cylinder Metadata

Correct cylinder geometry:

```text
diameter: 0.14605 m
radius:   0.073025 m
height:   0.0508 m
mass:     1.5 kg
```

`0.14605 m` is the diameter, not the radius.

Derived values used by the action contract:

```text
equivalent uniform density: 1762.522 kg/m^3
Ixx = Iyy: 0.002322324 kg m^2
Izz:       0.003999488 kg m^2
```

## Free-Fall And Mass Check

Command:

```bash
conda run -n tsplat python scripts/run_mass_controlled_bridge_checks.py \
  --backend cpu \
  --steps 160 \
  --dt 0.001
```

Output:

```text
outputs/mass_controlled_bridge_checks/free_fall_report.json
```

Result:

```text
status: pass
runtime mass: 1.5 kg
fitted acceleration z: -9.80977783 m/s^2
gravity relative error: 2.26e-05
runtime inertia diag: [0.002322323984375, 0.002322323984375, 0.003999487968750001]
```

Interpretation: Genesis can represent the corrected cylinder as a dynamic rigid
body with the intended mass/inertia under gravity.

## Short Terrain Gravity Smokes

Existing gravity-control path, `0.04 s`, CPU:

```text
outputs/mass_controlled_bridge_checks/gravity_terrain_smoke_m0p75
outputs/mass_controlled_bridge_checks/gravity_terrain_smoke
outputs/mass_controlled_bridge_checks/gravity_terrain_smoke_m3p0
```

Observed sinkage:

```text
0.75 kg -> 0.00132496872 m
1.50 kg -> 0.00242455521 m
3.00 kg -> 0.00399621048 m
```

Interpretation: short-run sinkage is monotonic with mass, and terrain particles
move under the disk. This is useful evidence that mass affects the coupled
response, but it does not prove loaded equilibrium or removal behavior.

## Mass-Controlled Terrain Runner Smoke

New runner:

```text
scripts/run_mass_controlled_terrain.py
```

Capped CPU smoke output:

```text
outputs/mass_controlled_bridge_checks/mass_controlled_terrain_smoke_cpu_capped
```

Result:

```text
loaded_termination_reason: timeout
loaded_depth: 0.00160224953 m
removal_capped: True
post_removal_termination_reason: timeout
final_depth: 0.00140221634 m
complete_state_restore: False
```

Interpretation: the load, removal, post-removal phase machine and artifact
writing work. The smoke was intentionally short and capped; it does not close
the equilibrium/removal gate.

## Remaining Gates Before Real Sweep

The real `log10_E` / `phi_deg` sweep is still blocked by:

- final two-view noise estimate
- independent review of footprint/static-border assumptions
- non-capped mass-controlled rollout reaching loaded equilibrium
- full removal and post-removal settling validation
- settled/equilibrium mass monotonicity
- initial simulated `S0` projection to the RealSense DEM grid
- complete MPM state restore or deterministic reconstruction beyond PLY
  positions
- no-cylinder drift characterization or subtraction
- synthetic `3 x 3` recovery

The remaining immediate dynamics test is settling-threshold sensitivity with
the same uncapped CUDA removal path, followed by settled mass monotonicity.

## Longer CUDA Mass-Controlled Rollout

Command:

```bash
conda run -n tsplat python scripts/run_mass_controlled_terrain.py \
  --backend cuda \
  --loaded-max-time 0.25 \
  --post-max-time 0.05 \
  --required-duration 0.02 \
  --dt 0.0005 \
  --save-every 500 \
  --output-dir outputs/mass_controlled_bridge_checks/mass_controlled_terrain_cuda_longer
```

Output:

```text
outputs/mass_controlled_bridge_checks/mass_controlled_terrain_cuda_longer
```

Result:

```text
backend: cuda
particles: 48430
loaded_termination_reason: timeout
loaded_steps: 500
loaded_duration: 0.25 s
loaded_depth: 0.00289781609 m
removal_capped: False
removal_steps: 5160
post_removal_termination_reason: equilibrium
post_removal_steps: 40
post_removal_duration: 0.02 s
final_depth: -0.00999991379 m
final_under_mean_dz: -0.00130574871 m
total_wall_seconds: 55.9334
```

Interpretation:

- The non-capped physical lift path runs on CUDA and writes the expected
  artifacts.
- The cylinder sinks about `2.90 mm` during the `0.25 s` loaded phase.
- Loaded equilibrium is not reached under the current threshold within `0.25 s`;
  this remains an open gate.
- Removal completed without a cap at the documented `5 mm/s` speed.
- Post-removal equilibrium was detected in `0.02 s`.
- The final residual deformation under the disk is about `-1.31 mm` mean dz
  against the initial simulation surface.

## Extended CUDA Loaded-Settling Check

Output: `outputs/mass_controlled_bridge_checks/mass_controlled_terrain_cuda_loaded1s`

```text
backend: cuda
particles: 48430
loaded_termination_reason: timeout
loaded_steps: 2000
loaded_duration: 1.0 s
loaded_depth: 0.00289662399 m
final loaded cylinder speed: 0.000292996793 m/s
final local p99 particle speed: 0.000672453374 m/s
removal_capped: False
removal_steps: 5159
post_removal_termination_reason: equilibrium
post_removal_duration: 0.02 s
final_under_mean_dz: -0.00130561076 m
total_wall_seconds: 66.3075
```

The `1.0 s` penetration differs from the `0.25 s` result by only about `1.2 um`,
so cylinder penetration has effectively stabilized. However, the local
99th-percentile particle speed is `0.672 mm/s`, above the configured `0.5 mm/s`
threshold, while cylinder speed is below threshold at `0.293 mm/s`. The loaded
phase therefore correctly times out under the configured rule.

This does not establish physical loaded equilibrium. The next gap is
settling-threshold sensitivity plus `0.75`, `1.5`, and `3.0 kg` cases under the
same loaded/post-removal criteria; that is also the settled mass-monotonicity
validation.

## Loaded-Settling Percentile Diagnostic

The runner now writes `loaded_settling_diagnostic.csv` with p50, p90, p95, and
p99 local particle speeds at every loaded-phase step, plus trailing penetration
drift metrics in `run_metrics.csv`.

Baseline output:

```text
outputs/mass_controlled_bridge_checks/mass_controlled_terrain_cuda_settling_diagnostic_1s
```

For the final `0.1 s` of the `1.5 kg`, `1.0 s` loaded run:

```text
penetration drift: 0 m at stored float32 precision
cylinder speed:    0.289 to 0.324 mm/s
local p50 speed:   0.050 to 0.054 mm/s
local p90 speed:   0.106 to 0.113 mm/s
local p95 speed:   0.188 to 0.205 mm/s
local p99 speed:   0.670 to 0.720 mm/s
```

The current `p99 < 0.5 mm/s` criterion never passes, even though penetration
is stable. In contrast, p95 and cylinder speed remain below `0.5 mm/s` for the
tail of this run. Treat p95 as a candidate diagnostic threshold only: it must
be checked for `0.75`, `1.5`, and `3.0 kg` with the same window and required
duration before the action contract changes.

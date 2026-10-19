# Static 35 mm proxy qualification — 2026-10-09

> Historical/quarantined evidence. This report may be read to understand the
> earlier strict-gate failure, but its artifacts and measurements are not
> admissible in the fresh 2026-10-17 campaign. See the
> [fresh hierarchical Phase 0 protocol](fresh-hierarchical-phase0-20261017.md).

## Decision

The initial static proxy sentinel is **not mechanics-qualified** in the
historical public Newton domain. Do not expand the 15-case position/load
matrix, fit material parameters, or train a residual until the 35 mm numerical
and contact domain passes its own qualification.

Chrono accepted the lowest-load center action. The unchanged 100 kPa Newton
control passed preparation, finite-state, guide, support, and final loaded
penetration checks, but failed the trajectory-wide strict zero
particle-center penetration gate.

## Frozen initial contract

| Item | Value |
| --- | --- |
| load model | static gravity-equivalent mass; dynamic loads excluded |
| proxy | 35 mm radius, 35 mm height, vertically guided cylinder |
| robot mass | 12.5 kg |
| planned loads | 30.656, 45.984, 61.313 N; 3.125, 4.6875, 6.25 kg equivalent |
| planned pressures | 7.966, 11.949, 15.932 kPa |
| planned positions | center and x/y offsets of plus or minus 100 mm |
| Chrono | 5 mm SCM grid, 0.6 m square pit, accepted speed hold, 0.25 s recovery |
| Newton baseline | 100 kPa, nu 0.2, friction coefficient 0.68 |
| Newton numerical setting | 7.8125 mm, PIC/PIC, P0/S2/Q1, 0.25 ms, stock contact, 8/16 |
| sentinel | `center_f031n` |

The complete plan contains 15 position/load cells. The lowest-load center cell
is an expansion sentinel: a failure prevents the other cells and convergence
anchor from launching.

The frozen contract is
[`configs/static_proxy_35mm_qualification.json`](../../configs/static_proxy_35mm_qualification.json).
The resumable runner is
[`scripts/run_static_proxy_qualification.py`](../../scripts/run_static_proxy_qualification.py).

## Chrono sentinel

Chrono accepted the 3.125 kg, 30.656 N action at `0.349 s`:

| Quantity | Result |
| --- | ---: |
| nominal pressure | 7.966 kPa |
| final linear speed | 1.057 mm/s |
| valid cells | 14,161 |
| footprint cells | 147 |
| valid-interior peak depression | 16.392 mm |
| footprint mean depression | 15.360 mm |

The legacy episode metrics writer also saw a `231.827 mm` negative delta on
the excluded one-cell SCM boundary ring. It did not occur on the valid mask
and did not enter the paired comparison. The writer now reports deformation
over the declared valid interior and retains all-cell minima as diagnostics.

## Newton sentinel

The shared full-bed preparation passed. Its two-second pre-settle ended at
`0.00147 mm/s` particle p99 speed. The continuous response then produced:

| Gate or metric | Result |
| --- | ---: |
| finite state | pass |
| preparation | pass |
| guide | pass |
| final loaded penetration | 0 centers; pass |
| trajectory-wide penetration | 8 centers, maximum 0.003759 mm; **fail** |
| loaded sinkage | 19.066 mm |
| loaded vertical speed at Chrono time | -7.786 mm/s |
| loaded Chrono RMSE | 0.835 mm, diagnostic only |
| residual Chrono RMSE | 0.683 mm, diagnostic only |
| response wall time | 2,573.95 s |

The small magnitude does not waive the frozen gate. Because the response is
mechanics-invalid, the RMSE values are not a model score or optimizer
observation. The result also shows that matching Chrono's early accepted time
does not imply that Newton has reached a comparable rigid-body speed.

## Stop boundary and next permitted diagnostic

- Do not launch the remaining 14 screen cells.
- Do not run material fitting or residual learning.
- First rerun only the same static sentinel at the declared `0.5`, `0.25`, and
  `0.125 ms` levels to establish whether the penetration failure converges
  with time resolution.
- If the strict failure persists or does not converge monotonically, test a
  finer public spatial/contact discretization for the 35 mm geometry before
  changing material controls.
- Keep stock contact, the analytic proxy, the zero-inset geometry, and all
  mechanics gates unchanged during that diagnosis.

## Canonical artifacts

- Plan and machine-readable status:
  `outputs/validity_experiment/newton/static_proxy_35mm_20261009/`
- Chrono episode:
  `../tera_splat_sim/validity_experiment/chrono_episodes/static_proxy_35mm_20261009/center_f031n/`
- Newton response:
  `outputs/validity_experiment/newton/static_proxy_35mm_20261009/responses/center_f031n/dt0p25ms/`

Claim boundary: this is one static, lowest-load, center-position sentinel. It
rejects the current 35 mm Newton domain; it does not characterize higher
loads, other positions, dynamic impacts, calibrated material fidelity, or
planner performance.

# Newton lateral-transfer holdout — 2026-10-01

This diagnostic records the A5 spatial-transfer action before the Newton
comparisons complete.

## Chrono oracle

- Episode: `A5_oracle_mass1p625kg_lateral_x50mm_gate6mm_v1`
- Mass: 1.625 kg; center `(x=+0.05 m, y=0.0 m)`
- Loaded termination: `converged_speed_hold`
- Accepted loaded time: 0.816 s
- Loaded sinkage: 22.188591 mm
- Residual duration: 0.25 s
- Support: 121x121, 14,161 valid cells
- Initial terrain and support mask are bitwise identical to A4
- Initial, loaded, and residual maps are finite on support

This is a spatial-transfer holdout: geometry, mass, guide, SCM grid, soil,
and numerical settings match the incumbent family; only the lateral action
center differs from the guided +5 mm-y training/holdout actions.

Newton incumbent and unchanged-control results will be appended after the
strict trajectory-wide penetration and guide gates complete.

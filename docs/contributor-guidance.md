# Agent Handoff

[`current-state.md`](current-state.md) is the sole live handoff and planning document. Read it
before editing code, data contracts, configurations, or reports.

## Working Rules

- Work from `/home/moog-2/christo/splatting_stuff/physical/Chrono/tera_splat`.
- Use the `chrono_splat` conda environment.
- Preserve user changes and generated evidence. Do not reset or delete outputs
  unless explicitly asked.
- Keep manual source edits scoped and use `apply_patch`.
- Use `rg` for code/document discovery.
- Run focused verification after code changes and record material validation
  results in `docs/current-state.md` in the same change.

## Source Boundaries

```text
EDGS splat:       ../EDGS/
PhysGaussian:     ../PhysGaussian/
RealSense source: ../lamp/ros2_ws/src/realsense_splat/
```

Treat the external repositories as source provenance. Calibration decisions,
RealSense trial contracts, and simulation status belong in this repository.

## Non-Negotiable Physics Rules

- The real action is mass-controlled gravitational cylinder placement.
- Penetration is a simulation output; do not substitute target-depth loading.
- `0.14605 m` is cylinder diameter, so radius is `0.073025 m`.
- Use a settled volumetric terrain bed, not a surface-only particle shell.
- Do not fit against a real DEM until initial frame, grid, surface, and
  footprint alignment are verified.
- Treat center offsets as protocol sensitivity, not free material parameters.

## Current Entry Points

```bash
conda run -n chrono_splat python scripts/view_iteration_7000.py --align-ground-z
conda run -n chrono_splat python scripts/view_particle_ply.py \
  assets/base_settled_stiff_mid/particles_initial_mpm.ply --point-size 0.003
conda run -n chrono_splat python scripts/run_mass_controlled_terrain.py --help
conda run -n chrono_splat python scripts/run_mass_controlled_bridge_checks.py --help
```

Do not create parallel status documents. Update `docs/current-state.md`; retain
specific generated-run evidence under `reports/` or `outputs/`.

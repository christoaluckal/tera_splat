# Project Handoff

Last updated: 2026-07-06

## Project Goal

This repository is a prototype for contact-conditioned terrain Gaussian
splatting. The target query is:

```text
Given a Gaussian-splat terrain map, what would the sand terrain look like after
a localized shallow surface load is applied at location X?
```

The current milestone is not full robot-terrain contact. The immediate goal is
a stable, inspectable pipeline that can load a terrain splat scene, convert a
local sand surface into MPM particles, run a shallow deformation simulation, and
eventually transfer particle displacement back into renderable Gaussians.

Primary docs:

- `README.md`: current commands, run recipes, and long-form roadmap.
- `docs/README.md`: phase reading order and global success criteria.
- `docs/00_physgaussian_notes.md`: relevant PhysGaussian implementation notes.
- `docs/04_phase_mpm_pressure_patch.md`: current MPM pressure-patch phase.
- `docs/11_current_solver_status.md`: latest solver status and observed runs.

## Current Scene And Assumptions

- Working scene:

```text
../EDGS/output/point_cloud/iteration_7000/point_cloud.ply
```

- Use conda environment: `tsplat`.
- First-pass material assumption: every retained Gaussian is sand.
- The rigid pole is intentionally ignored until viewing, extraction, and
  baseline deformation are stable.
- Default axis transform is `opencv-to-zup`, mapping:

```text
(x, y, z) -> (x, z, -y)
```

- The retained splat count in the current scene is 256,210.
- A 1/10 sample is about 25,621 input particles; with
  `--trim-quantile 0.005`, the current sample keeps 24,921 particles.

## Environment Notes

- CUDA is visible outside the managed sandbox on an RTX 3060 Ti.
- Inside the managed sandbox, CUDA is not visible to `nvidia-smi`, PyTorch, or
  Warp.
- Run CUDA solver jobs from an unsandboxed shell/session.
- Genesis compile/cache paths are redirected under `outputs/.cache` by
  `scripts/run_genesis_ground_plane_solver.py`.

Useful checks:

```bash
nvidia-smi
conda run -n tsplat python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

## Working Pieces

- `scripts/view_iteration_7000.py` loads the EDGS iteration-7000 scene in Viser.
- `--align-ground-z` fits the dominant sand plane and rotates its normal to
  world `+Z`; the same rotation is applied to centers and covariances.
- `scripts/particle_io.py` is the shared PLY-to-particle path for both solver
  backends. It currently builds a three-entity initial state: splat-derived
  surface particles, multilayer regular-grid subsurface support, and a ground
  plane.
- `scripts/test_ply_to_particles.py` validates conversion, writes
  `particles_initial_mpm.ply`, round-trips it, and reports bounds/ground stats.
- `scripts/run_ground_plane_solver.py --dry-run` creates initial PhysGaussian
  MPM particles and ground-plane metadata.
- `scripts/run_genesis_ground_plane_solver.py` imports the same particles into
  Genesis MPM and writes `simulation_ply/sim_*.ply`.
- `scripts/check_solver_displacement.py` reports first-to-last frame motion.
- `scripts/view_particle_ply.py` opens a single particle PLY in Viser.
- `scripts/view_solver_animation.py` plays solver PLY output in Viser.
- `scripts/render_solver_video.py` renders solver PLY sequences to MP4 without
  loading thousands of frames into Viser.
- `scripts/generate_ground_plane_preview.py` is a non-MPM viewer/debug fallback.

## Basic Commands

Inspect the source scene:

```bash
conda run -n tsplat python scripts/view_iteration_7000.py
```

Open Viser:

```text
http://localhost:8080
```

Run a non-server load check:

```bash
conda run -n tsplat python scripts/view_iteration_7000.py --dry-run
```

Validate PLY-to-particle conversion:

```bash
conda run -n tsplat python scripts/test_ply_to_particles.py \
  --max-particles 1000 \
  --output-dir outputs/ply_particle_test_1k
```

Create a PhysGaussian/Warp MPM setup without running Warp:

```bash
conda run -n tsplat python scripts/run_ground_plane_solver.py --dry-run
```

Check displacement after a solver run:

```bash
conda run -n tsplat python scripts/check_solver_displacement.py \
  outputs/cuda_soft_1k_s10
```

View one particle PLY:

```bash
conda run -n tsplat python scripts/view_particle_ply.py \
  outputs/ply_particle_test_10pct_trim005_min_ground/particles_initial_mpm.ply \
  --point-size 0.003 \
  --port 8082
```

## Current Initial PLY Suite

The current initial-state model is:

1. initial surface from retained splat centers,
2. regular XY-grid subsurface layers below the local surface,
3. ground plane just below the lowest subsurface layer.

The subsurface is no longer a cloned lower copy of the surface and no longer a
full bottom-up filled volume. The raw splat centers are used to estimate the
terrain height field, but `particles_surface_mpm.ply` is now an interpolated
surface cap rather than the raw splat points. This avoids buried raw splat
samples appearing as columns in the surface component.

The generator builds regular XY grids, writes the visible surface cap at the
interpolated height field, then creates subsurface layers at explicit depths.
Each subsurface layer gets XY shift/noise, then its height is clamped below both
the splat-derived height and the visible cap height at that jittered XY.

Current standard arguments:

```text
--center-radius 1.0
--subsurface-depth 0.2
--subsurface-xy-jitter 0.45
```

`--subsurface-spacing-mpm` controls XY grid spacing. If
`--subsurface-layer-depths` is omitted it also controls depth-layer spacing.
The current preferred initialization uses explicit layer depths
`0.05,0.10,0.15,0.20`.

Generated suite:

```text
outputs/initial_multilayer_suite/
  README.md
  summary.csv
  spacing008/
  spacing004/
  spacing002/
  spacing001/
```

Current suite counts:

```text
case        spacing_mpm  layers  surface  subsurface  total
spacing008 0.08         2       5,393    684         6,077
spacing004 0.04         4       5,393    5,540       10,933
spacing002 0.02         8       5,393    44,520      49,913
spacing001 0.01         17      5,393    378,471     383,864
```

Current validated cap-only initial states:

```text
output                                             spacing_mpm  layers  surface_cap  subsurface  total
outputs/initial_robust_cap_only_surface_v7         0.01         4       21,165       82,563      103,728
outputs/initial_robust_cap_only_surface_spacing00025_v1
                                                   0.0025       4       60,778       209,757     270,535
```

Both validated outputs have `surface_entity_source = interpolated_cap`, no
particles below the ground plane, and no subsurface particles above the
interpolated visible cap.

Current accepted manual splat-slice initializer:

```text
source splat: ../EDGS/output/point_cloud/iteration_7000/point_cloud.ply
aligned z band: [-2.4, -2.1]
XY crop: centered 1.0 x 1.0 box
accepted output:
  outputs/splat_surface_regular_grid_subsurface_1x1_depth0p2_spacing0p025_layer0p0125_noise1p5/
```

This path keeps the colored splat slice as the visible surface. The subsurface
is regular XY grids under a high-quantile local surface estimate, with per-layer
XY shift and random XY noise. The accepted case has 21,536 surface splats,
26,895 subsurface particles, 16 layers from 0.0125 to 0.2, and no copied
surface-offset layer.

3x3x3 Genesis matrix runner:

```bash
conda run -n tsplat python scripts/run_splat_matrix_experiments.py \
  --layer-counts 8,16,24 \
  --layer-depths 0.1,0.2,0.3 \
  --particle-sizes 0.015,0.025,0.035
```

Each case goes under `outputs/splat_matrix_3x3x3/` with initial PLYs, metadata,
Genesis metrics, `simulation_ply/`, and `solver_animation.mp4`.

Current base state:

```text
base case:
  layers = 16
  depth = 0.2
  layer_spacing = 0.0125
  particle_size = 0.0125
  render fps = 60

active base:
  outputs/base_settled_stiff_mid/

initial PLY:
  outputs/base_settled_stiff_mid/particles_initial_mpm.ply

metadata:
  outputs/base_settled_stiff_mid/ground_plane_metadata.json

config:
  configs/physgaussian_sand_stiff_mid.json
```

Use the settled mid-stiff base for future tuning unless explicitly testing
initialization. Do not restart from the unrelaxed splat/subsurface PLY by
default.

Recent base outputs:

```text
outputs/base_settled_stiff_mid/
  Current base state. Settled geometry with E=1e5, nu=0.2, density=1000,
  friction_angle=45, substeps=10, and coupled ground. Reference animation is
  solver_animation.mp4.

outputs/settled_material_sweep/
  Three 10s/60fps settled-material tests: current soft, mid-stiff, and
  Genesis-default-like. Mid-stiff and Genesis-default-like are stable.

outputs/particle_size_layer_matrix_3x3_capped_video/
  3x3 particle-size/layer-density sweep. Cases looked similar; resolution is
  not the main bounce knob.

outputs/base_clearance025_substeps10_coupled_layers16_depth0p2_ps0p0125/
  Previous unrelaxed base with clearance, substeps=10, and coupled ground.

outputs/base_earth_gravity_layers16_depth0p2_ps0p025/
  Earth gravity, E=2000, nu=0.2, density=200, friction_angle=35.

outputs/base_earth_less_bouncy_layers16_depth0p2_ps0p025/
  E=700, nu=0.05, density=500, friction_angle=42, dt=0.00025,
  ground offset 0.03, particle_size=0.025.

outputs/base_earth_less_bouncy_layers16_depth0p2_ps0p0125/
  Same less-bouncy config, but particle_size=0.0125 to match layer spacing.

outputs/base_substeps10_coupled_ground_layers16_depth0p2_ps0p0125/
  Adds SimOptions substeps=10 and Genesis-style coupled ground contact:
  Rigid(needs_coup=True, coup_friction=0.2, coup_softness=0.0,
  coup_restitution=0.0).
```

Comparison against Genesis `examples/coupling/sand_wheel.py`:

```text
sand_wheel uses default gs.materials.MPM.Sand():
  E=1e6, nu=0.2, rho=1000, friction_angle=45
  gravity=-9.81 from default SimOptions
  SimOptions(dt=3e-3, substeps=10), effective substep dt=3e-4

Key non-material differences:
  - sand is emitted dynamically, not initialized as a packed bed
  - plane material is Rigid(needs_coup=True, coup_friction=0.2)
  - wheel rigid material uses coup_softness=0.0
  - scene uses substeps=10
```

The bounce diagnosis is now:

```text
- Particle size/layer density was not the main knob.
- The unrelaxed packed bed collapses under gravity and rebounds.
- The old soft material (E=700, rho=500, nu=0.05) still oscillates even from
  the settled state.
- Settled geometry plus mid-stiff/default-like sand is stable.
```

Implemented base-case fixes:

```text
1. Added --substeps to scripts/run_genesis_ground_plane_solver.py.
2. Added Rigid(needs_coup=True, coup_friction=0.2, coup_softness=0.0,
   coup_restitution=0.0) for the ground plane.
3. Kept render fps at 60.
4. Re-ran only the single base case before any matrix.
5. Added configs/physgaussian_sand_stiff_mid.json and
   configs/physgaussian_sand_genesis_default.json.
6. Promoted outputs/base_settled_stiff_mid/ as the active base state.
```

Each case writes:

```text
particles_initial_mpm.ply
particles_surface_mpm.ply
particles_subsurface_mpm.ply
ground_plane_metadata.json
initial_oblique.png
```

Viewer for the densest generated case:

```bash
conda run -n tsplat python scripts/view_particle_ply.py \
  outputs/initial_multilayer_suite/spacing001/particles_initial_mpm.ply \
  --point-size 0.0015 \
  --host 0.0.0.0 \
  --port 8082
```

Avoid generating fully automatic multilayer `spacing00025` casually. With XY
spacing and layer spacing both at `0.0025`, the current radius-1 crop is
expected to create tens of millions of particles. The validated dense case uses
only the four explicit layer depths above.

## Current PhysGaussian/Warp Solver Status

The real PhysGaussian/Warp MPM path initializes on CUDA outside the sandbox, but
it is not yet stable for longer simulations.

Known behavior:

- Tiny CPU MPM smoke tests can write a few frames.
- Longer CPU MPM runs have segfaulted in Warp.
- A hard-parameter CUDA probe initializes and writes a few frames, then fails in
  `p2g_apic_with_stress` with `CUDA error 700: illegal memory access`.
- The hard config uses `E = 5e7`, which appears too stiff for the normalized
  EDGS surface shell.

Known-good tiny CPU smoke:

```bash
conda run -n tsplat python scripts/run_ground_plane_solver.py \
  --max-particles 1000 \
  --steps 2 \
  --n-grid 32 \
  --device cpu \
  --output-dir outputs/ground_plane_solver_cpu_smoke
```

Soft CUDA stability ladder start:

```bash
conda run -n tsplat python scripts/run_ground_plane_solver.py \
  --config configs/physgaussian_sand_soft.json \
  --max-particles 1000 \
  --steps 10 \
  --dt 0.0001 \
  --n-grid 64 \
  --device cuda:0 \
  --output-dir outputs/cuda_soft_1k_s10
```

Observed result for `outputs/cuda_soft_1k_s10`:

```text
frames: 11
particles: 1000
status: completed on cuda:0
max_displacement: 7.69e-05
mean_displacement: 9.85e-07
z_delta_min: -7.69e-05
z_delta_max: 8.94e-08
```

Interpretation: the softened CUDA setup is stable for a small run, but the
motion is still very small. Increase step count before particle count, grid
resolution, or stiffness.

## Current Genesis Solver Status

Genesis is additive; it does not replace the PhysGaussian/Warp path. It uses
the same PLY extraction and output format.

Current usable visualization recipe:

```bash
conda run -n tsplat python scripts/run_genesis_ground_plane_solver.py \
  --config configs/physgaussian_sand_soft.json \
  --max-particles 25621 \
  --trim-quantile 0.005 \
  --duration 2.0 \
  --dt 0.0005 \
  --n-grid 64 \
  --backend cuda \
  --gravity-scale 0.05 \
  --output-dir outputs/genesis_cuda_10pct_trim005_soft_g005_2s_dt0005
```

Observed displacement:

```text
frames: 4001
particles: 24921
max_displacement: 0.40269309680361826
mean_displacement: 0.26032774047886686
median_displacement: 0.26421751242576297
z_delta_min: -0.4026811718940735
z_delta_max: -0.0025490671396255493
```

Render that run:

```bash
conda run -n tsplat python scripts/render_solver_video.py \
  outputs/genesis_cuda_10pct_trim005_soft_g005_2s_dt0005 \
  --duration 4.0 \
  --fps 60 \
  --point-radius 1 \
  --output outputs/genesis_cuda_10pct_trim005_soft_g005_2s_dt0005/solver_animation_oblique_4s.mp4
```

Raised-ground 10-second recipe:

```bash
conda run -n tsplat python scripts/run_genesis_ground_plane_solver.py \
  --config configs/physgaussian_sand_soft.json \
  --max-particles 25621 \
  --trim-quantile 0.005 \
  --ground-quantile 0.02 \
  --duration 10.0 \
  --dt 0.0005 \
  --n-grid 64 \
  --backend cuda \
  --gravity-scale 0.05 \
  --output-dir outputs/genesis_cuda_10pct_trim005_soft_g005_gq002_10s_dt0005
```

Observed output:

```text
frames: 20001
particles: 24921
max_displacement: 0.7995077414054058
mean_displacement: 0.21824543399833113
median_displacement: 0.2201822295129591
z_delta_min: -0.7936241924762726
z_delta_max: 0.02162608504295349
folder size: 5.7G
```

Important caveat: these Genesis runs still simulate a sparse surface shell, not
a filled sand volume. Low gravity is a visualization stabilizer. The correct
next physics step is volumetric particle fill/support and then a localized
load; otherwise gravity keeps settling the surface.

## Current Configs

- `configs/physgaussian_sand.json`: hard initial sand config; `E = 5e7`.
- `configs/physgaussian_sand_soft.json`: current soft stability config;
  `E = 2000`, `nu = 0.2`, `density = 200`, `g = [0, 0, -4]`,
  `friction_angle = 35`, `n_grid = 64`.

Prefer the soft config for Genesis and current CUDA stability work.

## Current Indenter Contact State

Use the Genesis example pattern for any physical entity that should exert on
the MPM sand bed:

```python
scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=..., substeps=10, gravity=(0, 0, -9.81)),
    coupler_options=gs.options.LegacyCouplerOptions(rigid_mpm=True),
    mpm_options=gs.options.MPMOptions(...),
)

entity = scene.add_entity(
    gs.morphs.Cylinder(...),
    material=gs.materials.Rigid(
        needs_coup=True,
        coup_friction=...,
        coup_softness=0.0,
        coup_restitution=0.0,
    ),
)

sand = scene.add_entity(..., material=gs.materials.MPM.Sand(...))
```

This matches the mechanism used by Genesis' `sand_wheel.py` example: coupled
rigid geometry interacts with MPM through `LegacyCouplerOptions(rigid_mpm=True)`.
For this project, cylinders, wheels, feet, blades, and ground supports that
need physical sand interaction should be modeled as `Rigid(needs_coup=True)`.

Do not use the debug particle-edit paths for final behavior:

```text
--debug-contact-mode none
```

`scripts/run_genesis_indenter_test.py` currently has two indenter body modes,
but only one is recommended for physical runs:

```text
--indenter-body-mode rigid
  Coupled Genesis rigid cylinder. This is the current project default and the
  path that matches the Genesis example set.
  The best current non-debug run is:
    outputs/indenter_physical_pd_soft_coup_test/
    outputs/indenter_physical_pd_soft_coup_test/indenter_animation.mp4

--indenter-body-mode tool
  Experimental only. Genesis Tool is a prescribed one-way SDF collider. In the
  current scene it moves, but it does not transfer meaningful motion to the
  sand bed, so do not use Tool-mode outputs as physical evidence.
```

Validated Tool test:

```bash
conda run -n tsplat python scripts/run_genesis_indenter_test.py \
  --indenter-body-mode tool \
  --indenter-softness 0.03 \
  --indenter-friction 0.8 \
  --indent-depth 0.08 \
  --indent-start-time 0.10 \
  --indent-ramp-time 0.80 \
  --indent-hold-time 0.70 \
  --steps 6400 \
  --save-every 80 \
  --output-dir outputs/indenter_tool_contact_synced
```

Result: with an 8 cm commanded tool depth, the surface under the disk moved
only about `-0.08 cm`, comparable to background settling. The rendered video is:

```text
outputs/indenter_tool_contact_synced/indenter_animation.mp4
```

This means Tool mode is implemented, but not acceptable as the physical indenter
solution. Continue from rigid coupled contact for now. If Tool is revisited, it
should be treated as a Genesis internals investigation rather than the default
application path.

## Next Engineering Steps

1. Keep extending the soft PhysGaussian/Warp stability ladder:
   increase step count first, then particle count, grid resolution, or
   stiffness.
2. Add explicit particle/grid bounds checks around MPM stepping so illegal
   memory accesses can be tied to particles leaving the valid stencil.
3. Separate simulation substep `dt` from saved visual frame cadence so playback
   rate does not force unstable physics timesteps.
4. Implement shallow subsurface particle support/fill; the current surface shell
   is the main physics limitation.
5. Only after gravity + ground-plane runs are stable, add localized load/query
   controls for circular displacement or pressure.
6. Transfer particle displacement back to Gaussian centers first; defer
   covariance updates until center-only renders are clean.
7. Add deformation metrics: indentation depth, displaced-volume proxy, and
   local deformation radius.

## Avoid These Pitfalls

- Do not treat `generate_ground_plane_preview.py` output as a physics result;
  it is explicitly non-MPM viewer/debug output.
- Do not use the hard `E = 5e7` config for Genesis surface-shell runs unless the
  goal is to reproduce instability.
- Do not assume identical tiny MPM frames mean the viewer is broken; the current
  tiny real MPM smoke frames may advance too few very small substeps to show
  visible motion.
- Do not add contact loading before gravity-only ground-plane runs are stable.
- Do not run CUDA solver jobs inside the managed sandbox and expect the GPU to
  be visible.

## Worktree Snapshot At Handoff Creation

The worktree already had local modifications before this handoff file was
created. Treat these as in-progress project state:

```text
 M README.md
 M docs/11_current_solver_status.md
 M scripts/check_solver_displacement.py
 M scripts/run_ground_plane_solver.py
 M scripts/view_solver_animation.py
?? scripts/particle_io.py
?? scripts/render_solver_video.py
?? scripts/run_genesis_ground_plane_solver.py
?? scripts/test_ply_to_particles.py
?? scripts/view_particle_ply.py
```

This handoff file is additive and does not intentionally revert or overwrite
those changes.

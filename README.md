# Prototype Plan: Contact-Conditioned Terrain Gaussian Splatting

## Current Checkpoint

The current working scene is the EDGS iteration-7000 checkpoint:

```text
../EDGS/output/point_cloud/iteration_7000/point_cloud.ply
```

For the first prototype pass, assume every Gaussian in the scene is sand. This
intentionally ignores the rigid pole as a separate material/collider until the
viewer, patch extraction, and baseline deformation are stable.

Use the `tsplat` conda environment.

Inspect the scene with Viser:

```bash
conda run -n tsplat python scripts/view_iteration_7000.py
```

The viewer applies `--axis-transform opencv-to-zup` by default, converting
camera/COLMAP-style axes to a Z-up world view:

```text
(x, y, z) -> (x, z, -y)
```

If you need to compare against the raw trained coordinates:

```bash
conda run -n tsplat python scripts/view_iteration_7000.py --axis-transform identity
```

If the fixed axis conversion is still not enough, use analytic ground alignment.
This fits the dominant plane in the splat centers and rotates that plane normal
onto world `+Z`:

```bash
conda run -n tsplat python scripts/view_iteration_7000.py --align-ground-z
```

The loader applies the same rotation to both Gaussian centers and covariances.

Open:

```text
http://localhost:8080
```

By default the viewer sends an opacity-filtered, weighted subset of 300k
Gaussians for browser responsiveness. To send all retained Gaussians:

```bash
conda run -n tsplat python scripts/view_iteration_7000.py --max-gaussians 0
```

Run a non-server load check:

```bash
conda run -n tsplat python scripts/view_iteration_7000.py --dry-run
```

The PhysGaussian-style sand parameters for this prototype live in:

```text
configs/physgaussian_sand.json
```

Validate the PLY-to-particle conversion before running either MPM backend:

```bash
conda run -n tsplat python scripts/test_ply_to_particles.py \
  --max-particles 1000 \
  --output-dir outputs/ply_particle_test_1k
```

This writes the same initial particle PLY and ground-plane metadata consumed by
the solver runners. It round-trips the PLY and reports particle bounds, ground
height, and any particles below the current ground proxy. The default ground
height is the minimum retained particle height; use `--ground-quantile` only for
explicit experiments.

Initialize the first MPM smoke test with a fitted ground plane:

```bash
conda run -n tsplat python scripts/run_ground_plane_solver.py --dry-run
```

This writes:

```text
outputs/ground_plane_solver/
  particles_initial_mpm.ply
  ground_plane_metadata.json
```

The non-dry run uses the PhysGaussian Warp MPM solver and requires `warp` plus
CUDA in the active environment:

```bash
conda run -n tsplat python scripts/run_ground_plane_solver.py
```

Important environment note: sandboxed commands do not see the NVIDIA driver.
Use an unsandboxed shell/session for CUDA solver runs. On the host, CUDA is
visible:

```text
nvidia-smi: RTX 3060 Ti, driver 580.82.09
torch.cuda.is_available(): True
```

The current real MPM status:

- CPU MPM only survives tiny smoke tests; longer CPU runs segfault in Warp.
- CUDA MPM initializes and writes a few frames, then fails in
  `p2g_apic_with_stress` with `CUDA error 700: illegal memory access`.
- The likely next fix is to soften/stabilize the sand parameters before adding
  contact loading: reduce `E` from the current `5e7` toward the PhysGaussian
  sand example scale, start with very small `dt`, and keep particle/grid counts
  small while validating bounds.

Known-good tiny CPU MPM smoke test:

```bash
conda run -n tsplat python scripts/run_ground_plane_solver.py \
  --max-particles 1000 \
  --steps 2 \
  --n-grid 32 \
  --device cpu \
  --output-dir outputs/ground_plane_solver_cpu_smoke
```

CUDA solver probe, expected to initialize but currently fail after a few frames
until parameters are stabilized:

```bash
conda run -n tsplat python scripts/run_ground_plane_solver.py \
  --max-particles 1000 \
  --steps 100 \
  --dt 0.002 \
  --n-grid 64 \
  --device cuda:0 \
  --output-dir outputs/ground_plane_solver_cuda_smoke
```

Soft sand CUDA stability ladder:

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

Check displacement after any solver run:

```bash
conda run -n tsplat python scripts/check_solver_displacement.py \
  outputs/cuda_soft_1k_s10
```

Genesis MPM backend, using the same PLY extraction and output format:

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

Notes for the current scene:

- The retained splat count is 256,210, so 1/10 is about 25,621 input particles.
- `--trim-quantile 0.005` removes spatial outliers before normalization; the
  current 1/10 sample keeps about 24,921 particles after trimming.
- Use the soft config for Genesis. The hard config `E=5e7` explodes on the
  surface-only particle shell.
- `--gravity-scale 0.05` is a visualization stabilizer. Real gravity on a
  surface shell still settles because the terrain is not volumetrically filled.

Genesis CPU movement smoke test:

```bash
conda run -n tsplat python scripts/run_genesis_ground_plane_solver.py \
  --max-particles 200 \
  --steps 2 \
  --dt 0.01 \
  --n-grid 32 \
  --backend cpu \
  --output-dir outputs/genesis_cpu_smoke_200_dt001_active
```

Genesis needs writable compile caches. The runner sets `XDG_CACHE_HOME`,
`GS_CACHE_FILE_PATH`, `NUMBA_CACHE_DIR`, and `MPLCONFIGDIR` under
`outputs/.cache` before importing Genesis. Imported `gs.morphs.Nowhere`
particles are explicitly activated after their PLY-derived positions are set.

Inspect one particle PLY without loading an animation:

```bash
conda run -n tsplat python scripts/view_particle_ply.py \
  outputs/ply_particle_test_10pct_trim005_min_ground/particles_initial_mpm.ply \
  --point-size 0.003 \
  --port 8082
```

Render an MP4 without preloading thousands of PLYs:

```bash
conda run -n tsplat python scripts/render_solver_video.py \
  outputs/genesis_cuda_10pct_trim005_soft_g005_2s_dt0005 \
  --duration 4.0 \
  --fps 60 \
  --point-radius 1 \
  --output outputs/genesis_cuda_10pct_trim005_soft_g005_2s_dt0005/solver_animation_oblique_4s.mp4
```

Raised-ground 10-second run:

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

The 10-second run writes 20,001 PLY frames and is about 5.7G. Render it with:

```bash
conda run -n tsplat python scripts/render_solver_video.py \
  outputs/genesis_cuda_10pct_trim005_soft_g005_gq002_10s_dt0005 \
  --duration 10.0 \
  --fps 60 \
  --point-radius 1 \
  --output outputs/genesis_cuda_10pct_trim005_soft_g005_gq002_10s_dt0005/solver_animation_oblique_10s.mp4
```

View a solver output animation in Viser:

```bash
conda run -n tsplat python scripts/view_solver_animation.py \
  outputs/ground_plane_solver_cpu_smoke
```

Open:

```text
http://localhost:8081
```

For a representative 1/10 particle subset over a 2 second loop:

```bash
conda run -n tsplat python scripts/view_solver_animation.py \
  outputs/ground_plane_solver_cpu_smoke \
  --sample-fraction 0.1 \
  --duration 2.0
```

To regenerate a denser playback sequence where total frames are
`ceil(duration / dt)`:

```bash
conda run -n tsplat python scripts/resample_solver_frames.py \
  outputs/ground_plane_solver_cpu_smoke \
  outputs/ground_plane_solver_cpu_smoke_resampled_2s \
  --duration 2.0 \
  --dt 0.02
```

If the real MPM frames are identical or too sparse for viewer debugging, use the
explicitly non-MPM gravity preview. It applies kinematic gravity and a
ground-plane clamp so the viewer path can be inspected while the real MPM
stability issue is addressed:

```bash
conda run -n tsplat python scripts/generate_ground_plane_preview.py \
  outputs/ground_plane_solver_cpu_smoke \
  outputs/ground_plane_solver_cpu_gravity_preview_2s \
  --duration 2.0 \
  --dt 0.02
```

## 0. Project Goal

Build a prototype that answers the query:

> Given a Gaussian-splat terrain map, what would the terrain look like after a localized surface load is applied at location X, assuming the material is sand?

The initial goal is not full robot-terrain contact or deep object penetration. The initial goal is a stable, controllable, visually inspectable pipeline for shallow terrain deformation.

The prototype should output:

1. A deformed Gaussian splat map.
2. Rendered before/after RGB views.
3. Optional rendered before/after depth maps.
4. Simple terrain metrics such as indentation depth, displaced volume proxy, and local deformation radius.

## 1. Core Hypothesis

A terrain Gaussian map can be turned into a queryable physical world model if each local patch supports:

* geometry,
* material identity,
* material parameters,
* shallow subsurface support,
* localized force or displacement queries,
* splat deformation and rerendering.

The first prototype should use surface pressure or shallow displacement rather than rigid penetration. This avoids the hardest contact mechanics while still demonstrating the main idea.

## 2. Recommended Prototype Query

Use this as the first standardized query:

```text
Input:
- Gaussian terrain map G_t
- query location x
- material = sand
- circular contact radius r
- downward pressure or displacement magnitude
- duration or number of simulation steps

Output:
- deformed Gaussian map G_{t+1}
- rendered image I_{t+1}
- rendered depth D_{t+1}
- deformation metrics
```

Example:

```text
Apply a 5 cm radius circular pressure patch at location x on sand for 0.2 seconds.
Predict the resulting terrain splat deformation and render the new view.
```

## 3. Phase 1 — Minimal Terrain Splat Reconstruction

### Goal

Create a small terrain Gaussian scene that can be rendered reliably.

### Data Options

Start simple:

1. Synthetic sand height field.
2. Small real sand tray captured with phone video or RGB-D.
3. Public terrain/drone scene only after the controlled setup works.

### Tools

* Nerfstudio
* gsplat
* COLMAP
* OpenCV
* Python
* Open3D
* PyTorch

### Recommended Starting Choice

Use Nerfstudio with `splatfacto` or `splatfacto-big` to train the first Gaussian scene. Export the Gaussian `.ply`.

### Deliverables

* `terrain_initial.ply`
* camera poses
* before-render images
* script to load Gaussian means, scales, rotations, opacity, and colors

### Success Criteria

* The terrain renders from held-out views.
* Gaussian means roughly cover the terrain surface.
* You can crop a local region around a query point.

## 4. Phase 2 — Terrain Patch Extraction

### Goal

Given a query location X, extract only the local splats that matter.

### Method

Define a radius `R_patch` around the query point:

```python
local_ids = where(norm(gaussian_xyz - query_xyz) < R_patch)
```

For early tests, use a flat or nearly flat terrain patch. Avoid slopes, rocks, vegetation, and holes.

### Tools

* NumPy
* PyTorch
* Open3D
* scipy.spatial.KDTree

### Deliverables

* `extract_patch.py`
* local patch `.ply`
* visualization of selected splats
* local coordinate frame centered at query point

### Success Criteria

* The selected patch contains enough Gaussians for deformation.
* You can visualize the local patch independently.
* The local patch has a stable local ground normal.

## 5. Phase 3 — Kinematic Deformation Baseline

### Goal

Before using MPM, create a simple analytic deformation baseline.

This gives a visual proof-of-concept and a debugging target.

### Method

Apply a Gaussian-shaped indentation to splat centers:

```text
d_i = d_max * exp(-||xy_i - xy_query||^2 / (2 r^2))
z_i' = z_i - d_i
```

Optionally add a simple rim/pile-up around the indentation:

```text
rim_i = a * exp(-(||xy_i - xy_query|| - r_rim)^2 / (2 sigma_rim^2))
z_i' = z_i - indentation_i + rim_i
```

Update Gaussian covariances only after the center displacement works.

### Tools

* Python
* NumPy/PyTorch
* gsplat or original 3DGS renderer
* Open3D for visualization

### Deliverables

* `deform_kinematic.py`
* before/after `.ply`
* before/after render
* indentation-depth metric

### Success Criteria

* You can apply a query at X and get a plausible local dent.
* Rendering does not explode.
* The deformation is localized.
* This baseline becomes the first comparison for MPM.

## 6. Phase 4 — Surface Pressure MPM Patch

### Goal

Replace analytic deformation with a local MPM simulation while avoiding rigid penetrative contact.

### Method

Convert the local terrain patch into particles. Apply a downward force or velocity field to surface particles inside a circular patch.

Initial force model:

```text
f_i = f_0 * exp(-||xy_i - xy_query||^2 / (2 r^2)) * (-normal)
```

Alternatively, use displacement control:

```text
surface particles inside radius r receive a target downward velocity for N steps
```

Displacement control is recommended first because it is easier to stabilize than force control.

### Tools

* Taichi
* taichi_mpm
* NumPy
* PyTorch
* Open3D

### Material Model

For the first test, use a simplified material:

1. Start with elastic or weakly plastic material.
2. Then move to Drucker–Prager-style sand.
3. Tune only a few parameters at first:

   * density
   * Young’s modulus
   * Poisson’s ratio
   * friction angle
   * damping

### Deliverables

* `mpm_patch_sim.py`
* local particles before/after
* deformation field
* updated Gaussian centers
* rendered result

### Success Criteria

* Simulation remains stable.
* The patch deforms locally.
* The deformation can be transferred back to Gaussians.
* Before/after render shows visible terrain change.

## 7. Phase 5 — Subsurface Support

### Goal

Avoid simulating only a hollow terrain surface.

A surface-only splat map is usually not enough for physical terrain deformation. Add a shallow volume below the terrain.

### Method

For each surface splat or sampled surface point, create a short vertical column of particles below the surface:

```text
for each surface point p:
    for k in 1..K:
        particle = p - k * dz * normal
```

Use larger density near the surface and optionally coarser particles deeper down.

### Recommended First Parameters

```text
depth = 5 cm to 15 cm
layers = 4 to 10
particle spacing = 0.5 cm to 2 cm depending on scene scale
```

### Tools

* Open3D
* NumPy
* Taichi
* scipy.spatial

### Deliverables

* `fill_subsurface.py`
* visualization of surface and subsurface particles
* local terrain volume `.ply`
* MPM simulation with volume support

### Success Criteria

* Particles do not collapse immediately.
* The terrain deforms more plausibly than the surface-only version.
* Downward deformation produces compaction and some lateral motion.

## 8. Phase 6 — Gaussian Update from Simulation

### Goal

Transfer MPM particle deformation back to the renderable Gaussian map.

### Simple Version

Update only Gaussian centers:

```text
x_i' = x_i + interpolated_displacement(x_i)
```

Use nearest-neighbor or kernel interpolation from MPM particles.

### Better Version

Also update covariance using local deformation gradient:

```text
Sigma_i' = F_i Sigma_i F_i^T
```

This is the physically meaningful version and is closer to the PhysGaussian-style update.

### Tools

* PyTorch
* NumPy
* scipy KDTree
* gsplat / 3DGS renderer

### Deliverables

* `transfer_mpm_to_gaussians.py`
* deformed Gaussian `.ply`
* render script
* covariance-update option

### Success Criteria

* Center-only update works.
* Covariance update does not create severe artifacts.
* Deformed splats render from multiple views.

## 9. Phase 7 — Material Conditioning

### Goal

Make the query material-aware.

Start with:

```text
material = sand
```

Then add:

```text
material = mud
material = gravel
material = snow
material = grass/soil
```

### Material Parameter Table

Create a simple config file:

```yaml
sand:
  density: 1600
  youngs_modulus: 1.0e5
  poisson_ratio: 0.2
  friction_angle: 30
  cohesion: 0.0
  damping: 0.1

wet_sand:
  density: 1900
  youngs_modulus: 2.0e5
  poisson_ratio: 0.25
  friction_angle: 35
  cohesion: 0.1
  damping: 0.2

mud:
  density: 1700
  youngs_modulus: 5.0e4
  poisson_ratio: 0.35
  yield_stress: 100
  viscosity: 1.0
```

Do not worry about perfect physical realism at first. The purpose is controlled counterfactual behavior.

### Tools

* YAML
* Python dataclasses
* Taichi
* Optional: semantic segmentation model later

### Deliverables

* `materials.yaml`
* material-conditioned simulation runs
* comparison renders for sand vs wet sand vs mud

### Success Criteria

* Different materials produce visibly different deformation.
* Sand produces more granular/local collapse.
* Mud produces smoother, more viscous deformation.
* Parameters are easy to change from a config.

## 10. Phase 8 — Query Interface

### Goal

Create a clean interface for counterfactual terrain queries.

### CLI Example

```bash
python query_terrain.py \
  --scene terrain_initial.ply \
  --query_xyz 0.2 0.1 0.0 \
  --material sand \
  --radius 0.05 \
  --mode displacement \
  --depth 0.01 \
  --steps 100 \
  --out outputs/query_001
```

### Python API Example

```python
result = terrain_model.query(
    location=x,
    material="sand",
    contact_radius=0.05,
    mode="displacement",
    displacement=0.01,
    steps=100,
)
```

### Output

```text
outputs/query_001/
  before.png
  after.png
  before_depth.png
  after_depth.png
  terrain_deformed.ply
  metrics.json
  config.yaml
```

### Success Criteria

* One command runs the whole pipeline.
* Output is reproducible.
* Configs are saved with results.

## 11. Phase 9 — Evaluation

### Goal

Show that the method is doing more than visual editing.

### First Evaluation Without Real Robot

Use controlled indentation experiments:

1. Build a small sand tray.
2. Capture before images.
3. Apply known shallow indentation using a flat circular stamp.
4. Capture after images.
5. Compare predicted after-state to real after-state.

### Metrics

Rendering:

* PSNR
* SSIM
* LPIPS

Geometry:

* depth error
* Chamfer distance between reconstructed before/after surfaces
* indentation depth error
* deformation radius error

Physics/task metrics:

* displaced volume proxy
* sinkage error
* pile-up height error
* lateral spread error

### Baselines

1. No deformation.
2. Analytic kinematic indentation.
3. MPM without subsurface filling.
4. MPM with subsurface filling.
5. MPM with material conditioning.

### Success Criteria

* MPM with subsurface support beats no-deformation and analytic-only baselines on geometry.
* Rendered after-view is plausible.
* The method can answer multiple query locations in the same terrain map.

## 12. Phase 10 — Robotics Extension

Only start this after the shallow pressure prototype works.

### Extensions

1. Wheel contact patch instead of circular patch.
2. Footstep-shaped pressure patch.
3. Tangential shear force.
4. Repeated contacts.
5. Online update from observed before/after terrain.
6. Slip/sinkage prediction.
7. Planner queries: “which region deforms least?”

### Tools

* ROS2
* Isaac Sim or Genesis, optional
* robot logs: IMU, odometry, torque/current
* depth camera or LiDAR

### Success Criteria

* Given a planned foot/wheel contact, predict terrain deformation.
* Predict sinkage or rut depth.
* Update persistent terrain splat map after the robot acts.

## 13. Repository Structure

```text
terrain-gs-physics/
  README.md
  configs/
    materials.yaml
    scenes.yaml
  data/
    raw/
    processed/
  terrain_gs/
    io/
      load_gaussians.py
      save_gaussians.py
    patch/
      extract_patch.py
      local_frame.py
    deformation/
      kinematic_indent.py
      covariance_update.py
    mpm/
      fill_subsurface.py
      mpm_patch_sim.py
      material_models.py
    rendering/
      render_before_after.py
    query/
      query_terrain.py
    eval/
      metrics.py
      compare_depth.py
  outputs/
  scripts/
    train_splat.sh
    run_query.sh
    run_eval.sh
```

## 14. Minimum Viable Prototype Checklist

The first working demo should do the following:

* Load a Gaussian terrain `.ply`.
* Select a local patch around query point X.
* Apply analytic shallow indentation.
* Save deformed Gaussian `.ply`.
* Render before and after.
* Generate a simple metric JSON.
* Replace analytic indentation with local MPM.
* Add shallow subsurface particles.
* Transfer MPM deformation back to Gaussians.
* Render the deformed result.

## 15. Practical Risk Reduction

Avoid these at the start:

* deep rigid-body penetration,
* complex wheel geometry,
* full-scene MPM,
* learned material inference,
* differentiable MPM,
* real-time requirements,
* outdoor terrain immediately,
* multi-material segmentation.

Start with:

* small local patch,
* sand-only,
* shallow displacement,
* controlled camera views,
* center-only Gaussian updates,
* then covariance updates.

## 16. First Two-Week Milestone

### Week 1

* Train or load a small terrain Gaussian scene.
* Export `.ply`.
* Load Gaussian attributes in Python.
* Extract local patch.
* Apply analytic indentation.
* Render before/after.

### Week 2

* Generate subsurface particles.
* Run simple Taichi MPM patch simulation.
* Apply shallow displacement or pressure.
* Transfer particle displacement to Gaussian centers.
* Render deformed splat map.

### Demo at End of Week 2

A command like:

```bash
python query_terrain.py --scene sand_tray.ply --query_xyz X Y Z --material sand --radius 0.05 --depth 0.01
```

produces:

```text
before.png
after_analytic.png
after_mpm.png
terrain_deformed.ply
metrics.json
```

## 17. Paper Direction After Prototype

The eventual research framing should be:

> We introduce a contact-conditioned terrain Gaussian world model that predicts counterfactual terrain deformation under localized surface loading. Unlike generic physics-GS methods, the representation is terrain-native: it uses shallow subsurface support, material-conditioned local MPM, and splat-space rendering to predict future terrain appearance and geometry after robot-relevant contact queries.

The key novelty is not “MPM plus Gaussian splatting.” The key novelty is queryable, material-conditioned, terrain-specific Gaussian world modeling.

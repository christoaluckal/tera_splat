# Hybrid Chrono-MPM residual model for Gaussian terrain and planning

Date: 2026-10-08  
Status: proposed implementation and validation contract  
Code changes: none are implied by this document

For the live Phase 0 ledger, sequencing locks, chronological evidence, and
current claims, use [newton/phase0.md](newton/phase0.md). The dated execution
snapshots in this design are retained only as provenance.

## Goal

Build an offline, open-loop terrain what-if model with the following roles:

1. Chrono SCM generates synthetic ground-truth surface deformation and support
   outcomes.
2. A particle-grid MPM supplies volumetric dynamics and latent physical state.
3. A learned residual corrects the MPM response without replacing its mechanics.
4. Corrected particle motion and deformation update the terrain Gaussians.
5. Held-out novel views and a fixed robot planner test whether the corrected
   world model is useful.

The initial scope is a generated Gaussian scene, the existing 35 mm robot-foot
proxy, independent actions varying position and normal load, and one offline
planning decision. Real terrain, unseen material parameters, execution, and
closed-loop replanning are later work.

The intended system is:

    Chrono H0 + action -----------------------> surface/render targets
                    \
    prepared MPM + same action -> frozen MPM -> bounded residual field
                                                 |
                                                 +-> corrected particle x and F
                                                 +-> Gaussian update
                                                 +-> held-out NVS
                                                 +-> planner evaluation

This extends the repository direction in
[forward-model-direction-20261006.md](forward-model-direction-20261006.md)
and uses the bounded Newton conclusion in
[newton/phase0.md](newton/phase0.md).

## Resolved design decisions

### Chrono is the synthetic oracle

Chrono supplies accepted initial, loaded, residual, and preferably sampled
intermediate heightfields; action timing; valid support masks; and rigid support
outcomes. It is ground truth for this sim-to-sim experiment, not evidence of
real-sand accuracy.

Chrono SCM is a soil-contact heightfield model. It has no volumetric particle
correspondence, particle stress, plastic strain, or deformation gradient.
Therefore no MPM particle can be assigned a true Chrono particle target.

### Positions are the main learned state

The residual predicts corrected particle displacement. It does not predict
independent rigid-particle orientation. An MPM material point represents a
continuum volume, and its local orientation, stretch, and shear are carried by
the deformation gradient.

For MPM particle p:

\[
\mathbf{x}'_p =
\mathbf{x}^{MPM}_p +
\delta\mathbf{u}(\mathbf{x}^{MPM}_p, a, t).
\]

Derive the corrected deformation gradient from the correction field:

\[
\mathbf{F}'_p =
\left(\mathbf{I}+\nabla\delta\mathbf{u}\right)
\mathbf{F}^{MPM}_p.
\]

Use the polar decomposition:

\[
\mathbf{F}'_p=\mathbf{R}_p\mathbf{S}_p
\]

for local material rotation. This produces the state required for
PhysGaussian-style position, covariance, and appearance-orientation updates
without inventing an unobservable Chrono orientation label.

### Material fitting is training, not per-action inference

MPM parameters can adjust material response. For the action-generalization
experiment they must be calibrated once across training actions and frozen for
validation and test.

Per-action retuning would let the material setting absorb action identity. It
would measure optimization access to the held-out target, not forward-model
generalization.

### Planning is initially independent and open loop

The first planner may score proposed contacts independently from the same
initial terrain and choose a path or support candidate once. It need not
execute.

This does not validate sequential deformation accumulation. A Chrono heightmap
does not contain the internal stress, plastic state, packing history, or
velocity needed to initialize a later MPM action. The existing independent
reset restriction remains in force:
[pipeline proposal](../../tera_splat_sim/docs/archive/chrono-to-mpm-gaussian-pipeline-proposal-2026-08-12.md).

## Backend assessment

### Newton: primary first-stage backbone

Use Newton for the first offline residual experiment.

Reasons:

- the repository already has a public, mechanics-qualified numerical contract;
- the runner exports position, velocity, velocity gradient, elastic
  deformation gradient, plastic Jacobian, Cauchy stress, and total deformation
  transform;
- the contact, preparation, timing, support, and failure gates are already
  instrumented;
- the residual can be trained around precomputed Newton rollouts, so gradients
  through Newton are unnecessary.

Limitation: Newton SolverImplicitMPM is not differentiable. This prevents
straightforward end-to-end training of a residual inserted inside a long
rollout. The first correction must therefore operate on saved valid states or
short detached windows.

Official references:

- [Newton implicit MPM](https://newton-physics.github.io/newton/stable/api/_generated/newton.solvers.SolverImplicitMPM.html)
- [Newton solver feature matrix](https://github.com/newton-physics/newton/blob/main/docs/solvers/index.rst)

### Genesis: comparator and future differentiable path

Genesis provides a differentiable MPM, a Drucker-Prager sand material, and
rigid-MPM coupling. It is the better candidate if evidence later requires the
residual to operate within the rollout.

It is not the primary first-stage backend because the current repository has
not demonstrated converged Genesis preparation and response across the needed
timestep hierarchy. The installed differentiable path also does not support
CPIC. A learned residual must not be trained on a numerically unresolved prior
as though the discrepancy were purely constitutive.

Official references:

- [Genesis soft solvers](https://genesis-world.readthedocs.io/en/latest/user_guide/theory/soft_solvers.html)
- [Genesis coupling](https://genesis-world.readthedocs.io/en/latest/user_guide/theory/coupling/index.html)
- [Genesis differentiable simulation](https://genesis-world.readthedocs.io/en/latest/user_guide/theory/differentiable_simulation.html)

### Warp: later custom in-rollout option

Warp supports differentiable kernels and zero-copy PyTorch integration. A
custom Warp MPM would give full control over grid residual placement,
checkpointing, and Gaussian transfer.

The cost is ownership of preparation, contact, rigid coupling, constitutive
updates, and numerical qualification. The PhysGaussian warp-mpm repository is
a valuable transfer reference, but its published environment is tied to an
older Warp stack and is not a qualified robot-terrain engine.

References:

- [Warp differentiability](https://nvidia.github.io/warp/latest/user_guide/differentiability.html)
- [Warp PyTorch interoperability](https://nvidia.github.io/warp/latest/user_guide/interoperability/pytorch.html)
- [PhysGaussian warp-mpm](https://github.com/zeshunzong/warp-mpm)

### Taichi: research fallback

Taichi has a useful autodiff system and a history of differentiable MPM
research. It has no current repository integration, prepared-bed contract, or
qualified rigid-foot contact path. A Taichi backend would duplicate more
validated infrastructure than it reuses, so it is the lowest-priority option.

Reference:
[Taichi differentiable programming](https://docs.taichi-lang.org/docs/master/differentiable_programming).

## Proxy-foot mechanics qualification

The current Newton evidence is based on a 73.025 mm radius cylinder. The
selected Go1 proxy uses a 35 mm radius:
[Go1 configuration](../../tera_splat_sim/quick_support_demo/configs/go1.yaml).

For a 12.5 kg robot:

| Support assumption | Effective mass per foot | Approximate pressure |
| --- | ---: | ---: |
| four equal supports | 3.125 kg | 8 kPa |
| two stance supports | 6.25 kg | 16 kPa |
| historical A0 cylinder | 1.5 kg | 0.88 kPa |

The incumbent already failed strict mechanics at 55 and 65 mm radii. The
35 mm foot is outside the qualified geometry and operates at much higher
nominal pressure.

Before data generation:

1. fix the 35 mm area-equivalent contact geometry;
2. express the varying action as x, y, and normal force;
3. hold timing, friction convention, bed, preparation, and boundaries fixed;
4. sweep the proposed load interval through preparation, drift, support,
   timing, guide, and penetration gates;
5. define the admissible action region before fitting the material or network.

Use normal force and pressure as recorded action features even when the Chrono
runner specifies equivalent mass. This makes the action semantics explicit and
supports later geometry studies.

## MPM calibration protocol

The numerical configuration and action domain must be fixed before material
optimization.

Recommended sequence:

1. Screen sensitivity of Newton-native material controls.
2. Fit the smallest identifiable global subset across several training actions.
3. Use surface RMSE, peak, volume, footprint, centroid, and recovery rather
   than the historical scalar map objective alone.
4. Require every candidate to pass the full mechanics contract.
5. Select one setting using a declared multi-action Pareto or normalized score.
6. Freeze it before residual training and all validation/test actions.

The historical Young's modulus, Poisson ratio, and friction fit is a useful
initialization only if the 35 mm contract accepts it. Yield pressure,
dilatancy, hardening, softening, damping, and viscosity should enter only after
a sensitivity screen shows that the existing subset cannot represent a
training characteristic. Simultaneously optimizing every control would make
the effective material poorly identifiable from surface maps.

An action-specific best-fit material may be computed only as an oracle upper
bound. It must be labeled non-predictive and excluded from generalization
comparisons.

## First residual architecture

### Representation

Scatter Newton particles to the active MPM grid using the same or a compatible
compact kernel. Construct an action-aligned sparse 3D crop around the foot.

Use a small sparse 3D U-Net with:

- a zero-initialized output layer;
- bounded residual output through a scaled hyperbolic tangent;
- a shared backbone for loaded and residual states;
- a phase or time embedding;
- a displacement head;
- a log-variance head for uncertainty.

The primary output is a grid displacement correction. Gather it back to
particles. Derive the deformation correction from the spatial displacement
gradient.

This preserves particle permutation invariance and spatial continuity better
than an independent per-particle MLP. It also preserves more subsurface state
than a surface-only 2D network.

### Initial features

Always include:

- foot-relative coordinates;
- signed distance to the foot/contact region;
- normal force and pressure;
- load phase or normalized time;
- distance to bed walls and base;
- grid mass or occupancy;
- MPM velocity;
- initial-surface distance.

Candidate latent channels:

- particle or grid deformation-gradient invariants;
- singular values or logarithmic strain;
- plastic Jacobian;
- pressure and deviatoric stress magnitude;
- vertical normal stress and shear magnitude;
- velocity-gradient invariants;
- contact indicator.

Raw tensor components should be expressed in a foot-aligned frame or processed
by an equivariant architecture. Otherwise a rotated action may look like a new
material solely because tensor coordinates changed.

### Stability constraints

- bound correction magnitude relative to the local voxel size or prior motion;
- taper the correction to zero outside the affected support;
- require positive determinant of corrected deformation;
- clamp or penalize extreme singular values;
- penalize correction on a no-action episode;
- penalize spatial roughness;
- reject the entire sample if the MPM prior failed a mechanics gate.

The network must correct a valid model response, not legalize invalid physics.

## Supervision through observable operators

Chrono cannot supervise subsurface particles directly. Train through a
differentiable observation operator:

\[
\{\mathbf{x}'_p,\mathbf{F}'_p\}
\rightarrow
\widehat H(x,y),\widehat D_c,\widehat M_c.
\]

Here:

- \(\widehat H\) is a differentiable surface projection or density isosurface;
- \(\widehat D_c\) is rendered depth from camera c;
- \(\widehat M_c\) is the rendered terrain mask.

A soft upper-surface projection can provide stable gradients early. A density
field or extracted particle surface should be used for final evaluation so the
training approximation does not define the reported geometry.

### Losses

Use a balanced objective:

\[
L =
L_{\mathrm{surface}}
+\lambda_c L_{\mathrm{characteristics}}
+\lambda_r L_{\mathrm{render}}
+\lambda_q L_{\mathrm{regularization}}.
\]

Surface terms:

- robust loaded-height error;
- robust residual-height error;
- error inside and outside the contact footprint;
- surface normal error when available.

Characteristic terms:

- maximum and mean depression;
- displaced volume;
- footprint area and boundary overlap;
- depression centroid;
- recovery after unloading.

Render terms:

- held-out-view depth error;
- terrain silhouette or mask loss;
- normal error;
- RGB L1/SSIM or LPIPS only after geometry is correct.

Regularization:

- residual magnitude;
- spatial smoothness;
- no-action identity;
- deformation determinant and singular-value bounds;
- boundary taper;
- optional approximate volume or mass consistency.

Loaded and residual results must remain separate in reports. A single weighted
number can be used for optimization, but it cannot replace the characteristic
table.

## Dataset and split

### Episode schema

Every paired episode should record:

- source revision and software versions;
- complete Chrono and MPM configurations;
- initial terrain and support mask;
- action x, y, normal force, pressure, geometry, and timing;
- accepted Chrono event times;
- every sampled Chrono heightfield used for training;
- MPM particle and grid state at matching times;
- preparation and mechanics-gate results;
- camera calibration and render paths;
- loaded and residual characteristics.

Chrono and MPM must start independently from the same H0 and receive the action
once. Never initialize MPM from the Chrono loaded surface and repeat the load.

### Pilot budget

A useful initial target is:

| Split | Episodes | Purpose |
| --- | ---: | --- |
| train | 48 | global material fit and residual learning |
| validation | 16 | model selection and uncertainty calibration |
| test | 24 | locked action-generalization report |

Scale only if action-level learning curves are still improving. Dense cells or
particles within one episode are correlated and do not increase the number of
independent actions.

Sample training positions with a low-discrepancy design inside the qualified
interior. Sample normal force continuously within the accepted interval.

Create three test groups:

1. unseen positions at interpolated loads;
2. unseen loads in familiar spatial regions;
3. unseen position-load combinations.

Optional extrapolation outside the convex training action region must be
reported separately and should normally trigger higher uncertainty.

Split entire episodes before network development. Do not split cells,
particles, frames from the same action, or camera views across train and test
in a way that leaks the target state.

## Latent-state ablation

The MPM generates stress and deformation at inference, so they need not be
measured in the real world. Their value must still be demonstrated.

Train the same architecture and seeds with nested features:

| Model | Features |
| --- | --- |
| L0 | action, geometry, and initial terrain only |
| L1 | L0 plus MPM position, velocity, mass/occupancy, and contact |
| L2 | L1 plus deformation-gradient invariants and plastic Jacobian |
| L3 | L2 plus stress invariants and velocity-gradient invariants |
| L4 | raw tensors in an aligned or equivariant representation |

Normalize stress by applied pressure or an effective material scale. Prefer
log strain, principal stretches, determinant, pressure, and deviatoric
magnitude over unconstrained raw components.

Evaluate every ablation on the action-level held-out splits using:

- surface and characteristic errors;
- planner regret;
- uncertainty calibration;
- correction magnitude and deformation validity;
- sensitivity to feature dropout, clipping, and noise.

Run a small Newton-to-Genesis feature-transfer diagnostic when Genesis becomes
qualified. A latent that improves Newton interpolation but fails under a second
valid backend may encode solver artifacts rather than transferable mechanics.

## Uncertainty

Use both:

- heteroscedastic predicted variance over the corrected surface or grid;
- an ensemble or episode bootstrap for model uncertainty.

Calibrate coverage on the validation actions. Combine model uncertainty with:

- distance from the training action set;
- proximity to the qualified mechanics boundary;
- preparation and contact-gate status.

Mechanics-invalid inputs are rejected rather than assigned a large neural
variance. For valid inputs, the planner should use an upper-confidence or
worst-case sinkage cost rather than only the predicted mean.

## Segmenting and lifting the terrain region

The Gaussian map already exists. Render several novel views and apply SAM to
the sand region. Lift masks to Gaussians using each Gaussian's visibility and
alpha contribution, then fuse votes across views.

Recommended safeguards:

- require multiview agreement;
- retain the connected ground component;
- remove floaters and Gaussians inconsistent with the bed bounds;
- store a probability and uncertainty, not only a hard label;
- in the synthetic phase, compare against known Chrono object ownership.

This validates segmentation separately from dynamics. Training-free
contribution-based lifting is supported by
[Lifting by Gaussians](https://openaccess.thecvf.com/content/WACV2025/html/Chacko_Lifting_by_Gaussians_A_Simple_Fast_and_Flexible_Method_for_WACV_2025_paper.html).

## Particle-to-Gaussian update

Use volumetric MPM particles for physics and surface Gaussians for rendering.
Store the canonical particle neighborhood for every terrain Gaussian.

For Gaussian g, either interpolate corrected displacement and deformation or
fit a weighted local affine transform:

\[
\mathbf{x}'_p \approx \mathbf{A}_g\mathbf{x}_p+\mathbf{b}_g.
\]

Then update:

\[
\boldsymbol{\mu}'_g =
\mathbf{A}_g\boldsymbol{\mu}_g+\mathbf{b}_g,
\qquad
\boldsymbol{\Sigma}'_g =
\mathbf{A}_g\boldsymbol{\Sigma}_g\mathbf{A}_g^{T}.
\]

The local affine fit is preferred when the corrected state is defined mainly
by positions. It gives one compatible transform for the Gaussian mean,
covariance, and orientation. Use the polar rotation of \(\mathbf{A}_g\) to
rotate the view-dependent spherical-harmonic frame.

First milestone policy:

- update only sand Gaussians;
- update mean, covariance, and SH orientation;
- retain opacity and SH coefficients;
- clamp covariance eigenvalues and anisotropy;
- taper deformation at the MPM region boundary;
- keep robot, tray, tags, floor, and background rigid.

Large deformation may expose material that had no visible Gaussian in the
initial scene. PhysGaussian fills hidden volume for this reason. The first
terrain demonstration should either remain within moderate deformation or
explicitly add hidden/internal render particles. Do not conceal holes with
retraining and then claim pure physics transfer.

Primary references:

- [PhysGaussian](https://arxiv.org/html/2311.12198)
- [Particle-Grid Neural Dynamics](https://arxiv.org/html/2506.15680v2)
- [PhysReal](https://arxiv.org/html/2609.07532v1)

## Novel-view validation

Use the exact Chrono camera intrinsics and poses already exported by
[splat-rgbd-capture.md](../../tera_splat_sim/docs/splat-rgbd-capture.md).

Evaluate initial, loaded, and residual scenes from cameras excluded from any
render loss:

- metric depth RMSE, median, and high-percentile error;
- normal error;
- terrain-mask IoU;
- surface Chamfer distance where appropriate;
- RGB PSNR and SSIM;
- LPIPS as a secondary appearance metric.

Geometry is the acceptance signal for planning. A visually plausible RGB
render with incorrect depth does not validate the model.

## Planner validation

Keep the planner, candidate set, cost weights, and feasibility thresholds
fixed while changing only the world model.

Compare:

1. static Gaussian scene or DEM;
2. simple load-sinkage heuristic;
3. frozen MPM;
4. action-only neural baseline;
5. hybrid MPM plus residual;
6. Chrono oracle.

The planner may choose among support poses, footholds, or complete open-loop
candidate paths. For the first proof, score each contact from the same initial
terrain and aggregate maximum or uncertainty-adjusted risk. Label this as
independent counterfactual planning, not sequential terrain rollout.

Evaluate the chosen decision afterward with Chrono:

- oracle cost regret;
- top-1 and top-k agreement;
- unsafe-selection false-negative rate;
- maximum sinkage and tilt error;
- route feasibility and clearance;
- reachable-area or path-cost change;
- uncertainty coverage;
- runtime.

The existing objective combines view, path, sinkage, tilt, and uncertainty but
has no hard feasibility threshold:
[planning-and-outputs.md](../../tera_splat_sim/docs/planning-and-outputs.md).
Predeclare a maximum sinkage, tilt, clearance, or uncertainty threshold for
the planner experiment.

Relevant planning precedent:
[Path Planning in Physically Viable World Models](https://arxiv.org/html/2607.00673v1).

## Required baselines

The following baselines isolate where improvement comes from:

- unchanged MPM;
- globally recalibrated and frozen MPM;
- action plus initial DEM network with no MPM state;
- MPM kinematics without stress or deformation latents;
- hybrid model with all retained latents;
- Chrono oracle.

A pure learned particle-grid model is useful as a data-efficiency baseline but
is not the recommended primary system. NeuralMPM and PGND rely on observed or
corresponding particle trajectories that Chrono SCM does not provide:

- [NeuralMPM](https://arxiv.org/html/2408.15753v3)
- [Particle-Grid Neural Dynamics](https://arxiv.org/html/2506.15680v2)

## Staged implementation

### Phase 0 — Contract and domain

- freeze the 35 mm proxy geometry and action vector;
- define the normal-force interval;
- preserve strict Newton mechanics/convergence diagnostics and separately
  declare a bounded coarse-prior admission policy for the offline pilot;
- create the prospective episode split.

Strict exit: every admitted action has valid Chrono GT and a strictly
mechanics-valid, response-converged Newton prior.

Bounded pilot exit: every action in the final declared domain has valid Chrono
GT, identical H0, a fixed-0.25 ms Newton state that passes the frozen bounded
gate, and a whole-episode prospective split. This permits only the offline
residual experiment; strict mechanics and convergence remain failed claims.

Execution snapshot, 2026-10-16: the centered 31 N and 46 N training actions pass
bounded policy v2 and fail strict zero penetration. The policy is frozen at
10 micrometers transient depth and 0.02% affected particles before the 61 N
and spatial cases. The centered 61 N boundary subsequently failed loaded-state
clearance and is excluded. The pilot now contains 10 actions over five
positions at 31/46 N. Residual training remains blocked until that retained
matrix is complete. See the
[bounded admission report](newton/coarse-prior-admission-20261016.md).

### Phase 1 — Frozen physics prior

- fit one global Newton material across training actions;
- freeze it;
- report all held-out surface characteristics;
- establish unchanged, heuristic, and action-only baselines.

Exit: the residual is trained against a fixed, reproducible prior.

### Phase 2 — Offline residual

- build the sparse grid state representation;
- train the bounded post-rollout displacement correction;
- derive corrected deformation;
- complete latent and uncertainty ablations.

Exit: held-out action errors improve without deformation invalidity or
mechanics-gate bypass.

### Phase 3 — Gaussian update and NVS

- lift the sand region from multiview SAM masks;
- bind terrain Gaussians to the canonical MPM state;
- update mean, covariance, and orientation;
- compare held-out rendered depth and geometry.

Exit: one initial Gaussian map produces validated loaded and residual views
without scene retraining.

### Phase 4 — Planner proof

- fix planner candidates and thresholds;
- run all world-model baselines;
- score the chosen decision with Chrono;
- report regret, safety errors, and uncertainty.

Exit: the hybrid changes planning decisions and reduces Chrono-evaluated
regret or unsafe selections relative to static and MPM-only baselines.

### Phase 5 — Optional in-rollout residual

Proceed only if Phase 2-4 show that particle-level correction is useful but
post-rollout consistency limits performance.

Implement a periodic bounded grid-velocity residual in a qualified
differentiable Genesis or custom Warp solver. A later alternative is a
rotation-equivariant constitutive stress/plastic-return residual.

Relevant designs:

- [PhysCoRe](https://arxiv.org/html/2607.20653v1)
- [PhysReal](https://arxiv.org/html/2609.07532v1)
- [NCLaw](https://proceedings.mlr.press/v202/ma23a.html)

## Stop/go criteria

Advance beyond the offline residual only if the hybrid:

- improves frozen-MPM held-out surface and characteristic errors across
  position and load splits;
- retains positive, bounded deformation and small corrections;
- improves held-out-view depth and mask geometry;
- reduces Chrono-evaluated planner regret or unsafe choices;
- produces calibrated uncertainty on valid actions;
- raises uncertainty or rejects inputs near the mechanics and action-domain
  boundaries.

Stop or redesign if improvement appears only on the training positions, if
stress features fail backend-transfer diagnostics, if Gaussian geometry
improves only after retraining, or if the planner does not benefit.

## Claim boundary

If all first-stage gates pass, the supported claim is:

> A mechanics-gated MPM prior with a Chrono-supervised residual improves
> held-out synthetic terrain deformation, Gaussian-scene geometry, and
> open-loop planning decisions within a fixed proxy-foot action domain.

It does not establish:

- real-sand fidelity;
- material identification;
- arbitrary foot geometry or load transfer;
- sequential terrain-state prediction;
- closed-loop locomotion;
- zero-shot material-parameter generalization;
- general particle correspondence between SCM and MPM.

## Repository entry points

- [Main documentation index](README.md)
- [Repository current state](current-state.md)
- [Chrono oracle contract](chrono-oracle-run-contract.md)
- [Newton documentation](newton/README.md)
- [Authoritative Newton Phase 0](newton/phase0.md)
- [Cross-backend direction](forward-model-direction-20261006.md)
- [Companion simulation documentation](../../tera_splat_sim/docs/README.md)

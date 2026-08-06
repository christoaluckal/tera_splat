# Mass-Controlled MPM Calibration: Gap-Bridge Handoff

## Purpose

This document bridges the current implementation to the initial experimental goal:

> Given one localized real pre-action surface, one localized real post-action surface, and the action of placing and later removing a cylinder, estimate a noise-aware plausible region for only the effective Genesis parameters \(\log_{10}(E/\mathrm{Pa})\) and friction angle \(\phi\).

The result is not expected to uniquely identify true geotechnical material properties from one residual transition. The correct result may be a ridge or region of plausible parameter pairs.

The experiment is **mass-controlled gravitational loading**, not displacement-controlled indentation. The cylinder was placed on the terrain without an intentionally applied downward force.

## Authoritative experiment facts

| Property | Value |
|---|---:|
| Cylinder diameter | 5.75 in = 0.14605 m |
| Cylinder radius | 0.073025 m |
| Cylinder height | 2 in = 0.0508 m |
| Cylinder mass | 1.5 kg |
| Placement | Center of bed |
| Additional applied force | None |
| Initial condition | Placed at first contact with approximately zero velocity |
| Loading mechanism | Gravity acting on a dynamic rigid body |
| Available observation | One pre-action and one post-removal surface |
| Views per surface | Two, localized internally into a common frame |
| Free material parameters | Only \(\log_{10}E\) and \(\phi\) |

Derived cylinder properties:

| Property | Value |
|---|---:|
| Footprint area | 0.016753 m² |
| Weight, using \(g=9.81\,\mathrm{m/s^2}\) | 14.715 N |
| Nominal footprint pressure | 878.35 Pa |
| Equivalent uniform density | 1762.522 kg/m³ |
| \(I_{xx}=I_{yy}\), uniform solid cylinder approximation | 0.002322324 kg·m² |
| \(I_{zz}\), uniform solid cylinder approximation | 0.003999488 kg·m² |

### Critical geometry correction

The value `0.14605 m` is the **diameter**, not the radius. The correct radius is:

\[
r=\frac{0.14605}{2}=0.073025\ \mathrm m.
\]

Using `radius_m: 0.14605` makes the contact area four times too large and the nominal pressure four times too small. No calibration result obtained with that geometry is valid.

## Corrected action configuration

Use this as the action-model baseline:

```yaml
tool: cylinder

geometry:
  diameter_m: 0.14605
  radius_m: 0.073025
  height_m: 0.0508

rigid_body:
  mass_kg: 1.5
  equivalent_uniform_density_kg_m3: 1762.522
  inertia_model: uniform_solid_cylinder_approximation
  inertia_diagonal_kg_m2:
    - 0.002322324
    - 0.002322324
    - 0.003999488

contact_center_xy_world_m: [0.0, 0.0]

placement:
  mode: mass_controlled
  initial_condition: first_contact
  initial_linear_velocity_mps: [0.0, 0.0, 0.0]
  initial_angular_velocity_radps: [0.0, 0.0, 0.0]
  release_under_gravity: true
  additional_applied_force_n: [0.0, 0.0, 0.0]

first_contact:
  surface_statistic: percentile
  percentile: 99.0
  nominal_clearance_m: 0.0

loaded_settling:
  max_time_s: 5.0
  cylinder_speed_threshold_mps: 0.0005
  local_particle_speed_percentile: 99
  particle_speed_threshold_mps: 0.0005
  required_duration_s: 0.25

removal:
  mode: kinematic_lift_after_loaded_equilibrium
  upward_speed_mps: 0.005
  clearance_above_surface_m: 0.010

post_removal_settling:
  max_time_s: 5.0
  local_particle_speed_percentile: 99
  particle_speed_threshold_mps: 0.0005
  required_duration_s: 0.25
```

The contact center `[0, 0]` is valid only if the bed-frame origin is actually the physical center. Before simulation, overlay the 146.05 mm-diameter footprint on \(S_0\) and the observed residual deformation. Do not optimize the center using the real-data loss. Later, test fixed perturbations such as \(\pm 5\) mm in \(x\) and \(y\).

Mass-controlled mode must reject these fields:

```text
target_depth_m
downward_speed_mps
prescribed_downward_trajectory
additional_downward_force
```

Penetration depth is a simulation output, not an action input.

## Current gap summary

The project should not proceed directly to the full \(8\times8\) parameter sweep. The gaps must be closed in this order:

1. Correct the cylinder metadata.
2. Correct scan-frame bias and estimate measurement noise.
3. Implement true mass-controlled two-way rigid–MPM coupling.
4. Verify that the initial simulated bed matches the real \(S_0\) geometry.
5. Prove deterministic state restoration.
6. Run synthetic parameter recovery.
7. Run the real two-parameter loss landscape.
8. Transfer the validated MPM deformation to Gaussians.

## Gap 1: real-surface correction and noise estimation

The current deformation statistics reportedly include:

\[
\operatorname{median}(\Delta h)=+3.47\ \mathrm{mm}
\]

and

\[
V_{\mathrm{net}}=+81.4\ \mathrm{cm^3}.
\]

For a removed cylinder, these values are suspicious and may indicate a relative pre/post vertical offset or tilt. Such bias can make the optimizer fit artificial heave.

### Required preprocessing change

Compute:

\[
\Delta h_{\mathrm{corrected}}(x,y)
=h_1(x,y)-h_0(x,y)-(ax+by+c),
\]

where \(a\), \(b\), and \(c\) are estimated only from a known or assumed undeformed outer border. If the internal localization reliably constrains rotation, fit only the vertical offset \(c\).

Do not run unconstrained ICP over the entire terrain surface. The crater and heave are physical deformation and must not participate in registration.

### Preserve the two localized views separately

Export each localized view before fusion:

```text
S0_view0_height.npz
S0_view1_height.npz
S1_view0_height.npz
S1_view1_height.npz
```

On cells observed by both views, estimate:

\[
\sigma_0=1.4826\,\operatorname{MAD}(h_0^{v0}-h_0^{v1}),
\]

\[
\sigma_1=1.4826\,\operatorname{MAD}(h_1^{v0}-h_1^{v1}),
\]

and

\[
\sigma_{\Delta h}=\sqrt{\sigma_0^2+\sigma_1^2}.
\]

Use the initial Huber threshold:

\[
\delta_{\mathrm{Huber}}=1.345\sigma_{\Delta h}.
\]

Do not use the provisional 8.8 mm threshold for final calibration if it is comparable to the entire observed deformation.

### Required scan diagnostics

Export a visualization showing:

- Corrected \(\Delta h\).
- The 146.05 mm cylinder footprint.
- The valid-cell mask.
- The static border used for offset or plane estimation.
- Missing-data regions.

Report:

- Valid-cell fraction inside the cylinder footprint.
- Valid-cell fraction in the surrounding radial-profile region.
- Valid static-border fraction.
- \(\sigma_0\), \(\sigma_1\), and \(\sigma_{\Delta h}\).
- Pre- and post-correction median deformation and net volume.

## Gap 2: consistent first-contact initialization

For a vertical, flat-bottomed cylinder over a nonplanar pre-action surface, define the footprint:

\[
\mathcal F=
\left\{(x,y):(x-x_c)^2+(y-y_c)^2\le r^2\right\}.
\]

Estimate first-contact height robustly:

\[
z_{\mathrm{contact}}
=Q_{0.99}\left(h_0(x,y):(x,y)\in\mathcal F\right).
\]

Initialize the cylinder center at:

\[
z_{\mathrm{cylinder}}=z_{\mathrm{contact}}+\frac{h}{2}+c,
\]

where \(c\) is the initial clearance.

Use \(c=0\) for the baseline. Run \(c\in\{0,1,2\}\) mm as a later sensitivity test. Do not choose clearance based on whichever value minimizes the real-data loss.

## Gap 3: true mass-controlled rigid–MPM coupling

The existing prescribed-depth indenter cannot represent this experiment. The forward model needs a floating dynamic cylinder that exchanges momentum with the MPM terrain.

### Required runner behavior

The implementation must:

- Construct a vertical cylinder with `fixed=False`.
- Enable gravity on the rigid body.
- Set its equivalent density to approximately `1762.522 kg/m3`.
- Explicitly set mass to `1.5 kg` if the installed Genesis API permits it.
- Assert that the actual mass differs from 1.5 kg by less than 0.1%.
- Enable two-way rigid–MPM coupling.
- Use zero coupling restitution.
- Keep contact friction and softness fixed across every \((\log E,\phi)\) candidate.
- Apply no pose, velocity, depth, or force command during loading.
- Log cylinder position, orientation, linear velocity, and angular velocity every frame.
- Start kinematic removal only after loaded equilibrium.
- Record whether each settling phase stopped by equilibrium or timeout.

### Coupling validation tests

#### Test A: free fall

Run the cylinder without terrain. Its vertical acceleration should satisfy approximately:

\[
a_z\approx-9.81\ \mathrm{m/s^2}.
\]

This proves that the body is dynamic and gravity is active.

#### Test B: mass and inertia

After scene construction, assert:

```python
assert abs(cylinder_mass - 1.5) / 1.5 < 1e-3
```

Log the mass and inertia actually used by Genesis.

#### Test C: two-way contact

Release the cylinder at first contact over a stiff MPM bed.

Acceptance criteria:

- The cylinder does not pass through the bed.
- The terrain deforms.
- The cylinder decelerates due to contact.
- The cylinder reaches a stable supported height.
- At equilibrium, the average upward reaction is approximately \(mg\).

If the terrain deforms while the cylinder continues in free fall, the coupling is one-way or misconfigured.

#### Test D: mass monotonicity

Using one fixed material, run masses of 0.75, 1.5, and 3.0 kg.

Require:

\[
\operatorname{sinkage}_{0.75}
<\operatorname{sinkage}_{1.5}
<\operatorname{sinkage}_{3.0}.
\]

This is the strongest compact check that mass, gravity, and contact jointly control the response.

## Gap 4: settling and removal protocol

Do not use one extreme particle velocity as the only equilibrium measure; a few numerical outliers can prevent termination.

During loaded settling, require both:

- Cylinder speed below threshold.
- The 99th percentile of local terrain-particle speed below threshold.

Both must remain below threshold for the specified continuous duration. Restrict terrain-particle checks to the local interaction region.

After removal, use the local terrain-particle criterion without the cylinder condition.

Compare maximum post-removal settling durations of 5 and 10 seconds once. If the residual DEM difference is below measured scan noise, use 5 seconds thereafter.

Removal was not precisely measured in the real experiment. Treat the simulated upward speed as a fixed protocol assumption, not an optimized action variable. Run a sensitivity check using 2.5, 5, and 10 mm/s. The residual DEM should change less than the measured scan noise.

## Gap 5: initial MPM bed verification

Before releasing the cylinder, project the settled simulation state onto the real DEM grid:

\[
h_{0,\mathrm{sim}}=\Pi_{\mathrm{DEM}}(Z_0).
\]

Verify:

- Axis direction and handedness.
- Metric scale.
- Surface height datum.
- Cylinder footprint location.
- Topography within and around the footprint.
- Valid surface coverage.
- Consistency of the simulated and real regions of interest.

The simulated bed need not reproduce individual grains, but it must reproduce the local pre-action surface that determines first contact.

### Restore a complete physical state

A PLY containing only particle positions is not a complete reusable MPM state. Save or deterministically reconstruct at least:

```text
pos
vel
C
F
Jp
active
```

Restore the identical state before every cylinder rollout and no-cylinder control.

If the base drifts without contact, run a no-cylinder control for every candidate parameter pair and define the action-conditioned prediction as:

\[
\Delta h_{\mathrm{sim}}
=\Delta h_{\mathrm{cylinder}}
-\Delta h_{\mathrm{no\ cylinder}}.
\]

Cache one no-cylinder result for each \((\log E,\phi)\) pair.

## Calibration objective

For a candidate

\[
\theta=(\eta,\phi),\qquad
\eta=\log_{10}(E/\mathrm{Pa}),
\]

the forward model is:

\[
\widehat{\Delta h}(\theta)
=\Pi_{\mathrm{DEM}}
\left[
\operatorname{GenesisMPM}(Z_0,A;\theta)
\right].
\]

Use the same DEM grid, region of interest, valid-data mask, and processing for real and simulated surfaces.

A suitable loss is:

\[
\begin{aligned}
\mathcal L(\eta,\phi)={}&
w_h\,\operatorname{Huber}
\left(\Delta h_{\mathrm{sim}}-\Delta h_{\mathrm{real}}\right)\\
&+w_d\frac{|\widehat d-d|}{d_{\mathrm{scale}}}\\
&+w_r\operatorname{MAE}\left(\widehat p(r)-p(r)\right)\\
&+w_v\frac{|\widehat V^- -V^-|+|\widehat V^+ -V^+|}{V_{\mathrm{scale}}}.
\end{aligned}
\]

Here:

- \(d\) is a robust depression-depth statistic.
- \(p(r)\) is the radial deformation profile about the known bed center.
- \(V^-\) is depressed volume.
- \(V^+\) is heaved volume.

Suggested initial normalized weights are:

\[
w_h=0.50,\quad
w_d=0.15,\quad
w_r=0.20,\quad
w_v=0.15.
\]

Log every component separately. A low total loss is not interpretable if one component dominates due to units or normalization.

## Parameter-search plan

Search only:

\[
\log_{10}(E/\mathrm{Pa})\in[4,7],
\qquad
\phi\in[15^\circ,45^\circ].
\]

Keep all other material, contact, grid, time-step, initialization, settling, and removal quantities fixed.

### Execution sequence

1. Run one candidate at \((\log_{10}E,\phi)=(5.5,30^\circ)\).
2. Confirm nonzero sinkage, stable support, successful removal, and residual terrain deformation.
3. Repeat the exact rollout twice from the same checkpoint and verify determinism.
4. Generate a synthetic observation using a known parameter pair.
5. Run a \(3\times3\) synthetic search and verify recovery of the known neighborhood.
6. Run a \(3\times3\) search against the real transition.
7. Inspect maps, radial profiles, volumes, sinkage, termination reasons, and every loss component.
8. Run the full \(8\times8\) real-data landscape.
9. Refine locally only if the coarse landscape contains a meaningful basin.
10. Repeat the landscape under scan-noise perturbations to estimate uncertainty.

Because there is only one real transition, do not claim held-out real-world generalization.

## Required scientific result

Define the plausible set:

\[
\Theta_{\mathrm{plausible}}
=\left\{(\eta,\phi):
\mathcal L(\eta,\phi)
\le \mathcal L_{\min}+\epsilon
\right\},
\]

where \(\epsilon\) is derived from two-view disagreement and scan-noise perturbations.

Interpret the loss landscape explicitly:

| Landscape | Interpretation |
|---|---|
| Compact basin | Both effective parameters may be practically constrained |
| Narrow in \(\log E\), broad in \(\phi\) | \(E\) is better constrained |
| Broad in \(\log E\), narrow in \(\phi\) | \(\phi\) is better constrained |
| Diagonal ridge | The parameters compensate for one another |
| Boundary minimum | Search bounds or fixed assumptions are inadequate |
| Irregular/noisy landscape | Simulation instability, nondeterminism, or measurement mismatch |

With only a residual post-removal surface, expect \(\phi\) to be more observable than \(E\), because much of the elastic response has disappeared. A broad or diagonal plausible region is a valid result.

Report the inferred values as **effective Genesis parameters**, not unique physical soil constants.

## Readiness gates

Do not start the full \(8\times8\) sweep until all gates pass.

### Gate A: experiment metadata

- [ ] Radius is `0.073025 m`.
- [ ] Height is `0.0508 m`.
- [ ] Mass is `1.5 kg`.
- [ ] Center overlay is visually verified.
- [ ] No target depth or applied downward force remains in the configuration.

### Gate B: scan data

- [ ] Both views are preserved separately for \(S_0\) and \(S_1\).
- [ ] Pre/post vertical offset or plane bias is corrected using only a static border.
- [ ] Two-view disagreement produces a defensible noise estimate.
- [ ] Valid coverage is sufficient under and around the footprint.

### Gate C: physical runner

- [ ] Free-fall acceleration is correct.
- [ ] Runtime mass is 1.5 kg within 0.1%.
- [ ] Two-way contact is demonstrated.
- [ ] Sinkage is monotonic with mass.
- [ ] Cylinder reaches loaded equilibrium.
- [ ] Removal produces a stable residual bed.

### Gate D: reproducibility

- [ ] A complete settled MPM state is restored for each run.
- [ ] Duplicate rollouts agree within numerical tolerance.
- [ ] No-cylinder drift is characterized or subtracted.
- [ ] Synthetic \(3\times3\) parameter recovery succeeds.

## Bridge to deformable Gaussian splats

Splat deformation is downstream of calibration. Do not use the splat result to hide or compensate for a bad MPM forward model.

After the calibration diagnostics pass, transfer MPM motion to terrain Gaussians using nearby-particle interpolation:

\[
\mu_i'=\mu_i+
\sum_p w_{ip}(x_p'-x_p),
\]

and use the local affine deformation estimate for covariance:

\[
\Sigma_i'=\bar F_i\Sigma_i\bar F_i^\top.
\]

The first splat milestone should use one fixed plausible \((\log E,\phi)\) pair. The next should render an ensemble from \(\Theta_{\mathrm{plausible}}\) to show uncertainty in the predicted terrain deformation.

## Definition of done for this phase

This phase is complete when the repository produces:

1. Corrected action metadata and a footprint overlay.
2. Corrected real \(\Delta h\), masks, coverage statistics, and scan-noise estimates.
3. Passing free-fall, mass, two-way-contact, and mass-monotonicity tests.
4. A deterministic mass-controlled cylinder rollout from a reusable settled bed.
5. A passing synthetic recovery test.
6. A complete two-dimensional real-data loss landscape.
7. A noise-aware plausible region for effective \(\log_{10}E\) and \(\phi\).
8. A clear statement that the result comes from one real residual transition and is not held-out validation.

The immediate priority is scan correction and coupling validation. Running the full parameter sweep before these gates would optimize the wrong physical experiment.

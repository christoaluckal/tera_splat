# Newton experiment report — consolidated record

Last updated: 2026-10-08  
Status: canonical index and interpretation of the Newton experiments. Original
dated reports and raw artifacts remain the provenance records.

## Bottom line

Newton is a mechanically qualified, fixed-domain sim-to-sim surrogate with a
repeatable local map-level calibration. It is not a validated material model
or a general terrain-characteristics predictor.

The current qualified contract is:

| item | value |
|---|---|
| voxel / transfer / integration | 7.8125 mm / PIC / PIC |
| bases | P0 strain / S2 collider / Q1 velocity |
| contact | stock public Newton contact |
| coupling | 8 proxy iterations / 16 rigid substeps |
| selected timestep | 0.25 ms |
| Chrono action | guided 1.5 kg cylinder, radius 73.025 mm, center `(0,+5) mm` |
| observation | Chrono-accepted loaded time, then 0.25 s residual |
| support | fixed 14,161-cell Chrono mask |

Every candidate uses fresh preparation and a continuous loading/removal run.
Saved particle arrays are archival, not restart checkpoints. A failed mechanics
gate receives no objective and is not an optimizer observation.

## Experiment chronology

### 1. Initial preparation and coupling diagnosis

`newton_convergence_coupling_20260906` established the first preparation and
continuous-response path. APIC at 0.125 ms produced an upward top-layer mode;
the original explicit guide produced timestep-dependent gravity lag and
trajectory-wide analytic-cylinder penetration. Neither result was eligible for
calibration.

`newton_failure_resolution_20260906` corrected the preparation transfer to PIC
and used a circumscribed 128-segment collider, zero projection threshold, and a
small declared numerical guard. The PIC preparation matrix passed its speed,
height, and adjacent-map gates, and the full guided response became finite with
zero center penetration. This qualified a numerical starting point, not a
material fit.

### 2. Response/contact numerical studies

The first response matrix (`newton_response_convergence_20260906`) failed
because the explicit guide update accumulated approximately `g*T*dt` position
error. The native proxy follow-up (`newton_response_convergence_native_proxy_20260906`)
removed that dominant drift, but the fine adjacent sinkage pair missed the
0.5 mm gate by 0.086819 mm and exposed a roughly 10 mm collider-support gap.

The cylinder-only raised-support experiment
(`newton_collider_support_20260908`) passed a complete 0.5/0.25/0.125 ms
matrix at the 100 kPa smoke point and improved the shared A/B objective from
12.638 to 12.189 mm. It is not a promoted collision model: the raised proxy
omits a lower analytic-cylinder slice, and the later 25 kPa test put 1,330
particle centers inside that analytic cylinder by up to 5.950 mm.

The private, version-locked full-volume activation diagnostic
(`newton_contact_activation_20260910`) preserved analytic collision coverage
and passed all individual mechanics rows. Its 0.5-to-0.25 ms sinkage change was
0.975 mm, so the complete matrix remained `not_demonstrated`; private activation
overrides are diagnostic evidence only.

The active resolution is the public stock-contact study
(`newton_public_contact_20260914`). At the refined 7.8125 mm grid, 8/16
coupling passed the complete three-level response matrix:

| pair | loaded/residual map RMSE | loaded/residual max | sinkage difference |
|---|---:|---:|---:|
| 0.5 → 0.25 ms | 0.035 / 0.035 mm | 0.218 / 0.213 mm | 0.331 mm |
| 0.25 → 0.125 ms | 0.058 / 0.054 mm | 0.304 / 0.310 mm | 0.422 mm |

This qualifies a numerical domain, not Newton material semantics. The earlier
15.625 mm grid and public 4/8 coupling remain rejected or diagnostic because of
contact-location/sinkage bias.

### 3. Local material study

The fixed-domain BayesOpt-style campaign evaluated 21 candidates: 19 passed
all preparation/response mechanics gates and two near `mu≈0.273` were rejected
by strict center penetration. The valid incumbent is:

```text
E  = 70.46 kPa
nu = 0.237231507
mu = 0.305497980
```

It improved the A0 scalar objective from 12.698 to 8.823 mm; an independent
fresh replay scored 8.815 mm (0.008 mm difference). This demonstrates
repeatable local optimization inside one simulator domain. It does not prove
optimizer convergence, material identification, or transfer.

The 25 kPa stiffness-only screen is an important negative result:
unconstrained DEM error would improve from 12.189 to 11.207 mm, but the run
failed guide and strict penetration gates. Numerical validity must therefore
take precedence over a lower scalar score.

### 4. Frozen action-transfer holdouts

All results below use the incumbent and, where available, the unchanged
100 kPa control. `--` means invalid or deliberately unscored; invalid runs
have no objective.

| action | incumbent | control | interpretation |
|---|---|---|---|
| A1, 3.0 kg | invalid: 31 centers, 1.332 um | valid, 16.289 mm | selected material fails high-load admissibility |
| A2, 2.0 kg | invalid: 18 centers, 0.875 um | 13.211 / 3.993 / 18.434 mm | boundary failure |
| A3, 1.75 kg | invalid: 2 centers, 0.041 um | 11.353 / 3.420 / 15.866 mm | boundary failure |
| A4, 1.625 kg, y=+5 mm | 7.911 / 2.368 / 11.087 mm | 11.888 / 3.592 / 16.591 mm | valid transfer; incumbent wins scalar terms |
| A5, x=+50 mm | 3.379 / 1.224 / 4.311 mm | 3.272 / 0.961 / 4.623 mm | mixed ranking; control wins scalar |
| A6, x=-50 mm | 3.088 / 1.120 / 3.936 mm | 4.073 / 1.201 / 5.743 mm | incumbent wins scalar |
| A7, radius=55 mm | invalid | 2.643 / 0.574 / 4.138 mm | radius boundary |
| A8, radius=65 mm | invalid | unscored | radius boundary |
| A9, y=+50 mm | 8.490 / 2.543 / 11.894 mm | unscored | valid but characteristic stress test |
| A10, y=+25 mm | 8.146 / 2.451 / 11.391 mm | 12.244 / 3.705 / 17.079 mm | prospective interior holdout |

Triples in the table are `objective / loaded RMSE / residual-footprint RMSE`
in millimetres. A4--A6 establish some admissible transfer. A1--A3 and A7--A8
establish that the selected material point has a narrow mechanics envelope; the
exact threshold is not inferred.

### 5. Characteristic fidelity

The scalar map objective hides amplitude errors. A9 has valid timing and
mechanics but +14.730 mm loaded peak error and -178.812 cm3 volume error. A10
has +10.624 mm peak error and -171.121 cm3 volume error. Centroid can remain
accurate while peak and volume are wrong.

The A10 stop/go set then evaluated two additional candidates selected from the
prior A0 study, with the numerical contract unchanged:

| candidate | objective | loaded multi-score | residual multi-score |
|---|---:|---:|---:|
| incumbent | 8.146 mm | 3.154 | 11.997 |
| C2: `log10(E)=4.812`, `nu=.200`, `mu=.326` | 9.097 mm | 3.226 | 13.303 |
| C7: `log10(E)=5.092`, `nu=.155`, `mu=.411` | 10.375 mm | 3.956 | 15.342 |
| unchanged control | 12.244 mm | 4.900 | 18.292 |

Both added candidates passed mechanics but neither improved the incumbent's
held-out multi-characteristic profile. This supports stopping broad
parameter-only Newton search for the current model form. It does not prove
that a different constitutive model, state representation, or objective could
not improve the result.

## Canonical interpretation

Supported:

* Newton has a reproducible, mechanics-qualified numerical domain.
* The A0-fitted point improves a scalar map objective locally and repeats.
* Some 1.625 kg spatial/mass transfers are valid.
* The current global parameterization does not reliably predict peak or volume.
* Strict gates reveal a narrow admissible envelope that scalar optimization
  alone would hide.

Not supported:

* real-sand or material identification;
* general terrain-deformation prediction;
* grain-level Chrono/Newton equivalence;
* transfer outside the tested action family;
* universal characteristic superiority of the incumbent;
* validated Gaussian deformation transfer or planner improvement.

The defensible decision is: **stop broad Newton parameter-only refinement and
use Newton, if retained, as a bounded physics prior for a characteristic-level
discrepancy model.** Genesis remains a separate unresolved numerical branch;
its convergence limitations must not be silently merged with Newton evidence.

## Report inventory and provenance

### Canonical summaries

* [Newton fixed-domain contract](newton-fixed-domain.md)
* [Chrono→Newton model card](chrono_newton_forward_model_card_20261002.md)
* [Forward-model current state](forward-model-current-state-20261004.md)
* [Historical Chrono→Newton ledger](historical-forward-model-evidence-20261004.md)
* [A5 addendum](newton-handoff-a5-addendum-20261002.md)
* [A10 protocol/results](forward-model-a10-protocol-20261004.md)
* [Stop/go direction](forward-model-direction-20261006.md)

### Numerical diagnostics

* [`newton_convergence_coupling_20260906`](../diagnostics/newton_convergence_coupling_20260906/README.md)
* [`newton_failure_resolution_20260906`](../diagnostics/newton_failure_resolution_20260906/README.md)
* [`newton_response_convergence_20260906`](../diagnostics/newton_response_convergence_20260906/README.md)
* [`newton_response_convergence_native_proxy_20260906`](../diagnostics/newton_response_convergence_native_proxy_20260906/README.md)
* [`newton_collider_support_20260908`](../diagnostics/newton_collider_support_20260908/README.md)
* [`newton_contact_activation_20260910`](../diagnostics/newton_contact_activation_20260910/README.md)
* [`newton_calibration_20260910`](../diagnostics/newton_calibration_20260910/README.md)
* [`newton_public_contact_20260914`](../diagnostics/newton_public_contact_20260914/README.md)
* [`newton_preparation_20260903`](../diagnostics/newton_preparation_20260903/README.md)

### Transfer and stop/go artifacts

* [`forward_model_transfer_20261002`](../diagnostics/forward_model_transfer_20261002/README.md)
* [`newton_mass1p625kg_holdout_20261001`](../diagnostics/newton_mass1p625kg_holdout_20261001/README.md)
* [`newton_mass1p75kg_holdout_20260930`](../diagnostics/newton_mass1p75kg_holdout_20260930/README.md)
* [`newton_mass2kg_holdout_20260930`](../diagnostics/newton_mass2kg_holdout_20260930/README.md)
* [`newton_mass3kg_holdout_20260922`](../diagnostics/newton_mass3kg_holdout_20260922/README.md)
* [`newton_lateral_x50mm_holdout_20261001`](../diagnostics/newton_lateral_x50mm_holdout_20261001/README.md)
* [`forward_model_stopgo_20261006_A10`](../diagnostics/forward_model_stopgo_20261006_A10/summary.json)
* [`stop/go multi-characteristic scores`](../diagnostics/forward_model_stopgo_20261006_A10/multicharacteristic_scores.csv)

Superseded diagnostics remain useful for failure provenance, but only the
public 7.8125 mm, PIC/PIC, P0/S2/Q1, stock-contact, 8/16 domain is active for
the Newton evidence summarized here.

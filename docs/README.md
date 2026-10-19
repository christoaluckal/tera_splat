# Tera Splat documentation

Last updated: 2026-10-17

Tera Splat studies a planning-oriented hybrid terrain model:

    Chrono synthetic ground truth
        -> mechanics-gated MPM prior
        -> learned discrepancy and uncertainty
        -> Gaussian terrain update
        -> open-loop robot planning

Chrono is the synthetic oracle. Newton is the recommended first offline MPM
prior because its public numerical/contact domain and state export are already
qualified. Genesis remains a separate comparator and possible future
differentiable backend.

## Start here

1. [Hybrid model design](hybrid-chrono-mpm-residual-gaussian-planning-20261008.md)
   — complete proposed architecture, backend decision, data split, losses,
   latent-state ablations, Gaussian transfer, and planner validation.
2. [Current repository state](current-state.md) — authoritative live state for
   Chrono, Genesis, Newton, artifacts, and execution constraints.
3. [Newton documentation index](newton/README.md) — all Newton contracts,
   reports, boundaries, and dated provenance.
4. [Fresh hierarchical Phase 0](newton/fresh-hierarchical-phase0-20261017.md)
   — current fresh-only variation-characterization and geometric-utility protocol.
5. [Current Newton handoff](newton/handoff.md) — active Newton conclusion and
   next permitted work.
6. [Newton running analysis](newton/running-analysis.md) — chronological
   decision log for tracking new evidence.
7. [Cross-backend direction](forward-model-direction-20261006.md) — why the
   project moved from parameter-only fitting to a hybrid residual model.
8. [Chrono oracle contract](chrono-oracle-run-contract.md) — target episode,
   timing, support, preparation, and scoring rules.
9. [Contributor guidance](contributor-guidance.md) — repository, editing, and
   evidence-maintenance rules.

Files in [archive](archive/) are historical provenance. They are not current
instructions.

## Topic index

| Topic | Entry point |
| --- | --- |
| Current status | [current-state.md](current-state.md) |
| Hybrid architecture | [hybrid-chrono-mpm-residual-gaussian-planning-20261008.md](hybrid-chrono-mpm-residual-gaussian-planning-20261008.md) |
| Backend decision | [forward-model-direction-20261006.md](forward-model-direction-20261006.md) |
| Newton current handoff | [newton/handoff.md](newton/handoff.md) |
| Newton dated analysis | [newton/running-analysis.md](newton/running-analysis.md) |
| Newton full experiment record | [newton/experiment-consolidated-20261008.md](newton/experiment-consolidated-20261008.md) |
| Static 35 mm proxy qualification | [newton/static-proxy-qualification-20261009.md](newton/static-proxy-qualification-20261009.md) |
| Bounded coarse-prior admission | [newton/coarse-prior-admission-20261016.md](newton/coarse-prior-admission-20261016.md) |
| Fresh hierarchical Phase 0 | [newton/fresh-hierarchical-phase0-20261017.md](newton/fresh-hierarchical-phase0-20261017.md) |
| Newton fixed numerical domain | [newton/fixed-domain.md](newton/fixed-domain.md) |
| Newton A0-A10 evidence | [newton/historical-evidence-20261004.md](newton/historical-evidence-20261004.md) |
| Chrono target definition | [chrono-oracle-run-contract.md](chrono-oracle-run-contract.md) |
| Chrono oracle qualification | [chrono-oracle-diagnostics.md](chrono-oracle-diagnostics.md) |
| Genesis numerical blocker | [experiment_problems.md](experiment_problems.md) |
| Chrono-only surrogate | [chrono-characteristic-surrogate-20261003.md](chrono-characteristic-surrogate-20261003.md) |
| Diagnostics inventory | [../diagnostics/README.md](../diagnostics/README.md) |
| Simulation, NVS, and planning | [tera_splat_sim documentation](../../tera_splat_sim/docs/README.md) |
| RGB-D and Gaussian capture | [splat RGB-D capture](../../tera_splat_sim/docs/splat-rgbd-capture.md) |
| Planner outputs | [planning and outputs](../../tera_splat_sim/docs/planning-and-outputs.md) |

## Current decision snapshot

- No pre-2026-10-17 Chrono episode, particle bed, MPM preparation, or response
  is admissible for the current Phase 0 dataset or model score.
- The fresh matrix is at 1/15 complete and usable cases. The separate
  centered-31 N duplicate sentinel is qualification evidence rather than
  training data. It found exact
  Chrono/bed output and small, compatible Newton variation, so matrix expansion
  is permitted. Exact equality remains diagnostic, not a requirement.
- The first progressive rung is the five-position 31 N slice with a 3/1/1
  whole-position train/validation/test split. Canonical `center_f031n` is
  complete and passes all local positive-skill checks; the rung is 1/5.
- The current hard gates are provenance and numerical integrity.
  Contact overlap is classified as an artifact unless it is gross; local
  geometric skill in the footprint and twice-radius region is the primary
  physics-utility gate.

- Chrono SCM supplies accepted surface maps and support outcomes. It is
  reproducible synthetic ground truth, not real-sand measurement.
- Broad parameter-only tuning of the current Newton model form is stopped.
  Newton is retained as a bounded mechanics prior.
- The first learned model is an offline, post-rollout displacement residual.
  It is supervised through Chrono-observable surfaces and renders.
- Corrected particle position is the primary output. Local orientation and
  Gaussian covariance come from a compatible deformation gradient, not an
  independent particle quaternion.
- MPM material parameters are fit once across training actions and frozen for
  held-out position and load evaluation.
- Stress, deformation, plastic, and velocity-gradient features are ablated as
  privileged MPM inputs; they are not treated as real-world observations.
- Historical 35 mm runs failed strict zero penetration and were not declared
  converged. In the fresh campaign, overlap is measured and classified; only
  gross interaction failure blocks geometric-utility evaluation.
- The old centered-load and bounded-gate results are quarantined historical
  diagnostics. They do not admit or exclude any load in the fresh 15-action
  campaign.
- Gaussian transfer updates terrain means, covariance, and orientation without
  retraining the scene.
- Initial planning is offline and open loop. Candidate contacts are independent
  counterfactuals from the same initial terrain.

## Evidence snapshot

### Chrono

- Active A0 oracle: A0_oracle_guided_offset_5mm_gate6mm_v1.
- Map spacing: 5 mm.
- Fixed valid support: 14,161 cells.
- Loaded time: 3.595 s for A0.
- Residual observation: 0.25 s after removal.

### Genesis

- Accepted bed: 307,461 particles at 5 mm on n128.
- Confirmed incumbent: E=20.433 kPa, friction angle=14.727 degrees,
  Poisson ratio=0.101895.
- Loaded RMSE: 1.864 mm.
- Residual-footprint RMSE: 13.678 mm.
- Residual recovery remains too high and response convergence is unresolved.

### Newton

- Qualified domain: 7.8125 mm, PIC/PIC, P0/S2/Q1, public stock contact,
  0.25 ms, 8 proxy iterations, and 16 rigid substeps.
- A0 incumbent: E=70.46 kPa, Poisson ratio=0.237231507, friction
  coefficient=0.305497980.
- A0 objective improved from 12.698 to 8.823 mm and replayed at 8.815 mm.
- The incumbent is invalid at tested 1.75-3.0 kg actions and 55/65 mm radii.
- Valid A9/A10 responses still have approximately 10-15 mm peak error and
  171-179 cm3 displaced-volume error.
- The 35 mm, 31 N center sentinel is not mechanics-qualified at 0.25 ms:
  eight transient particle centers penetrated by at most 3.759 micrometers.
- Bounded policy v2 admits that action and the centered 46 N action for
  residual-pilot data only; it does not change their strict status.
- The 61 N boundary passes depth/fraction limits but fails loaded-state
  clearance and is retained only as out-of-domain evidence.

The supported conclusion is local, mechanics-gated sim-to-sim improvement.
General terrain prediction, real material identification, Gaussian-transfer
accuracy, and planner benefit are not yet demonstrated.

## Repository boundaries

| Repository or directory | Ownership |
| --- | --- |
| tera_splat | MPM preparation, response, scoring, residual-model direction, and joined evidence |
| tera_splat_sim | Chrono episode generation, robot proxy, RGB-D capture, Gaussian inputs, and planner prototype |
| diagnostics | Lightweight reviewable evidence and summaries |
| outputs on the data volume | Large states, maps, point clouds, videos, and study artifacts |
| PhysGaussian sibling repository | Reference MPM-to-Gaussian implementation |

Chrono and MPM start independently from the same initial terrain. Never apply
the same action again to a Chrono-deformed surface and call it a paired MPM
response.

## Environments

Genesis instrumentation:

    conda environment: chrono_splat

Newton tooling:

    /data/christoa/conda/envs/newton_splat

Generated calibration artifacts belong under:

    /data/christoa/Chrono/tera_splat/outputs

## Main entry points

Chrono/Genesis:

    scripts/build_chrono_settled_bed.py
    scripts/run_chrono_genesis_bridge.py
    scripts/run_chrono_genesis_bayesopt.py
    scripts/run_mass_controlled_terrain.py
    scripts/render_chrono_genesis_pointcloud_dem_comparison.py
    scripts/diagnose_chrono_genesis_model_form.py

Newton:

    scripts/run_newton_prepared_bed.py
    scripts/run_newton_cylinder_diagnostic.py
    scripts/analyze_newton_preparation_convergence.py
    scripts/analyze_newton_response_convergence.py
    scripts/analyze_forward_model_transfer_v3.py

Do not launch a study until its oracle, initial bed, geometry, action timing,
resolution, seed policy, mechanics gates, split, and acceptance metrics are
frozen.

## Documentation maintenance

- Update [current-state.md](current-state.md) when the repository-wide
  conclusion, incumbent, blocker, or next experiment changes.
- Update [newton/handoff.md](newton/handoff.md) when the active Newton contract
  or next permitted work changes.
- Append dated Newton decisions to
  [newton/running-analysis.md](newton/running-analysis.md).
- Put detailed new Newton reports under [newton](newton/).
- Keep dated reports as provenance; link forward instead of rewriting history.
- Keep [archive](archive/) immutable except for its index.
- Synchronize Chrono-facing changes with the companion
  [tera_splat_sim docs](../../tera_splat_sim/docs/README.md).

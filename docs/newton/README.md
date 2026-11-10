# Newton documentation index

Last updated: 2026-11-10

This directory contains the Newton-specific numerical contracts, experiment
reports, transfer evidence, and handoff material for the Chrono-to-MPM terrain
forward-model study.

## Read in this order

1. [Completed Phase 1 authority](phase1.md) — sole authority for the failed
   v1/v2 paths, successful direct-v4 exit, Phase 2 destination, and
   expertise-aware claim boundary.
2. [Phase 1 chronological record](phase1-running.md) — dated implementation
   evidence, frozen identities, decisions, blockers, and final qualification.
3. [Phase 1 completion report](phase1-completion-20261110.md) — protected D1
   metrics, model-type conclusion, artifact identities, and claim boundary.
4. [Alternate MPM-backbone handoff](../mpm-backend-pipeline-handoff.md) —
   backend-neutral adapter and qualification contract that requires a raw MPM
   or MPM-plus-neural final model.
5. [Completed Phase 0](phase0.md) — frozen action ledger, claims, evidence, and
   artifact routing for the completed residual proof.
6. [Fresh hierarchical Phase 0 protocol](fresh-hierarchical-phase0-20261017.md)
   — frozen fresh-only evidence boundary, variation characterization, and
   geometric-utility hierarchy.
7. [Running analysis through 2026-10-19](running-analysis.md) — detailed
   pre-consolidation decision provenance; current entries belong in
   `phase1-running.md`.
8. [Static 35 mm proxy qualification](static-proxy-qualification-20261009.md)
   — original strict Phase 0 sentinel result and expansion stop gate.
9. [Bounded coarse-prior admission](coarse-prior-admission-20261016.md) —
   strict/coarse status split, frozen v2 limits, and pilot restart.
10. [Consolidated experiment report](experiment-consolidated-20261008.md) —
   canonical interpretation of preparation, contact, calibration, transfer,
   and stop/go results.
11. [Fixed-domain contract](fixed-domain.md) — qualified historical numerical and mechanics
   configuration.
12. [Hybrid model design](../hybrid-chrono-mpm-residual-gaussian-planning-20261008.md)
   — historical design background; `phase1.md` owns the current destination.

Reliable one-action prediction is now established by direct-v4 within the
frozen synthetic domain. The next prospective research stage is a sequential
footprint world model. Inputs remain robotics-defensible or simulator-native.
If progress requires deeper constitutive soil theory, the claim and expertise
boundary must be revisited before the pipeline expands.

`phase1.md` owns all new Phase 1 work. `phase0.md` remains the sole authority
for its completed campaign; all other files are frozen protocols,
compatibility pointers, or dated provenance.

## Canonical reports

| Date | Document | Purpose |
| --- | --- | --- |
| live | [Completed Phase 1 authority](phase1.md) | Failed v1/v2 paths, successful direct-v4 exit, Phase 2 destination, and claim boundary |
| live | [Phase 1 chronological record](phase1-running.md) | Append-only implementation evidence, hashes, decisions, and final qualification |
| live | [Newton handoff pointer](handoff.md) | Compatibility entry point to the completed Phase 1 result and Phase 2 boundary |
| live | [Alternate MPM-backbone handoff](../mpm-backend-pipeline-handoff.md) | Backend-neutral raw-MPM or MPM-plus-neural execution contract |
| 2026-11-10 | [Phase 1 completion report](phase1-completion-20261110.md) | Protected D1 result, completion audit, model-type conclusion, and claim boundary |
| 2026-10-22 | [Completed Phase 0](phase0.md) | Frozen ledger, chronology, result, and claims |
| 2026-09-21 | [Fixed-domain contract](fixed-domain.md) | Public stock-contact Newton domain and local material study |
| 2026-09-28 | [Original handoff](handoff-20260928.md) | State before A2-A10; retained for provenance |
| 2026-10-02 | [Forward-model card](forward-model-card-20261002.md) | Inputs, outputs, established claims, and exclusions |
| 2026-10-02 | [Calibration protocol](calibration-protocol-20261002.md) | Mechanics gates and multi-characteristic scoring |
| 2026-10-02 | [Calibration result](calibration-result-20261002.md) | A0 re-score and evidence boundary |
| 2026-10-02 | [Transfer audit](transfer-audit-20261002.md) | Peak, volume, footprint, and centroid audit |
| 2026-10-04 | [Historical evidence](historical-evidence-20261004.md) | Chrono A0-A10 and Newton transfer ledger |
| 2026-10-04 | [Dated current state](current-state-20261004.md) | Concise pre-stop/go operational state |
| 2026-10-04 | [Handoff update](handoff-update-20261004.md) | A2-A10 bridge from the original handoff to the stop/go decision |
| 2026-10-08 | [Consolidated experiment report](experiment-consolidated-20261008.md) | Full campaign interpretation and stop/go decision |
| 2026-10-09 | [Static 35 mm proxy qualification](static-proxy-qualification-20261009.md) | Initial static sentinel, mechanics failure, and expansion stop gate |
| 2026-10-16 | [Bounded coarse-prior admission](coarse-prior-admission-20261016.md) | Frozen residual-data gate without a strict mechanics claim |
| 2026-10-17 | [Fresh hierarchical Phase 0](fresh-hierarchical-phase0-20261017.md) | Superseding fresh-only protocol; old outputs quarantined |

## Action-specific reports

| Date | Document | Finding |
| --- | --- | --- |
| 2026-10-02 | [A5 spatial transfer](a5-spatial-transfer-20261002.md) | Both materials valid; control wins scalar objective |
| 2026-10-02 | [A6 mirrored transfer](a6-spatial-transfer-20261002.md) | Both valid; incumbent wins scalar objective |
| 2026-10-03 | [A7 geometry boundary](a7-geometry-boundary-20261003.md) | Incumbent invalid at 55 mm radius |
| 2026-10-03 | [Radius boundary](radius-boundary-20261003.md) | Incumbent invalid at 55 and 65 mm radii |
| 2026-10-04 | [A9 validation](a9-validation-20261004.md) | Centroid can be accurate while peak and volume fail |
| 2026-10-04 | [A10 protocol and result](a10-protocol-and-result-20261004.md) | Prospective mixed-fidelity holdout |

## Artifact routing

- Lightweight, reviewable evidence:
  [diagnostics](../../diagnostics/README.md).
- Large particle states, maps, point clouds, and replays:
  tera_splat/outputs on the data volume.
- Machine-readable fresh Phase 0 ledger and evidence:
  `outputs/validity_experiment/newton/static_proxy_hierarchical_v3_20261017/`.
- Chrono source episodes and oracle-generation details:
  [tera_splat_sim documentation](../../../tera_splat_sim/docs/README.md).
- Cross-backend decision:
  [forward-model direction](../forward-model-direction-20261006.md).

## Maintenance rules

- Update [phase1.md](phase1.md) whenever the active Phase 1 contract, gate,
  conclusion, claim boundary, or next permitted work changes; append measured
  runtime evidence to [phase1-running.md](phase1-running.md) in the same change.
- Keep [handoff.md](handoff.md) as a concise compatibility entry point to those
  two authorities. Do not turn it or `running-analysis.md` into a competing
  operational ledger.
- Update [phase0.md](phase0.md) only when correcting or extending the frozen
  Phase 0 evidence; Phase 1 work must not rewrite that completed campaign.
- Add a separate dated report when the evidence needs tables, protocols, or
  detailed artifact routing.
- Do not rewrite dated reports to reflect later conclusions; link forward to
  `phase0.md` instead.
- Invalid mechanics runs have no model score and are never optimizer
  observations.

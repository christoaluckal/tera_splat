# Newton documentation index

Last updated: 2026-10-19

This directory contains the Newton-specific numerical contracts, experiment
reports, transfer evidence, and handoff material for the Chrono-to-MPM terrain
forward-model study.

## Read in this order

1. [Authoritative Phase 0](phase0.md) — live action ledger, ordered next work,
   current claims, chronological evidence, and artifact routing.
2. [Fresh hierarchical Phase 0 protocol](fresh-hierarchical-phase0-20261017.md)
   — frozen fresh-only evidence boundary, variation characterization, and
   geometric-utility hierarchy.
3. [Running analysis through 2026-10-19](running-analysis.md) — detailed
   pre-consolidation decision provenance; new entries belong in `phase0.md`.
4. [Static 35 mm proxy qualification](static-proxy-qualification-20261009.md)
   — original strict Phase 0 sentinel result and expansion stop gate.
5. [Bounded coarse-prior admission](coarse-prior-admission-20261016.md) —
   strict/coarse status split, frozen v2 limits, and pilot restart.
6. [Consolidated experiment report](experiment-consolidated-20261008.md) —
   canonical interpretation of preparation, contact, calibration, transfer,
   and stop/go results.
7. [Fixed-domain contract](fixed-domain.md) — qualified historical numerical and mechanics
   configuration.
8. [Hybrid model design](../hybrid-chrono-mpm-residual-gaussian-planning-20261008.md)
   — current destination for the Newton physics prior.

`phase0.md` is the only operational source for current completion counts,
sequencing, and next work. All other files are frozen protocols, compatibility
pointers, or dated provenance and must not silently replace it.

## Canonical reports

| Date | Document | Purpose |
| --- | --- | --- |
| live | [Authoritative Phase 0](phase0.md) | Current ledger, chronology, next work, and claims |
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

- Update [phase0.md](phase0.md) whenever the active contract, ledger,
  conclusion, claim boundary, or next permitted work changes.
- Append new dated evidence to `phase0.md`; do not add live state to
  `handoff.md` or `running-analysis.md`.
- Add a separate dated report when the evidence needs tables, protocols, or
  detailed artifact routing.
- Do not rewrite dated reports to reflect later conclusions; link forward to
  `phase0.md` instead.
- Invalid mechanics runs have no model score and are never optimizer
  observations.

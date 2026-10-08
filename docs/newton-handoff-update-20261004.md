# Newton handoff update — 2026-10-04

The original [Newton handoff](newton-handoff.md) is a correct record through
2026-09-28 but predates A2-A9. It must be read with the following current
documents:

1. [Forward-model current state](forward-model-current-state-20261004.md)
2. [Chrono-to-Newton historical evidence](historical-forward-model-evidence-20261004.md)

The ledger is authoritative for frozen parameters, exact action timings,
mechanics-validity boundaries, scalar metrics, characteristic analysis, source
artifacts, canonical scripts, and the resumption protocol. Do not use the
original handoff's “next experiment” section without applying the later gates
and A2-A9 evidence.

A10 is now complete: the canonical y=+25 mm interior spatial holdout is
mechanics-valid for both frozen materials. The incumbent improves scalar map
terms but remains mixed-fidelity in peak and volume. See the updated current
state and historical evidence ledger for exact values and the A10 analysis
artifact.

## Stop/go update — 2026-10-08

The bounded A10 Newton stop/go set is complete. Two additional prior-A0
candidates were run under the frozen `0.25 ms`, `8/16` contract. Both passed
all mechanics gates but were worse than the incumbent in held-out
multi-characteristic score: C2 objective `9.097 mm`, loaded/residual scores
`3.226/13.303`; C7 objective `10.375 mm`, scores `3.956/15.342`. The incumbent
is `8.146 mm`, `3.154/11.997`; the unchanged control is `12.244 mm`,
`4.900/18.292`.

This supports stopping broad parameter-only Newton search for the current
model form, while retaining the bounded claim that numerical or objective-level
improvement is not mathematically excluded. Genesis remains numerically
unresolved and is not declared exhausted. See
[forward-model direction](forward-model-direction-20261006.md) and
`diagnostics/forward_model_stopgo_20261006_A10/`.

The complete Newton experiment inventory and consolidated interpretation is now
in [newton experiment report](newton-experiment-consolidated-20261008.md).
Use it as the index for numerical diagnostics, calibration, action holdouts,
and stop/go evidence; retain the dated reports as provenance.

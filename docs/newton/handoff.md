# Newton handoff

Status: compatibility entry point for the active Phase 1 successor

The live handoff, current gate, claim boundary, and guarded continuation order
are the [Fresh-session handoff in `phase1.md`](phase1.md#fresh-session-handoff).
The append-only runtime evidence is in
[`phase1-running.md`](phase1-running.md), with the latest dated entry recording
the current successor smoke process and downstream locks.

As of the 2026-11-02 handoff, the frozen 8/4 successor engineering smoke is
still running under its original two-worker supervisor. No aggregate smoke
summary exists, so bulk generation, training, evaluation-plan freeze, and all
protected targets remain locked. Do not launch a duplicate supervisor or treat
partial Chrono completion as smoke admission. Recheck only on explicit user
request, then follow the guard in `phase1.md`.

[Phase 0](phase0.md) remains the immutable authority for the completed Phase 0
campaign and its artifacts. This filename is retained so older reports and
external notes still reach the active handoff without creating a competing
operational ledger.

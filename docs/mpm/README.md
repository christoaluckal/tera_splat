# Alternate MPM backend documentation

Last updated: 2026-11-10

This directory is the live documentation home for the alternate Material Point
Method backend study on branch `mpm_test`.

## Read in this order

1. [Goal and execution contract](goal.md) — authoritative objective, scope,
   architecture, qualification ladder, model comparison, protected evaluation,
   claim boundary, and required deliverables.
2. [Running experiment record](running.md) — append-only environment checks,
   implementation checkpoints, commands, artifact identities, measurements,
   failures, decisions, and next permitted gate.
3. [Original pipeline handoff](../mpm-backend-pipeline-handoff.md) — design
   source and historical handoff that preceded this live study.
4. [Completed Newton Phase 1](../newton/phase1.md) — inherited leakage,
   model-capacity, evaluation, and claim lessons. It is not an alternate-backend
   execution authority.

## Authority and maintenance

- `goal.md` is the sole live authority for what the MPM study is trying to
  establish and which gates permit progress.
- `running.md` is the only live location for detailed alternate-backend
  experiment chronology. Do not put live counts, trial results, or retry
  decisions in this index or in the historical handoff.
- Update `goal.md` only when the scope, contract, ordering, gate, deliverable,
  or claim boundary changes.
- Append to `running.md` whenever an environment, implementation, numerical,
  preparation, contact, export, smoke, training, or evaluation result changes
  the next permitted action.
- Give every backend, configuration, attempt, and artifact an explicit
  identity. Warp, Taichi, Genesis, and Newton evidence must remain separately
  named.

## Current status

The study is in pre-implementation setup. The `mpm_test` Git branch and Conda
environment exist. The environment currently contains Python 3.12.13 but no
NumPy, PyTorch, Warp, or Taichi installation. No Warp or Taichi terrain backend
has passed environment, numerical, preparation, contact, convergence, or state
export qualification.


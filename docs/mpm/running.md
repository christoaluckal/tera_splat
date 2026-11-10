# Alternate MPM backend running experiment record

Created: 2026-11-10

Last updated: 2026-11-10

Status: active append-only evidence record; pre-implementation setup

The authoritative goal, scope, gate order, success criteria, and claim boundary
are in [goal.md](goal.md). This file records dated environment checks,
implementation work, exact commands, artifact identities, measurements,
failures, decisions, and the next permitted gate. It must not redefine the
goal or maintain competing thresholds.

## Current snapshot

| Item | State | Evidence or next action |
| --- | --- | --- |
| Git branch | ready | `mpm_test`; clean at initial inspection |
| Conda environment | created but unpopulated | `/data/christoa/conda/envs/mpm_test`; Python 3.12.13 |
| accelerator | inventoried | NVIDIA GeForce RTX 5090, 32,607 MiB; driver 580.196.07 |
| canonical adapter | not implemented | define schemas and target-free plan first |
| Warp backend | not installed or qualified | pin environment, then device/interoperability smoke |
| Taichi backend | not installed or qualified | defer implementation until canonical fixture is stable |
| units/frame fixture | not implemented | Gate 2 after environment identity |
| volumetric-bed preparation | not implemented | Gate 3 after frame fixture |
| no-action stability | not run | blocked by preparation implementation |
| guided cylinder contact | not implemented | blocked by accepted no-action preparation |
| convergence matrix | not run | blocked by accepted contact path |
| state export | not qualified | blocked by admitted response |
| two-episode fixture | not run | blocked by Gates 1--7 |
| 8/4 smoke | not run | blocked by integration fixture |
| 48/16 generation | prohibited | blocked by smoke admission |
| training | prohibited | blocked by dataset admission |
| protected targets | locked/not selected | no protected access permitted |

## Experiment record template

Append new entries in chronological order using this structure:

```text
### YYYY-MM-DD — concise result title

Question:
- what gate or uncertainty was tested?

Frozen identity:
- study ID, backend, source revision, environment hash, config hash, device,
  worker count, seed, and exact command;

Result:
- complete measurements, artifact paths/hashes, pass/fail values, and failures;

Decision:
- what is admitted, rejected, preserved, or superseded?

Next permitted gate:
- the only work authorized by the result;
```

Do not overwrite an entry when later evidence changes the interpretation.
Append a new entry and link back to the earlier artifact.

## Chronology

### 2026-11-10 — alternate MPM study initialized

Question:

- establish a dedicated branch, environment, documentation authority, and
  backend ordering for a PhysGaussian-inspired multi-backend MPM study;
- determine whether the existing environment already contains a runnable Warp
  or Taichi stack.

Observed identity:

- repository: `tera_splat`;
- branch: `mpm_test`;
- initial `git status --short --branch`: `## mpm_test`, with no listed changes;
- Conda environment: `/data/christoa/conda/envs/mpm_test`;
- Python: 3.12.13, Anaconda build, GCC 14.3.0;
- GPU: NVIDIA GeForce RTX 5090;
- reported GPU memory: 32,607 MiB;
- NVIDIA driver: 580.196.07.

Environment probe:

```text
module/distribution    state
numpy                  missing
torch                  missing
warp / warp-lang       missing
taichi                 missing
```

Repository evidence:

- PhysGaussian-derived code already exists in historical ground-plane,
  particle, Genesis, configuration, and Gaussian-transfer paths;
- `scripts/run_ground_plane_solver.py` expects a sibling PhysGaussian checkout
  and contains compatibility shims for a newer Warp API;
- historical documentation already classifies PhysGaussian warp-mpm as a
  useful source reference but not a qualified robot-terrain backend;
- no canonical Warp or Taichi terrain adapter currently exists.

Decision:

- use one backend-neutral adapter contract;
- implement and qualify a modern Warp PhysGaussian-derived backend first;
- add Taichi as a second independent adapter only after the canonical
  two-episode fixture is stable;
- use a fixed backend-native material for initial qualification;
- keep Gaussian deformation downstream of admitted metric MPM exports;
- do not launch simulation, create bulk targets, or train a residual during
  environment setup.

Next permitted gate:

- freeze the environment strategy and dependency versions;
- implement Gate 1 identity/schema tests and a Warp device/interoperability
  smoke before writing terrain dynamics.

## Failure and retry ledger

No alternate-backend runtime attempt exists yet.

Every future failure must record:

- study and attempt ID;
- backend and exact execution identity;
- failed gate and raw error;
- whether any output is complete enough for diagnosis;
- preserved artifact path and hashes;
- prospective retry authorization and the exact changed fields.

## Protected-data ledger

- Previously revealed Newton Phase 1 protected targets are diagnosis-only.
- No fresh alternate-backend protected design has been frozen.
- No fresh alternate-backend protected target has been generated or opened.
- Protected generation remains prohibited until a backend passes full
  train/validation admission and validation-only selection is frozen.


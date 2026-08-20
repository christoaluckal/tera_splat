# Experiment Problems And Corrective Plan

Last reviewed: 2026-08-18

This document records active experimental blockers discovered while calibrating
the Chrono SCM A0 target with Genesis. It is linked from
[`current-state.md`](current-state.md), which remains the live handoff and
source of output provenance.

## Stage 1: Prepared-Bed Feasibility Fails Before Contact Calibration

The BayesOpt campaign has two gates:

1. **Stage 1 — feasibility:** construct a gravity-settled Genesis bed that
   reaches the frozen H0 geometry and low-speed acceptance gates.
2. **Stage 2 — response fit:** run the gravity-cylinder bridge and compare the
   loaded/residual Genesis DEM deformation against Chrono.

The current blocker is Stage 1. It is not evidence that a material candidate
has a poor contact response; it means its initial state is not comparable to
the Chrono H0 target and must not enter the objective model.

### Measured Evidence

Across the failed prepared beds recorded under the pilot and proper-study
output roots:

```text
pre-settle termination: equilibrium
all-bed p99 speed:      below the 0.5 mm/s threshold
failure gate:           frozen H0 surface match
surface RMSE:           typically 16--45 mm
surface maximum error:  typically 100--105 mm
required RMSE / max:    <= 5 mm / <= 10 mm
```

The maximum error is approximately the 100 mm bed depth. This points to a
surface-support or surface-extraction discontinuity, not ordinary gravity
compaction. Increasing the settle duration, adding damping, or loosening the
H0 gate would conceal rather than solve the discrepancy.

The broad particle proposal also established this empirical feasibility fact:

```text
15 mm spacing, 0.85 size ratio: rejected
25 mm spacing, 0.85 size ratio: rejected
```

The initial attempt to constrain the optimizer to apparently accepted particle
pairs was still insufficient: feasibility also depends on `E` and `phi`.
The 35-new-attempt continuation stopped with only two new valid observations.

## Likely Mechanisms

### 1. Particle Mass/Volume Is Coupled To Discretization

Particle spacing changes particles per unit volume. Genesis particle size
sets represented particle volume. Holding the material density fixed while
varying both changes the represented bulk density approximately as:

```text
rho_bulk = rho_material * (particle_size / particle_spacing)^3
```

For example, a `0.85` size ratio represents about `0.85^3 = 0.614` of the
bulk density of a ratio-1 lattice when the configured material density is
unchanged. That materially changes gravity settlement before the cylinder is
released, so it is not a pure particle-resolution experiment.

### 2. Surface Support Or Extraction Is Losing H0 Cells

The near-bed-depth maximum error suggests one or more target cells are mapped
to a deep particle, an unsupported nearest-fill value, or the wrong particle
layer. The current highest-particle projection must be diagnosed at the cells
that set the maximum error before interpreting any contact result.

### 3. Material Calibration Currently Rebuilds The Initial State

Rebuilding and gravity-settling a bed for each `E`/`phi` candidate lets the
candidate change H0 before contact. That confounds initial-state construction
with the material-response objective. A valid contact fit must compare from a
frozen, H0-matched initial state.

## Corrective Plan

### A. Enforce Mass/Volume Normalization First

For each particle configuration, compute the actual represented MPM volume
from the initialized particle count and particle volume. Set the material
density so the desired physical bulk density and total bed mass are unchanged
across spacing/size choices. Record:

- particle count;
- spacing and particle size;
- represented volume;
- target bulk density;
- resolved material density and total mass.

Do not compare different particle configurations until this check passes.

### B. Instrument The H0 Failure Cells

For every preparation attempt, save or report:

- pre- and post-settle surface support masks;
- coordinates and values of the worst H0-error cells;
- designated initial surface-cap particle IDs;
- highest-particle and designated-surface reconstructions at those cells;
- coverage, nearest-fill distance, and selected-particle depth.

Use this to determine whether the approximately 100 mm error comes from a
hole, a projection rule, or genuine surface collapse. Do not relax the H0
tolerances to pass this diagnostic.

### C. Split Feasibility From Contact Optimization

Build one accepted complete MPM state for each particle configuration using a
frozen preparation protocol. Persist position, velocity, `C`, `F`, `Jp`,
active mask, metric-bed metadata, and the accepted H0 reconstruction.

Then run `E`/`phi` contact candidates from that state. If the candidate needs
a different geostatic stress field, construct that stress consistently without
moving the accepted H0 geometry and require a short unconstrained stability
check before the cylinder release.

### D. Establish A Feasible Particle Family Before BayesOpt

Run a fixed-reference-material feasibility study over spacing/size pairs. A
pair becomes a discrete BayesOpt category only after it has an accepted,
volume-normalized prepared state. This is separate from minimizing the Chrono
DEM loss.

### E. Consider A Constrained Preparation Only If Needed

If gravity equilibration cannot retain H0, a temporary surface-height
constraint may be used during geostatic preparation. Remove it before loading
and require the resulting unconstrained state to pass the same H0 and speed
gates. Record the constraint exactly; never apply an undocumented vertical
offset after settlement.

## Current Decision

Do not spend another response-optimization budget until A and B are complete.
The current best response candidate is an incumbent only, not a calibrated
solution, because the feasible initial-state region has not yet been mapped.

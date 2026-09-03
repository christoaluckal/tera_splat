# Calibration Problems, Evidence, and Corrective Actions

Last reviewed: 2026-09-03

This document separates resolved setup failures from the current response
calibration problem. The historical 2026-08-18 diagnosis is archived in
[experiment-problems-through-2026-08-18.md](archive/experiment-problems-through-2026-08-18.md).

## Current problem

The active Chrono oracle and Genesis n128 initialization both pass their gates.
The remaining mismatch is post-removal response: Genesis retains too little
plastic deformation.

For the confirmed `20.433 kPa / 14.727 deg / 0.101895` incumbent at n128:

- loaded RMSE: `1.864 mm`;
- residual-footprint RMSE: `13.678 mm`;
- residual-footprint signed mean: `+12.941 mm`;
- objective: `8.704 mm`.

Positive signed residual error means Genesis is higher than Chrono in the
footprint after removal.

The retained-raw replay `ykep3esa` makes the spatial error inspectable without
changing this result. Its generated bundle contains separate and combined
loaded/residual isometric surface point clouds, signed 2D DEM-error maps,
compressed comparison arrays, aligned Chrono-grid PCDs, full 307,461-particle
Genesis PCDs, and 78 sampled rollout PLYs. The residual map shows a coherent
positive footprint error rather than an I/O-frame or support-mask offset.

`ykep3esa` scored `8.705 mm`, but it is not new confirmation evidence. Its p99
map disagreement stayed below `0.011 mm`, while four residual cells exceeded
the 1 mm discrete-projection threshold versus the frozen allowance of three.
The gate remains unchanged and `r2at0vvb` remains authoritative.

The non-learned diagnosis is now complete. Sixteen unique valid n128
candidates produce a four-point Pareto front: reducing residual-footprint
RMSE from `13.682` to `13.533 mm` costs loaded RMSE (`1.864 -> 1.997 mm`).
The incumbent recovery-error RMSE is `9.213 mm` in the footprint, and nonzero
Genesis `Jp` particle count grows from 1,243 initially to 8,481 after removal.
This is coherent recovery/plastic-state evidence, not a frame or mask error.

However, the controlled numerical matrix prevents a model-form-only verdict.
Halving timestep changes residual-footprint RMSE by `+2.325 mm` at n64 and
`+1.525 mm` at n128. Fixed-timestep resolution effects are only `+0.233` and
`-0.566 mm`, respectively. Numerical convergence is therefore not
demonstrated.

## Resolved problems

| Problem | Observation | Action | Result |
| --- | --- | --- | --- |
| incomplete legacy target | `A0_cal_full10mm` lacked a qualified residual-time/action contract | built guided, timed 5 mm oracle | active oracle accepted at `3.595 s` plus `0.25 s` residual |
| false grid-lock diagnosis | centroid included invalid SCM boundary ring | applied `valid_heightmap_mask.npy` | deformation follows cylinder; only millimetre-scale phase sensitivity remains |
| candidate stress mismatch | restoring `F` prepared at another `E` changed implied stress | reconstruct candidate-specific geostatic `F` | candidates start from frozen geometry with their own material state |
| rebound uncertainty | low speed alone did not prove surface stability | added separate 0.25 s no-action surface test | promoted candidates drift only `0.008--0.011 mm` RMSE |
| bootstrap geometry bug | first fresh-study candidate used hard-coded 20 mm spacing | derive particle geometry from prepared-bed manifest | corrected study completed 12/12 valid |
| n128 initialization failure | 10 mm particles left 1.5625 spacings per n128 cell | use 5 mm particles and restore ratio 3.125 | 307,461-particle bed accepts with H0 RMSE `0.070 mm` |
| n128 candidate timeout | old 2 s cap ended just before equilibrium | increase cap to 4 s, retain 0.5 mm/s gate | candidates accept at `2.077--2.180 s` |
| unresolved incumbent-region trend | previous best sat near the low-`nu` corner | ran compact n128 study `9on0s14j` and exact replay `85cw5i1i` | objective improved by `0.502 mm`; new best lies on lower `phi` boundary |
| lower-`phi` boundary trend | compact-study winner sat at `phi=16.5 deg` | ran boundary study `yab3idti` and exact replay `r2at0vvb` | objective improved another `0.420 mm`; winner at `phi=14.727 deg` passed repeatability |

No H0, no-action, RMSE, or speed gate was loosened.

## Previous best-known candidate

The coarse 20 kPa candidate was selected from these observations:

1. it matched Chrono sinkage at n64: `34.051 mm` versus `34.270 mm`;
2. it scored `8.548 mm`, better than the fresh unseeded study's
   `9.232 mm`;
3. anchor-inclusive study `vrxqwoe2` produced nearby low-`nu` results at
   `8.605` and `8.643 mm`, corroborating the same basin.

Actions taken before trusting it at high resolution:

1. fixed particle geometry in the proposal code;
2. constructed an accepted ratio-matched n128 bed;
3. retained physical geostatic scale 1.0;
4. extended only candidate preparation duration;
5. replayed the incumbent and both corroborating candidates with identical
   fixed loading and residual times.

Results:

| Candidate | n64 objective | n128 objective | n128 initialization |
| --- | ---: | ---: | --- |
| 20.000 kPa / 18.149 deg / 0.100004 | **`8.548 mm`** | **`9.626 mm`** | H0 `0.747 mm`; drift `0.011 mm` |
| 18.110 kPa / 18.984 deg / 0.103989 | `8.605 mm` | `9.833 mm` | H0 `0.793 mm`; drift `0.008 mm` |
| 20.186 kPa / 18.485 deg / 0.100693 | `8.643 mm` | `10.041 mm` | H0 `0.724 mm`; drift `0.011 mm` |

The ranking survives resolution promotion. Initialization quality is much
better at n128, while residual response is worse, so the remaining error cannot
be attributed to a bad starting bed.

## Current diagnosis

Lower friction improved both loaded and residual metrics, but the confirmed
residual signed error remains `+12.941 mm`. The winner is inside the extended
friction interval rather than at its lower boundary, so blind boundary
expansion is no longer justified.

The aligned maps, radial profiles, center cross-sections, recovery change,
Pareto decomposition, and `F`/`Jp` summaries all support a coherent recovery
mismatch. The 2x2 matrix also shows material timestep sensitivity, however, so
the constitutive limitation remains strongly suggested rather than isolated.
The requested third n128 level is complete as a failed-gate diagnostic.
End-to-end `0.125 ms` preparations timed out at 2 and 4 s with final p99 speeds
of `0.590` and `0.621 mm/s`; H0 remained inside its surface bounds. Reusing the
accepted `0.25 ms` state and refining downstream runtime to `0.125 ms` also
failed candidate relaxation before contact. No third score exists.

The same-state follow-up now records 401 samples over 4 s at each timestep.
At `0.5/0.25/0.125 ms`, final p50/p95/p99 speeds are respectively
`0.100/0.243/0.450`, `0.170/0.360/0.516`, and
`0.291/0.764/0.986 mm/s`. The fastest 1% changes from 98.4% wall and 76.7%
ground, to 97.7% wall and 49.9% surface, to 99.87% surface. Persistent movers
shift from `-3.135 mm` median vertical displacement to `+2.555 mm`.
This is timestep-dependent boundary/free-surface drift, not uniform bulk
compaction. Because fine-step p95 also exceeds the gate, it is not only a
one-percent wall artifact. Fix or ablate the numerical preparation mechanism
before another material sweep; do not add a discrepancy network.

## Decision rule

- If a valid n128 candidate lowers residual-footprint error without materially
  worsening loaded RMSE, promote it.
- If a third-level/fixed-state check demonstrates score convergence while the
  Pareto and recovery mismatch persist, record a limitation of the current
  Genesis Sand constitutive response.
- If timestep movement remains material, diagnose integrator/contact/state
  preparation sensitivity before changing material parameters.
- Do not solve the mismatch by changing Chrono, adding a classifier, loosening
  gates, fitting a stress multiplier, or mixing n64 and n128 objectives in one
  unmodelled-fidelity surrogate.

## Alternate Newton forward model

Newton is viable enough to prototype on a separate branch because its implicit
MPM path supports granular/elasto-plastic particles and rigid coupling. That is
an engineering option, not a resolution of the Genesis diagnosis and not a
drop-in solver swap. Newton is not installed or implemented in this baseline,
and no Newton result has been generated.

The Chrono oracle, action/timing, mask, surface projection, score, and
diagnostic schema can remain common. Genesis prepared states, `F`/`C`/`Jp`,
parameter meanings, observations, and calibration bounds cannot be transferred
without a new derivation and validation. The Newton branch must first qualify
its own static-container bed, timestep/solver-tolerance behavior, two-way
cylinder coupling, and moving-container removal before starting a fresh
calibration.

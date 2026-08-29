# Calibration Problems, Evidence, and Corrective Actions

Last reviewed: 2026-08-29

This document separates resolved setup failures from the current response
calibration problem. The historical 2026-08-18 diagnosis is archived in
[experiment-problems-through-2026-08-18.md](archive/experiment-problems-through-2026-08-18.md).

## Current problem

The active Chrono oracle and Genesis n128 initialization both pass their gates.
The remaining mismatch is post-removal response: Genesis retains too little
plastic deformation.

For the current 20 kPa incumbent at n128:

- loaded RMSE: `2.142 mm`;
- residual-footprint RMSE: `14.966 mm`;
- residual-footprint signed mean: `+14.308 mm`;
- objective: `9.626 mm`.

Positive signed residual error means Genesis is higher than Chrono in the
footprint after removal.

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

## Current hypothesis

Within the existing Genesis Sand model, a slightly more plastic response may
retain more deformation after removal. The next test should vary only the
existing `E`, `phi`, and `nu` values on the accepted n128 bed.

A compact evidence-based region is:

- `E = 18--26 kPa`;
- `phi = 16.5--18.5 deg`;
- `nu = 0.10--0.13`.

Lower friction may increase retained plastic deformation, while `E` must
preserve the loaded response. This is a parameter-search hypothesis, not a
request for a new parameter or changed physics.

## Decision rule

- If a valid n128 candidate lowers residual-footprint error without materially
  worsening loaded RMSE, promote it.
- If the current parameters trade loaded fit against residual retention with no
  joint improvement, record a limitation of the current Genesis Sand
  constitutive response.
- Do not solve the mismatch by changing Chrono, adding a classifier, loosening
  gates, fitting a stress multiplier, or mixing n64 and n128 objectives in one
  unmodelled-fidelity surrogate.

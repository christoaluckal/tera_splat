# A10 prospective interior spatial-validation protocol

Date: 2026-10-04  
Status: frozen before Chrono target generation

## Purpose

A10 is a prospective, sim-only interior spatial holdout for the established
Chrono-to-stock-Newton forward model.  It tests the frozen material point at
an action between the accepted A4 (`y=+5 mm`) and A9 (`y=+50 mm`) positions;
it is not a new calibration datum and will not be used to retune Newton or the
Chrono-only characteristic surrogate.

## Frozen action and numerical contract

Chrono will generate a vertically guided SCM episode for a right circular
cylinder with mass `1.625 kg`, radius `73.025 mm`, height `50.8 mm`, and
center `(x, y) = (0, +25) mm`.  It uses the canonical oracle configuration:
`1 ms` SCM timestep, `5 mm` map spacing, a `6 mm/s` loading-speed threshold,
a `0.10 s` hold, at most `5 s` loading, and a fixed `0.25 s` recovery.

Newton will use the episode-provided loaded time and recovery duration
exactly, the unchanged qualified `7.8125 mm` PIC/PIC, P0/S2/Q1, `0.25 ms`,
8-proxy-iteration, 16-rigid-substep contract, and fresh full-bed preparation
plus a separate continuous response for each material.  The only two material
points are the frozen A0 incumbent (`E=70.46 kPa`, `nu=0.237231507`,
`mu=0.305497980`) and the unchanged 100 kPa control (`nu=0.2`, `mu=0.68`).

## Gates and predefined interpretation

Each Newton response must have matching episode timing, finite maps on the
full 14,161-cell support, matching initial terrain/mask, prismatic-guide
compliance, and exactly zero analytic particle-center penetration.  A failed
response has no score and is not an optimizer observation.

For each mechanics-valid response, report the existing scalar objective,
loaded RMSE, residual-footprint RMSE, peak/mean/footprint depression,
depression volume, and depression centroid against Chrono.  The incumbent
will be called *comparatively characteristic-better on A10* only if both
responses are valid and it is no worse than the unchanged control in loaded
RMSE, residual-footprint RMSE, absolute peak error, absolute volume error, and
centroid-vector error.  This comparative label is an A10 result only; it is
not a generalization claim.  Any failed gate or any one worse term is reported
as a boundary or mixed-fidelity result rather than hidden by a scalar score.

## Planned canonical artifacts

* Chrono episode:
  `tera_splat_sim/validity_experiment/chrono_episodes/A10_oracle_mass1p625kg_lateral_yplus25mm_gate6mm_v1/`
* Newton outputs:
  `tera_splat/outputs/validity_experiment/newton_holdout/`
* Analysis:
  `tera_splat/diagnostics/forward_model_transfer_20261002/a10_newton/`


## Completion record

A10-v2 is complete. It uses explicit 1 ms, 5 mm, 0.6 m Chrono settings and
accepted at 2.289 s. Both frozen Newton responses passed all hard gates. The
incumbent wins scalar terms against the unchanged control but is mixed-fidelity
because it overpredicts peak and underpredicts volume; see
`diagnostics/forward_model_transfer_20261002/a10_newton/`.

A10-v1 is retained only as a rejected provenance artifact because it used
noncanonical runner defaults; it was never given a Newton score.

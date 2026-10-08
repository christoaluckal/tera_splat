# Forward-model current state — 2026-10-04

This concise operational note is the companion to the
[historical evidence ledger](historical-forward-model-evidence-20261004.md).

The active objective is a **sim-only** forward model: Chrono generates GT
terrain maps and stock Newton predicts them. The frozen Newton contract is
7.8125 mm, PIC/PIC, P0/S2/Q1, 0.25 ms, eight proxy iterations, and sixteen
rigid substeps. The A0-fitted incumbent is `E=70.46 kPa`, `nu=0.237231507`,
`mu=0.305497980`; the unchanged control is `E=100 kPa`, `nu=0.2`, `mu=0.68`.

Current conclusion: Newton is a mechanically qualified but bounded predictor.
The frozen incumbent is invalid under the strict zero-penetration gate at 1.75,
2.0, and 3.0 kg and at radii 55 and 65 mm. It is valid at A4, A5, A6, and A9.
A9 shows that validity and centroid accuracy do not ensure peak or volume
fidelity: loaded RMSE is 2.543 mm, but peak is +14.730 mm wrong and volume is
-178.812 cm3 wrong.

Every future valid action report must include:

1. accepted Chrono loaded time and residual duration;
2. map objective, loaded RMSE, and residual-footprint RMSE;
3. I/O, guide, and strict mechanics-gate status;
4. peak/mean/footprint depression, volume, and centroid versus Chrono.

The linear Chrono-only characteristic surrogate remains diagnostic only. A0-A9
leave-one-out peak and volume errors are 30.688 mm and 565.574 cm3; it must not
be used as a terrain predictor. The original [Newton handoff](newton-handoff.md)
predates A2-A9 and is background, not the current complete record.

## A10 update

A10 (1.625 kg, canonical radius, y=+25 mm) is a prospective interior spatial
holdout. Both materials are mechanics-valid; the incumbent wins the scalar
objective (8.146 versus 12.244 mm) yet has +10.624 mm loaded-peak and -171.121
cm3 loaded-volume error. This independently retains the A9 conclusion:
mechanics validity and scalar improvement do not establish characteristic
fidelity.

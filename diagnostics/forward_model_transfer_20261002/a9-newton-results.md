# A9 Chrono→Newton spatial validation

A9 is the accepted canonical-radius 1.625 kg action at y=+50 mm. Chrono
accepted at 3.341 s with 34.547 mm body sinkage. The frozen Newton incumbent
is mechanics-qualified with exact 3.341 s loaded / 0.25 s residual timing,
zero sampled center penetration, and guide compliance.

Prediction metrics:

- objective: 8.490 mm
- loaded map RMSE: 2.543 mm
- residual-footprint RMSE: 11.894 mm
- peak depression error: +14.730 mm
- depression-volume error: −178.812 cm³
- loaded centroid errors: +0.046 mm x, −0.258 mm y

The centroid is accurate while peak/volume fidelity is poor. This is direct
evidence that the fixed Newton rollout can remain mechanically valid while
mis-predicting important deformation characteristics in a nonlinear spatial
regime.

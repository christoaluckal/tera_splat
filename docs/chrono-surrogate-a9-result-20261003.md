# A9 spatial GT result

A9 is a canonical-radius 1.625 kg Chrono episode at y=+50 mm. It is accepted
at 3.341 s with 34.547 mm loaded sinkage, identical support/initial terrain,
and finite maps.

Adding A9 to the Chrono characteristic surrogate improves centroid prediction
but reveals strong nonlinear spatial behavior. A0–A9 leave-one-out errors are
1.279 mm x-centroid and 0.088 mm y-centroid, but 30.688 mm peak-depression
and 565.574 cm³ volume RMSE. The linear model is therefore not a reliable
terrain-deformation predictor; more local GT coverage or a nonlinear spatial
model is required.

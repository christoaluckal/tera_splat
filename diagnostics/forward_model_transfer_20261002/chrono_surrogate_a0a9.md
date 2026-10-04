# A0–A9 Chrono surrogate result

A9 adds a canonical-radius 1.625 kg action at y=+50 mm. Chrono accepts it at
3.341 s with 34.547 mm loaded sinkage. Refitting the transparent linear ridge
surrogate on ten accepted episodes gives:

| characteristic | LOO RMSE |
|---|---:|
| mean depression | 1.686 mm |
| peak depression | 30.688 mm |
| depression volume | 565.574 cm³ |
| x centroid | 1.279 mm |
| y centroid | 0.088 mm |

The centroid terms improve sharply, but peak/volume errors become much worse;
the A9 leave-one-out prediction underestimates the nonlinear y-offset response
by 91.419 mm in peak depression and 1,686.4 cm³ in volume. The next model
should use a nonlinear spatial representation (or denser Chrono sampling),
not a higher-order polynomial fitted to this tiny set.

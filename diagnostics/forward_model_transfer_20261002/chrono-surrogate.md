# Chrono characteristic surrogate baseline

`fit_chrono_characteristic_surrogate_v2.py` fits a transparent standardized
ridge model from accepted A2–A8 Chrono actions `(mass, radius, center_x,
center_y)` to loaded/residual deformation characteristics. It uses leave-one-
out predictions rather than training error.

On the seven accepted episodes, loaded-characteristic LOO errors were:

| characteristic | LOO RMSE |
|---|---:|
| mean depression | 0.387 mm |
| peak depression | 7.292 mm |
| depression volume | 130.143 cm³ |
| x centroid | 26.598 mm |
| y centroid | 2.661 mm |

This is a deliberately honest baseline. It shows that the episode interface
and characteristic targets are usable, but seven actions do not support a
reliable spatial/geometry predictor. More Chrono GT coverage (or real-sand
measurements) is required before using a learned characteristic surrogate for
planning.

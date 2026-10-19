# A9 spatial validation result

The y=+50 mm Chrono GT episode is accepted at 3.341 s. The frozen Newton
incumbent passes all hard mechanics/timing gates, but its deformation
characteristics are mixed:

| quantity | error |
|---|---:|
| loaded map RMSE | 2.543 mm |
| residual-footprint RMSE | 11.894 mm |
| peak depression | +14.730 mm |
| depression volume | −178.812 cm³ |
| loaded centroid x/y | +0.046 / −0.258 mm |

This confirms the forward model can predict spatial centroid location while
still missing peak and volume characteristics. A scalar map objective and
mechanics validity are therefore insufficient acceptance criteria for a
terrain-deformation predictor.

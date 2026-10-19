# Contact-domain radius boundary

Two accepted Chrono geometry variations were tested under the fixed Newton
domain. The frozen A0 incumbent failed the strict analytic center-penetration
gate at both smaller radii:

| radius | Newton incumbent result |
|---:|---|
| 55 mm | invalid; 4 centers, 1.406 µm maximum penetration |
| 65 mm | invalid; 6 centers, 1.283 µm maximum penetration |
| 73.025 mm | valid in A4–A6 |

Guide compliance passed at the two invalid radii, so this is a contact-domain
boundary rather than a guide failure. The smaller-radius Chrono oracles are
valid and remain useful GT episodes; the rejected incumbent responses must not
be scored or used as optimizer observations.

The current forward-model claim should therefore state the geometry domain
explicitly: canonical-radius guided cylinders are qualified, while the frozen
material/contact configuration is not mechanically admissible across all
smaller footprints at the 7.8125 mm voxel resolution.

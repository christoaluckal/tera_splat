# Diagnostics

This tracked directory stores lightweight analysis products that should remain
referenceable with the source tree:

- JSON summaries and manifests;
- CSV tables and profiles;
- PNG plots and comparison figures;
- short Markdown interpretation notes.

Large generated artifacts do not belong here. Prepared beds, solver states,
MPM checkpoints, PLY/PCD sequences, videos, and large-scale evaluation runs
remain under the repository-root `outputs/` symlink.

Each diagnostic bundle should use a descriptive, dated subdirectory and retain
absolute or repository-relative provenance paths to its source trials. This
directory is intentionally not ignored by Git.

Bundles are backend-specific. Newton diagnostics use an explicitly named
namespace and are not continuations of Genesis state or calibration evidence.

Current bundles:

- `newton_contact_activation_20260910/`: version-locked full-volume S2
  contact-activation diagnosis.  The `-0.25`-voxel cylinder-only setting makes
  every mechanics row pass and the medium/fine pair pass; coarse/medium
  sinkage is `0.975 mm` against the unchanged `0.5 mm` gate, so calibration
  remains blocked;
- `newton_calibration_20260910/`: qualified 25 kPa preparation and rejected
  response screen; its better DEM-only score exploits the raised proxy's
  uncollided analytic slice, so material calibration is stopped;
- `newton_collider_support_20260908/`: collider-basis controls, qualified
  9.375 mm support-inset timestep matrix at 100 kPa, corrected shared A/B, and
  the explicit boundary that the inset is diagnostic rather than a promotable
  collision model;
- `backend_ab_20260906/`: matched-material Newton/Genesis A/B, current-best
  comparison, and rejected reverse parameter-transfer diagnostic;
- `newton_response_convergence_native_proxy_20260906/`: complete native
  Kamino/prismatic proxy-coupling matrix; all map and mechanics gates pass,
  while the fine sinkage difference is `0.586819 mm` and misses its frozen
  gate by `0.086819 mm`;
- `newton_response_convergence_20260906/`: complete clean-commit three-level
  full-response matrix; all cases pass mechanics individually, but response
  convergence fails because the explicit guide accumulates an approximately
  `g*T*dt` position drift;
- `newton_failure_resolution_20260906/`: controlled APIC/PIC and collider
  ablations, passed PIC preparation matrix, and the first mechanics-qualified
  uncalibrated full Newton response;
- `newton_convergence_coupling_20260906/`: three-timestep/two-tolerance
  preparation diagnosis, fixed-time cylinder coupling/removal result, and
  Newton restart-I/O qualification;
- `newton_preparation_20260903/`: accepted full-bed Newton preparation summary
  and links to retained large evidence;
- `model_form_2x2_20260901/`: Pareto, spatial/recovery, hidden-state, and
  two-resolution/two-timestep diagnosis;
- `n128_dt0p125_20260901/`: rejected third-level attempts and provenance;
- `pre_settle_timestep_20260903/`: controlled same-state speed,
  localization, and persistent-mover drift diagnosis at three timesteps.

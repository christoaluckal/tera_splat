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

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

All current bundles are Genesis-specific. A Newton branch should use an
explicitly named backend namespace and must not present Newton diagnostics as
continuations of Genesis state or calibration evidence.

Current bundles:

- `model_form_2x2_20260901/`: Pareto, spatial/recovery, hidden-state, and
  two-resolution/two-timestep diagnosis;
- `n128_dt0p125_20260901/`: rejected third-level attempts and provenance;
- `pre_settle_timestep_20260903/`: controlled same-state speed,
  localization, and persistent-mover drift diagnosis at three timesteps.

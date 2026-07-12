# Contact-Conditioned Terrain Gaussian Splatting Docs

This folder turns the prototype roadmap in `../README.md`, the PhysGaussian paper
(`../../2311.12198v3.pdf`), and the local `../../PhysGaussian/` implementation
into phase-by-phase planning docs.

The target prototype answers one controlled query:

```text
Given a Gaussian-splat terrain map, what would the sand terrain look like after
a localized shallow surface load is applied at location X?
```

The first milestone is not full robot-terrain contact. It is a stable,
inspectable pipeline for shallow terrain deformation with before/after renders,
deformed splats, and simple deformation metrics. The accepted physical contact
method is Genesis-style coupled rigid-MPM contact:
`Rigid(needs_coup=True)` entities in a scene with
`LegacyCouplerOptions(rigid_mpm=True)`.

## Reading Order

1. [PhysGaussian Notes](00_physgaussian_notes.md)
2. [Phase 1: Minimal Reconstruction](01_phase_minimal_reconstruction.md)
3. [Phase 2: Patch Extraction](02_phase_patch_extraction.md)
4. [Phase 3: Kinematic Baseline](03_phase_kinematic_baseline.md)
5. [Phase 4: Coupled Rigid MPM Contact](04_phase_mpm_pressure_patch.md)
6. [Phase 5: Subsurface Support](05_phase_subsurface_support.md)
7. [Phase 6: Gaussian Update](06_phase_gaussian_update.md)
8. [Phase 7: Material Conditioning](07_phase_material_conditioning.md)
9. [Phase 8: Query Interface](08_phase_query_interface.md)
10. [Phase 9: Evaluation](09_phase_evaluation.md)
11. [Phase 10: Robotics Extension](10_phase_robotics_extension.md)
12. [Current Solver Status](11_current_solver_status.md)

## Phase Dependencies

Phases 1-3 establish the renderable terrain scene, local query patch, and
analytic baseline. Phases 4-6 replace the analytic deformation with local MPM
and transfer the result back into renderable Gaussians. Phases 7-9 make the
prototype configurable and measurable. Phase 10 is intentionally deferred until
the coupled rigid cylinder prototype works.

## Global Success Criteria

The prototype is useful when one command or API call can:

- load a terrain Gaussian scene,
- select a local sand patch around a query point,
- apply a coupled rigid contact query,
- update Gaussian centers and eventually covariances,
- render before/after views,
- save deformation metrics and the run config.

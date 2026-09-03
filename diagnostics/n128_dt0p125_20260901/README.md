# n128 / 0.125 ms Diagnostic

Experiment run: 2026-09-01. Reviewed: 2026-09-03.

Status: no valid loaded/residual observation was produced. The 0.125 ms level
failed the unchanged pre-contact equilibrium gate under both tested paths.

## End-to-end prepared-bed attempts

Both attempts used 307,461 particles at 5 mm on n128, CPIC, geostatic scale
1.0, and the frozen `0.5 mm/s for 0.02 s` p99-speed gate.

| cap | result | final p99 speed | H0 RMSE | H0 maximum |
| ---: | --- | ---: | ---: | ---: |
| 2.0 s | rejected timeout | 0.590 mm/s | 0.769 mm | 1.161 mm |
| 4.0 s | rejected timeout | 0.621 mm/s | 1.833 mm | 2.450 mm |

The surface bounds passed in both attempts, but the speed criterion did not.
Increasing the cap from 2 to 4 s did not move p99 speed toward the gate, so an
8 s retry was not treated as a justified convergence experiment.

## Accepted-state reuse attempt

The accepted n128/0.25 ms prepared state was reused as the declared source,
then candidate-specific geostatic reconstruction and all downstream dynamics
were run at 0.125 ms through the run-one-only
`--diagnostic-runtime-dt 0.000125` path. Candidate relaxation again timed out
before cylinder contact under the unchanged 4 s / 0.5 mm/s gate. The trial is
invalid and has no loaded or residual score.

## Interpretation

The requested third n128 experiment is complete as a failed-gate diagnostic.
It does not supply a third convergence value. Together with the material score
movement from 0.5 to 0.25 ms, it shows that the current forward pipeline is not
timestep-converged and is not valid at 0.125 ms under the frozen initialization
contract. Do not add this trial to BayesOpt observations or weaken the gate.

That follow-up is complete in
[`../pre_settle_timestep_20260903/`](../pre_settle_timestep_20260903/). The
controlled 4 s traces show the fast population moving from wall/ground settling
at `0.5 ms` to free-surface uplift at `0.125 ms`; fine-step p95 is
`0.764 mm/s`, so the failure is not only a one-percent wall tail. Large states
and PLYs remain in `outputs/`; this folder contains only lightweight evidence.

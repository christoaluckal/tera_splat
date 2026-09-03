# n128 pre-settle timestep diagnosis

This bundle compares 4.0 s Genesis pre-settle traces at 0.5, 0.25, and
0.125 ms from the exact same accepted n128/0.25 ms particle state. Material,
particle geometry, geostatic reinitialization, containment, and the unchanged
0.5 mm/s p99-for-0.02 s gate are fixed. No learned network is used.

| timestep | final p50 / p95 / p99 | fastest 1% localization | persistent-mover median vertical displacement |
| ---: | ---: | --- | ---: |
| 0.5 ms | 0.100 / 0.243 / 0.450 mm/s | 98.4% wall; 76.7% ground | -3.135 mm |
| 0.25 ms | 0.170 / 0.360 / 0.516 mm/s | 97.7% wall; 49.9% surface | -1.968 mm |
| 0.125 ms | 0.291 / 0.764 / 0.986 mm/s | 99.87% surface; 58.8% wall | +2.555 mm |

The 0.5 and 0.25 ms runs entered an accepted 0.02 s p99 window at 2.055 and
1.53025 s, respectively; the full-duration traces show that this condition can
later reactivate. The 0.125 ms trace never crossed the gate. Its p95 also
remains above the gate value, so the fine-step rejection is not merely one
percent of wall particles.

The common initial state does not undergo uniform bulk compaction. Instead,
the dominant fast population changes qualitatively with timestep: wall/ground
settling at 0.5 ms, mixed wall/surface motion at 0.25 ms, and free-surface
uplift/rebound at 0.125 ms. This identifies timestep-dependent state-preparation
dynamics. It does not supply a third response score, demonstrate convergence,
or justify changing the frozen gate after observing the result.

Artifacts:

- `diagnosis.json`: machine-readable method, per-run summary, and conclusion;
- `pre_settle_summary.csv`: compact final, late-window, localization, and drift metrics;
- `pre_settle_trajectories.csv`: all 401 samples per timestep;
- `persistent_top_movers.csv`: source/final positions and recurrence counts;
- `speed_percentile_trajectories.png`: p50/p95/p99 histories;
- `speed_tail_localization.png`: wall, ground, surface, and action-region fractions;
- `persistent_top_mover_positions.png`: final plan positions and net vertical drift.

Large solver states remain under
`/data/christoa/Chrono/tera_splat/outputs/validity_experiment/numerical_diagnosis/pre_settle_trace_n128_dt*`.

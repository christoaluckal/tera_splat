# Bounded 35 mm coarse-prior admission — 2026-10-16

> Historical/quarantined evidence. As of 2026-10-17, none of the episodes,
> particle beds, preparations, or responses in this report may be reused for
> current qualification, training, validation, or test claims. The active
> protocol is the [fresh hierarchical Phase 0 protocol](fresh-hierarchical-phase0-20261017.md).

## Decision

The 35 mm Newton response remains **not strictly mechanics-qualified**. The
zero-center gate failed at every tested timestep and response convergence was
not demonstrated. Those results remain visible and must not be relabeled.

For the initial offline residual pilot, a separate bounded coarse-prior gate
now permits data generation when the state is finite, guided, fully supported,
clean at the loaded observation, and any trajectory-only center overlap is
both microscopic and sparse. This is an engineering data-admission decision,
not a mechanics or material-validity claim.

## Completed timestep evidence

The same centered 30.656 N action was evaluated without changing material,
contact, geometry, coupling, or acceptance instrumentation:

| Timestep | Maximum overlap | Maximum centers | Loaded sinkage | Strict result |
| --- | ---: | ---: | ---: | --- |
| 0.5 ms | 0.523 micrometers | 20 | 23.461 mm | fail |
| 0.25 ms | 3.759 micrometers | 8 | 19.066 mm | fail |
| 0.125 ms | 4.407 micrometers | 8 | 14.333 mm | fail |

The overlap is non-monotonic and sinkage changes by several millimeters, so
timestep convergence is not claimed. The 0.25 and 0.125 ms response maps
differ by 0.513 mm loaded RMSE and 0.488 mm residual RMSE. The selected
0.25 ms row costs half as much and has 0.835/0.683 mm loaded/residual Chrono
RMSE on this action. It is therefore frozen as a practical coarse prior;
timestep spread is retained as numerical uncertainty.

## Frozen bounded policy v2

`bounded_static_prior_v2_20261016` requires:

- accepted preparation and finite state;
- passed vertical-guide constraint;
- all 14,161 surface cells and at least 95% initial support;
- no particle-center overlap at the saved loaded observation;
- trajectory-wide maximum center overlap no greater than 10 micrometers;
- no more than 0.02% of all particles inside at any sampled instant.

The 0.02% affected-particle limit was calibrated once from the centered 31 N
and 46 N training actions. It is frozen before the 61 N action and every
non-center action. A later failure shrinks the admitted load/position domain;
it does not justify another tolerance increase.

Strict and coarse status are separate fields. `accepted` and
`mechanics_qualified` retain their original strict meaning. The orchestration
summary adds `coarse_prior.admissible`, `coarse_prior_domain_admitted`, and
`residual_training_permitted`.

## Centered calibration actions

| Action | Chrono loaded time | Max overlap | Max affected fraction | Loaded/residual RMSE | Coarse result |
| --- | ---: | ---: | ---: | ---: | --- |
| 30.656 N | 0.349 s | 3.759 micrometers | 0.00260% | 0.835/0.683 mm | admit |
| 45.984 N | 0.415 s | 4.871 micrometers | 0.01171% | 1.719/1.411 mm | admit |
| 61.313 N | 0.454 s | 6.938 micrometers | 0.01399% | 2.610/2.064 mm | reject |

Both actions fail strict zero penetration and end with zero loaded-state
overlap. The second action exceeded policy v1's 0.01% affected fraction, which
motivated the one-time v2 calibration. No held-out position or 61 N evidence
was used to set v2.

The frozen policy then rejected 61 N because 38 particle centers remained
inside at the saved loaded observation. Its depth and affected fraction were
within v2, but endpoint clearance is mandatory. The initial pilot domain is
therefore capped at 30.656--45.984 N. The 61 N response is preserved as an
out-of-domain rejection case and the gate is not relaxed again.

## Prospective pilot split

- train: center and plus/minus x positions at 30.656 and 45.984 N;
- validation: plus-y position at both retained loads;
- test: minus-y position at both retained loads.

The resulting domain contains 10 actions assigned exactly once. The split was
reissued after the centered 61 N boundary rejection and before any non-center
Newton result was inspected.

## Phase 0 exit for the residual pilot

Phase 0 may exit for the bounded pilot when every action in the final declared
domain has accepted Chrono ground truth, an admissible fixed-0.25 ms Newton
coarse prior, identical H0, and a frozen whole-episode split. This permits an
offline residual experiment. It does not permit claims of strict mechanics,
timestep convergence, real material identification, sequential deformation,
Gaussian accuracy, or planner benefit.

## Verification snapshot before spatial Newton screening

After the 61 N rejection, the plan and live summary were regenerated from the
reissued contract. At this checkpoint:

- the contract contains exactly 10 retained actions at two loads;
- every action is assigned once to the frozen 6/2/2 train/validation/test
  split;
- the two attempted Chrono center episodes are accepted and have exactly
  equal H0 maps;
- the two attempted Newton center responses fail strict mechanics but pass
  bounded policy v2;
- `coarse_prior_domain_admitted` and `residual_training_permitted` remain
  false because eight retained actions are incomplete.

Focused qualification tests pass 10/10. The Newton contract, response,
qualification, BayesOpt seed-policy, and Chrono bridge suites pass 37/37 in
the Newton environment; the model-form diagnostic suite passes 9/9 in the
general environment. A single monolithic test invocation is not a valid
environment check because the Newton environment intentionally lacks unrelated
Torch/Viser/Matplotlib dependencies and the general environment lacks
`plyfile`. These are split-environment dependency boundaries, not failed
qualification assertions.

The machine-readable sources for future updates are `qualification_plan.json`,
`qualification_cases.csv`, and `qualification_summary.json` under the output
directory below. Documentation must follow those artifacts rather than infer
completion from launched processes.

## Canonical artifacts

- contract: `configs/static_proxy_35mm_qualification.json`;
- plan and summary:
  `outputs/validity_experiment/newton/static_proxy_35mm_20261009/`;
- centered responses:
  `outputs/validity_experiment/newton/static_proxy_35mm_20261009/responses/`;
- original strict result:
  [static proxy qualification](static-proxy-qualification-20261009.md).

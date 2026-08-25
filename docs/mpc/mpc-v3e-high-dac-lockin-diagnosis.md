# MPC V3E high-DAC lock-in diagnosis

Date: 2026-08-22

## Classification

**DISCONNECTED_CANDIDATE_ACTION_GRAPH_CONFIRMED**

## Real-run evidence

- SP: `450.0` raw;
- final 10 s mean Median9: `748.587` raw;
- maximum DAC: `11850.0`;
- fraction of active duration in the >=11800-DAC region:
  `80.4%`;
- current empty-baseline mismatch relative to the 288-raw model offset:
  `-61.0` raw.

## Recovered action set

Candidate values:

`[0.0, 11500.0, 11550.0, 11600.0, 11650.0, 11700.0, 11750.0, 11800.0, 11845.626677302696, 11850.0, 11900.0, 11950.0, 12000.0]`

Maximum move:

`750.0 DAC/update`

Connected components:

- component 1: `[0.0]`
- component 2: `[11500.0, 11550.0, 11600.0, 11650.0, 11700.0, 11750.0, 11800.0, 11845.626677302696, 11850.0, 11900.0, 11950.0, 12000.0]`

Low-to-high candidate gap: `11500.0` DAC.

From the equilibrium/high-DAC region around `11845.627` DAC:

- zero reachable: **NO**;
- minimum reachable candidate: `11500.000` DAC.

## Interpretation


The absolute candidate set is separated into disconnected components under the
750-DAC move constraint. The gap between the low candidate region and the first
high-DAC candidate is `11500.0` DAC, which is larger than the allowed move.

Starting near the equilibrium candidate `11845.627` DAC, the zero-DAC
candidate is not reachable. There are no intermediate low-DAC candidates that
allow the optimizer to descend in <=750-DAC steps. This is a structural
action-space limitation consistent with the observed persistent high-DAC
operation.


## Baseline mismatch

The current baseline is approximately 61 raw below the 288-raw model offset.
This remains a separate model-mismatch issue. It should not be conflated with
the candidate-action connectivity issue.

## Recommended additive next step

If the disconnected graph classification is confirmed, create an additive
**MPC V3F** whose first control-law change is only the candidate-action
parameterization:

- candidates derived around current `AppliedDAC`;
- include positive and negative moves;
- each candidate move <=750 DAC/update;
- clamp to 0..12000;
- keep Ts=500 ms;
- keep 9 s delay / 18-sample queue;
- keep tau=4.75 s;
- keep the 60-step / 30 s horizon;
- keep the V3E 1100/1400/1500 raw safety envelope;
- keep SP_RAW=450;
- keep bias adaptation disabled initially.

The empty-offset correction should be evaluated separately with offline replay,
so the dissertation can distinguish action-space and model-offset effects.

## Decision

- higher raw ceiling now: **NO**;
- longer real run before correction: **NO**;
- overwrite V3E: **NO**;
- next controller: **additive V3F, after offline replay validation**.

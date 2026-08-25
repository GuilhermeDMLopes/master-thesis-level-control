# MPC V3G output-bias replay rejection

Date: 2026-08-22

## Result

The first additive V3G output-bias attempt was **not accepted** for 4diac/FORTE
translation.

The preserved real-trace replay reported:

- canonical downward fraction: 100%;
- V3G downward fraction: 100%;
- final learned bias: approximately +41.9 raw;
- classification: `V3G_REAL_TRACE_DECISION_REPLAY_NOT_YET_ACCEPTED`.

## Replay-metric defect

The initial acceptance metric counted any command lower than current AppliedDAC
as a downward action.

At the operating point used by the real V3E trace:

- AppliedDAC was about 11846;
- the canonical equilibrium target was 11845.626677.

Therefore the canonical controller was counted as "downward" even though the
difference was only about 0.373 DAC. This is numerically downward but
operationally negligible.

The 100% canonical downward fraction is therefore not evidence that the
canonical controller was meaningfully reducing pump actuation.

## More important control result

Even after the bias estimate became positive, most selected replay points kept
the same ~11845.6-DAC target. Only isolated points moved to a nearby target such
as 11800.

The learned output bias was about +42 raw, while the prior 7.5AA long-horizon
comparison showed a median future underprediction of about +367.5 raw.

Thus the principal problem is not merely the acceptance metric. A constant
output offset learned from the one-step residual is too small to correct the
observed long-horizon dynamic/equilibrium mismatch.

## Correct next hypothesis

The canonical model has:

`a ~= 0.90009`

A persistent additive disturbance in the **state transition** accumulates over
future prediction steps. Its steady contribution is approximately:

`d / (1 - a)`

and `1/(1-a)` is approximately 10.

Therefore a one-step innovation in the range of 20-40 raw can represent a
long-horizon state/output displacement in the range of roughly 200-400 raw,
which is of the same order as the observed +367.5-raw future mismatch.

This motivates testing an additive process/state-disturbance correction before
changing the identified Hammerstein model.

## Decision

- preserve this V3G attempt: YES;
- translate this V3G attempt to 4diac/FORTE: NO;
- new real experiment now: NO;
- next evaluation: causal process/state-disturbance correction offline.

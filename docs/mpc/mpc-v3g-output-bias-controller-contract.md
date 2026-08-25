# MPC V3G output-bias/disturbance controller contract

## Motivation

The completed real V3E 60 s run showed a dominant model mismatch:

- the optimizer selected the ~11845.6-DAC target on every audited high-PV snapshot;
- baseline-only correction did not change that choice;
- move-weight=0 did not change that choice;
- removing the committed delay history did not change that choice;
- the model predicted a future near 450 raw while the real plant remained hundreds
  of raw above that value.

A held-out comparison then found:

- canonical validation RMSE: about 42.4 raw;
- causal bias-corrected validation RMSE: about 23.6 raw;
- local-refit validation RMSE: about 23.6 raw.

The local refit did not materially outperform the much smaller bias correction.
Therefore V3G first evaluates the minimal additive correction.

## Bias estimator

V3G uses a causal EWMA of the one-step output-model residual:

`r[k] = y[k] - yhat[k|k-1]`

`bias[k] = (1-alpha)*bias[k-1] + alpha*r[k]`

with:

`alpha = 0.10`

The bias is updated only after the current measurement is available, so it is
used for future predictions, not retroactively.

## Prediction interpretation

Positive bias means the physical output is systematically above the canonical
model prediction.

For candidate evaluation, V3G uses the canonical V3 predictor with:

- effective tracking setpoint = `SP - bias`;
- effective predicted soft limit = `soft_limit - bias`;
- effective predicted hard limit = `hard_limit - bias`.

Predicted output values reported externally are shifted back by `+bias`.

This is an additive output-disturbance correction; the identified Hammerstein
model itself is not overwritten.

## Parameters preserved from V3E

Initially unchanged:

- Ts = 500 ms;
- transport delay = 9 s;
- AppliedDAC queue = 18 samples;
- tau = 4.75 s;
- horizon = 60 steps / 30 s;
- existing 13 absolute target candidates;
- DAC envelope = 0..12000;
- maximum move = 750 DAC/update;
- predicted soft limit = 1100 raw;
- predicted hard limit = 1400 raw;
- measured hard limit = 1500 raw;
- SP_RAW = 450.

## Safety

V3G must fail closed if the underlying V3 prediction returns no feasible
candidate.

Positive bias tightens predicted safety limits rather than relaxing them.

## Scope

This stage is Python/offline only. It does not authorize:

- 4diac/FORTE translation;
- real deployment;
- real actuation;
- steady-state-regulation claims.

Before translation, V3G must pass:

1. unit/contract tests;
2. preserved-real-trace decision replay;
3. ideal disturbance closed-loop sanity tests;
4. existing V3/V3E regression tests.

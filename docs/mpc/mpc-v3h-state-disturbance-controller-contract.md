# MPC V3H state/process-disturbance controller contract

## Motivation

The real V3E experiment showed that the canonical model underpredicted the
future level by about 367.5 raw while continuing to select the ~11845.6-DAC
equilibrium target.

A simple output-bias V3G attempt was rejected because its learned ~42-raw
one-step offset did not materially change most long-horizon optimizer
decisions.

The V3H diagnostic then showed that treating the causal innovation as a
persistent state/process disturbance changes the control direction.

The alpha sensitivity selected:

`alpha = 0.10`

with preserved real evidence showing approximately:

- 81.4% of post-SP high-DAC records at or below the 11750-DAC dead-zone;
- 81.4% with >=90% reduction of modeled effective inflow;
- 0% premature dead-zone action in the <=400-raw screening region;
- final equivalent steady shift ~367.3 raw;
- independently measured future model error ~367.5 raw.

## State/process disturbance estimator

Canonical one-step innovation:

`innovation[k] = y[k] - yhat_V3[k|k-1]`

Causal EWMA:

`d_hat[k] = 0.9*d_hat[k-1] + 0.1*innovation[k]`

The estimate is bounded to +/-100 raw per controller step as a numerical
fail-safe in the Python reference.

## Prediction model

The canonical V3/V3E plant model is preserved.

Every prediction state transition becomes:

`y[k+1] = f_V3(y[k], u[k-delay]) + d_hat[k]`

The estimate is held constant over one candidate's prediction horizon.

## Preserved contract

V3H initially preserves:

- canonical V3 plant-model parameters;
- exactly 13 canonical V3 absolute target candidates;
- Ts = 500 ms;
- transport delay = 9 s;
- AppliedDAC history = 18 samples;
- prediction horizon = 60 steps / 30 s;
- DAC envelope = 0..12000;
- maximum move = 750 DAC/update;
- V3E predicted soft limit = 1100 raw;
- V3E predicted hard limit = 1400 raw;
- V3E measured hard limit = 1500 raw;
- SP_RAW = 450.

V1/V2/V3/V3E/V3G remain unchanged.

## Effective-actuation criterion

The actuator model contains a dead-zone at approximately 11750 DAC.

Therefore raw DAC reduction alone is not used as the principal offline
acceptance metric.

The preserved-trace replay evaluates:

- command at or below the dead-zone;
- reduction of the Hammerstein model's effective input contribution;
- premature dead-zone action below SP;
- agreement between the learned steady disturbance effect and the independent
  long-horizon model-error measurement.

## Scope

V3H is still Python/offline only.

This stage does not authorize:

- 4diac/FORTE translation;
- resource deployment;
- real actuation;
- steady-state regulation claims.

Translation is considered only after:

1. V3H contract tests pass;
2. preserved real-trace replay passes;
3. ideal persistent-process-disturbance closed-loop sanity passes;
4. the existing automated regression suite remains green.

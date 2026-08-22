# MPC V3E output-bias versus local-refit evaluation

Date: 2026-08-22

## Classification

**OUTPUT_BIAS_CORRECTION_PREFERRED_AS_MINIMAL_ADDITIVE_FIX**

## Canonical one-step prediction

Across the usable 500 ms samples:

- RMSE: `37.065` raw;
- MAE: `28.784` raw;
- mean residual: `+22.350` raw;
- median residual: `+22.314` raw.

On the held-out final 40% validation segment:

- RMSE: `42.418` raw;
- MAE: `36.706` raw.

## Causal output-bias correction

The bias estimator is an EWMA of the one-step model residual and is updated
only after the current measurement, so it is causal for the next prediction.

Best tested alpha: `0.100`.

Validation:

- RMSE: `23.586` raw;
- MAE: `15.247` raw;
- improvement versus canonical RMSE:
  `44.4%`;
- final learned bias: `+41.894` raw.

## Local affine refit

Diagnostic one-step form:

`y[k] = c + a*y[k-1] + b*phi(u[k-delay])`

Fitted only on the first 60% and validated on the final 40%.

Parameters:

- c: `18.060774435`;
- a: `0.936896278`;
- b: `0.159592833`.

Validation:

- RMSE: `23.648` raw;
- MAE: `16.166` raw;
- improvement versus canonical RMSE:
  `44.2%`.

Excitation / numerical diagnostics:

- delayed-DAC span in fit segment: `11850.0`;
- high-DAC fraction in fit segment: `60.7%`;
- regression rank: `3/3`;
- design-matrix condition number: `1.239e+03`;
- local-refit identifiability weak: **NO**.

## Interpretation

A full local model refit from one commissioning trajectory is only defensible if
there is enough independent input excitation. The completed V3E run spent most
of its time near the high-DAC region, so a strong fit on this single trajectory
can overfit that operating history rather than identify a reusable plant model.

A causal output-bias/disturbance correction is a smaller additive intervention:
it leaves the identified Hammerstein dynamics and 9 s delay intact, but corrects
the persistent output-prediction mismatch observed online.

## Decision

- increase raw ceiling: **NO**;
- new real run now: **NO**;
- overwrite V3/V3E: **NO**;
- preferred next controller, if classification supports it:
  **additive MPC V3G with causal output-bias/disturbance correction**.

Before any 4diac/FORTE translation, the V3G Python reference must be implemented
and closed-loop tested offline.

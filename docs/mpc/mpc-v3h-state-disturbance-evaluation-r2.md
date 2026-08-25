# MPC V3H state/process-disturbance evaluation R2

Date: 2026-08-22

## Evaluator correction

R1 failed because it changed `baseline_raw` and instantiated a new canonical
V3 controller. The V3 constructor uses baseline to recompute its exact
equilibrium target and requires the resulting target set to contain exactly 13
unique values.

R2 does not construct a modified V3 controller.

It freezes the canonical 13 targets and reproduces the authoritative candidate
prediction directly, adding the disturbance explicitly to each state
transition:

`y[k+1] = f_V3(y[k], u[k-delay]) + d_hat`

## Classification

**STATE_DISTURBANCE_CHANGES_CONTROL_DIRECTION__TUNING_REQUIRED**

## Fixed V3 contract

- candidate targets: `[0.0, 11500.0, 11550.0, 11600.0, 11650.0, 11700.0, 11750.0, 11800.0, 11845.626677302696, 11850.0, 11900.0, 11950.0, 12000.0]`;
- candidate count: `13`;
- equilibrium target: `11845.626677302696`;
- max command move: `750 DAC/update`;
- delay: `18 x 500 ms`;
- horizon: `60 x 500 ms`.

## Causal disturbance estimator

`d_hat[k] = 0.9*d_hat[k-1] + 0.1*(y[k]-yhat[k|k-1])`

The steady-state equivalent of a persistent state disturbance is:

`d_hat / (1-a)`

with:

- `a = 0.900087626252`;
- `1/(1-a) = 10.009`.

## Operational decision effect on preserved real trace

Records: `70`.

Canonical controller:

- equilibrium-target fraction: `100.0%`;
- meaningful first-command reduction >=50 DAC:
  `0.0%`;
- median first-command reduction:
  `0.373 DAC`.

State-disturbance evaluation:

- meaningful first-command reduction >=50 DAC:
  `81.4%`;
- meaningful first-command reduction >=250 DAC:
  `0.0%`;
- near-max first-command reduction >=749 DAC:
  `0.0%`;
- zero target fraction:
  `0.0%`;
- median first-command reduction:
  `96.0 DAC`;
- median target reduction:
  `95.6 DAC`;
- median d_hat:
  `+25.553 raw/step`;
- median equivalent steady shift:
  `+255.8 raw`;
- final d_hat:
  `+36.700 raw/step`;
- final equivalent steady shift:
  `+367.3 raw`.

Representative points:

- t=24.50s, Median9=471.0, d_hat=+8.95 raw/step, steady shift=+89.6 raw, canonical target=11845.627, canonical cmd=11845.627, disturbed target=11800.000, disturbed cmd=11800.000, meaningful cmd reduction=46.0 DAC
- t=28.50s, Median9=502.0, d_hat=+7.72 raw/step, steady shift=+77.3 raw, canonical target=11845.627, canonical cmd=11845.627, disturbed target=11800.000, disturbed cmd=11800.000, meaningful cmd reduction=46.0 DAC
- t=33.50s, Median9=522.0, d_hat=+8.03 raw/step, steady shift=+80.3 raw, canonical target=11845.627, canonical cmd=11845.627, disturbed target=11800.000, disturbed cmd=11800.000, meaningful cmd reduction=46.0 DAC
- t=37.50s, Median9=696.0, d_hat=+24.90 raw/step, steady shift=+249.2 raw, canonical target=11845.627, canonical cmd=11845.627, disturbed target=11750.000, disturbed cmd=11750.000, meaningful cmd reduction=96.0 DAC
- t=41.50s, Median9=757.0, d_hat=+30.77 raw/step, steady shift=+308.0 raw, canonical target=11845.627, canonical cmd=11845.627, disturbed target=11750.000, disturbed cmd=11750.000, meaningful cmd reduction=96.0 DAC
- t=45.50s, Median9=706.0, d_hat=+25.58 raw/step, steady shift=+256.0 raw, canonical target=11845.627, canonical cmd=11845.627, disturbed target=11750.000, disturbed cmd=11750.000, meaningful cmd reduction=96.0 DAC
- t=49.50s, Median9=665.0, d_hat=+21.43 raw/step, steady shift=+214.5 raw, canonical target=11845.627, canonical cmd=11845.627, disturbed target=11750.000, disturbed cmd=11750.000, meaningful cmd reduction=96.0 DAC
- t=53.50s, Median9=686.0, d_hat=+23.52 raw/step, steady shift=+235.4 raw, canonical target=11845.627, canonical cmd=11845.627, disturbed target=11750.000, disturbed cmd=11750.000, meaningful cmd reduction=96.0 DAC

## Decision

- rejected output-bias V3G -> 4diac: **NO**;
- modify V3/V3E: **NO**;
- increase raw ceiling: **NO**;
- new real run now: **NO**;
- implement additive Python V3H next:
  **NOT YET**.

No controller source is changed by this evaluation.

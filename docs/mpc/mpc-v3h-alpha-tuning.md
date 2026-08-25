# MPC V3H state-disturbance alpha tuning

Date: 2026-08-22

## Why the R2 250-DAC criterion was too conservative

The V3 plant model is Hammerstein/dead-zone nonlinear.

Resolved dead-zone boundary:

`11750.000 DAC`

Canonical equilibrium target:

`11845.626677 DAC`

The one-step modeled input contribution at the equilibrium target is:

`16.185805 raw/step`

At the dead-zone boundary it is:

`0.000000 raw/step`

Therefore a numerical command reduction of only about 96 DAC from 11846 to
11750 can remove essentially the entire modeled positive inflow contribution.
A requirement such as >=250 DAC is not physically meaningful for this
nonlinear actuator model.

## Independent disturbance-magnitude check

The previously measured median long-horizon future prediction error was:

`367.5 raw`

The state-disturbance estimator is checked against that value through:

`steady shift = d_hat / (1-a)`

with:

- `a = 0.900087626252`;
- `1/(1-a) = 10.009`.

## Alpha sweep

| alpha | cmd <= deadzone after SP | >=90% effective-input reduction | median effective-input reduction | median DAC reduction | premature deadzone <=400 raw | final steady shift | shift error | qualifies |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| 0.02 | 60.0% | 60.0% | 100.0% | 96.0 | 0.0% | +224.6 | 38.9% | NO |
| 0.05 | 72.9% | 72.9% | 100.0% | 96.0 | 0.0% | +322.0 | 12.4% | YES |
| 0.08 | 80.0% | 80.0% | 100.0% | 96.0 | 0.0% | +355.2 | 3.4% | YES |
| 0.10 | 81.4% | 81.4% | 100.0% | 96.0 | 0.0% | +367.3 | 0.1% | YES |
| 0.15 | 85.7% | 85.7% | 100.0% | 96.0 | 0.0% | +381.5 | 3.8% | YES |
| 0.20 | 91.4% | 91.4% | 100.0% | 96.0 | 4.0% | +383.5 | 4.4% | YES |
| 0.30 | 87.1% | 87.1% | 100.0% | 96.0 | 16.0% | +377.9 | 2.8% | YES |
| 0.50 | 82.9% | 82.9% | 100.0% | 96.0 | 24.0% | +374.1 | 1.8% | NO |

## Classification

**V3H_STATE_DISTURBANCE_TUNING_SUPPORTED**

Selected:

`alpha=0.10, final shift=+367.3 raw, dead-zone fraction=81.4%`

## Decision

- rejected output-bias V3G -> 4diac: **NO**;
- increase raw ceiling: **NO**;
- new real run now: **NO**;
- implement additive Python V3H next:
  **YES**;
- 4diac/FORTE translation now: **NO**.

The next implementation, if authorized by this result, must preserve the
canonical 13 V3 targets and add only the causal state/process-disturbance
estimator/predictor.

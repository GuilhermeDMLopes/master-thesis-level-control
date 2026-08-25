# MPC V3H single input-map replay: dead-zone 11750 -> 11550 DAC

## Classification

`V3H_11550_INPUT_MAP_REPLAY_NOT_ACCEPTED__REVIEW_REQUIRED`

## Scope

This is a decision replay on the preserved first active real V3H trace.
It is not a counterfactual closed-loop plant simulation.

Only the in-memory Hammerstein dead-zone was changed:

- canonical: 11750 DAC;
- candidate: 11550 DAC.

The exact existing 13 V3H target candidates, controller period, 9 s delay,
30 s horizon, weights, move limit, DAC envelope, safety limits and
disturbance estimator alpha remain unchanged.

The exact physical dead-zone is still **not** claimed to equal 11550 DAC.

## Model-effect check

- canonical modeled effect at 11600: 0.000000 raw/step;
- 11550-map modeled effect at 11600: 7.433672 raw/step;
- canonical modeled effect at 11750: 0.000000 raw/step;
- 11550-map modeled effect at 11750: 39.235158 raw/step.

## Late plateau result

- late records: 48;
- candidate command <=11550: 0.0%;
- command reduction >=50 DAC: 85.4%;
- command reduction >=150 DAC: 18.8%;
- median command reduction: 75.0 DAC;
- median target reduction: 75.0 DAC;
- premature <=11550 action with PV<=400: 31.6%;
- selected-prediction hard-limit violation fraction: 0.0%.

## Selected snapshots

- t=27.5s: Med9=502.0, Applied=11750.0, canonical target/cmd=11750.000/11750.000, candidate target/cmd=11700.000/11700.000, command reduction=+50.0 DAC;
- t=36.5s: Med9=665.0, Applied=11750.0, canonical target/cmd=11750.000/11750.000, candidate target/cmd=11700.000/11700.000, command reduction=+50.0 DAC;
- t=45.0s: Med9=686.0, Applied=11750.0, canonical target/cmd=11750.000/11750.000, candidate target/cmd=11650.000/11650.000, command reduction=+100.0 DAC;
- t=52.5s: Med9=471.0, Applied=11750.0, canonical target/cmd=11750.000/11750.000, candidate target/cmd=11750.000/11750.000, command reduction=+0.0 DAC;
- t=60.0s: Med9=757.0, Applied=11750.0, canonical target/cmd=11750.000/11750.000, candidate target/cmd=11600.000/11600.000, command reduction=+150.0 DAC;

## Decision

- replay accepted: **NO**;
- exact real dead-zone identified: **NO**;
- one minimal input-map implementation supported: **NO**;
- new MPC variant required: **NO**;
- new real run now: **NO**;

If accepted, the next implementation must alter only the input-map dead-zone
in the existing V3H path and must rerun the existing offline regression,
4diac export/build/type-smoke and protected zero-output gates before any
subsequent active test.

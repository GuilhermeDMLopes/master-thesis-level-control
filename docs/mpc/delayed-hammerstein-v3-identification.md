# Delayed Hammerstein MPC V3 candidate

## Status

Offline identification from the preserved 2026-08-18 real V2 commissioning evidence. No network, PLC, gateway, FORTE, deployment, or actuator write is used by this analysis.

## Physical reference

- physically empty tank: 0.0 cm
- empty raw offset: 288.000
- central bottom pipe drains water by gravity to the lower reservoir

The empty-tank raw offset is treated as the non-negative physical level-state floor. Sensor excursions below it remain measurement noise, not negative water height.

## Preserved evidence

- active V2 CSV: `data/sample/mpc-v3-real-evidence/first-active-v2-20260818-192023.csv`
- active SHA256: `F31AACC2776DA64F76876350CDB28E41451D09A084101EBD2401F0507AED1562`
- empty baseline CSV: `data/sample/mpc-v3-real-evidence/empty-baseline-20260818-192945.csv`
- empty SHA256: `030443E50CC55755FE57A1E3BCDBCA4D6C10C4085D207D736EF2253941E7096D`
- static model: `models/mpc/deadzone-hammerstein-v1.json`
- static model SHA256: `29D0B0AE747D7C2E85963BE9F8C8B619140C8EF73012E69F5A9EC69C2C82A681`

## Empty baseline observation

- samples: 276
- min raw: 267.000
- median raw: 288.000
- mean raw: 287.471
- max raw: 298.000
- initial raw: 288.000
- final raw: 288.000

## Static nonlinearity retained from V1

- dead-zone: 11750.000 DAC
- exponent: 1.200000
- equilibrium gain: 0.680487474306

Only delay and the effective dynamic time constant are reidentified from the latest commissioning transient. This avoids trying to estimate static gain and transient dynamics from one short run.

## V3 delayed dynamic fit

- transport delay: 9.000 s
- delay queue: 18 samples at 500 ms
- tau: 4.750 s
- discrete a: 0.900087626252259
- discrete b: 0.067989118863552
- empirical delay to baseline+50 raw rise: 9.953 s
- V3 replay RMSE: 13.808 raw
- canonical V2 replay RMSE on same interval: 82.911 raw
- V3/V2 RMSE ratio: 0.1665

The replay result supports an explicit transport-delay state. The prior no-delay first-order dynamics are not retained for V3.

## Target implication

- target: 450.000 raw
- implied equilibrium DAC with measured empty offset: 11845.627

## Proposed V3 implementation contract

- control/model sample: 0.500 s
- prediction horizon: 30.0 s
- prediction steps: 60
- target candidates: 13
- candidate prediction iterations/update: 780
- max move: 750.0 DAC/update
- DAC envelope: 0 .. 12000
- applied-DAC history queue required: True
- history queue length: 18 samples

The predictor must initialize its delay queue from actual applied DAC history. Future candidate moves are appended after already committed hydraulic input, so water already in transit is predicted.

Immediate-input bias adaptation must not interpret the transport delay as model bias. Any retained bias estimator must use delayed input sensitivity.

## Scope limitation

The gravity drain is not separately parameterized in this candidate. Its net effect is included in the effective first-order dynamics. A separate Torricelli-style outflow model is intentionally deferred because the available commissioning evidence does not identify its parameters independently and it is not required to move the thesis to a delay-aware MPC validation.

## Decision

```text
MPC V3 DELAYED MODEL CANDIDATE IDENTIFIED: YES
V1 STATIC NONLINEARITY PRESERVED: YES
PHYSICAL EMPTY OFFSET INCLUDED: YES
EXPLICIT TRANSPORT DELAY REQUIRED: YES
REAL ACTUATION BY THIS STAGE: NO
REAL MPC FULL OPERATION AUTHORIZED: NO
```

Next: implement V3 additively in the reference controller and 4diac/FORTE, then replay/simulate offline before another lab run.

# First Real MPC Controller Contract

## Status

This contract defines the first commissioning-stage nonlinear MPC behavior.

It does **not** authorize real-plant MPC execution.

The implementation must remain additive. Existing PI, communication, historical
MPC attempts, and `OPAS_Tank_System` artifacts must not be removed, renamed, or
overwritten.

## Validated offline basis

Controller model:

- dead-zone Hammerstein first-order model
- raw-count process variable
- model baseline: 298 raw
- model time constant: 32 s
- estimated pump dead-zone: 11750 DAC
- nonlinear exponent: 1.2
- target operating point: 450 raw

First commissioning envelope:

- `SP_RAW = 450`
- `DAC_MIN = 0`
- `DAC_MAX = 12000`
- `MAX_DELTA_DAC = 150` per 100 ms cycle
- controller sample time: 100 ms
- prediction horizon: 20 s
- predicted soft level: 650 raw
- predicted hard level: 750 raw
- measured hard level: 800 raw

No first-stage MPC implementation may silently expand these limits.

## Required FB/runtime inputs

The 4diac/FORTE implementation must receive, directly or equivalently:

- `PV_RAW`
- `APPLIED_DAC`
- `ENABLE_REQUEST`
- `EXTERNAL_HEALTHY`
- `RESET_REQUEST`
- `SP_RAW`

`APPLIED_DAC` is required so the controller closes its internal move constraint
around the value that is actually being applied, not merely the previous
requested command.

## Required outputs

The implementation must expose, directly or equivalently:

- `COMMAND_ENABLE`
- `COMMAND_DAC`
- `TRIPPED`
- `TRIP_REASON` or deterministic trip-status code
- `SELECTED_TARGET_DAC`
- `INPUT_BIAS_ESTIMATE_DAC`
- predicted maximum level or equivalent diagnostic

## Fail-closed behavior

The controller must immediately request:

```text
COMMAND_ENABLE = FALSE
COMMAND_DAC    = 0
```

and latch `TRIPPED` when any of these occurs:

1. external health becomes false;
2. `PV_RAW` is non-finite;
3. `PV_RAW >= 800`;
4. `APPLIED_DAC` is non-finite;
5. `APPLIED_DAC` is outside `0..12000`;
6. setpoint is non-finite or outside the stage-safe raw range;
7. no feasible prediction exists.

A latched trip may be cleared only by an explicit reset request.

`ENABLE_REQUEST = FALSE` is a normal disabled state, not a fault. It must still
request zero output.

## Move constraint

While active and healthy:

```text
0 <= COMMAND_DAC <= 12000
abs(COMMAND_DAC - APPLIED_DAC) <= 150
```

This constraint is independent of the downstream limiter. Keeping the existing
downstream rate limiter is recommended for defense in depth.

## Prediction constraints

The MPC prediction must:

- penalize predicted level above 650 raw;
- reject candidates predicted above 750 raw;
- never treat the predicted constraint as a substitute for the measured
  800-raw hard trip.

## Offset compensation

The validated offline controller includes a bounded input-bias estimate.

Bounds:

```text
abs(INPUT_BIAS_ESTIMATE_DAC) <= 250
abs(single bias update)      <= 5 DAC/cycle
```

This compensates moderate dead-zone/model mismatch. It must never enlarge the
physical command envelope above 12000 DAC.

## Implementation sequence

1. Freeze this Python reference behavior with automated tests.
2. Add the MPC implementation to the 4diac project as a new artifact.
3. Keep all PI and historical MPC artifacts unchanged.
4. Validate the new FB offline against the same controller contract.
5. Add explicit PI fallback / MPC enable selection.
6. Only then prepare a real-plant commissioning script.

## Current authorization

- Offline nonlinear MPC robustness: passed.
- Runtime/controller contract: pending.
- 4diac implementation: pending.
- Real MPC: **not authorized**.

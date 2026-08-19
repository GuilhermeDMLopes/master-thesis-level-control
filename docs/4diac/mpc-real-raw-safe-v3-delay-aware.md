# MPC real raw safe V3 - delay-aware 500 ms

## Purpose

`MPC_REAL_RAW_SAFE_V3` is an additive 4diac/FORTE implementation of the
delay-aware V3 reference controller identified from the first real V2
commissioning evidence.

V1, V2 and the historical `MPC_LEVEL.fbt` remain preserved.

## Frozen V3 model

```text
physical empty level            0 cm
empty sensor offset             288 raw
controller period               0.5 s
transport delay                 9.0 s
AppliedDAC history              18 samples
effective time constant         4.75 s
discrete a                      0.900087626252259
discrete b                      0.067989118863552
dead-zone                       11750 DAC
input exponent                  1.2
prediction horizon              30 s
prediction steps                60
target candidates               13
maximum move                    750 DAC/update
DAC envelope                    0 .. 12000
```

The central bottom drain is represented indirectly by the identified real-plant
dynamics. This V3 stage does not introduce an independent hydraulic drain law.

## Delay semantics

The controller stores the last 18 **actual `AppliedDAC`** samples.

During prediction, the oldest queued value acts on the plant first. A newly
selected command is appended behind that already committed hydraulic input.
Therefore a new command cannot cancel water already in transit.

The queue is filled while `ENABLE_REQUEST=FALSE`. Active control is fail-closed
until 18 valid samples have been collected.

A software reset clears the V3 controller trip latch but does not erase the
AppliedDAC history.

## Bias policy

The V2 immediate input-bias adaptation is not reused in V3.

`INPUT_BIAS_ESTIMATE_DAC` remains exactly zero because the identified transport
delay must not be reinterpreted as an instantaneous model-input bias.

## Safety envelope

The outer commissioning envelope remains:

```text
predicted soft level            650 raw
predicted hard level            750 raw
measured hard trip              800 raw
MpcCycle.DT                     T#500ms
MpcSafeDACLimiter.MAX_DELTA     750 DAC/update
DAC_MIN                         0
DAC_MAX                         12000
SP_RAW                          450
ENABLE_REQUEST default          FALSE
```

The independent PLC watchdog and laboratory zero-output/abort supervision remain
authoritative outside this controller.

## Additive 4diac objects

```text
FB type       MPC_MOVE_BLOCKED_NMPC_V3
Application   MPC_REAL_RAW_SAFE_V3
Resource      ResRealRawMPCV3
```

The application/resource outer wiring is cloned from the validated V2
commissioning structure:

- deterministic `E_CYCLE` at 500 ms;
- subscription events do not clock the MPC directly;
- no automatic `START.COLD` / `START.WARM` resource activation;
- same gateway OPC UA NodeIds;
- same final `SAFE_DAC_RATE_LIMITER`;
- complete application/resource mapping.

## State of authorization

This stage is offline only.

It does **not** build FORTE, deploy the application, access the PLC/gateway, or
authorize real MPC actuation.

Next: open/refresh the project in Eclipse 4diac, validate the V3 parser and
network manually, then checkpoint/export/build the V3 type for an isolated
FORTE runtime before any protected real-plant commissioning.

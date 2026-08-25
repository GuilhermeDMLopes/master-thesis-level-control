# MPC_REAL_RAW_SAFE_V1

## Purpose

`MPC_REAL_RAW_SAFE_V1` is the first additive 4diac/FORTE integration of the
offline nonlinear MPC checkpoint tagged `offline-nmpc-v1`.

It does not replace or rename the historical `MPC_LEVEL.fbt`, the validated
`PI_REAL_RAW_SAFE` application, communication experiments, or earlier MPC
attempts.

## Current authorization

This stage is **offline engineering only**.

The new application is created with:

```text
MpcController.ENABLE_REQUEST = FALSE
```

and its dedicated resource has no `START.COLD` or `START.WARM` connection.

Real MPC actuation is not authorized by this stage.

## Runtime signal path

```text
gateway Nivel (raw LREAL)
    |-------------------------------> MPC PV_RAW hard-trip input
    |
    +-> MPC_MEDIAN_FILTER_9
             |
             +----------------------> MPC PV_MODEL

gateway AppliedDAC (Int16)
    -> F_INT_TO_LREAL
    -> MPC APPLIED_DAC

gateway WatchdogHealthy
    -> MPC EXTERNAL_HEALTHY

MPC_MOVE_BLOCKED_NMPC_V1
    -> SAFE_DAC_RATE_LIMITER
       MAX_DELTA_DAC = 150
       DAC_MIN = 0
       DAC_MAX = 12000
    -> F_LREAL_TO_INT
    -> gateway DAC

MPC COMMAND_ENABLE
    -> gateway Enable
```

The gateway already exposes `Nivel`, `AppliedDAC`, and `WatchdogHealthy` as
read-only/runtime values for FORTE in addition to the writable `DAC` and
`Enable` commands.

## Model coordinate

The selected nonlinear model was fitted to rolling-median raw-count
trajectories. Therefore the new application adds `MPC_MEDIAN_FILTER_9` rather
than reusing the PI application's first-order `PV_FILTER`.

The controller receives both:

- `PV_RAW`: the unfiltered level used for the measured `800 raw` hard trip;
- `PV_MODEL`: the 9-sample median used by the prediction model.

This keeps the safety trip responsive to the raw measurement while aligning
the prediction state with the identification data.

## Frozen V1 controller envelope

```text
SP_RAW                  = 450
Ts                      = 0.1 s
prediction horizon      = 20 s (200 prediction steps)
DAC_MIN                 = 0
DAC_MAX                 = 12000
MAX_DELTA_DAC           = 150 per cycle
predicted soft limit    = 650 raw
predicted hard limit    = 750 raw
measured hard trip      = 800 raw
input-bias bound        = +/-250 DAC
single bias update      = +/-5 DAC/cycle
```

Model:

```text
tau                     = 32 s
baseline                = 298 raw
pump dead-zone          = 11750 DAC
input exponent          = 1.2
equilibrium gain        = 0.680487474306...
```

The runtime FB uses a deterministic piecewise-linear approximation of
`max(0, u - 11750)^1.2` over the complete V1 prediction range including the
bounded bias estimate. The approximation is tested offline and does not
require transcendental functions inside Structured Text.

## Trip codes

```text
0 = no trip
1 = external health false
2 = invalid/non-finite PV
3 = measured raw level >= 800
4 = AppliedDAC invalid or outside 0..12000
5 = invalid setpoint
6 = no feasible prediction under the 750-raw predicted hard limit
```

Trips are latched until `RESET_REQUEST=TRUE`.

`ENABLE_REQUEST=FALSE` is a normal disabled mode and requests:

```text
COMMAND_ENABLE = FALSE
COMMAND_DAC    = 0
```

without creating a new trip.

## Historical preservation

The existing `MPC_LEVEL.fbt` remains a historical development artifact. The
validated `PI_REAL_RAW_SAFE` application remains the current real-plant
baseline and fallback.

This stage adds:

```text
Type Library/net_custom/MPC_MEDIAN_FILTER_9.fbt
Type Library/net_custom/MPC_MOVE_BLOCKED_NMPC_V1.fbt
Application: MPC_REAL_RAW_SAFE_V1
Resource:    ResRealRawMPCV1
```

## Required manual IDE validation

After the automated repository tests pass:

1. open/refresh the complete `OPAS_Tank_System` project in Eclipse 4diac;
2. confirm that both new FB types load without parser errors;
3. open `MPC_REAL_RAW_SAFE_V1`;
4. confirm all connections are resolved;
5. confirm `ENABLE_REQUEST=FALSE`;
6. do **not** deploy the application to the real FORTE yet.

The next stage will address 4diac/FORTE zero-output deployment validation.
## Eclipse 4diac IDE validation - 2026-08-10

Manual inspection in Eclipse 4diac passed before this Git checkpoint.

Confirmed:

- MPC_MEDIAN_FILTER_9 opens without parser errors;
- MPC_MOVE_BLOCKED_NMPC_V1 opens without parser errors;
- the Problems view is empty for the inspected MPC artifacts;
- MPC_REAL_RAW_SAFE_V1 opens with resolved main signal connections;
- ResRealRawMPCV1 exists;
- START.COLD and START.WARM are not connected to the MPC network;
- ENABLE_REQUEST = FALSE;
- RESET_REQUEST = FALSE;
- SP_RAW = 450;
- DAC_MAX = 12000;
- MAX_DELTA_DAC = 150;
- AppliedDAC is connected to the controller;
- WatchdogHealthy is connected to the controller;
- PI_REAL_RAW_SAFE remains present;
- historical MPC_LEVEL.fbt remains present.

No FORTE deployment or real actuator command was performed during this
validation.

Real MPC commissioning remains unauthorized.

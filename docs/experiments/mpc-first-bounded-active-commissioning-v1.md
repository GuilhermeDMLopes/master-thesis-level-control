# First bounded active MPC commissioning V1

## Purpose

This is the first experiment in which the real nonlinear MPC is allowed to
produce a physical actuator command.

It follows the successful protected zero-output R5 deployment.

This experiment is intentionally short and ends by stopping FORTE and forcing a
verified zero-output state. It is not a normal closed-loop performance test.

## Initial controller state

Before starting the supervisor:

```text
ResRealRawMPCV1 deployed and initialized
MpcInitMerge.EI1 already executed once after deployment
SP_RAW = 450.0
ENABLE_REQUEST = FALSE
EXTERNAL_HEALTHY = TRUE
TRIPPED = FALSE
TRIP_CODE = 0
```

Observed idle raw level should be inside:

```text
240 .. 340 raw
```

## Existing controller-side limiting

The additive 4diac application already contains the defense-in-depth limiter:

```text
DAC_MIN = 0
DAC_MAX = 12000
MAX_DELTA_DAC = 150 per 100 ms controller cycle
INITIAL_DAC = 0
```

The selected nonlinear model has an identified effective dead-zone around:

```text
11750 DAC
```

Therefore, the first active window must be long enough to cross the rate-limited
dead-zone but short enough to remain a commissioning pulse rather than a
performance experiment.

## Independent supervisor defaults

```text
active duration                  15 s
initial raw band                 240 .. 340
maximum rolling-median raw       550
maximum instantaneous raw        700
maximum positive median rate     180 raw/s
maximum command/applied DAC      12000
sample period                    0.1 s
arm timeout                      60 s
```

These limits are intentionally tighter than the plant's broad physical limits.

## Authorization sequence

The supervisor never writes a positive actuator command and never changes
`ENABLE_REQUEST`.

It first verifies zero output and healthy watchdog state.

After it prints `ARMED`, the operator manually changes only:

```text
MpcController.ENABLE_REQUEST = TRUE
```

The supervisor detects the resulting gateway/PLC output activity and starts the
15-second active timer.

## Automatic abort/end behavior

At any safety violation or at the normal 15-second endpoint, the supervisor:

1. terminates the specified canonical FORTE process;
2. writes `Enable = FALSE` and `DAC = 0` to the gateway;
3. writes `Enable = FALSE` and `DAC = 0` directly to the PLC as a
   defense-in-depth fallback;
4. verifies command and applied output return to zero.

The supervisor does not write `SafetyReset`.

## Immediate abort conditions

The experiment aborts on any of:

- gateway watchdog unhealthy;
- PLC watchdog unhealthy;
- PLC watchdog tripped;
- rolling-median raw level >= 550;
- instantaneous raw level >= 700;
- positive rolling-median level rate >= 180 raw/s;
- gateway/PLC command or applied DAC > 12000;
- negative DAC;
- communication/read failure;
- premature unexplained return to complete zero output during the active window.

The physical stop remains the final safety mechanism if software shutdown does
not verify zero output.

## Interpretation

R6A passes only if:

- real MPC actuation is observed;
- the pump responds without violating any bound;
- the active window ends normally;
- final command and applied output are verified at zero;
- the trajectory is captured in CSV.

Even after R6A passes:

```text
REAL MPC FULL OPERATION AUTHORIZED: NO
```

The trajectory must be inspected before any longer run.
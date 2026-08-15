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

## R6A-1 first active attempt - no-flow result

The first real MPC authorization was executed on 2026-08-15.

Preserved CSV:

```text
data/sample/mpc-first-active-r6a1-no-flow-monitor.csv
```

SHA256:

```text
C6AF1A7F72CE3A5B19B9598ECD94B4DA3E4EF0C401089FBB49047895922DD9B7
```

Observed result:

```text
active window                       approximately 15 s
maximum commanded DAC               6300
maximum applied DAC                 6300
physical pump water delivery        none observed
physical retained level             none observed
watchdog continuously healthy       yes
PLC watchdog trip                   no
final Enable                        false
final DAC                           0
final AppliedEnable                 false
final AppliedDAC                    0
```

The raw sensor signal varied substantially during the active window even though
no physical water delivery was observed. The raw/median trajectory is preserved
as evidence and is not interpreted as physical level movement without further
evidence.

### Timing finding

The original MPC network used:

```text
MpcLevelRead.IND -> MpcMedian9.REQ
```

Therefore controller execution was driven by asynchronous OPC UA subscription
events instead of the intended fixed 100 ms controller period.

The first active CSV reached only DAC 6300 during the approximately 15 s active
window, which was insufficient to reach the previously identified useful pump
region near the actuator dead-zone.

The corrected architecture uses:

```text
MpcLevelRead.INITO -> MpcCycle.START
MpcCycle.DT = T#100ms
MpcCycle.EO -> MpcMedian9.REQ
```

The subscriptions continue updating the latest process values, while the
controller/median/limiter execution chain is now clocked deterministically.

### Shutdown finding

The first R6A supervisor attempted explicit zero-output writes using the generic
high-level write helper and the real B&R PLC returned `BadWriteNotSupported` for
the redundant fallback write.

Despite that warning, subsequent reads verified complete zero output.

The corrected supervisor now uses the same Value-only OPC UA write pattern
already used by the gateway for the B&R PLC:

```text
write_attribute(AttributeIds.Value, DataValue(Variant(...)))
```

A write warning is no longer classified as unsafe if the independent final
readback still verifies all command and applied outputs at zero. Failure to
verify zero remains an abort condition.

## Retry requirement

Do not repeat active MPC commissioning immediately after this software change.

Required sequence:

1. refresh/open the changed MPC application in Eclipse 4diac;
2. confirm `MpcCycle` is present with `DT = T#100ms`;
3. repeat protected deployment with `ENABLE_REQUEST = FALSE`;
4. verify zero output and healthy watchdog;
5. only then execute the next bounded active R6A attempt.

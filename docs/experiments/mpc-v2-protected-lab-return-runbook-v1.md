# MPC V2 protected laboratory return runbook

## Scope

This procedure is the next stage after the successful offline V2 runtime
type-availability smoke test.

It is intended for execution only while physically present in the laboratory.

Target:

```text
FORTE_PC -> ResRealRawMPCV2
```

Validated runtime:

```text
FORTE SHA256
49BB157D27BD0545AC96E50305529C255791BBF5257A14A2563D0FB5F6F13173

open62541.dll SHA256
452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318
```

## Control state required before deployment

```text
MpcController.ENABLE_REQUEST = FALSE
MpcController.RESET_REQUEST  = FALSE
SP_RAW                       = 450
MpcCycle.DT                  = T#500ms
MpcSafeDACLimiter.MAX_DELTA_DAC = 750
MpcSafeDACLimiter.DAC_MIN       = 0
MpcSafeDACLimiter.DAC_MAX       = 12000
```

Initialization remains manual:

```text
MpcInitMerge.EI1
```

Do not trigger initialization until the zero-output guard is already active.

## Laboratory sequence

1. Confirm the physical stop is immediately accessible.
2. Confirm no previous FORTE process is running.
3. Confirm port 61499 is initially free.
4. Confirm the correct PLC/plant is physically available.
5. Start the established Python gateway.
6. Verify PLC OPC UA and gateway OPC UA connectivity.
7. Start only the preserved MPC V2 FORTE runtime.
8. Run the zero-output guard as a short preflight with no deployment.
9. Require continuously healthy watchdog and zero command/applied outputs.
10. Start a protected zero-output guard window long enough for deployment.
11. Deploy only `FORTE_PC -> ResRealRawMPCV2`.
12. Keep `MpcController.ENABLE_REQUEST = FALSE`.
13. Trigger `MpcInitMerge.EI1` exactly once only after the guard is active.
14. Confirm command and applied actuator states remain zero.
15. Save the Deployment Console and zero-output guard CSV.
16. Stop. Do not enable active MPC in this same checkpoint.

## Zero-output acceptance

PASS requires continuous:

```text
Enable=False
DAC=0
AppliedEnable=False
AppliedDAC=0
WatchdogHealthy=True
```

Also require:

```text
no UNSUPPORTED_TYPE for MPC custom FBs
no NO_SUCH_OBJECT involving custom MPC FB instances
no ZERO-OUTPUT VIOLATION
FORTE remains alive
```

## Abort

Abort immediately if any of the following occurs:

```text
Enable becomes TRUE
DAC becomes non-zero
AppliedEnable becomes TRUE
AppliedDAC becomes non-zero
WatchdogHealthy becomes FALSE
FORTE exits unexpectedly
unsupported custom type is reported
resource creation fails
```

On abort, ensure the physical plant returns to safe zero output before any
further test.

## Active MPC

A successful protected zero-output deployment is still not permission for
unbounded MPC operation.

The first active V2 experiment must be a separate, bounded commissioning stage
with explicit level, rate, DAC, watchdog, time-window and automatic shutdown
limits.

```text
REAL MPC FULL OPERATION AUTHORIZED: NO
```

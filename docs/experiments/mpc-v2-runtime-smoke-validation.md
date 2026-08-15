# FORTE MPC V2 offline runtime smoke validation

## Purpose

This checkpoint records the first isolated runtime type-availability validation
of the 500 ms MPC V2 FORTE.

The test did not connect to the PLC or Python gateway and did not initialize or
enable the MPC controller.

## Runtime

```text
forte/preserved-v2/runtimes/mpc-v2/forte.exe

SHA256
49BB157D27BD0545AC96E50305529C255791BBF5257A14A2563D0FB5F6F13173
```

Dependency:

```text
forte/preserved-v2/runtimes/mpc-v2/open62541.dll

SHA256
452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318
```

## Test timestamp

```text
2026-08-15 14:18:50 -03:00
```

## Test conditions

```text
gateway port 4841 initially free: YES
FORTE management port 61499 initially free: YES
existing FORTE process: NO

PLC access by smoke script: NO
gateway access by smoke script: NO
OPC UA writes by smoke script: NO
real actuation: NO
```

The preserved V2 FORTE was started locally and opened management port 61499.

Using Eclipse 4diac, only this resource was deployed:

```text
FORTE_PC -> ResRealRawMPCV2
```

The following actions were explicitly prohibited and were not performed:

```text
deploy whole System
deploy whole FORTE_PC device
deploy ResRealRawMPCV1
trigger MpcInitMerge.EI1
change MpcController.ENABLE_REQUEST
start Monitoring
```

## Result

The deployment console was confirmed clean for the three custom FB types and
the FORTE runtime logs contained neither `UNSUPPORTED_TYPE` nor
`NO_SUCH_OBJECT`.

```text
MPC_MEDIAN_FILTER_9 runtime type accepted: YES
MPC_MOVE_BLOCKED_NMPC_V2 runtime type accepted: YES
SAFE_DAC_RATE_LIMITER runtime type accepted: YES

MpcInitMerge.EI1 triggered: NO
gateway available: NO
real plant actuation path available: NO

FORTE remained running after deployment: YES
FORTE process after shutdown: NO
port 61499 after shutdown: CLOSED
```

## Evidence

```text
data/sample/mpc-v2-runtime-smoke-20260815-141850/forte-mpc-v2-smoke-20260815-141850.out.log
SHA256 E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855

data/sample/mpc-v2-runtime-smoke-20260815-141850/forte-mpc-v2-smoke-20260815-141850.err.log
SHA256 E840034E18C173A03D4E101CEA4F7FB5A89A38846B09AEB723AD92962AAA214A
```

## Interpretation

This checkpoint validates that the isolated FORTE V2 runtime can instantiate
the custom types required by `ResRealRawMPCV2`.

It does **not** validate closed-loop control, plant response, actuator behavior,
or real MPC performance.

```text
REAL MPC FULL OPERATION AUTHORIZED: NO
```

The next meaningful validation requires physical presence in the laboratory and
must begin with a protected zero-output deployment using the real gateway/PLC
path.

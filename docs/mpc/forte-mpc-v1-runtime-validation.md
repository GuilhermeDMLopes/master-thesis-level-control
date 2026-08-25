# FORTE MPC V1 runtime validation

## Scope

This checkpoint records the transition from an additive 4diac MPC definition to
a FORTE runtime that actually contains the three required custom function block
types.

No real MPC actuation was authorized by these stages.

## Exporter compatibility correction

MPC_MOVE_BLOCKED_NMPC_V1.fbt was corrected after the FORTE 1.x NG exporter
rejected integer-form typed LREAL literals and a typed scientific-notation
sentinel.

The corrected ST passed:

- XML parsing;
- the MPC contract suite;
- the full automated test suite;
- FORTE 1.x NG C++ export.

A regression test was added to prevent the rejected literal forms from being
reintroduced.

## Isolated FORTE MPC V1 build

Build directory:

$BuildDir

Validation runtime directory:

$RuntimeDir

Validated executable SHA256:

$ExpectedForteSha256

The isolated build has OPC UA, conversion, IEC 61131 and utility support enabled
and includes the dedicated external module containing only the MPC V1 custom
types.

Compiled evidence:

- $(@{Name=MPC_MEDIAN_FILTER_9; ObjectPath=C:\Users\guilh\4diac\4diac-forte\build-mpc-v1\src\FORTE_LITE.dir\Debug\MPC_MEDIAN_FILTER_9.obj; ObjectBytes=163808; GeneratedPath=C:\Users\guilh\4diac\4diac-forte\build-mpc-v1\src_gen\MPC_MEDIAN_FILTER_9_gen.cpp}.Name): object size 163808 bytes; generated source present.
- $(@{Name=MPC_MOVE_BLOCKED_NMPC_V1; ObjectPath=C:\Users\guilh\4diac\4diac-forte\build-mpc-v1\src\FORTE_LITE.dir\Debug\MPC_MOVE_BLOCKED_NMPC_V1.obj; ObjectBytes=394155; GeneratedPath=C:\Users\guilh\4diac\4diac-forte\build-mpc-v1\src_gen\MPC_MOVE_BLOCKED_NMPC_V1_gen.cpp}.Name): object size 394155 bytes; generated source present.
- $(@{Name=SAFE_DAC_RATE_LIMITER; ObjectPath=C:\Users\guilh\4diac\4diac-forte\build-mpc-v1\src\FORTE_LITE.dir\Debug\SAFE_DAC_RATE_LIMITER.obj; ObjectBytes=199861; GeneratedPath=C:\Users\guilh\4diac\4diac-forte\build-mpc-v1\src_gen\SAFE_DAC_RATE_LIMITER_gen.cpp}.Name): object size 199861 bytes; generated source present.

## Offline runtime type-availability smoke test

The isolated runtime was started with the Python gateway absent and local port
4841 closed.

Only ResRealRawMPCV1 was deployed from Eclipse 4diac.

The deployment console accepted the three custom runtime types:

- MPC_MEDIAN_FILTER_9;
- MPC_MOVE_BLOCKED_NMPC_V1;
- SAFE_DAC_RATE_LIMITER.

The previous UNSUPPORTED_TYPE failure was therefore resolved.

During this smoke test:

- MpcInitMerge.EI1 was not triggered;
- monitoring was not started;
- the Python gateway was absent;
- no real plant command path was available;
- no real actuator command was issued;
- FORTE was stopped after the test.

## Zero-output guard history

The first zero-output deployment guard used incorrect B&R PLC NodeIds and is
preserved under:

$ArchivedGuard

The corrected implementation is the canonical:

$CanonicalGuard

The corrected guard previously completed a real read-only 10 s preflight with:

- Enable = FALSE;
- DAC = 0;
- AppliedEnable = FALSE;
- AppliedDAC = 0;
- WatchdogHealthy = TRUE.

## Decision

UNSUPPORTED_TYPE for the MPC V1 custom FBs is resolved.

REAL MPC AUTHORIZED: **NO**

Next step: repeat the protected zero-output deployment using the MPC-capable
FORTE executable, keep ENABLE_REQUEST = FALSE, initialize the MPC resource
only after the independent guard is active, and require continuous zero output
before any active MPC commissioning is considered.
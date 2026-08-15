# MPC real raw safe V2 - 500 ms

## Purpose

`MPC_REAL_RAW_SAFE_V2` is an additive commissioning application created after
the real-plant V1 timing experiments showed that the synchronous nonlinear MPC
could not complete reliably within the original 100 ms compute budget.

The complete V1 implementation is preserved.

## Timing contract

```text
MpcCycle type                  E_CYCLE
MpcCycle.DT                    T#500ms
prediction model sample        0.5 s
prediction horizon             20 s
prediction steps               40
MPC maximum move/update        750 DAC
4diac safe limiter move        750 DAC/update
equivalent controller rate     1500 DAC/s
DAC_MIN                        0
DAC_MAX                        12000
SP_RAW                         450
ENABLE_REQUEST default         FALSE
```

The move envelope is intentionally preserved in physical time:

```text
V1: 150 DAC / 0.1 s = 1500 DAC/s
V2: 750 DAC / 0.5 s = 1500 DAC/s
```

## Computation

The target grid remains 13 candidates.

```text
V1: 13 x 200 = 2600 prediction iterations
V2: 13 x 40  =  520 prediction iterations
```

The V2 inner prediction workload is therefore reduced by 80 percent.

## Model discretization

The same identified nonlinear plant model is retained and rediscretized at
500 ms:

```text
a = 0.984496437005408
b = 0.010549980424939
```

Model provenance:

`models/mpc/deadzone-hammerstein-v1.json`

## V2 commissioning cost

```text
tracking stage weight       5.0
move stage weight           0.00004
soft-level stage weight     100.0
terminal weight             10.0
```

## Application/resource

New application:

`MPC_REAL_RAW_SAFE_V2`

New manual-start resource:

`FORTE_PC -> ResRealRawMPCV2`

Initialization remains manual through `MpcInitMerge.EI1`.

```text
MpcLevelRead.INITO -> MpcCycle.START
MpcCycle.EO        -> MpcMedian9.REQ
```

There is no automatic `START.COLD` or `START.WARM` connection for V2.

## Preservation

The following remain preserved:

- `MPC_MOVE_BLOCKED_NMPC_V1`;
- `MPC_REAL_RAW_SAFE_V1`;
- `ResRealRawMPCV1`;
- historical `MPC_LEVEL`;
- validated PI applications.

## Current authorization

```text
FORTE V2 runtime built: NO
FORTE V2 deployed: NO
real V2 actuation: NO
REAL MPC FULL OPERATION AUTHORIZED: NO
```

## Eclipse 4diac IDE validation record

Manual validation recorded at:

```text
2026-08-15T12:05:45-03:00
```

Operator confirmed in Eclipse 4diac:

```text
MPC_MOVE_BLOCKED_NMPC_V2 opens without parser error: YES
MPC_REAL_RAW_SAFE_V2 opens correctly: YES
ResRealRawMPCV2 opens correctly: YES
Problems contains no V2 error: YES
MpcCycle.DT = T#500ms: YES
MpcController type = MPC_MOVE_BLOCKED_NMPC_V2: YES
MpcSafeDACLimiter.MAX_DELTA_DAC = 750: YES
MpcController.ENABLE_REQUEST = FALSE: YES
MpcLevelRead.IND -> MpcMedian9.REQ absent: YES
automatic START.COLD / START.WARM V2 resource connection absent: YES
```

This record is paired with automated XML/ST regression validation in
`tests/test_mpc_4diac_v2_contract.py`.

No FORTE V2 build or deployment was performed as part of this IDE checkpoint.

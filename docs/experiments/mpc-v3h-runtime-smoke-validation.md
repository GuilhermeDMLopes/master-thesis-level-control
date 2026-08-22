# MPC V3H runtime type-smoke validation

Date: 2026-08-22

## Scope

This validation checked only whether the isolated FORTE V3H runtime accepts
the custom function-block types required by ResRealRawMPCV3H.

No gateway was running. Port 4841 remained closed. MpcInitMerge.EI1 was not
triggered. No PLC access or real actuation occurred.

## Runtime

FORTE:

$ForteExe

SHA256:

$ForteHash

open62541:

$Open62541

SHA256:

$OpenHash

## Deployment scope

Only:

FORTE_PC -> ResRealRawMPCV3H

was deployed.

The full System and full Device were not deployed.

## Result

Accepted runtime types:

- MPC_MEDIAN_FILTER_9;
- MPC_MOVE_BLOCKED_NMPC_V3H;
- SAFE_DAC_RATE_LIMITER.

Runtime evidence contained:

- UNSUPPORTED_TYPE: no;
- NO_SUCH_OBJECT: no.

MpcInitMerge.EI1 triggered: **NO**.

Gateway available during smoke: **NO**.

Real plant actuation path available during smoke: **NO**.

FORTE was stopped after the validation and management port 61499 closed.

## Evidence

stdout:

data/sample/mpc-v3h-runtime-smoke-20260822-120740/forte-mpc-v3h-smoke-20260822-120740.out.log

SHA256:

$OutHash

stderr:

data/sample/mpc-v3h-runtime-smoke-20260822-120740/forte-mpc-v3h-smoke-20260822-120740.err.log

SHA256:

$ErrHash

## Classification

OFFLINE_V3H_RUNTIME_TYPE_SMOKE_PASSED

This result authorizes preparation of a protected zero-output deployment only.
It does not authorize active MPC V3H operation.

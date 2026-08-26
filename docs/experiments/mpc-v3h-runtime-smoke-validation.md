# MPC V3H runtime type-smoke validation

Date: 2026-08-22

## Scope

This validation checked only whether the isolated FORTE V3H runtime accepts
the custom function-block types required by ResRealRawMPCV3H.

No gateway was running. Port 4841 remained closed. MpcInitMerge.EI1 was not
triggered. No PLC access or real actuation occurred.

## Runtime

FORTE:

C:\Projetos\forte-mpc-v3h-runtime\mpc-v3h-candidate\forte.exe

SHA256:

8B3D4E7BA1B87F678AD4BE6F991FC16C00CE010B36EA4D49C205874553DBBAD2

open62541:

C:\Projetos\forte-mpc-v3h-runtime\mpc-v3h-candidate\open62541.dll

SHA256:

452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318

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

E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855

stderr:

data/sample/mpc-v3h-runtime-smoke-20260822-120740/forte-mpc-v3h-smoke-20260822-120740.err.log

SHA256:

1EBE4973A96C3D208BD45CDAD05B0C0E743FB513409D9A7A5D3B992BD696708F

## Classification

OFFLINE_V3H_RUNTIME_TYPE_SMOKE_PASSED

This result authorizes preparation of a protected zero-output deployment only.
It does not authorize active MPC V3H operation.

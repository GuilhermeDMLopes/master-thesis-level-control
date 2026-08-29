# Preserved FORTE MPC V3H 3.9 candidate

This directory preserves the final offline-built runtime and the exact external
module used for the M5 resource-only type smoke.

## Controller export

- `MPC_MOVE_BLOCKED_NMPC_V3H.cpp`: `8E4416BA2EA270F23C58EF44AD9C420BEA776875F2154CE7DE8439F0D36FFF26`
- `MPC_MOVE_BLOCKED_NMPC_V3H.h`: `FCD18ACA11255185800DA27BDC02CB0AC0C7127CA0884583D9FC7A2295170576`

## Runtime

- `forte.exe`: `2535F31A5A5FC246BFC699ABDB4171531C71E56C4B72675D284C1322F7FAF31A`
- `open62541.dll`: `452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318`

The runtime type smoke deployed only `FORTE_PC.ResRealRawMPCV3H`. The gateway
was absent, `MpcInitMerge.EI1` was not triggered, and no PLC access or real
actuation occurred.

# MPC V3H 3.9 runtime type-smoke validation

Date: 2026-08-26

## Scope

The isolated final runtime accepted the custom types required by
`FORTE_PC.ResRealRawMPCV3H`. Only that resource was deployed. The full System
and Device were not deployed, `MpcInitMerge.EI1` was not triggered, monitoring
was not started, and no gateway or PLC was available.

## Runtime hashes

- FORTE SHA256: `2535F31A5A5FC246BFC699ABDB4171531C71E56C4B72675D284C1322F7FAF31A`
- open62541 SHA256: `452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318`
- controller C++ SHA256: `8E4416BA2EA270F23C58EF44AD9C420BEA776875F2154CE7DE8439F0D36FFF26`
- controller header SHA256: `FCD18ACA11255185800DA27BDC02CB0AC0C7127CA0884583D9FC7A2295170576`

## Result

- `MPC_MEDIAN_FILTER_9`: accepted;
- `MPC_MOVE_BLOCKED_NMPC_V3H`: accepted;
- `SAFE_DAC_RATE_LIMITER`: accepted;
- `UNSUPPORTED_TYPE`: absent;
- `NO_SUCH_OBJECT`: absent;
- management port 61499 closed after the smoke;
- gateway ports 4841 and 4842 remained closed.

## Preserved evidence

Directory:

`data/sample/mpc-v3h-3_9-runtime-smoke-20260826-213438/`

- stdout SHA256: `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`
- stderr SHA256: `537844F1C606EC573C734C296914DCEC6EA13EC992E6E6828D4206E03416F108`
- summary SHA256: `CC7F42F4F0FB6337BC484FC3DCCA9A44522C5054C366D8FF9306FF16B3560639`

Classification: `OFFLINE_V3H_3_9_RUNTIME_TYPE_SMOKE_PASSED`.

This result authorizes only the next protected zero-output laboratory gate. It
does not authorize active real-plant operation by itself.

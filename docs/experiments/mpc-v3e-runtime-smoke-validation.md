# MPC V3E runtime smoke validation

Date: 2026-08-22

## Runtime

- FORTE: `C:\Projetos\forte-mpc-v3e-runtime\mpc-v3e-candidate\forte.exe`
- FORTE SHA256: `B55B040828BAF5DAD961B04DE04DA625BC680E1FBAF0F04F595EB803D2F3B9E6`
- open62541 SHA256: `452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318`

## Test conditions

- gateway absent;
- gateway port 4841 closed;
- PLC access by script: no;
- OPC UA writes: no;
- real actuation: no;
- isolated FORTE management connection only;
- deployed resource: `FORTE_PC -> ResRealRawMPCV3E`;
- `MpcInitMerge.EI1` not triggered;
- `MpcController.ENABLE_REQUEST` unchanged / FALSE;
- Monitoring not started.

## Result

The isolated runtime accepted all required custom types:

- `MPC_MEDIAN_FILTER_9`: accepted;
- `MPC_MOVE_BLOCKED_NMPC_V3E`: accepted;
- `SAFE_DAC_RATE_LIMITER`: accepted.

Runtime logs contained:

- `UNSUPPORTED_TYPE`: no;
- `NO_SUCH_OBJECT`: no.

FORTE remained running after resource deployment and was stopped at the end of
the smoke test. No real-plant actuation path was available during this test.

## Preserved evidence

- stdout: `data/sample/mpc-v3e-runtime-smoke-20260822-101515/forte-mpc-v3e-smoke-20260822-101515.out.log`
  - SHA256: `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`
- stderr: `data/sample/mpc-v3e-runtime-smoke-20260822-101515/forte-mpc-v3e-smoke-20260822-101515.err.log`
  - SHA256: `D009BD8E834FF2AFE95D909F9F2F1D530E9B470861602DB68AD66C76CF1CC2EF`

## Status

Offline V3E runtime type smoke: **PASSED**.

Real MPC V3E operation remains **not authorized** until a protected real-plant
deployment is performed with zero-output validation, one-time initialization,
watchdog supervision, and independent physical-height observation.

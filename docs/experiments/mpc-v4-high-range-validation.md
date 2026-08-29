# MPC V4 high-range real-plant validation

## Objective

Validate the final 4diac/FORTE MPC around the physical 15 cm operating point.
The earlier 20 s V3H 3.9 run remains a valid actuation-chain commissioning
result, but it is not used as performance evidence.

## Evidence basis

- 0 cm: approximately 257 raw;
- 5 cm: 4465 raw;
- 8.5 cm: 8503 raw;
- 13 cm: 13791 raw;
- the 13 cm point required DAC 16000 for 80 s;
- the first 180 s V4 run stabilized near 15700 raw at approximately 14 cm;
- the refined 15 cm target is 17000 raw and must be confirmed manually
  during the follow-up run.

The joint high-range replay identifies a 500 ms first-order model with
`a=0.997231776304349`, `b=0.004607840412330`, dead zone 11750 DAC and exponent
1.2. Its joint replay RMSE is approximately 146 raw. This model is intentionally
separate from the fast low-range V3H dynamics.

## First real V4 result and target refinement

The first complete 180 s V4 run ended normally with verified zero output. It
reached a maximum of 15945 raw, a maximum median9 of 15853 raw and a physical
height of approximately 14 cm. During the final 20 s the controller was not
saturated at the 16000 DAC ceiling; it mainly selected 14500 DAC while tracking
the original 16000 raw setpoint. Therefore, increasing the actuator ceiling
would not correct the final level. The follow-up changes only `SP_RAW` from
16000 to 17000 and preserves `DAC_MAX=16000` and every safety limit.

## Frozen V4 contract

- application: `MPC_REAL_RAW_SAFE_V4`;
- resource: `FORTE_PC.ResRealRawMPCV4`;
- controller: `MPC_MOVE_BLOCKED_NMPC_V4`;
- sample time: 500 ms;
- prediction horizon: 30 s / 60 steps;
- setpoint: 17000 raw, refined target for approximately 15 cm;
- actuator range: 0..16000 DAC;
- maximum move: 750 DAC per 500 ms;
- predicted soft limit: 18000 raw;
- predicted hard limit: 19500 raw;
- measured hard trip: 20000 raw;
- independent supervisor window: 180 s;
- supervisor median/instant limits: 19000/20000 raw;
- operator physical abort: 20 cm;
- declared plant safe maximum: 25 cm.

`ENABLE_REQUEST` remains `FALSE` by default. The independent supervisor never
writes a positive DAC or enables the plant; it only observes, terminates FORTE,
writes safe zero on completion/abort and verifies the applied zero state.

## Required offline gate

The V4 type must be exported, compiled into a dedicated FORTE runtime and pass a
local type-only smoke test before any gateway, PLC or plant access. The real run
must start from a visually empty tank and preserve the full monitor CSV, gateway
CSV, FORTE logs, manual maximum height and final independent zero-output check.

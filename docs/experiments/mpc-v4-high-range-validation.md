# MPC V4 high-range real-plant validation

## Objective and status

The final 4diac/FORTE MPC was validated around the physical 15 cm operating
point on 2026-08-29. The complete 180 s V4 run reached 15 cm and stabilized,
then ended with verified zero output. This closes the bounded real-plant MPC
performance stage.

The earlier 20 s V3H 3.9 run remains valid actuation-chain commissioning
evidence. The first 180 s V4 run remains the basis for the target refinement
from 16000 to 17000 raw.

## Evidence basis

- 0 cm: approximately 257 raw in the preserved M3 calibration;
- 5 cm: 4465 raw;
- 8.5 cm: 8503 raw;
- 13 cm: 13791 raw;
- first V4 run: approximately 14 cm and 15700 raw in the final interval;
- final V4 run: 15 cm physically observed, with a 17000 raw target.

The joint high-range replay identifies a 500 ms first-order model with
`a=0.997231776304349`, `b=0.004607840412330`, dead zone 11750 DAC and exponent
1.2. Its joint replay RMSE is approximately 146 raw. This high-range model is
intentionally separate from the fast low-range V3H dynamics.

## Frozen final V4 contract

- application: `MPC_REAL_RAW_SAFE_V4`;
- resource: `FORTE_PC.ResRealRawMPCV4`;
- controller: `MPC_MOVE_BLOCKED_NMPC_V4`;
- sample time: 500 ms;
- prediction horizon: 30 s / 60 steps;
- setpoint: 17000 raw;
- physical target: 15 cm;
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
writes a positive DAC or enables the plant. It observes the real state,
terminates FORTE, writes safe zero on completion or abort, and verifies the
applied zero state.

## Final result

The final active window completed at 179.969 s with 1481 active samples. The
maximum median-9 level was 17086 raw, corresponding to 0.506% overshoot. The
last-30-s mean was 16848.45 raw, 151.55 raw below the target, and its standard
deviation was 107.59 raw. The mean applied DAC over the same interval was
14092.91, with a 13500..14500 range.

The physical level reached 15 cm and stabilized. The controller first used the
16000 DAC ceiling to fill the tank, then reduced the command to balance the
continuous bottom drain. The watchdog remained healthy for every active sample.

Before deployment, 695 samples confirmed zero output. After the active window,
FORTE was terminated and 74 independent samples confirmed that command and
applied output remained zero. The gateway was then stopped and ports 4841 and
61499 were closed.

Full metrics, evidence hashes, interpretation and figures are documented in
`docs/experiments/mpc-v4-target17000-20260829-analysis.md`.

## Scope

This result validates the bounded experimental MPC implementation required for
the dissertation. It does not authorize unattended or unrestricted future
real-plant operation. The high-range fit remains a commissioning model rather
than a fully observed steady-state map, and the manual 15 cm observation is the
authoritative physical interpretation of the final raw-count trajectory.

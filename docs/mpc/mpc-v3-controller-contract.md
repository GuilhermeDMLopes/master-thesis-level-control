# MPC V3 delay-aware reference controller contract

## Scope

This stage implements the identified V3 delayed Hammerstein model only in the
offline Python reference controller. It does not access PLC, gateway, FORTE,
OPC UA, or the physical actuator.

## Frozen V3 model

The controller loads `models/mpc/delayed-hammerstein-v3-candidate.json` and
requires:

- sample time: 0.5 s;
- transport delay: 9.0 s;
- applied-DAC queue: 18 samples;
- effective dynamic time constant: 4.75 s;
- physical empty-state offset: 288 raw;
- dead-zone: 11750 DAC;
- input exponent: 1.2;
- prediction horizon: 30 s / 60 steps;
- 13 target candidates;
- maximum move: 750 DAC/update;
- DAC envelope: 0..12000.

## Delay-state semantics

The queue stores **actual applied DAC**, not requested DAC. At prediction time,
its oldest sample is the hydraulic input already due to affect the plant.
Candidate future commands are appended behind this committed queue. Therefore a
new command cannot cancel water already in transit.

The controller must observe 18 valid applied-DAC samples before active control
is allowed. While `ENABLE_REQUEST=FALSE`, the controller continues filling the
queue and always commands `Enable=FALSE`, `DAC=0`.

A software reset clears the controller trip latch but intentionally does not
erase the applied-DAC queue.

## Bias policy

Input-bias adaptation is disabled in the first V3 implementation. The V2
immediate-input adaptation is not reused because it could interpret the
identified transport delay as an input-model bias.

## Safety envelope

The V2 safety envelope remains unchanged:

- predicted soft level: 650 raw;
- predicted hard level: 750 raw;
- measured hard trip: 800 raw;
- DAC: 0..12000;
- maximum move: 750 DAC per 500 ms.

The controller remains fail-closed on invalid inputs, unhealthy external state,
insufficient delay history, measured hard limit, applied-DAC envelope
violation, invalid setpoint, or absence of a feasible prediction.

## Offline acceptance

The contract tests verify:

- exact V3 identified parameters;
- 18-sample history readiness gate;
- delayed candidate propagation;
- no bias adaptation;
- pre-emptive reduction with a committed 12000-DAC pipeline;
- ideal delayed closed-loop convergence to 450 raw without significant
  overshoot;
- V2 safety limits remain enforced;
- no network or actuator code is present.

Real MPC operation is not authorized by this stage.

Next: translate this validated V3 reference behavior additively into
`MPC_MOVE_BLOCKED_NMPC_V3`, `MPC_REAL_RAW_SAFE_V3`, and `ResRealRawMPCV3`.

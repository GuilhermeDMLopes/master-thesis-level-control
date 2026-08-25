# MPC V2 500 ms timing contract

## Status

This document proposes an additive second commissioning controller.

It does not modify or replace the preserved MPC V1 contract.

Real MPC full operation remains unauthorized.

## Evidence motivating V2

R6A-2 used the V1 controller with an E_CYCLE configured at 100 ms.

The protected active run completed safely but reached only approximately
5850 DAC in the 15-second window and produced no physical water flow.

The preserved R6A-2 evidence is:

```text
data/sample/mpc-first-active-r6a2-100ms-no-flow-monitor.csv
SHA256: 866D99AA3CA79C54E62002591B8D1A9D79FF95CFD8663F74A8B3E502151560E6
```

Inspection of the generated V1 FORTE controller shows:

```text
target candidates       13
prediction steps        200
prediction horizon      20 s
prediction iterations   2600 per optimization
move limit              150 DAC per controller update
```

The 100 ms timer therefore cannot force 10 Hz closed-loop execution when one
synchronous NMPC evaluation takes substantially longer than 100 ms.

## V2 timing proposal

```text
controller compute period      500 ms
prediction model sample        500 ms
prediction horizon             20 s
prediction steps               40
candidate grid                 unchanged
maximum move/update            750 DAC
equivalent move rate           1500 DAC/s
DAC envelope                   0 .. 12000
setpoint                       450 raw
```

The prediction loop therefore falls from approximately:

```text
13 x 200 = 2600
```

to:

```text
13 x 40 = 520
```

candidate prediction steps per controller evaluation, an 80 percent reduction.

## Objective-function scaling

With five times fewer prediction samples, V2 uses the commissioning proposal:

```text
tracking weight        5.0
move weight            0.00004
soft-level weight      100.0
terminal weight        10.0
```

This approximately preserves the physical-horizon contribution of the V1
stage costs while accounting for the larger 750-DAC control increment.

## Defense in depth

The V2 controller does not enlarge the approved actuator envelope:

```text
0 <= DAC <= 12000
```

The controller move envelope remains equivalent in physical time:

```text
V1: 150 DAC / 0.1 s = 1500 DAC/s
V2: 750 DAC / 0.5 s = 1500 DAC/s
```

The existing gateway final boundary limiter remains an independent protection
layer and continues limiting each successful gateway DAC write by 150 units.

## Implementation rule

V2 must be additive.

Do not overwrite:

- MPC_MOVE_BLOCKED_NMPC_V1;
- the V1 controller contract;
- historical MPC_LEVEL;
- the validated PI applications.

The next stage may create a V2 FB/application/resource only after this offline
contract passes.

## Current authorization

```text
MPC V1 real commissioning: no-flow timing limitation identified
MPC V2 offline timing contract: pending execution of 7.4C
REAL MPC FULL OPERATION AUTHORIZED: NO
``

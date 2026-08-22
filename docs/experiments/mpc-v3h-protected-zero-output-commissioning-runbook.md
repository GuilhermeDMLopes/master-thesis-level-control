# MPC V3H protected zero-output commissioning runbook

## Purpose

Prepare and validate MPC_REAL_RAW_SAFE_V3H on the real communication stack
while the actuator remains at zero.

This runbook does **not** authorize active MPC operation.

## Validated runtime

FORTE SHA256:

$ForteHash

open62541 SHA256:

$OpenHash

Required resource:

FORTE_PC -> ResRealRawMPCV3H

## Required initial state

Before deployment:

- physical/emergency stop accessible;
- tank visually safe;
- physical level below the operator abort threshold used for V3E/V3H laboratory work;
- PI and all other MPC resources stopped;
- PLC actuator state verified zero;
- gateway healthy;
- isolated V3H FORTE is the only FORTE runtime;
- MpcController.ENABLE_REQUEST = FALSE;
- zero-output guard active before deployment/init.

## Deployment scope

Deploy only:

FORTE_PC -> ResRealRawMPCV3H

Do not deploy:

- the whole System;
- the whole FORTE_PC Device;
- V1, V2, V3 or V3E resources.

## Initialization

On a **fresh** V3H resource deployment, and only while the zero-output guard is
active:

1. keep ENABLE_REQUEST = FALSE;
2. trigger MpcInitMerge.EI1 exactly once;
3. confirm actuator state remains:
   - Enable = FALSE;
   - DAC = 0;
   - AppliedEnable = FALSE;
   - AppliedDAC = 0;
4. confirm watchdog/communication health remains acceptable after initialization.

If the resource is redeployed, the initialization count restarts for that fresh
deployment. Do not use repeated EI1 triggers as a normal operating action.

## V3H estimator behavior while disabled

The V3H implementation clears its disturbance-estimator state while
ENABLE_REQUEST = FALSE.

Therefore zero-output commissioning validates:

- resource creation;
- OPC UA FB connections;
- initialization event path;
- safety/watchdog state;
- zero actuator output.

It does **not** validate learning of d_hat; disturbance adaptation is evaluated
only during a later explicitly authorized active run.

## V3H control contract retained for later active testing

- Ts: 500 ms;
- delay: 9 s;
- AppliedDAC history: 18 samples;
- prediction horizon: 60 steps / 30 s;
- maximum move: 750 DAC/update;
- DAC envelope: 0..12000;
- predicted soft limit: 1100 raw;
- predicted hard limit: 1400 raw;
- measured hard limit: 1500 raw;
- disturbance alpha: 0.10;
- disturbance clamp: +/-100 raw/controller-step;
- default ENABLE_REQUEST = FALSE.

## Stop conditions

Abort immediately and force zero output if any of these occurs during protected
deployment:

- non-zero PLC DAC;
- Enable = TRUE;
- non-zero AppliedDAC;
- AppliedEnable = TRUE;
- unexpected FORTE exit;
- gateway loss;
- unhealthy/tripped watchdog state that cannot be explained by the known
  startup/reset sequence;
- deployment errors involving V3H custom types;
- unexpected resource initialization behavior.

## What this commissioning may authorize

A successful protected zero-output commissioning may authorize preparation of
one bounded active V3H laboratory run.

It does not itself prove regulation, model adequacy, or closed-loop safety.

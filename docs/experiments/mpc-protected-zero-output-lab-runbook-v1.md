# MPC protected zero-output laboratory runbook V1

## Purpose

This is the next physical milestone for the thesis.

It validates the complete PLC ↔ Python gateway ↔ FORTE/4diac MPC path while the
MPC remains disabled and actuator output is independently required to stay at
zero.

This runbook does **not** authorize active MPC control.

## Frozen checkpoints before laboratory return

Repository branch:

`feature/mpc-preparation`

Key checkpoints:

- `offline-nmpc-v1`: offline nonlinear MPC robustness checkpoint;
- `4diac-mpc-v1`: additive 4diac MPC V1 application/types;
- `forte-mpc-v1-runtime`: custom MPC types accepted by the compiled FORTE runtime;
- `345d684`: validated FORTE runtimes and source/build provenance preserved;
- `9b219fa`: reproducible FORTE MPC V1 build workflow;
- `04130e1`: zero-output guard automated safety tests.

## Canonical runtime

Use only:

`forte/preserved-v1/runtimes/mpc-v1/forte.exe`

Expected SHA256:

`DBA3C8280819F648B0F75CF4F748799C7EE1CBEC5E901C2E3788302C09FB28DE`

Required colocated dependency:

`forte/preserved-v1/runtimes/mpc-v1/open62541.dll`

Expected SHA256:

`452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318`

Do not substitute the historical generic `build\src\Debug\forte.exe`.

## Canonical independent guard

Use:

`scripts/mpc_zero_output_deployment_guard.py`

The automated test contract verifies:

- exact B&R `::Program:` NodeIds;
- no OPC UA write operations in the guard;
- independent gateway/PLC command and applied-output checks;
- all individual non-zero/active actuator violation paths;
- offline `--plan` behavior.

## Before touching the plant

With gateway and FORTE stopped:

```powershell
cd C:\Projetos\master-thesis-level-control

powershell.exe `
    -NoProfile `
    -ExecutionPolicy Bypass `
    -File .\scripts\mpc_lab_return_preflight.ps1 `
    -LocalCheck
```

This command does not contact the PLC or gateway.

It must report:

`LOCAL MPC LAB PRE-FLIGHT: PASSED`

## Manual sequence

### 1. Physical readiness

Confirm before creating the control path:

- physical stop is immediately accessible;
- tank and reservoir are visually safe;
- no other person is relying on the plant being idle;
- `MpcController.ENABLE_REQUEST` is still `FALSE`.

If any of these are uncertain, do not continue.

### 2. Start the established gateway manually

Use the already validated project gateway and the same Python environment used
by the project.

Keep its console visible.

### 3. Verify communication

Verify the PLC OPC UA endpoint and local gateway endpoint are reachable.

Do not change process outputs during this check.

### 4. Start the canonical MPC V1 FORTE manually

Run the preserved MPC V1 `forte.exe` from its own directory so the validated
`open62541.dll` remains colocated.

Verify management port `61499` is listening and is owned by that FORTE process.

### 5. Independent 10 s zero-output preflight

Run:

```powershell
python scripts\mpc_zero_output_deployment_guard.py `
    --observe `
    --duration-s 10 `
    --sample-s 0.1
```

During these 10 seconds:

- do not deploy;
- do not trigger `MpcInitMerge.EI1`;
- do not change `ENABLE_REQUEST`;
- do not start monitoring that changes values.

Required result:

`ZERO-OUTPUT DEPLOYMENT VALIDATION: PASSED`

If it fails, stop and diagnose before any deployment.

### 6. Start the protected 90 s observation

Run:

```powershell
python scripts\mpc_zero_output_deployment_guard.py `
    --observe `
    --duration-s 90 `
    --sample-s 0.1
```

Wait for:

`INITIAL ZERO OUTPUT: PASSED`

Only then go to Eclipse 4diac.

### 7. Deploy only the MPC resource

Deploy only:

`FORTE_PC -> ResRealRawMPCV1`

Do not deploy the complete System or the complete device.

The Deployment Console must not report `UNSUPPORTED_TYPE` for:

- `MPC_MEDIAN_FILTER_9`;
- `MPC_MOVE_BLOCKED_NMPC_V1`;
- `SAFE_DAC_RATE_LIMITER`.

### 8. Keep MPC disabled

Confirm:

`MpcController.ENABLE_REQUEST = FALSE`

It must remain false for this entire run.

### 9. Initialize once

With the independent guard still active, trigger:

`MpcInitMerge.EI1`

exactly once.

Do not trigger any other control input.

### 10. Observe

If monitoring is used, observe without editing values.

Useful signals include:

- raw level input;
- median/model level;
- applied DAC;
- watchdog health;
- controller command enable;
- controller command DAC;
- controller trip state/code.

The external independent guard remains the acceptance authority for actuator
zero state.

## PASS criteria

The 90 s protected run passes only if all are true:

- final gateway `Enable = FALSE`;
- final gateway `DAC = 0`;
- final gateway `AppliedEnable = FALSE`;
- final gateway `AppliedDAC = 0`;
- equivalent PLC command/applied states remain zero/false;
- `WatchdogHealthy` is observed true;
- no `ZERO-OUTPUT VIOLATION` occurs;
- no custom MPC `UNSUPPORTED_TYPE` occurs;
- FORTE remains alive;
- initialization can occur without creating actuator output.

Preserve:

- zero-output guard CSV;
- Deployment Console output/screenshot;
- relevant FORTE console output;
- any 4diac monitoring screenshot used for diagnosis.

## FAIL / abort criteria

Stop the experiment immediately if:

- any command or applied actuator state becomes active/non-zero;
- watchdog becomes unhealthy;
- FORTE exits;
- deployment cannot create the required resource/types cleanly;
- any unexpected physical pump action occurs;
- plant state becomes visually unsafe.

Do not try to continue by changing MPC parameters during the failed run.

Return the plant to the established safe zero-output condition before diagnosis.

## End of R5

Even after a PASS:

**do not set `ENABLE_REQUEST = TRUE` in this step.**

R5 ends at validated disabled deployment and initialization.

The first active MPC commissioning must be treated as a separate, explicitly
bounded experiment after the R5 evidence has been reviewed.

REAL MPC AUTHORIZED: **NO**
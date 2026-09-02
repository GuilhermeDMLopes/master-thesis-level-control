# Final Real-Plant Execution Assets

## Purpose

This runbook identifies the exact repository assets that formed the execution stack used to obtain the accepted real-plant MPC V4 and matched PI results. It does not introduce a new controller or a new experiment.

## Versioned Execution Stack

| Role | Versioned asset | Use in the accepted experiments |
|---|---|---|
| PLC/FORTE gateway | `gateway/src/gateway_opcua.py` | OPC UA bridge between the B&R PLC and FORTE |
| 4diac engineering project | `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | Contains the final MPC and matched PI applications and resource mappings |
| Canonical FORTE runtime | `forte/preserved-v4/runtimes/mpc-v4-candidate/forte.exe` | Runtime used for both final controller executions |
| Required runtime DLL | `forte/preserved-v4/runtimes/mpc-v4-candidate/open62541.dll` | Kept adjacent to the canonical runtime |
| Independent zero-output guard | `scripts/mpc_zero_output_deployment_guard.py` | Verified disabled actuation before deployment and after shutdown |
| MPC active-run supervisor | `scripts/mpc_high_range_validation.py` | Enforced the bounded final MPC V4 active window and safe shutdown |
| PI active-run supervisor | `scripts/pi_high_range_validation.py` | Enforced the bounded matched PI active window and safe shutdown |

The canonical `forte.exe` SHA-256 is:

```text
62AB0F00FB1DFE30E89BF89D81249A83AEBBEABE9A7565327BFB3B7FBA536C60
```

## Controller Resources Used

### MPC V4

- application: `MPC_REAL_RAW_SAFE_V4`;
- resource: `FORTE_PC.ResRealRawMPCV4`;
- initialization: trigger `MpcInitMerge.EI1` exactly once after a fresh protected deployment;
- activation: change only `MpcController.ENABLE_REQUEST` to `TRUE` after the supervisor reports `ARMED`.

### Matched PI

- application: `PI_REAL_RAW_HIGH_RANGE_COMPARE`;
- resource: `FORTE_PC.ResRealRawPICompare`;
- initialization: trigger `RawInitMerge.EI1` exactly once after a fresh protected deployment;
- initial mode: keep `RawPI.MANUAL=TRUE` until the supervisor reports `ARMED`;
- activation: change only `RawPI.MANUAL` to `FALSE`.

Deployment and initialization remain deliberate 4diac operator actions. They were not hidden inside an unattended script.

## Safe Offline Demonstration

These commands print the bounded configurations and procedure without starting the gateway, FORTE or plant actuation:

```powershell
.\.venv\Scripts\python.exe .\scripts\mpc_high_range_validation.py --plan
.\.venv\Scripts\python.exe .\scripts\pi_high_range_validation.py --plan
```

## Real-Plant Entrypoints

The gateway entrypoint used by both experiments is:

```powershell
.\.venv\Scripts\python.exe .\gateway\src\gateway_opcua.py
```

The runtime must be started from its preserved directory so `open62541.dll` is resolved from the same location:

```powershell
$runtime = Join-Path `
    (Get-Location).Path `
    "forte\preserved-v4\runtimes\mpc-v4-candidate"

Set-Location $runtime
.\forte.exe
```

The bounded supervisor entrypoints are:

```powershell
.\.venv\Scripts\python.exe `
    .\scripts\mpc_high_range_validation.py `
    --run `
    --forte-pid <FORTE_PID>

.\.venv\Scripts\python.exe `
    .\scripts\pi_high_range_validation.py `
    --run `
    --forte-pid <FORTE_PID>
```

The final accepted retuned PI execution explicitly used:

```powershell
.\.venv\Scripts\python.exe `
    .\scripts\pi_high_range_validation.py `
    --run `
    --forte-pid ([int]$env:M5L_FORTE_PID) `
    --initial-min-raw 50 `
    --initial-max-raw 180 `
    --active-duration-s 180 `
    --arm-timeout-s 60 `
    --sample-s 0.1 `
    --maximum-dac 16000 `
    --maximum-median-raw 19000 `
    --maximum-instant-raw 20000 `
    --maximum-rate-raw-per-s 500 `
    --zero-timeout-s 30 `
    --output-root <SESSION_EVIDENCE_DIRECTORY>
```

Process identifiers and session directories are intentionally environment-specific. The controller logic, engineering application, runtime binary, safety supervisors and accepted evidence are versioned.

## Safety Boundary

`--run` is not a demonstration mode. It can lead to physical pump actuation when the laboratory stack is connected. A real run requires the physical stop to be immediately accessible, PLC interlocks active, initial zero output independently verified, the correct single resource deployed and initialized, and continuous operator observation.

No additional real-plant run is required for the dissertation. Use `--plan`, the preserved evidence and the offline analysis for demonstrations outside the laboratory.

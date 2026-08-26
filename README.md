# Level Control with 4diac, FORTE, OPC UA, and a B&R PLC

## Overview

This repository contains the software, engineering artifacts, automated tests, experimental procedures, and datasets developed for a master's thesis on level control using:

- a real B&R PLC;
- OPC UA communication;
- a Python integration gateway;
- Eclipse 4diac IDE;
- Eclipse 4diac FORTE;
- a validated real-plant PI baseline;
- a Model Predictive Controller implemented in 4diac, with staged real-plant evidence and final online thesis validation still pending.

The research objective is to develop, validate, and compare PI and MPC control strategies on a real level-control process while preserving reproducibility, operational safety, and the complete engineering history of the project.

## Current Project Status

The PLC-gateway-FORTE communication path and the fail-closed raw-count PI baseline have been validated on the real plant. Plant characterization, calibration evidence, delayed model identification, MPC preparation, and staged real-plant MPC actuation evidence are also preserved in `main`.

Validated checkpoints:

| Checkpoint | Git reference | Result |
|---|---|---|
| Initial repository and gateway baseline | `baseline-gateway-v1` | Repository, Python environment, gateway source, and complete 4diac project validated |
| Real FORTE/gateway communication with zero output | `real-forte-zero-output-v1` | PLC-gateway-FORTE communication validated without positive actuator output |
| Real raw-count PI baseline | `real-raw-pi-v1` | Safe real-plant PI test completed, evidence preserved, and automated acceptance criteria passed |
| MPC preparation and real evidence | `7d9a3b5` | M1-M4 evidence integrated into `main`, including the final V3H application and preserved real-plant datasets |
| Canonical evidence hash correction | `ecada4e` | Model evidence manifest normalized to the canonical LF representation |

The complete automated test suite currently contains **472 passing tests**.

The final 4diac application is `MPC_REAL_RAW_SAFE_V3H`, mapped to `FORTE_PC.ResRealRawMPCV3H`. It includes real signal acquisition, median filtering, the delayed MPC controller, actuator limiting, gateway communication, and fail-closed output handling.

The MPC has produced staged real-plant actuation evidence and preserved runtime datasets. The remaining milestone is **M5 - Final 4diac MPC Integration and Thesis Evidence**: offline structural verification followed, in the laboratory, by deployment, online monitoring, synchronized screenshots, final safe-stop evidence, and consolidation of the PI-MPC comparison.

The repository therefore does not yet claim that the final M5 online validation package is complete.

## Current Architecture

```text
B&R PLC
OPC UA Server
    |
    v
Python Gateway
OPC UA Client for the B&R PLC
OPC UA Server for FORTE
    |
    v
4diac FORTE
PI_REAL_RAW_SAFE or MPC_REAL_RAW_SAFE_V3H
    |
    +-- MPC_MEDIAN_FILTER_9
    +-- MPC_MOVE_BLOCKED_NMPC_V3H
    +-- MpcSafeDACLimiter
    +-- DAC and Enable writers
```

Current communication path:

```text
B&R PLC <-> Python Gateway <-> 4diac FORTE
```

The PI application remains the validated experimental baseline and fallback. The V3H application is the final MPC implementation selected for M5 structural and online thesis evidence.

## Why the Python Gateway Is Required

The B&R PLC exposes the process variables through an OPC UA server. However, 4diac FORTE could not reliably use the original NodeIds exposed by the PLC.

The Python gateway is therefore maintained as an explicit integration layer. It:

- connects to the B&R OPC UA server;
- reads process variables, actuator feedback, watchdog state, and safety state;
- exposes simplified OPC UA NodeIds for FORTE;
- receives control commands from FORTE;
- writes permitted commands to the B&R PLC;
- records experimental data;
- supports heartbeat and communication diagnostics;
- participates in the fail-closed command path.

The simplified NodeIds used by the existing 4diac applications remain:

```text
Nivel
Enable
DAC
```

Changing these names requires a coordinated migration of the gateway and the 4diac applications and is not part of the current MPC preparation stage.

## Safety Architecture

The real plant is operated through a fail-closed command path.

A communication failure, stale heartbeat, unhealthy gateway state, controlled shutdown, or related safety trip must result in:

```text
Enable = FALSE
DAC = 0
```

The PLC remains the final authority for the applied actuator state. Test procedures distinguish commanded values from values confirmed and applied by the PLC.

The real-plant workflows include:

1. preflight validation;
2. controlled stack startup;
3. controlled experiment execution;
4. explicit physical-stop confirmation;
5. stack shutdown;
6. final PLC safe-trip verification;
7. evidence preservation;
8. automated test execution.

Do not bypass PLC interlocks, watchdog logic, physical stop procedures, or the documented test workflow.

## Validated Real PI Baseline

The validated real-plant controller is the additive 4diac application documented as `PI_REAL_RAW_SAFE`.

Its current purpose is to provide:

- a safe and reproducible real PI baseline;
- a fallback controller during MPC development;
- reference data for model identification and controller comparison;
- a stable interface for the existing PLC-gateway-FORTE architecture.

The baseline uses raw level counts in the validated control path. Historical applications using other scaling and control structures remain preserved in the 4diac project.

The final baseline experiment produced:

- 427 recorded rows;
- 167 automatic-control rows;
- an automatic DAC range of 648 counts;
- an automatic rolling-median range from 318 to 736 counts;
- a preserved evidence CSV with recorded SHA-256 integrity information;
- a successful final PLC safe-trip check;
- 149 passing automated tests.

Evidence files:

```text
data/sample/real-raw-pi-v1-monitor.csv
docs/experiments/real-raw-pi-baseline-validation.md
docs/4diac/pi-real-raw-safe-application.md
```

The baseline establishes a valid experimental reference. It does not claim that the current PI gains are globally optimal.

## Current 4diac Project

The engineering project is:

```text
OPAS_Tank_System
```

Repository location:

```text
4diac/application/OPAS_Tank_System/
```

The final MPC application selected for M5 is:

```text
Application: MPC_REAL_RAW_SAFE_V3H
Resource: FORTE_PC.ResRealRawMPCV3H
Controller: MPC_MOVE_BLOCKED_NMPC_V3H
Filter: MPC_MEDIAN_FILTER_9
Safety limiter: MpcSafeDACLimiter
```

The application retains fail-closed defaults, including `ENABLE_REQUEST=FALSE`, and uses real level, watchdog, and applied-DAC feedback from the gateway path.

The complete project must remain versioned, including:

- `.project`;
- `OPAS_Tank_System.sys`;
- local function block definitions;
- the complete `Type Library`;
- historical communication applications;
- historical PI/PID applications;
- MPC development artifacts;
- intermediate and experimental applications.

Changes to the 4diac project must be additive and documented. Existing historical applications and function blocks must not be deleted, renamed, or overwritten merely to simplify the final implementation.

Historical MPC artifacts remain preserved, but only `MPC_REAL_RAW_SAFE_V3H` is the selected final application for the remaining structural and online validation work.

## Repository Structure

```text
.
|-- .gitignore
|-- README.md
|-- requirements.txt
|-- requirements-dev.txt
|-- 4diac
|   |-- application
|   |   `-- OPAS_Tank_System
|   `-- function-blocks
|-- data
|   |-- raw
|   `-- sample
|-- docs
|   |-- 4diac
|   |-- architecture
|   |-- current-state
|   |-- experiments
|   `-- testing
|-- forte
|   `-- custom-blocks
|-- gateway
|   |-- config
|   `-- src
|-- results
|-- scripts
|   `-- pi_tuned_test
|-- simulation
`-- tests
```

### `4diac/application`

Contains the complete Eclipse 4diac engineering project. Always copy and version the complete project directory rather than selected `.sys` or `.fbt` files.

### `forte/custom-blocks`

Contains C++ source exported or implemented for custom FORTE builds.

### `gateway`

Contains the Python OPC UA integration gateway.

Current entry point:

```text
gateway/src/gateway_opcua.py
```

### `scripts`

Contains experiment managers, controlled commissioning workflows, identification tools, and auxiliary processing scripts.

Relevant current tools include:

```text
scripts/open_loop_identification.py
scripts/pi_tuned_test/
```

### `data/raw`

Contains raw experimental outputs. These files are ignored by Git by default.

### `data/sample`

Contains selected, non-sensitive, versioned evidence datasets used for validation, documentation, and tests.

### `results`

Contains generated plots, identified models, processed tables, and comparison outputs. Generated content is normally ignored unless explicitly selected as thesis evidence.

## Main Technologies

- Python
- `asyncua`
- OPC UA
- Eclipse 4diac IDE
- Eclipse 4diac FORTE
- IEC 61499
- Structured Text
- B&R PLC
- Git
- GitHub
- `pytest`

## Python Environment

Create a virtual environment from the repository root:

```powershell
python -m venv ".venv"
```

Install runtime and development dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Check the environment:

```powershell
.\.venv\Scripts\python.exe -m pip check
```

## Automated Testing

Run the complete offline test suite from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

When the virtual environment is already active:

```powershell
python -m pytest -q
```

Current validated result:

```text
472 passed
```

The offline tests do not require access to the B&R PLC, FORTE, or the laboratory network.

Testing documentation:

```text
docs/testing/testing-guide.md
```

## Gateway Execution

Run the gateway only in the intended laboratory environment or against an approved test/simulation endpoint:

```powershell
python gateway/src/gateway_opcua.py
```

The gateway may attempt to connect to the configured real B&R endpoint. Verify the active configuration before execution.

Before a real-plant connection, confirm:

- B&R OPC UA endpoint;
- B&R NodeIds;
- gateway OPC UA endpoint;
- OPC UA data types;
- heartbeat and watchdog behavior;
- level signal interpretation;
- DAC limits and sign;
- command and feedback consistency;
- Enable behavior;
- PLC interlocks;
- physical emergency and safe-stop procedures.

## Real-Plant Experiment Evidence

Raw experiment files are written under:

```text
data/raw/
```

Only selected evidence files should be copied to `data/sample/` and committed. Each preserved experiment should include:

- source path;
- experiment date and purpose;
- row count and test phases;
- controller configuration;
- acceptance criteria;
- safety result;
- integrity hash;
- analysis document;
- associated commit or Git tag.

## Development Roadmap

### Completed - Repository and Historical Preservation

- organized the repository;
- preserved the complete `OPAS_Tank_System` project;
- created automated preservation checks;
- validated a clean clone and rebuild workflow;
- established Git references for reproducible checkpoints.

### Completed - Communication and Fail-Closed Integration

- validated PLC-gateway communication;
- validated gateway-FORTE communication;
- integrated heartbeat and watchdog information;
- confirmed zero-output communication before positive actuation;
- implemented and tested fail-closed shutdown behavior.

### Completed - Real PI Baseline

- added the `PI_REAL_RAW_SAFE` application without replacing historical applications;
- added controlled PI commissioning scripts;
- tuned the PI to a conservative real-plant configuration;
- preserved the final experiment dataset;
- documented the acceptance result;
- integrated the checkpoint into `main`.

### Completed - Plant Characterization and Calibration Evidence

- completed the minimum local actuator characterization;
- selected one conservative input-map/model interpretation;
- preserved the physical zero and level-calibration evidence;
- documented the central bottom drain and dynamic calibration limitations;
- froze the evidence required for the final controller stage.

### Completed - Offline MPC Preparation

- identified the delayed Hammerstein candidate;
- preserved the canonical static nonlinearity;
- defined the controller input/output contract;
- implemented delay-aware prediction with applied-DAC history;
- validated controller contracts and safety constraints offline;
- preserved historical MPC variants without replacing them.

### Completed - Staged Real MPC Evidence

- implemented `MPC_REAL_RAW_SAFE_V3H`;
- mapped the application to `FORTE_PC.ResRealRawMPCV3H`;
- preserved staged real-plant runtime and first-actuation evidence;
- retained the validated PI path as the experimental baseline;
- integrated M1-M4 evidence into `main`.

### In Progress - M5 Final 4diac MPC Integration and Thesis Evidence

- verify the final V3H application structure offline;
- verify event, data, initialization, and safety connections;
- document the MPC function block interface and internal behavior;
- prepare a reproducible deployment and monitoring checklist;
- perform the final online validation when laboratory access is available;
- capture synchronized 4diac, CSV, plot, and safe-stop evidence.

### In Progress - Final PI-MPC Comparison

The final experimental presentation will consolidate:

- Integral Absolute Error;
- Integral Squared Error;
- overshoot;
- settling time;
- steady-state error;
- control effort;
- constraint violations;
- computation time;
- communication jitter;
- safety and fallback behavior.

No additional model variants or unrelated controller implementations are planned unless the M5 structural audit identifies a necessary correction.

## Git and Documentation Conventions

Repository documentation, source-code comments, branch names, and commit messages are written in English.

Recommended commit examples:

```text
docs: update validated project status
test: preserve plant identification dataset
feat: add offline prediction model
feat: add constrained MPC prototype
test: validate real MPC baseline
docs: compare PI and MPC experiments
```

Use annotated or lightweight tags only for meaningful validated checkpoints.

## Current Priority

The immediate priority is **M5 - Final 4diac MPC Integration and Thesis Evidence**.

Outside the laboratory, work is limited to the offline structural verification of `MPC_REAL_RAW_SAFE_V3H`, documentation, automated tests, evidence preparation, and the deployment checklist. Positive real-plant actuation must wait for the documented laboratory procedure.

The repository should remain focused on completing the dissertation. Additional model candidates, controller variants, refactoring, or organizational work should be avoided unless required to correct the final V3H application, preserve reproducibility, or support the final PI-MPC evidence package.

# Level Control with 4diac, FORTE, OPC UA, and a B&R PLC

## Overview

This repository contains the software, documentation, and experimental structure developed for a master's thesis on level control using:

- A real B&R PLC;
- OPC UA communication;
- A Python integration gateway;
- Eclipse 4diac IDE;
- Eclipse 4diac FORTE;
- A PI controller;
- A future Model Predictive Controller.

The main objective is to develop, validate, and compare PI and MPC control strategies applied to a real level process.

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
OPC UA Client
PI controller and future MPC
```

## Why the Python Gateway Is Required

The B&R PLC already exposes process variables through an OPC UA server.

However, 4diac FORTE was not able to access the original NodeIds exposed by the B&R OPC UA server. The Python gateway was introduced as an integration layer that translates the original B&R NodeIds into simplified NodeIds that can be used by FORTE.

The gateway currently:

1. Connects to the B&R OPC UA server.
2. Reads process variables and actuator states.
3. Exposes simplified OPC UA NodeIds for FORTE.
4. Receives control commands from FORTE.
5. Writes control commands to the B&R PLC.
6. Records experimental data in CSV files.

The gateway is part of the current system architecture and will remain in use during the PI and MPC development phases.

## Current Communication Path

```text
B&R PLC <-> Python Gateway <-> 4diac FORTE
```

## Current 4diac Project

The current 4diac project is named:

```text
OPAS_Tank_System
```

The complete project must be stored at:

```text
4diac/application/OPAS_Tank_System/
```

The project currently contains:

```text
OPAS_Tank_System/
|-- .project
|-- OPAS_Tank_System.sys
|-- DAC_RATE_LIMITER.fbt
|-- MPC_LEVEL.fbt
|-- PV_FILTER.fbt
`-- Type Library/
```

The `.project` file and the `Type Library` directory are part of the 4diac engineering project and must be committed with the other project files.

The presence of `MPC_LEVEL.fbt` does not mean that the MPC has already been experimentally validated. It is currently treated as a development artifact.

## Current Control Structure

The current 4diac application includes:

- Level acquisition through OPC UA;
- Raw-to-physical level scaling;
- Process variable filtering;
- PI/PID control logic;
- Manipulated-variable scaling;
- DAC rate limiting;
- OPC UA command writing.

The currently documented derivative gain is zero. Therefore, the existing PID configuration behaves as a PI controller.

The complete closed-loop behavior still requires laboratory validation.

## Repository Structure

```text
.
|-- .gitignore
|-- README.md
|-- requirements.txt
|-- 4diac
|   |-- application
|   |   `-- OPAS_Tank_System
|   `-- function-blocks
|-- data
|   |-- raw
|   `-- sample
|-- docs
|   |-- architecture
|   |-- current-state
|   `-- experiments
|-- forte
|   `-- custom-blocks
|-- gateway
|   |-- config
|   `-- src
|-- results
|-- scripts
|-- simulation
`-- tests
```

### `4diac/application`

Contains the complete 4diac engineering project.

Copy the entire directory:

```text
C:\Users\guilh\4diacIDE-workspace\OPAS_Tank_System
```

to:

```text
C:\Projetos\master-thesis-level-control\4diac\application\OPAS_Tank_System
```

Do not copy only the `.sys` file or only the `.fbt` files. Copy the complete project directory, including `.project` and `Type Library`.

### `4diac/function-blocks`

Reserved for standalone IEC 61499 function block definitions when they need to be maintained independently from the complete application project.

The current `.fbt` files are already present inside the `OPAS_Tank_System` project, so duplication is not required during Stage 1.

### `forte/custom-blocks`

Contains C++ code exported from 4diac for inclusion in a custom FORTE build.

### `gateway`

Contains the Python OPC UA integration gateway.

The current entry point is:

```text
gateway/src/gateway_opcua.py
```

### `docs`

Contains architecture descriptions, current-state documentation, and experimental procedures.

### `simulation`

Reserved for offline plant models and controller simulations.

### `scripts`

Reserved for data processing, plotting, and auxiliary scripts.

### `tests`

Reserved for offline and automated tests.

### `data/raw`

Contains raw experimental CSV files. These files are ignored by Git by default.

### `data/sample`

May contain small, non-sensitive CSV examples used for documentation and tests.

### `results`

Contains generated plots, tables, and processed experimental results. Generated files are ignored by Git by default.

## Main Technologies

- Python
- asyncua
- OPC UA
- Eclipse 4diac IDE
- Eclipse 4diac FORTE
- IEC 61499
- Structured Text
- B&R PLC
- Git
- GitHub

## Python Environment

Create a virtual environment from the repository root:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Gateway Execution

Run the gateway from the repository root:

```powershell
python gateway/src/gateway_opcua.py
```

The gateway writes raw experiment CSV files to:

```text
data/raw/
```

Before connecting the gateway to the real plant, verify:

- The B&R OPC UA endpoint;
- The original B&R NodeIds;
- The gateway OPC UA endpoint;
- OPC UA variable data types;
- Level scaling;
- DAC limits;
- Enable behavior;
- PLC safety interlocks.

## Current Gateway Compatibility

The gateway preserves the simplified OPC UA NodeIds already used by the existing 4diac application:

```text
Nivel
Enable
DAC
```

These names remain unchanged even though the Python source code and documentation are written in English.

Changing these NodeIds would require coordinated changes in the 4diac application and is outside Stage 1.

## Safety Notice

The real plant must only be operated after validating:

- OPC UA communication;
- Sensor calibration;
- Actuator scaling;
- Control action direction;
- Minimum and maximum actuator values;
- Enable behavior;
- Command and feedback consistency;
- PLC interlocks;
- Emergency and safe shutdown behavior.

The software must not be connected to the physical plant without a previously defined and approved test procedure.

## Development Roadmap

### Stage 1 â€” Project Organization and Version Control

- Organize the source files.
- Preserve the complete 4diac project.
- Preserve the current gateway baseline.
- Create the local Git repository.
- Create the private GitHub repository.
- Document the initial state.

### Stage 2 â€” Gateway Review

- Separate command variables from feedback variables.
- Improve communication diagnostics.
- Improve error handling.
- Standardize process units.
- Review timing and logging behavior.

### Stage 3 â€” PI Controller Review

- Implement anti-windup.
- Improve manual and automatic modes.
- Add safe initialization.
- Record internal PI variables.
- Validate the complete output chain.

### Stage 4 â€” Offline Simulation

- Create a simplified process simulator.
- Test PI behavior.
- Test saturation.
- Test communication failures.
- Prepare the controller interface for the MPC.

### Stage 5 â€” Experimental PI Validation

- Calibrate the level signal.
- Validate manual actuation.
- Confirm the control direction.
- Tune the PI controller.
- Generate the PI experimental baseline.

### Stage 6 â€” Model Predictive Control

- Identify the plant model.
- Define the prediction model.
- Define constraints and horizons.
- Validate the MPC in simulation.
- Validate the MPC with the real plant.

### Stage 7 â€” PI and MPC Comparison

The controllers will be compared using:

- Integral Absolute Error;
- Integral Squared Error;
- Overshoot;
- Settling time;
- Steady-state error;
- Control effort;
- Constraint violations;
- Computation time;
- Communication jitter.

## Git and Documentation Conventions

All repository documentation, source-code comments, branch names, and commit messages must be written in English.

Recommended commit examples:

```text
chore: initialize project structure
docs: document current communication architecture
refactor: separate gateway configuration from runtime logic
fix: correct level scaling documentation
test: add offline gateway conversion tests
```

## Project Status

**Under development.**

The communication architecture has been implemented, but the complete closed-loop control system still requires experimental validation.


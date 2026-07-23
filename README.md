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

## Testing

The project includes automated offline tests for the gateway processing functions.

Install the development dependencies:

```powershell
python -m venv ".venv"

.\.venv\Scripts\python.exe `
    -m pip install `
    -r requirements-dev.txt
```

Run the complete test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The tests do not require access to the B&R PLC, 4diac FORTE, or the laboratory network.

Detailed instructions are available in:

```text
docs/testing/testing-guide.md
```
## Repository Validation

The repository baseline was validated by cloning it into a separate directory and rebuilding the Python and 4diac development environments.

The validated baseline is identified by the following Git tag:

```text
baseline-gateway-v1
```

### Clone the Repository

Choose a directory outside the original development repository:

```powershell
New-Item `
    -ItemType Directory `
    -Force `
    -Path "C:\Projetos\repository-validation" |
    Out-Null

Set-Location "C:\Projetos\repository-validation"
```

Clone the repository:

```powershell
git clone `
    "https://github.com/GuilhermeDMLopes/master-thesis-level-control.git"
```

Enter the cloned repository:

```powershell
Set-Location `
    "C:\Projetos\repository-validation\master-thesis-level-control"
```

### Validate the Git Repository

Confirm that the working tree is clean:

```powershell
git status
```

Confirm the current commit:

```powershell
git log --oneline -1
```

Confirm the available baseline tag:

```powershell
git tag
```

Confirm the remote repository:

```powershell
git remote -v
```

Count the tracked files:

```powershell
$trackedFileCount = (
    git ls-files |
    Measure-Object
).Count

Write-Host "Tracked files: $trackedFileCount"
```

The initial validated baseline contains:

```text
529 tracked files
```

### Create the Python Validation Environment

Confirm the Python version:

```powershell
python --version
```

The initial baseline was validated with:

```text
Python 3.10.11
```

Create a virtual environment:

```powershell
python -m venv ".venv"
```

Confirm that the virtual environment was created:

```powershell
Test-Path ".venv\Scripts\python.exe"
```

Install the project dependencies:

```powershell
.\.venv\Scripts\python.exe `
    -m pip install `
    -r requirements.txt
```

Confirm the installed `asyncua` version:

```powershell
.\.venv\Scripts\python.exe -c `
    "import importlib.metadata as metadata; print(metadata.version('asyncua'))"
```

Expected version:

```text
1.1.8
```

Confirm that the main OPC UA classes can be imported:

```powershell
.\.venv\Scripts\python.exe -c `
    "from asyncua import Client, Server, ua; print('asyncua import: OK')"
```

Check the installed dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip check
```

Expected result:

```text
No broken requirements found.
```

### Validate the Gateway Source Code

Validate the Python syntax without connecting to the real PLC:

```powershell
.\.venv\Scripts\python.exe `
    -m py_compile `
    "gateway\src\gateway_opcua.py"
```

A successful syntax validation produces no output.

Do not execute the gateway outside the laboratory unless a simulation mode or a test OPC UA server is being used.

The current gateway attempts to connect to the real B&R endpoint:

```text
opc.tcp://10.0.0.3:4840
```

### Import the Project into Eclipse 4diac

Use a temporary workspace to avoid modifying the original development workspace.

In Eclipse 4diac IDE:

1. Select `File -> Switch Workspace -> Other`.
2. Choose a temporary workspace, for example:

```text
C:\Projetos\4diac-workspace-validation
```

3. After 4diac restarts, select `File -> Import`.
4. Select `General -> Existing Projects into Workspace`.
5. Select the following repository directory as the root directory:

```text
<repository-root>\4diac\application
```

6. Confirm that the project `OPAS_Tank_System` is detected.
7. Enable `Copy projects into workspace`.
8. Select `Finish`.

### Validate the Imported 4diac Project

Open:

```text
OPAS_Tank_System.sys
```

Confirm that the system diagram, devices, resources, applications, event connections, and data connections are loaded.

Open the main custom function blocks:

```text
DAC_RATE_LIMITER.fbt
PV_FILTER.fbt
MPC_LEVEL.fbt
Type Library/net_custom/PID_LEVEL.fbt
Type Library/net_custom/CLIENT_1_0.fbt
```

For each function block, verify:

- The interface opens correctly.
- Event inputs and outputs are visible.
- Data inputs and outputs are visible.
- The Execution Control Chart can be opened when applicable.
- Algorithms can be opened.
- No required function block type is missing.

Open the 4diac `Problems` view:

```text
Window -> Show View -> Problems
```

The validation is successful when no error prevents the project or its function blocks from opening.

Warnings should be reviewed, but they do not necessarily indicate that the import failed.

### Confirm That the Clone Remains Clean

After the validation, return to the cloned repository and execute:

```powershell
git status
```

Expected result:

```text
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

The `.venv` directory and Python cache files must remain ignored by Git.

### Validated Baseline Result

The initial repository baseline was successfully validated with the following results:

- Repository cloned successfully.
- Commit `1f38b83` recovered.
- Tag `baseline-gateway-v1` recovered.
- 529 tracked files recovered.
- Python 3.10.11 environment created.
- `asyncua==1.1.8` installed.
- No broken Python requirements found.
- Gateway syntax validation completed.
- `OPAS_Tank_System` imported into a temporary 4diac workspace.
- System and custom function blocks opened correctly.
- No errors were reported in the 4diac `Problems` view.
- The cloned repository remained clean after validation.


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

# Current Project State

## Project Objective

This project is part of a master's thesis focused on the development and experimental evaluation of level control strategies using Eclipse 4diac, Eclipse 4diac FORTE, OPC UA, a Python integration gateway, a real B&R PLC, and a physical level process.

The current control strategy is based on a PI controller. A Model Predictive Controller will be developed after the communication architecture, plant interface, and PI controller have been validated.

## Current Architecture

The current communication architecture is:

```text
B&R PLC
OPC UA Server
    |
    v
Python Gateway
OPC UA Client for the B&R PLC
OPC UA Server for 4diac FORTE
    |
    v
4diac FORTE
OPC UA Client
PI Controller and Future MPC
```

In compact form:

```text
B&R PLC <-> Python Gateway <-> 4diac FORTE
```

## Communication Roles

### B&R PLC

The B&R PLC operates as an OPC UA server.

It provides access to the physical process variables and actuator commands.

### Python Gateway

The Python gateway performs two OPC UA roles:

1. It operates as an OPC UA client for the B&R PLC.
2. It operates as an OPC UA server for 4diac FORTE.

### 4diac FORTE

4diac FORTE operates as an OPC UA client for the Python gateway.

The control algorithms are executed in 4diac FORTE.

## Gateway Justification

The gateway is required because 4diac FORTE was not able to correctly access the original NodeIds exposed by the B&R OPC UA server.

The gateway translates the original B&R NodeIds into simplified NodeIds that can be accessed by FORTE.

The gateway currently performs the following functions:

1. Connects to the B&R OPC UA server.
2. Reads the physical process variables.
3. Exposes simplified OPC UA NodeIds for FORTE.
4. Receives control commands from FORTE.
5. Writes the commands to the B&R PLC.
6. Records experimental data in CSV files.

The gateway is currently considered part of the project architecture. Direct communication between FORTE and the B&R PLC may be investigated later, but it is not required before the PI and MPC development stages.

## Current B&R OPC UA Configuration

The Python gateway connects to the following B&R OPC UA endpoint:

```text
opc.tcp://10.0.0.3:4840
```

The currently documented B&R NodeIds are:

```text
ns=6;s=::Program:Nivel
ns=6;s=::Program:Enable
ns=6;s=::Program:DAC
```

## Current Gateway OPC UA Configuration

The Python gateway exposes an OPC UA server at:

```text
opc.tcp://0.0.0.0:4841
```

The gateway namespace URI is:

```text
urn:br-4diac-gateway
```

The simplified NodeIds currently exposed to 4diac FORTE are:

```text
Nivel
Enable
DAC
```

These NodeId names remain in Portuguese because the existing 4diac application already depends on them.

They will not be renamed during the initial project organization stage because changing them would require coordinated modifications in the Python gateway and the 4diac application.

## Current 4diac Project

The current 4diac project is named:

```text
OPAS_Tank_System
```

The project is stored in the repository at:

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

The `.project` file is required to import the project into another Eclipse 4diac workspace.

The `Type Library` directory is also part of the engineering project and must be preserved.

The presence of the `MPC_LEVEL.fbt` file does not mean that the MPC has already been experimentally validated. It is currently treated as a development artifact.

## Current Controller

The current application contains a PI/PID controller implemented in 4diac.

The currently documented parameters are:

```text
Setpoint: 14.0 cm
KP: 4.0
KI: 0.5
KD: 0.0
Sampling time: 0.1 s
```

Since the derivative gain is zero, the current controller operates as a PI controller.

These values are not considered final tuning parameters.

The controller still requires laboratory validation.

## Current Process Variable Filter

The current process variable filter uses the following discrete equation:

```text
Filtered_PV(k) =
    Alpha * Filtered_PV(k - 1)
    + (1 - Alpha) * Current_PV(k)
```

The currently documented parameter is:

```text
Alpha: 0.95
```

The Python gateway also calculates a filtered level value for CSV analysis.

The gateway filter does not affect the control signal. The control filter is executed in 4diac FORTE.

## Current Level Scaling

The currently documented level conversion is:

```text
Level_cm = Raw_Level / 1000.0
```

Example:

```text
Raw_Level = 14000
Level_cm = 14.0
```

This conversion is provisional and must still be physically validated in the laboratory.

## Current DAC Configuration

The currently documented DAC range is:

```text
Minimum DAC: 0
Maximum DAC: 32000
```

The 4diac application contains a DAC rate limiter.

The currently documented maximum DAC variation is:

```text
Maximum delta per control cycle: 150
```

The physical actuator scaling and the effective safe operating range still require laboratory validation.

## Current Control Chain

The current control chain is:

```text
Level reading
    |
    v
Raw-to-LREAL conversion
    |
    v
Level scaling
    |
    v
Process variable filter
    |
    v
PI controller
    |
    v
Manipulated-variable scaling
    |
    v
DAC rate limiter
    |
    v
LREAL-to-INT conversion
    |
    v
Python gateway
    |
    v
B&R PLC DAC output
```

## Current Validation Status

The following items have already been demonstrated:

- Communication between the B&R PLC and the Python gateway.
- Communication between the Python gateway and 4diac FORTE.
- Reading the level signal from the B&R PLC.
- Exposure of simplified OPC UA NodeIds to FORTE.
- Writing experimental information to CSV files.
- Loading the current application in Eclipse 4diac.
- Use of custom function blocks in the 4diac project.

The following items still require laboratory validation:

- Physical level calibration.
- Control action direction.
- Enable command behavior.
- DAC command transmission.
- DAC command confirmation.
- PI controller output behavior.
- Complete closed-loop operation.
- Closed-loop stability.
- Final PI tuning.
- Communication timing.
- Communication jitter.
- Safe behavior after communication failure.

## Current Known Issues

A previous experimental record indicated that the DAC command remained at zero even though the calculated level error was positive.

The current CSV structure does not contain all internal controller variables.

Therefore, it is not yet possible to determine whether the zero command originated:

1. Inside the PI controller.
2. During manipulated-variable scaling.
3. Inside the DAC rate limiter.
4. During data type conversion.
5. During the OPC UA write operation.
6. Inside the PLC logic.

The current Enable logic also depends on the PI output. This behavior will be reviewed in a later development stage.

No controller tuning conclusions should be obtained from that experiment until the complete actuation chain has been validated.

## Current Repository Structure

The current repository root is:

```text
C:\Projetos\master-thesis-level-control
```

The planned repository structure is:

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

## Current Development Priority

The current priority is to preserve, document, and version the existing implementation before modifying the gateway or controller.

The current stage does not include controller tuning or MPC development.

## Next Technical Objective

After project organization and version control are completed, the next technical objective will be to review the Python gateway.

The future gateway review will focus on:

- Separating command variables from feedback variables.
- Improving error handling.
- Improving communication diagnostics.
- Standardizing process units.
- Reviewing CSV logging.
- Reviewing timing behavior.

## Planned Development Sequence

1. Organize and version the existing project.
2. Review and improve the Python gateway.
3. Review and improve the PI controller.
4. Create an offline plant simulator.
5. Validate the complete communication and actuation chain.
6. Validate and tune the PI controller with the real plant.
7. Identify the real plant model.
8. Develop and validate the MPC in simulation.
9. Validate the MPC with the real plant.
10. Compare PI and MPC performance.

## Documentation and Git Conventions

All repository documentation must be written in English.

Source-code comments should be written in English.

Branch names and commit messages should also be written in English.

Examples:

```text
chore: initialize project structure
docs: document current system architecture
refactor: separate gateway commands and feedback
fix: correct level scaling documentation
test: add offline gateway tests
```

## Project Status

**Under development.**

The basic communication architecture has been implemented.

The complete closed-loop control system still requires experimental validation.

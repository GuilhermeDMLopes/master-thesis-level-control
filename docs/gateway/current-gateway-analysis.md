# Current Gateway Analysis

## Document Purpose

This document describes the current structure and behavior of the Python OPC UA gateway before its refactoring.

The purpose of this analysis is to preserve the existing behavior, identify responsibilities that are currently combined in one file, and define the order of future structural improvements.

No communication behavior is changed by this document.

## Analyzed Source File

The current gateway implementation is located at:

```text
gateway/src/gateway_opcua.py
```

## Current System Role

The Python gateway operates as an integration layer between the B&R PLC and 4diac FORTE.

Its current communication roles are:

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
```

The gateway is required because 4diac FORTE was not able to access the original NodeIds exposed by the B&R OPC UA server.

## Current B&R Connection

The gateway connects to the B&R OPC UA server at:

```text
opc.tcp://10.0.0.3:4840
```

The current B&R NodeIds are:

```text
ns=6;s=::Program:Nivel
ns=6;s=::Program:Enable
ns=6;s=::Program:DAC
```

The current data flow is:

```text
B&R Nivel  -> Gateway -> FORTE
FORTE Enable -> Gateway -> B&R Enable
FORTE DAC    -> Gateway -> B&R DAC
```

## Current Gateway Server

The gateway provides its own OPC UA server at:

```text
opc.tcp://0.0.0.0:4841
```

The current namespace URI is:

```text
urn:br-4diac-gateway
```

The simplified NodeIds exposed to FORTE are:

```text
Nivel
Enable
DAC
```

These NodeIds are preserved because the existing 4diac application already depends on them.

They must not be renamed during the initial structural refactoring.

## Current File Responsibilities

The current `gateway_opcua.py` file performs all of the following responsibilities:

1. Defines project paths.
2. Defines OPC UA endpoints.
3. Defines the original B&R NodeIds.
4. Defines the gateway namespace.
5. Defines experiment parameters.
6. Defines level scaling.
7. Defines DAC scaling metadata.
8. Defines PI parameter metadata.
9. Defines filter parameter metadata.
10. Defines DAC limiter metadata.
11. Converts raw level values to centimeters.
12. Converts DAC values to percentages.
13. Calculates a filtered level for offline analysis.
14. Creates and writes the CSV file.
15. Creates the B&R OPC UA client.
16. Creates the OPC UA server used by FORTE.
17. Creates the simplified gateway variables.
18. Reads the physical level.
19. Receives Enable and DAC commands from FORTE.
20. Writes Enable and DAC commands to the B&R PLC.
21. Reads feedback values from the B&R PLC.
22. Writes diagnostic messages to the terminal.
23. Handles program shutdown.

This concentration of responsibilities makes the file functional but difficult to test and modify safely.

## Current Project Paths

The project root is calculated from the location of the gateway source file.

The CSV output directory is:

```text
data/raw/
```

The current CSV filename is defined directly in the Python source code.

## Current Experiment Parameters

The gateway currently contains copies of parameters that are also configured in the 4diac application.

The documented values are:

```text
Level scale: 1000.0
Setpoint: 14.0 cm
KP: 4.0
KI: 0.5
KD: 0.0
Sampling time: 0.1 s
PV filter alpha: 0.95
DAC limiter maximum delta: 150
DAC minimum: 0
DAC maximum: 32000
```

These values are currently used mainly as CSV metadata and for gateway-side analysis.

The real controller continues to execute in 4diac FORTE.

## Current Auxiliary Functions

### `write_value_only`

Writes only the OPC UA Value attribute.

This implementation is used because some industrial OPC UA servers may reject writes containing additional status or timestamp information.

### `dac_to_percent`

Converts the DAC range into a percentage.

Current conversion:

```text
0     -> 0 %
32000 -> 100 %
```

The function limits values to the configured DAC range before performing the conversion.

### `raw_level_to_cm`

Converts the raw level value into centimeters.

Current documented conversion:

```text
Level_cm = Raw_Level / 1000.0
```

This conversion is provisional and still requires physical validation in the laboratory.

### `clamp_alpha`

Limits the filter coefficient to:

```text
0.0 <= alpha <= 1.0
```

### `update_filtered_value`

Calculates a filtered level value for CSV analysis.

This filter does not affect the controller executed in 4diac FORTE.

### `open_csv_logger`

Creates the experiment CSV file and writes its header.

The CSV delimiter is:

```text
;
```

The file is encoded as UTF-8.

## Current Startup Sequence

The current startup sequence is:

1. Configure Python logging.
2. Create the B&R OPC UA client.
3. Connect to the B&R OPC UA server.
4. Obtain references to the level, Enable, and DAC nodes.
5. Read the initial values from the PLC.
6. Create the gateway OPC UA server.
7. Register the gateway namespace.
8. Create the `BR_Gateway` object.
9. Create the `Nivel`, `Enable`, and `DAC` variables.
10. Mark `Enable` and `DAC` as writable.
11. Create the CSV file.
12. Start the gateway server.
13. Enter the continuous communication loop.

## Current Communication Cycle

During each gateway cycle, the code performs the following actions:

1. Reads the level from the B&R PLC.
2. Publishes the raw level through the gateway OPC UA server.
3. Reads the Enable command exposed to FORTE.
4. Reads the DAC command exposed to FORTE.
5. Compares each command with the last command stored by the gateway.
6. Writes changed commands to the B&R PLC.
7. Periodically reads confirmation values from the B&R PLC.
8. Calculates level and actuator analysis values.
9. Writes one row to the CSV file.
10. Flushes the CSV file.
11. Waits for the configured cycle period.

The configured gateway cycle period is:

```text
0.1 s
```

The configured CSV period is also:

```text
0.1 s
```

## Current Command Handling

The current gateway stores:

```text
last_enable_command
last_dac_command
```

A command is written to the B&R PLC only when the value exposed by the gateway differs from the last value stored by the gateway.

This reduces repeated OPC UA writes.

However, the stored values represent the last commands handled by the gateway. They do not represent an independent command acknowledgement mechanism.

Command and feedback variables are not yet separated in the gateway OPC UA interface.

This behavior must be reviewed in a later stage.

## Current Feedback Handling

The gateway reads the actual B&R values during CSV logging:

```text
confirmed_raw_level
confirmed_enable
confirmed_dac
```

These values are written to the CSV file.

However, the current gateway OPC UA server does not expose separate feedback NodeIds to FORTE.

The current interface therefore uses:

```text
Enable
DAC
```

as the command variables, while B&R feedback is used mainly for logging.

## Current CSV Content

The current CSV contains:

- Timestamp.
- Elapsed time.
- Raw level.
- Level in centimeters.
- Gateway-filtered level.
- Setpoint.
- Raw and filtered errors.
- Gateway DAC command.
- B&R DAC feedback.
- Gateway manipulated variable percentage.
- B&R manipulated variable percentage.
- Gateway Enable command.
- B&R Enable feedback.
- PI parameter metadata.
- Filter parameter metadata.
- DAC limiter metadata.
- Level scaling metadata.
- Experiment notes.

The CSV is flushed after each row.

This protects recently collected data if the program stops unexpectedly, but it may add execution overhead.

## Current Error Handling

The gateway has two error-handling levels.

### Cycle-level handling

Exceptions inside the continuous loop are logged, and the loop continues after the configured sleep interval.

### Application-level handling

Fatal startup or execution errors are logged.

During shutdown, the code attempts to:

1. Close the CSV file.
2. Disconnect from the B&R OPC UA server.

## Current Strengths

The current gateway already provides:

- Working B&R OPC UA client integration.
- A simplified OPC UA server for FORTE.
- Stable NodeIds used by the existing 4diac project.
- Explicit OPC UA data types.
- Raw and physical unit logging.
- Command and B&R feedback logging.
- A monotonic clock for elapsed experiment time.
- CSV storage inside the repository data structure.
- Controlled cleanup of the CSV file and OPC UA connection.
- Python type annotations in several functions.
- English source-code comments and log messages.

## Current Structural Limitations

The following limitations have been identified.

### 1. Hard-coded configuration

Endpoints, NodeIds, scaling, controller metadata, timing, DAC limits, and the CSV filename are defined directly in the source file.

Changing an experiment configuration therefore requires editing executable source code.

### 2. Multiple responsibilities in one file

Configuration, conversion functions, OPC UA communication, CSV logging, and the runtime loop are all combined in one module.

### 3. Duplicated controller metadata

PI, filter, and limiter values are configured in 4diac and copied into the Python source code for logging.

The two configurations may become inconsistent.

### 4. Command and feedback are not separate interface variables

FORTE writes `Enable` and `DAC`, while B&R feedback is read separately only for logging.

The interface does not currently provide explicit variables such as:

```text
EnableCommand
EnableFeedback
DACCommand
DACFeedback
```

### 5. No explicit reconnection state machine

The gateway logs cycle errors, but there is no explicit connection-state or reconnection sequence inside the current implementation.

### 6. No offline simulation mode

The gateway always attempts to connect to the real B&R OPC UA endpoint when executed.

### 7. No automated tests

Conversion and filtering functions can be tested offline, but no automated tests currently exist.

### 8. Silent conversion fallback

Invalid level or DAC values are converted to zero by the auxiliary functions.

This prevents some exceptions but may hide invalid process data.

### 9. Cycle timing includes execution time

The loop waits for the configured sleep period after completing its work.

Therefore, the real cycle interval is approximately:

```text
execution time + configured sleep time
```

### 10. Repeated PLC reads during logging

The level is read during the main cycle and may be read again during the logging section.

This provides confirmation data but increases communication work.

### 11. Immediate CSV flushing

Flushing after every row improves data preservation but may affect cycle timing.

### 12. No explicit gateway diagnostics exposed to FORTE

The current OPC UA interface does not expose variables such as:

```text
BRConnected
GatewayReady
LastError
CycleTime
CommandAge
```

## Refactoring Constraints

The initial structural refactoring must preserve:

- The B&R endpoint behavior.
- The original B&R NodeIds.
- The gateway endpoint.
- The namespace URI.
- The simplified NodeIds `Nivel`, `Enable`, and `DAC`.
- The current OPC UA data types.
- The current CSV information.
- The ability to run the existing 4diac application without modification.

Behavioral changes must not be mixed with the initial file reorganization.

## Planned Refactoring Order

The gateway should be improved in the following order:

1. Document the current structure.
2. Separate configuration definitions from runtime code.
3. Move pure conversion functions into a dedicated module.
4. Create automated offline tests.
5. Preserve and validate the existing gateway behavior.
6. Separate command variables from feedback variables.
7. Add connection-state diagnostics.
8. Add explicit reconnection behavior.
9. Improve cycle-time measurement.
10. Add an offline simulation mode.

## Scope of the Next Step

The next step will separate configuration values from the gateway runtime code.

The next step must not yet:

- Rename OPC UA NodeIds.
- Change B&R communication.
- Change DAC behavior.
- Change Enable behavior.
- Change the CSV columns.
- Change the controller.
- Change the 4diac project.

## Analysis Status

**Completed.**

This document represents the gateway structure before refactoring.

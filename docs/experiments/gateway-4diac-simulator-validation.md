# Gateway and 4diac Simulator Validation

## Validation Date

July 24, 2026.

## Objective

The objective of this validation was to verify the complete OPC UA communication path without requiring access to the real B&R PLC or the physical level plant.

The validated architecture was:

```text
B&R PLC simulator
        |
        | OPC UA, port 4842
        v
Python OPC UA gateway
        |
        | OPC UA, port 4841
        v
Eclipse 4diac FORTE
        |
        v
GATEWAY_COMM_TEST application
```

The validation covered process variable reading, command writing, and command feedback.

## Test Environment

The validation used:

- Python 3.10.11;
- `asyncua==1.1.8`;
- Eclipse 4diac IDE;
- Eclipse 4diac FORTE with OPC UA support;
- the `feature/plc-simulator` Git branch;
- the local B&R PLC simulator;
- the Python OPC UA gateway;
- the `GATEWAY_COMM_TEST` 4diac application.

The real PLC and physical plant were not used.

## Network Endpoints

| Component | Endpoint |
|---|---|
| B&R PLC simulator | `opc.tcp://127.0.0.1:4842` |
| Python gateway server | `opc.tcp://127.0.0.1:4841` |
| FORTE management interface | `localhost:61499` |

All three TCP ports were verified as available during the test.

## Simulated B&R PLC Interface

The simulator reproduced the original B&R PLC NodeIds:

| Variable | NodeId | OPC UA type |
|---|---|---|
| Level | `ns=6;s=::Program:Nivel` | `Double` |
| Enable | `ns=6;s=::Program:Enable` | `Boolean` |
| DAC | `ns=6;s=::Program:DAC` | `Int16` |

The Python gateway connected to these NodeIds as an OPC UA client.

## Gateway Interface for FORTE

The gateway exposed simplified NodeIds for FORTE:

| Variable | NodeId | Direction |
|---|---|---|
| Level | `ns=2;s=Nivel` | Gateway to FORTE |
| Enable command | `ns=2;s=Enable` | FORTE to gateway |
| DAC command | `ns=2;s=DAC` | FORTE to gateway |
| Enable feedback | `ns=2;s=EnableFeedback` | Gateway to FORTE |
| DAC feedback | `ns=2;s=DACFeedback` | Gateway to FORTE |

The namespace index assigned during this validation was `2`.

## 4diac Diagnostic Application

An additive application named `GATEWAY_COMM_TEST` was created.

No historical application, function block, mapping, or communication configuration was removed.

### OPC UA read blocks

- `CommTestNivelRead`;
- `CommTestEnableFeedbackRead`;
- `CommTestDACFeedbackRead`.

### OPC UA write blocks

- `CommTestEnableWrite`;
- `CommTestDACWrite`.

### Typed read blocks

- `CommTestNivelType`, using `LREAL2LREAL`;
- `CommTestEnableFeedbackType`, using `BOOL2BOOL`;
- `CommTestDACFeedbackType`, using `INT2INT`.

### Typed command blocks

- `CommTestEnableCommand`, using `BOOL2BOOL`;
- `CommTestDACCommand`, using `INT2INT`.

### Initialization blocks

- resource-native `CommTestStart`, using `E_RESTART`;
- `CommTestInitMerge`, using `E_MERGE`;
- `CommTestInitSplit1`;
- `CommTestInitSplit2`;
- `CommTestInitSplit3`;
- `CommTestInitSplit4`.

The application blocks were mapped to:

```text
FORTE_PC.Res0
```

## OPC UA Configuration Strings

The read blocks used:

```text
opc_ua[SUBSCRIBE;opc.tcp://127.0.0.1:4841#;,2:s=Nivel]
opc_ua[SUBSCRIBE;opc.tcp://127.0.0.1:4841#;,2:s=EnableFeedback]
opc_ua[SUBSCRIBE;opc.tcp://127.0.0.1:4841#;,2:s=DACFeedback]
```

The write blocks used:

```text
opc_ua[WRITE;opc.tcp://127.0.0.1:4841#;,2:s=Enable]
opc_ua[WRITE;opc.tcp://127.0.0.1:4841#;,2:s=DAC]
```

## Type Resolution

### Read ports

The OPC UA `SUBSCRIBE_1` blocks expose `RD_1` as a generic `ANY` port.

The following typed connections were added:

```text
CommTestNivelRead.RD_1
-> CommTestNivelType.IN

CommTestEnableFeedbackRead.RD_1
-> CommTestEnableFeedbackType.IN

CommTestDACFeedbackRead.RD_1
-> CommTestDACFeedbackType.IN
```

The corresponding indication events were connected to the typed blocks:

```text
CommTestNivelRead.IND
-> CommTestNivelType.REQ

CommTestEnableFeedbackRead.IND
-> CommTestEnableFeedbackType.REQ

CommTestDACFeedbackRead.IND
-> CommTestDACFeedbackType.REQ
```

### Write ports

The OPC UA `CLIENT_1_0` blocks expose `SD_1` as a generic `ANY` port.

FORTE initially reported invalid `SD_1` connections. The following typed connections were added:

```text
CommTestEnableCommand.OUT
-> CommTestEnableWrite.SD_1

CommTestDACCommand.OUT
-> CommTestDACWrite.SD_1
```

This resolved the write types as:

```text
Enable command -> BOOL
DAC command    -> INT
```

## Initialization

The OPC UA blocks were initialized using an event distribution chain:

```text
CommTestStart
-> CommTestInitMerge
-> CommTestInitSplit1
-> CommTestInitSplit2
-> CommTestInitSplit3
-> CommTestInitSplit4
```

Because the FORTE boot file was not available, initialization was also triggered manually after deployment using:

```text
CommTestInitMerge.EI1
```

After initialization, the read and write blocks reported valid communication status.

## Read Validation Results

### Level

The level subscription was successfully established.

Observed values included:

```text
10000
12000
14000
```

The values followed the deterministic profile generated by the PLC simulator.

Result: **Passed**

### Enable feedback

The Enable feedback subscription returned:

```text
TRUE
FALSE
```

Result: **Passed**

### DAC feedback

The DAC feedback subscription returned:

```text
2500
0
```

Result: **Passed**

## Write Validation Results

### Enable command

The following command sequence was tested:

```text
FALSE -> TRUE -> FALSE
```

For each write:

- the command reached `CommTestEnableWrite.SD_1`;
- the `REQ` event was triggered manually;
- the `CNF` counter incremented;
- `QO` was `TRUE`;
- `STATUS` was `OK`;
- `EnableFeedback` confirmed the value.

Result: **Passed**

### DAC command

The following command sequence was tested:

```text
0 -> 2500 -> 0
```

For each write:

- the command reached `CommTestDACWrite.SD_1`;
- the `REQ` event was triggered manually;
- the `CNF` counter incremented;
- `QO` was `TRUE`;
- `STATUS` was `OK`;
- `DACFeedback` confirmed the value.

Result: **Passed**

## Acceptance Criteria

| Criterion | Result |
|---|---|
| Simulator available on port 4842 | Passed |
| Gateway available on port 4841 | Passed |
| FORTE available on port 61499 | Passed |
| Level read through FORTE | Passed |
| Enable feedback read through FORTE | Passed |
| DAC feedback read through FORTE | Passed |
| Enable write through FORTE | Passed |
| DAC write through FORTE | Passed |
| Enable restored to `FALSE` | Passed |
| DAC restored to `0` | Passed |
| Historical 4diac artifacts preserved | Passed |

## Validated Communication Paths

```text
Simulator level
-> Python gateway
-> FORTE subscription
-> typed 4diac output
```

```text
4diac Enable command
-> FORTE OPC UA write
-> Python gateway
-> PLC simulator
-> gateway feedback
-> FORTE subscription
-> typed 4diac output
```

```text
4diac DAC command
-> FORTE OPC UA write
-> Python gateway
-> PLC simulator
-> gateway feedback
-> FORTE subscription
-> typed 4diac output
```

## Known Limitations

This validation does not include:

- the real B&R PLC;
- the physical tank;
- real sensor calibration;
- real DAC calibration;
- PI control;
- MPC control;
- physical safety interlocks;
- automatic gateway reconnection;
- dynamic tank behavior based on the DAC command.

The current PLC simulator uses a deterministic level profile and does not yet represent the physical process dynamics.

## Conclusion

The complete OPC UA communication path between the B&R PLC simulator, the Python gateway, Eclipse 4diac FORTE, and the `GATEWAY_COMM_TEST` application was successfully validated.

The communication architecture is ready for the gateway robustness work and the later offline validation of the PI controller.

# Gateway Dynamic Level Plant Validation

## Validation Date

July 25, 2026.

## Objective

Validate the dynamic offline level plant through both the simulated B&R OPC UA interface and the Python gateway, without using the physical B&R PLC or the physical tank.

## Validated Architecture

```text
Dynamic level plant
        |
        v
B&R PLC OPC UA simulator
opc.tcp://127.0.0.1:4842
        |
        v
Python OPC UA gateway
opc.tcp://127.0.0.1:4841
        |
        v
Temporary OPC UA validation client
```

## Software Components

- `simulation/level_plant.py`
- `simulation/br_plc_simulator.py`
- `gateway/src/gateway_opcua.py`
- `gateway/src/gateway_connection.py`
- `gateway/src/gateway_interface.py`
- `gateway/src/gateway_processing.py`

## OPC UA Compatibility

The dynamic simulator preserved the previously validated B&R-compatible interface:

```text
Endpoint: opc.tcp://127.0.0.1:4842
Namespace index: 6

ns=6;s=::Program:Nivel
ns=6;s=::Program:Enable
ns=6;s=::Program:DAC
```

The gateway preserved its client-facing interface:

```text
Endpoint: opc.tcp://127.0.0.1:4841
Namespace URI: urn:br-4diac-gateway

Nivel
Enable
DAC
EnableFeedback
DACFeedback
```

## Automated Test Results

The implementation passed:

```text
9 simulator mode tests
25 combined plant and simulator tests
91 total repository tests
```

The deterministic simulator mode remained available, and the dynamic mode was selected explicitly with:

```powershell
python simulation/br_plc_simulator.py --mode dynamic
```

## Direct Simulator Validation

The first functional test accessed the dynamic B&R simulator directly through OPC UA.

Initial command state:

```text
Enable = FALSE
DAC = 0
```

Observed values:

```text
Level before fill: 6.583 cm
Level after fill: 10.218 cm
Level after drain: 9.107 cm
```

Test sequence:

1. Set `Enable = FALSE` and `DAC = 0`.
2. Read the initial level.
3. Set `Enable = TRUE` and `DAC = 32000`.
4. Wait five seconds and verify that the level increased.
5. Set `Enable = FALSE`.
6. Wait five seconds and verify that the level decreased.
7. Restore the original command values.

Result:

```text
Dynamic OPC UA smoke test: PASSED
```

## Gateway Validation

The second functional test accessed the same dynamic plant through the Python gateway.

Both communication ports were available:

```text
127.0.0.1:4842 — simulator
127.0.0.1:4841 — gateway
```

Initial gateway command state:

```text
Enable = FALSE
DAC = 0
```

Observed values:

```text
Level before fill: 1.730 cm
Level after fill: 5.888 cm
Level after drain: 5.324 cm
```

Command and feedback behavior:

```text
Enable command during fill: TRUE
DAC command during fill: 32000
Enable feedback during fill: TRUE
DAC feedback during fill: 32000

Enable command during drain: FALSE
Enable feedback during drain: FALSE
DAC feedback during drain: 32000
```

Keeping the DAC value at `32000` while setting `Enable = FALSE` was intentional. The dynamic model correctly removed the pump inflow while preserving the DAC command value.

Result:

```text
Gateway dynamic plant smoke test: PASSED
```

The original gateway command values were restored after the test.

## Dynamic Behavior Confirmed

The tests confirmed that:

- the level decreases naturally when the pump is disabled;
- `Enable = FALSE` prevents pump inflow regardless of the DAC value;
- `Enable = TRUE` with a positive DAC command produces inflow;
- a full-scale DAC command produces a measurable level increase;
- the level remains bounded by the configured physical limits;
- raw level values remain compatible with `level_raw = level_cm * 1000`;
- the gateway transfers commands to the simulated B&R PLC;
- gateway feedback matches the simulated PLC values;
- the deterministic simulator mode remains preserved.

## Known Limitations

The current dynamic plant parameters are provisional and are not identified from the physical plant.

This validation does not include:

- the physical B&R PLC;
- the physical tank;
- sensor calibration;
- actuator calibration;
- verified DAC direction on the real plant;
- safety interlocks;
- closed-loop PI behavior through 4diac;
- MPC behavior;
- experimentally identified process parameters.

The `asyncua` startup log may contain messages about missing parent nodes while loading parts of the standard OPC UA address space. These messages did not prevent either OPC UA server from starting and did not affect the validated nodes or functional tests.

## Conclusion

The dynamic offline level plant was successfully integrated into the B&R PLC OPC UA simulator and validated through the Python gateway.

The complete validated path was:

```text
LevelPlant
→ B&R PLC simulator
→ Python gateway
→ OPC UA validation client
```

The implementation is ready for the next stage: integration of `PI_LEVEL_CONTROLLER` into an isolated 4diac offline closed loop using the dynamic simulated plant.

# Read-Only Real-Plant Observation

## Purpose

This workflow records the current B&R PLC level signal while the actuator command and PLC-applied output remain zero.

It is intended to support physical-limit review and sensor-noise observation before open-loop identification.

## Safety properties

The observer:

- connects only to the B&R PLC;
- does not connect to the Python gateway;
- does not require FORTE;
- contains no OPC UA write operation;
- requires `Enable=FALSE`, `DAC=0`, `AppliedEnable=FALSE`, and `AppliedDAC=0`;
- aborts if any command or applied output becomes non-zero;
- checks the final PLC state before declaring success.

The tool cannot stop an active actuator because it is intentionally read-only. Existing plant safety mechanisms and the physical stop remain mandatory.

## Modes

Offline plan:

```powershell
python scripts/observe_real_plant_read_only.py --plan
```

The plan performs no network access.

Real read-only observation template:

```powershell
python scripts/observe_real_plant_read_only.py `
    --observe `
    --label <APPROVED_LABEL> `
    --duration-s <APPROVED_DURATION>
```

Execution requires typing:

```text
OBSERVATION_READY
```

## Suggested observations

Only perform a label when the physical condition is actually true and recorded in the laboratory notes.

Examples:

```text
empty-tank
known-physical-level
initial-band
pump-off-noise
```

Do not label a tank as empty, full, or at a known height based only on the raw sensor value.

## Output

The observer stores a CSV under:

```text
data/raw/plant-observation-<label>-<timestamp>/
```

It reports:

- sample count;
- raw-level minimum and maximum;
- median and mean;
- peak-to-peak variation;
- final zero-output confirmation.

The resulting measurements remain raw evidence. Calibration and physical-limit approval require the corresponding physical observation and source documentation.

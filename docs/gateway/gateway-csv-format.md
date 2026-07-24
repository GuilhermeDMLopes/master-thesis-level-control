# Gateway CSV Format

## Purpose

The Python OPC UA gateway records valid PLC samples and experiment metadata in a semicolon-delimited CSV file.

The current output file is:

```text
data/raw/real_pi_test_cm_alpha095_dac_delta150.csv
```

Raw experiment CSV files are ignored by Git. Small representative datasets may be stored separately under `data/sample`.

## General Format

- Encoding: UTF-8
- Delimiter: semicolon (`;`)
- Header language: English
- Timestamp format: ISO 8601 with millisecond precision
- Numeric decimal separator: period (`.`)
- One row is written only after a valid PLC read
- No row is written while the PLC connection is unavailable
- Calculated floating-point values are written with at most six decimal places

## Columns

| Column | Description | Unit or type |
|---|---|---|
| `timestamp` | Local timestamp when the CSV row was created | ISO 8601 string |
| `elapsed_time_s` | Time elapsed since gateway startup | s |
| `level_raw` | Raw level value confirmed by the PLC | raw units |
| `level_cm` | Level converted by `level_raw / level_scale` | cm |
| `level_filtered_gateway_cm` | Gateway-side filtered level used only for offline analysis | cm |
| `setpoint_raw_equivalent` | Raw-unit equivalent of the configured setpoint | raw units |
| `setpoint_cm` | Configured PI setpoint metadata | cm |
| `error_cm` | `setpoint_cm - level_cm` | cm |
| `filtered_error_gateway_cm` | `setpoint_cm - level_filtered_gateway_cm` | cm |
| `dac_gateway_command` | DAC command currently exposed by the gateway | integer |
| `dac_br_feedback` | DAC value read back from the PLC | integer |
| `mv_gateway_percent` | Gateway DAC command converted to percent | % |
| `mv_br_percent` | PLC-confirmed DAC value converted to percent | % |
| `enable_gateway_command` | Enable command currently exposed by the gateway | Boolean |
| `enable_br_feedback` | Enable value read back from the PLC | Boolean |
| `kp` | Proportional gain metadata for the 4diac controller | dimensionless |
| `ki` | Integral gain metadata for the 4diac controller | controller-dependent |
| `kd` | Derivative gain metadata for the 4diac controller | controller-dependent |
| `sampling_time_s` | Controller sampling time metadata | s |
| `manual_mode` | Manual-mode metadata | Boolean |
| `manual_output` | Manual controller output metadata | controller output units |
| `reset` | Controller reset metadata | Boolean |
| `pv_filter_alpha` | Process-variable filter coefficient metadata | dimensionless |
| `pv_filter_reset` | Process-variable filter reset metadata | Boolean |
| `dac_limiter_max_delta` | Maximum allowed DAC command change per limiter execution | DAC units |
| `dac_limiter_min` | Minimum DAC limiter output | DAC units |
| `dac_limiter_max` | Maximum DAC limiter output | DAC units |
| `dac_limiter_reset` | DAC rate-limiter reset metadata | Boolean |
| `level_scale` | Raw-to-centimeter conversion scale | raw units per cm |
| `notes` | Experiment and implementation notes | string |
| `communication_state` | Communication state associated with the valid sample | enum string |
| `reconnection_count` | Number of successful PLC reconnections since gateway startup | non-negative integer |

## Communication State Values

The `communication_state` column uses English uppercase values.

### `CONNECTED`

The row was recorded during the initial PLC connection or during normal operation after a previously marked reconnection sample.

### `RECONNECTED`

The row is the first valid sample written after PLC communication was restored.

The gateway does not write `DISCONNECTED` rows because no valid PLC sample exists while the PLC connection is unavailable.

## Reconnection Counter

The `reconnection_count` column:

- starts at `0`;
- increments after every successful reconnection;
- remains at the latest value for subsequent rows;
- is not reset until the gateway process restarts.

Example:

```text
communication_state;reconnection_count
CONNECTED;0
CONNECTED;0
RECONNECTED;1
CONNECTED;1
CONNECTED;1
```

## Command and Feedback Semantics

Command and feedback columns must not be interpreted as equivalent signals.

```text
dac_gateway_command
enable_gateway_command
```

represent the values exposed by the gateway command nodes.

```text
dac_br_feedback
enable_br_feedback
```

represent values read back and confirmed from the PLC.

After reconnection, offline commands are discarded and the gateway command nodes are synchronized with the values confirmed by the PLC.

## Data Validity

Every CSV row represents a valid PLC-side sample because the gateway writes rows only after successful communication.

During a PLC disconnection:

- the gateway OPC UA server remains available;
- the gateway does not write CSV rows;
- previous feedback values may remain exposed to OPC UA clients;
- commands written while offline are not automatically forwarded after reconnection.

## Current Validation Result

The CSV format was validated with the local B&R PLC simulator.

Observed results:

```text
CSV rows: 227
CSV columns: 32
CONNECTED rows: 226
RECONNECTED rows: 1
Maximum reconnection count: 1
Values with more than 6 decimal places: 0
Empty values: 0
Automated tests: 47 passed
```

The tested reconnection sample recorded:

```text
communication_state = RECONNECTED
reconnection_count = 1
```

## Compatibility Notes

The existing 30 columns were preserved. The following columns were appended:

```text
communication_state
reconnection_count
```

This additive change avoids breaking scripts that depend on the previous column order.

The legacy OPC UA NodeId `Nivel` is intentionally preserved for compatibility with the B&R PLC and existing 4diac applications. New code, documentation, and CSV fields use English names.

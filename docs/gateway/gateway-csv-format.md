# Gateway CSV Format

## Purpose

The Python OPC UA gateway records valid PLC samples, gateway command
diagnostics, and PLC watchdog diagnostics in a semicolon-delimited CSV file.

The current output file remains:

```text
data/raw/real_pi_test_cm_alpha095_dac_delta150.csv
```

## General Format

- Encoding: UTF-8
- Delimiter: semicolon (`;`)
- Header language: English
- Timestamp: ISO 8601 with millisecond precision
- Decimal separator: period (`.`)
- A row is written only after a valid PLC read
- No row is written while PLC communication is unavailable
- Floating-point values use at most six decimal places

## Column Groups

### Process and provisional control metadata

The original columns are preserved:

```text
timestamp
elapsed_time_s
level_raw
level_cm
level_filtered_gateway_cm
setpoint_raw_equivalent
setpoint_cm
error_cm
filtered_error_gateway_cm
```

`level_cm` and derived error columns still use the provisional
`level_raw / level_scale` conversion. They are not yet a validated physical
centimeter measurement.

### Commands and PLC command feedback

```text
dac_gateway_command
dac_br_feedback
mv_gateway_percent
mv_br_percent
enable_gateway_command
enable_br_feedback
```

- `dac_gateway_command` and `enable_gateway_command` are FORTE requests.
- `dac_br_feedback` and `enable_br_feedback` are the PLC command variables,
  not the post-watchdog physical outputs.

### Controller and limiter metadata

```text
kp
ki
kd
sampling_time_s
manual_mode
manual_output
reset
pv_filter_alpha
pv_filter_reset
dac_limiter_max_delta
dac_limiter_min
dac_limiter_max
dac_limiter_reset
level_scale
notes
```

### Communication and final DAC boundary limiter

```text
communication_state
reconnection_count
dac_gateway_applied
mv_gateway_applied_percent
dac_boundary_limited
dac_boundary_max_delta
```

`dac_gateway_applied` is the last DAC command successfully selected and
written by the Python boundary limiter. It is not equivalent to `AppliedDAC`.

### PLC watchdog diagnostics

Seven columns are appended:

| Column | Meaning | Type |
|---|---|---|
| `heartbeat_gateway_value` | Latest UDINT heartbeat value written by the gateway | integer |
| `safety_reset_br_feedback` | PLC `SafetyReset` value read in the sampled state | Boolean |
| `watchdog_healthy` | PLC watchdog healthy state | Boolean |
| `watchdog_tripped` | PLC watchdog trip latch | Boolean |
| `applied_enable` | Enable value after the PLC watchdog gate | Boolean |
| `applied_dac` | DAC value after the PLC watchdog gate | integer |
| `watchdog_commands_permitted` | Gateway decision that commands may be forwarded | Boolean |

The complete format contains 43 columns.

## Watchdog Interpretation

During normal enabled operation:

```text
watchdog_healthy = True
watchdog_tripped = False
applied_enable = True
applied_dac = requested bounded output
watchdog_commands_permitted = True
```

After heartbeat loss:

```text
watchdog_healthy = False
watchdog_tripped = True
applied_enable = False
applied_dac = 0
watchdog_commands_permitted = False
```

The PLC command variables may temporarily retain nonzero values after a trip.
`AppliedEnable` and `AppliedDAC` are the authoritative physical-output gate
diagnostics.

## Communication State Values

### `CONNECTED`

Normal valid PLC sample.

### `RECONNECTED`

First valid sample after a successful reconnection and watchdog handshake.

The gateway writes no `DISCONNECTED` CSV row because no valid PLC sample
exists while communication is unavailable.

## Reconnection Rules

After communication returns:

- offline commands are discarded;
- gateway command nodes are reset to `Enable=False` and `DAC=0`;
- Heartbeat is re-established;
- `SafetyReset` is pulsed only in the safe zero-command state;
- logging resumes only after the watchdog becomes healthy.

## Compatibility

The original 36 columns remain in their existing order. The seven watchdog
columns are appended, preserving index compatibility for earlier analysis
scripts that read the original prefix.

# Offline PI Closed-Loop Analysis with Safe DAC Limiting

## Data Source

- Run ID: `20260727-144356`
- Duration requested from the OPC UA monitor: `300 s`
- Closed-loop duration measured from the first positive applied DAC: `315.635 s`
- Gateway rows analyzed: `2211`
- OPC UA monitor samples: `300`

## Controller Configuration

| Parameter | Value |
|---|---:|
| Setpoint | `14.0 cm` |
| Proportional gain | `4.0` |
| Integral gain | `0.50` |
| Sampling time | `0.1 s` |
| FORTE DAC maximum delta | `150` |
| Gateway DAC maximum delta | `150` |

## Closed-Loop Metrics

| Metric | Value |
|---|---:|
| Initial level at control start | `0.042671 cm` |
| Peak level | `18.953819 cm` |
| Peak time | `50.609 s` |
| Absolute overshoot | `4.953819 cm` |
| Overshoot relative to setpoint | `35.384%` |
| 10-90% rise time | `20.181 s` |
| Settling time, +/-5% | `118.914 s` |
| Settling time, +/-2% | `129.157 s` |
| Final 30 s mean level | `13.999270 cm` |
| Final 30 s level standard deviation | `0.002278 cm` |
| Final 30 s mean signed error | `0.000730 cm` |
| IAE | `475.666235 cm.s` |
| ISE | `3605.620505 cm2.s` |

## DAC Boundary Validation

| Metric | Value |
|---|---:|
| Maximum requested DAC | `31988` |
| Maximum applied DAC | `31986` |
| Maximum requested-applied gap | `300` |
| Boundary-limited CSV rows | `153` |
| Actual DAC writes | `1427` |
| Maximum actual write delta | `150` |
| Actual write-rate violations | `0` |
| Logged-delta mismatches | `0` |
| Limited-flag mismatches | `0` |

## Communication Integrity

- Enable command-feedback mismatches: `0`
- Maximum reconnection count: `0`
- Rows in the `RECONNECTED` state: `0`
- Maximum sampled applied-feedback error: `0`

## Assessment

The complete offline closed loop passed the 300-second functional validation.

The response is stable and converges to the 14 cm setpoint with negligible steady-state error.

The response is underdamped. The observed overshoot was `35.384%` relative to the setpoint.

This overshoot must be considered during laboratory commissioning, but it must not be used alone to retune the real plant because the offline plant model is provisional.

The requested DAC approached full scale because the simulated tank started almost empty. No requested or applied sample reached the configured saturation value of 32000.

All actual gateway writes respected the maximum absolute change of 150 DAC units. No communication interruption, reconnection, feedback mismatch, or limiter diagnostic inconsistency was detected.

The measured closed-loop duration exceeds 300 seconds because the controller was already active before the independent OPC UA monitor began recording.

## Generated Artifacts

- [Metrics CSV](../../results/pi-offline-safe-dac-300s/metrics.csv)
- [Level response](../../results/pi-offline-safe-dac-300s/level-response.png)
- [Control effort](../../results/pi-offline-safe-dac-300s/control-effort.png)
- [Control error](../../results/pi-offline-safe-dac-300s/control-error.png)
- [DAC boundary activity](../../results/pi-offline-safe-dac-300s/dac-boundary-gap.png)
- [Source evidence archive](../../data/sample/pi-offline-safe-dac-300s-20260727-144356.zip)

## Conclusion

`PI_OFFLINE_SAFE_DAC_CLOSED_LOOP` is approved as the offline baseline for controlled laboratory commissioning.

This approval demonstrates software integration and functional safety behavior in the provisional simulator. It does not replace physical calibration, actuator-direction verification, interlock verification, or conservative commissioning with the real plant.

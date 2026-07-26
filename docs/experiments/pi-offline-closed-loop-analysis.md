# Offline PI Closed-Loop Analysis

## Data Source

- Archive: `pi_offline_closed_loop_20260726_183810.zip`
- CSV: `pi_offline_closed_loop_20260726_183810.csv`
- Rows: 2993
- Closed-loop start detected at the first nonzero DAC or enabled command: `12.157 s`

## Source Integrity

- Source archive SHA-256: `4F757AA730DBAC5F809B9CC2877C658AE125CC59CAF5A19A1396AC186746E4AD`

## Main Results

| Metric | Value |
|---|---:|
| Initial level at control start | 6.956185 cm |
| Setpoint | 14.000 cm |
| 10–90% rise time | 22.609 s |
| First setpoint crossing | 30.890 s |
| Peak level | 15.602199 cm at 50.203 s |
| Overshoot relative to setpoint | 11.444% |
| Overshoot relative to step amplitude | 22.746% |
| Settling time, ±5% | 71.125 s |
| Settling time, ±2% | 114.312 s |
| Settling time, ±1% | 124.453 s |
| Final 60 s mean level | 14.000052 cm |
| Final 60 s mean absolute error | 0.00005212 cm |
| Final 60 s mean DAC | 11200.0 |
| Final 60 s mean MV | 35.000% |
| IAE | 176.782449 cm·s |
| ISE | 612.322613 cm²·s |
| ITAE | 5655.164978 cm·s² |

## Communication Integrity

- Communication states: `{'CONNECTED': 2993}`
- Maximum reconnection count: `0`
- DAC command-feedback mismatches: `0`
- Enable command-feedback mismatches: `0`

## Control Effort

- Maximum DAC: `17945` at `21.203 s` after control start.
- First observed DAC transition: `0 -> 9084`.
- Final operating point: approximately `35.000%` or `11200.0` DAC.

## Sampling

- Configured controller sampling time: `0.1 s`.
- Median gateway CSV interval: `0.125 s`.
- Mean gateway CSV interval: `0.143 s`.
- The CSV cadence is the gateway logging cadence and must not be treated as the exact FORTE execution period.

## Assessment

The closed loop is stable and strongly convergent. The response is underdamped: it crosses the setpoint, reaches a first peak, and then exhibits decaying oscillations.
The final operating point matches the provisional plant equilibrium: approximately 14 cm, 35% controller output, and 11200 DAC.
The initial DAC jump confirms that the current historical `DAC_RATE_LIMITER` initializes its state from the first input rather than ramping from zero. This does not invalidate the offline test, but it should be corrected in an additive safe limiter before physical-plant deployment.

## Repository Artifacts

- [Metrics CSV](../../results/pi-offline-closed-loop/metrics.csv)
- [Level response](../../results/pi-offline-closed-loop/level-response.png)
- [Control effort](../../results/pi-offline-closed-loop/control-effort.png)
- [Control error](../../results/pi-offline-closed-loop/error.png)
- [Source data archive](../../data/sample/pi-offline-closed-loop-20260726.zip)

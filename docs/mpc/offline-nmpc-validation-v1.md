# Offline Nonlinear MPC Validation

## Controller

Move-blocked nonlinear receding-horizon MPC with:

- setpoint: 450.0 raw
- DAC range: 0..12000
- maximum DAC move: 150 per 0.100 s
- prediction horizon: 20.0 s
- predicted hard raw limit: 750.0
- adaptive input-bias estimate for offset-free behavior

## Scenario Results

| Scenario | Pass | Final raw | Max raw | Final DAC | Tail MAE | Settling s | Bias estimate DAC |
|---|---:|---:|---:|---:|---:|---:|---:|
| nominal | YES | 446.45 | 446.45 | 11840.7 | 4.93 | 20.3 | 0.00 |
| tau_fast_25pct | YES | 447.55 | 447.55 | 11840.7 | 3.82 | 18.0 | 0.70 |
| tau_slow_35pct | YES | 447.78 | 447.78 | 11840.7 | 2.82 | 21.5 | -0.44 |
| gain_high_20pct | YES | 460.53 | 460.82 | 11790.7 | 10.46 | 18.4 | 13.61 |
| gain_low_20pct | YES | 441.62 | 448.05 | 11840.7 | 8.25 | 21.7 | -17.60 |
| deadzone_minus_75 | YES | 444.84 | 450.08 | 11750.0 | 5.16 | 16.3 | 74.98 |
| deadzone_plus_75 | YES | 449.15 | 449.42 | 11890.7 | 0.77 | 27.0 | -74.98 |
| aggressive_combined | YES | 442.48 | 442.48 | 11750.0 | 7.94 | 13.6 | 87.52 |
| sluggish_combined | YES | 454.08 | 454.08 | 11940.7 | 2.25 | 28.8 | -95.91 |
| nominal_with_noise | YES | 463.79 | 463.79 | 11890.7 | 9.26 | 21.9 | -40.72 |

## Decision

Passed scenarios: 10/10.

This is an offline controller-validation result only. Real MPC commissioning remains unauthorized until the controller implementation, safety fallback, and preserved-data tests are completed.

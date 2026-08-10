# Dead-zone Hammerstein Model Identification

## Purpose

Trajectory-level nonlinear identification using preserved laboratory data. This model explicitly represents the experimentally observed pump dead-zone/nonlinearity.

## Selected model

- tau: 32.000000 s
- sensor/raw baseline y0: 298.000 raw
- pump dead-zone: 11750.000 DAC
- input exponent p: 1.200000
- equilibrium gain G: 0.680487474306

```text
y_eq(u)=y0+G*max(0,u-u_dead)^p
```

## Validation

- training rollout RMSE: 117.439 raw
- validation rollout RMSE: 55.745 raw
- validation rollout MAE: 49.003 raw
- validation bias: 18.176 raw
- validation maximum absolute error: 136.848 raw

## Target implication

- target: 450.000 raw
- implied equilibrium DAC: 11840.681677122655

## Decision

This file identifies a candidate model only. Real MPC remains unauthorized until offline robustness and constraint tests pass.

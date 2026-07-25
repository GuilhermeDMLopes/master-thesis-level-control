# Offline Level Plant Model

## Purpose

This document defines the first dynamic level-plant model used for offline control validation.

The model is deliberately simple. Its parameters are provisional and are not identified from the physical tank.

## State and Units

The internal state is:

```text
level_cm
```

The B&R-compatible raw value is:

```text
level_raw = level_cm * 1000.0
```

This preserves the level conversion currently used by the gateway and 4diac application.

## Input Contract

The plant receives:

```text
Enable : Boolean
DAC    : integer command
```

The provisional DAC range is:

```text
0 to 32000
```

The command is clamped before it is used.

When `Enable = FALSE`, pump inflow is zero regardless of the DAC value.

## Dynamic Equation

One explicit Euler step is:

```text
level[k + 1] = clamp(
    level[k]
    + sampling_time_s
      * (inflow[k] - outflow[k]),
    minimum_level_cm,
    maximum_level_cm
)
```

The normalized actuator command is:

```text
normalized_dac =
    (clamped_dac - dac_min)
    / (dac_max - dac_min)
```

Pump inflow is:

```text
inflow =
    maximum_inflow_cm_per_s
    * normalized_dac
```

Natural outflow is represented by a first-order term:

```text
outflow =
    drain_coefficient_per_s
    * (level_cm - minimum_level_cm)
```

## Initial Provisional Parameters

| Parameter | Value |
|---|---:|
| Sampling time | `0.1 s` |
| Initial level | `10.0 cm` |
| Minimum level | `0.0 cm` |
| Maximum level | `30.0 cm` |
| Level scale | `1000 raw/cm` |
| DAC minimum | `0` |
| DAC maximum | `32000` |
| Maximum inflow | `1.0 cm/s` |
| Drain coefficient | `0.025 1/s` |

At `10 cm`, the natural outflow is provisionally:

```text
0.025 * 10 = 0.25 cm/s
```

A `50%` DAC command produces:

```text
1.0 * 0.5 = 0.5 cm/s
```

The resulting initial net flow is:

```text
0.5 - 0.25 = 0.25 cm/s
```

## Scope

This model is intended to validate:

- basic filling and draining behavior;
- physical level limits;
- Enable behavior;
- DAC command scaling;
- PI controller integration;
- OPC UA gateway integration;
- communication-loss scenarios.

It does not yet model:

- measured pump curves;
- nonlinear valve or pump behavior;
- transport delay;
- sensor noise;
- dead time;
- overflow dynamics;
- actuator hysteresis;
- the real tank geometry.

These effects must be added only when supported by experimental data.

## Preservation Requirement

The existing deterministic simulator profile remains the validated communication baseline. Dynamic behavior will be added as a separate selectable mode after this isolated plant model passes its tests.

## OPC UA Simulator Integration

The B&R-compatible OPC UA simulator supports two explicit modes:

```text
deterministic
dynamic
```

The deterministic mode remains the default so the previously validated communication baseline is preserved.

Run the original deterministic profile:

```powershell
.\.venv\Scripts\python.exe `
    "simulation\br_plc_simulator.py"
```

Run the provisional dynamic plant:

```powershell
.\.venv\Scripts\python.exe `
    "simulation\br_plc_simulator.py" `
    --mode dynamic
```

The mode can also be selected through the environment:

```powershell
$env:BR_SIMULATION_MODE = "dynamic"

.\.venv\Scripts\python.exe `
    "simulation\br_plc_simulator.py"
```

In dynamic mode, the simulator reads the B&R-compatible `Enable` and `DAC` variables every cycle and publishes:

```text
Nivel = level_cm * 1000.0
```

The OPC UA endpoint, namespace index, and legacy NodeIds remain unchanged.

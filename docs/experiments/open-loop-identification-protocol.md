# Open-Loop Plant Identification Protocol

## Status

This protocol is under development and has not yet produced a validated real-plant model.

The current script performs a single open-loop DAC step. It is a controlled data-collection tool, not a complete identification or MPC implementation.

## Purpose

The procedure is intended to collect real-plant data for estimating a low-order dynamic model of the level process while preserving the validated PLC–gateway fail-closed architecture.

The resulting dataset may support estimation of:

- effective process gain;
- dominant time constant;
- apparent delay;
- useful operating region;
- actuator threshold and saturation behavior;
- sensor noise and experiment repeatability.

## Safety Boundary

The procedure must not be executed merely to inspect its command-line interface.

The command-line modes are explicit:

```text
--plan
--execute
```

`--plan` performs no OPC UA connection and no actuator write.

`--execute` is the only mode allowed to connect to the real PLC and gateway. It additionally requires:

- an explicit maximum raw-level trip threshold;
- an interactive `IDENTIFICATION_READY` confirmation;
- the existing PLC watchdog and fail-closed path;
- a stable initial state with `Enable=FALSE` and applied DAC equal to zero.

The procedure writes `Enable=FALSE` and `DAC=0` in its final cleanup block. The PLC remains the final authority for the applied output.

## Offline Inspection

Display help:

```powershell
python scripts/open_loop_identification.py --help
```

Print the resolved default plan without network access:

```powershell
python scripts/open_loop_identification.py --plan
```

Inspect a proposed configuration without network access:

```powershell
python scripts/open_loop_identification.py `
    --plan `
    --target-dac 12000 `
    --maximum-level-raw <APPROVED_RAW_LIMIT> `
    --baseline-s 8 `
    --hold-s 20 `
    --recovery-s 10 `
    --sample-s 0.1
```

## Real Execution Template

Do not execute this template until the DAC target and maximum level have been reviewed against the physical plant, the validated PI evidence, and the approved laboratory operating limits.

```powershell
python scripts/open_loop_identification.py `
    --execute `
    --target-dac <APPROVED_DAC_TARGET> `
    --maximum-level-raw <APPROVED_RAW_LIMIT>
```

Execution still requires typing:

```text
IDENTIFICATION_READY
```

## Recorded Data

Each CSV row includes:

- timestamp and elapsed time;
- experiment phase;
- raw level;
- configured DAC target;
- configured maximum raw level;
- PLC heartbeat;
- watchdog health and trip states;
- safety reset;
- PLC command values;
- PLC-applied values;
- gateway request values.

Raw outputs are stored below:

```text
data/raw/open-loop-identification-<timestamp>/
```

## Current Sequence

The current sequence is:

1. verify a stable safe initial state;
2. record a zero-output baseline;
3. request `Enable=TRUE` with DAC zero;
4. request the configured DAC target;
5. wait for the applied DAC to reach the target;
6. hold the target for the configured duration;
7. request `Enable=FALSE`;
8. confirm applied output removal;
9. request DAC zero;
10. record recovery;
11. issue final safe commands.

The sequence aborts when the watchdog becomes invalid or the measured raw level reaches the configured maximum threshold.

## Limitations

A single step is generally insufficient to characterize all relevant plant behavior.

Before final model identification, the workflow should be extended or repeated to cover:

- more than one safe DAC amplitude;
- more than one initial level;
- repeat runs under comparable conditions;
- filling and natural draining behavior;
- an independent validation dataset;
- detected transport delay;
- the effective pump-flow threshold;
- nonlinear behavior across the operating range.

The provisional offline model in `simulation/level_plant.py` must not be treated as the real identified model. Its parameters remain placeholders until replaced or supplemented by experimentally estimated values.

The historical `MPC_LEVEL.fbt` must remain preserved. A new validated MPC path will be added only after the real model and the offline MPC behavior have been established.

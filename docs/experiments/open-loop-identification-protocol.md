# Open-Loop Plant Identification Protocol

## Status

This protocol is under development and has not yet produced a validated real-plant model.

The validated PI baseline has been screened offline. It observed a raw-level range from 136 to 787 counts and an applied-DAC range from 0 to 12000 counts. These are observations from one PI commissioning run, not approved physical limits and not an identified model.

## Purpose

The procedure collects real-plant data for estimating low-order dynamic models while preserving the validated PLC–gateway fail-closed architecture.

The intended identification outputs include:

- effective process gain in defined operating regions;
- dominant time constant;
- apparent transport or communication delay;
- pump-flow threshold;
- actuator saturation behavior;
- sensor noise;
- run-to-run repeatability.

## Safety Boundary

The command-line modes are explicit:

```text
--plan
--execute
```

`--plan` performs no OPC UA connection and no actuator write.

`--execute` is the only mode permitted to connect to the real PLC and gateway. It requires all of the following:

- at least one explicitly supplied `--dac-step DAC:HOLD_S`;
- an explicitly supplied initial raw-level band;
- an explicitly supplied maximum raw-level trip threshold;
- the existing PLC watchdog and fail-closed path;
- a stable initial state with `Enable=FALSE` and applied DAC equal to zero;
- the interactive `IDENTIFICATION_READY` confirmation.

No excitation DAC value is supplied by default. The previous unreviewed default of 12000 counts has been removed from the workflow.

The PLC remains the final authority for the applied output. The procedure writes `Enable=FALSE` and `DAC=0` in its final cleanup block.

## Offline Inspection

Display help:

```powershell
python scripts/open_loop_identification.py --help
```

Display an empty plan without network access:

```powershell
python scripts/open_loop_identification.py --plan
```

Display a proposed plan using only values that have already been reviewed for the physical plant:

```powershell
python scripts/open_loop_identification.py `
    --plan `
    --initial-level-min-raw <APPROVED_INITIAL_MIN> `
    --initial-level-max-raw <APPROVED_INITIAL_MAX> `
    --maximum-level-raw <APPROVED_TRIP_LIMIT> `
    --dac-step <APPROVED_DAC_1>:<HOLD_SECONDS_1> `
    --dac-step <APPROVED_DAC_2>:<HOLD_SECONDS_2> `
    --dac-step <APPROVED_DAC_3>:<HOLD_SECONDS_3>
```

The `--dac-step` option may be repeated. The order supplied on the command line is the order executed.

## Real Execution Template

Do not execute until the initial-level band, every DAC step, every hold duration, and the maximum raw-level trip threshold have been approved against the real plant and laboratory procedure.

```powershell
python scripts/open_loop_identification.py `
    --execute `
    --initial-level-min-raw <APPROVED_INITIAL_MIN> `
    --initial-level-max-raw <APPROVED_INITIAL_MAX> `
    --maximum-level-raw <APPROVED_TRIP_LIMIT> `
    --dac-step <APPROVED_DAC_1>:<HOLD_SECONDS_1> `
    --dac-step <APPROVED_DAC_2>:<HOLD_SECONDS_2>
```

Execution additionally requires typing:

```text
IDENTIFICATION_READY
```

## Recorded Data

Each CSV row includes:

- timestamp and elapsed time;
- phase;
- excitation-step index;
- excitation DAC and hold duration;
- raw level;
- approved initial-level bounds;
- maximum raw-level trip threshold;
- PLC heartbeat;
- watchdog health and trip state;
- SafetyReset state;
- PLC command values;
- PLC-applied values;
- gateway request values.

Raw outputs are stored below:

```text
data/raw/open-loop-identification-<timestamp>/
```

## Multi-Step Sequence

The current sequence is:

1. verify a stable safe initial state inside the approved raw-level band;
2. record a zero-output baseline;
3. request `Enable=TRUE` with DAC zero;
4. apply each explicitly supplied DAC step in order;
5. confirm the PLC-applied DAC for every step;
6. record each plateau for its explicitly supplied hold duration;
7. abort if the watchdog becomes invalid;
8. abort if raw level reaches the maximum trip threshold;
9. request `Enable=FALSE`;
10. confirm applied output removal;
11. request DAC zero;
12. record zero-output recovery;
13. issue final safe commands.

## Current Evidence and Limitations

The PI screening report is stored in:

```text
docs/experiments/real-raw-pi-identification-screening.md
docs/experiments/real-raw-pi-identification-screening.json
```

The PI dataset is useful for observed-range and safety screening. It is not an open-loop identification dataset because the actuator and process output were coupled by manual staging and PI feedback.

The maximum observed level of 787 counts is not a physical limit. The maximum observed applied DAC of 12000 counts is not an automatically approved excitation value.

Before real execution, the project still requires:

- explicit physical level limits;
- an approved initial-level band;
- reviewed DAC plateaus and hold times;
- at least one repeated run;
- a separate model-validation dataset;
- post-run evidence preservation and safe-trip validation.

The provisional parameters in `simulation/level_plant.py` must not be treated as identified real-plant parameters.

The historical `MPC_LEVEL.fbt` remains preserved. A new MPC path will be added only after model identification and offline validation.

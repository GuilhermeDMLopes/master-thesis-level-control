# Open-Loop Plant Identification Protocol

## Status

The identification workflow is prepared but no real open-loop model has been collected or approved.

The validated PI baseline observed a raw-level range from 136 to 787 counts and an applied-DAC range from 0 to 12000 counts. These observations are not physical limits and do not authorize a new experiment.

## Explicit execution boundary

The script has two modes:

```text
--plan
--execute
```

`--plan` performs no OPC UA connection and no actuator write.

`--execute` requires all of the following explicit inputs:

- one or more `--dac-step DAC:HOLD_S` values;
- approved initial raw-level minimum;
- approved initial raw-level maximum;
- approved maximum raw-level abort threshold;
- approved maximum positive raw-level rate;
- approved maximum total experiment duration;
- interactive `IDENTIFICATION_READY` confirmation.

No excitation DAC, level trip, rate trip, or duration limit is supplied by default.

## Independent abort layers

A real execution aborts when any of these conditions occurs:

1. the PLC watchdog becomes unhealthy or tripped;
2. `SafetyReset` becomes active;
3. the measured raw level reaches the configured maximum;
4. the positive raw-level rate exceeds the configured threshold;
5. elapsed time reaches the configured maximum duration;
6. the requested applied DAC is not reached within the transition timeout;
7. the initial safe state and level band do not stabilize.

The positive level-rate guard uses a configurable time window and records the calculated rate in the CSV.

## Final safe-state verification

After success or failure, the script requests:

```text
Enable = FALSE
DAC = 0
```

It then reads the PLC and requires five consecutive samples with:

```text
AppliedEnable = FALSE
AppliedDAC = 0
```

Failure to verify that final zero-output state causes the procedure itself to fail.

The PLC remains the final authority for the actuator state.

## Offline plan template

Only use values that have documented engineering and laboratory approval:

```powershell
python scripts/open_loop_identification.py `
    --plan `
    --initial-level-min-raw <APPROVED_INITIAL_MIN> `
    --initial-level-max-raw <APPROVED_INITIAL_MAX> `
    --maximum-level-raw <APPROVED_LEVEL_TRIP> `
    --maximum-level-rate-raw-per-s <APPROVED_RATE_TRIP> `
    --maximum-experiment-duration-s <APPROVED_TOTAL_DURATION> `
    --dac-step <APPROVED_DAC_1>:<HOLD_1> `
    --dac-step <APPROVED_DAC_2>:<HOLD_2>
```

The configured maximum duration must exceed the nominal baseline, hold, and recovery time. Transition and startup time must also be considered during approval.

## Recorded data

Each row includes:

- timestamp and elapsed time;
- phase and step information;
- raw level;
- calculated raw-level rate;
- configured level, rate, and duration abort values;
- heartbeat and watchdog states;
- command values;
- PLC-applied values;
- gateway-request values.

Raw results are stored under:

```text
data/raw/open-loop-identification-<timestamp>/
```

## Current approval status

The following remain unresolved for real execution:

- physical tank high-level limit;
- PLC high-level trip, if present;
- physically approved abort level;
- approved positive level-rate threshold;
- minimum repeatable pump-flow DAC;
- approved DAC sequence;
- approved hold durations;
- approved total duration.

The provisional values previously displayed in an offline plan remain unapproved. In particular, 700 raw counts is not a physical limit and 9000, 10500, and 12000 are not an authorized identification sequence merely because they were displayed by `--plan`.

The historical `MPC_LEVEL.fbt` and all existing 4diac applications remain preserved.

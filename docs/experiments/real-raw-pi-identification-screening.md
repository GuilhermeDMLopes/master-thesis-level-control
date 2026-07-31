# Real Raw-Count PI Identification Screening

## Status

This is an offline screening of the validated PI baseline. It does not identify the real plant and does not approve a real open-loop test automatically.

## Source and integrity

```text
Source: data/sample/real-raw-pi-v1-monitor.csv
SHA256: 197D0F0113564EACC40D16325CF1760008C595CE815300DA8BE5841CAB060E07
Rows: 427
Recorded duration: 180.391 s
```

## Scope

The baseline is useful for confirming observed operating ranges, recorded phases, command/application consistency, sampling behavior, and safety-state preservation.

It is not a valid standalone open-loop identification dataset. The actuator command was produced by manual staging and closed-loop PI behavior, so the measured input and output are coupled.

## Sampling

```text
Median: 0.172 s
P05: 0.171 s
P95: 0.203 s
Minimum: 0.015 s
Maximum: 104.469 s
```

## Observed level range

```text
Raw level minimum: 136.000
Raw level maximum: 787.000
Raw level median: 411.000

Rolling-median minimum: 217.000
Rolling-median maximum: 736.000
Rolling-median median: 411.000

Maximum raw observation: 787.000
Maximum observation time: 43.265 s
Maximum observation phase: AUTO_ACTIVE
```

The maximum observed value is evidence from this run, not a physical or approved safety limit.

## Observed actuator range

```text
Applied DAC minimum: 0.000
Applied DAC maximum: 12000.000
Applied DAC median: 11187.000
Command/applied mismatch rows: 69
Maximum command/applied mismatch: 2686
Enable/applied-enable mismatch rows: 0
```

```text
Minimum positive applied DAC: 150
Maximum positive applied DAC: 12000
Median positive applied DAC: 11556.000
```

## Automatic phase

```text
Rows: 167
Duration: 29.890 s
Rolling-median level minimum: 318.000
Rolling-median level maximum: 736.000
Applied DAC minimum: 11082.000
Applied DAC maximum: 11730.000
Applied DAC range: 648
```

## Rolling-median level-rate screening

```text
P05: -164.894 raw-count/s
Median: 0.000 raw-count/s
P95: 120.640 raw-count/s
Minimum: -2000.000 raw-count/s
Maximum: 540.698 raw-count/s
```

These rates are descriptive. They must not be interpreted as an identified process gain or time constant.

## Phase segments

| # | Phase | Start (s) | End (s) | Rows | Level min | Level max | Applied DAC min | Applied DAC max |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | `WAIT_MANUAL` | 0.093 | 14.906 | 82 | 360.000 | 400.000 | 0 | 150 |
| 2 | `RAMP_12000` | 14.921 | 26.656 | 66 | 136.000 | 553.000 | 150 | 12000 |
| 3 | `WAIT_STAGE` | 26.671 | 34.265 | 43 | 288.000 | 522.000 | 11700 | 12000 |
| 4 | `WAIT_AUTO` | 34.296 | 41.109 | 39 | 328.000 | 655.000 | 11510 | 11700 |
| 5 | `AUTO_ACTIVE` | 41.125 | 71.015 | 167 | 207.000 | 787.000 | 11082 | 11730 |
| 6 | `DISABLE_OUTPUT` | 175.484 | 175.484 | 1 | 411.000 | 411.000 | 0 | 0 |
| 7 | `RETURN_ZERO` | 175.515 | 180.484 | 29 | 400.000 | 421.000 | 0 | 0 |

## Stable positive-DAC plateaus detected

| Phase | Applied DAC | Start (s) | Duration (s) | Median-level change |
|---|---:|---:|---:|---:|
| `WAIT_STAGE` | 12000 | 26.671 | 6.172 | 40.000 |
| `WAIT_STAGE` | 11700 | 33.187 | 1.078 | -10.000 |
| `WAIT_AUTO` | 11700 | 34.296 | 4.297 | 172.000 |

Exact plateaus can help locate sections for visual review, but they do not remove the closed-loop bias from this dataset.

## Safety screening

```text
Watchdog-unhealthy rows: 0
Watchdog-tripped rows: 0
SafetyReset rows: 0
Negative AppliedDAC rows: 0
AppliedDAC above 12000 rows: 0
Final zero-output state: YES
```

## Identification decision

```text
BASELINE SCREENING COMPLETED: YES
DATASET IS OPEN LOOP: NO
REAL PLANT MODEL IDENTIFIED: NO
REAL TEST LIMITS AUTO-APPROVED: NO
OPEN-LOOP DATA REQUIRED: YES
OPERATOR-APPROVED MAXIMUM LEVEL REQUIRED: YES
MULTIPLE EXCITATION LEVELS REQUIRED: YES
```

## Required inputs before a real identification run

The following values still require explicit engineering and laboratory approval:

1. physical maximum raw-level limit and emergency margin;
2. approved initial level band;
3. staged DAC sequence, rather than an unreviewed single step;
4. hold time for each DAC level;
5. abort criteria for level rate, communication, and elapsed time;
6. repeat-run count and independent validation dataset.

The next real experiment should use multiple safe excitation levels and retain the validated PLC watchdog and fail-closed shutdown path.

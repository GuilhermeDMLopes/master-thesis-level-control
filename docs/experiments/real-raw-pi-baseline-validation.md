# Real Raw-Count PI Baseline Validation

## Validation date

July 31, 2026.

## Objective

Validate a conservative PI baseline on the real B&R level-control plant through the complete chain:

```text
4diac application
    -> FORTE
    -> Python OPC UA gateway
    -> B&R PLC watchdog
    -> physical output mapping
```

## Validated controller configuration

```text
Application: PI_REAL_RAW_SAFE
Setpoint: 450 raw counts
Proportional gain: 4.0 DAC/count
Integral gain: 0.02 DAC/(count*s)
Sampling time: 0.1 s
PV filter alpha: 0.98
DAC bias: 9000
DAC range: 0 to 12000
Maximum DAC change per execution: 150
```

## Experimental procedure

The validated sequence was:

1. Fail-closed startup with `MANUAL=TRUE` and `MANUAL_OUTPUT=-9000`.
2. Manual ramp to physical DAC 12000.
3. Manual staging at physical DAC 11700.
4. Transfer from manual to automatic PI near the setpoint region.
5. Thirty-second automatic observation.
6. Return to manual zero output.
7. Immediate physical-output disable.
8. Controlled gateway and FORTE shutdown.
9. Final PLC watchdog safe-trip validation.

## Recorded evidence

```text
Source CSV: C:\Projetos\master-thesis-level-control\data\raw\pi-tuned-test-20260731-155856\pi-tuned-monitor.csv
Repository evidence CSV: data/sample/real-raw-pi-v1-monitor.csv
CSV SHA256: 197D0F0113564EACC40D16325CF1760008C595CE815300DA8BE5841CAB060E07
Rows: 427
Recorded duration: 180.484 s
Automatic observation duration: 29.890 s
Observed phases: WAIT_MANUAL, RAMP_12000, WAIT_STAGE, WAIT_AUTO, AUTO_ACTIVE, DISABLE_OUTPUT, RETURN_ZERO
```

## Automatic-phase measurements

```text
Raw level minimum: 207
Raw level maximum: 787
Raw level median: 461.000

Rolling-median level minimum: 318.000
Rolling-median level maximum: 736.000
Rolling-median level median: 461.000

Applied DAC minimum: 11082
Applied DAC maximum: 11730
Applied DAC range: 648
```

The maximum raw level observed over the complete recorded sequence was `787` counts.

## Safety results

The following results were confirmed:

```text
Manual ramp to DAC 12000: PASSED
Manual staging at DAC 11700: PASSED
Automatic PI modulation: PASSED
Applied DAC remained within 0 to 12000: PASSED
Watchdog remained healthy during the active test: PASSED
Watchdog trip during the active test: NOT OBSERVED
SafetyReset during the active test: NOT OBSERVED
Immediate applied-output disable during shutdown: PASSED
Complete DAC command return to zero: PASSED
Final physical stop confirmation: PASSED
Final PLC watchdog safe-trip state: PASSED
```

## Interpretation

The `KP=4.0`, `KI=0.02` configuration is accepted as the validated real-plant PI baseline for the thesis architecture.

The experiment demonstrated:

- correct fail-closed startup;
- correct manual-to-automatic transfer;
- automatic DAC modulation without exceeding the configured boundary;
- healthy gateway-to-PLC watchdog operation;
- deterministic physical-output disable;
- complete command return to zero;
- final watchdog safe trip after stack shutdown.

The test also exhibited a substantial initial level transient. Therefore, this checkpoint must not be described as an optimal or production-grade tuning. It is a safe and functional PI baseline suitable for comparison with the subsequent MPC implementation.

## Acceptance decision

```text
REAL PI COMMUNICATION PATH: ACCEPTED
REAL PI SAFETY PATH: ACCEPTED
REAL PI FUNCTIONAL BASELINE: ACCEPTED
OPTIMAL PI TUNING: NOT CLAIMED
READY FOR MPC PREPARATION: YES
```

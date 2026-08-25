# Existing evidence audit for the local 11500–12000 DAC input map

## Classification

`EXISTING_EVIDENCE_INSUFFICIENT_FOR_STATIC_LOCAL_DEADZONE_IDENTIFICATION__NEW_SMALL_BOUNDED_LOCAL_IDENTIFICATION_RECOMMENDED`

## Why this audit is needed

The first real V3H run and the internal replay established that 11750 DAC is a
structural holding point of the **current model/objective**. They did not identify
the real plant's static dead-zone.

A real local dead-zone/gain estimate requires evidence at multiple input levels
around the boundary and observation windows long enough to get beyond the
identified 9 s transport delay.

For this audit, a plateau is considered minimally useful only if its total hold
is at least delay + 2*tau = 18.50 s. A stronger plateau has
delay + 3*tau = 23.25 s.

Closed-loop V3E/V3H holds are retained as diagnostic evidence, but they are not
treated as static identification data because process state, estimator action and
feedback policy are changing simultaneously.

## Existing local evidence

- `data/raw/local-identification-20260808-120916/local-identification.csv` — IDENTIFICATION_OR_CALIBRATION_NAMED; local DAC levels (50-count bins): [11550.0, 11700.0, 12000.0]; local constant segments: 3.
- `data/raw/local-identification-v3-20260808-121546/local-identification.csv` — IDENTIFICATION_OR_CALIBRATION_NAMED; local DAC levels (50-count bins): [11550.0, 11600.0, 11700.0, 11850.0, 12000.0]; local constant segments: 3.
- `data/raw/mpc-v3-clean-active-20260822-085254/clean-active-monitor.csv` — CLOSED_LOOP_NAMED; local DAC levels (50-count bins): [11550.0, 11700.0, 11850.0]; local constant segments: 1.
- `data/raw/mpc-v3-extended-active-20260822-091514/extended-active-monitor.csv` — CLOSED_LOOP_NAMED; local DAC levels (50-count bins): [11850.0]; local constant segments: 1.
- `data/raw/mpc-v3-extended-active-20260822-091942/extended-active-monitor.csv` — CLOSED_LOOP_NAMED; local DAC levels (50-count bins): [11550.0, 11700.0, 11850.0]; local constant segments: 1.
- `data/raw/mpc-v3e-expanded-active-20260822-103807/expanded-active-monitor.csv` — CLOSED_LOOP_NAMED; local DAC levels (50-count bins): [11550.0, 11850.0]; local constant segments: 1.
- `data/raw/mpc-v3h-first-active-20260822-124042/v3h-first-active-monitor.csv` — CLOSED_LOOP_NAMED; local DAC levels (50-count bins): [11550.0, 11700.0, 11750.0, 11800.0, 11850.0, 11900.0, 11950.0, 12000.0]; local constant segments: 11.
- `data/raw/mpc-v3h-first-active-20260822-124503/v3h-first-active-monitor.csv` — CLOSED_LOOP_NAMED; local DAC levels (50-count bins): [11550.0, 11700.0, 11750.0, 11800.0, 11850.0]; local constant segments: 4.
- `data/raw/open-loop-identification-20260729-142246/open-loop-identification.csv` — IDENTIFICATION_OR_CALIBRATION_NAMED; local DAC levels (50-count bins): [11550.0, 11700.0, 12000.0]; local constant segments: 1.
- `data/raw/pi-tuned-test-20260731-151307/pi-tuned-monitor.csv` — CLOSED_LOOP_NAMED; local DAC levels (50-count bins): [11550.0, 11700.0, 12000.0]; local constant segments: 2.
- `data/raw/pi-tuned-test-20260731-152327/pi-tuned-monitor.csv` — CLOSED_LOOP_NAMED; local DAC levels (50-count bins): [11500.0, 11550.0, 11600.0, 11650.0, 11700.0, 11750.0, 11800.0, 11850.0, 11900.0, 11950.0, 12000.0]; local constant segments: 54.
- `data/raw/pi-tuned-test-20260731-154406/pi-tuned-monitor.csv` — CLOSED_LOOP_NAMED; local DAC levels (50-count bins): [11550.0, 11600.0, 11650.0, 11700.0, 11850.0, 12000.0]; local constant segments: 20.
- `data/raw/pi-tuned-test-20260731-155856/pi-tuned-monitor.csv` — CLOSED_LOOP_NAMED; local DAC levels (50-count bins): [11500.0, 11550.0, 11600.0, 11650.0, 11700.0, 11750.0, 11850.0, 12000.0]; local constant segments: 25.
- `data/raw/positive-dac-manual-stop-20260729-134727/positive-dac-monitor.csv` — DYNAMIC_CONTROL_OR_UNKNOWN; local DAC levels (50-count bins): [11550.0, 11700.0, 11850.0, 12000.0]; local constant segments: 1.
- `data/raw/steady-calibration-20260808-103415/samples.csv` — IDENTIFICATION_OR_CALIBRATION_NAMED; local DAC levels (50-count bins): [11550.0, 11700.0, 11850.0, 12000.0]; local constant segments: 1.
- `data/raw/steady-calibration-20260808-103827/samples.csv` — IDENTIFICATION_OR_CALIBRATION_NAMED; local DAC levels (50-count bins): [11550.0, 11700.0, 11850.0, 12000.0]; local constant segments: 1.
- `data/raw/steady-calibration-20260808-104108/samples.csv` — IDENTIFICATION_OR_CALIBRATION_NAMED; local DAC levels (50-count bins): [11550.0, 11700.0, 11850.0, 12000.0]; local constant segments: 2.
- `data/raw/steady-calibration-20260808-113116/samples.csv` — IDENTIFICATION_OR_CALIBRATION_NAMED; local DAC levels (50-count bins): [11700.0, 11850.0, 12000.0]; local constant segments: 2.
- `data/raw/steady-calibration-20260808-113159/samples.csv` — IDENTIFICATION_OR_CALIBRATION_NAMED; local DAC levels (50-count bins): [11550.0, 11700.0, 11850.0, 12000.0]; local constant segments: 1.
- `data/raw/steady-calibration-20260808-113516/samples.csv` — IDENTIFICATION_OR_CALIBRATION_NAMED; local DAC levels (50-count bins): [11550.0, 11700.0, 11850.0, 12000.0]; local constant segments: 2.
- `data/raw/steady-calibration-20260808-113623/samples.csv` — IDENTIFICATION_OR_CALIBRATION_NAMED; local DAC levels (50-count bins): [11550.0, 11700.0, 11850.0, 12000.0]; local constant segments: 2.
- `data/raw/steady-calibration-20260808-113720/samples.csv` — IDENTIFICATION_OR_CALIBRATION_NAMED; local DAC levels (50-count bins): [11550.0, 11700.0, 11850.0, 12000.0]; local constant segments: 2.
- `data/raw/steady-calibration-dac13000-20260808-114728/samples.csv` — IDENTIFICATION_OR_CALIBRATION_NAMED; local DAC levels (50-count bins): [11550.0, 11700.0, 11850.0, 12000.0]; local constant segments: 0.
- `data/raw/steady-calibration-dac14000-20260808-114400/samples.csv` — IDENTIFICATION_OR_CALIBRATION_NAMED; local DAC levels (50-count bins): [11550.0, 11700.0, 11850.0, 12000.0]; local constant segments: 1.

## Identification-quality coverage

- minimum qualifying identification-like DAC levels: [11600.0, 12000.0];
- preferred-duration identification-like DAC levels: [11600.0];
- evidence at/below 11600 DAC: YES;
- evidence around 11650–11800 DAC: NO;
- evidence at/above 11900 DAC: YES;
- minimum three-level low/boundary/high structure: NO;
- preferred-duration depth: NO.

## Decision

The existing repository does **not** provide a defensible static local dead-zone
identification around 11500–12000 DAC under the stated delay/dynamics criteria.

The V3H closed-loop 11750-DAC plateau remains useful diagnostic evidence, but it
does not substitute for multi-level local excitation.

If a new experiment is approved, it should be a **small bounded local
identification experiment**, not another 60 s closed-loop V3H performance run.

The next stage should design that experiment offline first: DAC points, hold times,
initial-level envelope, raw/physical aborts, and mandatory zero-output recovery.

## Important limitation

This audit classifies evidence sufficiency from the available CSV signals and
experiment context. It does not infer an exact physical dead-zone value.

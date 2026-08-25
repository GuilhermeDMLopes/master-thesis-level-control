# MPC V3E â€” expanded-envelope real-plant variant

## Purpose

`MPC V3E` is an additive commissioning variant of the validated delay-aware
MPC V3. It exists to investigate a wider raw-count operating envelope after the
60 s V3 experiment demonstrated that the original internal 800-raw measured
hard trip was reached while the physically observed water height was only about
1 cm.

The original V3 is preserved unchanged.

## Unchanged control/model contract

- controller period: 500 ms;
- identified transport delay: 9.0 s;
- AppliedDAC history queue: 18 controller samples;
- identified dynamic time constant: 4.75 s;
- prediction horizon: 30 s;
- prediction steps: 60;
- target candidates: 13;
- DAC range: 0 .. 12000;
- maximum move: 750 DAC/update;
- bias adaptation: disabled;
- default `ENABLE_REQUEST`: FALSE.

## Expanded envelope

| Limit | V3 | V3E |
| --- | ---: | ---: |
| predicted soft | 650 raw | 1100 raw |
| predicted hard | 750 raw | 1400 raw |
| measured hard | 800 raw | 1500 raw |

The expanded limits do not claim that 1500 raw is physically safe by itself.
A later real-plant test must retain independent physical observation.

## Physical commissioning guard

The first V3E real-plant run should use:

- physical ruler visible during the entire active phase;
- operator abort at 5 cm;
- existing declared operational safe maximum of 25 cm remains unchanged;
- automatic watchdog, DAC and rate protections remain active;
- no increase of DAC beyond 12000;
- no change of MPC sample time or identified model.

## Evidence basis

The 2026-08-22 60 s V3 experiment reached:

- maximum raw: 818;
- maximum Median9: 757;
- maximum DAC: 11850;
- maximum positive median rate: 67.3 raw/s;
- watchdog healthy throughout;
- approximately 1 cm maximum observed physical water height.

Offline trace analysis confirmed:

- `PV_RAW` measured hard threshold in V3: 800 raw;
- the trace crossed 800 raw at approximately 33.047 s;
- `Enable` changed TRUE -> FALSE at approximately 34.141 s;
- classification:
  `INTERNAL_PV_RAW_TRIP_CONFIRMED_BY_FBT_AND_TRACE`.

Therefore the post-trip level fall in the 60 s experiment is not considered
evidence of MPC steady-state settling.

## Status

This file documents an **offline additive implementation only**.

Real V3E commissioning is not authorized until:

1. Eclipse/4diac parser and system layout validation passes;
2. the V3E FB is exported with FORTE 1.x NG;
3. an isolated FORTE V3E build succeeds;
4. an offline runtime type smoke test succeeds;
5. a protected zero-output deployment succeeds.

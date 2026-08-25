# MPC V3H first bounded active 60 s run — 2026-08-22

## Classification

`COMPLETED_BOUNDED_V3H_RUN__ACTUATION_DIRECTION_IMPROVED__REGULATION_NOT_VALIDATED`

## Experimental result

- active records: 481;
- active duration: 60.031 s;
- initial active Median9: 370.0 raw;
- maximum raw: 910.0;
- maximum Median9: 767.0;
- Median9 overshoot: 317.0 raw (70.4%);
- MAE: 133.017 raw;
- RMSE: 155.090 raw;
- IAE: 7966.390 raw*s;
- first target band (±5%): 2.031 s;
- final 10 s mean Median9: 608.988 raw;
- final 10 s MAE: 158.988 raw;
- final 20 s Median9 slope: -1.432 raw/s;
- maximum positive median rate: 123.7 raw/s;
- maximum AppliedDAC: 11850.0;
- physical maximum: 1.200 cm;
- physical abort utilization: 24.0%;
- watchdog healthy throughout: YES;
- 60 s window completed: YES;
- bounded 1100-raw / 5-cm envelope respected: YES.

## V3H actuation-direction question

- first AppliedDAC <= 11800 after high-equilibrium region: 18.016 s;
- first AppliedDAC <= 11750 after high-equilibrium region: 27.031 s;
- above-SP samples at/below 11750 DAC: 92.5%;
- above-SP samples at/below 11800 DAC: 100.0%;
- final contiguous hold at/below 11750 DAC: 33.000 s;
- actuation-direction improvement supported: YES.

This is the main positive result of the first V3H run: the real controller did
not remain locked at the ~11845.6-DAC equilibrium-like target throughout the
trajectory. It moved to the identified 11750-DAC dead-zone boundary.

## Regulation claim

Steady-state regulation validated: **NO**.

The first V3H run is therefore interpreted as a controller-behavior validation
experiment. A completed bounded run and improved actuation direction do not by
themselves establish steady-state regulation.

## Comparison with preserved V3E

**Strict controlled A/B test: NO.**

The V3H initial condition was materially different from the preserved V3E run,
so direct performance differences are descriptive rather than causal A/B evidence.

- V3H initial Median9: 370.0 raw;
- V3H max raw: 910.0;
- V3H max Median9: 767.0;
- V3H final-10-s mean Median9: 609.0;
- V3H physical maximum: 1.20 cm;
- preserved V3E max raw: 920.0;
- preserved V3E max Median9: 838.0;
- preserved V3E physical maximum: 1.50 cm;

## Decision

- increase the raw ceiling now: **NO**;
- repeat the plant run immediately: **NO**;
- claim steady-state regulation: **NO**;
- preserve this run as positive evidence that V3H changed the real actuation direction: **YES**;
- next action: inspect the V3H trajectory/model residual and decide whether a second
  experiment should target regulation or further disturbance/model correction.

## Evidence hashes

- active CSV SHA256: `EF977716F8FD55B939FEE251D8580DF38AA4525E76908DBFF511FF8F034E3C76`;
- physical observation SHA256: `1FFF6805758F79F7C28FF6F47AE00D046262789A2FF7B2E434AC84F73A916222`.

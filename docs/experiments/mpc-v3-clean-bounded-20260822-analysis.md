# MPC V3 clean bounded experiment ??? 2026-08-22

## Classification

**Result:** bounded safety abort, suitable as commissioning/safety evidence.

This run is **not** classified as a successful steady-state regulation validation.
The experiment was terminated automatically when the rolling median level exceeded
the predeclared supervisory limit of 550 raw.

## Preserved evidence

- Active CSV: `data/sample/mpc-v3-clean-evidence-20260822/clean-active-monitor.csv`
- Warm-up CSV: `data/sample/mpc-v3-clean-evidence-20260822/warmup-monitor.csv`
- Metrics: `data/sample/mpc-v3-clean-evidence-20260822/metrics.json`

SHA256:

- Active: `1704E2CB6C34DBA0EE51252529FBE2B6D6F96697C6731CD1033BADD06A17AA97`
- Warm-up: `69BD80F861ADA592DB53039EA67D07B6746AB4C4E62560C1C0ABDF999287AEFB`

## Clean warm-up

- Samples: 93
- Raw level range: 298.0 .. 318.0
- Raw median: 308.0
- Distinct heartbeat values: 47
- Zero output throughout: True
- Watchdog healthy throughout: True

The 12 s warm-up exceeded the identified 9 s transport-delay history requirement.

## Active-window metrics

- Observed active duration: 27.297 s
- SP: 450.0 raw
- Raw range: 115.0 .. 573.0
- Median9 range: 166.0 .. 553.0
- Median9 overshoot above SP: 103.0 raw (22.9% of SP)
- Maximum positive median rate: 96.0 raw/s
- Maximum command/applied DAC: 11850.0
- Near-equilibrium DAC first reached: 11.719 s
- Approx. time near equilibrium DAC: 15.578 s
- First raw >= SP: 23.297 s
- First Median9 in 440..460 target band: 24.391 s
- First Median9 >= SP: 24.391 s
- First Median9 >= 500: 26.406 s
- First Median9 > 550: 27.297 s
- Watchdog healthy in all logged rows: True
- Watchdog tripped in any logged row: False

## Interpretation

The experiment demonstrates that the delay-aware MPC V3 can drive the real plant
from the empty-tank region toward the target while maintaining a healthy watchdog
and bounded actuator command. The controller command converged close to the
identified equilibrium DAC, but the measured level exhibited a delayed late rise.

The late rise continued while the command remained close to the equilibrium value,
and the rolling median ultimately crossed the supervisory limit. This indicates that
the V3 model/control policy does not yet represent the complete late plant response
well enough to claim steady-state regulation at SP=450 raw.

The supervisory layer behaved correctly: the run was terminated by the declared
median-level protection rather than by watchdog failure or an actuator-command
violation, and the operator log confirmed final zero output.

## Dissertation use

Use this run as:

1. evidence of successful real PLC / gateway / FORTE / MPC V3 integration;
2. evidence of the identified transport-delay behavior;
3. evidence that the safety supervisor correctly terminates a bounded experiment;
4. evidence of remaining model mismatch / late overshoot.

Do **not** describe this experiment as validated steady-state tracking.

For a time-efficient thesis completion, further model retuning is optional rather
than required for documenting the implemented MPC architecture and its experimentally
observed limitations. A PI vs MPC comparison should explicitly include the V3
safety-abort/overshoot result instead of hiding it.

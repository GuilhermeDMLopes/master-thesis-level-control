# MPC V3E protected expanded-envelope commissioning

## Objective

Perform the first real-plant commissioning of the additive MPC V3E while
preserving the validated V3/V3E artifacts and maintaining independent software
and physical safety barriers.

## V3E controller contract

Unchanged from V3:

- controller period: 500 ms;
- transport delay: 9.0 s;
- AppliedDAC history queue: 18 samples;
- dynamic tau: 4.75 s;
- prediction horizon: 30 s / 60 steps;
- DAC range: 0 .. 12000;
- maximum DAC move: 750 per controller update;
- setpoint for the first V3E run: 450 raw.

Expanded internal envelope:

- predicted soft: 1100 raw;
- predicted hard: 1400 raw;
- measured hard: 1500 raw.

Independent physical commissioning barrier:

- operator abort threshold: 5 cm;
- declared operational safe maximum remains 25 cm.

## Required sequence

1. Working tree clean and V3E runtime hash verified.
2. Physical emergency stop accessible.
3. Tank visually safe and ruler/measurement reference ready.
4. Start gateway and verify PLC + gateway connectivity.
5. Verify zero actuator state at PLC:
   - Enable = FALSE;
   - DAC = 0;
   - AppliedEnable = FALSE;
   - AppliedDAC = 0;
   - WatchdogHealthy = TRUE;
   - WatchdogTripped = FALSE.
6. Start only the preserved/candidate V3E FORTE.
7. Deploy only `FORTE_PC -> ResRealRawMPCV3E`.
8. Keep `MpcController.ENABLE_REQUEST = FALSE`.
9. Run the canonical zero-output deployment guard.
10. While the guard is active, trigger `MpcInitMerge.EI1` exactly once on a fresh deployment.
11. Confirm the pump remains stopped and zero output is preserved.
12. Inspect V3E runtime inputs before any active command.
13. Only after all previous checks pass, arm a bounded active experiment.

## First active V3E experiment

Recommended initial experiment:

- active window: 60 s maximum;
- sample period of supervisor: 0.2 s;
- MPC internal sample time: 500 ms;
- SP_RAW: 450;
- DAC hard ceiling: 12000;
- software median supervisory stop: 1400 raw;
- software instantaneous stop: 1500 raw;
- positive median-rate stop: 180 raw/s;
- physical operator stop: 5 cm.

The operator must abort immediately if the physical level reaches 5 cm or if
the visible hydraulic behavior is inconsistent with the expected bounded test.

## Interpretation

This experiment is intended to test whether the expanded V3E envelope prevents
the premature 800-raw V3 trip while maintaining bounded behavior. It is not a
claim of steady-state regulation unless the full trajectory supports that
conclusion.

The physical height in cm must be recorded at the maximum observed level.

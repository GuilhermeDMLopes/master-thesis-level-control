# MPC V3E expanded-envelope 60 s experiment — 2026-08-22

## Experimental classification

**COMPLETED_EXPANDED_ENVELOPE_RUN__REGULATION_NOT_VALIDATED**

The 60 s active window completed normally. The experiment therefore demonstrates
that the additive V3E envelope removed the premature 800-raw measured-PV trip
that limited the earlier V3 experiment. It does **not** establish satisfactory
steady-state regulation.

## Experiment duration relative to the identified dynamics

- active duration: 60.047 s;
- MPC sample time: 0.500 s;
- equivalent controller updates: 120.1;
- identified transport delay: 9.000 s;
- experiment length / transport delay: 6.67x;
- identified tau: 4.750 s;
- experiment length / tau: 12.64x.

This window is long enough to expose multiple transport-delay intervals and
multiple identified time constants. The result should not be described as a
short transient-only test.

## Tracking and overshoot

- SP: 450.0 raw;
- maximum instantaneous raw: 920.0;
- maximum Median9 raw: 838.0;
- Median9 peak overshoot: 388.0 raw (86.2%);
- instantaneous peak overshoot: 470.0 raw (104.4%);
- MAE: 207.820 raw;
- RMSE: 230.068 raw;
- IAE: 12450.265 raw·s;
- first Median9 within ±5% band: 22.672 s;
- first Median9 within ±10% band: 22.672 s;
- first Median9 >= SP: 22.672 s;
- first Median9 >= 550 raw: 29.516 s;
- first Median9 >= 800 raw: 57.172 s;
- time above SP: 35.125 s;
- time >= 550 raw: 26.937 s;
- time >= 800 raw: 2.875 s.

## Final 10 s

- mean Median9: 748.587 raw;
- MAE: 298.587 raw;
- Median9 range: 625.0 .. 838.0 raw;
- final 5 s mean Median9: 808.826 raw;
- final 5 s mean AppliedDAC: 11846.000.

The final portion remains materially above the 450-raw setpoint. Steady-state
regulation is therefore **not validated**.

## Actuator behavior

- maximum DAC: 11850.0;
- threshold used to identify near-equilibrium/high-DAC operation: 11800.0;
- time at or above that threshold: 48.266 s;
- fraction of active duration at high DAC: 80.4%;
- AppliedDAC total variation: 11854.0.

The controller spent a substantial fraction of the experiment near the
~11846-DAC region even after the measured level exceeded SP. This behavior is a
more important next diagnostic target than further increasing the raw safety
ceiling.

## Expanded-envelope utilization

- Median9 supervisory limit: 1400.0 raw;
- maximum Median9: 838.0 raw;
- remaining Median9 margin: 562.0 raw;
- Median9 limit utilization: 59.9%;
- instantaneous supervisory limit: 1500.0 raw;
- maximum instantaneous raw: 920.0 raw;
- remaining instantaneous margin: 580.0 raw;
- instantaneous limit utilization: 61.3%.

**Envelope limiting the experiment: NO.**

Therefore, increasing the raw ceiling again is not justified by this run.

## Empty-baseline mismatch

- V3 identified model empty offset: 288.0 raw;
- pre-active observed baseline median: 227.0 raw;
- observed minus model offset: -61.0 raw.

The baseline moved materially relative to the 288-raw value used during V3
identification. This mismatch should be investigated before another controller
variant is commissioned.

## Physical observation

- maximum observed physical water height: 1.500 cm;
- physical abort threshold: 5.0 cm;
- fraction of physical abort threshold used: 30.0%;
- declared operational safe maximum: 25.0 cm;
- fraction of declared safe maximum used: 6.0%.

The raw signal is not converted to centimeters here; the physical observation
is preserved as an independent measurement.

## Watchdog / runtime

- Watchdog healthy throughout active window: YES;
- controller remained enabled after active-output detection: YES;
- active window completed without supervisor abort: YES;
- final zero output was verified by the commissioning script: YES.

## Decision

**Do not increase the V3E raw ceiling again before changing the control/model
logic.**

The 60 s test already completed with substantial margin to both 1400 and 1500
raw. The next offline work should focus on:

1. updating or compensating the empty raw offset, because the current baseline
   is materially below the 288-raw identification offset;
2. explaining why the controller remains near 11846 DAC after PV exceeds SP;
3. reviewing the candidate-action set and objective/cost behavior;
4. preserving this experiment as evidence that the previous 800-raw internal
   trip was removed without approaching the 5 cm physical abort threshold.

No further real actuation should be performed until that offline diagnosis is
completed.

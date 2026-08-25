# MPC V3H first-active 11750-DAC plateau diagnosis

## Classification

`11750_BOUNDARY_REACHED__REAL_RESPONSE_REMAINS_DYNAMIC__STATIC_DEADZONE_NOT_IDENTIFIABLE_FROM_SINGLE_CLOSED_LOOP_HOLD`

## What the real run established

- V3H reached <=11750 DAC after the high-DAC region at 27.031 s;
- the final exact 11750-DAC hold lasted 33.000 s;
- plateau Median9 started at 593.0 raw and ended at 675.0 raw;
- plateau Median9 ranged from 451.0 to 767.0 raw;
- total Median9 excursion while AppliedDAC stayed at ~11750 was 316.0 raw;
- linear slope across the whole final plateau was -0.090 raw/s;
- 100.0% of plateau samples were above the 450-raw SP.

## Interpretation

The first V3H run confirms the intended **control-direction change**: the command
moved from the high equilibrium-like region to the 11750-DAC boundary and remained
there for a substantial part of the experiment.

However, this trace does **not** identify the real static dead-zone threshold.
The plant output remained strongly dynamic while the applied command was fixed near
11750 DAC. That motion can contain delayed input effects, stored hydraulic state,
gravity-drain dynamics and model/disturbance mismatch. A single closed-loop hold is
not persistently exciting enough to assign the observed motion uniquely to the
11750-DAC input.

Therefore it would be premature to conclude either:

- that 11750 DAC is the exact real dead-zone; or
- that the Hammerstein dead-zone assumption is wrong.

## Segment behavior

- segment 1: 27.03..38.05 s, mean=613.3 raw, slope=+8.10 raw/s, range=492.0..686.0;
- segment 2: 38.19..49.03 s, mean=657.7 raw, slope=-19.65 raw/s, range=543.0..757.0;
- segment 3: 49.16..60.03 s, mean=598.5 raw, slope=+24.75 raw/s, range=451.0..767.0;

## Decision

- change V3H now: **NO**;
- increase the raw ceiling: **NO**;
- repeat the same 60 s experiment immediately: **NO**;
- claim the real dead-zone is exactly 11750 DAC: **NO**;
- next: offline replay of the V3H disturbance estimator and prediction at plateau snapshots.

The next analysis should determine whether V3H remains at 11750 because its learned
disturbance/prediction says that this is optimal, or because the model's nonlinear
input map/dead-zone is still inaccurate around that operating region.

# MPC V3F connected action-space contract

## Purpose

MPC V3F is an additive successor to V3E. The first V3F change is limited to
the optimizer action-space parameterization.

V3 and V3E are preserved unchanged.

## Confirmed V3E defect

The V3/V3E absolute candidate set is split into two components under the
750-DAC move constraint:

- `{0}`;
- approximately `{11500 .. 12000}`.

Once the controller enters the high-DAC component, it cannot legally return
toward zero because no intermediate candidates exist.

## V3F candidate principle

V3F generates candidates relative to current `AppliedDAC` rather than using
the disconnected absolute candidate set.

The initial offline V3F action kernel uses 13 symmetric relative moves:

`[-750, -625, -500, -375, -250, -125, 0, 125, 250, 375, 500, 625, 750]`

Each relative move is added to current `AppliedDAC` and clamped to `0..12000`.

Properties:

- maximum move remains 750 DAC/update;
- hold action is always available;
- downward actions exist at high DAC;
- upward actions exist below the upper bound;
- zero is reachable from the high-DAC region through legal moves;
- no V3/V3E artifact is overwritten.

## Parameters intentionally unchanged

The first V3F iteration must preserve:

- controller sample time: 500 ms;
- transport delay: 9 s;
- AppliedDAC history: 18 samples;
- tau: 4.75 s;
- prediction horizon: 60 steps / 30 s;
- DAC envelope: 0..12000;
- maximum move: 750 DAC/update;
- V3E expanded safety envelope: predicted soft 1100, predicted hard 1400,
  measured hard 1500 raw;
- SP_RAW: 450;
- bias adaptation: disabled.

## Separate model issue

The completed V3E run observed a pre-active empty baseline around 227 raw,
while the identified model uses 288 raw. The approximately -61 raw mismatch is
retained as a separate model issue.

It is not changed in this first action-space kernel so the effect of action
connectivity can be isolated.

## Validation scope of this stage

This stage validates candidate topology and availability only. It does not yet
claim that the full V3F MPC objective produces satisfactory closed-loop
regulation.

The next stage must integrate this candidate kernel into an additive Python
V3F reference controller and replay the preserved V3E evidence before any
4diac/FORTE implementation or real actuation.

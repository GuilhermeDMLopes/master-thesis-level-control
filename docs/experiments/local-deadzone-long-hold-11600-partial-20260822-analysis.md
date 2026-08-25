# Partial long-hold local identification: 11600 DAC

## Classification

`PARTIAL_LONG_HOLD_11600_COMPLETED__APPLIED_TARGET_RAMP_REDUCED_CONSTANT_HOLD__FIXED_INITIAL_BASELINE_RECOVERY_NOT_REESTABLISHED__ZERO_OUTPUT_SETTLED_AT_SHIFTED_LEVEL__REAL_DEADZONE_NOT_YET_IDENTIFIED`

## What completed

- one bounded open-loop point was executed at 11600 DAC;
- the ACTIVE phase lasted 44.91 s;
- maximum physical height was 0.50 cm;
- watchdog remained healthy;
- output was forced to zero after the plateau;
- final zero state was verified.

## Important correction: 45 s ACTIVE was not 45 s at 11600 DAC

AppliedDAC first reached 11600 at approximately 11.14 s.
The continuous constant-target interval was therefore about 33.77 s.

This matters for identification. The actuator/gateway path ramped from zero to the
requested point during the beginning of the ACTIVE window. A future executor should
start the 45 s identification hold clock only after AppliedDAC has reached and
stabilized at the requested target.

After the 9 s transport delay from target attainment, this run still preserved
approximately 24.66 s of constant-target response,
equivalent to about 5.19 identified time constants.

## 11600-DAC response

- post-delay Median9: 288.0 -> 492.0 raw;
- post-delay change: +204.0 raw;
- post-delay linear slope: +7.152 raw/s;
- maximum Median9 during ACTIVE: 492.0 raw;
- final 10 s mean Median9: 417.7 raw.

The run therefore contains evidence of a late plant response while AppliedDAC was
constant at 11600. This is relevant to the local input-map question, but a single
point does not identify the static dead-zone threshold.

## Why recovery timed out

The initial zero-output Median9 reference was 278.0 raw, so the
protocol required recovery to <= 308.0 raw.

During the 180 s zero-output recovery, Median9 never re-established that criterion.
The final Median9 was 360.0 raw,
approximately +82.0 raw above the initial baseline.

However:

- commanded/applied output remained zero throughout recovery: YES;
- watchdog remained good: YES;
- final 60 s mean Median9: 355.7 raw;
- final 60 s slope: -0.103 raw/s;
- final 20 s mean Median9: 354.3 raw;
- final 20 s slope: +0.461 raw/s.

So the failure was not a failure to force the actuator to zero. The issue is that
the plant/sensor did not numerically return to the original session baseline within
180 s. The zero-output signal instead approached a shifted, comparatively stable
level.

The physical cause of that shift is **not identified by this trace alone**. It may
reflect residual hydraulic inventory, slow drainage, sensor offset/drift, or another
plant-state effect. The data do not justify choosing one explanation yet.

## Protocol implications

Do not continue with the remaining DAC points using the current executor unchanged.

Two aspects need revision before the next real run:

1. **Target-settling gate** — begin the 45 s identification hold only after
   AppliedDAC is at the requested target and stable;
2. **Recovery-state gate** — require verified zero output plus a stable zero-output
   state, while recording a new local baseline for the next point, instead of
   requiring every point to return to the first numerical baseline.

Any revised recovery rule must still preserve the physical 5 cm abort, the raw
safety bounds, watchdog checks, and manual operator confirmation.

## Decision

- preserve this 11600-DAC plateau: **YES**;
- classify it as a completed seven-point identification set: **NO**;
- claim the real dead-zone is below/above 11600 from this point alone: **NO**;
- repeat the current executor unchanged: **NO**;
- increase the raw ceiling: **NO**;
- next: checkpoint this evidence and revise the local-identification execution
  semantics offline before another real point.

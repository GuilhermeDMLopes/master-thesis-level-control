# Long-hold local dead-zone identification protocol

## Status

Prepared offline by ETAPA 7.5AT.

**This preparation stage does not authorize real actuation.**

The preceding evidence audit concluded:

EXISTING_EVIDENCE_INSUFFICIENT_FOR_STATIC_LOCAL_DEADZONE_IDENTIFICATION__NEW_SMALL_BOUNDED_LOCAL_IDENTIFICATION_RECOMMENDED

Audit checkpoint:

$AuditCommit

## Why a longer experiment is justified

The identified plant model currently uses approximately:

- transport delay: **9 s**;
- time constant: **4.75 s**.

The earlier evidence audit treated delay + 3*tau = 23.25 s as a preferred
minimum hold for static/local-map identification.

The new protocol uses a **45 s hold at each DAC point**. This leaves:

- **36 s after the 9 s transport delay**;
- approximately **7.58 time constants after the delay**;
- approximately **450 raw samples per complete plateau** at 0.1 s logging.

This is intentionally much longer than the earlier short excitation used during
initial model development.

## Identification objective

Estimate the real local input map around the model's current 11750-DAC
dead-zone boundary.

The experiment is not a closed-loop MPC performance run. PI/MPC/FORTE must
remain inactive.

## DAC points

Execute separately, with zero recovery between points:

1. 11600 DAC
2. 11650 DAC
3. 11700 DAC
4. 11750 DAC
5. 11800 DAC
6. 11850 DAC
7. 11900 DAC

The 50-count spacing around 11750 is deliberate. The repository already has
coarser evidence at approximately 11600 and 12000, while the missing
identification coverage is concentrated around 11650â€“11800.

The sequence is ascending for operational safety. This is not claimed as a
randomized system-identification design.

## Timing

Before the first point:

- command Enable=FALSE, DAC=0;
- verify commanded and applied zero output;
- collect **20 s** of zero-output baseline.

For every DAC point:

- plateau maximum duration: **45 s**;
- log at **0.1 s**;
- never extend a plateau because the response looks incomplete;
- abort earlier if any safety limit is reached.

After every plateau:

- force Enable=FALSE, DAC=0;
- verify commanded and applied zero;
- hold zero for at least **10 s**;
- continue recovery until the level is near the session zero baseline;
- recovery target: Median9 <= baseline + 30 raw;
- stable-trend target: |slope| <= 5 raw/s over at least **8 s**;
- maximum recovery waiting time: **180 s**;
- if recovery cannot be established, end the experiment instead of starting
  the next plateau.

## Independent safety envelope

Automatic / supervisor abort:

- instantaneous raw level >= **1100 raw**;
- rolling median >= **1100 raw**;
- positive median-rate >= **180 raw/s**;
- DAC > **12000**;
- WatchdogHealthy = FALSE;
- WatchdogTripped = TRUE;
- PLC/gateway communication failure.

Physical operator abort:

- water height >= **5 cm**;
- visually unexpected hydraulic behavior;
- loss of confidence in plant state;
- physical stop must remain immediately accessible.

The declared 25 cm operational maximum is **not** the experimental target. The
5 cm threshold remains the local-identification operator limit.

## Evidence required

For every sample:

- time;
- plateau index / DAC point;
- phase (BASELINE, ACTIVE, RECOVERY);
- raw level;
- rolling Median9;
- positive level rate;
- commanded Enable/DAC;
- applied Enable/DAC;
- watchdog healthy/tripped.

For every plateau also record:

- initial raw/Median9;
- maximum raw/Median9;
- maximum physical water height in cm;
- actual active duration;
- whether the full 45 s hold completed;
- stop reason;
- zero-output recovery duration.

## Acceptance criterion for the data set

A DAC point is considered identification-quality only if:

- the plateau starts from a verified safe/stable zero-recovery state;
- no watchdog/communication fault occurs;
- the actuator command is constant for the analyzed interval;
- the plateau provides a substantial post-delay observation interval;
- final zero output is verified.

An early safety abort remains valid safety evidence but is not automatically
treated as a completed static-identification plateau.

## Planned analysis

After the experiment, fit/compare local input maps using the completed plateaus:

- candidate dead-zone threshold;
- local effective gain above threshold;
- confidence / residuals;
- held-out prediction error;
- consistency with the V3H real trajectory.

Do **not** modify the V3H controller until the new identification data are
preserved and analyzed offline.

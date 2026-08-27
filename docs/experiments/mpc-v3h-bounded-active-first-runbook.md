# First bounded active MPC V3H experiment

## Status

Prepared offline by ETAPA 7.5AM.

**Real actuation is not authorized by the preparation stage itself.**

The prior protected zero-output commissioning is classified:

PROTECTED_V3H_ZERO_OUTPUT_DEPLOYMENT_PASSED

Evidence checkpoint:

7f27e21

## Objective

Run one bounded 60 s active V3H experiment on the real plant to test whether
the accepted state/process-disturbance correction changes the real closed-loop
behavior in the expected direction.

The first active run is deliberately a validation run, not a performance claim.

## Exact runtime

FORTE:

C:\Projetos\master-thesis-level-control\forte\preserved-v3h-3_9\runtimes\mpc-v3h-3_9\forte.exe

SHA256:

2535F31A5A5FC246BFC699ABDB4171531C71E56C4B72675D284C1322F7FAF31A

open62541 SHA256:

452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318

## Controller contract - unchanged

- SP: 450 raw;
- Ts: 500 ms;
- transport delay: 9.0 s;
- AppliedDAC history: 18 samples;
- prediction horizon: 60 steps / 30 s;
- max move: 750 DAC/update;
- DAC envelope: 0..12000;
- disturbance alpha: 0.10;
- disturbance clamp: +/-100 raw/controller-step;
- predicted soft limit: 1100 raw;
- predicted hard limit: 1400 raw;
- measured hard limit: 1500 raw;
- default ENABLE_REQUEST = FALSE.

No parameter tuning is allowed during this first active V3H run.

## Experimental timing

1. Start/verify gateway and exact V3H FORTE.
2. Fresh deploy only:
   FORTE_PC -> ResRealRawMPCV3H.
3. Keep ENABLE_REQUEST = FALSE.
4. Trigger MpcInitMerge.EI1 exactly once on the fresh deployment.
5. Keep zero output for **12 s** before enabling V3H.
   - This exceeds the 9 s / 18-sample delay-history requirement.
6. Start active evidence logging.
7. Set MpcController.ENABLE_REQUEST = TRUE.
8. Run V3H for at most **60 s**.
9. Disable V3H immediately at the first abort condition or at 60 s.
10. Confirm zero output for at least **10 s** after disable.
11. Stop FORTE only after final zero state is confirmed.
12. Record maximum physical water height in centimetres.

## Mandatory abort criteria

Immediately disable V3H and use the physical stop if necessary if any of these
occurs:

- measured/raw level reaches **1100 raw**;
- physical water height reaches **5 cm**;
- WatchdogHealthy = FALSE;
- WatchdogTripped = TRUE;
- communication/gateway becomes unhealthy;
- exact V3H FORTE exits;
- unexpected resource/deployment error occurs;
- actuator behavior is visibly inconsistent with commands;
- operator loses confidence in the physical state.

The 1100-raw operator threshold is intentionally below the controller's
1500-raw measured hard trip.

## Evidence required during the active window

At minimum preserve at approximately 0.1 s logging cadence:

- elapsed time;
- raw level;
- filtered/Median9 level when available;
- SP;
- requested Enable;
- requested DAC;
- AppliedEnable;
- AppliedDAC;
- WatchdogHealthy;
- WatchdogTripped;
- V3H command/target outputs when available;
- V3H disturbance estimate d_hat when available;
- final stop reason.

Also record manually:

- initial physical water height;
- maximum physical water height;
- any visible transient not represented adequately by raw sensor values.

## Primary acceptance questions

The first V3H run is useful if it can answer:

1. Does V3H move effective actuation toward the 11750-DAC dead-zone once the
   real process rises above SP?
2. Does the real trajectory avoid the persistent ~11846-DAC lock-in seen in V3E?
3. Does the learned disturbance estimate grow in a direction consistent with
   the previously inferred positive process/model mismatch?
4. Does the experiment remain inside the 1100-raw / 5-cm bounded envelope?
5. Does the system return to verified zero output after disable?

## What must not be claimed from one run

Do not claim from this single experiment alone:

- validated steady-state regulation;
- global MPC superiority over PI;
- final disturbance-model correctness;
- safety beyond the tested bounded envelope.

## Comparison basis

The preserved V3E 60 s experiment reached approximately:

- max raw: 920;
- max Median9: 838;
- max AppliedDAC: 11850;
- physical maximum: 1.5 cm;
- final regulation not validated.

The V3H run should first be evaluated against that failure mode, especially
persistent high-DAC behavior, before any broader PI-vs-MPC conclusion.

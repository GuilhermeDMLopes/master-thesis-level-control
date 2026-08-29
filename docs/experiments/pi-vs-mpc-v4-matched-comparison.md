# Matched PI versus MPC V4 real-plant comparison

This stage adds one bounded PI run for a methodologically comparable baseline.
It does not replace or modify the historical `PI_REAL_RAW_SAFE` application.

## Frozen comparison contract

- physical target: 15 cm;
- raw-count target: 17000;
- initial band: 240 to 340 raw;
- active duration: 180 s;
- sampling period: 0.1 s;
- final DAC range: 0 to 16000;
- safe limiter: 150 DAC per 100 ms cycle, equivalent to the MPC limit of
  750 DAC per 500 ms cycle (1500 DAC/s);
- PI gains retained from the validated raw PI: KP=4.0 and KI=0.02;
- feedforward bias: 14000 DAC, based on the observed steady-state region of
  the successful MPC V4 experiment;
- startup state: `RawPI.MANUAL=TRUE`, producing a zero biased request;
- activation: manually change only `RawPI.MANUAL` to `FALSE` after the
  independent supervisor prints `ARMED`.

The PI bias is disclosed because it uses the same operating-region evidence
available after the MPC validation. The comparison therefore concerns closed-
loop transient and steady-state behavior under the same target and actuator
bounds, not blind controller tuning.

## Protected execution

Deploy only `FORTE_PC -> ResRealRawPICompare`. With the plant near zero output,
trigger `RawInitMerge.EI1` exactly once while `RawPI.MANUAL` remains `TRUE`.
Run `scripts/pi_high_range_validation.py --plan` before any active command.

The supervisor never writes a positive actuator command. At completion or any
violation it terminates the exact FORTE process, writes safe zero through the
existing gateway/PLC safety path, and verifies final zero output.

If this single matched attempt is unsafe, unstable, or requires a new tuning
campaign, stop the PI comparison. The dissertation then reports the PI only as
historical infrastructure evidence and bases its final experimental conclusion
on the validated MPC V4 result, without claiming quantitative superiority.

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
- PI gains for the final single retuned attempt: KP=4.0 and KI=0.10;
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

## One-step integral retuning decision

The first matched attempt retained the historical `KI=0.02`. It completed the
180 s safety window without faults, but reached only about 6 cm: maximum level
6370 raw, median9 maximum 6257 raw, and maximum DAC 14306. The target was not
reached because bumpless transfer made the command rise too slowly.

One final attempt therefore uses `KI=0.10`, with `KP=4.0` unchanged. At the
initial error of approximately 16750 raw, the nominal integral increment is
about 167.5 DAC per 100 ms cycle. This is already above the independent limiter
of 150 DAC per cycle, so the limiter—not `KI`—defines the initial ramp. Values
above 0.10 would not accelerate that ramp and would only increase integral
aggressiveness near the reference.

No iterative tuning campaign is authorized. If this single retuned attempt
does not reach and regulate the 15 cm target safely, the experimental thesis
conclusion remains based on the validated MPC V4 controller.

## Final accepted result

The final single retuned PI attempt was completed on 2026-09-01 with
`KP=4.0`, `KI=0.10`, a 17000-raw target, 14000-DAC bias, 0..16000 DAC bounds,
and the independent 180 s supervisor. The physically measured level reached
14.7 cm against the nominal 15 cm target. The maximum median-9 level was 16148
raw, maximum applied DAC was 16000, and maximum positive median rate was 375.6
raw/s. The watchdog remained healthy, the run ended with
`ACTIVE_WINDOW_COMPLETE`, FORTE stopped automatically, and 80 independent
post-shutdown samples confirmed zero output.

The PI baseline is accepted. No additional PI tuning or real-plant repetition
is required. The final comparison with MPC V4 is documented in
`pi-vs-mpc-v4-final-20260901-analysis.md`.

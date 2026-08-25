# Revised local dead-zone identification execution semantics

## Status

Prepared offline after the first 11600-DAC long-hold experiment.

**This stage does not authorize new real actuation.**

Source evidence checkpoint:

$EvidenceCommit

## Why the original executor must not be repeated unchanged

The 11600-DAC run exposed two execution-semantics issues.

### 1. The 45 s ACTIVE clock included actuator acquisition

The command was requested at the start of ACTIVE, but AppliedDAC first reached
11600 only after approximately **11.14 s**.

Consequently the constant-11600 interval was approximately
**33.77 s**, not 45 s.

The run still contains approximately
**24.66 s**
of constant-target data after the 9 s transport delay, equivalent to
**5.19 tau**.
That exceeds the previously preferred 3-tau post-delay criterion, so 11600 does
not need an automatic repeat.

However, all future points must use a separate target-acquisition gate.

## Revised target acquisition gate

For each remaining DAC point:

1. command the requested DAC;
2. keep all safety checks active during the ramp;
3. wait until AppliedDAC is within **+/-5 DAC** of target;
4. require **5 consecutive samples** inside that tolerance;
5. maximum acquisition wait: **30 s**;
6. only then start the **45 s constant-target identification hold**.

If the acquisition gate is not met, force zero and end the experiment.

Remaining points:

- 11650
- 11700
- 11750
- 11800
- 11850
- 11900

The completed 11600 point is preserved and is **not repeated automatically**.

## Why the original recovery gate must change

The original session baseline was **278 raw**.
The executor therefore required recovery to
**<= 308 raw**.

During approximately 180 s of recovery:

- commanded and applied actuator output remained zero;
- watchdog remained healthy;
- the final Median9 was approximately **360 raw**;
- final 60 s slope was approximately **-0.103 raw/s**;
- final 20 s slope was approximately **0.461 raw/s**.

Therefore the timeout was caused by the requirement to return to the **first
numerical baseline**, not by failure to force the actuator to zero.

The physical reason for the shifted zero-output level remains unidentified and
must not be guessed from this run alone.

## Revised zero-output recovery / rebaseline gate

After every point:

1. force and verify:
   - Enable=FALSE;
   - DAC=0;
   - AppliedEnable=FALSE;
   - AppliedDAC=0;
2. wait at least **30 s** at verified zero output;
3. then search for a **20 s** stable zero-output window;
4. require:
   - watchdog healthy;
   - no trip;
   - |Median9 slope| <= 1 raw/s;
   - Median9 range over the window <= 30 raw;
5. define the new point-local baseline as the **median Median9** over that
   accepted stable window;
6. manually measure the physical water height;
7. require physical height **<= 1 cm** before authorizing the next point.

The next point is analyzed as:

Delta Median9 = Median9 - local zero-output baseline

This makes the local input-map comparison robust to the zero-output baseline
shift observed in the real plant.

The executor no longer requires every point to return numerically to the first
baseline of the session.

## Safety envelope remains unchanged

- instantaneous raw abort: **1100 raw**;
- rolling Median9 abort: **1100 raw**;
- positive Median9-rate abort: **180 raw/s**;
- DAC hard maximum: **12000**;
- physical active-run abort: **5 cm**;
- watchdog unhealthy/tripped: **ABORT**;
- communication failure: **ABORT**.

No raw ceiling is increased.

## Interpretation of the 11600 point

The 11600 point is useful local dynamic evidence because it contains more than
5 identified time constants of constant-target response after the transport
delay.

It also exhibited a strong late Median9 increase while AppliedDAC was fixed at
11600.

This is evidence that the current local model requires further validation, but
it is **not sufficient by itself to identify the exact static dead-zone**.

## Next step

Checkpoint this revised contract separately, then build a protected resume
executor for the remaining points **11650..11900**.

Do not run another real point before that checkpoint.

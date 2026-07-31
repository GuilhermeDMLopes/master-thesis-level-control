# PI_REAL_RAW_SAFE

## Purpose

`PI_REAL_RAW_SAFE` is an additive 4diac application for the first real-plant PI commissioning run in raw PLC level counts.

It does not replace, rename, or remove any historical communication, PID, PI, MPC, or offline-validation application.

## Validated signal basis

The real PLC publishes `Nivel` as an `INT`/Int16 raw count. No centimetre calibration is currently available.

The application therefore uses:

```text
PROCESS_VARIABLE = raw Nivel counts
SETPOINT = 450 raw counts
```

No division by `1000` is present in this application.

## Control structure

```text
Nivel subscription
    -> LREAL type adapter
    -> PV_FILTER
    -> PI_LEVEL_CONTROLLER
    -> +9000 DAC bias
    -> SAFE_DAC_RATE_LIMITER
    -> LREAL-to-INT
    -> gateway DAC write

biased DAC request
    -> > 0 check
    -> gateway Enable write
```

The PI output is a deviation around a `9000` DAC feedforward bias.

## Current tuned commissioning parameters

```text
SETPOINT = 450.0 raw counts
PROPORTIONAL_GAIN = 8.0 DAC/count
INTEGRAL_GAIN = 0.05 DAC/(count*s)
SAMPLING_TIME_S = 0.1 s

PI OUTPUT_MIN = -9000.0
PI OUTPUT_MAX = 3000.0

DAC bias = 9000.0
final DAC range = 0.0 .. 12000.0
MAX_DELTA_DAC = 150.0 per execution

PV_FILTER ALPHA = 0.98
```

These are conservative real-plant commissioning parameters. Final tuning still depends on the validated experiment.

## Fail-closed startup

The application starts with:

```text
RawPI.MANUAL = TRUE
RawPI.MANUAL_OUTPUT = -9000.0
```

After adding the `9000` bias, the requested DAC is exactly zero. Consequently:

```text
RawEnableWrite = FALSE
RawDACWrite = 0
```

`ResRealRawPI` has no connection from `START.COLD` or `START.WARM`. Initialization must be triggered manually through `RawInitMerge.EI1` after the gateway, FORTE, PLC watchdog, and zero-output state have been validated.

## First commissioning sequence

1. Keep the physical manual stop active.
2. Start and validate the gateway and FORTE.
3. Deploy only `PI_REAL_RAW_SAFE`.
4. Confirm the online values:
   - `RawPI.MANUAL = TRUE`;
   - `RawPI.MANUAL_OUTPUT = -9000.0`;
   - `RawSafeDACLimiter.DAC_OUT = 0`;
   - gateway and PLC requested/applied outputs are zero.
5. Trigger `RawInitMerge.EI1` exactly once.
6. Confirm continued zero output before releasing the physical stop.
7. For the manual fill phase, set `RawPI.MANUAL_OUTPUT = 3000.0`; the bias produces a bounded `12000` DAC request.
8. When the filtered raw level reaches approximately `380` to `400` counts, reduce `RawPI.MANUAL_OUTPUT` to `1500.0`; the bias produces a `10500` DAC request.
9. Switch `RawPI.MANUAL` to `FALSE` only when the filtered raw level is between `420` and `450` counts and the physical stop remains immediately accessible.
10. Abort by setting:
    - `RawPI.MANUAL = TRUE`;
    - `RawPI.MANUAL_OUTPUT = -9000.0`.

The PLC watchdog and gateway boundary limiter remain independent protective layers.

## Not approved by this patch

This patch does not approve:

- automatic deployment or automatic resource start;
- operation without the physical stop available;
- PI gains as final tuned values;
- level interpretation in centimetres;
- MPC commissioning.

# PI Level Controller FORTE Validation

## Validation Date

July 25, 2026.

## Objective

Validate the additive `PI_LEVEL_CONTROLLER` function block in a real 4diac FORTE runtime before integrating it into the simulated or physical level-control loop.

## Validated Artifacts

- IEC 61499 function block: `PI_LEVEL_CONTROLLER.fbt`
- Python reference model: `simulation/pi_level_controller.py`
- FORTE C++ export:
  - `PI_LEVEL_CONTROLLER.h`
  - `PI_LEVEL_CONTROLLER.cpp`
- FORTE runtime built from:
  - source: `C:\Users\guilh\4diac\4diac-forte`
  - build: `C:\Users\guilh\4diac\4diac-forte\build`
- Validation runtime:
  - `C:\Projetos\forte-pi-controller-validation\forte.exe`
  - SHA-256: `C3FA8E12B486FEF6C8846DAFC85A35A1D2A4233EDD5E065E494398494E2E950D`

## Runtime Build Result

The controller C++ source was added to the existing FORTE `utils` module through:

```cmake
forte_add_sourcefile_hcpp(PI_LEVEL_CONTROLLER)
```

CMake configuration and the Debug build completed successfully.

Generated and rebuilt artifacts included:

```text
build/src_gen/PI_LEVEL_CONTROLLER_gen.cpp
build/src/Debug/forte.exe
build/src/Debug/forte-shared.dll
```

The validation runtime started successfully and opened the management interface at:

```text
localhost:61499
```

No startup error related to `PI_LEVEL_CONTROLLER`, missing symbols, DLL loading, or unknown function block types was reported.

## Diagnostic Application

A separate additive application was created:

```text
PI_CONTROLLER_TEST
```

The tested instance was:

```text
ControllerUnderTest : PI_LEVEL_CONTROLLER
```

It was mapped to:

```text
FORTE_PC.Res0.ControllerUnderTest
```

Historical controllers, applications, and mappings were preserved.

## Base Parameters

```text
PROCESS_VARIABLE    = 10.0
SETPOINT            = 14.0
PROPORTIONAL_GAIN   = 4.0
INTEGRAL_GAIN       = 0.5
SAMPLING_TIME_S     = 0.1
OUTPUT_MIN          = 0.0
OUTPUT_MAX          = 100.0
MANUAL              = FALSE
MANUAL_OUTPUT       = 0.0
RESET               = FALSE
```

## Test Results

### Test 1 — First Automatic Cycle

Observed:

```text
ERROR                 = 4.0
PROPORTIONAL_TERM     = 16.0
INTEGRAL_TERM         = 0.2
UNSATURATED_OUTPUT    = 16.2
OUTPUT                = 16.2
SATURATED             = FALSE
MANUAL_ACTIVE         = FALSE
RESET_ACTIVE          = FALSE
CONFIGURATION_VALID   = TRUE
```

Result: **Passed**

### Test 2 — Integral State Persistence

Second cycle observed:

```text
INTEGRAL_TERM         = 0.4
UNSATURATED_OUTPUT    = 16.4
OUTPUT                = 16.4
```

Result: **Passed**

### Test 3 — Upper Saturation Anti-Windup

Inputs:

```text
PROCESS_VARIABLE = 0.0
SETPOINT         = 100.0
```

Two consecutive cycles observed:

```text
ERROR                 = 100.0
PROPORTIONAL_TERM     = 400.0
INTEGRAL_TERM         = 0.4
UNSATURATED_OUTPUT    = 400.4
OUTPUT                = 100.0
SATURATED             = TRUE
CONFIGURATION_VALID   = TRUE
```

The integral term remained at `0.4`.

Result: **Passed**

### Test 4 — Lower Saturation Anti-Windup

Inputs:

```text
PROCESS_VARIABLE = 100.0
SETPOINT         = 0.0
```

Two consecutive cycles observed:

```text
ERROR                 = -100.0
PROPORTIONAL_TERM     = -400.0
INTEGRAL_TERM         = 0.4
UNSATURATED_OUTPUT    = -399.6
OUTPUT                = 0.0
SATURATED             = TRUE
CONFIGURATION_VALID   = TRUE
```

The integral term remained at `0.4`.

Result: **Passed**

### Test 5 — Manual Tracking

Inputs:

```text
PROCESS_VARIABLE = 10.0
SETPOINT         = 14.0
MANUAL           = TRUE
MANUAL_OUTPUT    = 60.0
```

Observed:

```text
OUTPUT                = 60.0
PROPORTIONAL_TERM     = 16.0
INTEGRAL_TERM         = 44.0
UNSATURATED_OUTPUT    = 60.0
SATURATED             = FALSE
MANUAL_ACTIVE         = TRUE
```

Result: **Passed**

### Test 6 — Bumpless Manual-to-Automatic Transfer

On the first automatic cycle after manual mode:

```text
OUTPUT                = 60.0
INTEGRAL_TERM         = 44.0
MANUAL_ACTIVE         = FALSE
```

On the following automatic cycle:

```text
OUTPUT                = 60.2
INTEGRAL_TERM         = 44.2
UNSATURATED_OUTPUT    = 60.2
```

Result: **Passed**

### Test 7 — Deterministic Reset

With `RESET = TRUE`, two consecutive cycles observed:

```text
INTEGRAL_TERM         = 0.0
UNSATURATED_OUTPUT    = 0.0
OUTPUT                = 0.0
RESET_ACTIVE          = TRUE
CONFIGURATION_VALID   = TRUE
```

After setting `RESET = FALSE`:

```text
INTEGRAL_TERM         = 0.2
UNSATURATED_OUTPUT    = 16.2
OUTPUT                = 16.2
RESET_ACTIVE          = FALSE
```

Result: **Passed**

### Test 8 — Invalid Sampling Time

Input:

```text
SAMPLING_TIME_S = 0.0
```

Observed:

```text
OUTPUT                = 0.0
INTEGRAL_TERM         = 0.0
UNSATURATED_OUTPUT    = 0.0
SATURATED             = FALSE
CONFIGURATION_VALID   = FALSE
```

Result: **Passed**

### Test 9 — Invalid Output Limits

Inputs:

```text
SAMPLING_TIME_S = 0.1
OUTPUT_MIN      = 100.0
OUTPUT_MAX      = 100.0
```

Observed:

```text
OUTPUT                = 0.0
INTEGRAL_TERM         = 0.0
UNSATURATED_OUTPUT    = 0.0
CONFIGURATION_VALID   = FALSE
```

Result: **Passed**

### Test 10 — Manual Upper Clamp

Inputs:

```text
OUTPUT_MIN      = 0.0
OUTPUT_MAX      = 100.0
MANUAL          = TRUE
MANUAL_OUTPUT   = 150.0
```

Observed:

```text
OUTPUT                = 100.0
PROPORTIONAL_TERM     = 16.0
INTEGRAL_TERM         = 84.0
UNSATURATED_OUTPUT    = 100.0
SATURATED             = TRUE
MANUAL_ACTIVE         = TRUE
CONFIGURATION_VALID   = TRUE
```

Result: **Passed**

### Test 11 — Manual Lower Clamp

Input:

```text
MANUAL_OUTPUT = -20.0
```

Observed:

```text
OUTPUT                = 0.0
PROPORTIONAL_TERM     = 16.0
INTEGRAL_TERM         = -16.0
UNSATURATED_OUTPUT    = 0.0
SATURATED             = TRUE
MANUAL_ACTIVE         = TRUE
CONFIGURATION_VALID   = TRUE
```

Result: **Passed**

## Validation Summary

| Validation item | Result |
|---|---|
| FORTE C++ generation | Passed |
| FORTE compilation | Passed |
| Runtime startup | Passed |
| Function block type registration | Passed |
| Deployment | Passed |
| ECC event execution | Passed |
| Basic PI calculation | Passed |
| Integral persistence | Passed |
| Upper anti-windup | Passed |
| Lower anti-windup | Passed |
| Manual tracking | Passed |
| Bumpless transfer | Passed |
| Deterministic reset | Passed |
| Invalid configuration handling | Passed |
| Manual output clamping | Passed |

## Notes

During one deployment, historical OPC UA client blocks also attempted to connect to:

```text
opc.tcp://127.0.0.1:4841
```

The gateway was not running, so FORTE reported OPC UA connection failures. These messages were unrelated to `PI_LEVEL_CONTROLLER` and did not affect the isolated numerical validation.

## Conclusion

`PI_LEVEL_CONTROLLER` was successfully generated, compiled, deployed, monitored, and numerically validated in 4diac FORTE.

Its observed runtime behavior matches the Python reference model for the tested cases.

The controller is ready for the next stage: integration into an isolated offline closed-loop application using the simulated level plant. It is not yet approved for direct deployment to the physical plant; DAC scaling, actuator direction, safety interlocks, and laboratory operating limits still require validation.

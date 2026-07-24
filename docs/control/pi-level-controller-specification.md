# PI Level Controller Specification

## Purpose

This document defines the additive IEC 61499 function block:

```text
PI_LEVEL_CONTROLLER
```

The block is the 4diac implementation target for the validated Python reference model in:

```text
simulation/pi_level_controller.py
```

Historical controller blocks and applications must remain unchanged.

## Design Goals

The controller shall provide:

- positional PI control;
- configurable output limits;
- conditional-integration anti-windup;
- clamped manual output;
- manual-output tracking;
- bumpless manual-to-automatic transfer when the process conditions do not change;
- deterministic reset behavior;
- configuration diagnostics;
- controller diagnostics suitable for online monitoring.

Derivative action is intentionally excluded.

## Compatibility Boundary

For valid configurations, the 4diac algorithm shall match the Python reference model.

A valid configuration satisfies:

```text
SAMPLING_TIME_S > 0.0
OUTPUT_MIN < OUTPUT_MAX
```

The Python model raises `ValueError` for an invalid configuration.

The 4diac runtime cannot raise a Python exception. Therefore, the IEC 61499 block shall report:

```text
CONFIGURATION_VALID = FALSE
```

and force a deterministic safe result without executing the normal PI update.

## Function Block Type

```text
PI_LEVEL_CONTROLLER
```

Type:

```text
Basic Function Block
```

## Event Interface

### Event Input

| Event | With variables | Description |
|---|---|---|
| `REQ` | All data inputs | Executes one PI controller cycle |

### Event Output

| Event | With variables | Description |
|---|---|---|
| `CNF` | All data outputs | Confirms completion of the controller cycle |

## Data Inputs

| Name | Type | Description |
|---|---|---|
| `PROCESS_VARIABLE` | `LREAL` | Measured process level in engineering units |
| `SETPOINT` | `LREAL` | Desired process level in engineering units |
| `PROPORTIONAL_GAIN` | `LREAL` | Proportional gain |
| `INTEGRAL_GAIN` | `LREAL` | Integral gain |
| `SAMPLING_TIME_S` | `LREAL` | Controller sampling time in seconds |
| `OUTPUT_MIN` | `LREAL` | Minimum controller output |
| `OUTPUT_MAX` | `LREAL` | Maximum controller output |
| `MANUAL` | `BOOL` | Enables manual mode |
| `MANUAL_OUTPUT` | `LREAL` | Requested output in manual mode |
| `RESET` | `BOOL` | Forces deterministic controller reset behavior |

## Data Outputs

| Name | Type | Description |
|---|---|---|
| `OUTPUT` | `LREAL` | Saturated controller output |
| `ERROR` | `LREAL` | `SETPOINT - PROCESS_VARIABLE` |
| `PROPORTIONAL_TERM` | `LREAL` | Proportional contribution |
| `INTEGRAL_TERM` | `LREAL` | Current stored integral contribution |
| `UNSATURATED_OUTPUT` | `LREAL` | Sum of proportional and integral terms before clamping |
| `SATURATED` | `BOOL` | Indicates output or manual-command clamping |
| `MANUAL_ACTIVE` | `BOOL` | Indicates that the cycle executed in manual mode |
| `RESET_ACTIVE` | `BOOL` | Indicates that reset behavior was executed |
| `CONFIGURATION_VALID` | `BOOL` | Indicates valid sampling time and output limits |

## Internal State

| Name | Type | Initial value | Description |
|---|---|---:|---|
| `integral_term_internal` | `LREAL` | `0.0` | Stored integral contribution |
| `manual_was_active` | `BOOL` | `FALSE` | Tracks the previous operating mode |
| `integral_increment` | `LREAL` | `0.0` | Candidate integral change |
| `candidate_integral` | `LREAL` | `0.0` | Candidate integral state |
| `candidate_unsaturated_output` | `LREAL` | `0.0` | Candidate output used by anti-windup |
| `clamped_manual_output` | `LREAL` | `0.0` | Manual output after limits |

## Priority Order

Each `REQ` cycle shall execute in this order:

```text
1. Calculate ERROR and PROPORTIONAL_TERM
2. Validate configuration
3. Apply RESET when active
4. Apply MANUAL mode when active
5. Otherwise execute automatic PI mode
6. Emit CNF
```

`RESET` has priority over `MANUAL`.

## Common Calculations

For every valid or invalid cycle:

```text
ERROR =
    SETPOINT
    - PROCESS_VARIABLE

PROPORTIONAL_TERM =
    PROPORTIONAL_GAIN
    * ERROR
```

## Configuration Validation

```text
CONFIGURATION_VALID =
    (SAMPLING_TIME_S > 0.0)
    AND
    (OUTPUT_MIN < OUTPUT_MAX)
```

### Invalid Configuration Behavior

When `CONFIGURATION_VALID = FALSE`:

```text
integral_term_internal = 0.0
manual_was_active = FALSE

OUTPUT = 0.0
INTEGRAL_TERM = 0.0
UNSATURATED_OUTPUT = 0.0
SATURATED = FALSE
MANUAL_ACTIVE = FALSE
RESET_ACTIVE = FALSE
```

The application shall not use the output for physical actuation while `CONFIGURATION_VALID = FALSE`.

## Reset Behavior

When `RESET = TRUE` and the configuration is valid:

```text
integral_term_internal = 0.0
manual_was_active = FALSE

OUTPUT =
    clamp(
        0.0,
        OUTPUT_MIN,
        OUTPUT_MAX
    )

INTEGRAL_TERM = 0.0
UNSATURATED_OUTPUT = OUTPUT
SATURATED = FALSE
MANUAL_ACTIVE = MANUAL
RESET_ACTIVE = TRUE
```

Reset is level-sensitive. While `RESET` remains true, every cycle produces the reset result.

## Manual Mode

When `MANUAL = TRUE`, `RESET = FALSE`, and the configuration is valid:

```text
OUTPUT =
    clamp(
        MANUAL_OUTPUT,
        OUTPUT_MIN,
        OUTPUT_MAX
    )

integral_term_internal =
    OUTPUT
    - PROPORTIONAL_TERM

INTEGRAL_TERM =
    integral_term_internal

UNSATURATED_OUTPUT =
    OUTPUT

SATURATED =
    OUTPUT <> MANUAL_OUTPUT

MANUAL_ACTIVE = TRUE
RESET_ACTIVE = FALSE
manual_was_active = TRUE
```

Tracking the manual output aligns the integral contribution with the actual manual command.

## Automatic Mode

When `MANUAL = FALSE`, `RESET = FALSE`, and the configuration is valid:

### First Automatic Cycle After Manual Mode

When `manual_was_active = TRUE`:

```text
manual_was_active = FALSE
```

The integration step is skipped for this cycle.

This preserves the tracked manual output when the proportional term has not changed.

### Normal Integral Candidate

When the previous cycle was not manual:

```text
integral_increment =
    INTEGRAL_GAIN
    * ERROR
    * SAMPLING_TIME_S

candidate_integral =
    integral_term_internal
    + integral_increment

candidate_unsaturated_output =
    PROPORTIONAL_TERM
    + candidate_integral
```

## Conditional Anti-Windup

Integration shall be blocked only when it would increase an existing saturation.

### Upper Saturation Condition

```text
candidate_unsaturated_output > OUTPUT_MAX
AND
integral_increment > 0.0
```

### Lower Saturation Condition

```text
candidate_unsaturated_output < OUTPUT_MIN
AND
integral_increment < 0.0
```

When either condition is true:

```text
integral_term_internal
```

is not updated.

Otherwise:

```text
integral_term_internal =
    candidate_integral
```

This allows the integral contribution to unwind when the error changes direction.

## Automatic Output

After the anti-windup decision:

```text
INTEGRAL_TERM =
    integral_term_internal

UNSATURATED_OUTPUT =
    PROPORTIONAL_TERM
    + INTEGRAL_TERM

OUTPUT =
    clamp(
        UNSATURATED_OUTPUT,
        OUTPUT_MIN,
        OUTPUT_MAX
    )

SATURATED =
    OUTPUT <> UNSATURATED_OUTPUT

MANUAL_ACTIVE = FALSE
RESET_ACTIVE = FALSE
```

## Clamp Definition

```text
clamp(value, minimum, maximum)
```

is defined as:

```text
IF value > maximum:
    maximum
ELSE IF value < minimum:
    minimum
ELSE:
    value
```

## ECC Definition

The Basic Function Block shall use three states:

```text
START
CALCULATE
CONFIRM
```

Transitions:

```text
START
-- REQ -->
CALCULATE

CALCULATE
-- 1 -->
CONFIRM

CONFIRM
-- 1 -->
START
```

Actions:

```text
CALCULATE:
    execute PI_CONTROL_ALGORITHM

CONFIRM:
    emit CNF
```

## Structured Text Pseudocode

```text
ERROR := SETPOINT - PROCESS_VARIABLE;
PROPORTIONAL_TERM := PROPORTIONAL_GAIN * ERROR;

CONFIGURATION_VALID :=
    (SAMPLING_TIME_S > 0.0)
    AND
    (OUTPUT_MIN < OUTPUT_MAX);

IF NOT CONFIGURATION_VALID THEN
    integral_term_internal := 0.0;
    manual_was_active := FALSE;

    OUTPUT := 0.0;
    INTEGRAL_TERM := 0.0;
    UNSATURATED_OUTPUT := 0.0;
    SATURATED := FALSE;
    MANUAL_ACTIVE := FALSE;
    RESET_ACTIVE := FALSE;

ELSIF RESET THEN
    integral_term_internal := 0.0;
    manual_was_active := FALSE;

    OUTPUT := 0.0;

    IF OUTPUT > OUTPUT_MAX THEN
        OUTPUT := OUTPUT_MAX;
    ELSIF OUTPUT < OUTPUT_MIN THEN
        OUTPUT := OUTPUT_MIN;
    END_IF;

    INTEGRAL_TERM := 0.0;
    UNSATURATED_OUTPUT := OUTPUT;
    SATURATED := FALSE;
    MANUAL_ACTIVE := MANUAL;
    RESET_ACTIVE := TRUE;

ELSIF MANUAL THEN
    clamped_manual_output := MANUAL_OUTPUT;

    IF clamped_manual_output > OUTPUT_MAX THEN
        clamped_manual_output := OUTPUT_MAX;
    ELSIF clamped_manual_output < OUTPUT_MIN THEN
        clamped_manual_output := OUTPUT_MIN;
    END_IF;

    OUTPUT := clamped_manual_output;
    integral_term_internal := OUTPUT - PROPORTIONAL_TERM;

    INTEGRAL_TERM := integral_term_internal;
    UNSATURATED_OUTPUT := OUTPUT;
    SATURATED := OUTPUT <> MANUAL_OUTPUT;
    MANUAL_ACTIVE := TRUE;
    RESET_ACTIVE := FALSE;
    manual_was_active := TRUE;

ELSE
    IF manual_was_active THEN
        manual_was_active := FALSE;
    ELSE
        integral_increment :=
            INTEGRAL_GAIN
            * ERROR
            * SAMPLING_TIME_S;

        candidate_integral :=
            integral_term_internal
            + integral_increment;

        candidate_unsaturated_output :=
            PROPORTIONAL_TERM
            + candidate_integral;

        IF NOT (
            (
                candidate_unsaturated_output > OUTPUT_MAX
                AND
                integral_increment > 0.0
            )
            OR
            (
                candidate_unsaturated_output < OUTPUT_MIN
                AND
                integral_increment < 0.0
            )
        ) THEN
            integral_term_internal :=
                candidate_integral;
        END_IF;
    END_IF;

    INTEGRAL_TERM := integral_term_internal;

    UNSATURATED_OUTPUT :=
        PROPORTIONAL_TERM
        + INTEGRAL_TERM;

    OUTPUT := UNSATURATED_OUTPUT;

    IF OUTPUT > OUTPUT_MAX THEN
        OUTPUT := OUTPUT_MAX;
    ELSIF OUTPUT < OUTPUT_MIN THEN
        OUTPUT := OUTPUT_MIN;
    END_IF;

    SATURATED := OUTPUT <> UNSATURATED_OUTPUT;
    MANUAL_ACTIVE := FALSE;
    RESET_ACTIVE := FALSE;
END_IF;
```

## Initial Application Parameters

The first offline 4diac test application shall use:

```text
SETPOINT = 14.0
PROPORTIONAL_GAIN = 4.0
INTEGRAL_GAIN = 0.5
SAMPLING_TIME_S = 0.1
OUTPUT_MIN = 0.0
OUTPUT_MAX = 100.0
MANUAL = FALSE
MANUAL_OUTPUT = 0.0
RESET = FALSE
```

These values preserve the current tuning for comparison. They do not constitute final laboratory tuning.

## Output Scaling Boundary

`PI_LEVEL_CONTROLLER.OUTPUT` is a percentage-like command in the configured output interval.

The controller block shall not convert directly to DAC counts.

DAC scaling and DAC rate limiting remain external to the controller so they can be tested and diagnosed independently.

## Historical Preservation

The following artifacts shall remain unchanged:

```text
PID_LEVEL.fbt
PID
PID_1
historical applications
historical mappings
```

The new block is additive:

```text
PI_LEVEL_CONTROLLER.fbt
```

## Acceptance Criteria

The 4diac implementation is acceptable when:

- all interface names and comments are in English;
- historical artifacts remain unchanged;
- the block imports without 4diac Problems errors;
- one `REQ` produces one `CNF`;
- valid automatic cycles match the Python reference model;
- upper and lower anti-windup behavior matches the Python tests;
- manual output is clamped and tracked;
- the first automatic cycle after manual mode is bumpless under unchanged conditions;
- reset produces the defined output;
- invalid configuration sets `CONFIGURATION_VALID = FALSE`;
- diagnostics are observable online.

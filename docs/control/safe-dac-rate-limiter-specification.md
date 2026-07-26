# Safe DAC Rate Limiter Specification

## Purpose

`SAFE_DAC_RATE_LIMITER` is an additive replacement candidate for the
historical `DAC_RATE_LIMITER`.

The historical block must remain unchanged for traceability.

The new block removes the unsafe startup behavior where the first execution
copies `DAC_IN` directly to `DAC_OUT` and bypasses both the configured rate
limit and the configured output bounds.

## Safety Objective

The first output must be deterministic and independent of the current input:

```text
first execution:
    DAC_OUT = clamp(INITIAL_DAC, DAC_MIN, DAC_MAX)
```

On later executions, the output may move toward the bounded input by no more
than `MAX_DELTA_DAC` per execution:

```text
requested_dac = clamp(DAC_IN, DAC_MIN, DAC_MAX)

delta = requested_dac - previous_dac

DAC_OUT =
    previous_dac + clamp(
        delta,
        -MAX_DELTA_DAC,
        MAX_DELTA_DAC
    )
```

The resulting output must always remain inside the configured bounds.

## Proposed 4diac Interface

### Event input

```text
REQ
```

`REQ` executes one limiter cycle.

### Event output

```text
CNF
```

`CNF` is emitted after the outputs have been updated.

### Data inputs

```text
DAC_IN               : LREAL
MAX_DELTA_DAC        : LREAL
DAC_MIN              : LREAL
DAC_MAX              : LREAL
INITIAL_DAC          : LREAL
RESET                : BOOL
```

### Data outputs

```text
DAC_OUT              : LREAL
LIMITED              : BOOL
INITIALIZED          : BOOL
RESET_ACTIVE         : BOOL
CONFIGURATION_VALID  : BOOL
```

## Configuration Rules

A configuration is valid when:

```text
MAX_DELTA_DAC > 0.0
DAC_MIN < DAC_MAX
```

`INITIAL_DAC` does not make the configuration invalid. It is clamped to the
configured output interval.

If the configuration is invalid:

```text
DAC_OUT = 0.0
LIMITED = TRUE
INITIALIZED = FALSE
RESET_ACTIVE = FALSE
CONFIGURATION_VALID = FALSE
```

The physical command path must also use `Enable = FALSE` as the independent
safe-state mechanism.

## Initialization Behavior

Before the first valid execution, the internal state is uninitialized.

On the first valid execution:

```text
DAC_OUT = clamp(INITIAL_DAC, DAC_MIN, DAC_MAX)
INITIALIZED = TRUE
RESET_ACTIVE = FALSE
```

The block does not move toward `DAC_IN` during this execution.

For the initial offline integration:

```text
INITIAL_DAC = 0.0
```

With:

```text
MAX_DELTA_DAC = 150.0
DAC_MIN = 0.0
DAC_MAX = 32000.0
```

and an initial requested input of `9084`, the expected sequence is:

```text
0
150
300
450
...
```

## Normal Operation

After initialization:

1. Clamp `DAC_IN` to `[DAC_MIN, DAC_MAX]`.
2. Calculate the difference from the previous output.
3. Limit that difference to `[-MAX_DELTA_DAC, MAX_DELTA_DAC]`.
4. Apply the limited difference.
5. Clamp the final output to `[DAC_MIN, DAC_MAX]`.
6. Store the final output as the state for the next execution.

`LIMITED` is true whenever `DAC_OUT` differs from the original `DAC_IN`,
including rate limiting and boundary clamping.

## Reset Behavior

When `RESET = TRUE` with a valid configuration:

```text
DAC_OUT = clamp(INITIAL_DAC, DAC_MIN, DAC_MAX)
INITIALIZED = TRUE
RESET_ACTIVE = TRUE
```

Reset is level-sensitive and deterministic. Repeated reset cycles keep the same
output.

After `RESET` returns to false, the next cycle ramps from the reset output
toward the current bounded input.

## Historical Preservation

The following artifacts must not be modified by this implementation:

```text
DAC_RATE_LIMITER.fbt
PID
PID_1
PI_OFFLINE_CLOSED_LOOP
historical mappings
offline-pi-v1
```

The first implementation stage adds only:

```text
simulation/safe_dac_rate_limiter.py
tests/test_safe_dac_rate_limiter.py
docs/control/safe-dac-rate-limiter-specification.md
```

The 4diac block and diagnostic application will be added in later commits.

## Acceptance Criteria

The reference implementation is accepted when:

- the first valid execution returns the bounded `INITIAL_DAC`;
- the first execution never copies a nonzero `DAC_IN` directly to the output;
- each later output change is no greater than `MAX_DELTA_DAC`;
- upward and downward limiting are symmetric;
- input and output bounds are always respected;
- reset returns immediately to the bounded initial value;
- release from reset ramps from the reset value;
- invalid configurations are rejected by the Python model;
- all new names, comments, tests, and documentation are in English;
- historical artifacts remain unchanged.

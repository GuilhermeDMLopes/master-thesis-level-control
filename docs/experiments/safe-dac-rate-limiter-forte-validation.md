# SAFE_DAC_RATE_LIMITER FORTE Runtime Validation

## Objective

This experiment validates `SAFE_DAC_RATE_LIMITER` as a compiled IEC 61499
function block running in FORTE.

The validation verifies deterministic startup, symmetric rate limiting,
deterministic reset, output bounds, invalid-configuration behavior, and
diagnostic outputs.

The historical `DAC_RATE_LIMITER` was not modified.

## Source Version

```text
Branch: feature/safe-dac-rate-limiter
Source commit: 2a7f429
```

The validated function block is:

```text
SAFE_DAC_RATE_LIMITER.fbt
```

The reference implementation and automated tests were introduced in:

```text
0d37609 feat: add safe DAC rate limiter reference model
```

The IEC 61499 function block was introduced in:

```text
2a7f429 feat: add safe DAC rate limiter function block
```

## Runtime Build

The function block was exported using:

```text
4diac IDE Type Export
Exporter: FORTE 1.x NG
```

The external FORTE module was enabled with:

```text
FORTE_MODULE_EXTERNAL_SAFE_DAC_RATE_LIMITER=ON
```

The isolated runtime directory was:

```text
C:\Projetos\forte-safe-dac-rate-limiter-validation
```

The runtime used the management endpoint:

```text
localhost:61499
```

### Runtime Hashes

```text
forte.exe
SHA-256:
AD1F5DFE4203C75B89789F0A95927210A6A7190AACA596018F0CCBE230EC04A1

forte-shared.dll
SHA-256:
BCCD18412EC3BCF14BF2CBAF19481E6FA8A8A1771291FA47692FDC4E90B77F29

open62541.dll
SHA-256:
452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318
```

## Temporary 4diac System

A temporary project outside the repository was used:

```text
Project:
SAFE_DAC_RATE_LIMITER_RUNTIME_VALIDATION

System:
SAFE_DAC_RATE_LIMITER_VALIDATION

Application:
SAFE_DAC_RATE_LIMITER_TEST

Device:
FORTE_PC

Resource:
Res0

Function block instance:
LimiterUnderTest
```

The instance was mapped as:

```text
SAFE_DAC_RATE_LIMITER_TEST.LimiterUnderTest
->
FORTE_PC.Res0.LimiterUnderTest
```

No automatic event source was connected. Each `REQ` event was triggered
manually during online monitoring.

## Base Configuration

```text
DAC_IN          = 9084.0
MAX_DELTA_DAC   = 150.0
DAC_MIN         = 0.0
DAC_MAX         = 32000.0
INITIAL_DAC     = 0.0
RESET           = FALSE
```

## Deterministic Startup and Upward Ramp

The following sequence was observed:

| REQ | CNF | DAC_OUT | LIMITED | INITIALIZED |
|---:|---:|---:|---|---|
| 1 | 1 | 0 | TRUE | TRUE |
| 2 | 2 | 150 | TRUE | TRUE |
| 3 | 3 | 300 | TRUE | TRUE |
| 4 | 4 | 450 | TRUE | TRUE |
| 5 | 5 | 600 | TRUE | TRUE |
| 6 | 6 | 750 | TRUE | TRUE |
| 7 | 7 | 900 | TRUE | TRUE |

The first cycle returned `INITIAL_DAC` instead of copying the requested
`DAC_IN`.

This removes the historical startup transition:

```text
0 -> 9084
```

The safe sequence begins with:

```text
0 -> 150 -> 300 -> 450 -> ...
```

## Reachable Input

Starting from:

```text
DAC_OUT = 900
DAC_IN = 1000
```

one execution produced:

```text
DAC_OUT = 1000
LIMITED = FALSE
```

The input was reachable because the requested change was smaller than
`MAX_DELTA_DAC`.

## Downward Ramp

With `DAC_IN = 0`, the following sequence was observed:

```text
850
700
550
400
250
100
0
```

Each limited cycle changed by `-150`.

At the final value:

```text
DAC_OUT = 0
LIMITED = FALSE
```

## Deterministic Reset

With:

```text
DAC_IN = 9084
INITIAL_DAC = 500
RESET = TRUE
```

repeated executions produced:

```text
DAC_OUT = 500
RESET_ACTIVE = TRUE
```

After changing only:

```text
RESET = FALSE
```

the next execution produced:

```text
DAC_OUT = 650
RESET_ACTIVE = FALSE
```

This confirms that normal rate limiting resumes from the reset state.

## Initial-Value Bounds

With:

```text
INITIAL_DAC = 40000
RESET = TRUE
```

the result was:

```text
DAC_OUT = 32000
```

With:

```text
INITIAL_DAC = -100
RESET = TRUE
```

the result was:

```text
DAC_OUT = 0
```

The startup and reset value is therefore constrained to the configured
physical output interval.

## Invalid Configuration

With:

```text
MAX_DELTA_DAC = 0
RESET = FALSE
```

the result was:

```text
DAC_OUT = 0
LIMITED = TRUE
INITIALIZED = FALSE
RESET_ACTIVE = FALSE
CONFIGURATION_VALID = FALSE
```

This is the defined safe diagnostic state.

## Recovery After Invalid Configuration

After restoring:

```text
MAX_DELTA_DAC = 150
INITIAL_DAC = 0
DAC_IN = 9084
```

the first valid execution produced:

```text
DAC_OUT = 0
INITIALIZED = TRUE
CONFIGURATION_VALID = TRUE
```

The following execution produced:

```text
DAC_OUT = 150
```

This confirms deterministic reinitialization after invalid configuration.

## Event Semantics

For every manually triggered cycle:

```text
REQ count = CNF count
```

One `REQ` produced exactly one `CNF`.

## Runtime Log

The runtime log was checked for:

```text
ERROR:
unknown type
could not be loaded
failed to load
entry point
unresolved external
DLL not found
```

Result:

```text
Unexpected runtime issues: 0
```

## Automated Tests

Before runtime validation, the complete repository test suite reported:

```text
112 passed
```

The automated tests include:

- Python reference-model behavior;
- deterministic initialization;
- upward and downward limiting;
- output bounds;
- reset behavior;
- invalid-configuration rejection;
- IEC 61499 XML structure;
- interface and WITH associations;
- ECC structure;
- English names and comments.

## Conclusion

`SAFE_DAC_RATE_LIMITER` was successfully exported, compiled, deployed, and
executed in FORTE.

The function block satisfies the required runtime behaviors:

- deterministic startup at `INITIAL_DAC`;
- no uncontrolled first-cycle jump;
- symmetric upward and downward rate limiting;
- bounded startup, reset, and normal outputs;
- deterministic reset;
- controlled release from reset;
- explicit invalid-configuration diagnostics;
- deterministic recovery after invalid configuration;
- one confirmation event for each request event.

The historical `DAC_RATE_LIMITER` and the validated `PI_OFFLINE_CLOSED_LOOP`
baseline remain unchanged.

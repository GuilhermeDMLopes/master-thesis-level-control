# Current PI Controller Analysis

## Scope

This document analyzes the current level controller and its active 4diac signal chain without modifying any historical application or function block.

Analyzed sources:

- `PID_LEVEL.fbt`;
- `PV_FILTER.fbt`;
- `DAC_RATE_LIMITER.fbt`;
- `OPAS_Tank_System.sys`;
- `gateway_config.py`;
- the generated 4diac inventory;
- source hashes recorded at commit `c2f25c823a8e7b5aa7042971a34d4baf4b71980e`.

## Current Active Control Chain

The mapped controller path associated with `PID_1` is:

```text
Gateway NodeId Nivel
-> NivelReadPID_1
-> NivelTypePID_1
-> NivelScalePID_1
-> PV_FILTERPID_1
-> PID_1
-> MVScaleDiv
-> DACScaleMul_1
-> DAC_RATE_LIMITER_1
-> DACTypePID_1
-> DACWritePID_1
```

The Enable command path is:

```text
PID_1.MV
-> EnableCheck_1
-> EnableWritePID_1
```

The active blocks are mapped to:

```text
FORTE_PC.Res0
```

## Current Parameters

| Element | Parameter | Value |
|---|---|---:|
| Cycle | `DT` | `100 ms` |
| Level scaling | divisor | `1000.0` |
| PV filter | `ALPHA` | `0.95` |
| Controller | `SP` | `14.0 cm` |
| Controller | `KP` | `4.0` |
| Controller | `KI` | `0.50` |
| Controller | `KD` | `0.0` |
| Controller | `TS` | `0.100 s` |
| Controller | `MANUAL` | `FALSE` |
| Controller | `MAN_OUT` | `0.0` |
| Controller | `RESET` | `FALSE` |
| Output scaling | divide by | `10.0` |
| DAC scaling | multiply by | `3276.7` |
| DAC limiter | `MAX_DELTA_DAC` | `150.0` |
| DAC limiter | `DAC_MIN` | `0.0` |
| DAC limiter | `DAC_MAX` | `32767.0` |
| Enable threshold | `MV >` | `1.0` |

The controller is currently a PI controller because `KD = 0.0`.

## Current Discrete Controller Equation

For automatic operation, the implemented algorithm is:

```text
error[k] = setpoint[k] - process_variable[k]

integral_accumulator[k] =
    integral_accumulator[k - 1]
    + error[k] * sampling_time

proportional_term[k] =
    proportional_gain * error[k]

integral_term[k] =
    integral_gain * integral_accumulator[k]

derivative_term[k] =
    derivative_gain
    * (error[k] - error[k - 1])
    / sampling_time

unsaturated_output[k] =
    proportional_term[k]
    + integral_term[k]
    + derivative_term[k]

controller_output[k] =
    clamp(unsaturated_output[k], 0.0, 100.0)
```

The error from the current cycle is stored for the next derivative calculation.

## ECC Behavior

The controller ECC contains three states:

```text
START
-> CALC
-> DONE
-> START
```

A `REQ` event executes the algorithm and a `CNF` event publishes:

- `MV`;
- `ERR`;
- `P_TERM`;
- `I_TERM`;
- `D_TERM`.

The ECC structure is deterministic and appropriate for one controller calculation per `REQ`.

## Correct or Consistent Aspects

### Sampling-time consistency

The application cycle is configured as `100 ms` and the controller sampling time is configured as `0.100 s`.

This is internally consistent.

### Level conversion consistency

The 4diac application divides the raw level by `1000.0`.

The gateway metadata uses the same provisional scale:

```text
level_cm = raw_level / 1000.0
```

### Current PI configuration

`KD = 0.0`, so the derivative term does not affect the current controller output.

### Signal order

The current order is logically coherent:

```text
raw level
-> engineering-unit conversion
-> process-variable filter
-> PI controller
-> output scaling
-> DAC rate limiter
-> integer conversion
-> OPC UA write
```

## Main Controller Defects

## 1. No Anti-Windup

The integral accumulator is updated on every automatic cycle, including when the output is saturated at `0.0` or `100.0`.

There is no conditional integration, back-calculation, integral clamping, or tracking mechanism.

Consequences:

- the integral can continue increasing while the actuator is already at maximum output;
- the integral can continue decreasing while the actuator is already at minimum output;
- recovery after saturation can be very slow;
- overshoot can increase after a prolonged large error.

Example using the current parameters and a constant positive error of `4 cm`:

```text
P term = 4.0 * 4.0 = 16.0

I-term increase per 100 ms cycle =
    0.50 * 4.0 * 0.100
    = 0.20
```

The unsaturated output reaches `100%` after approximately `42 s`, but the integral continues increasing after that point.

## 2. Manual-to-Automatic Transfer Is Not Bumpless

In manual mode:

- `MV` follows the clamped `MAN_OUT`;
- the integral accumulator is frozen;
- the previous error is frozen;
- `P_TERM`, `I_TERM`, and `D_TERM` are forced to zero.

When automatic mode resumes, the output is immediately recalculated from the old integral state and the current error.

Consequences:

- the output can jump when switching from manual to automatic;
- the stored integral may not correspond to the manual output;
- a derivative kick can occur if `KD` is later enabled.

## 3. Reset Does Not Produce a Safe Defined Output

When `RESET = TRUE`, the algorithm clears:

```text
integral_accumulator = 0
previous_error = 0
```

The same cycle then continues into manual or automatic calculation.

In automatic mode, reset therefore does not force the output to zero. It immediately:

- calculates the current error;
- adds one new integral increment;
- calculates a new controller output.

If `RESET` remains true, this behavior repeats every cycle.

Consequences:

- reset behaves as a continuous level input rather than a one-shot state initialization;
- reset does not guarantee a safe actuator command;
- the post-reset output is not explicitly defined.

## 4. Sampling Time Is Not Validated

The derivative expression divides by `TS`.

There is no protection against:

```text
TS <= 0
```

Even with `KD = 0`, the division expression may still be evaluated before multiplication, depending on runtime behavior.

A zero or invalid sampling time can therefore cause a runtime calculation fault.

## 5. Fixed Output Limits

The output limits are hard-coded:

```text
0.0 to 100.0
```

They are not exposed as controller inputs.

This makes reuse and testing less explicit and prevents the controller from reporting or adapting to a different command range.

## 6. Insufficient Diagnostics

The block exposes the P, I, and D terms, but it does not expose:

- unsaturated output;
- saturation state;
- integral accumulator;
- automatic/manual tracking state;
- reset state;
- anti-windup activity.

These signals are important for diagnosing a controller that appears unresponsive or remains saturated.

## Active-Chain Issues Outside the PI Algorithm

## 7. DAC Range Mismatch

The 4diac chain scales `100%` to:

```text
100 / 10 * 3276.7 = 32767
```

The 4diac DAC limiter also uses:

```text
DAC_MAX = 32767
```

The gateway configuration and experiment metadata use:

```text
DAC_MAX = 32000
DAC_LIMITER_MAX = 32000
```

This creates two different definitions of full scale.

Consequences:

- a `100%` controller output can command `32767`;
- gateway percentage calculations treat `32000` as `100%`;
- the top `767` DAC counts are inconsistent with gateway metadata;
- the 4diac maximum is approximately `2.40%` above the gateway maximum.

This range must be resolved before laboratory operation.

## 8. Strong PV Filter Lag

The PV filter uses:

```text
alpha = 0.95
sample time = 0.1 s
```

The approximate equivalent first-order time constant is:

```text
1.95 s
```

This is a significant delay for a feedback controller and must be considered during tuning.

The filter is not necessarily incorrect, but it can make the loop appear slow and can increase overshoot when combined with integral action.

## 9. Very Restrictive DAC Rate Limit

The DAC limiter permits:

```text
150 DAC counts per 100 ms
```

Equivalent rate:

```text
1500 DAC counts per second
```

At a nominal full scale of `32000`, a complete zero-to-full-scale ramp requires approximately:

```text
21.3 s
```

At `32767`, it requires approximately:

```text
21.8 s
```

This may be intentional for actuator protection, but it can dominate the closed-loop response and cause the PI integral to wind up while the actuator command is still ramping.

## 10. Enable Dead Zone

The Enable command is generated by:

```text
Enable = controller_output > 1.0
```

Therefore:

- outputs from `0.0%` through `1.0%` disable the actuator;
- the DAC command can still be nonzero while Enable is false;
- the closed loop contains an additional dead zone not represented inside the PI block.

This behavior must be confirmed against the real PLC and actuator semantics.

## Additional Block Observations

### PV filter

The filter correctly clamps `ALPHA` to `[0, 1]`.

On its first execution, it initializes its output directly from the current input, avoiding a startup transient from zero.

### DAC rate limiter

The normal limiting branch applies both rate limiting and output bounds.

However, the initialization and reset branches copy `DAC_IN` directly to `DAC_OUT` without applying `DAC_MIN` or `DAC_MAX`.

Consequences:

- the first output can bypass rate limiting;
- reset can create an immediate output step;
- an out-of-range input can bypass the configured limits during initialization or reset.

## Likely Reasons the Physical Loop May Not Behave as Expected

The most likely combined causes are:

1. integral windup during actuator saturation or rate limiting;
2. approximately two seconds of PV filter lag;
3. approximately twenty-one seconds for a full DAC ramp;
4. inconsistent DAC full-scale values (`32000` versus `32767`);
5. the Enable dead zone at `1%`;
6. non-bumpless transitions and ambiguous reset behavior;
7. unvalidated physical scaling and control direction.

The current PI equation alone is not necessarily the only source of poor behavior. The complete signal chain must be validated.

## Recommended Additive Controller

Historical blocks must remain unchanged.

Create a new block:

```text
PI_LEVEL_CONTROLLER
```

The new block should be a PI controller rather than a PID controller because derivative action is not currently required.

Recommended inputs:

```text
PV
SP
KP
KI
TS
OUTPUT_MIN
OUTPUT_MAX
MANUAL
MANUAL_OUTPUT
RESET
```

Recommended outputs:

```text
OUTPUT
ERROR
P_TERM
I_TERM
UNSATURATED_OUTPUT
SATURATED
MANUAL_ACTIVE
```

Recommended internal behavior:

- validate `TS > 0`;
- clamp output limits consistently;
- use conditional integration or back-calculation anti-windup;
- track manual output for bumpless transfer;
- define reset output explicitly;
- expose the unsaturated output and saturation state;
- keep all new names, comments, and documentation in English.

## Recommended Implementation Order

1. Create a Python reference implementation of the new PI algorithm.
2. Add offline tests for:
   - proportional response;
   - integral accumulation;
   - upper saturation;
   - lower saturation;
   - anti-windup;
   - manual output clamping;
   - bumpless manual-to-automatic transfer;
   - reset behavior;
   - invalid sampling time.
3. Create `PI_LEVEL_CONTROLLER.fbt` as a new additive 4diac block.
4. Create a separate diagnostic application using the new controller.
5. Keep `PID_LEVEL.fbt`, `PID`, `PID_1`, and all historical mappings unchanged.
6. Resolve the DAC maximum before commanding the real PLC.
7. Test the complete loop with the simulator before laboratory deployment.

## Conclusion

The current controller executes a mathematically recognizable positional PI algorithm, and its configured sampling time matches the application cycle.

However, it is not ready for reliable closed-loop laboratory operation because it lacks anti-windup and bumpless transfer, has ambiguous reset behavior, and operates inside a signal chain with significant filtering, restrictive rate limiting, a DAC range mismatch, and an Enable dead zone.

The next implementation should be additive and should focus first on a testable PI reference algorithm with explicit safety and diagnostic behavior.

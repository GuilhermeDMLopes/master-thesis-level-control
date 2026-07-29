# Gateway and PLC Watchdog Integration Validation

## Validation date

July 29, 2026.

## Objective

Validate the integration between the Python OPC UA gateway and the communication watchdog implemented in the real B&R PLC.

The validation was performed before connecting FORTE or executing the PI controller.

## Validated architecture

```text
Python gateway
    |
    | OPC UA client
    | Heartbeat and SafetyReset
    v
B&R PLC watchdog
    |
    | AppliedEnable and AppliedDAC
    v
Physical output mapping
```

The gateway also operated as an OPC UA server on port `4841`, but no FORTE application was connected during this validation.

## Automated tests

The complete repository test suite passed after the watchdog integration and compatibility correction:

```text
145 passed
```

## Zero-output startup

The gateway was started against the real PLC endpoint:

```text
opc.tcp://10.0.0.3:4840
```

The gateway server was exposed at:

```text
opc.tcp://0.0.0.0:4841
```

Twelve distinct heartbeat values were observed.

The state remained:

```text
Enable=False
DAC=0
WatchdogHealthy=True
WatchdogTripped=False
AppliedEnable=False
AppliedDAC=0
```

Result: passed.

## Abrupt gateway loss

The gateway process was forcibly terminated while all commands and applied outputs were zero.

The last heartbeat value was `1768`.

The PLC watchdog entered the safe trip state after:

```text
1.031 s
```

Final state:

```text
Enable=False
DAC=0
WatchdogHealthy=False
WatchdogTripped=True
AppliedEnable=False
AppliedDAC=0
```

Result: passed.

## Restart from trip

The gateway was restarted while the PLC watchdog was latched in the trip state.

The gateway:

1. forced `Enable=False`;
2. forced `DAC=0`;
3. started the heartbeat;
4. applied the controlled `SafetyReset` pulse;
5. waited for a healthy watchdog state.

Fifteen distinct heartbeat values were observed after recovery.

No old command was reused and no physical output was released.

Result: passed.

## Graceful gateway shutdown

The gateway was stopped with `Ctrl+C`.

The shutdown path reported:

```text
Gateway stopped by the user.
Final safe PLC commands were written.
CSV file closed.
Disconnected from the B&R OPC UA server.
```

After shutdown:

```text
Gateway process count=0
Gateway port 4841 listening=False
Heartbeat stopped
WatchdogHealthy=False
WatchdogTripped=True
Enable=False
DAC=0
AppliedEnable=False
AppliedDAC=0
```

Five consecutive PLC samples contained the same heartbeat value, `3741`.

Result: passed.

## Non-blocking shutdown warning

The following warning was emitted by `asyncua` during the `Ctrl+C` cancellation sequence:

```text
RuntimeWarning: coroutine 'Client.check_connection' was never awaited
```

This warning did not prevent:

- the final safe PLC writes;
- closure of the gateway CSV;
- closure of the internal OPC UA server;
- closure of the PLC OPC UA session and SecureChannel;
- closure of the socket;
- transition of the PLC watchdog to the safe trip state.

It is recorded as a non-blocking technical issue for later cleanup.

## Acceptance criteria

| Criterion | Result |
|---|---|
| Safe gateway startup | Passed |
| Periodic PLC heartbeat | Passed |
| Controlled SafetyReset | Passed |
| Watchdog telemetry publication | Passed |
| Zero command before watchdog release | Passed |
| Abrupt-loss trip | Passed |
| Restart from trip | Passed |
| Graceful-shutdown trip | Passed |
| Applied outputs remain zero | Passed |
| Full automated test suite | Passed |

## Limitations

This validation did not include:

- FORTE;
- a deployed 4diac application;
- positive DAC commands through the gateway;
- PI closed-loop control;
- level-sensor calibration.

## Conclusion

The Python gateway and the real PLC watchdog were successfully integrated and validated in a fail-closed zero-output configuration.

The integration is ready for a communication-only FORTE validation. It is not yet approved for PI closed-loop execution.

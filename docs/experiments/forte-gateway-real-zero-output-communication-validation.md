# Real FORTE and Gateway Zero-Output Communication Validation

## Validation date

July 29, 2026.

## Objective

Validate the complete communication path from the 4diac communication-only application through FORTE and the Python OPC UA gateway to the real B&R PLC, while maintaining zero requested and applied output.

## Validated path

```text
4diac GATEWAY_COMM_TEST
    |
    v
FORTE runtime
    |
    | OPC UA client
    v
Python gateway at opc.tcp://127.0.0.1:4841
    |
    | OPC UA client and watchdog heartbeat
    v
Real B&R PLC at opc.tcp://10.0.0.3:4840
```

## Software checkpoint

```text
Branch: feature/gateway-plc-watchdog-integration
Commit before validation: 364d7c50d4ede3b0efd43b5702078ecfad65c1b4
FORTE executable SHA256:
3D0C115C256844ACC243CF46E29109E7E0EFA0F52DC6D2ED2D734FED08430FE3
```

## Initial safe state

Before starting the stack:

```text
Enable=False
DAC=0
SafetyReset=False
WatchdogHealthy=False
WatchdogTripped=True
AppliedEnable=False
AppliedDAC=0
```

Gateway port `4841` and FORTE management port `61499` were closed.

## Managed stack startup

The real gateway was started as process `4728`.

The startup monitor explicitly observed the controlled reset transient:

```text
Initial watchdog state:
WatchdogHealthy=False
WatchdogTripped=True

Controlled reset pulse:
SafetyReset=True
WatchdogHealthy=True
WatchdogTripped=False

Stable released state:
SafetyReset=False
WatchdogHealthy=True
WatchdogTripped=False
```

Eight consecutive stable samples were required before FORTE was started.

Eight distinct heartbeat values were observed during the startup acceptance window.

The validated FORTE runtime was then started as process `31736`, with port `61499` listening.

## 4diac deployment scope

Only `GATEWAY_COMM_TEST` was deployed.

The command constants remained:

```text
CommTestEnableCommand.IN = FALSE
CommTestDACCommand.IN = 0
```

No PI application was deployed.

No positive DAC command was requested.

## Post-deployment communication validation

Twenty consecutive samples were collected after deployment.

During every sample:

```text
WatchdogHealthy=True
WatchdogTripped=False
Enable=False
DAC=0
AppliedEnable=False
AppliedDAC=0
```

Twenty distinct heartbeat values were observed.

The gateway level value followed the real PLC input. Small one-sample differences between direct PLC and gateway reads were consistent with asynchronous acquisition times.

## FORTE communication evidence

The FORTE logs confirmed:

```text
Unexpected issue lines: 0
Gateway endpoint found: True
FORTE client connection found: True
Subscription creation lines: 1
CommTest monitoring lines: 3
```

The three monitored communication items corresponded to the communication-only read path.

## Controlled shutdown

FORTE was stopped first and the gateway second.

After shutdown:

```text
Port 4841 listening=False
Port 61499 listening=False
Heartbeat=4581 and no longer changing
WatchdogHealthy=False
WatchdogTripped=True
Enable=False
DAC=0
AppliedEnable=False
AppliedDAC=0
```

Five consecutive PLC samples contained the same heartbeat value.

Result: passed.

## Acceptance criteria

| Criterion | Result |
|---|---|
| Validated FORTE binary used | Passed |
| Gateway connected to the real PLC | Passed |
| Watchdog recovered through controlled reset | Passed |
| SafetyReset returned to false | Passed |
| Heartbeat remained active | Passed |
| GATEWAY_COMM_TEST deployed alone | Passed |
| FORTE connected to gateway endpoint | Passed |
| OPC UA subscription created | Passed |
| Three communication items monitored | Passed |
| Requested Enable remained false | Passed |
| Requested DAC remained zero | Passed |
| AppliedEnable remained false | Passed |
| AppliedDAC remained zero | Passed |
| Controlled stack stop | Passed |
| Final PLC safe trip state | Passed |

## Limitations

This checkpoint does not approve:

- positive DAC commands;
- physical pump actuation;
- PI closed-loop control;
- conversion of raw level counts to centimetres;
- level-sensor calibration;
- MPC execution.

## Conclusion

The real communication chain `4diac -> FORTE -> gateway -> B&R PLC` was validated in a fail-closed zero-output state.

This checkpoint is ready to be merged and tagged before any positive-output commissioning test.

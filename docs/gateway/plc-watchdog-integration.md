# PLC Watchdog Integration in the Python Gateway

## Validated PLC Safety Contract

The real PLC watchdog was validated with the physical plant before gateway
integration.

Observed behavior:

```text
PLC task period: 100 ms
watchdog timeout setting: 10 cycles
measured physical trip: 1.094 s
```

With `Enable=True` and `DAC=12000`, heartbeat loss produced:

```text
WatchdogHealthy=False
WatchdogTripped=True
AppliedEnable=False
AppliedDAC=0
```

The pump sound and water flow stopped at the watchdog trip.

## Gateway Responsibilities

The Python gateway must:

- force safe PLC commands before arming the watchdog;
- maintain the UDINT Heartbeat at 200 ms;
- pulse SafetyReset only while `Enable=False` and `DAC=0`;
- block FORTE commands until the watchdog is healthy;
- publish watchdog and applied-output diagnostics;
- discard commands written while the PLC is disconnected;
- repeat the safe handshake after reconnection;
- attempt safe writes during normal process shutdown;
- rely on the independent PLC timeout if communication prevents those writes.

## Startup State Machine

```text
DISCONNECTED
    |
    v
CONNECTING
    |
    v
FORCE_SAFE_COMMANDS
    |
    v
START_HEARTBEAT
    |
    v
PULSE_SAFETY_RESET
    |
    v
WAIT_HEALTHY_AND_ZERO_APPLIED_OUTPUTS
    |
    v
COMMANDS_PERMITTED
```

Any failure returns the gateway to a disconnected, fail-closed state.

## SafetyReset Rule

The gateway may pulse `SafetyReset` only after explicitly writing:

```text
Enable=False
DAC=0
SafetyReset=False
```

It then confirms:

```text
WatchdogHealthy=True
WatchdogTripped=False
AppliedEnable=False
AppliedDAC=0
```

## Runtime Rule

Commands are permitted only when:

```text
WatchdogHealthy and not WatchdogTripped
```

If this condition becomes false, the gateway:

1. clears its writable command nodes;
2. forces safe PLC commands;
3. performs a new safe watchdog handshake;
4. keeps FORTE commands discarded during the handshake.

## Reconnection Rule

A fresh OPC UA client is created for each attempt. No offline command is
replayed. The reconnection is successful only after the watchdog handshake
passes.

## Shutdown Rule

On gateway shutdown, the process attempts:

```text
Enable=False
DAC=0
SafetyReset=False
```

If communication is already unavailable, the PLC watchdog trips independently
after approximately one second.

## Acceptance Criteria

- automated gateway tests pass;
- gateway starts with `Enable=False` and `DAC=0`;
- gateway-exposed watchdog diagnostics match the PLC;
- FORTE command nodes remain writable;
- applied-output and watchdog nodes remain read only;
- stopping the gateway trips the PLC watchdog;
- no positive command is replayed after reconnection;
- real testing starts with the physical manual stop active and DAC zero.

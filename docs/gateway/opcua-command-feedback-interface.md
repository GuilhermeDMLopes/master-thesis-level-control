# Gateway OPC UA Command, Feedback, and Watchdog Interface

## Purpose

This document defines the interface between the Python OPC UA gateway,
4diac FORTE, and the communication watchdog executed in the B&R PLC.

The legacy command NodeIds remain unchanged. The watchdog diagnostics are
additive and read only for FORTE.

## Complete Gateway Interface

| NodeId | OPC UA type | FORTE access | Source or role |
|---|---|---|---|
| `Nivel` | `Double` | Read | Raw level value read from `::Program:Nivel` |
| `Enable` | `Boolean` | Read and write | Enable command requested by FORTE |
| `DAC` | `Int16` | Read and write | DAC command requested by FORTE |
| `EnableFeedback` | `Boolean` | Read | PLC command variable `::Program:Enable` |
| `DACFeedback` | `Int16` | Read | PLC command variable `::Program:DAC` |
| `WatchdogHealthy` | `Boolean` | Read | PLC communication watchdog healthy state |
| `WatchdogTripped` | `Boolean` | Read | PLC watchdog trip latch |
| `AppliedEnable` | `Boolean` | Read | Enable value reaching the physical-output gate |
| `AppliedDAC` | `Int16` | Read | DAC value reaching the physical-output gate |

Only `Enable` and `DAC` are marked writable in the gateway server.

## Signal Chain

```text
FORTE Enable / DAC
        |
        v
Python gateway command nodes
        |
        +--> final DAC write-boundary limiter
        |
        v
PLC Enable / DAC command variables
        |
        +--> PLC communication watchdog
        |
        v
PLC AppliedEnable / AppliedDAC
        |
        v
EnableOut / DACOut
        |
        v
physical outputs
```

## Command and Feedback Semantics

The following values are intentionally different signals:

```text
Enable
EnableFeedback
AppliedEnable
```

```text
DAC
dac_gateway_applied
DACFeedback
AppliedDAC
```

- `Enable` and `DAC` are the latest requests from FORTE.
- `dac_gateway_applied` is the value selected by the final Python boundary
  limiter for a PLC command write.
- `EnableFeedback` and `DACFeedback` confirm the PLC command variables.
- `AppliedEnable` and `AppliedDAC` confirm the values after the PLC watchdog
  and output gate.

A watchdog trip may therefore produce this valid state:

```text
Enable = True
DAC = 12000
EnableFeedback = True
DACFeedback = 12000
WatchdogHealthy = False
WatchdogTripped = True
AppliedEnable = False
AppliedDAC = 0
```

## Gateway Startup Sequence

The gateway does not expose a command-ready server before completing this
safe PLC sequence:

```text
connect to PLC
-> write Enable=False
-> write DAC=0
-> write SafetyReset=False
-> produce observable Heartbeat changes
-> pulse SafetyReset
-> wait for WatchdogHealthy=True
-> verify WatchdogTripped=False
-> verify AppliedEnable=False
-> verify AppliedDAC=0
-> start the gateway OPC UA command server
```

A positive FORTE command cannot be forwarded before this handshake succeeds.

## Reconnection Sequence

When PLC communication returns:

1. Create a fresh `asyncua.Client`.
2. Force `Enable=False`, `DAC=0`, and `SafetyReset=False`.
3. Re-establish Heartbeat.
4. Pulse `SafetyReset`.
5. Wait for a healthy watchdog with zero applied outputs.
6. Reset the gateway `Enable` and `DAC` command nodes to safe values.
7. Publish the confirmed PLC feedback and diagnostics.
8. Resume command processing.

Commands written by FORTE while the PLC is offline are discarded.

## Communication Failure

When a connected PLC cycle fails:

- the gateway attempts final safe writes;
- the PLC watchdog remains the independent fallback;
- the PLC connection is closed;
- gateway command nodes are reset to `Enable=False` and `DAC=0`;
- read-only gateway diagnostics are published fail-closed:

```text
WatchdogHealthy=False
WatchdogTripped=True
AppliedEnable=False
AppliedDAC=0
```

No positive offline command is automatically replayed after reconnection.

## Command Ordering

For a normal stop, the gateway writes:

```text
Enable=False
-> DAC ramp or DAC=0
```

For an activation from a disabled state, the gateway writes the bounded DAC
step before `Enable=True`.

The PLC watchdog still has final authority over the physical outputs.

## Data Types

```text
Nivel             Double
Enable            Boolean
DAC               Int16
EnableFeedback    Boolean
DACFeedback       Int16
WatchdogHealthy   Boolean
WatchdogTripped   Boolean
AppliedEnable     Boolean
AppliedDAC        Int16
```

The operational DAC range remains `0..32000`.

## Level Signal Limitation

`Nivel` remains a raw `INT` value in the PLC and a `Double` raw value in the
gateway. The current `raw / 1000` conversion is retained only as provisional
analysis metadata. It must not yet be treated as a validated centimeter scale.

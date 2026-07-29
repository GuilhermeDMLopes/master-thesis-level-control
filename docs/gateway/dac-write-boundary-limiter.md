# Gateway DAC Write-Boundary Limiter

## Purpose

The IEC 61499 `SAFE_DAC_RATE_LIMITER` limits the DAC change produced by each
FORTE execution. The OPC UA command node stores only the latest value, so an
intermediate FORTE value may be replaced before the Python gateway reads it.

The gateway therefore applies a final independent limiter immediately before
each write to the B&R DAC node.

## Safety Property

For every pair of consecutive successful DAC writes performed by the gateway:

```text
abs(DAC_applied(k) - DAC_reference(k)) <= 150
```

`DAC_reference(k)` is the latest value that was either:

- successfully written by the gateway; or
- subsequently confirmed by the PLC.

The operational range remains:

```text
0 <= DAC_applied <= 32000
```

## Signal Semantics

```text
DAC                     requested command from FORTE
DAC_gateway_applied     final value selected by the gateway limiter
DACFeedback             value confirmed by the PLC
```

The writable OPC UA interface remains unchanged. No second command NodeId is
created.

During a limited ramp, this state is expected:

```text
DAC != DAC_gateway_applied
DAC_gateway_applied == DACFeedback
```

A temporary difference between the applied value and feedback can occur while
a write is being confirmed.

## Runtime Sequence

For each connected gateway cycle:

1. Read the latest requested `DAC` value from the gateway OPC UA server.
2. Clamp the request and the reference to `0..32000`.
3. Limit the requested change to `-150..150`.
4. Write the resulting value only when it differs from the reference.
5. Advance the reference only after a successful write.
6. Read the PLC feedback during the normal feedback/logging cycle.
7. Use the confirmed PLC DAC as the next reference.

`Enable` keeps its existing immediate write behavior.

## Startup

At gateway startup, the PLC watchdog handshake first forces:

```text
Enable=False
DAC=0
AppliedEnable=False
AppliedDAC=0
```

The boundary reference and writable gateway DAC command then start from zero.
The gateway server begins accepting FORTE commands only after
`WatchdogHealthy=True` and `WatchdogTripped=False`.

With a large positive FORTE request, the effective PLC command-write sequence
starts from:

```text
150, 300, 450, 600, ...
```

The requested command may advance more quickly, but each effective write is
still limited.

## Reconnection

After communication is restored:

1. Force PLC `Enable=False` and `DAC=0`.
2. Re-establish Heartbeat and pulse `SafetyReset`.
3. Confirm a healthy watchdog with zero applied outputs.
4. Discard commands written while the PLC was offline.
5. Reset writable gateway `Enable` and `DAC` nodes to safe zero values.
6. Synchronize command feedback and watchdog diagnostics.
7. Reset the boundary reference and last applied value to zero.

The first post-reconnection positive write is therefore limited from zero.

## Invalid Configuration

The gateway validates these conditions before accepting FORTE commands:

```text
maximum_delta > 0
minimum < maximum
all boundary values are finite integers
```

Invalid configuration stops gateway startup through the existing fatal-error
path instead of running without write-boundary protection.

## CSV Evidence

The existing 32 columns remain in their original order. Four columns are
appended:

```text
dac_gateway_applied
mv_gateway_applied_percent
dac_boundary_limited
dac_boundary_max_delta
```

Validation must compare consecutive `dac_gateway_applied` values, not
consecutive requested `dac_gateway_command` values.

## Acceptance Criteria

The implementation is accepted when:

- the first positive DAC write from zero is at most `150`;
- every successful upward and downward write changes by at most `150`;
- the applied command remains within `0..32000`;
- requested and applied commands are logged separately;
- command and feedback match after normal write confirmation;
- reconnection resets the reference from confirmed PLC state;
- offline commands remain discarded after reconnection;
- all automated tests pass;
- the existing OPC UA NodeIds and data types remain unchanged.

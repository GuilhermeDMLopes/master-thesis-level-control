# Gateway Reconnection Validation

## Validation Date

July 24, 2026.

## Objective

The objective of this validation was to verify that the Python OPC UA gateway can tolerate a temporary loss of communication with the B&R PLC interface, keep its own OPC UA server available to 4diac FORTE, reconnect automatically, and resume operation without forwarding commands that were written while the PLC was offline.

The validation used the local B&R PLC simulator instead of the real PLC.

## Tested Architecture

```text
B&R PLC simulator
        |
        | OPC UA, port 4842
        v
Python OPC UA gateway
        |
        | OPC UA, port 4841
        v
External OPC UA clients / 4diac FORTE
```

## Test Environment

The validation used:

- Python 3.10.11;
- `asyncua==1.1.8`;
- the local B&R PLC simulator;
- the Python OPC UA gateway;
- the `fix/gateway-reconnection` Git branch;
- reconnect interval configured as `5.0 s`;
- automated unit tests for the gateway connection layer.

The real PLC and the physical plant were not used.

## Initial State

The simulator and gateway were started normally.

The following ports were confirmed as available:

| Component | Port | Result |
|---|---:|---|
| B&R PLC simulator | 4842 | Available |
| Python gateway OPC UA server | 4841 | Available |

The gateway successfully connected to the simulator and started its own OPC UA server.

## Simulated PLC Disconnection

The simulator was stopped while the gateway remained active.

Observed port state:

| Component | Port | Result |
|---|---:|---|
| B&R PLC simulator | 4842 | Unavailable |
| Python gateway OPC UA server | 4841 | Available |

This confirmed that the gateway server remained accessible even after losing the PLC-side connection.

## Gateway Behavior During the Failure

The gateway detected the closed OPC UA client connection and reported a single connection-loss condition.

Example message:

```text
B&R PLC connection lost (ConnectionError: Connection is closed).
```

The gateway then attempted controlled reconnection instead of continuing the normal 100 ms communication cycle against the closed session.

Observed behavior:

- no repeated Python traceback at every gateway cycle;
- no repeated `Error during the gateway cycle` messages;
- reconnection attempts were logged at controlled intervals;
- the gateway OPC UA server remained available on port 4841;
- PLC reads and writes were suspended while the PLC interface was unavailable.

Measured log results:

```text
Tracebacks: 0
Gateway cycle errors: 0
```

The baseline implementation had previously produced thousands of repeated connection-failure log entries. The corrected implementation eliminated this log flood.

## Commands Written While Offline

While the simulator was unavailable, an OPC UA client wrote the following values to the gateway command nodes:

```text
Enable = TRUE
DAC = 2500
```

The gateway accepted these values on its local OPC UA server, demonstrating that the gateway interface remained available to 4diac FORTE or other clients while the PLC was offline.

These values were intentionally treated as offline commands and were not forwarded automatically after reconnection.

## Simulator Restart and Automatic Reconnection

The simulator was restarted without restarting the gateway.

The gateway automatically created a fresh OPC UA client connection and restored PLC communication.

Observed messages included:

```text
Reconnected to the B&R OPC UA server.
PLC communication restored: raw level=10000.0, Enable=False, DAC=0.
Offline commands were discarded.
```

Measured result:

```text
Successful reconnections: 1
```

Both ports were available after recovery:

| Component | Port | Result |
|---|---:|---|
| B&R PLC simulator | 4842 | Available |
| Python gateway OPC UA server | 4841 | Available |

## Post-Reconnection State Synchronization

After reconnection, the gateway synchronized its exposed command and feedback nodes with the values confirmed by the simulator.

Observed values:

```text
Nivel: 12000.0
Enable: False
DAC: 0
EnableFeedback: False
DACFeedback: 0
```

The exact level value depends on the deterministic simulator profile. The command and feedback values were the critical acceptance criteria.

The following assertions passed:

```text
Enable == False
DAC == 0
EnableFeedback == False
DACFeedback == 0
```

Result:

```text
Offline command discard: PASSED
```

This confirmed that the offline values `Enable=True` and `DAC=2500` were not transmitted to the simulator after communication was restored.

## Automated Test Results

A dedicated connection test module was added.

The new tests verified:

- creation of a fresh OPC UA client connection;
- initial PLC state reading;
- cleanup after a failed connection attempt;
- cleanup behavior when `disconnect()` fails;
- synchronization after reconnection;
- discard of offline commands;
- concise connection error formatting.

New connection tests:

```text
6 passed
```

Complete project test suite:

```text
44 passed
```

## Acceptance Criteria

| Criterion | Result |
|---|---|
| Gateway detects loss of PLC communication | Passed |
| Gateway OPC UA server remains available on port 4841 | Passed |
| PLC communication loop stops using the closed session | Passed |
| No traceback is generated every 100 ms | Passed |
| Reconnection attempts occur at controlled intervals | Passed |
| Gateway reconnects after simulator restart | Passed |
| PLC readings resume after reconnection | Passed |
| Offline Enable command is discarded | Passed |
| Offline DAC command is discarded | Passed |
| Command nodes are synchronized with confirmed PLC values | Passed |
| Feedback nodes are synchronized with confirmed PLC values | Passed |
| Automated connection tests pass | Passed |
| Complete automated test suite passes | Passed |

## Files Added or Modified

The reconnection implementation changes the following files:

```text
gateway/src/gateway_config.py
gateway/src/gateway_connection.py
gateway/src/gateway_opcua.py
tests/test_gateway_connection.py
```

The reconnect interval is configured by:

```python
BR_RECONNECT_INTERVAL_S = 5.0
```

## Known Limitations

The current validation does not include:

- the real B&R PLC;
- the physical plant;
- network packet loss with an active TCP session;
- authentication or encrypted OPC UA sessions;
- multiple simultaneous PLC endpoints;
- persistent command queues;
- automatic fail-safe action in the real PLC;
- PI or MPC execution during a communication failure.

The measured interval between some reconnection log entries may be longer than the configured five seconds because a failed OPC UA connection attempt also consumes connection and cleanup time.

## Conclusion

The gateway reconnection mechanism was successfully validated with the local B&R PLC simulator.

The gateway now:

- keeps its OPC UA server available during PLC-side communication failures;
- avoids uncontrolled traceback generation;
- retries connection in a controlled manner;
- creates a fresh OPC UA client after the previous session is lost;
- resumes PLC communication automatically;
- synchronizes command and feedback values after recovery;
- discards commands written while the PLC was offline.

This result satisfies the minimum gateway robustness requirements defined for Stage 2.8.

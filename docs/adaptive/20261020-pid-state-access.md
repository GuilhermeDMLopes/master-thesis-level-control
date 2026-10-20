# PID state access for gradual gain application

Date: 2026-10-20. Experimental type; not exported or validated in native FORTE.
The validated PID_FLAG and its mapped application are unchanged.

## Downloadable architecture

- [PDF](images/PID_Adaptativo_Estrutura.pdf)
- [SVG](images/PID_Adaptativo_Estrutura.svg)

The drawing follows the recorded functional topology of the advisor board. It is not a literal reproduction of the photo. The gradual transition is an explicit project addition.

## New prototype

Path: 4diac/prototypes/PID_Adaptation/Type Library/pid/PID_FLAG_STATE_ACCESS.fbt.
This is a standalone experimental type, not a complete deployable application.

The original INITIALIZE, CALCULATE, UPDATE_GAINS and FAIL ST algorithms are identical to the current PID_FLAG. Added READ_STATE event:
- In READY: copies nine state values to read-only output ports, then emits STATE_CNF.
- Before INIT: emits STATE_ERR and remains uninitialized.
- In failure: emits STATE_ERR and remains in a failure waiting state; INIT is still required for recovery. An idle failure state prevents re-emitting the original ERR just because a read was attempted.
- A state read never emits normal CNF or GAINS_CNF and does not compute an actuator command.

| STATE_CNF output | Internal source |
|---|---|
| ACTIVE_PROPORTIONAL_GAIN | KP_ACTIVE |
| ACTIVE_INTEGRAL_GAIN | KI_ACTIVE |
| ACTIVE_DERIVATIVE_GAIN | KD_ACTIVE |
| ACTIVE_SAMPLE_TIME_S | TS_ACTIVE |
| ACTIVE_OUTPUT_MIN / ACTIVE_OUTPUT_MAX | LOW / HIGH |
| INTEGRAL_MEMORY | I_MEMORY |
| PREVIOUS_ERROR | E_PREV |
| INTEGRATION_ENABLED | FLAG |

All nine values have WITH associations to STATE_CNF. They are snapshots, not continuously updated values; consume them only with the associated successful event. STATE_ERR does not authorize consuming an old snapshot.

## Proposed event transaction

One coordinator owns the sample and the gain request. No independent REQ/INIT/SET_GAINS may interleave the transaction.

1. Latch current setpoint, measured output and previously applied-command history.
2. Update identification; when due, accept/reject a target gain calculation.
3. Issue PID.READ_STATE.
4. STATE_CNF enables calculation of current features using that snapshot and the SAME latched setpoint/measurement:
   error=SP-PV;
   integral_next=INTEGRAL_MEMORY + T/2*(error+PREVIOUS_ERROR) only if INTEGRATION_ENABLED;
   derivative=(error-PREVIOUS_ERROR)/T.
5. Compute the bounded gain step, maintaining prior gains if the candidate is rejected.
6. Send a coherent triplet via PID.SET_GAINS; await GAINS_CNF.
7. Issue PID.REQ with the latched SP/PV; PID.CNF authorizes applying the command.
8. Commit history and complete the transaction before admitting another sample.

This preserves PID arithmetic and lets an external transition block evaluate the gain-induced command change without dividing weighted terms by gains. It requires a real coordinator/latching implementation: data wires alone are not a transaction lock. The drawing is not a verified native network.

## Verification completed

Four unittest cases passed using the existing limited offline ST/ECC interpreter:
- Original ST algorithm bodies are unchanged.
- Reads before initialization and after a numerical failure are rejected; recovery through INIT works.
- State reads preserve all original variables; 100 updates including saturation and a gain change produce exactly the original PID trace.
- All nine snapshot data outputs are declared and associated with STATE_CNF.

Run from repository root:
```powershell
py -m unittest discover -s tests -p test_pid_state_access.py -v
```

This does not validate native event scheduling, queues, XML schema conformity, deadlines or concurrent readers. The named prototype is not part of the existing FORTE build scripts.

Next implementation work: transition block and sample coordinator, then explicit event-chain tests before native export. No adaptation is enabled in the user's validated projects by this commit. The earlier closed-loop results and limitations remain in [the simulation record](20261020-gain-transition-and-closed-loop.md).

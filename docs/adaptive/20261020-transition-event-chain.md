# Event-coordinated PID gain transition — offline prototype

Date: 2026-10-20. Changes limited to experimental types, generator, tests and documentation. Validated applications and PID_FLAG remain unchanged.

## What was implemented

- PID_GAIN_TRANSITION: stateless REQ/CNF calculation of a bounded gain step from a coherent PID state snapshot, latched SP/PV, target gains and estimated model.
- PID_SAMPLE_COORDINATOR: serial handshake from sample capture through state read, transition, gain update, PID calculation and output acknowledgment.
- Existing PID_FLAG_STATE_ACCESS supplies the nine snapshot ports.

Paths: 4diac/prototypes/PID_Adaptation/Type Library/pid/.
These files are NOT a mapped application, not in current native build scripts, and not an implemented complete adaptive control loop. The gain tuner and quality authorization still run only in the prior Python simulation.

## Transition contract

REQ associates every input. CNF associates NEXT_PROPORTIONAL_GAIN, NEXT_INTEGRAL_GAIN, NEXT_DERIVATIVE_GAIN, GAIN_OUTPUT_CHANGE, STEP_FRACTION, UPDATE_APPLIED and VALID.

State inputs: SETPOINT, PROCESS_VARIABLE, INTEGRAL_MEMORY, PREVIOUS_ERROR, ACTIVE_SAMPLE_TIME_S, ACTIVE_OUTPUT_MIN/MAX, ACTIVE_PROPORTIONAL/INTEGRAL/DERIVATIVE_GAIN, INTEGRATION_ENABLED.
Target inputs: TARGET_PROPORTIONAL/INTEGRAL/DERIVATIVE_GAIN and TUNING_ALLOWED.
Configuration: MAX_GAIN_OUTPUT_CHANGE, MAX_RELATIVE_GAIN_STEP, PROPORTIONAL/INTEGRAL/DERIVATIVE_SCALE_FLOOR.
Model: MODEL_OUTPUT_COEFFICIENT_1/2 and MODEL_INPUT_COEFFICIENT_1/2.

Recommended reproduction values only: 0.02 output-effect bound, 0.02 relative step, gain scale floors [0.01,0.01,0.001]. No physical limits are inferred.

Invalid active state/configuration emits ERR with VALID=FALSE and never CNF. The caller must not use stale gain outputs after ERR.
Disallowed tuning, prior saturation, invalid target/model, raw-command saturation or rejected stability check return the existing gains through CNF with UPDATE_APPLIED=FALSE. VALID then means the transaction produced a usable hold decision, not that a new model/gain set was accepted.

No pending target is stored inside the stateless block. The future target manager must keep TUNING_ALLOWED false after quality rejection until a new target/model pair is explicitly accepted.

The state feature calculation preserves the original trapezoidal integral and backward derivative. One common interpolation fraction bounds the raw-command effect and relative movement of each gain. No integral rescaling/reset or alternate anti-windup was introduced.

For the candidate frozen-gain characteristic polynomial [1,A1,A2,A3,A4], a scalar Schur recursion checks all poles inside the unit circle. At each degree n require abs(last)<1, denominator=1-last^2 > 1e-12, then reduce ai to (ai-last*a(n-i))/denominator. Repeat to degree one. All computed values receive numerical finite-domain guards. This is an implementation of a polynomial stability test, not a guarantee of adaptive/time-varying stability. Near-boundary candidates can be conservatively rejected by the denominator threshold.

## Coordinator event wiring

Initialize the PID successfully before coordinator INIT. Initialize target/configuration sources separately before admitting samples. The coordinator does not initialize the PID itself.

| Source | Destination |
|---|---|
| acquisition completion with valid coherent data | Coordinator.SAMPLE |
| Coordinator.READ_PID_STATE | PID.READ_STATE |
| PID.STATE_CNF | Coordinator.STATE_READY |
| Coordinator.CALCULATE_TRANSITION | Transition.REQ |
| Transition.CNF | Coordinator.TRANSITION_READY |
| Coordinator.APPLY_GAINS | PID.SET_GAINS |
| PID.GAINS_CNF | Coordinator.GAINS_READY |
| Coordinator.EXECUTE_PID | PID.REQ |
| PID.CNF | Coordinator.CONTROL_READY |
| Coordinator.APPLY_OUTPUT | actuator request |
| actuator acknowledgment | Coordinator.OUTPUT_APPLIED |
| PID.STATE_ERR, PID.ERR, Transition.ERR, acquisition/actuation fault | Coordinator.FAULT |

Coordinator.CNF marks the whole sample transaction complete. Coordinator.ERR must stop the experiment timer and invoke the application's failure policy; it does not by itself turn off a physical actuator.

Data wiring: coordinator LATCHED_SETPOINT and LATCHED_PROCESS_VARIABLE feed Transition.SETPOINT/PROCESS_VARIABLE and PID.SP/PV. Snapshot ports feed matching transition state ports. Transition.NEXT_* gains feed PID.KP/KI/KD. PID.MV feeds actuator command. Target and model sources must be frozen coherently through each transition calculation.

Only the coordinator may issue PID.READ_STATE/SET_GAINS/REQ during a transaction. A second SAMPLE or INIT while busy emits ERR and ends the transaction in FAILED. Unexpected confirmations are ignored; they cannot skip a waiting stage. Recovery requires INIT after outstanding operations have been stopped/drained. No transaction IDs, deadline timer or duplicate-message defense across resets is implemented.

The 10-sample tuning counter, model-quality gate, tuner, acquisition, actuator and timeout source are not implemented by these two types. Their event wiring must be added before representing this as an autonomous application.

## Tests and limits

14 unittest methods passed across test_pid_state_access.py and test_pid_transition_chain.py in the limited offline ST/ECC interpreter:
- unchanged original PID algorithms and equivalent control traces;
- snapshot and gain-handshake ordering;
- integrated sample updates the integral once, after the gain acknowledgment;
- latched SP/PV survive changes to incoming data during a transaction;
- overrun/fault stops the chain;
- invalid state errors, rejected candidates hold gains;
- gain-induced raw-command bound in 100 deterministic state cases;
- scalar polynomial gate agrees with independently computed NumPy roots for 100 deterministic polynomial cases.

This is actual prototype FBT ST/ECC replay, but not native FORTE or WITH/queue/concurrency validation. No new performance claim beyond the previously documented Python simulations.

Reproduce:
```powershell
py -m unittest discover -s tests -p test_pid_state_access.py -v
py -m unittest discover -s tests -p test_pid_transition_chain.py -v
```
NumPy is required for the independent root cross-check.
Generator: scripts/generate_pid_transition_prototypes.py (writes only the two experimental types).

Next step: assemble a dedicated offline application and the remaining target-generation/authorization wiring, then export/build and validate native event behavior. Do not copy these prototypes over the user's validated PID project or connect them to the physical plant.

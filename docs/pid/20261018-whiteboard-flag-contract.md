# Advisor whiteboard contract — flag PID and adaptation
Date: 2026-10-18. Status: design decision; no new native FORTE validation.
This decision supersedes the pending anti-windup choice and fixed-only gain interface
in [the source review](20261011-architecture-review.md). Its source/page analysis remains applicable.

## Authority and scope
The user explicitly selected the advisor whiteboard over alternative anti-windup
methods. Reproduce the delayed binary flag. Do not substitute directional
conditional integration, back-calculation, derivative filtering, or automatic
integral rescaling. Keep the known saturation-recovery limitation documented.

## Exact update order
The whiteboard does not index flag. Resolve this explicitly as the flag from the
previous accepted update, because saturation is evaluated after integration.
For each accepted sample:
1. e = SP - PV
2. I = I_old + TS_S/2 * (e + e_old) * flag_old
3. D = (e - e_old)/TS_S
4. raw = KP*e + KI*I + KD*D
5. If raw > U_MAX: MV = U_MAX, flag = 0.
   Else if raw < U_MIN: MV = U_MIN, flag = 0.
   Else: MV = raw, flag = 1.
6. Save e and I; publish outputs with CNF.
Exact equality with a limit follows the else branch. Updating flag must not
retroactively undo the current integral increment.
Initialization convention (not specified on the board): I=0, e_old=0, flag=1.
Consequently the first sample uses those values in the same equations; no special
first-sample derivative suppression. This supersedes the previous proposed
first-sample policy. These zero initial conditions must be stated in experiments.

## Modular architecture
- Periodic event source: E_CYCLE, outside the PID.
- Acquisition: coherent measured PV and available applied-input history.
- PID: one Basic FB with ECC, small ST update, output bounds and flag.
- Actuation: output conversion and OPC UA write/status.
- Identifier: MMQE/RLS parameter estimation from correctly aligned applied input
  and measured output history. It estimates a model, not PID gains directly.
- Tuner (CALCULA in the photo): model coefficients -> KP, KI, KD.
Names here describe roles, not implemented or standard library types.

The two lower blocks in the image are ID and CALCULA. They remain distinct.
Use the existing RLS implementation only after verifying the model and regressor
convention; four coefficients are from the prior lecture example, not specified
by this photo. A numerical VALID flag alone does not establish model adequacy.

## Event/data contract
PID INIT / INITO: initialize parameters and state.
PID REQ with SP,PV / CNF with MV,ERROR,P_TERM,I_TERM,D_TERM,FLAG: one accepted sample.
PID SET_GAINS with KP,KI,KD / GAINS_CNF: latch the complete gain triplet;
do not reset integral, previous error or flag and do not calculate/write MV.
Rejected configuration/sample emits an error indication without normal CNF.
Numeric values LREAL; FLAG BOOL, implemented as an IF around the integral
increment instead of implicit BOOL-to-real multiplication.
A gain update affects the next REQ. Document that this simple design does not
guarantee bumpless transfer, particularly because the stored integral is unweighted.

Use WITH associations for event-related data, and separate ECC handling for INIT,
REQ and SET_GAINS. Do not use INIT for online gain updates.
A completed valid read triggers the PID; PID CNF triggers actuation. Bad
communication status is not a valid sample. Only one read/control/write
transaction is in flight in the initial implementation.
Identifier CNF triggers tuner REQ; tuner CNF triggers PID SET_GAINS.
Adaptation may run less often than control, but no rate or enable policy is supplied
by the photo. Do not start independent unsynchronized reads of live scalar inputs.
Before native concurrent execution, ensure coherent gain transfer using the chosen
resource/runtime's verified event/data behavior; use a buffer/handshake if needed.

Identification must use the input actually applied over the relevant interval,
not pair the newly computed command with the measurement that preceded it.
The photo is a topology, not a complete temporal/data acquisition specification.

## Remaining source gap
No confirmed model-to-PID gain equation is present in the whiteboard or the
previously reviewed lecture diagram. The two PID articles do not establish a
selected online MMQE-to-KP/KI/KD law for this project.
Implementing a fictitious tuner, passing model coefficients through as gains,
or silently selecting a tuning method would violate source fidelity.
The next implementation can implement/test the flag PID and SET_GAINS separately;
connect an actual tuner only once its formula and input convention are supplied.

## Acceptance
Verify P/I/D arithmetic, first sample, strict bounds, delayed flag and saturation
recovery limitation, gain-triplet updates without state reset, one CNF per accepted
REQ, native export/build, and event/timing traces. No native runtime or plant
validation is claimed by this document.

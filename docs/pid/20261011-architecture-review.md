# Fixed PID: source review and implementation contract

Date: 2026-10-11. Status: reviewed design, not a newly implemented or deployed PID.
Current target: 4diac IDE 2.0.1 (build 2023-10-23_0926), as reported by the user.
The corresponding FORTE build must be identified independently; IDE and runtime
versions must not be assumed equal. Existing adaptive identification remains an
independent experiment. The immediate advisor-directed task is a simple fixed PID.

## Sources and exact locations

Page numbers are 1-based PDF viewer pages. Source PDFs/photos are not redistributed.

| ID | Supplied material | Location and supported decision |
|---|---|---|
| A | Caiza, Saeteros, Pillajo and Arevalo, Development of an IEC-61499 PID Control for Industrial Processes Applications (2018) | PDF p.2 equations 1-3 discuss filtered PID; pp.3-4 section III-B and p.4 Figs.6-7 separate SENSOR, PID and ACTUADOR, with E_CYCLE and restart; gain inputs are exposed. Implementation uses C++. It does not provide a complete reproducible discrete algorithm/ECC listing. |
| B | Ramos et al., Experimental Platform for Testing Open Process Automation Technologies Based on OPC UA and IEC 61499 (2024), DOI 10.1109/SIOT63830.2024.10780765 | PDF p.3: process/control/OPC UA roles and Kp, Ti, Td convention. PDF p.4 section IV-A: basic PID FB and back-calculation anti-windup with MV bounds. PDF p.5 Fig.7: cyclic OPC UA acquisition, conversion, PID and output write. No full discrete PID implementation or back-calculation coefficient is supplied. |
| C | Advisor whiteboard photo, WhatsApp Image 2026-10-11 at 18.14.54.jpeg | Left: error, trapezoidal integral multiplied by flag, weighted P/I/D sum, saturation and flag update. Right: backward difference derivative of error. Center: acquisition, PID, output and a later identification/tuning branch; some small handwriting is not unambiguously readable. No adaptive tuning equation is derived from it. |

SHA256 of supplied files:

- A: `d6687365edc44d6c8d5656be463531f95b4af7b7d946eba3a610ee168fdb0a2f`
- B: `89cd725aeea1d6d7a668f4df73775dc0f419da6b2e84b01815098634f0ba97ce`
- C: `9c8f9b842ee52b08c5ac85b59c6c6af477356ac1ceb8548d9d34d062e63b9201`

## Source conflicts and reviewer findings

1. Article A p.4 prose describes INIT/INITO as cyclic data handling and REQ as
   library execution. Fig.6 labels initialization and service request, while Fig.7
   connects E_CYCLE.EO to SENSOR.REQ and chains CNF to REQ. Follow an explicit
   initialization/sample contract; do not reset PID memory on every sample.
2. A shows DINT gain inputs. B uses REAL/LREAL conversion and fractional gains.
   Use LREAL for controller arithmetic; this is our implementation choice, not
   an IEC requirement to use LREAL. Do not silently quantize fractional gains.
3. A discusses a filtered derivative; C specifies an unfiltered backward
   difference. These are different control laws and must be labeled accordingly.
4. B uses back-calculation; C uses a flag gating integration. They are not the
   same anti-windup method. B does not specify enough detail to reproduce its
   exact discrete update, coefficient or state initialization.
5. B p.4 prose describes reading MV/writing PV, opposite the physical direction
   described on p.3 and shown by Fig.7 (PVCliente reads PV, MVCliente writes MV).
   Our contract is measurement read and manipulated-variable write.
6. A's 100 ms and B's 1 s are experimental choices for different systems, not
   timing requirements imposed by IEC 61499 or established values for our plant.
7. A lack of Problems in the IDE does not validate ST export, native event/data
   semantics, sample timing or controller performance. OPC UA plus IEC 61499
   alone also does not establish complete O-PAS conformance or portability.

## Standards and implementation evidence

- IEC 61499-1:2012: architecture/reference models.
  https://webstore.iec.ch/en/publication/5506
- IEC 61499-2:2012: software tool/exchange requirements.
  https://webstore.iec.ch/en/publication/5507
- Eclipse 4diac own-types guide:
  https://eclipse.dev/4diac/doc/tutorials/createowntypes.html
- Eclipse 4diac periodic event example:
  https://eclipse.dev/4diac/doc/tutorials/use4diaclocally.html

Public IEC descriptions and official tool documentation were consulted. The full
normative standard was not provided/read in this checkpoint. No clause-by-clause
compliance certification is claimed. The following is an engineering contract to
verify against the target implementation, not a quotation of mandatory clauses.

## Minimal external architecture

| Component | Responsibility |
|---|---|
| E_CYCLE (existing library type) | Provide the periodic event; DT is a TIME duration. |
| Acquisition | Read measurement through the existing OPC UA client infrastructure, check read status, expose a coherent value in defined units. |
| PID_FIXED (new basic FB, proposed name) | Execute one discrete PID update, maintain controller memory, and bound its output using the selected anti-windup law. |
| Actuation | Convert/scale the bounded MV and write through the existing OPC UA infrastructure; expose write status. |

Acquisition and actuation are logical responsibilities, not invented standard FB
names. Their concrete SIFBs, data types, node IDs and completion events must be
checked against the project's actual FORTE/OPC UA configuration. Reuse existing
communication blocks. A/D and D/A conversion occur in PLC/hardware; OPC UA carries
values and is not itself an analog-to-digital converter.

Initialization: Acquisition.INITO -> PID.INIT -> PID.INITO -> Actuation.INIT;
start the timer only after successful actuation-interface initialization. A
restart/init trigger starts this chain. Initialization alone must not command
plant motion.

Sample order: Cycle.EO -> acquisition request -> successful read completion ->
required numeric conversion -> PID.REQ -> PID.CNF -> required output conversion
-> actuation request. Associate data with the relevant events using WITH. Do not
fan the timer out independently to read, calculate and write. A data wire alone
must not be treated as execution authorization. A communication completion with
bad status must not be forwarded as a good sample.

Keep at most one transaction in flight during this first implementation. Measure
request/completion times and overruns. If a read overruns the nominal interval,
report the missed deadline; do not silently feed irregular updates to a fixed-Ts
PID. For an asynchronous subscription, sampling the latest value is a different
architecture and requires an explicit freshness/timestamp policy.

Map to a dedicated test resource for the first run. Exact resource and native
module build are pending. E_CYCLE pacing is not proof of hard real-time behavior.

## Proposed PID interface

Keep configuration fixed between initialization and reset in the first version.
This is a scope decision; live retuning and bumpless transfer are later features.

| Event | Associated data / behavior |
|---|---|
| INIT | KP, KI, KD, TS_S, U_MIN, U_MAX; validate and latch parameters, reset memory. |
| INITO | VALID; emitted only after successful initialization. |
| REQ | SP, PV; accept one coherent input sample and compute one update. |
| CNF | MV, ERROR, P_TERM, I_TERM, D_TERM, SATURATED, VALID; publish only after accepted update. |
| ERR | VALID=FALSE; no normal CNF for a failed update. |

Numeric signals use LREAL; SATURATED/VALID use BOOL. The three term outputs are
observability aids for teaching/tests. They are already weighted contributions
KP*P, KI*I and KD*D, which avoids ambiguity when comparing their sum with MV.
TS_S is seconds as LREAL; E_CYCLE.DT is TIME. Use one configuration source and an
explicit conversion to keep them consistent. TS_S does not schedule the block.

Basic ECC concept: START -> INITIALIZE -> READY -> CALCULATE -> CONFIRM -> READY,
with an ERROR state for invalid initialization/update. INIT is also available for
reinitialization; REQ before successful INIT is not a valid control transaction.
Output confirmations occur after computation. Numeric failure must not corrupt the
last accepted integral/history. Concrete ECC and ST are pending anti-windup choice.

One PID FB is consistent with both articles. P/I/D can be clearly separated inside
one small ST algorithm; IEC 61499 modular design does not require one FB for each
addition or multiplication. No identifier, tuner or OPC UA code belongs in PID_FIXED.

## Whiteboard mathematics

Use the parallel gain convention:

    e[k] = SP[k] - PV[k]
    P[k] = e[k]
    I[k] = I[k-1] + (TS_S/2) * (e[k] + e[k-1]) * flag
    D[k] = (e[k] - e[k-1]) / TS_S
    u_raw[k] = KP*P[k] + KI*I[k] + KD*D[k]
    MV[k] = min(U_MAX, max(U_MIN, u_raw[k]))

I is the integral of error, not an already KI-weighted term. D is a derivative of
error, not of measurement. Do not multiply by KI or KD twice. A setpoint step may
therefore produce derivative kick. Filtering or derivative-on-measurement would
be explicit modifications of the whiteboard algorithm, not a faithful copy.

B uses Kp, Ti, Td instead. For the corresponding ideal parallel form, Ki=Kp/Ti
and Kd=Kp*Td (Ti>0). These conversions do not equate different derivative filters,
anti-windup methods or discretizations. Do not copy Ti directly into KI.

The photo does not specify initial integral/error history, first-sample derivative
handling, the time index of flag, or how to update state in manual operation.
Proposed first-sample policy to review: I=0 at INIT, first valid sample sets
previous_error=current_error, D=0, and integral accumulation begins on the next
sample. This policy is our engineering choice, not attributed to the sources.
No plant KP/KI/KD, bounds, scaling or physical sample interval is assigned yet.

## Anti-windup decision required before final ST

If the flag is calculated after saturation and reused at the next update, the
literal interpretation is flag[k-1] in the integral equation and flag[k]=0 when
u_raw[k] is outside the limits. This delayed interpretation can lock integration
while saturated, including when the error reverses direction.

Counterexample (synthetic arithmetic, not plant data): KP=1, KI=1, KD=0,
TS_S=1 s, limits [0,1], initial I=0, previous_error=0 and flag=1. With error 10,
I becomes 5, raw output 15, MV=1 and next flag=0. Repeating error -1 then keeps
I=5, raw output 4 and MV=1 indefinitely. This was checked numerically in Python.
The initial-state choice here is part of this counterexample, not a settled PID
initialization contract.

A minimal correction close to C is directional conditional integration: compute
a trial trapezoidal increment; block it only if it drives an already/trial
saturated output further outward, and allow increments that bring it back. The
increment's sign matters (KP/KI sign and trapezoidal history must be considered),
not merely the current error's sign. This would be an explicit design modification.

Alternatively, reproduce B's anti-windup family using back-calculation with a
specified tracking time/gain and discrete update order. Those missing details
must be selected and documented; they cannot be claimed to be recovered from B.

Do not combine a freeze flag and back-calculation without a defined control law.
The advisor's preference between literal teaching reproduction, corrected
conditional integration and back-calculation remains to be confirmed.

## Minimal acceptance evidence

1. INIT resets state; REQ before INIT and invalid TS_S/bounds/inputs are handled.
2. P-only, I-only and D-only numeric sequences match hand calculations.
3. A constant error produces the expected trapezoidal accumulation and zero
   derivative after initialization; setpoint-step behavior is documented.
4. Upper/lower saturation tests include sustained saturation and error reversal.
5. Each accepted sample produces one CNF; no mixed sample or duplicate update.
6. Native export/build and offline FORTE traces agree with the numerical reference.
7. Read/write status, actual update interval, jitter and overruns are recorded.
8. Real-plant comparison records units, tuning, initial state, setpoint, limits and
   actuator dynamics. A prettier diagram or working simulation does not prove
   improved real-plant performance or a novel research contribution.

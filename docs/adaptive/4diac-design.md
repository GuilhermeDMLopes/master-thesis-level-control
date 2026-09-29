# Offline IEC 61499 identification prototype

Status: original XML/ST source and unmapped application, checked by offline tests.
**Not yet imported in the user's IDE, natively exported, compiled, deployed or run in FORTE.**
This is not the adaptive PID or a claim of IEC 61499 conformance certification.

## Files and separation

Project: `4diac/application/Adaptive_Identification/`.
Existing `OPAS_Tank_System` applications and the preserved runtime are unchanged.

| Type | Inputs sampled by events | Outputs | Persistent responsibility |
|---|---|---|---|
| `ADP_REPLAY100` | INIT: CHANGE; REQ: tick | K (UINT), U1, U2, B1 (LREAL); CNF/DONE | Replay exactly the archived excitation; maintain input history; change B1 at k=51 if configured |
| `ADP_HISTORY2` | REQ: snapshot; COMMIT: Y_CURRENT | Y1,Y2 (LREAL); CNF/ACK | Keep two previous outputs; expose a snapshot before any current sample is committed |
| `ADP_ARX22_PROCESS` | REQ: Y1,Y2,U1,U2,B1 | Y (LREAL), CNF | Evaluate the lecture's signed ARX equation; no estimator logic |
| `ADP_RLS4` | INIT: LAMBDA,P0; REQ: Y,F1,F2,F3,F4 | T1..T4,Y_HAT,ERROR (LREAL), VALID (BOOL); CNF/ERR | Estimate four parameters and store P; no controller/gain tuning |
| `ADP_IDENTIFICATION` | INIT: CHANGE,LAMBDA,P0; REQ: tick | Completed sample and estimator outputs; INITO,CNF,DONE,ERR | Composite connection network; no algorithm |
| Standard `E_CYCLE` | START,STOP; DT | EO | Pace offline execution; existing repository type reused unchanged |

CHANGE, LAMBDA and P0 are captured at INIT. Changes require stopping the timer and reinitializing the experiment. DT=100 ms only makes the demonstration observable; equations are indexed by k, not physically discretized using that DT.

## Event order

Initialization: `Experiment.INIT -> Replay.INIT -> History.INIT -> Process.INIT -> Estimator.INIT -> Experiment.INITO -> Cycle.START`.
Each block's INITO triggers the next INIT. A bad estimator initialization emits ERR instead of INITO, so the timer does not start.

Sample: `Cycle.EO -> Replay.REQ -> History.REQ -> Process.REQ -> Estimator.REQ -> History.COMMIT -> Experiment.CNF`.
Each arrow after REQ is driven by the preceding block's CNF (History.COMMIT ends in ACK).
This order is explicit in the composite EventConnections, not inferred from the visual positions.

Data used at sample k:

- Replay supplies u(k-1), u(k-2) and the actual b1 for the simulated process.
- History supplies y(k-1), y(k-2).
- Process computes y(k).
- Estimator uses `[y(k-1),y(k-2),u(k-1),u(k-2)]` and y(k).
- Only after a successful estimator update does History commit y(k).
- CNF on the composite denotes a complete sample. Log/observe its values at CNF.

Actual b1 is connected to the simulated process and monitoring output only. It is NOT an estimator input. There is no event fan-out requiring an assumed sibling order in the sample chain.

After 100 samples, the next tick emits DONE without computing sample 101. DONE stops E_CYCLE. An estimator ERR also stops it; restart requires INIT. Do not inject REQ while a transaction is in flight or INIT while the timer is running. The intended mapping is a dedicated, serial offline resource; concurrent/distributed operation has not been qualified.

## ECC and algorithm boundaries

- Replay: START -> INITIALIZE -> READY; REQ with K<100 -> EXECUTE -> READY. K>=100 -> FINISH/DONE. Initialization resets the sequence.
- History: START -> INITIALIZE -> READY; REQ -> SNAPSHOT -> WAIT; COMMIT -> STORE -> READY. A second REQ in WAIT does not advance the history. INIT can recover WAIT.
- Process: START -> INITIALIZE -> READY; REQ -> EXECUTE -> READY.
- RLS: START -> INITIALIZE -> INIT_OK or FAILED. REQ from READY -> EXECUTE -> UPDATE_OK or FAILED. FAILED accepts INIT only.

RLS uses scalar, unrolled arithmetic rather than multidimensional ST arrays to keep the generated algorithm easy to inspect against the existing scalar-style custom FBs. Temporary V/R/G/N/C variables preserve the old P/theta until the candidate passes numerical checks. This decomposition is an implementation decision, not a requirement from the lectures.

`VALID=TRUE` only reports a numerically accepted update. It is **not** model validation for tuning. Excitation monitoring, stability/quality checks, gain bounds and bumpless gain transfer belong to the later controller stage.

## Checks already performed

`tests/test_adaptive_identification.py`:
- replays all four archived scenarios through the Python reference;
- compares recursive estimates with independent weighted batch least squares;
- interprets the actual generated assignment/IF ST text and local ECC to compare all 100 samples against archived CSVs;
- checks invalid lambda, failed-sample state preservation, reset and completion;
- checks composite port types and WITH names.

The small test interpreter is intentionally limited. It does not test the IDE parser/exporter, native numeric typing, event queues, sampling/transport semantics, target scheduling or wall-clock timing. Native validation remains a separate gate.

## Import and native validation procedure

1. Use a separate offline workspace or import `Adaptive_Identification` alongside the old project without overwriting it.
2. Import its `.project` as an existing 4diac project. Open `Adaptive_Identification.sys` and check that all five custom types and E_CYCLE resolve.
3. Inspect Problems and each ECC/ST algorithm. Record the installed IDE version and build identifier. The existing repository preserves a custom FORTE V4 binary but does not establish that it contains these new types.
4. Export the four basic types and composite using the supported workflow for that IDE/runtime pair. Build a separate offline FORTE executable with those types registered. Do not overwrite the preserved V4 executable or assume dynamic type loading is available.
5. Add/map a dedicated local device/resource in the new system. The committed system is deliberately unmapped. No OPC UA nodes or physical plant connections are present.
6. First run the fixed case: CHANGE=FALSE, LAMBDA=1, P0=10000. Trigger Experiment.INIT only after a fresh deployment. It starts the timer after successful initialization.
7. Capture K,Y,Y_HAT,ERROR,T1..T4,U1,U2,B1 at each Experiment.CNF. Stop/reinitialize between cases. Run CHANGE=TRUE with lambda 1,0.8,0.6.
8. Compare all captured rows to `data/sample/adaptive/20260926/`. Start from absolute/relative tolerance 1e-8 used by the scalar ST checks; review any platform-specific deviation rather than relaxing tolerances silently.
9. Preserve native exported sources, runtime identity, exact mapping, logs, captured rows and observed timing before reporting FORTE validation.

If import/export reports an error, capture the Problems entry and IDE version before modifying the block contract. No physical PLC action is part of this procedure.

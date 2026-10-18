# Whiteboard PID — implementation and verification

Checkpoint: 2026-10-18. Branch: `feature/adaptive-pid-iec61499`.
**Implemented:** flag PID, gain-update event, synthetic process, offline application,
local ST/ECC subset replay and 12 automated tests.
**Not validated:** 4diac 2.0.1 export, native FORTE build/runtime, event timing or a
physical plant. No claim of complete IEC 61499 conformity or automatic tuning.

## Decisions and sources

1. [Source review](20261011-architecture-review.md): exact PDF pages, source hashes,
   article differences and standards/documentation consulted.
2. [Advisor flag contract](20261018-whiteboard-flag-contract.md): the user selected
   the whiteboard flag, overriding the earlier anti-windup alternatives.
3. On 2026-10-18 the user clarified that a gain formula will NOT be supplied: this
   project must select and implement a documented model-to-PID tuning rule. This
   supersedes the earlier request to wait for an advisor formula. Selecting that
   rule is the next research/design task; the MMQE itself is not a gain tuner.
4. The immediate implementation is a PID baseline plus an event interface for
   later gains. No dummy identifier/tuner is connected or represented as working.

Source A (Caiza et al., 2018), PDF pp.3–4, Figs.6–7: separate process I/O and PID,
with periodic event scheduling. Source B (Ramos et al., 2024), PDF pp.4–5,
section IV-A and Fig.7: PID BFB and OPC UA I/O separation. The advisor photo
controls the selected numerical law. Back-calculation from B and the filtered
 derivative discussed by A are deliberately not the selected law.
The synthetic plant, initial conditions, finite-domain checks and test gains are
our explicit implementation choices, not values extracted from either paper.

## Files and responsibilities

| Path | Role |
|---|---|
| `4diac/application/PID_Whiteboard/PID_Whiteboard.sys` | Unmapped three-block application `PID_Simulation`. |
| `4diac/application/PID_Whiteboard/Type Library/pid/PID_FLAG.fbt` | Basic FB, ECC and ST: the actual PID implementation. |
| `4diac/application/PID_Whiteboard/Type Library/pid/PID_DEMO_PROCESS.fbt` | Basic FB: synthetic process with input latched by an event. |
| `4diac/application/PID_Whiteboard/Type Library/events/` | Existing project's E_CYCLE and E_DELAY definitions, reused with copyright notices. |
| `scripts/verify_pid_whiteboard.py` | Narrow offline ST/ECC interpreter and serial application replay. |
| `tests/test_pid_whiteboard.py` | Hand-calculated cases, fault/gain semantics and XML connection checks. |
| `docs/pid/offline-validation.json` | Recorded verification scope, trace summary and implementation hashes. |

The historical OPAS_Tank_System and Adaptive_Identification projects are untouched.
Use this separate project first. Do not overwrite the user's local ECC layout or
application edits in OPAS_Tank_System.

## Numerical contract

At accepted sample k:

```
e = SP - PV
I = I_old
if flag_old: I = I_old + TS_S/2 * (e + e_old)
D = (e - e_old)/TS_S
raw = KP*e + KI*I + KD*D
if raw > U_MAX: MV = U_MAX; flag = FALSE
else if raw < U_MIN: MV = U_MIN; flag = FALSE
else: MV = raw; flag = TRUE
save e and I
```

In ST the two limit comparisons are separate IFs. With validated U_MIN < U_MAX,
they are mutually exclusive and implement the exact if/else-if behavior above.
Initialization: I=0, previous error=0, flag=TRUE; all term/MV outputs start at zero.
INIT emits INITO, never CNF; it is not an actuation request. Initial MV is an
initial value, not a claim that zero is within every possible configured range.
The first sample runs the same equations, including derivative from zero history.
There is no bias, rate limiter, derivative filter, manual mode or automatic integral
rescaling in this educational PID. These are not implicitly copied from the old PI.
SP and PV must use the same units; gains and limits must use compatible units.

The new flag applies on the NEXT sample. It does not undo the current integral
increment. Equality with either bound sets flag TRUE and SATURATED FALSE.
Derivative is on error, so setpoint steps can create derivative kick.

### Known limitation preserved intentionally

With KP=KI=1, KD=0, TS_S=1, limits [0,1], zero initial histories and flag TRUE:
error 10 gives I=5, raw=15, MV=1, flag FALSE. Repeated error -1 leaves I=5,
raw=4 and MV=1. The tests preserve this behavior rather than silently replacing
it with another anti-windup algorithm. Do not claim guaranteed saturation recovery.

## PID interface and ECC

All numeric data are LREAL; FLAG, SATURATED and VALID are BOOL.

| Event in | WITH inputs | Event out / behavior |
|---|---|---|
| INIT | KP, KI, KD, TS_S, U_MIN, U_MAX | INITO: latch configuration; reset history and outputs. |
| REQ | SP, PV | CNF: one completed numerical update. |
| SET_GAINS | KP, KI, KD | GAINS_CNF: latch all three gains without computing MV or resetting memory. |

INITO and CNF associate MV, ERROR, P_TERM, I_TERM, D_TERM, RAW, FLAG, SATURATED,
VALID. GAINS_CNF and ERR associate VALID. P_TERM, I_TERM, D_TERM are weighted;
I_MEMORY is unweighted. The active gains are internal KP_ACTIVE/KI_ACTIVE/KD_ACTIVE.
Editing gain data without SET_GAINS or INIT does not apply them.
SET_GAINS affects the next accepted REQ. It does not guarantee bumpless transfer.
TS_S and limits change only through INIT in this version.

ECC: START -> INITIALIZE -> INIT_OK -> READY; READY -> CALCULATE -> SAMPLE_OK ->
READY; READY -> GAINS -> GAINS_OK -> READY. Algorithms run before confirmation
states emit their event. Invalid operations enter FAILED and emit ERR; INIT is
required for recovery. A REQ or SET_GAINS before INIT also emits ERR.

VALID means the last operation passed numeric/configuration checks, not that the
plant is stable or a model is accurate. Checks require finite values within
[-1e100,1e100], positive TS_S and U_MIN < U_MAX. The 1e100 bound is a documented
numerical guard, not a physical limit. Candidate arithmetic is checked before
committing PID history and outputs. Rejected gain triplets do not partially apply.
On error the last MV remains available, but no CNF authorizes a new actuation.
The demo stops its timer on ERR; a real plant needs a separate failure policy.

## Three-block offline network

The demo has Cycle (E_CYCLE), Process (PID_DEMO_PROCESS), Controller (PID_FLAG).
The process models y[k] = 0.9*y[k-1] + 0.1*u[k-1], with zero histories.
These are synthetic dimensionless coefficients, not the tank, RC circuit, or the
four-coefficient ARX model from the previous identification exercise.

| Event connection | Meaning |
|---|---|
| Process.INITO -> Controller.INIT | Initialize PID after resetting the simulated process. |
| Controller.INITO -> Cycle.START | Start pacing only after successful PID initialization. |
| Cycle.EO -> Process.REQ | Advance the process using its previously latched input. |
| Process.CNF -> Controller.REQ | Calculate PID after the new measurement is available. |
| Controller.CNF -> Process.APPLY | Latch the new MV for the next process step. |
| Process.ERR or Controller.ERR -> Cycle.STOP | Stop the demo on numerical failure. |

Data: Process.Y -> Controller.PV; Controller.MV -> Process.U.
Process.APPLY emits ACK and does NOT advance Y. Process.REQ emits CNF and advances
Y using APPLIED_U. This explicit latch avoids relying on a changed data wire alone
as permission to apply a command. No independent timer event drives Controller.REQ.
No OPC UA or hardware actuation exists in this project.

Cycle.DT=T#100ms and Controller.TS_S=0.1 must match. The process coefficients are
fixed for this example; changing its discrete interval does not automatically
rediscretize a physical plant. Demo gains: KP=1, KI=.5, KD=.1; SP=1; bounds [0,10].
These demonstrate arithmetic and are not a tuning recommendation for the tank.

Initialization starts the clock automatically. To restart, first stop Cycle,
then trigger Process.INIT. To change gains for a manual test, stop Cycle, set all
three gain inputs, trigger Controller.SET_GAINS, verify GAINS_CNF, then start Cycle.
Do not trigger INIT merely to update gains. Native concurrency/data transfer must
be checked before connecting an asynchronously executing tuner.

## Run verification on Windows (no extra Python packages needed)

From the repository root:

```powershell
py -m unittest discover -s tests -p test_pid_whiteboard.py -v
if ($LASTEXITCODE -ne 0) { throw "PID tests failed." }
py scripts/verify_pid_whiteboard.py --csv "$env:TEMP\pid-whiteboard-synthetic.csv"
if ($LASTEXITCODE -ne 0) { throw "PID replay failed." }
```

The replay executes the actual FBT ST subset and follows the XML connections in a
serial Python loop. It is NOT a native runtime, general ST interpreter, timer,
WITH/concurrency simulation, or portability certification. time_s is a calculated
sample time, not measured wall-clock performance. Tests need no network or PLC.

Expected first two rows:

| k | PV | Previous applied U | P_TERM | I_TERM | D_TERM | MV |
|---|---|---|---|---|---|---|
| 1 | 0 | 0 | 1 | .025 | 1 | 2.025 |
| 2 | .2025 | 2.025 | .7975 | .0699375 | -.2025 | .6649375 |

At sample 100: PV approximately .9732477887220724, MV .981112810300077.
These are synthetic offline results only.

## Import and inspect in 4diac IDE 2.0.1

1. Update the existing feature branch without resetting local changes (see commands
   below). A Git conflict should be inspected, not bypassed with reset --hard.
2. Use File -> Import -> General -> Existing Projects into Workspace; select
   `C:\Projetos\master-thesis-level-control\4diac\application\PID_Whiteboard`.
   If the IDE exposes a dedicated 4diac project importer instead, select that same
   folder. Do not copy the project into another directory unless intentionally
   maintaining an independent copy.
3. Open PID_Whiteboard -> PID_Simulation. Expect Cycle, Process and Controller.
4. Open PID_FLAG to inspect Interface, ECC and algorithms. Check Problems.
5. The system is intentionally unmapped. Importing it does not execute it.
6. Before execution: export the two new Basic FB types using the installed IDE's
   exporter, build them into a compatible FORTE (or use a verified supported type
   loading mechanism), create a local test device/resource and map all three FBs.
   The runtime must support the supplied timer definitions and dependencies.
7. Only after successful build/deployment: start monitoring and trigger
   Process.INIT. Observe PV, MV, P/I/D, FLAG, VALID. Stop using Cycle.STOP.
8. Record the exact FORTE version/build, compiler/exporter, Problems output and
   runtime traces. Zero IDE errors alone is not sufficient validation.

The existing FORTE binary must not be assumed to contain these new types.
The user's IDE version is known; FORTE version and native build path are not yet
confirmed. Consequently no fabricated native build command is supplied here.

```powershell
Set-Location "C:\Projetos\master-thesis-level-control"
git status --short
$branch = git branch --show-current
if ($branch -ne "feature/adaptive-pid-iec61499") {
    throw "Switch to the feature branch after preserving your local changes."
}
git pull --ff-only origin feature/adaptive-pid-iec61499
if ($LASTEXITCODE -ne 0) { throw "Update failed; do not discard local changes." }
Get-ChildItem "4diac\application\PID_Whiteboard\Type Library\pid" -Filter *.fbt
```

## Verification and next gate

12 unittest methods passed on the actual local FBT algorithms through the limited
interpreter: P/I/D hand calculations, first sample, upper/lower/exact limits,
delayed flag and known freeze case, gain latching/state preservation, reset,
invalid inputs/configuration/arithmetic, simulated input application, hand-derived
closed-loop samples, port/connection and WITH-reference checks.
The 100-step synthetic trace completed. See offline-validation.json for hashes.

Next gate: import/export/native execution and timing validation. Then validate
identification on a known model and choose a sourced model-to-PID tuning rule.
Use the existing MMQE only with consistent model order and applied-input history.
The later architecture is Identifier.CNF -> Tuner.REQ -> PID.SET_GAINS (via tuner
CNF), with coherent model/gain data and an explicit adaptation schedule. Do not
claim this branch is implemented by the current two custom FBs.

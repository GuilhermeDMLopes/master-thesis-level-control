# Adaptive control workstream

Checkpoint: 2026-09-29. Development branch: `feature/adaptive-pid-iec61499`.

## Goal and current boundary

Build the advisor's indirect adaptive PID structure with separate identification,
model validation, tuning and control responsibilities in IEC 61499. RC hardware is
deferred. The current deliverable covers lecture identification examples and an
initial offline 4diac source prototype, not a closed-loop adaptive PID.

The earlier tank PI/MPC evidence is preserved. Its single-run comparison is not a
claim of controller optimality or proof that further PID investigation is unnecessary.

## Read in this order

1. [Source/page traceability](references-and-traceability.md): lectures, articles,
   video links, earlier project material and explicit project-specific choices.
2. [4diac design](4diac-design.md): ports, ECCs, algorithms, event/sample ordering
   and native import/export/runtime gates.
3. [Source manifest](source-manifest.json): exact supplied-file hashes/page counts.
4. [Evidence manifest](evidence-manifest.json): hashes of the user's returned results.

## Reproduce locally

From the repository root in PowerShell (use a project environment):

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts/reproduce_adaptive_identification.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_adaptive_identification.py
```

The script reads the archived excitation, reproduces four cases and checks the
archived numbers. It does not overwrite user evidence or start FORTE/the gateway.
Regenerate the reviewable XML sources with `python scripts/generate_adaptive_4diac.py`.
The standard E_CYCLE type is reused from the existing repository.

## Progress and validation

| Item | Status |
|---|---|
| Fixed process (L1 p.30) | Reproduced in Python |
| RLS forgetting equations (L1 p.29) | Implemented and cross-checked against batch least squares |
| Parameter change (L1 p.37) | Reproduced for lambda 1,0.8,0.6 |
| Original returned CSVs/PNGs/summary | Preserved without rewriting |
| Four basic FBs, composite and unmapped application | Source generated; offline arithmetic/ECC/structure checks pass |
| IDE import / ST export / FORTE build / execution | Pending; no runtime result claimed |
| Fixed PID on this simulated process | Pending |
| Model-to-PID gain law | Pending confirmation; lecture RST is not automatically PID |
| Adaptive closed-loop comparison | Pending |
| Adaptive-control publication novelty | Not established |

The targeted suite currently contains 15 passing tests. These checks include a
limited interpreter of the actual ST text, not native IEC language/runtime testing.
Full local suite on Linux / Python 3.12: **519 passed, 3 failed** on 2026-09-29.
All three failures reproduce unchanged in a clean worktree of the base commit
`d4c08e8848e6d6e448ee7ce164121e7cb1ec4ac3`:

- `test_preserved_evidence_hashes_match_model_manifest`: historical evidence hash mismatch.
- `test_plan_mode_runs_offline`: historical runner imports Windows-only `msvcrt`.
- `test_final_smoke_evidence_and_documentation_are_preserved`: historical log hash mismatch.

No historical evidence, expected hash or test was rewritten to hide these failures.
The existing GitHub CI runs on Windows/Python 3.11; its result is a separate PR check.
The reproduction script also matched all four archived experiments.

## Why the prototype is modular

`ADP_REPLAY100` reproduces input history, `ADP_HISTORY2` manages output history,
`ADP_ARX22_PROCESS` evaluates the process, and `ADP_RLS4` estimates parameters.
`ADP_IDENTIFICATION` connects them in a serial event chain; E_CYCLE provides a tick.
Python is the mathematical reference and evidence tool at this stage. A Python/OPC
UA gateway is not required for this self-contained simulated experiment.

## Next checkpoint: laboratory session 2026-10-02

With the advisor, record the local PLC PID equation, Kp/Ki/Kd versus Kp/Ti/Td
convention, actual sample period, units/scaling, output limits, derivative filter,
anti-windup, mode transfer and applied-command feedback. Obtain the relevant project
export if authorized by the laboratory. Compare under equivalent reference and
initial conditions. No gains from the old tank are transferred to this ARX example.

Separately confirm the exact adaptive PID tuning rule from the teaching scripts or
self-tuning video transcript. Introduce fixed PID, estimator observation, model/gain
validation and only then gain adaptation. Keep evidence and development stages in
small English commits; do not change the historical validation tag.

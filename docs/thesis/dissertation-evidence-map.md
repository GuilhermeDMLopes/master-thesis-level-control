# Dissertation evidence map

## Purpose

This map connects the existing repository evidence to the dissertation and
identifies the few sections still waiting for final laboratory data.

It is intended to prevent unnecessary repetition of experiments and to make
clear what each dataset can legitimately support.

---

## 1. Experimental platform and architecture

### Evidence

- `gateway/src/gateway_opcua.py`
- `4diac/application/OPAS_Tank_System/`
- communication/runbook documentation under `docs/`
- automated tests under `tests/`

### Dissertation use

Sections:

- experimental platform;
- PLC / OPC UA architecture;
- Python gateway;
- 4diac/FORTE integration;
- signal path and safety architecture.

### Claim status

**READY TO WRITE**

No additional experiment required.

---

## 2. PI baseline

### Evidence

- `data/sample/real-raw-pi-v1-monitor.csv`
- `docs/experiments/real-raw-pi-baseline-validation.md`
- `docs/experiments/pi-vs-mpc-v3-real-plant-comparison.md`
- existing PI-vs-MPC figures under `docs/figures/pi-vs-mpc-v3/`

### Dissertation use

Sections:

- conventional controller baseline;
- real-plant PI behavior;
- baseline controller parameters;
- initial comparative reference.

### Claim status

**BASELINE VALIDATED**

The existing PI run is sufficient as historical baseline evidence.

A new PI run is required only for the final physically calibrated 5/10/15 cm
comparison.

---

## 3. Early MPC development and bounded V3 result

### Evidence

- `docs/experiments/mpc-v3-clean-bounded-20260822-analysis.md`
- `docs/experiments/mpc-v3-extended-60s-internal-trip-analysis-r1.md`
- `docs/experiments/pi-vs-mpc-v3-real-plant-comparison.md`

### Dissertation use

Sections:

- first real MPC commissioning;
- safety-envelope behavior;
- limitations of early controller version;
- motivation for subsequent corrections.

### Claim status

**READY AS DEVELOPMENT HISTORY**

Allowed:

- bounded run;
- safety abort;
- descriptive comparison.

Not allowed:

- steady-state regulation validated;
- strict A/B superiority claim.

---

## 4. V3E expanded envelope

### Evidence

- `docs/4diac/mpc-real-raw-safe-v3e-expanded-envelope.md`
- `docs/experiments/mpc-v3e-expanded-60s-20260822-analysis.md`
- `data/sample/mpc-v3e-expanded-60s-20260822/`
- `docs/figures/mpc-v3e-expanded-60s/`

### Dissertation use

Sections:

- expanded safety envelope;
- 60 s real-plant response;
- demonstration that the previous raw ceiling was not the dominant limitation.

### Claim status

**READY TO WRITE**

Supported:

- 60 s experiment completed;
- expanded envelope was not limiting;
- persistent high-DAC behavior remained;
- regulation not validated.

---

## 5. Model/objective mismatch diagnosis

### Evidence

- `docs/mpc/mpc-v3e-action-semantics-correction.md`
- `docs/mpc/mpc-v3e-model-cost-delay-diagnosis.md`
- `docs/mpc/mpc-v3e-bias-vs-local-refit.md`
- corresponding JSON files under `results/`

### Dissertation use

Sections:

- diagnosis of high-DAC lock-in;
- correction of the initial action-space interpretation;
- model-vs-real prediction mismatch;
- selection of disturbance correction over immediate local refit.

### Claim status

**READY TO WRITE**

This evidence should be used to show engineering reasoning, not to claim
closed-loop performance.

---

## 6. Rejected output-bias V3G attempt

### Evidence

- `docs/mpc/mpc-v3g-output-bias-controller-contract.md`
- `docs/mpc/mpc-v3g-output-bias-replay-rejected.md`
- `results/mpc-v3g-real-trace-replay-20260822/replay.json`

### Dissertation use

Optional subsection:

- rejected alternative correction;
- reason output-bias correction was insufficient;
- justification for process/state-disturbance approach.

### Claim status

**OPTIONAL WRITING MATERIAL**

Do not spend additional development time on V3G.

---

## 7. V3H disturbance-estimator selection

### Evidence

- `docs/mpc/mpc-v3h-state-disturbance-evaluation-r2.md`
- `docs/mpc/mpc-v3h-alpha-tuning.md`
- Python V3H reference/controller tests
- corresponding result JSON files

### Dissertation use

Sections:

- process/state-disturbance formulation;
- alpha sensitivity;
- selection of alpha = 0.10;
- causal prediction correction.

### Claim status

**READY TO WRITE**

No further alpha tuning required.

---

## 8. V3H 4diac/FORTE implementation

### Evidence

- `docs/4diac/mpc-real-raw-safe-v3h-state-disturbance.md`
- V3H FBT under the 4diac type library;
- `docs/experiments/mpc-v3h-runtime-smoke-validation.md`
- `docs/experiments/mpc-v3h-protected-zero-output-20260822-analysis.md`

### Dissertation use

Sections:

- implementation in IEC 61499 / 4diac;
- FORTE export and runtime validation;
- safe deployment;
- zero-output commissioning.

### Claim status

**IMPLEMENTATION VALIDATED**

No additional build/smoke work required unless source code changes.

---

## 9. First active real V3H experiment

### Evidence

- `data/sample/mpc-v3h-first-active-20260822-124503/`
- `docs/experiments/mpc-v3h-first-active-60s-20260822-analysis.md`
- `docs/mpc/mpc-v3h-first-active-11750-plateau-diagnosis.md`
- `docs/mpc/mpc-v3h-first-active-internal-replay.md`

### Dissertation use

Sections:

- first real V3H active experiment;
- improved actuator direction;
- 11750-DAC plateau;
- internal replay;
- limitation of the assumed local actuator map.

### Claim status

**REAL V3H EVIDENCE AVAILABLE, FINAL REGULATION STILL OPEN**

Supported:

- bounded 60 s run;
- improved actuation direction;
- safe operation;
- plateau structurally reproduced by the model.

Not supported:

- exact dead-zone = 11750;
- final steady-state regulation validated;
- final physically representative operating-range validation.

---

## 10. Existing local dead-zone evidence audit

### Evidence

- `docs/mpc/mpc-local-deadzone-existing-evidence-audit.md`
- `results/mpc-local-deadzone-evidence-audit-20260822/`

### Dissertation use

Sections:

- justification for one focused additional local-identification experiment.

### Claim status

**READY**

No need to repeat the evidence audit.

---

## 11. 11600-DAC long-hold evidence

### Evidence

- `data/sample/local-deadzone-long-hold-20260822-131919/`
- `docs/experiments/local-deadzone-long-hold-11600-partial-20260822-analysis.md`

### Key observations

- AppliedDAC first reached 11600 after actuator acquisition;
- constant 11600 interval preserved;
- more than 5 tau of post-delay constant-target response available;
- clear late positive level response at 11600;
- physical maximum approximately 0.5 cm;
- output zero throughout recovery;
- zero-output sensor/plant baseline shifted relative to session start.

### Dissertation use

Sections:

- local actuator-map identification;
- justification for target-acquisition gating;
- justification for local rebaseline between points.

### Claim status

**VALID LOCAL DYNAMIC EVIDENCE**

Not sufficient alone to identify the exact real static dead-zone.

No automatic repeat required.

---

## 12. Remaining local actuator-map identification

### Prepared executor

- `scripts/local_deadzone_resume_11650_11900.py`
- `scripts/run_local_deadzone_resume_11650_11900.ps1`
- `docs/experiments/mpc-local-deadzone-resume-11650-11900-executor.md`

### Remaining evidence

Still required:

- 11650;
- 11700;
- 11750;
- 11800;
- 11850;
- 11900.

### Dissertation use

Will support:

- final local actuator-map decision;
- retain or minimally correct the Hammerstein input map.

### Claim status

**MANDATORY / WAITING FOR LAB**

---

## 13. Wide-range physical calibration

### Planning evidence

- `docs/experiments/mpc-wide-range-operating-envelope-validation-plan.md`
- `results/mpc-wide-range-validation-plan-20260822/plan.json`

### Required future measurements

- 0 cm;
- 2 cm;
- 5 cm;
- 10 cm;
- 15 cm.

### Dissertation use

Sections:

- sensor calibration;
- physical interpretation of raw counts;
- operating envelope;
- physically defensible safety limits.

### Claim status

**MANDATORY / WAITING FOR LAB**

20 cm is optional.

25 cm is the declared safe maximum, not a required validation setpoint.

40 cm is the overflow geometry reference.

---

## 14. Final PI-vs-MPC comparison

### Required future evidence

PI and MPC around:

- 5 cm;
- 10 cm;
- 15 cm.

### Required outputs

For each controller/setpoint:

- trajectory;
- physical setpoint;
- overshoot;
- settling behavior;
- MAE;
- RMSE;
- IAE;
- actuator total variation;
- maximum DAC;
- physical safety margin.

### Dissertation use

Primary final results section.

### Claim status

**MANDATORY / WAITING FOR LAB**

This is the main evidence still needed before the experimental chapter can be
closed.

---

## 15. Evidence that should not trigger new work

The following are already sufficient for their intended role:

- PI baseline;
- V3 bounded safety result;
- V3E expanded-envelope result;
- model mismatch diagnosis;
- V3G rejection;
- V3H estimator tuning;
- V3H 4diac/FORTE export/build/smoke;
- protected V3H zero-output commissioning;
- first active V3H run;
- 11750 plateau replay;
- existing local-evidence audit;
- 11600 long-hold point;
- wide-range validation rationale.

Do not repeat these solely to obtain cleaner numbers.

---

## 16. Minimum path to final figures

The remaining data dependency is:

1. collect 11650..11900;
2. make one final input-map/model decision;
3. calibrate 0/2/5/10/15 cm;
4. run PI and MPC at 5/10/15 cm;
5. generate final comparison tables/figures;
6. freeze experiments;
7. finish results/discussion/conclusion.

Everything else is secondary.

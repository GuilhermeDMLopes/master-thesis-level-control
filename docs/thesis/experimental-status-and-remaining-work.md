# Experimental status and minimum remaining work

## Purpose

This document freezes the experimental scope around the work already completed
and defines the minimum remaining work required to finish the dissertation.

The priority from this point forward is **completion**, not further expansion of
the control architecture.

A new activity is justified only if it directly:

- closes a missing experimental claim;
- produces evidence needed by a dissertation section;
- fixes a demonstrated defect that blocks one of the remaining mandatory tests.

Activities that merely improve architecture, generality, repository structure,
or controller sophistication are outside the minimum completion path.

---

## 1. Thesis objective retained

The dissertation remains focused on development and real-plant evaluation of
level-control strategies using:

- B&R PLC;
- OPC UA;
- Python gateway;
- Eclipse 4diac / FORTE;
- validated PI baseline;
- model predictive control on the real plant.

The final experimental narrative must compare the conventional baseline with
the MPC approach using physically meaningful evidence.

---

## 2. Work considered closed

The following topics are considered sufficiently established for the thesis and
must not be reopened without a concrete blocking defect.

### 2.1 PLC / gateway / FORTE communication

Status: **CLOSED**

Established:

- PLC B&R OPC UA communication;
- Python gateway communication;
- 4diac/FORTE integration;
- real signal read/write path;
- zero-output safety behavior;
- watchdog handling.

No architecture inversion or communication redesign is required for thesis
completion.

### 2.2 Real PI baseline

Status: **CLOSED / VALIDATED BASELINE**

Evidence exists for:

- real-plant operation;
- preserved monitor CSV;
- baseline analysis;
- controller parameters;
- dissertation comparison material.

The PI should only be run again when required for the final physically
calibrated PI-vs-MPC comparison.

### 2.3 Historical MPC V1/V2/V3/V3E development

Status: **CLOSED AS DEVELOPMENT HISTORY**

These variants remain important as engineering history and evidence for why the
final controller changed.

They are not candidates for additional tuning.

### 2.4 MPC V3H implementation

Status: **CURRENT MPC CONTROLLER / FROZEN**

Established:

- Python reference logic;
- causal state/process-disturbance correction;
- alpha = 0.10;
- 4diac implementation;
- FORTE export/build/type smoke;
- protected zero-output deployment;
- bounded real active run.

No MPC V3I/V4 or new estimator/controller architecture should be created unless
a remaining mandatory experiment demonstrates that V3H cannot be validated.

### 2.5 First active V3H result

Status: **PRESERVED, POSITIVE BUT NOT FINAL REGULATION VALIDATION**

Supported claims:

- bounded 60 s experiment completed;
- safety envelope respected;
- actuator command direction improved relative to V3E;
- V3H reached and held the lower effective-action region;
- final behavior was improved relative to the earlier high-DAC lock-in;
- exact static dead-zone remained unidentified;
- steady-state regulation was not yet validated.

### 2.6 Low-level experiments

Status: **COMMISSIONING / LOCAL IDENTIFICATION ONLY**

The experiments up to approximately 1.5 cm remain valid and useful for:

- commissioning;
- safety verification;
- local actuator-map diagnosis;
- MPC development.

They are explicitly **not** the final proof of controller performance over the
tank operating range.

---

## 3. Mandatory work remaining

Only the following laboratory tasks are considered mandatory at this point.

### M1. Finish local actuator-map identification

Remaining DAC points:

- 11650;
- 11700;
- 11750;
- 11800;
- 11850;
- 11900.

The already preserved 11600-DAC point is not repeated automatically.

Use the checkpointed protected resume executor.

Purpose:

- determine the local actuator/input behavior around the current model
  transition;
- verify whether the assumed Hammerstein input map is adequate;
- provide one final basis for retaining or minimally correcting the input map.

**Stop rule:** once these points are available, do not create a larger
identification campaign unless the data are unusable.

### M2. Make one final model decision

After M1:

- compare the measured local input response with the current MPC input map;
- retain the current map if adequate, or apply the smallest supported
  correction;
- validate it offline;
- freeze the model.

**Maximum expected outcome:** one minimal model/input-map correction.

**Not allowed by default:** new MPC variant sequence or redesign of the
controller objective.

### M3. Physical raw-to-cm calibration

Required nominal physical points:

- 0 cm;
- 2 cm;
- 5 cm;
- 10 cm;
- 15 cm.

Purpose:

- establish an empirical raw-to-cm relationship;
- quantify the usable physical operating range;
- define defensible raw limits from physical measurements.

The 20 cm point is **optional**, not mandatory.

The 25 cm value remains the declared operational safe maximum.

The 40 cm value remains the overflow geometry reference, not an experimental
target.

### M4. Final PI-vs-MPC validation at multiple physical setpoints

Minimum final comparison:

- approximately 5 cm;
- approximately 10 cm;
- approximately 15 cm.

Preferred methodology:

- physically calibrated setpoints;
- comparable initial conditions;
- comparable duration;
- same safety criteria;
- PI and MPC both evaluated.

Required reported metrics:

- overshoot;
- settling behavior;
- MAE;
- RMSE;
- IAE;
- actuator total variation;
- maximum DAC;
- physical safety margin.

This is the principal remaining experimental evidence needed for the thesis.

---

## 4. Optional work

The following items are optional and should be skipped if the mandatory evidence
is already adequate.

### O1. 20 cm physical calibration / control point

Use only if:

- 0/2/5/10/15 cm calibration is reliable;
- 5/10/15 cm controller tests are safe;
- the additional point materially strengthens the dissertation.

Otherwise omit it.

### O2. Longer-duration final MPC run

Use only if the 5/10/15 cm experiments leave a genuine ambiguity about
settling or steady-state behavior.

Do not add longer runs merely to collect more data.

### O3. Additional model identification

Use only if M1 fails to support either the current input map or one minimal
correction.

---

## 5. Explicitly out of scope unless blocking

Do not start the following work unless it becomes necessary to complete a
mandatory item:

- new MPC versions beyond V3H;
- alternative optimizers;
- new gateway architecture;
- PLC/FORTE architecture inversion;
- new repository restructuring;
- generic experiment frameworks;
- automatic report systems beyond what is needed for the final figures;
- new filters or observers;
- extensive sensitivity campaigns;
- raw-limit increases without physical calibration;
- additional setpoints above 15 cm by default.

---

## 6. Experimental completion criteria

The experimental phase can be declared complete when all conditions below are
true.

### Required

- [ ] local 11650..11900 actuator-map evidence collected;
- [ ] one final input-map/model decision documented;
- [ ] V3H/model frozen;
- [ ] raw-to-cm calibration available for 0/2/5/10/15 cm;
- [ ] PI experiment available at approximately 5 cm;
- [ ] PI experiment available at approximately 10 cm;
- [ ] PI experiment available at approximately 15 cm;
- [ ] MPC experiment available at approximately 5 cm;
- [ ] MPC experiment available at approximately 10 cm;
- [ ] MPC experiment available at approximately 15 cm;
- [ ] final comparison metrics/figures generated;
- [ ] validated physical operating range stated honestly.

### Not required

- [ ] 20 cm test;
- [ ] 25 cm test;
- [ ] full 0..40 cm validation;
- [ ] new MPC architecture;
- [ ] new communication architecture.

---

## 7. Writing can proceed before the final laboratory work

The following dissertation content can already be written:

- system architecture;
- PLC/gateway/4diac integration;
- experimental plant description;
- PI implementation;
- initial identification methodology;
- MPC model structure;
- MPC V1/V2/V3/V3E development rationale;
- model mismatch diagnosis;
- disturbance-estimator motivation;
- V3H formulation;
- software/runtime validation;
- zero-output commissioning;
- first bounded real V3H run;
- limitations of low-level commissioning data;
- planned physically calibrated final validation.

The final PI-vs-MPC results chapter should remain open for the 5/10/15 cm data.

---

## 8. Decision rule from this point forward

Before adding any new technical task, ask:

> Does this task directly close one of M1, M2, M3, M4, or a dissertation section?

If the answer is no, defer it.

The project is now in **thesis completion mode**, not exploratory controller
development mode.

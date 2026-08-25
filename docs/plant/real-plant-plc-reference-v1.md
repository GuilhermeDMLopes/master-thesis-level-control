# Real plant, PLC and watchdog reference V1

## 1. Purpose and scope

This document is the canonical engineering reference for the physical level
control plant used in the master thesis.

It consolidates:

- physical tank geometry and manually measured limits;
- sensor/transmitter information;
- PLC and Automation Studio configuration;
- OPC UA interface;
- watchdog and fail-safe output architecture;
- the exact TON-less watchdog patch logic preserved from the laboratory work;
- inverter parameter values recorded during commissioning;
- observed operating points;
- PI baseline and nonlinear MPC model reference values.

The document intentionally distinguishes exact digital configuration from
approximate physical measurements.

It is not a replacement for the original Automation Studio project.

## 2. Evidence classification

| Classification | Meaning |
|---|---|
| Configuration evidence | Recovered from Automation Studio validation/report files or versioned project artifacts |
| Exact patch code | Copied from the preserved watchdog patch package |
| Manual measurement | Measured manually at the physical plant; approximate unless stated otherwise |
| Experimental observation | Value observed during a laboratory test |
| Identified model parameter | Estimated from experimental data; not a direct physical measurement |
| Adopted operating limit | Engineering limit used by this project for safe experimentation |

## 3. Experimental architecture

The experimentally used control path is:

```text
physical plant
    ↑ ↓
B&R PLC
    ↕ OPC UA
Python gateway
    ↕ OPC UA
Eclipse 4diac / FORTE
    ↓
PI baseline or MPC controller
```

The Python gateway exists because the FORTE/4diac communication path used by the
project could not directly use the PLC NodeId naming in the required way.

PLC endpoint:

```text
opc.tcp://10.0.0.3:4840
```

Gateway endpoint:

```text
opc.tcp://127.0.0.1:4841
```

Gateway namespace URI:

```text
urn:br-4diac-gateway
```

Gateway nominal cycle:

```text
0.1 s
```

## 4. Physical plant geometry

| Item | Value | Classification |
|---|---:|---|
| Tank shape | Cylindrical | Manual observation |
| Tank internal/visible diameter | approximately 28 cm | Manual measurement |
| Bottom drain diameter | approximately 1.5 cm | Manual measurement |
| Bottom to start of sensor connection tube | approximately 1.3 cm | Manual measurement |
| Bottom to overflow lip | approximately 40 cm | Manual measurement |
| Adopted operationally safe maximum level | 25 cm | Adopted operating limit |

### 4.1 Permanent drain

The tank has a permanently open bottom drain.

It is a physical hole connected through a pipe to the lower reservoir. There is
no adjustment valve in this drain path.

Therefore, when the pump is turned off, water returns to the lower reservoir and
the measured tank level is not cumulative.

This point is fundamental to the plant model:

```text
level dynamics = pump inflow - permanent drain outflow
```

The system must therefore be treated as a process with an operating equilibrium,
not as a simple tank that integrates pump volume indefinitely.

## 5. Sensor and level signal

Sensor/transmitter reported for the plant:

```text
ABB 2600TT
```

The pressure/sensing tubing is connected to the tank/reservoir measurement path.

PLC variable:

```text
Nivel : INT
```

The Automation Studio validation evidence confirms that `Nivel` remains mapped
to the physical input.

### 5.1 Raw signal versus physical height

Early project work used a computational scaling of:

```text
Nivel_cm = Nivel_raw / 1000
```

That scaling was useful for the original PI baseline implementation but must not
be interpreted as a complete independent physical calibration of the final
plant.

Subsequent manual experiments showed that the raw signal has noise/offset and
that the permanent drain strongly affects steady operating levels.

For MPC work, the current model therefore uses the experimentally identified raw
level domain directly.

## 6. PLC and Automation Studio

Controller family/configuration evidence:

```text
B&R X20CP0483
```

Automation Studio version recorded during the project:

```text
4.10.2.37
```

Automation Runtime recorded in the validated OPC UA map:

```text
B4.91
```

Validated watchdog working-copy project path from the evidence:

```text
C:\projects\mestrado_guilherme_watchdog_v2_20260403-021715
```

Project:

```text
PLANTA_LCPIC
```

Key project files referenced by the validators:

```text
Logical\Program\Variables.var
Logical\Program\Init.st
Logical\Program\Cyclic.st
Logical\Program\Exit.st

Physical\Config1\X20CP0483\IoMap.iom
Physical\Config1\X20CP0483\Connectivity\OpcUA\OpcUaMap.uad
Physical\Config1\Hardware.hw
```

## 7. Program variables

The pre-rebuild and OPC UA finalizer validation evidence confirms these
declarations:

```iecst
Nivel           : INT;
Enable          : BOOL;
DAC             : INT;
Heartbeat       : UDINT;
SafetyReset     : BOOL;

EnableOut       : BOOL;
DACOut          : INT;

WatchdogHealthy : BOOL;
WatchdogTripped : BOOL;

AppliedEnable   : BOOL;
AppliedDAC      : INT;
```

The final TON-less patch additionally introduces:

```iecst
WdCyclesWithoutHeartbeat : UDINT;
WdTimeoutCycles          : UDINT;
WdTimedOut               : BOOL;
```

Other internal watchdog state, including the heartbeat/latch state, is preserved
in the Automation Studio source/validation evidence and is intentionally not
reconstructed here without the complete final source files.

## 8. PLC task timing used by the watchdog

The OPC UA finalizer report recorded:

```text
Detected Program task classes: 4
Cyclic4 duration raw: 100000
derived duration: 100 ms
Cyclic4 tolerance raw: 100000
derived tolerance: 100 ms
```

The evidence package still notes that the task name/priority assignment required
manual review. This reference therefore treats **100 ms** as the validated
watchdog timing basis without inventing an unrecorded priority.

## 9. Watchdog design

### 9.1 Purpose

The watchdog prevents stale external control commands from remaining physically
applied when the gateway/control path stops refreshing its heartbeat.

The architecture distinguishes requested command variables from physically
applied variables.

Requested through OPC UA:

```text
Enable
DAC
```

Safety-gated feedback:

```text
AppliedEnable
AppliedDAC
WatchdogHealthy
WatchdogTripped
```

Physical output variables:

```text
EnableOut
DACOut
```

The Automation Studio validation confirms that the old direct physical mappings
to `Enable` and `DAC` were removed and that the physical outputs are instead
mapped to:

```text
::Program:EnableOut
::Program:DACOut
```

The cyclic logic then gates these outputs through:

```iecst
EnableOut := AppliedEnable;
DACOut := AppliedDAC;
```

### 9.2 Fail-safe initialization and exit

Validation evidence confirms that `Init.st` initializes the command/output path
to a safe state including:

```iecst
Enable := FALSE;
DAC := 0;
EnableOut := FALSE;
DACOut := 0;
WdTripLatched := TRUE;
```

Validation evidence confirms that `Exit.st` also forces:

```iecst
Enable := FALSE;
DAC := 0;
EnableOut := FALSE;
DACOut := 0;
WdTripLatched := TRUE;
```

The exact complete source files are not reconstructed in this document.

### 9.3 Initial TON implementation and rebuild failure

The first watchdog implementation used:

```iecst
WdTimer : TON;
```

with an intended timeout:

```iecst
PT := T#1s
```

The first recorded rebuild after this work produced:

```text
Build: 4 error(s), 7 warning(s)
```

The preserved TON-less patch README records the blocking compiler condition as:

```text
Unknown data type: TON
Data type TON not defined
```

### 9.4 Final TON-less implementation

The final patch replaces the unsupported timer FB with a deterministic cycle
counter.

Given the validated 100 ms timing basis:

```text
10 cycles × 100 ms ≈ 1 s watchdog timeout
```

The exact replacement code in the preserved patch is:

```iecst
WdCyclesWithoutHeartbeat := 0;
WdTimeoutCycles := 10;
WdTimedOut := TRUE;
```

and the cyclic counter logic is:

```iecst
IF WdHeartbeatChanged THEN
    WdHeartbeatLast := Heartbeat;
    WdHeartbeatSeen := TRUE;
    WdCyclesWithoutHeartbeat := 0;

ELSIF WdHeartbeatSeen THEN
    IF WdCyclesWithoutHeartbeat < WdTimeoutCycles THEN
        WdCyclesWithoutHeartbeat := WdCyclesWithoutHeartbeat + 1;
    END_IF;

ELSE
    WdCyclesWithoutHeartbeat := 0;
END_IF;

WdTimedOut := (
    WdHeartbeatSeen
    AND
    (WdCyclesWithoutHeartbeat >= WdTimeoutCycles)
);
```

The patch replaces references to the original timer output:

```text
WdTimer.Q
```

with:

```text
WdTimedOut
```

while preserving the existing watchdog latch and safe physical-output gate.

On exit, the TON-less patch establishes:

```iecst
WdCyclesWithoutHeartbeat := 0;
WdTimedOut := TRUE;
```

### 9.5 Successful rebuild evidence

The second post-rebuild collection records:

```text
Errors displayed: 0
Warnings displayed: 1
Final result text: Rebuild has been executed.
```

This is the preserved successful build evidence after the TON-less correction.

### 9.6 Previously observed watchdog behavior

A project commissioning test previously observed the watchdog removing applied
output after approximately:

```text
1.094 s
```

with the safe feedback state:

```text
WatchdogHealthy = FALSE
WatchdogTripped = TRUE
AppliedEnable   = FALSE
AppliedDAC      = 0
```

This value is an experimental observation, not the configured timeout itself.
The configured TON-less threshold is 10 cycles on the 100 ms timing basis.

## 10. OPC UA publication

The final Automation Studio OPC UA map publishes exactly these task variables:

```text
Nivel
DAC
Enable
Heartbeat
SafetyReset
WatchdogHealthy
WatchdogTripped
AppliedEnable
AppliedDAC
```

The finalizer evidence explicitly verifies that physical output variables such
as `EnableOut` and `DACOut`, and internal `Wd...` state variables, are not
published.

The finalizer also records the access-right requirement:

```text
Heartbeat and SafetyReset must be writable.
```

Diagnostic variables are written by PLC cyclic logic and do not bypass the
physical-output safety gate.

### 10.1 PLC NodeIds used by the current gateway/guard

The validated project contract uses:

```text
ns=6;s=::Program:Nivel
ns=6;s=::Program:Enable
ns=6;s=::Program:DAC
ns=6;s=::Program:Heartbeat
ns=6;s=::Program:SafetyReset
ns=6;s=::Program:WatchdogHealthy
ns=6;s=::Program:WatchdogTripped
ns=6;s=::Program:AppliedEnable
ns=6;s=::Program:AppliedDAC
```

## 11. Inverter / pump-drive parameter records

The following parameter IDs and values were manually read during the plant
investigation.

No semantic name is assigned here unless independently verified from the drive
documentation.

```text
1103: 1
1104: 0.0
1105: 50.0

1301: 0.0
1302: 100.0

2007: 0.0
2008: 50.0

2202: 5.0
2203: 5.0

9902: 1
```

Additional displayed values recorded:

```text
0103: 11.1
0111: 11.1
0120: 34.3
```

Observed drive frequencies during manual characterization included:

```text
17.1 Hz
18.6 Hz at approximately 1.0 cm physical level
20.1 Hz at approximately 1.5 cm physical level
```

The physical heights above were approximate manual readings.

## 12. Pump and plant operating observations

Important experimental observations:

- low DAC values can produce little or no useful water delivery;
- a strong effective input dead-zone exists;
- the permanent drain continuously removes water from the tank;
- turning the pump off causes water to return to the lower reservoir;
- very short pump pulses may produce visible flow without a measurable retained
  level;
- a stationary level requires pump inflow to balance the permanent drain.

One manual pulse experiment at DAC 12000 with a 5 s target hold produced only an
approximately 0.6 cm physical reading before the water returned through the
drain. This value was explicitly recorded as approximate.

## 13. Historical PI baseline reference

The validated historical PI baseline used:

```text
SP = 14.0 cm
KP = 4.0
KI = 0.50
KD = 0.0
Ts = 0.1 s

PV filter ALPHA = 0.95

DAC range = 0 .. 32000
maximum DAC change per controller cycle = 150
```

This PI configuration is preserved as the experimental baseline for comparison.
It is not the current MPC plant model.

## 14. Current nonlinear MPC plant-model reference

The selected dead-zone Hammerstein model checkpoint uses:

```text
tau_s = 32.0
baseline raw = 298.0
dead-zone DAC = 11750.0
input exponent = 1.2
equilibrium gain = 0.680487474306
implied equilibrium DAC at target = 11840.681677...
```

Model quality recorded during identification:

```text
training rollout RMSE = 117.439421 raw
validation rollout RMSE = 55.744873 raw
validation rollout MAE = 49.002777 raw
validation bias = 18.175759 raw
validation max abs error = 136.848347 raw
```

The subsequent offline nonlinear MPC robustness campaign passed:

```text
10 / 10 scenarios
```

These are identified/model-validation values, not direct hardware dimensions.

## 15. Current physical and experimental safety constraints

Project constraints currently used for real-plant work include:

```text
operational level limit: 25 cm
overflow lip: approximately 40 cm
physical stop must be accessible during active experiments
```

The first real MPC deployment remains a disabled/zero-output experiment.

During that step:

```text
MpcController.ENABLE_REQUEST = FALSE
```

must remain false.

The independent zero-output guard must remain the acceptance authority for:

```text
Enable
DAC
AppliedEnable
AppliedDAC
WatchdogHealthy
```

## 16. Evidence and reproducibility

The watchdog source/evidence archive is preserved under:

```text
docs/evidence/automation-studio-watchdog-v2/
```

The original ZIP files are preserved byte-for-byte with SHA256 hashes.

The exact finalizer, rebuild validator and TON-less patch scripts are also
extracted for direct inspection.

The large generated post-build diagnostic dumps remain inside their ZIP archives
only.

## 17. Known limitations

1. Several tank dimensions were measured manually and are approximate.
2. The uploaded watchdog evidence packages are not a complete byte-for-byte
   snapshot of all final Automation Studio source files.
3. The exact watchdog patch and the validation criteria are preserved, but this
   document does not silently invent source lines that are absent from the
   evidence.
4. Inverter parameter semantic names are not assigned without the corresponding
   verified drive manual.
5. The raw level signal is the current MPC modeling domain; the historical
   `/1000` PI scaling is not treated as a universal physical calibration.

## 18. Thesis relevance

This reference supports the dissertation sections covering:

- experimental bench;
- plant geometry;
- instrumentation;
- PLC implementation;
- OPC UA communication;
- fail-safe/watchdog design;
- PI baseline;
- system identification;
- nonlinear MPC implementation and validation.

## 19. Status at end of offline preparation

```text
offline nonlinear MPC model: validated
additive 4diac MPC V1: preserved
MPC-capable FORTE: built and runtime-type validated
FORTE runtime artifacts: preserved
FORTE build recipe: reproducible
zero-output guard: automated contract tested
laboratory return runbook: versioned
plant/PLC/watchdog reference: this document
```

REAL MPC AUTHORIZED: **NO**

The next useful engineering activity requires physical access to the laboratory:
the protected zero-output deployment of `ResRealRawMPCV1`.
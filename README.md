# Level Control with 4diac, FORTE, OPC UA, and a B&R PLC

## Overview

This repository contains the software, engineering artifacts, automated tests, experimental procedures, and datasets developed for a master's thesis on level control using:

- a real B&R PLC;
- OPC UA communication;
- a Python integration gateway;
- Eclipse 4diac IDE;
- Eclipse 4diac FORTE;
- a validated real-plant PI baseline;
- a Model Predictive Controller implemented in 4diac and validated on the real plant at the physical 15 cm operating point.

The research objective is to develop, validate, and compare PI and MPC control strategies on a real level-control process while preserving reproducibility, operational safety, and the complete engineering history of the project.

## Current Project Status

The complete PLC-gateway-FORTE path, the fail-closed raw-count PI baseline, the final matched PI baseline, and the high-range MPC V4 implementation have been validated on the real plant. Under the common bounded 180 s protocol, MPC V4 reached and stabilized at the physically measured 15 cm target, while the matched PI reached 14.7 cm. Both runs maintained a healthy watchdog state and ended with independently verified zero output.

The final PI-MPC comparison, reproducible metrics, figures, limitations, and source-evidence hashes are complete and integrated into `main`.

Validated checkpoints:

| Checkpoint | Git reference | Result |
|---|---|---|
| Initial repository and gateway baseline | `baseline-gateway-v1` | Repository, Python environment, gateway source, and complete 4diac project validated |
| Real FORTE/gateway communication with zero output | `real-forte-zero-output-v1` | PLC-gateway-FORTE communication validated without positive actuator output |
| Real raw-count PI baseline | `real-raw-pi-v1` | Safe real-plant PI test completed, evidence preserved, and automated acceptance criteria passed |
| MPC preparation and real evidence | `7d9a3b5` | M1-M4 evidence integrated, including calibration, model identification and staged real-plant datasets |
| Final MPC V4 implementation | `3d1fa16` | Additive high-range 4diac MPC V4 application and validation workflow added |
| Final 15 cm target refinement | `82f0978` | V4 target refined from the observed 14 cm response to `SP_RAW=17000` |
| Final mapped V4 application | `ca02fe7` | Mapped target and 4diac layout synchronized before the successful final run |

The complete automated test suite contains **507 passing tests** after the final evidence closure. The validated repository state is preserved by the annotated tag `thesis-real-plant-validation-20260901`.
final evidence closure.

The selected application is `MPC_REAL_RAW_SAFE_V4`, mapped to
`FORTE_PC.ResRealRawMPCV4`. The exact generated module, custom FORTE runtime,
experimental CSV files, metrics and figures are preserved in the repository.
The validated PI path remains available as the experimental baseline and
fallback.

## Current Architecture

```text
B&R PLC OPC UA server
    |
    v
Python gateway
PLC OPC UA client + local OPC UA server
    |
    v
Custom 4diac FORTE V4 runtime
    |
    v
MPC_REAL_RAW_SAFE_V4
    +-- MPC_MEDIAN_FILTER_9
    +-- MPC_MOVE_BLOCKED_NMPC_V4
    +-- SAFE_DAC_RATE_LIMITER
    +-- OPC UA DAC and Enable writers
```

Current communication path:

```text
B&R PLC <-> Python gateway <-> 4diac FORTE
```

The PI application remains the validated experimental baseline and fallback.
The V4 application is the final MPC implementation and the V3H applications
remain preserved as commissioning history.

## Why the Python Gateway Is Required

The B&R PLC exposes the process variables through an OPC UA server. However, 4diac FORTE could not reliably use the original NodeIds exposed by the PLC.

The Python gateway is therefore maintained as an explicit integration layer. It:

- connects to the B&R OPC UA server;
- reads process variables, actuator feedback, watchdog state, and safety state;
- exposes simplified OPC UA NodeIds for FORTE;
- receives control commands from FORTE;
- writes permitted commands to the B&R PLC;
- records experimental data;
- supports heartbeat and communication diagnostics;
- participates in the fail-closed command path.

The simplified NodeIds used by the existing 4diac applications remain:

```text
Nivel
Enable
DAC
```

Changing these names requires a coordinated migration of the gateway and the 4diac applications and is not part of the validated final architecture.

## Safety Architecture

The real plant is operated through a fail-closed command path.

A communication failure, stale heartbeat, unhealthy gateway state, controlled shutdown, or related safety trip must result in:

```text
Enable = FALSE
DAC = 0
```

The PLC remains the final authority for the applied actuator state. Test procedures distinguish commanded values from values confirmed and applied by the PLC.

The real-plant workflows include:

1. preflight validation;
2. controlled stack startup;
3. controlled experiment execution;
4. explicit physical-stop confirmation;
5. stack shutdown;
6. final PLC safe-trip verification;
7. evidence preservation;
8. automated test execution.

Do not bypass PLC interlocks, watchdog logic, physical stop procedures, or the documented test workflow.

## Validated Real PI Baseline

The validated real-plant controller is the additive 4diac application documented as `PI_REAL_RAW_SAFE`.

Its current purpose is to provide:

- a safe and reproducible real PI baseline;
- a fallback controller during MPC development;
- reference data for model identification and controller comparison;
- a stable interface for the existing PLC-gateway-FORTE architecture.

The baseline uses raw level counts in the validated control path. Historical applications using other scaling and control structures remain preserved in the 4diac project.

The final baseline experiment produced:

- 427 recorded rows;
- 167 automatic-control rows;
- an automatic DAC range of 648 counts;
- an automatic rolling-median range from 318 to 736 counts;
- a preserved evidence CSV with recorded SHA-256 integrity information;
- a successful final PLC safe-trip check;
- 149 passing automated tests.

Evidence files:

```text
data/sample/real-raw-pi-v1-monitor.csv
docs/experiments/real-raw-pi-baseline-validation.md
docs/4diac/pi-real-raw-safe-application.md
```

The baseline establishes a valid experimental reference. It does not claim that the current PI gains are globally optimal.

## Current 4diac Project

The engineering project is:

```text
OPAS_Tank_System
```

Repository location:

```text
4diac/application/OPAS_Tank_System/
```

The final validated MPC application is:

```text
Application: MPC_REAL_RAW_SAFE_V4
Resource: FORTE_PC.ResRealRawMPCV4
Controller: MPC_MOVE_BLOCKED_NMPC_V4
Filter: MPC_MEDIAN_FILTER_9
Safety limiter: SAFE_DAC_RATE_LIMITER
Setpoint: 17000 raw (physically observed as 15 cm)
DAC range: 0..16000
```

The application retains fail-closed defaults, including `ENABLE_REQUEST=FALSE`, and uses real level, watchdog, and applied-DAC feedback from the gateway path.

The complete project must remain versioned, including:

- `.project`;
- `OPAS_Tank_System.sys`;
- local function block definitions;
- the complete `Type Library`;
- historical communication applications;
- historical PI/PID applications;
- MPC development artifacts;
- intermediate and experimental applications.

Changes to the 4diac project must be additive and documented. Existing historical applications and function blocks must not be deleted, renamed, or overwritten merely to simplify the final implementation.

Historical MPC artifacts remain preserved, while `MPC_REAL_RAW_SAFE_V4` is the final validated application.

## Repository Structure

```text
.
|-- .gitignore
|-- README.md
|-- requirements.txt
|-- requirements-dev.txt
|-- 4diac
|   |-- application
|   |   `-- OPAS_Tank_System
|   `-- function-blocks
|-- data
|   |-- raw
|   `-- sample
|-- docs
|   |-- 4diac
|   |-- architecture
|   |-- current-state
|   |-- experiments
|   `-- testing
|-- forte
|   |-- custom-blocks
|   `-- preserved-v4
|-- gateway
|   |-- config
|   `-- src
|-- results
|-- scripts
|   `-- pi_tuned_test
|-- simulation
`-- tests
```

### `4diac/application`

Contains the complete Eclipse 4diac engineering project. Always copy and version the complete project directory rather than selected `.sys` or `.fbt` files.

### `forte/preserved-v4`

Contains the exact final MPC V4 runtime, its adjacent `open62541.dll`, the
generated custom-block sources and the historical build provenance. The
canonical executable and its required DLL are intentionally stored together at
`forte/preserved-v4/runtimes/mpc-v4-candidate/`.

### `forte/custom-blocks`

Contains earlier C++ source exported or implemented for historical custom FORTE
builds.

### `gateway`

Contains the Python OPC UA integration gateway.

Current entry point:

```text
gateway/src/gateway_opcua.py
```

### `scripts`

Contains experiment managers, controlled commissioning workflows, identification tools, and auxiliary processing scripts.

Relevant current tools include:

```text
scripts/open_loop_identification.py
scripts/pi_tuned_test/
```

### `data/raw`

Contains raw experimental outputs. These files are ignored by Git by default.

### `data/sample`

Contains selected, non-sensitive, versioned evidence datasets used for validation, documentation, and tests.

### `results`

Contains generated plots, identified models, processed tables, and comparison outputs. Generated content is normally ignored unless explicitly selected as thesis evidence.

## Main Technologies

- Python
- `asyncua`
- OPC UA
- Eclipse 4diac IDE
- Eclipse 4diac FORTE
- IEC 61499
- Structured Text
- B&R PLC
- Git
- GitHub
- `pytest`

## Installing and Running the Complete Project

This repository supports three distinct activities:

1. **offline reproduction**, which recalculates evidence and runs tests without
   the PLC, gateway or FORTE;
2. **4diac engineering**, which opens and inspects the IEC 61499 project;
3. **real-plant execution**, which requires the laboratory network, the B&R PLC,
   the protected supervisor and immediate access to the physical stop.

### 1. Obtain the repository

```powershell
git clone https://github.com/GuilhermeDMLopes/master-thesis-level-control.git
Set-Location .\master-thesis-level-control
git switch main
```

For exact reproduction of a historical experiment, switch to the Git commit or
tag named by its analysis document instead of `main`.

### 2. Install Python and project dependencies

Install a supported Python 3 version, create `.venv` and install both dependency
sets as described in [Python Environment](#python-environment). Run `pip check`
and the complete offline test suite before connecting to any runtime.

### 3. Download and install 4diac IDE

The official downloads are available at:

- <https://eclipse.dev/4diac/download/>
- <https://eclipse.dev/4diac/doc/installation/>

The project was created and validated with **4diac IDE 2.0.1**. For the closest
reproduction, open **Older Eclipse 4diac Releases**, select **2.0.1**, download
the package for the operating system, extract it to a local directory and run
the included 4diac IDE executable. No installer is required.

The latest IDE may be used for inspection, but importing and saving the project
with a newer major version can rewrite engineering files. Do that only in a
separate Git branch and inspect the resulting diff. The official introductory
tutorial is available at <https://eclipse.dev/4diac/doc/tutorials/>.

### 4. Open the engineering project

1. Start 4diac IDE and select a workspace outside the Git repository.
2. Select **File > Import > General > Existing Projects into Workspace**.
3. Use `4diac/application` as the root directory.
4. Import `OPAS_Tank_System` without copying it into the workspace.
5. Open `OPAS_Tank_System.sys`.
6. For the final controller, select `MPC_REAL_RAW_SAFE_V4` and confirm that it is
   mapped to `FORTE_PC.ResRealRawMPCV4`.

Do not delete or replace the historical applications. They are part of the
experimental record.

### 5. Reproduce the final result offline

The following commands require no laboratory connection:

```powershell
.\.venv\Scripts\python.exe scripts\analyze_mpc_v4_target17000.py
.\.venv\Scripts\python.exe -m pytest -q
```

The analysis recreates `metrics.json` and the PNG/SVG figures from the frozen
CSV. The expected test result is `507 passed`.

### 6. Use the correct FORTE runtime

Do not use a generic FORTE executable for the final MPC. It does not contain the
custom V4 function blocks. The accepted Windows runtime is preserved at:

```text
forte/preserved-v4/runtimes/mpc-v4-candidate/forte.exe
forte/preserved-v4/runtimes/mpc-v4-candidate/open62541.dll
```

The preserved `forte.exe` SHA-256 is:

```text
62AB0F00FB1DFE30E89BF89D81249A83AEBBEABE9A7565327BFB3B7FBA536C60
```

Generated source and historical build provenance are under
`forte/preserved-v4/external-modules/MPC_V4/` and `forte/preserved-v4/build/`.
The preserved build script records the original pinned build environment; the
already preserved runtime is the canonical executable for reproducing the
validated experiment.

### 7. Start the real stack in the laboratory

Real-plant execution must not be attempted unless the physical stop is
accessible, the tank and reservoir are ready, the PLC interlocks are active,
and ports 4841 and 61499 are initially free.

In terminal A, from the repository root, start the gateway:

```powershell
.\.venv\Scripts\python.exe .\gateway\src\gateway_opcua.py
```

In terminal B, start the preserved runtime from its own directory so that
`open62541.dll` is resolved correctly:

```powershell
$runtime = Join-Path `
    (Get-Location).Path `
    "forte\preserved-v4\runtimes\mpc-v4-candidate"

Set-Location $runtime
.\forte.exe
```

The expected listeners are gateway port 4841 and FORTE management port 61499.

### 8. Deploy and initialize the final resource

With `ENABLE_REQUEST=FALSE` and zero output already confirmed:

1. deploy only `FORTE_PC -> ResRealRawMPCV4`;
2. do not deploy the full System or full Device;
3. confirm that the Deployment Console contains no unsupported-type or
   missing-object error;
4. trigger `MpcInitMerge.EI1` exactly once on the fresh deployment;
5. keep `ENABLE_REQUEST=FALSE` until the independent supervisor reports that it
   is armed.

### 9. Execute a bounded real-plant run

First inspect the plan:

```powershell
.\.venv\Scripts\python.exe `
    .\scripts\mpc_high_range_validation.py `
    --plan
```

Then run the protected supervisor using the PID of the exact FORTE process:

```powershell
.\.venv\Scripts\python.exe `
    .\scripts\mpc_high_range_validation.py `
    --run `
    --forte-pid <FORTE_PID>
```

Type the requested confirmation token only after checking the physical plant.
When the supervisor prints `ARMED`, manually change only
`MpcController.ENABLE_REQUEST` to `TRUE` in 4diac. Do not change the target,
model or safety limits during the run.

The final validated configuration uses `SP_RAW=17000`, `DAC_MAX=16000`, a
19000-raw median supervisor ceiling, a 20000-raw instantaneous ceiling and a
20 cm physical operator-abort threshold. On completion or violation, the
supervisor terminates FORTE, writes safe zero and verifies the applied state.

### 10. Finish safely

After every real run, confirm `Enable=FALSE`, `DAC=0`,
`AppliedEnable=FALSE`, `AppliedDAC=0`, stop the gateway and verify that ports
4841 and 61499 are closed. Preserve the generated evidence directory before
starting another experiment.

The successful dissertation experiment does not authorize unattended or
unrestricted future real-plant operation.

## Python Environment

Create a virtual environment from the repository root:

```powershell
python -m venv ".venv"
```

Install runtime and development dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Check the environment:

```powershell
.\.venv\Scripts\python.exe -m pip check
```

## Final Real-Plant Execution Assets

The exact gateway, 4diac engineering project, preserved FORTE runtime and bounded supervisors used for the accepted MPC V4 and matched PI experiments are versioned in this repository. Their roles, controller mappings, laboratory sequence and safe demonstration commands are recorded in [`docs/experiments/final-real-plant-execution-assets.md`](docs/experiments/final-real-plant-execution-assets.md).

The `--plan` modes can be used to demonstrate the validated configurations without plant actuation. The `--run` modes belong exclusively to the supervised laboratory procedure and can command the real pump when the approved stack is connected.

## Automated Testing

The automated test suite provides regression protection for the complete experimental chain. At a general level, it verifies the structural integrity and historical preservation of the 4diac project; communication and data-type contracts across the gateway, FORTE, and PLC interfaces; controller configuration, prediction, filtering, actuator constraints, and fail-closed safety behavior; controlled CLI preconditions and zero-output procedures; and the integrity and reproducibility of preserved experimental evidence, metrics, figures, and documentation.

These tests are deterministic and run offline. They do not replace real-plant experiments; their purpose is to ensure that later code or documentation changes do not invalidate the software, safety contracts, evidence, or conclusions that were already validated on the physical plant.

Run the complete offline test suite from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

When the virtual environment is already active:

```powershell
python -m pytest -q
```

Current validated result after the final PI-MPC evidence closure:

```text
507 passed
```

The offline tests do not require access to the B&R PLC, FORTE, or the laboratory network.

Testing documentation:

```text
docs/testing/testing-guide.md
```

## Gateway Execution

Run the gateway only in the intended laboratory environment or against an approved test/simulation endpoint:

```powershell
python gateway/src/gateway_opcua.py
```

The gateway may attempt to connect to the configured real B&R endpoint. Verify the active configuration before execution.

Before a real-plant connection, confirm:

- B&R OPC UA endpoint;
- B&R NodeIds;
- gateway OPC UA endpoint;
- OPC UA data types;
- heartbeat and watchdog behavior;
- level signal interpretation;
- DAC limits and sign;
- command and feedback consistency;
- Enable behavior;
- PLC interlocks;
- physical emergency and safe-stop procedures.

## Real-Plant Experiment Evidence

Raw experiment files are written under:

```text
data/raw/
```

Only selected evidence files should be copied to `data/sample/` and committed. Each preserved experiment should include:

- source path;
- experiment date and purpose;
- row count and test phases;
- controller configuration;
- acceptance criteria;
- safety result;
- integrity hash;
- analysis document;
- associated commit or Git tag.

## Development Roadmap

### Completed - Repository and Historical Preservation

- organized the repository;
- preserved the complete `OPAS_Tank_System` project;
- created automated preservation checks;
- validated a clean clone and rebuild workflow;
- established Git references for reproducible checkpoints.

### Completed - Communication and Fail-Closed Integration

- validated PLC-gateway communication;
- validated gateway-FORTE communication;
- integrated heartbeat and watchdog information;
- confirmed zero-output communication before positive actuation;
- implemented and tested fail-closed shutdown behavior.

### Completed - Real PI Baseline

- added the `PI_REAL_RAW_SAFE` application without replacing historical applications;
- added controlled PI commissioning scripts;
- tuned the PI to a conservative real-plant configuration;
- preserved the final experiment dataset;
- documented the acceptance result;
- integrated the checkpoint into `main`.

### Completed - Plant Characterization and Calibration Evidence

- completed the minimum local actuator characterization;
- selected one conservative input-map/model interpretation;
- preserved the physical zero and level-calibration evidence;
- documented the central bottom drain and dynamic calibration limitations;
- froze the evidence required for the final controller stage.

### Completed - Offline MPC Preparation

- identified the delayed Hammerstein candidate;
- preserved the canonical static nonlinearity;
- defined the controller input/output contract;
- implemented delay-aware prediction with applied-DAC history;
- validated controller contracts and safety constraints offline;
- preserved historical MPC variants without replacing them.

### Completed - Staged Real MPC Evidence

- implemented `MPC_REAL_RAW_SAFE_V3H`;
- mapped the application to `FORTE_PC.ResRealRawMPCV3H`;
- preserved staged real-plant runtime and first-actuation evidence;
- retained the validated PI path as the experimental baseline;
- integrated M1-M4 evidence into `main`.

### Completed - M5 Final 4diac MPC Integration and Thesis Evidence

- validated the additive `MPC_REAL_RAW_SAFE_V4` application and mapped resource;
- preserved the exact generated FORTE V4 module and runtime;
- completed protected zero-output deployment checks;
- completed the final 180 s real-plant MPC run;
- reached and stabilized at the physically measured 15 cm target;
- preserved synchronized CSV, runtime, physical and safe-stop evidence;
- generated reproducible final metrics and figures.

### Completed - Final PI-MPC Comparison

The final matched comparison has been completed and integrated into `main`:

- preserved the first matched PI attempt with `KI=0.02` as retuning evidence;
- completed the accepted matched PI run with `KP=4.0`, `KI=0.10`, the 17000-raw reference, and the same 180 s and 0..16000 DAC envelope used by MPC V4;
- measured 14.7 cm for PI and 15.0 cm for MPC V4;
- consolidated tracking error, IAE, ISE, overshoot, settling behavior, control effort, sampling behavior, watchdog state, and safe-zero evidence;
- generated reproducible metrics and PI-MPC comparison figures;
- documented the single-run and raw-to-centimetre offset limitations;
- preserved the final repository state with the annotated tag `thesis-real-plant-validation-20260901`.

The results support a descriptive engineering comparison rather than a statistical superiority claim. No additional PI tuning, model variant, or real-plant experiment is required.

## Git and Documentation Conventions

Repository documentation, source-code comments, branch names, and commit messages are written in English.

Recommended commit examples:

```text
docs: update validated project status
test: preserve plant identification dataset
feat: add offline prediction model
feat: add constrained MPC prototype
test: validate real MPC baseline
docs: compare PI and MPC experiments
```

Use annotated or lightweight tags only for meaningful validated checkpoints.

## Current Priority

The practical MPC implementation, the matched PI baseline, and the final real-plant PI-MPC comparison are complete. The current priority is limited to dissertation writing, academic review, and optional preparation of the repository for public release.

No additional controller variants, PI tuning campaigns, model-identification stages, or real-plant experiments are planned. The repository should remain focused on preserving the validated evidence and supporting the dissertation.

## M5F - High-range final MPC validation

The additive V4 controller completed the final independently supervised 180 s real-plant validation. With `SP_RAW=17000` and `DAC_MAX=16000`, the level reached and stabilized at the physically measured 15 cm target. The maximum median overshoot was 0.506%, the final 30 s mean error was 151.55 raw, the watchdog remained healthy and independent post-run monitoring verified zero output. Full evidence is documented in `docs/experiments/mpc-v4-target17000-20260829-analysis.md`.

## Final Conclusion

The project achieved its primary practical objective: implementing and
validating a Model Predictive Controller on the real level-control plant using
the B&R PLC, OPC UA, the Python gateway and Eclipse 4diac/FORTE.

The final additive `MPC_REAL_RAW_SAFE_V4` application completed the full 180 s
supervised active window and brought the process to the physically measured
15 cm operating point. With `SP_RAW=17000` and `DAC_MAX=16000`, the maximum
median-9 level was 17086 raw, corresponding to 0.506% overshoot. During the
last 30 s, the mean tracking error was 151.55 raw, or approximately 0.891% of
the target. The watchdog remained healthy throughout the active run and the
independent post-shutdown observation verified disabled actuation and zero DAC.

The complete engineering project, historical controller variants, final V4
function blocks, exact custom FORTE runtime, generated C++ sources, experimental
CSV files, physical observation, metrics, figures and automated acceptance
tests are preserved in the repository. The complete offline suite passes 494
tests, providing regression protection for the communication, controller,
safety, evidence and reproducibility contracts.

The practical MPC implementation, matched PI baseline and final real-plant
comparison are complete. The PI reached 14.7 cm and the MPC V4 reached 15.0 cm
under the common bounded 180 s protocol; both ended with healthy watchdog state
and independently verified zero output. Based on the accepted evidence, no
additional controller variant, model-identification campaign, PI tuning or
real-plant experiment is required. The remaining work is limited to using the
preserved metrics and figures in the dissertation and completing academic
writing and review.

## Final matched PI comparison

The final matched PI baseline is complete. The additive
`PI_REAL_RAW_HIGH_RANGE_COMPARE` application, mapped to
`FORTE_PC.ResRealRawPICompare`, preserves the historical PI application while
providing the same nominal 15 cm target, 17000-raw reference, 180 s active
window and 0..16000 DAC envelope used by the final MPC V4 experiment.

The first matched attempt with `KP=4.0` and `KI=0.02` reached approximately
6 cm and was preserved as retuning evidence. The single justified final attempt
kept `KP=4.0`, used `KI=0.10`, and reached 14.7 cm with no physical overshoot.
It completed the full active window with a healthy watchdog and independently
verified zero output after FORTE termination.

The final descriptive comparison shows that MPC V4 reached 15.0 cm and had a
last-30-s mean raw error of 151.55, while the PI reached 14.7 cm and had a
last-30-s mean raw error of 1132.23. The PI had no overshoot; MPC raw overshoot
was 0.506%. Both converged to a similar applied-DAC region near 14000 to balance
the continuous bottom drain. Because one final run per controller was used and
the raw-to-centimetre offset varied between sessions, the evidence supports an
engineering comparison rather than a statistical superiority claim.

Full metrics, figures, limitations and reproducibility paths are documented in
`docs/experiments/pi-vs-mpc-v4-final-20260901-analysis.md`. No additional
real-plant experiment or PI tuning campaign is required.

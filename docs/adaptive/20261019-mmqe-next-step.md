# Next step: validate the identifier separately

Checkpoint: 2026-10-19. This guide follows the native PID checks in
[the PID checkpoint](../pid/20261019-native-functional-checkpoint.md).
The PID and identifier are separate experiments for now. No plant actuation is required.

## What we are learning

The PID calculates the command from the error. The MMQE (recursive least squares
with forgetting) estimates process coefficients from input/output measurements.
A future tuning block must transform an accepted model into PID gains using a
specified tuning law. **The four estimated coefficients are not Kp, Ki and Kd.**

Source: `aula1_ident_linear (2).pdf`, PDF viewer p.29 (MMQE), p.30 (process),
p.37 (coefficient change). See [source register](references-and-traceability.md)
for exact filenames, article contributions and limits. No new tuning formula is
attributed to the lectures or articles at this checkpoint.

## One responsibility per block

| Block | Responsibility |
|---|---|
| `INPUT_SEQUENCE_REPLAY` | InputSequence the archived input and its delays; select the simulated coefficient change. |
| `OUTPUT_HISTORY` | Snapshot the two previous outputs; commit the new output after estimation. |
| `SECOND_ORDER_PROCESS` | Calculate the lecture's simulated output. |
| `RLS_PARAMETER_ESTIMATOR` | Estimate four coefficients using measured output and delayed inputs/outputs. |
| `PROCESS_IDENTIFICATION` | Composite wiring of the blocks above; no additional control algorithm. |
| `E_CYCLE` | Generate periodic execution events. |

Each sample follows InputSequence -> OutputHistory snapshot -> SimulatedProcess -> ParameterEstimator -> OutputHistory
commit -> completion. Updating history before estimation would shift the regression
vector and identify the wrong equation. The implementation uses event/data WITH
associations and explicit ECCs; this is not a certification of IEC 61499 compliance.

The simulated equation is:

`y(k) = 1.2*y(k-1) - 0.36*y(k-2) + b1*u(k-1) + 0.06*u(k-2)`.

The estimator receives `phi=[y(k-1), y(k-2), u(k-1), u(k-2)]` and `y(k)`.
It does not receive the true coefficients. Its outputs EST_OUTPUT_COEFFICIENT_1..EST_INPUT_COEFFICIENT_2 estimate
`[1.2, -0.36, b1, 0.06]`. This second-order lecture process differs from the
first-order `PID_DEMO_PROCESS`; do not connect the two experiments yet.

## First native experiment to prepare

1. Update the feature branch while preserving local changes. Import/open the
   separate project `4diac/application/Adaptive_Identification` in 4diac 2.0.1.
2. Refresh the project and inspect Problems. In `Identification_Offline`, set
   IdentificationTest `ENABLE_PROCESS_CHANGE=FALSE`, `FORGETTING_FACTOR=1.0`, `INITIAL_COVARIANCE=10000.0`; SamplingClock `DT=T#100ms`.
   The existing source defaults use a changed process and lambda=0.8, so explicitly
   change them for this first experiment. Save the project.
3. Export the four basic types `INPUT_SEQUENCE_REPLAY`, `OUTPUT_HISTORY`,
   `SECOND_ORDER_PROCESS`, `RLS_PARAMETER_ESTIMATOR` to a new external-module folder. Keep
   `PROCESS_IDENTIFICATION` in the IDE type library as the composite network.
4. Check the export messages and generated C++ before building. The existing PID
   runtime is not evidence that the ADP types are installed. A separate native
   build/module configuration and device/resource mapping are still required.
5. After deployment is prepared, initialize the experiment once. Observe SAMPLE_INDEX,
   EST_OUTPUT_COEFFICIENT_1..EST_INPUT_COEFFICIENT_2, PREDICTED_OUTPUT, PREDICTION_ERROR and ESTIMATION_VALID. Let 100 samples finish. Record the terminal
   values and the completion event. Do not repeatedly initialize mid-experiment.

The 100 ms timer paces the demonstration; it does not establish the sampling time
of a physical plant. `ESTIMATION_VALID` reports numerical acceptance, not model accuracy.

## Expected comparisons (offline reference, not native measurements)

| ENABLE_PROCESS_CHANGE | lambda | EST_OUTPUT_COEFFICIENT_1 | EST_OUTPUT_COEFFICIENT_2 | EST_INPUT_COEFFICIENT_1 | EST_INPUT_COEFFICIENT_2 |
|---|---:|---:|---:|---:|---:|
| FALSE | 1.0 | 1.198251 | -0.358444 | 0.100004 | 0.060200 |
| TRUE | 1.0 | 1.598929 | -0.646396 | 0.191907 | -0.074122 |
| TRUE | 0.8 | 1.200227 | -0.360178 | 0.399971 | 0.059895 |
| TRUE | 0.6 | 1.200000 | -0.360000 | 0.400000 | 0.060000 |

With ENABLE_PROCESS_CHANGE=TRUE, b1 changes from 0.1 to 0.4 at sample 51. Smaller lambda discounts
old data faster in this noiseless example. It is not evidence that lambda=0.6 is
best on the plant. Run each case from a fresh initialization; assess the trajectory
as well as the final coefficients.

## What changed and what is still pending

The RLS numerical guards now use `1.0E+100`, with an explicit exponent sign, in
both the generator and generated ST. This follows the PID export correction and
does not alter the equations. A regression test prevents unsigned exponents.

Reproduce the mathematical reference with:

```powershell
py scripts/reproduce_adaptive_identification.py
```

Python/ST-subset checks do not execute native FORTE scheduling or generated C++.
Pending: IDE export, native build, mapping, four native identification runs,
model-acceptance criteria and a justified model-to-PID tuning law.

For each native run, keep one screenshot at completion plus a small table with
revision, runtime, parameters and observed values. Record failures too. Avoid
archiving every timer tick.

Verification on 2026-10-19: 17 identification tests and 13 PID tests passed
(30 total, plus 5 subtests); the four archived numerical experiments reproduced.
Native identification execution remains pending.

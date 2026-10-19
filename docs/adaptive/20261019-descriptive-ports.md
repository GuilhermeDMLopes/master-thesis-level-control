# Descriptive identification interfaces

2026-10-19: user requested readable input/output names. The mathematical algorithm and event order are unchanged. Existing PID runtime and historical OPAS application are preserved. Use the separate Adaptive_Identification project; old copies in OPAS are not migrated automatically. Re-export the four basic types and rebuild before native execution.

| Previous | Current |
|---|---|
| `CHANGE` | `ENABLE_PROCESS_CHANGE` |
| `LAMBDA` | `FORGETTING_FACTOR` |
| `P0` | `INITIAL_COVARIANCE` |
| `K` | `SAMPLE_INDEX` |
| `Y` | `PROCESS_OUTPUT` |
| `Y_CURRENT` | `CURRENT_OUTPUT` |
| `Y1` | `OUTPUT_PREVIOUS_1` |
| `Y2` | `OUTPUT_PREVIOUS_2` |
| `U1` | `INPUT_PREVIOUS_1` |
| `U2` | `INPUT_PREVIOUS_2` |
| `B1` | `TRUE_INPUT_COEFFICIENT` |
| `F1` | `OUTPUT_PREVIOUS_1` |
| `F2` | `OUTPUT_PREVIOUS_2` |
| `F3` | `INPUT_PREVIOUS_1` |
| `F4` | `INPUT_PREVIOUS_2` |
| `T1` | `EST_OUTPUT_COEFFICIENT_1` |
| `T2` | `EST_OUTPUT_COEFFICIENT_2` |
| `T3` | `EST_INPUT_COEFFICIENT_1` |
| `T4` | `EST_INPUT_COEFFICIENT_2` |
| `Y_HAT` | `PREDICTED_OUTPUT` |
| `ERROR` | `PREDICTION_ERROR` |
| `VALID` | `ESTIMATION_VALID` |

INIT initializes; INITO confirms initialization; REQ requests a calculation; CNF confirms it; ERR reports numerical failure; DONE ends replay. History COMMIT stores the sample and ACK confirms storage. These event names remain unchanged.

ESTIMATION_VALID means numerical acceptance, not sufficient identification quality for tuning. TRUE_INPUT_COEFFICIENT belongs to the simulated process and is never passed to the estimator. Coefficients use the signed-output convention documented in the source register.

## Block names

| Previous type | Descriptive type |
|---|---|
| `ADP_REPLAY100` | `INPUT_SEQUENCE_REPLAY` |
| `ADP_HISTORY2` | `OUTPUT_HISTORY` |
| `ADP_ARX22_PROCESS` | `SECOND_ORDER_PROCESS` |
| `ADP_RLS4` | `RLS_PARAMETER_ESTIMATOR` |
| `ADP_IDENTIFICATION` | `PROCESS_IDENTIFICATION` |

Instances: SamplingClock, IdentificationTest, InputSequence, OutputHistory, SimulatedProcess and ParameterEstimator. RLS means recursive least squares. Standard E_CYCLE remains unchanged.

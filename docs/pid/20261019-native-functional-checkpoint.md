# Native PID functional checkpoint — 2026-10-19

## Scope and evidence
User-operated Windows FORTE, 4diac IDE 2.0.1, PID_Whiteboard/PID_Simulation mapped to LocalPID/EMB_RES at localhost:61499. Evidence: screenshots supplied in the development conversation; rounded values transcribed below. Screenshots are not yet archived in this repository. No physical PLC, OPC UA, adaptive identifier, or automatic tuning was tested.
Runtime build and executable hash: see 20261019-native-build-result.md.

The user copied devices/FORTE_PC.dev, resources/EMB_RES.res and events/E_RESTART.fbt from OPAS_Tank_System/Type Library into PID_Whiteboard/Type Library. These dependencies and the user-created device/resource mapping still need to be captured from the user's saved project. Do not overwrite that project with the unmapped repository version.

## Configuration
KP=1, KI=0.5, KD=0.1; TS_S=0.1 s; E_CYCLE DT=T#100ms; limits [0,10].
Synthetic dimensionless process: y[k]=0.9*y[k-1]+0.1*u[k-1].
Process.INIT initializes the controller, whose INITO starts the timer.
Timer -> Process.REQ -> Process.CNF -> Controller.REQ -> Controller.CNF -> Process.APPLY.
E_RESTART START remains unconnected.

## Reference tracking
| Screenshot | SP | PV | MV | Processing counter |
|---|---:|---:|---:|---:|
| image(20261019-125121).png | 1 | 0.999988574 | 0.999991933 | 360 |
| image(20261019-125733).png | 1 | approximately 1 | approximately 1 | 3998 |
| image(20261019-130111).png | 2 | 1.999963413 | 1.999974169 | 4319 |
| image(20261019-130758).png | 1 | 1.000041343 | 1.000029188 | 4638 |

INIT remained 1. Both VALID outputs were TRUE and ERR counters zero. Final SATURATED was FALSE. Counter differences imply 321 and 319 nominal 100 ms steps, not measured wall-clock timing or settling times. Screenshots do not establish overshoot or the entire transient.

## Manual saturation and recovery
Timer stopped at EO=4638. Each Process.REQ manually advances one complete chain; wall-clock click intervals are not sample periods. Internal TS_S remains 0.1.
| Screenshot suffix | Counter | SP | PV | RAW | MV | I_TERM | FLAG | SATURATED |
|---|---:|---:|---:|---:|---:|---:|---|---|
| 131933 | 4639 | 20 | 1.000040 | 39.475028 | 10 | 1.475067242 | FALSE | TRUE |
| 132018 | 4640 | 20 | 1.900036 | 18.675035 | 10 | 1.475067242 | FALSE | TRUE |
| 132356 | 4641 | 3 | 2.710033 | -16.044962 | 0 | 1.475067242 | FALSE | TRUE |
| 132413 | 4642 | 3 | 2.439029 | 2.307041 | 2.307041 | 1.475067242 | TRUE | FALSE |
| 132429 | 4643 | 3 | 2.425830 | 2.090814 | 2.090814 | 1.503445749 | TRUE | FALSE |

Full names follow image(20261019-HHMMSS).png. Both VALID outputs stayed TRUE; ERR stayed zero.
This supports upper/lower limiting, use of the previous flag to gate integration, and resumption one calculation after FLAG becomes TRUE. It does not remove the known freeze limitation documented in the flag contract/tests. Derivative is on error, so reference steps produce derivative kick.

## Gain update interface
image(20261019-141612).png: KP changed to 2, KI=0.5 and KD=0.1 unchanged. SET_GAINS=1 and GAINS_CNF=1, CNF remained 4643, MV=2.090814 and I_TERM=1.503445 unchanged.
image(20261019-141632).png: next Process.REQ advanced processing to 4644:
PV=2.392328816, ERROR=0.607671184, P_TERM=1.215342368,
I_TERM=1.532991768, D_TERM=0.033501635, MV=2.781835770.
P_TERM=2*ERROR confirms application of the new KP. No reset or control calculation occurred on SET_GAINS itself. VALID remained TRUE; ERR remained zero.
Only KP was varied in this native experiment; independent KI/KD changes and invalid gain updates were not tested natively. No bumpless-transfer guarantee is claimed.

## Checkpoint and next work
Current runtime is paused with SP=3, KP=2, KI=0.5, KD=0.1. Online writes must not be assumed to persist in the .sys file.
Save and obtain the user's complete PID_Whiteboard project before updating its mapping or dependencies in Git. Preserve all OPAS_Tank_System changes.
Basic functional cases are complete; avoid repeating them without a concrete discrepancy.
Next development: review the existing RLS identifier and source-material model, validate identification separately, then define and justify the parameter-to-PID tuning law before connecting automatic gain updates. RLS parameter estimation alone is not a PID tuning rule.
No claim of full IEC 61499 certification, physical-plant validation, or adaptive-control validation is made.

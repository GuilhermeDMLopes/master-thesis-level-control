# M1 local actuator-map evidence analysis

- Classification: `M1_LOCAL_MAP_EVIDENCE_SUFFICIENT__MODEL_11750_DEADZONE_NOT_SUPPORTED__STOP_UPWARD_EXCITATION_AFTER_11800_RATE_ABORT`
- Source run: `local-deadzone-resume-20260825-182908`
- Real actuation in this analysis stage: **NO**
- Recorded executor stop: `POSITIVE_MEDIAN_RATE_ABORT` during the 11800-DAC hold.

## Point summary

| DAC | Status | Hold s | Baseline raw | Post-delay mean Delta | Final-10s mean Delta | Max Median9 | Max raw | Physical max |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 11650 | COMPLETED | 44.95 | 267.0 | 75.0 | 245.8 | 726.0 | 787.0 | 0.8 cm |
| 11700 | COMPLETED | 44.89 | 451.0 | 168.6 | 251.1 | 828.0 | 900.0 | 1.0 cm |
| 11750 | COMPLETED | 44.89 | 370.0 | 277.9 | 441.6 | 950.0 | 1022.0 | 1.2 cm |
| 11800 | PARTIAL_SAFETY_ABORT | 23.30 | 370.0 | 199.9 | 271.2 | 797.0 | 858.0 | not recorded before abort |
| 11850 | NOT ATTEMPTED | - | - | - | - | - | - | - |
| 11900 | NOT ATTEMPTED | - | - | - | - | - | - | - |

## Interpretation

- The earlier 11600-DAC experiment already produced a material post-delay level response (+204 raw; 0.5 cm physical maximum).
- The current run completed full constant-target holds at 11650, 11700 and 11750 DAC.
- The 11800-DAC point produced useful partial evidence but was terminated by the existing positive Median9-rate safety guard.
- Therefore the model assumption that effective input begins only at 11750 DAC is not supported by the real-plant evidence.
- This does **not** identify the exact real dead-zone threshold; it only shows that 11750 is too high as the model's zero-effect boundary.
- Escalating to 11850/11900 is not necessary for that decision and would add risk without closing a thesis-critical uncertainty.

## Decision

- Retry 11800 now: **NO**
- Run 11850 now: **NO**
- Run 11900 now: **NO**
- Increase raw ceiling: **NO**
- Change V3H immediately: **NO**
- M1 sufficient to enter M2 offline: **YES**
- Next: evaluate one final local input-map/model correction offline using 11600, 11650, 11700, 11750 and the partial 11800 evidence.

The physical maxima for 11650/11700/11750 above are operator-reported console observations from the run; the aborted 11800 point did not reach the physical-height prompt.

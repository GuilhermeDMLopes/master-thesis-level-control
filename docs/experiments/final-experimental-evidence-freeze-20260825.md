# Final experimental evidence freeze - 2026-08-25

## Final scope

The practical master-thesis campaign is frozen after completion of the minimum M1-M4 plan. No additional controller variant, plant campaign or automatic model candidate is authorized by this freeze.

## Milestones

| Milestone | Final status | Primary conclusion |
| --- | --- | --- |
| M1 - local plant identification | COMPLETED | The required local DAC evidence was collected and preserved. |
| M2 - MPC input map/model decision | CLOSED_WITH_DOCUMENTED_LIMITATION | The 11550 replay was rejected; canonical 11750 DAC dead-zone retained provisionally. |
| M3 - physical level calibration | CLOSED_WITH_DYNAMIC_CAPTURE_LIMITATION | Operational points 0, 3, 5, 8.5 and 13 cm preserved; raw/1000 retained. |
| M4 - PI versus MPC comparison | COMPLETED_AS_DESCRIPTIVE_COMPARISON | Real PI baseline and real MPC execution compared; no global MPC superiority claimed. |

## Validation

- Full automated suite on feature branch: PASSED (472 tests observed before this freeze and rerun by ETAPA 7.7).
- Corrupted Markdown documents repaired and verified: 10.
- Remaining Markdown sequences with two or more question marks: 0.
- M2 closure commit: 6b7f616.
- M3 closure commit: b48245.
- M4 comparison source commit: $comparisonCommit.
- PLC/gateway/FORTE access during this freeze: NO.
- Real actuation during this freeze: NO.

## Evidence hashes

- M2 decision JSON SHA256: $m2Hash
- M3 summary JSON SHA256: $m3Hash
- M4 comparison JSON SHA256: $m4Hash

## Dissertation-safe conclusion

The PLC B&R - Python OPC UA gateway - FORTE architecture was exercised with both PI and MPC on the real plant. The PI is retained as a validated functional baseline. The MPC demonstrated real integration, explicit delay treatment and bounded supervisory shutdown, but the available experiment does not establish global closed-loop superiority or steady-state regulation. The permanent bottom drain, sensor offset, dynamic calibration captures and imperfect local model remain explicit experimental limitations.

The evidence is sufficient for the dissertation comparison when reported with these classifications and limitations. Further plant work is outside the minimum completion scope.

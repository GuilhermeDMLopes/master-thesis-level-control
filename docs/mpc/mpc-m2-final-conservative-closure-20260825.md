# M2 final conservative closure - 2026-08-25

## Decision

- M2 status: CLOSED_WITH_DOCUMENTED_LIMITATION
- Dead-zone 11550 replay accepted: NO
- Dead-zone 11550 correction implemented: NO
- Exact physical dead-zone identified: NO
- Canonical V3H dead-zone retained: 11750 DAC
- Retention basis: PROVISIONAL_CONSERVATIVE_MODEL_ASSUMPTION
- Another replay candidate authorized: NO
- Controller source modified: NO
- 4diac modified: NO
- Real actuation performed: NO
- Next milestone: M3

## Interpretation

The single authorized 11550 DAC input-map replay changed the controller decision materially but was not accepted. It reduced the command in 85.4% of the 48 late records and produced premature command at or below 11550 DAC in 31.6% of the eligible low-PV records. No hard-limit violation occurred.

The preserved trajectory was generated with the real applied command recorded in the experiment, not with the counterfactual commands proposed by the 11550 model. Therefore this offline replay cannot establish the real plant response at the alternative commands and cannot identify the exact physical dead-zone.

The canonical 11750 DAC dead-zone is retained unchanged solely as a conservative provisional modeling assumption. This retention is not a claim that 11750 DAC is the exact physical dead-zone.

No further dead-zone candidate is authorized automatically. M2 is closed with this limitation documented so the project can proceed without expanding the experimental scope.

## Preserved evidence

- Rejected replay report: `docs/mpc/mpc-v3h-deadzone-11550-replay-20260825.md`
- Rejected replay JSON: `results/mpc-v3h-deadzone-11550-replay-20260825/replay.json`
- Report SHA256: `6FC6937882FCCB51D8E900D014689B74AAB568EAFFE3E6A27DEC15F6BD648642`
- Replay JSON SHA256: `FCE44CA0DB952DC4529518891803A4F212511C1046D4B9BE9A5896C8D481CE2B`
- Pre-closure decision commit: `2b6e543`

## Scope guard

This closure does not modify the authoritative Python V3H, controller weights, timing, delay, limits, target set, 4diac artifacts, or real-plant state.

# M2 final input-map candidate decision

## Classification

`M2_MODEL_11750_DEADZONE_REJECTED__EXACT_REAL_DEADZONE_NOT_IDENTIFIED__SINGLE_11550_CANDIDATE_SELECTED_FOR_OFFLINE_REPLAY`

## Evidence

The completed same-session points were:

| DAC | Post-delay mean Delta Median9 (raw) |
|---:|---:|
| 11650 | 75.0 |
| 11700 | 168.6 |
| 11750 | 277.9 |

A simple local linear trend over these three completed same-session points gives:

- slope: `2.0290 raw/DAC` in this empirical response metric;
- zero crossing: `11614.3 DAC`;
- R²: `0.9980`.

This zero crossing is **not** accepted as the physical dead-zone estimate because the earlier independent 11600-DAC long-hold experiment already produced a material response (`+204.0 raw` by its own recorded metric). The two sessions also use different response summaries and must not be pooled as if they were identical observations.

## Final M2 candidate rule

The model's current hard zero-effect boundary at **11750 DAC is rejected**.

The exact real dead-zone remains **not identified**.

If a hard dead-zone representation is retained, the boundary must be below the lowest already responsive tested input, 11600 DAC. With the existing 50-DAC local grid, the single conservative candidate selected for replay is:

**11550 DAC**

This is a model candidate for offline replay, not a claim that the physical dead-zone equals 11550 DAC.

## Scope

- New controller variant: **NO**
- 4diac modification: **NO**
- Real plant run: **NO**
- Implementation of 11550 candidate authorized now: **NO**
- Next: one authoritative offline V3H replay with dead-zone only changed from 11750 to 11550 and every other parameter unchanged.

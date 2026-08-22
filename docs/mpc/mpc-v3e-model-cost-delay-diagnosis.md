# MPC V3E model / cost / delay diagnosis

Date: 2026-08-22

## Classification

**MODEL_STATIC_DYNAMIC_MISMATCH_DOMINANT**

## Why the optimizer stays near 11845.6 DAC

The authoritative V3 objective was replayed on 7 representative real V3E
snapshots with `Median9 > SP` and `AppliedDAC >= 11800`.

- canonical model selected a high-DAC target in 7/7 snapshots;
- changing only the model baseline from 288 to 227 selected a high-DAC target
  in 7/7 snapshots;
- setting move weight to zero selected a high-DAC target in 7/7
  snapshots;
- replacing the committed high-DAC delay history with zero history selected a
  high-DAC target in 7/7 snapshots.

Thus:

- baseline-only correction sufficient: **NO**;
- move-penalty-only correction sufficient: **NO**;
- committed delay/history changes target preference: **NO**.

## Model prediction versus real future

For snapshots with sufficient future evidence, the median difference

`actual future Median9 - equilibrium-target predicted final`

was `367.5 raw`.

Large future underprediction (>=100 raw): **YES**.

The real Median9 slope over the final 20 s was approximately
`5.193 raw/s` while the actuator remained in the high-DAC region.

This directly tests the model belief that the ~11845.6-DAC target is an
equilibrium near SP against the observed real trajectory.

## Snapshot summary

- t=22.67s, Med9=461.0, Applied=11846.0, canonical best=11845.627, baseline227 best=11874.806519722419, moveWeight0 best=11845.626677302696, zero-history best=11850.0, eq predicted final=450.1, actual future final=665.0
- t=29.52s, Med9=553.0, Applied=11846.0, canonical best=11845.627, baseline227 best=11874.806519722419, moveWeight0 best=11845.626677302696, zero-history best=11850.0, eq predicted final=450.2, actual future final=818.0
- t=36.67s, Med9=716.0, Applied=11846.0, canonical best=11845.627, baseline227 best=11874.806519722419, moveWeight0 best=11845.626677302696, zero-history best=11850.0, eq predicted final=450.5, actual future final=818.0
- t=42.66s, Med9=757.0, Applied=11846.0, canonical best=11845.627, baseline227 best=11874.806519722419, moveWeight0 best=11845.626677302696, zero-history best=11850.0, eq predicted final=450.6, actual future final=818.0
- t=48.38s, Med9=696.0, Applied=11846.0, canonical best=11845.627, baseline227 best=11874.806519722419, moveWeight0 best=11845.626677302696, zero-history best=11850.0, eq predicted final=450.5, actual future final=818.0
- t=54.06s, Med9=777.0, Applied=11846.0, canonical best=11845.627, baseline227 best=11874.806519722419, moveWeight0 best=11845.626677302696, zero-history best=11850.0, eq predicted final=450.6, actual future final=818.0
- t=60.05s, Med9=818.0, Applied=11846.0, canonical best=11845.627, baseline227 best=11874.806519722419, moveWeight0 best=11845.626677302696, zero-history best=11850.0, eq predicted final=450.7, actual future final=818.0

## Decision

Do not increase the raw ceiling and do not run the plant again yet.

Do not change the candidate topology first.

The next offline stage should evaluate an additive model/bias correction using
the preserved 60 s V3E evidence. The first candidates should be:

1. local model re-fit around the real high-DAC transient;
2. output-bias/disturbance correction while preserving the identified delay;
3. only after offline comparison, choose the smallest additive change for the
   next controller variant.

The V3/V3E artifacts remain unchanged.

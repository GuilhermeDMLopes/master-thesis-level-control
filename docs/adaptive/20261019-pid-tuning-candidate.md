# Offline PID tuning candidate and first switching experiment

Date: 2026-10-19. Scope: Python numerical experiment only. No new 4diac block, runtime deployment, online RLS loop or physical test.

## Design choice and derivation

Following the [feasibility derivation](20261019-pid-tuning-feasibility.md), assign three poles p=0.7 and solve the remaining pole r together with q0,q1,q2. This is an original project choice inspired by the lecture pole-placement principle, not a formula transcribed from the supplied articles. T=0.1 s is now explicitly assigned to this synthetic experiment. It is not a physical sampling interval inferred from the lecture.

Let [1,c1,c2,c3] be coefficients of (z-p)^3. Solve:
b1*q0+r = c1+1+a1
b2*q0+b1*q1+c1*r = c2-a1+a2
b2*q1+b1*q2+c2*r = c3-a2
b2*q2+c3*r = 0

This imposes D(z)=(z-p)^3(z-r), rather than independently specifying four poles. Reject singular/ill-conditioned equations, nonfinite or negative gains, and any resulting pole outside the unit circle. The condition-number threshold 1e10 is a numerical screening choice, not a robustness certificate. Repeated-root numerical extraction gives moduli near 0.700003, consistent with repeated-root sensitivity; coefficient residuals are below 1e-16.

Convert q to the existing parallel PID using the previously derived formulas. Gains:
- Before change: KP=0.4588233955; KI=1.6381884388; KD=0.01670505234; remaining pole 0.02922166591.
- After change, true model: KP=0.1551602890; KI=0.5822613474; KD=0.00457286790; remaining pole 0.00799918583.
- After change, archived lambda=0.8 estimated model: KP=0.1552793769; KI=0.5824050143; KD=0.00460717084.

These are synthetic candidate gains only.

## Experiments and findings

300 samples, SP=1, limits [0,10], zero histories, original trapezoidal integral/backward derivative and delayed flag. Applied command influences the next process sample. Change b1 from 0.1 to 0.4 at sample 151; prescribe gain update at 171 without resetting/rescaling integral, error or flag. These schedules extend the earlier identification exercise and are project choices. The estimator is NOT running online: an archived final estimate is used for the estimated-model case.

| Experiment | Final output | Sum of absolute error (sample units) | Saturated samples |
|---|---:|---:|---:|
| Fixed process, tuned fixed gains | 1.0 | 6.10430 | 0 |
| Changed process, retain original gains | 1.0 | 10.14204 | 0 |
| Changed process, prescribed true-model gain update | 1.0 | 13.98928 | 0 |
| Changed process, prescribed estimated-model gain update | 1.0 | 13.98780 | 0 |

Integral absolute error in seconds is the tabulated sum multiplied by T=0.1. All changed cases peak at approximately 1.706918 before the prescribed retuning. The update did NOT improve this comparison: fixed gains recover on their own; changing KI reweights the stored integral and introduces another transient. Do not claim adaptive superiority or guaranteed bumpless transfer.

SP=20 stress case is infeasible for the original process with maximum command 10 (DC gain=1). Output approaches 10 with error 10; 298 saturated samples. This checks bounded actuation under an unreachable reference, not saturation recovery or stable adaptation.

## Reproduce

Requires NumPy (already used by the identification simulation):
```powershell
py scripts/verify_pid_model_tuning.py --output "$env:TEMP\pid-model-tuning.json"
```

[Recorded output](pid-model-tuning.json). The script checks final tracking for two cases, rejects a zero-input plant, and checks each computed characteristic polynomial/pole set. It reimplements the documented PID equations in Python; it does not execute exported ST.

## Decision

Keep this as a candidate, not a deployed tuner. No whiteboard PID behavior is changed.
Next gate is a gain-update policy compatible with preserving that PID, plus tests of transients and model quality. A bumpless state adjustment would change the existing contract and must not be introduced silently. The current numerical VALID signal alone must not authorize gain adaptation.

# Multirate tuning and bounded gain transitions

Date: 2026-10-20. Python-only candidate, not deployed in FORTE. Reuses the repository RLS4 implementation and the preceding tuning candidate.

## Responsibilities and schedule

Tuning IS the calculation of KP, KI, KD. It is not a second calculation required after those gains. The additional transition stage determines how the new gains are applied without an abrupt reweighting of the stored integral.

Preserve the advisor topology: PID -> process; measured output and previously applied input -> identifier -> CALCULA -> PID. Subdivide CALCULA into target-gain computation and transition management. This subdivision is a project implementation proposal, not a new block required by IEC 61499.

Proposed synthetic schedule:
- PID and aligned identification update every 100 ms.
- Request new target gains every 10 completed samples (1 second), after 50 initial samples.
- Advance the gain transition on control-sample boundaries.
- Derive all requests from one sample-event chain, with a counter; no unrelated second timer.
- Acquire a coherent measurement and applied-input history; update identifier; on due samples calculate/accept a target; advance gains; complete PID SET_GAINS/GAINS_CNF; issue PID REQ; apply command; commit history.
- Rejecting a target retains active gains and cancels pending transition. A missed/overrunning calculation must not lead to silently using an incorrect fixed sample interval.

This is a serial offline schedule. There is no evidence of native WCET, asynchronous execution, deadline compliance or event/data concurrency yet. A slower calculation rate does not imply another thread.

## Gain transition without changing the whiteboard PID

Preserve integral memory, previous error and delayed saturation flag. No reset, integral rescaling, derivative filtering or substitute anti-windup.

For current sample, form f=[error, next_integral, derivative], using exactly the PID's original equations and previous flag. With active gains g and target g*, let delta=g*-g.
Gain-only raw-command change for an interpolation fraction alpha is alpha*(delta dot f). Select a common fraction for all three gains:

alpha=min(1, 0.02/abs(delta dot f), 0.02/max_i(abs(delta_i)/scale_i))
scale=max(abs(active_gains), [0.01,0.01,0.001]).

Zero denominators are treated with a small positive floor. These bounds/floors are explicit synthetic design choices in compatible normalized units, not physical-plant limits. The per-gain bound avoids large moves hidden by cancellation in the dot product.

Apply g_next=g+alpha*delta only when the old flag is true, old and candidate raw commands are within [0,10], and the candidate frozen-gain characteristic polynomial is stable on the most recently accepted model. Otherwise hold gains.
The 0.02 bound concerns ONLY the raw-command difference caused by gains at identical current state; it is not a bound on total command change across samples. It reduces bumps but does not guarantee zero bump or time-varying/adaptive stability.

The Python prototype reads state directly. A native external transition block will need coherent read-only PID state (integral memory, previous error, flag, active gains), or an explicitly designed state interface. Do not wire old P/I/D term values as if they were current unweighted features. No such interface modification was made in this checkpoint.

## Closed-loop identification setup

400 samples; initial PID gains from the true nominal synthetic model; initial RLS theta=0, P=10000 I. This is not automatic startup from an unknown plant. Process b1 changes 0.1 -> 0.4 at sample 151. RLS receives y(k) and [y(k-1),y(k-2),u(k-1),u(k-2)] with actual bounded command history; no true coefficients are supplied to the online tuner.

Default forgetting=0.8 (same value as an earlier lecture reproduction). A preliminary 0.98 trial did not recover the post-change coefficients in these tests and is not silently presented as successful; --forgetting allows reproduction.

Compare constant SP=1 against alternating SP=1/0.8 every 50 samples. This extra reference variation is a deliberate synthetic excitation choice, not provided by the professor. No measurement noise is simulated.

Before each tuning request, a 50-sample column-normalized regressor matrix must have condition number <=1e6, the prior PID flag must be true, and the tune() numerical/gain/pole checks must pass. These checks do not establish model accuracy. RLS continues every sample even when tuning is rejected; prolonged weak excitation and covariance growth remain limitations.

## Results

| Variable-reference case, lambda=0.8 | IAE (output-unit seconds) | Maximum gain-only raw jump |
|---|---:|---:|
| Fixed original gains | 1.511407 | 0 |
| Online RLS, abrupt gains | 2.083240 | 0.175768 |
| Online RLS, limited gains | 1.937321 | 0.005736 |

The limited case accepted 32 target calculations and rejected 4, had zero saturated samples, and ended with coefficients approximately [1.2,-0.36,0.4,0.06]. It reduced the maximum gain-induced jump by about 96.7% relative to abrupt updates and reduced IAE relative to abrupt adaptation. It did NOT outperform the fixed PID. Model fit and control superiority are distinct conclusions.

With constant reference the limited case ended near [1.712800,-0.757567,0.527501,-0.398794], not the true post-change model. Good tracking alone did not recover all four coefficients. This observation motivates excitation/model-quality handling; it is not proof of a single exclusive cause.

All ten recorded cases and configuration are in [gain-transition-summary.json](gain-transition-summary.json). The prescribed-update cases isolate transition behavior; only rls_* cases use current online estimates for tuning. Timing metrics here are simulated, not wall-clock measurements.

## Reproduce and implementation boundary

Requires NumPy and the repository simulation/adaptive/identification.py plus scripts/verify_pid_model_tuning.py:
```powershell
py scripts/verify_pid_gain_transition.py --output-dir "$env:TEMP\pid-gain-transition"
```

Generates summary.json and ten per-sample CSVs. Assertions check finite trajectories and the gain-induced bound for limited cases; an unchanged target leaves gains unchanged. No native ST/ECC test is claimed.

Next native design gate: define coherent state access and event ordering for transition handling, together with adaptation authorization under weak excitation. Preserve the validated PID arithmetic and historical projects. Current work supports a candidate transition policy and a successful deterministic identification case, not a completed real-plant adaptive controller.

# MPC V3H first-active internal replay

## Classification

`MODEL_DEADZONE_PLUS_MOVE_PENALTY_CREATES_11750_STRUCTURAL_HOLD__LATE_HOLD_NOT_EXPLAINED_BY_COMMITTED_HIGH_DAC_DELAY__AUTHORITATIVE_V3H_REPLAY_SUPPORTS_11750_CHOICE__REAL_STATIC_DEADZONE_REMAINS_UNIDENTIFIED`

## Scope and caveat

This is an offline causal reconstruction using the authoritative Python V3H
reference controller and the real first-active V3H evidence.

The FORTE internal `d_hat` and controller Median9 were not logged directly.
The replay therefore reconstructs the controller-cadence Median9 from raw data
at 500 ms and seeds it with the final zero-output warmup evidence.

The replay is suitable for diagnosing optimizer structure; it is not a claim of
bit-exact runtime-state reconstruction.

## Main result

- late plateau analyzed: 36.5..60.0 s;
- delay history fully at/below 11750 in 100.0% of late points;
- authoritative replay chose target ~11750 in 100.0% of late points;
- 11500-vs-11750 model-equivalence + move-cost tie-break held in 100.0% of late points;
- 0-vs-11750 model-equivalence + move-cost tie-break held in 100.0% of late points;
- mean reconstructed d_hat: +31.682 raw/controller-step;
- mean reconstructed equivalent steady shift: +317.1 raw;
- median replay-vs-recorded command error: 0.0 DAC.

## Interpretation

Once the applied command is at 11750 DAC, the current Hammerstein input map
assigns zero modeled effective input to 11750 and to every lower command.
Consequently, targets such as 11500 or 0 do not improve the modeled future
plant trajectory relative to 11750 after the delayed history has flushed.

They do, however, require additional control movement. Because the MPC objective
contains a positive move penalty, 11750 becomes the lowest-cost representative
of an entire model-equivalent below-dead-zone action region.

Therefore a persistent 11750-DAC command is structurally expected from the current
model/objective and is not, by itself, evidence that the optimizer is stuck.

The late plateau also persists after the 9 s committed high-DAC history has largely
flushed, so the final hold cannot be explained only by old high-DAC commands still
inside the delay queue.

## What remains unknown

The real static dead-zone threshold is still not identified by this experiment.
If the real plant has non-negligible effective input near 11750 DAC, the model
would treat that input as zero and would have no incentive to command farther
below the boundary because lower commands are model-equivalent but move-costly.

That is now a more specific model-fidelity question than the original V3E
high-DAC lock-in problem.

## Selected snapshots

- t=27.5 s: Med9(reconstructed)=502.0, AppliedDAC=11750.0, d_hat=+12.24, steady shift=+122.5, delay-high fraction=94.4%, best target=11750.0, cost(11500)=360206.2, cost(11750)=360203.7, cost(11800)=412207.2;
- t=36.5 s: Med9(reconstructed)=665.0, AppliedDAC=11750.0, d_hat=+31.40, steady shift=+314.2, delay-high fraction=0.0%, best target=11750.0, cost(11500)=8128704.4, cost(11750)=8128701.9, cost(11800)=12976377.8;
- t=45.0 s: Med9(reconstructed)=686.0, AppliedDAC=11750.0, d_hat=+38.72, steady shift=+387.5, delay-high fraction=0.0%, best target=11750.0, cost(11500)=15981510.7, cost(11750)=15981508.2, cost(11800)=22714284.6;
- t=52.5 s: Med9(reconstructed)=471.0, AppliedDAC=11750.0, d_hat=+18.06, steady shift=+180.8, delay-high fraction=0.0%, best target=11750.0, cost(11500)=112940.3, cost(11750)=112937.8, cost(11800)=1445474.9;
- t=60.0 s: Med9(reconstructed)=757.0, AppliedDAC=11750.0, d_hat=+46.83, steady shift=+468.7, delay-high fraction=0.0%, best target=11750.0, cost(11500)=29169265.0, cost(11750)=29169262.5, cost(11800)=38015375.8;

## Decision

- change V3H now: **NO**;
- increase raw ceiling: **NO**;
- repeat the same 60 s run: **NO**;
- claim exact real dead-zone = 11750 DAC: **NO**;
- next: review existing identification evidence around 11500–12000 DAC and
  determine whether it is sufficient to estimate the real local dead-zone/gain;
- if existing evidence is insufficient, prepare a separate small bounded
  identification experiment rather than another closed-loop performance run.

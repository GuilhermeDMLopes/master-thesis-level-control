# MPC V3H protected zero-output deployment â€” 2026-08-22

## Classification

PROTECTED_V3H_ZERO_OUTPUT_DEPLOYMENT_PASSED

The real communication stack and isolated V3H FORTE were exercised only in a
protected zero-output commissioning state. This was not an active MPC
experiment.

## Runtime

FORTE V3H SHA256:

$ForteHash

open62541 SHA256:

$OpenHash

Deployed resource:

FORTE_PC -> ResRealRawMPCV3H

MpcController.ENABLE_REQUEST remained FALSE.

The operator reported one MpcInitMerge.EI1 trigger on the fresh deployment,
as required by the commissioning runbook.

## Guard result

The protected guard completed its full observation window and reported:

- samples: 580;
- raw level range: 196 .. 247;
- raw level median: 217;
- WatchdogHealthy remained true;
- final Enable = FALSE;
- final DAC = 0;
- final AppliedEnable = FALSE;
- final AppliedDAC = 0;
- OPC UA writes by the guard: none;
- ZERO-OUTPUT DEPLOYMENT VALIDATION: PASSED.

No ZERO-OUTPUT VIOLATION, Python traceback or runtime error is present in the
guard evidence.

The FORTE evidence contains neither UNSUPPORTED_TYPE nor NO_SUCH_OBJECT.

## Why ETAPA 7.5AL printed a failure after the guard passed

The failure was in the PowerShell wrapper, not in the guard.

After Wait-Process, the wrapper read:

$guard.ExitCode

but the value was blank/null in that process object. The script then evaluated:

if ( -ne 0)

In PowerShell, a null value is not equal to numeric zero, so the wrapper entered
the failure branch even though the child process had already completed and its
stdout explicitly contained:

ZERO-OUTPUT DEPLOYMENT VALIDATION: PASSED

Therefore the original final status is superseded by this offline evidence
review.

No redeployment or second EI1 trigger is required to resolve this bookkeeping
error.

## Evidence hashes

Guard stdout:

$GuardOutHash

Guard stderr:

$GuardErrHash

Guard stdin token:

$GuardInputHash

Guard CSV:

$CsvHash

## Safety conclusion

This evidence supports the following limited claim:

> The V3H resource was deployed and initialized on the real communication stack
> while the actuator remained at zero and the watchdog remained healthy during
> the protected observation window.

It does **not** validate active V3H regulation, disturbance-estimator behavior
under actuation, or steady-state performance.

A later bounded active V3H experiment requires a separate explicit stage and
fresh physical safety confirmation.

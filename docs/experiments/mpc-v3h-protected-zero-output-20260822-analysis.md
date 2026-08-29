# MPC V3H protected zero-output deployment - 2026-08-22

## Classification

PROTECTED_V3H_ZERO_OUTPUT_DEPLOYMENT_PASSED

The real communication stack and isolated V3H FORTE were exercised only in a
protected zero-output commissioning state. This was not an active MPC
experiment.

## Runtime

FORTE V3H SHA256:

8B3D4E7BA1B87F678AD4BE6F991FC16C00CE010B36EA4D49C205874553DBBAD2

open62541 SHA256:

452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318

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

C84EAC96994D25F70C99E730DC05ACC6FC5FD544B94F6D5D8D1498A0DD900383

Guard stderr:

E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855

Guard stdin token:

5E7CA2C51A0C8DACFED5FF9D9656A41D8F3AD75254962A672C2FBC9FA00D0272

Guard CSV:

EC9CCBF304F605B8C69CFA2EB4C1E82C702261DB09C0A92DD2D5166E0B77FCB4

## Safety conclusion

This evidence supports the following limited claim:

> The V3H resource was deployed and initialized on the real communication stack
> while the actuator remained at zero and the watchdog remained healthy during
> the protected observation window.

It does **not** validate active V3H regulation, disturbance-estimator behavior
under actuation, or steady-state performance.

A later bounded active V3H experiment requires a separate explicit stage and
fresh physical safety confirmation.

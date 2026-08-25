TON-LESS WATCHDOG PATCH
=======================

This patch addresses the failed Automation Studio rebuild:

Unknown data type: TON
Data type TON not defined

It replaces TON with a deterministic cycle counter.

ASSUMPTION
----------
The watchdog task period was previously identified as 100 ms.

The new timeout uses:
10 cycles x 100 ms = approximately 1 second.

WHAT IT CHANGES
---------------
Variables.var:
- removes WdTimer : TON;
- adds:
  WdCyclesWithoutHeartbeat : UDINT;
  WdTimeoutCycles : UDINT;
  WdTimedOut : BOOL;

Init.st:
- initializes the counter;
- sets WdTimeoutCycles to 10.

Cyclic.st:
- resets the counter when Heartbeat changes;
- increments it each cycle without a new Heartbeat;
- trips when the counter reaches 10;
- preserves the latched watchdog and safe physical-output gate.

Exit.st:
- removes the TON call and leaves the watchdog in a safe state.

It also moves OpcUaMap.uad.pre_finalizer_*.bak outside the project tree to
remove the Automation Studio additional-file warning.

EXECUTION
---------
1. Run the post-rebuild collector first if you want to preserve the failed
   build evidence:
   02_RUN_POST_REBUILD_COLLECTION_V2.cmd

   Enter:
   Rebuild completed: YES
   Errors: 4
   Warnings: 7
   Result: Build: 4 error(s), 7 warning(s)

2. Close Automation Studio.

3. Run:
   RUN_APPLY_TONLESS_WATCHDOG_PATCH.cmd

4. Continue only if the terminal shows:
   TON-less watchdog validation: PASSED
   READY FOR MANUAL REBUILD CONFIGURATION: YES
   READY FOR PLC TRANSFER: NO

5. Open the same watchdog_v2 project.

6. Run only:
   Project -> Rebuild Configuration

7. Do not rerun the old pre-rebuild validator. It expects WdTimer : TON.

8. Do not Transfer, Install, Build and Transfer, or enter Online mode.

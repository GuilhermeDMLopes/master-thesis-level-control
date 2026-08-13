WATCHDOG OPC UA FINALIZER
=========================

Use this package on the laboratory computer.

WHAT IT DOES
------------
- verifies the watchdog variable declarations;
- verifies INIT, CYCLIC and EXIT safety logic;
- verifies the physical I/O remapping;
- creates a timestamped backup of OpcUaMap.uad;
- adds the missing OPC UA variables:
  Heartbeat
  SafetyReset
  WatchdogHealthy
  WatchdogTripped
  AppliedEnable
  AppliedDAC
- verifies that EnableOut, DACOut and Wd... variables are not published;
- validates the resulting XML;
- collects task-class timing evidence;
- creates a report ZIP;
- optionally opens the correct project in Automation Studio.

WHAT IT DOES NOT DO
-------------------
- no PLC connection;
- no PLC write;
- no Build;
- no Transfer;
- no Install;
- no Online mode.

EXECUTION
---------
1. Close Automation Studio.
2. Extract this package.
3. Run:

   RUN_FINALIZE_WATCHDOG_OPCUA.cmd

4. Continue only when the output says:

   STATIC PROJECT VALIDATION: PASSED
   READY FOR MANUAL REBUILD CONFIGURATION: YES
   READY FOR PLC TRANSFER: NO

5. The script can open the correct project automatically.
6. In Automation Studio, run only:

   Project -> Rebuild Configuration

7. Do not Transfer, Install, Build and Transfer, or enter Online mode.

OUTPUT
------
WatchdogOpcUaFinalizeReport-<timestamp>.zip

The report contains:
- before and after copies of OpcUaMap.uad;
- all validation checks;
- the final published-variable list;
- task timing evidence;
- SHA-256 hashes.

WATCHDOG REBUILD VALIDATOR V2
=============================

Do not reuse the previous validator package.

1. Close Automation Studio.
2. Run:

   01_RUN_PRE_REBUILD_VALIDATION_V2.cmd

3. Continue only if the terminal shows:

   STATIC PROJECT VALIDATION: PASSED
   READY FOR MANUAL REBUILD CONFIGURATION: YES
   READY FOR PLC TRANSFER: NO

4. Open only:

   C:\projects\mestrado_guilherme_watchdog_v2_20260403-021715

5. Review OPC UA access permissions visually.
6. Record task name, cycle time, tolerance, and priority.
7. Run only:

   Project -> Rebuild Configuration

8. Do not Transfer, Install, Build and Transfer, or go Online.
9. Then run:

   02_RUN_POST_REBUILD_COLLECTION_V2.cmd

The validator is read-only. It does not modify the project or connect to the PLC.

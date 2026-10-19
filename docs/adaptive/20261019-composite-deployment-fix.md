# Composite type required by native deployment

The user deployment log on 2026-10-19 sends CREATE IdentificationTest Type=PROCESS_IDENTIFICATION. FORTE returns UNSUPPORTED_TYPE. Subsequent NO_SUCH_OBJECT responses follow because that instance was never created. EMB_RES and E_CYCLE creation succeed; the final resource START response does not mean the application deployed successfully.

Correction: the earlier instruction to exclude the composite from export was incorrect for this observed deployment mode. Export PROCESS_IDENTIFICATION with FORTE 1.x NG and compile its .cpp/.h alongside the four basic types. The build script now requires all ten files and checks all five object files. Keep the modular composite architecture and existing event/data connections unchanged.

Stop the old runtime, build in a fresh timestamped directory, start the newly built executable, then perform a full LocalIdentification download. Do not reuse the previous executable path or its SHA256. A fresh runtime avoids the partially created EMB_RES from the failed attempt. Only trigger INIT after all CREATE/WRITE/connection requests succeed.

Status: fix prepared; corrected composite export, compilation and native execution still require user confirmation. No algorithm changes were made.

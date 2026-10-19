# Saved mapped project checkpoint — 2026-10-19

Imported the user's PID_Whiteboard-validado-20261019-112535(1).zip (SHA256 6fa7b014f239a3de5faf04c09173813c1225d000d637530cc1be476a285b651c).

The saved project now includes LocalPID (FORTE_PC), localhost:61499, EMB_RES and all three mappings: Cycle, Process and Controller. Application and resource contain the same seven event connections and two data connections. FORTE_PC.dev, EMB_RES.res and E_RESTART.fbt are included. PID_FLAG and PID_DEMO_PROCESS are byte-identical to the previously tested local source files. All 13 offline PID tests passed after import; no additional native run was performed by the assistant.

Saved defaults remain KP=1, KI=0.5, KD=0.1, SP=1, TS_S=0.1, limits [0,10], DT=T#100ms. Runtime writes KP=2 and SP=3 were not persisted as defaults. User layout and XML are preserved exactly, including historical comments saying unmapped/native validation pending; these comments are stale. See 20261019-native-functional-checkpoint.md for the user-operated native evidence. This import supersedes that document's statement that mapping/dependencies still need to be obtained.

OPAS_Tank_System is unchanged. The PID project is a synthetic baseline; it does not yet contain an identifier or tuning law. Preserve local IDE changes before pulling this commit: the user's working copy already contains the newly tracked dependency files and modified .sys, so a direct pull may report local-file conflicts. Do not use a hard reset or clean to resolve them.

# Identification export and isolated build

2026-10-19: user reported successful FORTE 1.x NG export from 4diac 2.0.1. The file inventory confirms exactly one non-empty .cpp/.h pair per basic type. Contents have not been independently inspected or compiled here.

| Type | .cpp bytes | .h bytes |
|---|---:|---:|
| INPUT_SEQUENCE_REPLAY | 13549 | 3538 |
| OUTPUT_HISTORY | 5445 | 3385 |
| SECOND_ORDER_PROCESS | 4575 | 3052 |
| RLS_PARAMETER_ESTIMATOR | 15580 | 9091 |

The IDE capture image(20261019-190650).png shows no Problems entries and the fixed-case settings FALSE / 1.0 / 10000.0, with T#100ms. It also shows unsaved changes; save before deployment.

## Build

Run scripts/build_forte_adaptive_identification.ps1 in Windows PowerShell. This adapts the PID build procedure already executed by the user. It creates a detached worktree at FORTE revision 7c8b6296227fa292c13d71d2958a404c6db03e53 and a timestamped run under C:\Projetos\forte-adaptive-identification\runs. Existing modified FORTE sources and PID executables are preserved.

The script copies the eight exports into an isolated external module, writes its CMakeLists.txt, enables that module and monitoring, and builds with Visual Studio 18 2026 / x64. The CMake compatibility change is confined to the isolated worktree. OPC UA and boot-file loading are disabled for this simulated experiment. It verifies four object files and the executable, and records SHA256 hashes plus a transcript.

This script has been reviewed against the successful PID procedure; it has not been executed on Windows by the assistant. Compilation and native identification execution remain pending until the user returns the result. No runtime is launched or application deployed automatically.

On success return BUILD COMPLETED, the executable hash and transcript path. On failure return the first compiler/configuration error and the final lines. Do not infer mathematical correctness from compilation alone.

# Native build preparation — 2026-10-18

The user reports successful export of both custom types after the explicit
exponent-sign correction, and 13 tests passing on Windows in 0.120 s.
The exported C++ files have not been independently retrieved/reviewed yet.
This is export evidence, not a successful native build or runtime test.

Confirmed user environment: FORTE source at %USERPROFILE%\4diac\4diac-forte,
commit 7c8b6296227fa292c13d71d2958a404c6db03e53, describe
2.0.1-7-g7c8b62962-dirty; Visual Studio 18 2026 with C++ tools, x64 platform;
CMake 4.2.0-rc1. Preserve all existing tracked modifications and untracked modules.

## Build script

`scripts/build_forte_pid_whiteboard.ps1` consumes exactly one nonempty .cpp/.h
pair for PID_FLAG and PID_DEMO_PROCESS under the export directory. It creates a
fresh detached worktree at the confirmed revision and copies exported files to
an isolated external module. Existing original-source modifications are not
copied. Only the isolated top-level CMake minimum-version declaration is changed
from 2.6 to 3.5...3.20, as in the preserved reproduction compatibility patch.
The external module registration uses the existing repository's validated
forte_add_directory_module / forte_add_all_sourcefiles pattern. The exporter
CMakeLists is not overwritten; registration is created in the isolated copy.

Configuration enables LREAL support, monitoring and the PID module. OPC UA and
boot-file loading are disabled for this synthetic-only build. The script does
not launch FORTE or deploy any application. It retains source/build/module files,
export hashes and a transcript under C:\Projetos\forte-pid-whiteboard\runs.
Success requires CMake/build exit code 0, object files for both FB types and the
expected executable. This does not prove algorithm fidelity of generated C++,
runtime behavior or IEC 61499 conformity; native traces are a subsequent gate.

The script is prepared from inspected prior build scripts; it has not been run
on the user's Windows system by the assistant. Report the configure/build output
before proceeding to mapping and deployment. Do not discard original source or
project changes if any step fails.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_forte_pid_whiteboard.ps1
```

ExecutionPolicy is scoped to this process, not a system-wide setting change.

Preparation completed on 2026-10-19 after the user reconfirmed export success.
The build script has been reviewed against the preserved Windows build procedure;
PowerShell/Visual Studio are unavailable in the assistant environment, so no
Windows execution or parser-test result is claimed.

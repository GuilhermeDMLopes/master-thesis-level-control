# FORTE MPC V1 build reproduction

## Objective

This procedure reproduces the FORTE runtime configuration used for the MPC V1
work without accessing the PLC, gateway, plant, or internet.

It is intentionally limited to the runtime needed to continue MPC commissioning.

## Preserved canonical runtime

The validated runtime remains:

`forte/preserved-v1/runtimes/mpc-v1/forte.exe`

Expected SHA256:

`DBA3C8280819F648B0F75CF4F748799C7EE1CBEC5E901C2E3788302C09FB28DE`

The matching runtime dependency is:

`forte/preserved-v1/runtimes/mpc-v1/open62541.dll`

Expected SHA256:

`452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318`

## Source provenance

FORTE source commit:

`7c8b6296227fa292c13d71d2958a404c6db03e53`

open62541 source commit:

`ce5209d78d3821504d31b3bbdb03f53d6e3f93a7`

The historical FORTE source tree used for the thesis was dirty. Rather than
requiring that original mutable working tree, the reproduction script creates a
detached worktree at the recorded commit and reapplies:

- `forte/preserved-v1/provenance/forte-source/dirty-tracked.patch`;
- `forte/preserved-v1/provenance/forte-source/untracked-overlay`.

The MPC external module itself is restored from:

`forte/preserved-v1/external-modules/mpc-v1`

## Usage

Verify only:

```powershell
powershell.exe `
    -NoProfile `
    -ExecutionPolicy Bypass `
    -File .\scripts\build_forte_mpc_v1.ps1 `
    -VerifyOnly
```

Perform an isolated local rebuild:

```powershell
powershell.exe `
    -NoProfile `
    -ExecutionPolicy Bypass `
    -File .\scripts\build_forte_mpc_v1.ps1 `
    -Build
```

No network download is performed by the script.

The local machine must already contain the recorded FORTE and open62541 Git
repositories and the validated local open62541 build dependency.

## Acceptance

A rebuild passes when:

1. CMake configuration completes;
2. FORTE compiles successfully;
3. objects exist for all three custom FB types;
4. generated FORTE sources exist for all three custom FB types;
5. a new `forte.exe` is produced.

A rebuilt executable is not required to be byte-identical to the preserved
runtime because toolchain metadata may prevent deterministic binary identity.

The preserved validated executable remains the runtime for the next real-plant
zero-output deployment.

## Scope

This procedure is a reproducibility safeguard, not a new control-development
workstream.

REAL MPC AUTHORIZED: **NO**

The next physical milestone remains protected zero-output deployment of
`ResRealRawMPCV1`.
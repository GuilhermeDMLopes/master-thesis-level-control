# Validated FORTE runtime preservation V1

## Purpose

This checkpoint preserves the FORTE runtime artifacts that were actually used
during development and validation of the thesis control system.

The goal is reproducibility, not preservation of temporary CMake/Visual Studio
build directories.

## Unique runtimes

Four unique FORTE executables were identified.

| Runtime | SHA256 |
|---|---|
| PI controller V1 | C3FA8E12B486FEF6C8846DAFC85A35A1D2A4233EDD5E065E494398494E2E950D |
| Safe DAC rate limiter V1 | AD1F5DFE4203C75B89789F0A95927210A6A7190AACA596018F0CCBE230EC04A1 |
| Offline safe DAC V1 | 3D0C115C256844ACC243CF46E29109E7E0EFA0F52DC6D2ED2D734FED08430FE3 |
| MPC V1 | DBA3C8280819F648B0F75CF4F748799C7EE1CBEC5E901C2E3788302C09FB28DE |

Duplicate copies from their corresponding build directories are intentionally
not stored again.

## Canonical MPC runtime

The current runtime for the next protected MPC deployment is:

orte/preserved-v1/runtimes/mpc-v1/forte.exe

Its required open62541.dll is stored in the same directory.

## FORTE source provenance

FORTE commit:

$ForteCommit

FORTE describe:

$ForteDescribe

The FORTE source working tree used during thesis development was dirty. To avoid
losing that provenance, this checkpoint stores:

- the tracked CMake diff;
- the non-build untracked source overlay;
- the exact external MPC V1 module;
- the MPC V1 CMake cache and selected options.

The historical source overlay is evidence and is not automatically treated as
the canonical MPC implementation.

## open62541 provenance

open62541 commit:

$OpenCommit

Describe:

$OpenDescribe

The open62541 working tree was clean during this inventory.

## Scope decision

Temporary build directories such as uild, uild-offline-safe-dac,
uild-safe-dac-rate-limiter, and uild-mpc-v1 are not copied into the thesis
repository.

The reproducibility inputs, validated runtime binaries, required dependency,
source provenance, licenses, and hashes are preserved instead.

## MPC status

REAL MPC AUTHORIZED: **NO**

The next real-plant step remains the protected zero-output deployment using the
validated MPC V1 FORTE runtime.
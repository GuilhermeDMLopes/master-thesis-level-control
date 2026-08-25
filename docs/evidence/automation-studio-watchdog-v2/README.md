# Automation Studio watchdog V2 evidence

This directory preserves the Automation Studio watchdog development and
validation evidence used by the master-thesis level-control project.

## Why these files are preserved

The watchdog is part of the physical-output safety path between OPC UA command
variables and the actual PLC outputs. These files document how that path was
introduced, statically validated, rebuilt, corrected after a `TON` type build
failure, and successfully rebuilt.

The original ZIP archives are preserved byte-for-byte. Selected small files are
also extracted for direct review.

The very large post-rebuild error/warning context files are intentionally kept
only inside their ZIP archives to avoid duplicating several megabytes of
generated diagnostic text in the Git working tree.

## Evidence sequence

1. `WatchdogOpcUaFinalizeReport-20260403-030134.zip`
   - finalizes the OPC UA variable publication;
   - records the before/after `OpcUaMap.uad`;
   - records the task timing evidence.

2. `WatchdogPreRebuildValidationV2-20260403-030318.zip`
   - validates variables, watchdog logic, I/O mapping and OPC UA publication
     before the manual rebuild.

3. `WatchdogPostRebuildCollectionV2-20260403-031810.zip`
   - records the failed rebuild with 4 errors and 7 warnings.

4. `automation_studio_watchdog_tonless_patch.zip`
   - contains the exact patch script that replaced the unsupported `TON`
     watchdog timer with a deterministic cycle counter.

5. `WatchdogPostRebuildCollectionV2-20260403-032310.zip`
   - records the subsequent rebuild with 0 errors and 1 warning.

6. `automation_studio_watchdog_opcua_finalizer.zip`
   - preserves the exact finalizer script/package.

7. `automation_studio_watchdog_rebuild_validator_v2.zip`
   - preserves the exact pre/post rebuild validation package.

## Important limitation

These archives contain the exact patch/validation scripts and extensive evidence
about `Variables.var`, `Init.st`, `Cyclic.st`, `Exit.st`, `IoMap.iom` and
`OpcUaMap.uad`, but they are not themselves a complete byte-for-byte snapshot of
all final Automation Studio source files.

Accordingly, the canonical plant/PLC reference distinguishes:

- directly evidenced configuration;
- exact patch code;
- user-measured physical values;
- project-derived model/control parameters.

No missing source text is silently reconstructed as if it were original.
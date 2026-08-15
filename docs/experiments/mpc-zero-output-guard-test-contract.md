# MPC zero-output deployment guard automated test contract

## Purpose

The zero-output deployment guard is an independent, read-only safety observer
used before and during the first disabled deployment of `ResRealRawMPCV1`.

This test checkpoint hardens the guard without changing its production code.

## Required safety contract

The automated tests require the canonical guard to:

- use the established gateway endpoint and namespace;
- use the exact B&R `::Program:` PLC NodeIds validated by the project;
- contain no OPC UA value/attribute write calls;
- accept only finite numeric values;
- reject invalid BOOL-compatible values;
- treat actuator output as zero only within the explicit numerical tolerance;
- raise `ZERO-OUTPUT VIOLATION` if any gateway or PLC command/applied output
  becomes active or non-zero;
- raise `ZERO-OUTPUT VIOLATION` if gateway or PLC `WatchdogHealthy` becomes
  false at any observed sample;
- resolve and read the mandatory B&R feedback nodes before observation;
- expose an offline `--plan` mode;
- reject invalid duration/sample parameters before observation;
- require exactly one execution mode.

## Covered actuator states

The guard is tested independently against violations of:

- gateway `Enable`;
- gateway `DAC`;
- gateway `AppliedEnable`;
- gateway `AppliedDAC`;
- PLC `Enable`;
- PLC `DAC`;
- PLC `AppliedEnable`;
- PLC `AppliedDAC`.

Multiple simultaneous failures must also remain visible in the exception.

## Offline scope

The tests do not:

- connect to the gateway;
- connect to the PLC;
- start FORTE;
- deploy a 4diac resource;
- write OPC UA values;
- command any actuator.

The `--observe` mode is not executed by this automated suite.

## Laboratory use

Passing this test suite does not authorize real MPC actuation.

It only establishes that the independent guard's software contract is suitable
for the protected zero-output deployment procedure.

REAL MPC AUTHORIZED: **NO**

Next physical milestone: run the validated MPC-capable FORTE, activate the guard
first, deploy only `ResRealRawMPCV1` with `ENABLE_REQUEST = FALSE`, trigger
`MpcInitMerge.EI1` once, and require continuous zero actuator output.
# Offline MPC checkpoint v1

## Status

This checkpoint freezes the first reproducible nonlinear MPC development
baseline before any additive 4diac/FORTE implementation.

## Selected model

Canonical repository path:

models/mpc/deadzone-hammerstein-v1.json

SHA-256:

$ExpectedModelSha256

Model family:

- first-order dead-zone Hammerstein model;
- positive monotone input effect;
- stable state dynamics;
- raw-count process variable;
- identified pump dead-zone;
- trajectory-level validation.

## Offline controller envelope

- setpoint: 450 raw;
- sample time: 0.1 s;
- DAC range: 0..12000;
- maximum command move: 150 DAC/cycle;
- prediction horizon: 20 s;
- predicted soft level: 650 raw;
- predicted hard level: 750 raw;
- measured hard trip: 800 raw.

## Validation

The move-blocked nonlinear MPC robustness simulation passed 10/10 configured
offline scenarios before this checkpoint was created.

The executable controller contract is preserved in:

- scripts/mpc_reference_controller.py
- 	ests/test_mpc_reference_controller_contract.py
- docs/mpc/mpc-controller-contract.md

## Reproducibility

The real laboratory identification CSVs used during this phase are preserved
under:

data/sample/mpc-identification-v1

Generated working outputs may continue to be written below esults/, which
remains ignored by Git.

## Historical preservation

This checkpoint does not delete, rename, overwrite, or replace existing
OPAS_Tank_System communication, PI, or historical MPC artifacts.

The next 4diac implementation must be additive.

## Authorization

Offline MPC robustness: PASSED.

Controller contract tests: must pass before commit.

Real MPC commissioning: NOT AUTHORIZED by this checkpoint.
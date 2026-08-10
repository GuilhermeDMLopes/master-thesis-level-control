# MPC identification dataset v1

This directory preserves the real laboratory CSV files used by the offline
MPC identification workflow in August 2026.

The original acquisition files remain under data/raw locally. Those paths
are ignored by Git. This sample checkpoint exists so a clean repository clone
can reproduce and audit the model-selection workflow.

## Intended use

The nonlinear model can be regenerated with:

``powershell
python scripts/identify_deadzone_hammerstein_model.py
    --data-root data/sample/mpc-identification-v1
``

The independent 12000-DAC 20-second plateau remains identifiable by the
default validation-source pattern:

steady-calibration-20260808-103827

## Safety

These are preserved data files only. Re-running identification is offline and
does not authorize real-plant MPC execution.

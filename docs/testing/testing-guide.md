# Testing Guide

## Purpose

This document describes how to configure the Python development environment and execute the automated offline tests for the project.

The current tests validate gateway processing functions, OPC UA interface helpers, and preservation of the historical 4diac project without requiring:

- A B&R PLC.
- An OPC UA server.
- Eclipse 4diac FORTE.
- Access to the laboratory network.
- A running physical process.

## Tested Environment

The initial test environment was validated with:

```text
Python 3.10.11
pytest 9.1.1
asyncua 1.1.8
```

The Python package versions used by the project are defined in:

```text
requirements.txt
requirements-dev.txt
```

## Repository Location

All commands in this document must be executed from the repository root:

```text
C:\Projetos\master-thesis-level-control
```

Confirm the current directory in PowerShell:

```powershell
Get-Location
```

## Create the Virtual Environment

Create a Python virtual environment:

```powershell
python -m venv ".venv"
```

Confirm that the Python executable was created:

```powershell
Test-Path ".venv\Scripts\python.exe"
```

Expected result:

```text
True
```

Confirm the Python version:

```powershell
.\.venv\Scripts\python.exe --version
```

The virtual environment directory is ignored by Git.

## Install Development Dependencies

Install the runtime and test dependencies:

```powershell
.\.venv\Scripts\python.exe `
    -m pip install `
    -r requirements-dev.txt
```

The development requirements file includes the runtime requirements through:

```text
-r requirements.txt
```

Therefore, it is not necessary to install both files separately.

## Validate Installed Dependencies

Check whether the installed packages have unresolved dependency conflicts:

```powershell
.\.venv\Scripts\python.exe -m pip check
```

Expected result:

```text
No broken requirements found.
```

Confirm the installed pytest version:

```powershell
.\.venv\Scripts\python.exe -m pytest --version
```

Confirm the installed asyncua version:

```powershell
.\.venv\Scripts\python.exe -c `
    "import importlib.metadata as metadata; print(metadata.version('asyncua'))"
```

## Run All Tests

Execute all automated tests from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The `-q` option produces a compact report.

The current offline gateway test baseline contains:

```text
38 tests
```

A successful result is similar to:

```text
........................ [100%]
38 passed
```

The execution time may vary between computers.

## Run Tests with Detailed Output

Use verbose mode to display every test case:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

## Run Only the Gateway Processing Tests

```powershell
.\.venv\Scripts\python.exe `
    -m pytest `
    "tests\test_gateway_processing.py" `
    -v
```

## Run Only the Gateway Interface Tests

```powershell
.\.venv\Scripts\python.exe `
    -m pytest `
    "tests\test_gateway_interface.py" `
    -v
```
## Run a Specific Test Function

Example:

```powershell
.\.venv\Scripts\python.exe `
    -m pytest `
    "tests\test_gateway_processing.py::test_dac_to_percent" `
    -v
```

## List Tests Without Executing Them

```powershell
.\.venv\Scripts\python.exe `
    -m pytest `
    --collect-only `
    -q
```

This command is useful for confirming which tests pytest discovered.

## Current Test Coverage

The current unit tests validate:

### DAC conversion

Function:

```text
dac_to_percent
```

Cases include:

- Zero DAC command.
- Mid-range DAC command.
- Maximum DAC command.
- Values below the configured range.
- Values above the configured range.
- Invalid string input.
- `None` input.

### Level conversion

Function:

```text
raw_level_to_cm
```

Cases include:

- Zero raw level.
- Normal raw level.
- Negative raw level.
- Invalid string input.
- `None` input.

### Filter coefficient limiting

Function:

```text
clamp_alpha
```

Cases include:

- Values below zero.
- Zero.
- Intermediate values.
- One.
- Values above one.
- Invalid string input.
- `None` input.

### Filter update

Function:

```text
update_filtered_value
```

Cases include:

- Filter initialization.
- Normal filter calculation.
- Filter reset.
- Alpha equal to zero.
- Alpha equal to one.

## Gateway OPC UA Interface Coverage

The gateway interface tests validate:

- Creation of the legacy `Nivel`, `Enable`, and `DAC` NodeIds.
- Creation of `EnableFeedback` and `DACFeedback`.
- Initial OPC UA values and Variant types.
- Write access only for command variables.
- Read-only behavior of process and feedback variables.
- References returned by `GatewayVariables`.
- Publication of confirmed PLC feedback values.
- Separation between command and feedback variables.
- Conversion to OPC UA `Boolean` and `Int16` values.
## Validate Python Syntax

Validate the gateway source modules without executing the gateway:

```powershell
.\.venv\Scripts\python.exe `
    -m py_compile `
    "gateway\src\gateway_config.py" `
    "gateway\src\gateway_processing.py" `
    "gateway\src\gateway_opcua.py"
```

Validate the test source files:

```powershell
.\.venv\Scripts\python.exe `
    -m py_compile `
    "tests\conftest.py" `
    "tests\test_gateway_processing.py"
```

Successful syntax validation produces no output.

## Important Safety Restriction

The automated unit tests do not execute the gateway main loop.

Do not run the following command outside the laboratory unless a simulator or test OPC UA server has been configured:

```powershell
python gateway/src/gateway_opcua.py
```

The current gateway attempts to connect to the real B&R OPC UA endpoint:

```text
opc.tcp://10.0.0.3:4840
```

## Test Directory Structure

```text
tests/
|-- conftest.py
|-- test_gateway_interface.py
`-- test_gateway_processing.py
```

### `conftest.py`

Adds the following source directory to the Python import path during test execution:

```text
gateway/src
```

### `test_gateway_interface.py`

Contains offline unit tests for NodeId creation, access rules,
initial values, and feedback publication in the gateway OPC UA interface.

### `test_gateway_processing.py`

Contains parameterized unit tests for the gateway processing functions.

## Adding New Tests

New test files should follow the pytest naming convention:

```text
test_*.py
```

Test functions should follow:

```text
test_*
```

Example:

```python
def test_example_behavior() -> None:
    assert expected_value == actual_value
```

Tests that require the physical PLC must not be added to the offline unit test suite without an explicit integration-test marker or a separate test configuration.

## Before Creating a Commit

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Then validate the staged files:

```powershell
git diff --cached --check
```

A commit containing gateway changes should not be created while any automated test is failing.

## Troubleshooting

### `pytest` is not installed

Install the development dependencies:

```powershell
.\.venv\Scripts\python.exe `
    -m pip install `
    -r requirements-dev.txt
```

### `ModuleNotFoundError` for gateway modules

Confirm that the command is being executed from the repository root and that this file exists:

```text
tests/conftest.py
```

### The virtual environment does not exist

Recreate it:

```powershell
python -m venv ".venv"
```

### PowerShell activation is blocked

Activation is not required.

Use the environment executable directly:

```powershell
.\.venv\Scripts\python.exe
```

### Cache directories appear in Git

The following directories must remain ignored:

```text
.venv/
.pytest_cache/
__pycache__/
```

Check an ignored path with:

```powershell
git check-ignore -v ".pytest_cache"
```

## Validation Status

The initial offline gateway processing suite was successfully validated with:

```text
38 passed
```

## Run the 4diac Preservation Tests

```powershell
.\.venv\Scripts\python.exe `
    -m pytest `
    "tests\test_4diac_gateway_contract.py" `
    -v
```

These tests allow additive changes to the 4diac project but detect removal or renaming of recorded historical artifacts.

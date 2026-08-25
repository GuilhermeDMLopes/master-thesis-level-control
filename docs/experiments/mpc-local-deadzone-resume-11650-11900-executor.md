# Protected resume executor for local dead-zone identification

## Status

Prepared offline after checkpointing the revised execution semantics.

This artifact is **not executed by the preparation stage**.

## Remaining DAC points

The already-preserved 11600-DAC point is not repeated automatically.

Remaining points:

- 11650
- 11700
- 11750
- 11800
- 11850
- 11900

## Target acquisition

The old executor counted the actuator ramp inside the 45 s ACTIVE window.

The resume executor separates the phases:

1. `ACQUIRE`
   - command the requested DAC;
   - monitor all safety variables;
   - require `AppliedDAC = target +/-5 DAC`;
   - require 5 consecutive samples;
   - timeout after 30 s;
2. `HOLD`
   - only after acquisition succeeds;
   - preserve a full 45 s constant-target interval;
   - abort if AppliedDAC leaves the target tolerance.

## Recovery and local rebaseline

After every point:

- force and verify commanded/applied zero output;
- remain at zero for at least 30 s;
- require a 20 s stable window;
- require `|Median9 slope| <= 1 raw/s`;
- require Median9 range `<=30 raw`;
- define the median of that accepted stable window as the next local baseline;
- require a manual physical measurement `<=1 cm` before the next point.

Each point logs:

`Delta Median9 = Median9 - local baseline`

This avoids requiring the plant to return to the first numerical baseline of the
entire session.

## Safety contract

Unchanged:

- instantaneous raw abort: 1100;
- rolling Median9 abort: 1100;
- positive Median9-rate abort: 180 raw/s;
- maximum DAC: 12000;
- active physical abort: 5 cm;
- watchdog unhealthy/tripped: abort;
- communication failure: abort;
- operator may press `Q` during acquisition/hold/rebaseline.

## Runtime separation

The Python runner supports:

- `--plan`: offline contract printout, no OPC UA import/network access;
- `--run`: real-lab execution.

The PowerShell wrapper executes the Python file normally. It does **not** pipe
the Python source through stdin, so interactive `APPLY_<DAC>` prompts remain
attached to the console.

FORTE, PI and MPC must remain stopped during this open-loop identification.

## Evidence

A real execution creates a dedicated directory under `data/raw/` containing:

- `local-deadzone-resume-monitor.csv`;
- `run-summary.json`;
- `physical-observations.txt`;
- gateway stdout/stderr when the wrapper starts the gateway.

No partial or aborted point is automatically repeated.

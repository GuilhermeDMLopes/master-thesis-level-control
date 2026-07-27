from __future__ import annotations

import os
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

# Repository root:
#
# gateway/src/gateway_config.py
#       -> src
#       -> gateway
#       -> repository root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Raw experiment files are stored outside the source directory.
CSV_OUTPUT_DIRECTORY = PROJECT_ROOT / "data" / "raw"


# ============================================================
# OPC UA CONFIGURATION
# ============================================================

# Default OPC UA server provided by the real B&R PLC.
DEFAULT_BR_ENDPOINT = "opc.tcp://10.0.0.3:4840"

# The endpoint may be overridden without editing the source code.
#
# Real PLC:
#     BR_ENDPOINT is not defined in the environment.
#
# Local simulator:
#     BR_ENDPOINT=opc.tcp://127.0.0.1:4842
BR_ENDPOINT = os.environ.get(
    "BR_ENDPOINT",
    DEFAULT_BR_ENDPOINT,
)

# OPC UA server exposed by the Python gateway to 4diac FORTE.
GATEWAY_ENDPOINT = "opc.tcp://0.0.0.0:4841"

# Original OPC UA NodeIds exposed by the B&R PLC.
BR_LEVEL_NODE_ID = "ns=6;s=::Program:Nivel"
BR_ENABLE_NODE_ID = "ns=6;s=::Program:Enable"
BR_DAC_NODE_ID = "ns=6;s=::Program:DAC"

# Namespace exposed by the Python gateway.
GATEWAY_NAMESPACE_URI = "urn:br-4diac-gateway"

# Read-only feedback NodeIds exposed by the gateway.
GATEWAY_ENABLE_FEEDBACK_NODE_ID = "EnableFeedback"
GATEWAY_DAC_FEEDBACK_NODE_ID = "DACFeedback"

# Internal gateway execution period.
GATEWAY_CYCLE_TIME_S = 0.1

# Delay between attempts to reconnect to the B&R PLC.
BR_RECONNECT_INTERVAL_S = 5.0


# ============================================================
# LEVEL CONFIGURATION
# ============================================================

# Current provisional level conversion:
#
#     Level_cm = Raw_Level / LEVEL_SCALE
#
# Example:
#
#     Raw_Level = 14000
#     Level_cm = 14.0
#
# This value still requires physical validation in the laboratory.
LEVEL_SCALE = 1000.0


# ============================================================
# CONTROLLER METADATA
# ============================================================

# These parameters describe the current PI/PID configuration in 4diac.
#
# They are used by the gateway only for logging and offline analysis.
# The real controller continues to execute in 4diac FORTE.
PI_SETPOINT_CM = 14.0
PI_KP = 4.0
PI_KI = 0.5
PI_KD = 0.0
PI_SAMPLING_TIME_S = 0.1
PI_MANUAL_MODE = False
PI_MANUAL_OUTPUT = 0.0
PI_RESET = False

# Raw setpoint equivalent recorded as experiment metadata.
PI_SETPOINT_RAW_EQUIVALENT = PI_SETPOINT_CM * LEVEL_SCALE


# ============================================================
# FILTER METADATA
# ============================================================

# Process variable filter configured in 4diac.
#
#     Filtered_PV(k) =
#         Alpha * Filtered_PV(k - 1)
#         + (1 - Alpha) * Current_PV(k)
PV_FILTER_ALPHA = 0.95
PV_FILTER_RESET = False


# ============================================================
# DAC CONFIGURATION
# ============================================================

# Computational range of the DAC command.
DAC_MIN = 0
DAC_MAX = 32000

# DAC rate limiter parameters configured in 4diac.
#
# These values are recorded by the gateway as experiment metadata.
DAC_LIMITER_MAX_DELTA = 150.0
DAC_LIMITER_MIN = 0.0
DAC_LIMITER_MAX = 32000.0
DAC_LIMITER_RESET = False


# ============================================================
# FINAL DAC BOUNDARY LIMITER
# ============================================================

# The IEC 61499 limiter constrains each FORTE execution. The gateway applies
# an additional final limit at the PLC write boundary because more than one
# FORTE update may occur between two gateway reads.
#
# This guarantees that every DAC value effectively written by the gateway
# changes by no more than DAC_BOUNDARY_MAX_DELTA relative to the latest value
# successfully applied or confirmed by the PLC.
DAC_BOUNDARY_MAX_DELTA = 150
DAC_BOUNDARY_MIN = DAC_MIN
DAC_BOUNDARY_MAX = DAC_MAX


# ============================================================
# CSV LOGGING
# ============================================================

# CSV logging period.
LOG_PERIOD_S = 0.1

# CSV output filename.
CSV_FILENAME = "real_pi_test_cm_alpha095_dac_delta150.csv"

# Complete CSV output path.
CSV_PATH = CSV_OUTPUT_DIRECTORY / CSV_FILENAME

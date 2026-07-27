from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

from gateway_config import (
    DAC_MAX,
    DAC_MIN,
    LEVEL_SCALE,
)


@dataclass(frozen=True)
class DacBoundaryResult:
    """Result of one final DAC rate-limiting calculation."""

    requested_dac: int
    bounded_requested_dac: int
    reference_dac: int
    applied_dac: int
    applied_delta: int
    limited: bool


def _integer_configuration_value(
    value: Any,
    *,
    name: str,
) -> int:
    """Convert an integer-valued configuration item or reject it."""
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"{name} must be a finite integer"
        ) from error

    if not isfinite(numeric_value) or not numeric_value.is_integer():
        raise ValueError(
            f"{name} must be a finite integer"
        )

    return int(numeric_value)


def _dac_value_or_minimum(
    value: Any,
    *,
    dac_min: int,
) -> int:
    """Normalize a DAC value while retaining the gateway's safe fallback."""
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return dac_min

    if not isfinite(numeric_value):
        return dac_min

    return int(numeric_value)


def limit_dac_boundary_step(
    *,
    requested_dac: Any,
    reference_dac: Any,
    maximum_delta: Any,
    dac_min: Any,
    dac_max: Any,
) -> DacBoundaryResult:
    """
    Limit one DAC write relative to the value applied at the PLC boundary.

    The function is intentionally stateless. The caller must use the latest
    successfully written or PLC-confirmed DAC value as ``reference_dac``.
    This makes reconnection behavior explicit and prevents a failed write from
    advancing hidden limiter state.
    """
    minimum = _integer_configuration_value(
        dac_min,
        name="dac_min",
    )
    maximum = _integer_configuration_value(
        dac_max,
        name="dac_max",
    )
    delta_limit = _integer_configuration_value(
        maximum_delta,
        name="maximum_delta",
    )

    if minimum >= maximum:
        raise ValueError(
            "dac_min must be less than dac_max"
        )

    if delta_limit <= 0:
        raise ValueError(
            "maximum_delta must be greater than zero"
        )

    requested = _dac_value_or_minimum(
        requested_dac,
        dac_min=minimum,
    )
    reference = _dac_value_or_minimum(
        reference_dac,
        dac_min=minimum,
    )

    bounded_requested = max(
        minimum,
        min(maximum, requested),
    )
    bounded_reference = max(
        minimum,
        min(maximum, reference),
    )

    requested_delta = (
        bounded_requested - bounded_reference
    )

    applied_delta = max(
        -delta_limit,
        min(delta_limit, requested_delta),
    )

    applied_dac = bounded_reference + applied_delta

    return DacBoundaryResult(
        requested_dac=requested,
        bounded_requested_dac=bounded_requested,
        reference_dac=bounded_reference,
        applied_dac=applied_dac,
        applied_delta=applied_delta,
        limited=(applied_dac != requested),
    )


def dac_to_percent(dac_value: Any) -> float:
    """
    Convert a DAC command to actuator percentage.

    DAC = 0     -> 0 %
    DAC = 32000 -> 100 %

    Invalid values are converted to zero to preserve the current
    gateway behavior.
    """
    try:
        numeric_value = float(dac_value)
    except (TypeError, ValueError):
        numeric_value = 0.0

    numeric_value = max(
        DAC_MIN,
        min(DAC_MAX, numeric_value),
    )

    return (numeric_value / DAC_MAX) * 100.0


def raw_level_to_cm(raw_level: Any) -> float:
    """
    Convert the raw B&R level value to centimeters.

    Current provisional conversion:

        Level_cm = Raw_Level / LEVEL_SCALE

    This conversion still requires physical validation in the laboratory.

    Invalid values are converted to zero to preserve the current
    gateway behavior.
    """
    try:
        return float(raw_level) / LEVEL_SCALE
    except (TypeError, ValueError):
        return 0.0


def clamp_alpha(alpha: Any) -> float:
    """
    Limit a filter coefficient to the interval [0, 1].

    alpha = 0.0 -> no memory
    alpha = 1.0 -> full memory

    Invalid values are converted to zero to preserve the current
    gateway behavior.
    """
    try:
        numeric_alpha = float(alpha)
    except (TypeError, ValueError):
        numeric_alpha = 0.0

    return max(
        0.0,
        min(1.0, numeric_alpha),
    )


def update_filtered_value(
    previous_filtered: float | None,
    current_value: float,
    alpha: float,
    reset: bool = False,
) -> float:
    """
    Calculate the filtered value used for CSV analysis.

    Equation:

        Filtered_Value(k) =
            Alpha * Filtered_Value(k - 1)
            + (1 - Alpha) * Current_Value(k)

    This calculation does not affect the controller executed in
    4diac FORTE.
    """
    limited_alpha = clamp_alpha(alpha)

    if reset or previous_filtered is None:
        return current_value

    return (
        limited_alpha * previous_filtered
        + (1.0 - limited_alpha) * current_value
    )

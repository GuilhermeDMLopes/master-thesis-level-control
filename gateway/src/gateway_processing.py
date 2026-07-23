from __future__ import annotations

from typing import Any

from gateway_config import (
    DAC_MAX,
    DAC_MIN,
    LEVEL_SCALE,
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

from __future__ import annotations

from typing import Any

import pytest

from gateway_processing import (
    clamp_alpha,
    dac_to_percent,
    raw_level_to_cm,
    update_filtered_value,
)


@pytest.mark.parametrize(
    "dac_value, expected_percent",
    [
        (0, 0.0),
        (16000, 50.0),
        (32000, 100.0),
        (-100, 0.0),
        (40000, 100.0),
        ("invalid", 0.0),
        (None, 0.0),
    ],
)
def test_dac_to_percent(
    dac_value: Any,
    expected_percent: float,
) -> None:
    assert dac_to_percent(dac_value) == pytest.approx(
        expected_percent
    )


@pytest.mark.parametrize(
    "raw_level, expected_level_cm",
    [
        (0, 0.0),
        (14000, 14.0),
        (-1000, -1.0),
        ("invalid", 0.0),
        (None, 0.0),
    ],
)
def test_raw_level_to_cm(
    raw_level: Any,
    expected_level_cm: float,
) -> None:
    assert raw_level_to_cm(raw_level) == pytest.approx(
        expected_level_cm
    )


@pytest.mark.parametrize(
    "alpha, expected_alpha",
    [
        (-1.0, 0.0),
        (0.0, 0.0),
        (0.5, 0.5),
        (1.0, 1.0),
        (2.0, 1.0),
        ("invalid", 0.0),
        (None, 0.0),
    ],
)
def test_clamp_alpha(
    alpha: Any,
    expected_alpha: float,
) -> None:
    assert clamp_alpha(alpha) == pytest.approx(
        expected_alpha
    )


@pytest.mark.parametrize(
    (
        "previous_filtered",
        "current_value",
        "alpha",
        "reset",
        "expected_value",
    ),
    [
        (None, 10.0, 0.95, False, 10.0),
        (10.0, 20.0, 0.5, False, 15.0),
        (10.0, 20.0, 0.5, True, 20.0),
        (10.0, 20.0, 0.0, False, 20.0),
        (10.0, 20.0, 1.0, False, 10.0),
    ],
)
def test_update_filtered_value(
    previous_filtered: float | None,
    current_value: float,
    alpha: float,
    reset: bool,
    expected_value: float,
) -> None:
    assert update_filtered_value(
        previous_filtered=previous_filtered,
        current_value=current_value,
        alpha=alpha,
        reset=reset,
    ) == pytest.approx(expected_value)

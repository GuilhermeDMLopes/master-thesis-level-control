from __future__ import annotations

from typing import Any

import pytest

from gateway_processing import (
    clamp_alpha,
    dac_to_percent,
    limit_dac_boundary_step,
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


@pytest.mark.parametrize(
    (
        "requested_dac",
        "reference_dac",
        "expected_applied",
        "expected_delta",
        "expected_limited",
    ),
    [
        (0, 0, 0, 0, False),
        (9084, 0, 150, 150, True),
        (9084, 150, 300, 150, True),
        (1000, 900, 1000, 100, False),
        (0, 900, 750, -150, True),
        (0, 150, 0, -150, False),
        (40000, 31900, 32000, 100, True),
        (-100, 100, 0, -100, True),
    ],
)
def test_limit_dac_boundary_step(
    requested_dac: int,
    reference_dac: int,
    expected_applied: int,
    expected_delta: int,
    expected_limited: bool,
) -> None:
    result = limit_dac_boundary_step(
        requested_dac=requested_dac,
        reference_dac=reference_dac,
        maximum_delta=150,
        dac_min=0,
        dac_max=32000,
    )

    assert result.requested_dac == requested_dac
    assert result.applied_dac == expected_applied
    assert result.applied_delta == expected_delta
    assert result.limited is expected_limited


def test_boundary_reference_can_be_reset_from_confirmed_dac() -> None:
    """A reconnect starts the next step from the PLC-confirmed value."""
    result = limit_dac_boundary_step(
        requested_dac=32000,
        reference_dac=750,
        maximum_delta=150,
        dac_min=0,
        dac_max=32000,
    )

    assert result.reference_dac == 750
    assert result.applied_dac == 900
    assert result.applied_delta == 150


@pytest.mark.parametrize(
    (
        "maximum_delta",
        "dac_min",
        "dac_max",
        "expected_message",
    ),
    [
        (0, 0, 32000, "maximum_delta must be greater than zero"),
        (-1, 0, 32000, "maximum_delta must be greater than zero"),
        (150.5, 0, 32000, "maximum_delta must be a finite integer"),
        (150, 100, 100, "dac_min must be less than dac_max"),
        (150, 101, 100, "dac_min must be less than dac_max"),
    ],
)
def test_invalid_dac_boundary_configuration_is_rejected(
    maximum_delta: float,
    dac_min: int,
    dac_max: int,
    expected_message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        limit_dac_boundary_step(
            requested_dac=1000,
            reference_dac=0,
            maximum_delta=maximum_delta,
            dac_min=dac_min,
            dac_max=dac_max,
        )

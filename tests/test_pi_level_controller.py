from __future__ import annotations

import pytest

from simulation.pi_level_controller import PILevelController


DEFAULT_CONFIGURATION = {
    "proportional_gain": 4.0,
    "integral_gain": 0.5,
    "sampling_time_s": 0.1,
    "output_min": 0.0,
    "output_max": 100.0,
}


def run_cycle(
    controller: PILevelController,
    *,
    process_variable: float,
    setpoint: float = 14.0,
    **overrides: object,
):
    configuration = {
        **DEFAULT_CONFIGURATION,
        **overrides,
    }

    return controller.update(
        process_variable=process_variable,
        setpoint=setpoint,
        **configuration,
    )


def test_proportional_and_integral_terms_are_calculated() -> None:
    controller = PILevelController()

    result = run_cycle(
        controller,
        process_variable=10.0,
    )

    assert result.error == pytest.approx(4.0)
    assert result.proportional_term == pytest.approx(16.0)
    assert result.integral_term == pytest.approx(0.2)
    assert result.unsaturated_output == pytest.approx(16.2)
    assert result.output == pytest.approx(16.2)
    assert result.saturated is False


def test_integral_term_accumulates_across_cycles() -> None:
    controller = PILevelController()

    first = run_cycle(
        controller,
        process_variable=12.0,
    )
    second = run_cycle(
        controller,
        process_variable=12.0,
    )

    assert first.integral_term == pytest.approx(0.1)
    assert second.integral_term == pytest.approx(0.2)


def test_upper_saturation_prevents_positive_windup() -> None:
    controller = PILevelController()

    for _ in range(100):
        result = run_cycle(
            controller,
            process_variable=-20.0,
        )

    assert result.output == pytest.approx(100.0)
    assert result.saturated is True
    assert controller.integral_term == pytest.approx(0.0)


def test_lower_saturation_prevents_negative_windup() -> None:
    controller = PILevelController()

    for _ in range(100):
        result = run_cycle(
            controller,
            process_variable=40.0,
        )

    assert result.output == pytest.approx(0.0)
    assert result.saturated is True
    assert controller.integral_term == pytest.approx(0.0)


def test_integral_is_allowed_to_unwind_from_upper_saturation() -> None:
    controller = PILevelController()

    run_cycle(
        controller,
        process_variable=14.0,
        manual=True,
        manual_output=90.0,
    )
    result = run_cycle(
        controller,
        process_variable=16.0,
    )

    assert result.integral_term == pytest.approx(90.0)
    assert result.output == pytest.approx(82.0)

    next_result = run_cycle(
        controller,
        process_variable=16.0,
    )

    assert next_result.integral_term < 90.0
    assert next_result.output < result.output


def test_manual_output_is_clamped_and_tracked() -> None:
    controller = PILevelController()

    result = run_cycle(
        controller,
        process_variable=14.0,
        manual=True,
        manual_output=120.0,
    )

    assert result.output == pytest.approx(100.0)
    assert result.integral_term == pytest.approx(100.0)
    assert result.saturated is True
    assert result.manual_active is True


def test_manual_to_automatic_transfer_is_bumpless() -> None:
    controller = PILevelController()

    manual_result = run_cycle(
        controller,
        process_variable=12.0,
        manual=True,
        manual_output=35.0,
    )
    automatic_result = run_cycle(
        controller,
        process_variable=12.0,
        manual=False,
    )

    assert manual_result.output == pytest.approx(35.0)
    assert automatic_result.output == pytest.approx(35.0)
    assert automatic_result.manual_active is False


def test_reset_clears_state_and_forces_zero_output() -> None:
    controller = PILevelController()

    run_cycle(
        controller,
        process_variable=12.0,
    )

    result = run_cycle(
        controller,
        process_variable=10.0,
        reset=True,
    )

    assert controller.integral_term == pytest.approx(0.0)
    assert result.output == pytest.approx(0.0)
    assert result.integral_term == pytest.approx(0.0)
    assert result.reset_active is True


def test_reset_output_respects_positive_output_minimum() -> None:
    controller = PILevelController()

    result = run_cycle(
        controller,
        process_variable=10.0,
        output_min=10.0,
        reset=True,
    )

    assert result.output == pytest.approx(10.0)


@pytest.mark.parametrize(
    "sampling_time_s",
    [0.0, -0.1],
)
def test_invalid_sampling_time_is_rejected(
    sampling_time_s: float,
) -> None:
    controller = PILevelController()

    with pytest.raises(
        ValueError,
        match="sampling_time_s must be greater than zero",
    ):
        run_cycle(
            controller,
            process_variable=10.0,
            sampling_time_s=sampling_time_s,
        )


@pytest.mark.parametrize(
    "output_min, output_max",
    [
        (100.0, 100.0),
        (101.0, 100.0),
    ],
)
def test_invalid_output_limits_are_rejected(
    output_min: float,
    output_max: float,
) -> None:
    controller = PILevelController()

    with pytest.raises(
        ValueError,
        match="output_min must be less than output_max",
    ):
        run_cycle(
            controller,
            process_variable=10.0,
            output_min=output_min,
            output_max=output_max,
        )

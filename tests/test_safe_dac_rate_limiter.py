from __future__ import annotations

import pytest

from simulation.safe_dac_rate_limiter import SafeDacRateLimiter


DEFAULT_CONFIGURATION = {
    "max_delta_dac": 150.0,
    "dac_min": 0.0,
    "dac_max": 32000.0,
    "initial_dac": 0.0,
}


def run_cycle(
    limiter: SafeDacRateLimiter,
    *,
    dac_input: float,
    **overrides: object,
):
    configuration = {
        **DEFAULT_CONFIGURATION,
        **overrides,
    }

    return limiter.update(
        dac_input=dac_input,
        **configuration,
    )


def test_first_cycle_uses_initial_dac_instead_of_input() -> None:
    limiter = SafeDacRateLimiter()

    result = run_cycle(
        limiter,
        dac_input=9084.0,
    )

    assert result.dac_output == pytest.approx(0.0)
    assert result.limited is True
    assert result.initialized is True
    assert result.reset_active is False


def test_second_cycle_moves_up_by_maximum_delta() -> None:
    limiter = SafeDacRateLimiter()

    run_cycle(limiter, dac_input=9084.0)
    result = run_cycle(limiter, dac_input=9084.0)

    assert result.dac_output == pytest.approx(150.0)
    assert result.limited is True


def test_repeated_cycles_ramp_up_without_exceeding_delta() -> None:
    limiter = SafeDacRateLimiter()

    outputs = [
        run_cycle(limiter, dac_input=1000.0).dac_output
        for _ in range(5)
    ]

    assert outputs == pytest.approx(
        [0.0, 150.0, 300.0, 450.0, 600.0]
    )

    changes = [
        current - previous
        for previous, current in zip(outputs, outputs[1:])
    ]

    assert max(changes) <= 150.0


def test_downward_change_is_limited_symmetrically() -> None:
    limiter = SafeDacRateLimiter()

    run_cycle(
        limiter,
        dac_input=0.0,
        initial_dac=1000.0,
    )
    result = run_cycle(
        limiter,
        dac_input=0.0,
        initial_dac=1000.0,
    )

    assert result.dac_output == pytest.approx(850.0)
    assert result.limited is True


def test_reachable_input_is_copied_without_limiting() -> None:
    limiter = SafeDacRateLimiter()

    run_cycle(limiter, dac_input=100.0)
    result = run_cycle(limiter, dac_input=100.0)

    assert result.dac_output == pytest.approx(100.0)
    assert result.limited is False


def test_input_above_maximum_is_bounded() -> None:
    limiter = SafeDacRateLimiter()

    run_cycle(
        limiter,
        dac_input=50000.0,
        initial_dac=31900.0,
    )
    result = run_cycle(
        limiter,
        dac_input=50000.0,
        initial_dac=31900.0,
    )

    assert result.dac_output == pytest.approx(32000.0)
    assert result.limited is True


def test_input_below_minimum_is_bounded() -> None:
    limiter = SafeDacRateLimiter()

    run_cycle(
        limiter,
        dac_input=-1000.0,
        dac_min=100.0,
        initial_dac=250.0,
    )
    result = run_cycle(
        limiter,
        dac_input=-1000.0,
        dac_min=100.0,
        initial_dac=250.0,
    )

    assert result.dac_output == pytest.approx(100.0)
    assert result.limited is True


def test_initial_dac_is_clamped_to_output_limits() -> None:
    limiter = SafeDacRateLimiter()

    result = run_cycle(
        limiter,
        dac_input=1000.0,
        initial_dac=-500.0,
    )

    assert result.dac_output == pytest.approx(0.0)
    assert limiter.dac_output == pytest.approx(0.0)


def test_reset_forces_bounded_initial_value() -> None:
    limiter = SafeDacRateLimiter()

    run_cycle(limiter, dac_input=1000.0)
    run_cycle(limiter, dac_input=1000.0)
    result = run_cycle(
        limiter,
        dac_input=1000.0,
        initial_dac=200.0,
        reset=True,
    )

    assert result.dac_output == pytest.approx(200.0)
    assert result.reset_active is True
    assert result.initialized is True


def test_repeated_reset_cycles_are_deterministic() -> None:
    limiter = SafeDacRateLimiter()

    first = run_cycle(
        limiter,
        dac_input=1000.0,
        initial_dac=200.0,
        reset=True,
    )
    second = run_cycle(
        limiter,
        dac_input=3000.0,
        initial_dac=200.0,
        reset=True,
    )

    assert first.dac_output == pytest.approx(200.0)
    assert second.dac_output == pytest.approx(200.0)


def test_release_from_reset_ramps_from_reset_value() -> None:
    limiter = SafeDacRateLimiter()

    run_cycle(
        limiter,
        dac_input=1000.0,
        initial_dac=200.0,
        reset=True,
    )
    result = run_cycle(
        limiter,
        dac_input=1000.0,
        initial_dac=200.0,
        reset=False,
    )

    assert result.dac_output == pytest.approx(350.0)
    assert result.reset_active is False


@pytest.mark.parametrize("max_delta_dac", [0.0, -1.0])
def test_invalid_maximum_delta_is_rejected(
    max_delta_dac: float,
) -> None:
    limiter = SafeDacRateLimiter()

    with pytest.raises(
        ValueError,
        match="max_delta_dac must be greater than zero",
    ):
        run_cycle(
            limiter,
            dac_input=1000.0,
            max_delta_dac=max_delta_dac,
        )


@pytest.mark.parametrize(
    ("dac_min", "dac_max"),
    [
        (100.0, 100.0),
        (101.0, 100.0),
    ],
)
def test_invalid_output_limits_are_rejected(
    dac_min: float,
    dac_max: float,
) -> None:
    limiter = SafeDacRateLimiter()

    with pytest.raises(
        ValueError,
        match="dac_min must be less than dac_max",
    ):
        run_cycle(
            limiter,
            dac_input=1000.0,
            dac_min=dac_min,
            dac_max=dac_max,
        )

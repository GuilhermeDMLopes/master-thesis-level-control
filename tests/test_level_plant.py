from __future__ import annotations

import pytest

from simulation.level_plant import (
    LevelPlant,
    LevelPlantConfig,
)


def test_initial_state_uses_engineering_and_raw_units() -> None:
    plant = LevelPlant()

    assert plant.level_cm == pytest.approx(10.0)
    assert plant.level_raw == pytest.approx(10000.0)


def test_disabled_pump_ignores_the_dac_command() -> None:
    plant = LevelPlant()

    result = plant.update(
        enable=False,
        dac=32000,
    )

    assert result.applied_dac == 32000
    assert result.normalized_dac == pytest.approx(0.0)
    assert result.inflow_cm_per_s == pytest.approx(0.0)
    assert result.outflow_cm_per_s == pytest.approx(0.25)
    assert result.level_cm == pytest.approx(9.975)


def test_enabled_full_scale_command_increases_the_level() -> None:
    plant = LevelPlant()

    result = plant.update(
        enable=True,
        dac=32000,
    )

    assert result.normalized_dac == pytest.approx(1.0)
    assert result.inflow_cm_per_s == pytest.approx(1.0)
    assert result.outflow_cm_per_s == pytest.approx(0.25)
    assert result.net_flow_cm_per_s == pytest.approx(0.75)
    assert result.level_cm == pytest.approx(10.075)


def test_intermediate_dac_uses_explicit_euler_integration() -> None:
    plant = LevelPlant()

    result = plant.update(
        enable=True,
        dac=16000,
    )

    assert result.normalized_dac == pytest.approx(0.5)
    assert result.net_flow_cm_per_s == pytest.approx(0.25)
    assert result.level_cm == pytest.approx(10.025)
    assert result.level_raw == pytest.approx(10025.0)


def test_dac_command_is_clamped_to_the_configured_range() -> None:
    plant = LevelPlant()

    upper = plant.update(
        enable=True,
        dac=50000,
    )
    lower = plant.update(
        enable=True,
        dac=-100,
    )

    assert upper.applied_dac == 32000
    assert upper.normalized_dac == pytest.approx(1.0)
    assert lower.applied_dac == 0
    assert lower.normalized_dac == pytest.approx(0.0)


def test_level_is_clamped_at_the_upper_physical_limit() -> None:
    config = LevelPlantConfig(
        initial_level_cm=29.99,
        maximum_level_cm=30.0,
        maximum_inflow_cm_per_s=10.0,
        drain_coefficient_per_s=0.0,
    )
    plant = LevelPlant(config)

    result = plant.update(
        enable=True,
        dac=32000,
    )

    assert result.level_cm == pytest.approx(30.0)
    assert result.upper_limit_active is True
    assert result.lower_limit_active is False


def test_level_is_clamped_at_the_lower_physical_limit() -> None:
    config = LevelPlantConfig(
        initial_level_cm=0.01,
        drain_coefficient_per_s=20.0,
    )
    plant = LevelPlant(config)

    result = plant.update(
        enable=False,
        dac=0,
    )

    assert result.level_cm == pytest.approx(0.0)
    assert result.lower_limit_active is True
    assert result.upper_limit_active is False


def test_reset_restores_the_initial_or_requested_level() -> None:
    plant = LevelPlant()

    plant.update(
        enable=True,
        dac=32000,
    )
    plant.reset()
    assert plant.level_cm == pytest.approx(10.0)

    plant.reset(15.0)
    assert plant.level_cm == pytest.approx(15.0)
    assert plant.level_raw == pytest.approx(15000.0)


def test_invalid_update_sampling_time_is_rejected() -> None:
    plant = LevelPlant()

    with pytest.raises(
        ValueError,
        match="sampling_time_s must be greater than zero",
    ):
        plant.update(
            enable=True,
            dac=1000,
            sampling_time_s=0.0,
        )


@pytest.mark.parametrize(
    "config, message",
    [
        (
            LevelPlantConfig(sampling_time_s=0.0),
            "sampling_time_s must be greater than zero",
        ),
        (
            LevelPlantConfig(
                minimum_level_cm=10.0,
                maximum_level_cm=10.0,
            ),
            "minimum_level_cm must be less than maximum_level_cm",
        ),
        (
            LevelPlantConfig(initial_level_cm=40.0),
            "initial_level_cm must be within the configured limits",
        ),
        (
            LevelPlantConfig(level_scale=0.0),
            "level_scale must be greater than zero",
        ),
        (
            LevelPlantConfig(dac_min=32000, dac_max=32000),
            "dac_min must be less than dac_max",
        ),
        (
            LevelPlantConfig(maximum_inflow_cm_per_s=-1.0),
            "maximum_inflow_cm_per_s must not be negative",
        ),
        (
            LevelPlantConfig(drain_coefficient_per_s=-0.1),
            "drain_coefficient_per_s must not be negative",
        ),
    ],
)
def test_invalid_configuration_is_rejected(
    config: LevelPlantConfig,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        LevelPlant(config)

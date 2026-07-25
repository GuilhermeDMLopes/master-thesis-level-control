from __future__ import annotations

import pytest

from simulation.br_plc_simulator import (
    BR_DAC_NODE_IDENTIFIER,
    BR_ENABLE_NODE_IDENTIFIER,
    BR_LEVEL_NODE_IDENTIFIER,
    DEFAULT_SIMULATION_MODE,
    SIMULATION_MODE_DETERMINISTIC,
    SIMULATION_MODE_DYNAMIC,
    calculate_simulated_level,
    normalize_simulation_mode,
    parse_arguments,
)
from simulation.level_plant import LevelPlant


def test_default_mode_preserves_the_deterministic_baseline() -> None:
    assert DEFAULT_SIMULATION_MODE == SIMULATION_MODE_DETERMINISTIC
    assert normalize_simulation_mode(None) == SIMULATION_MODE_DETERMINISTIC
    assert parse_arguments([]).mode == SIMULATION_MODE_DETERMINISTIC


def test_mode_names_are_normalized() -> None:
    assert normalize_simulation_mode(" DYNAMIC ") == SIMULATION_MODE_DYNAMIC
    assert (
        normalize_simulation_mode("DETERMINISTIC")
        == SIMULATION_MODE_DETERMINISTIC
    )


def test_invalid_mode_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported simulation mode"):
        normalize_simulation_mode("unknown")


def test_command_line_can_select_dynamic_mode() -> None:
    arguments = parse_arguments(["--mode", "dynamic"])

    assert arguments.mode == SIMULATION_MODE_DYNAMIC


def test_deterministic_mode_ignores_commands() -> None:
    level_raw, result = calculate_simulated_level(
        mode=SIMULATION_MODE_DETERMINISTIC,
        elapsed_s=15.0,
        enable=True,
        dac=32000,
        plant=None,
    )

    assert level_raw == pytest.approx(12000.0)
    assert result is None


def test_dynamic_mode_uses_enable_and_dac_commands() -> None:
    plant = LevelPlant()

    level_raw, result = calculate_simulated_level(
        mode=SIMULATION_MODE_DYNAMIC,
        elapsed_s=0.0,
        enable=True,
        dac=32000,
        plant=plant,
    )

    assert result is not None
    assert result.level_cm == pytest.approx(10.075)
    assert level_raw == pytest.approx(10075.0)


def test_dynamic_mode_drains_when_enable_is_false() -> None:
    plant = LevelPlant()

    level_raw, result = calculate_simulated_level(
        mode=SIMULATION_MODE_DYNAMIC,
        elapsed_s=0.0,
        enable=False,
        dac=32000,
        plant=plant,
    )

    assert result is not None
    assert result.inflow_cm_per_s == pytest.approx(0.0)
    assert result.level_cm == pytest.approx(9.975)
    assert level_raw == pytest.approx(9975.0)


def test_dynamic_mode_requires_a_plant_instance() -> None:
    with pytest.raises(
        ValueError,
        match="LevelPlant instance is required",
    ):
        calculate_simulated_level(
            mode=SIMULATION_MODE_DYNAMIC,
            elapsed_s=0.0,
            enable=True,
            dac=1000,
            plant=None,
        )


def test_br_node_identifiers_remain_unchanged() -> None:
    assert BR_LEVEL_NODE_IDENTIFIER == "::Program:Nivel"
    assert BR_ENABLE_NODE_IDENTIFIER == "::Program:Enable"
    assert BR_DAC_NODE_IDENTIFIER == "::Program:DAC"

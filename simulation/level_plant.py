from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LevelPlantConfig:
    """Configuration for the provisional offline level-plant model."""

    sampling_time_s: float = 0.1
    initial_level_cm: float = 10.0
    minimum_level_cm: float = 0.0
    maximum_level_cm: float = 30.0
    level_scale: float = 1000.0
    dac_min: int = 0
    dac_max: int = 32000
    maximum_inflow_cm_per_s: float = 1.0
    drain_coefficient_per_s: float = 0.025

    def validate(self) -> None:
        """Reject configurations that cannot define a valid plant."""

        if self.sampling_time_s <= 0.0:
            raise ValueError(
                "sampling_time_s must be greater than zero"
            )

        if self.minimum_level_cm >= self.maximum_level_cm:
            raise ValueError(
                "minimum_level_cm must be less than maximum_level_cm"
            )

        if not (
            self.minimum_level_cm
            <= self.initial_level_cm
            <= self.maximum_level_cm
        ):
            raise ValueError(
                "initial_level_cm must be within the configured limits"
            )

        if self.level_scale <= 0.0:
            raise ValueError(
                "level_scale must be greater than zero"
            )

        if self.dac_min >= self.dac_max:
            raise ValueError(
                "dac_min must be less than dac_max"
            )

        if self.maximum_inflow_cm_per_s < 0.0:
            raise ValueError(
                "maximum_inflow_cm_per_s must not be negative"
            )

        if self.drain_coefficient_per_s < 0.0:
            raise ValueError(
                "drain_coefficient_per_s must not be negative"
            )


@dataclass(frozen=True)
class LevelPlantResult:
    """State and diagnostics produced by one plant integration step."""

    level_cm: float
    level_raw: float
    applied_dac: int
    normalized_dac: float
    inflow_cm_per_s: float
    outflow_cm_per_s: float
    net_flow_cm_per_s: float
    lower_limit_active: bool
    upper_limit_active: bool


class LevelPlant:
    """
    Stateful first-order level plant for offline controller validation.

    The provisional model uses explicit Euler integration:

        level[k + 1] = clamp(
            level[k]
            + sampling_time_s * (
                inflow(dac, enable)
                - outflow(level[k])
            ),
            minimum_level_cm,
            maximum_level_cm,
        )

    Inflow is proportional to the clamped DAC command when Enable is true.
    Outflow is proportional to the level above the configured minimum.
    Parameters are deliberately simple and must later be replaced by values
    identified from the physical plant.
    """

    def __init__(
        self,
        config: LevelPlantConfig | None = None,
    ) -> None:
        self.config = config or LevelPlantConfig()
        self.config.validate()
        self._level_cm = float(self.config.initial_level_cm)

    @property
    def level_cm(self) -> float:
        """Return the current simulated level in centimeters."""

        return self._level_cm

    @property
    def level_raw(self) -> float:
        """Return the current level using the B&R raw-value convention."""

        return self._level_cm * self.config.level_scale

    def reset(self, level_cm: float | None = None) -> None:
        """Reset the plant to the initial or explicitly requested level."""

        target_level = (
            self.config.initial_level_cm
            if level_cm is None
            else float(level_cm)
        )

        if not (
            self.config.minimum_level_cm
            <= target_level
            <= self.config.maximum_level_cm
        ):
            raise ValueError(
                "reset level must be within the configured limits"
            )

        self._level_cm = target_level

    def update(
        self,
        *,
        enable: bool,
        dac: int | float,
        sampling_time_s: float | None = None,
    ) -> LevelPlantResult:
        """Advance the plant by one integration step."""

        step_time_s = (
            self.config.sampling_time_s
            if sampling_time_s is None
            else float(sampling_time_s)
        )

        if step_time_s <= 0.0:
            raise ValueError(
                "sampling_time_s must be greater than zero"
            )

        applied_dac = int(
            min(
                max(int(dac), self.config.dac_min),
                self.config.dac_max,
            )
        )

        normalized_dac = (
            (applied_dac - self.config.dac_min)
            / (self.config.dac_max - self.config.dac_min)
        )

        if not bool(enable):
            normalized_dac = 0.0

        inflow_cm_per_s = (
            self.config.maximum_inflow_cm_per_s
            * normalized_dac
        )

        level_above_minimum_cm = max(
            self._level_cm - self.config.minimum_level_cm,
            0.0,
        )
        outflow_cm_per_s = (
            self.config.drain_coefficient_per_s
            * level_above_minimum_cm
        )
        net_flow_cm_per_s = (
            inflow_cm_per_s
            - outflow_cm_per_s
        )

        unconstrained_level_cm = (
            self._level_cm
            + step_time_s * net_flow_cm_per_s
        )
        next_level_cm = min(
            max(
                unconstrained_level_cm,
                self.config.minimum_level_cm,
            ),
            self.config.maximum_level_cm,
        )

        lower_limit_active = (
            unconstrained_level_cm < self.config.minimum_level_cm
        )
        upper_limit_active = (
            unconstrained_level_cm > self.config.maximum_level_cm
        )

        self._level_cm = next_level_cm

        return LevelPlantResult(
            level_cm=self._level_cm,
            level_raw=self.level_raw,
            applied_dac=applied_dac,
            normalized_dac=normalized_dac,
            inflow_cm_per_s=inflow_cm_per_s,
            outflow_cm_per_s=outflow_cm_per_s,
            net_flow_cm_per_s=net_flow_cm_per_s,
            lower_limit_active=lower_limit_active,
            upper_limit_active=upper_limit_active,
        )

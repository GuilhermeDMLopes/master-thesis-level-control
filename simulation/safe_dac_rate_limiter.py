from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SafeDacRateLimiterResult:
    """Outputs produced by one safe DAC rate-limiter cycle."""

    dac_output: float
    limited: bool
    initialized: bool
    reset_active: bool
    configuration_valid: bool = True


class SafeDacRateLimiter:
    """
    Stateful DAC rate limiter with deterministic startup and reset.

    The first valid cycle returns the bounded initial DAC value without moving
    toward the requested input. Later cycles move toward the bounded request by
    no more than the configured maximum delta.
    """

    def __init__(self) -> None:
        self._dac_output = 0.0
        self._initialized = False

    @property
    def dac_output(self) -> float:
        """Return the stored DAC output."""

        return self._dac_output

    @property
    def initialized(self) -> bool:
        """Return whether a valid initialization or reset has occurred."""

        return self._initialized

    def update(
        self,
        *,
        dac_input: float,
        max_delta_dac: float,
        dac_min: float,
        dac_max: float,
        initial_dac: float = 0.0,
        reset: bool = False,
    ) -> SafeDacRateLimiterResult:
        """Execute one limiter cycle."""

        self._validate_configuration(
            max_delta_dac=max_delta_dac,
            dac_min=dac_min,
            dac_max=dac_max,
        )

        numeric_input = float(dac_input)
        bounded_input = self._clamp(
            numeric_input,
            minimum=float(dac_min),
            maximum=float(dac_max),
        )
        bounded_initial = self._clamp(
            float(initial_dac),
            minimum=float(dac_min),
            maximum=float(dac_max),
        )

        if reset or not self._initialized:
            self._dac_output = bounded_initial
            self._initialized = True

            return SafeDacRateLimiterResult(
                dac_output=self._dac_output,
                limited=(self._dac_output != numeric_input),
                initialized=True,
                reset_active=bool(reset),
            )

        delta = bounded_input - self._dac_output
        limited_delta = self._clamp(
            delta,
            minimum=-float(max_delta_dac),
            maximum=float(max_delta_dac),
        )

        self._dac_output = self._clamp(
            self._dac_output + limited_delta,
            minimum=float(dac_min),
            maximum=float(dac_max),
        )

        return SafeDacRateLimiterResult(
            dac_output=self._dac_output,
            limited=(self._dac_output != numeric_input),
            initialized=True,
            reset_active=False,
        )

    @staticmethod
    def _validate_configuration(
        *,
        max_delta_dac: float,
        dac_min: float,
        dac_max: float,
    ) -> None:
        if float(max_delta_dac) <= 0.0:
            raise ValueError(
                "max_delta_dac must be greater than zero"
            )

        if float(dac_min) >= float(dac_max):
            raise ValueError(
                "dac_min must be less than dac_max"
            )

    @staticmethod
    def _clamp(
        value: float,
        *,
        minimum: float,
        maximum: float,
    ) -> float:
        return min(max(value, minimum), maximum)

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PIControllerResult:
    """Outputs and diagnostics produced by one PI controller cycle."""

    output: float
    error: float
    proportional_term: float
    integral_term: float
    unsaturated_output: float
    saturated: bool
    manual_active: bool
    reset_active: bool


class PILevelController:
    """
    Stateful positional PI controller with conditional anti-windup.

    The integral state is stored directly as its contribution to the controller
    output. While manual mode is active, the integral term tracks the clamped
    manual output. The first automatic cycle after manual mode does not
    integrate, which provides a bumpless transfer when the process conditions
    have not changed between cycles.
    """

    def __init__(self) -> None:
        self._integral_term = 0.0
        self._manual_was_active = False

    @property
    def integral_term(self) -> float:
        """Return the current integral contribution."""

        return self._integral_term

    def reset_state(self) -> None:
        """Clear all internal controller state."""

        self._integral_term = 0.0
        self._manual_was_active = False

    def update(
        self,
        *,
        process_variable: float,
        setpoint: float,
        proportional_gain: float,
        integral_gain: float,
        sampling_time_s: float,
        output_min: float,
        output_max: float,
        manual: bool = False,
        manual_output: float = 0.0,
        reset: bool = False,
    ) -> PIControllerResult:
        """Execute one controller cycle and return output diagnostics."""

        self._validate_configuration(
            sampling_time_s=sampling_time_s,
            output_min=output_min,
            output_max=output_max,
        )

        error = float(setpoint) - float(process_variable)
        proportional_term = float(proportional_gain) * error

        if reset:
            self.reset_state()
            output = self._clamp(
                0.0,
                output_min=output_min,
                output_max=output_max,
            )

            return PIControllerResult(
                output=output,
                error=error,
                proportional_term=proportional_term,
                integral_term=0.0,
                unsaturated_output=output,
                saturated=False,
                manual_active=bool(manual),
                reset_active=True,
            )

        if manual:
            output = self._clamp(
                float(manual_output),
                output_min=output_min,
                output_max=output_max,
            )

            # Track the manual output so automatic mode starts from the same
            # controller output when the error has not changed.
            self._integral_term = output - proportional_term
            self._manual_was_active = True

            return PIControllerResult(
                output=output,
                error=error,
                proportional_term=proportional_term,
                integral_term=self._integral_term,
                unsaturated_output=output,
                saturated=(output != float(manual_output)),
                manual_active=True,
                reset_active=False,
            )

        if self._manual_was_active:
            # The integral term was aligned with the manual output during the
            # previous cycle. Skip one integration step for bumpless transfer.
            self._manual_was_active = False
        else:
            integral_increment = (
                float(integral_gain)
                * error
                * float(sampling_time_s)
            )
            candidate_integral = (
                self._integral_term
                + integral_increment
            )
            candidate_unsaturated = (
                proportional_term
                + candidate_integral
            )

            integration_worsens_upper_saturation = (
                candidate_unsaturated > output_max
                and integral_increment > 0.0
            )
            integration_worsens_lower_saturation = (
                candidate_unsaturated < output_min
                and integral_increment < 0.0
            )

            if not (
                integration_worsens_upper_saturation
                or integration_worsens_lower_saturation
            ):
                self._integral_term = candidate_integral

        unsaturated_output = (
            proportional_term
            + self._integral_term
        )
        output = self._clamp(
            unsaturated_output,
            output_min=output_min,
            output_max=output_max,
        )

        return PIControllerResult(
            output=output,
            error=error,
            proportional_term=proportional_term,
            integral_term=self._integral_term,
            unsaturated_output=unsaturated_output,
            saturated=(output != unsaturated_output),
            manual_active=False,
            reset_active=False,
        )

    @staticmethod
    def _validate_configuration(
        *,
        sampling_time_s: float,
        output_min: float,
        output_max: float,
    ) -> None:
        if sampling_time_s <= 0.0:
            raise ValueError(
                "sampling_time_s must be greater than zero"
            )

        if output_min >= output_max:
            raise ValueError(
                "output_min must be less than output_max"
            )

    @staticmethod
    def _clamp(
        value: float,
        *,
        output_min: float,
        output_max: float,
    ) -> float:
        return min(
            max(value, output_min),
            output_max,
        )

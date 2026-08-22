# Wide-range operating-envelope validation plan

## Why this plan is necessary

The tank overflow reference is approximately 40 cm and the declared operational
safe maximum is 25 cm. The real-plant MPC work performed so far has remained in
a deliberately conservative commissioning region, with observed physical water
levels no higher than approximately 1.5 cm.

That is defensible for:

- communication commissioning;
- zero-output safety validation;
- first PI/MPC closed-loop commissioning;
- local pump/input-map identification near the actuator threshold.

It is **not sufficient by itself** for a dissertation claim that the controller
has been validated over the useful operating range of the physical tank.

The final experimental program must therefore include a second, wider-range
validation phase.

## Important distinction

The current 11600..11900 DAC identification is not intended to represent the
full tank range.

Its purpose is to identify the local actuator/input nonlinearity that caused the
MPC model to treat approximately 11750 DAC as a structural boundary.

The final tank-range validation is a separate experiment.

## Do not increase raw limits blindly

The observed relation between raw sensor values and physical centimetres is not
yet sufficiently calibrated over the tank height.

Therefore the correct progression is:

1. establish an empirical physical-height calibration;
2. map the corresponding raw-count regions;
3. validate/refit the model over those physical regions;
4. only then define larger raw safety/operating limits.

A larger raw ceiling chosen before this calibration would be difficult to
defend experimentally.

## Stage 1 - physical sensor calibration

Planned nominal physical-height points:

- 0 cm;
- 2 cm;
- 5 cm;
- 10 cm;
- 15 cm.

Optional extension:

- 20 cm, only after review of the lower tiers.

The declared operational maximum remains 25 cm. The 40 cm value is the overflow
geometry reference, not an experimental target.

At each physical point record:

- manually measured physical height;
- steady raw-level distribution;
- Median9;
- zero-output baseline;
- watchdog state;
- relevant hydraulic condition.

The result should be an empirical raw-to-cm calibration with uncertainty, not a
single assumed scale factor.

## Stage 2 - model validation across level

After physical calibration:

- check whether the local actuator/input map changes with operating level;
- validate the Hammerstein input map;
- test whether process gain changes materially with level;
- test whether the identified delay/time constant remain adequate;
- refit only when supported by data.

## Stage 3 - controller validation across operating range

After the model is physically calibrated, perform controller tests at multiple
physical references.

Initial target set for final comparison:

- approximately 5 cm;
- approximately 10 cm;
- approximately 15 cm.

An optional approximately 20 cm validation point may be considered only after
the lower levels are safe and well modelled.

The PI and MPC comparisons should use, as far as practical:

- the same calibrated physical setpoints;
- comparable initial conditions;
- comparable experiment duration;
- the same physical safety criteria.

Report:

- overshoot;
- settling behavior;
- MAE;
- RMSE;
- IAE;
- actuator total variation;
- maximum DAC;
- physical safety margin.

## Dissertation framing

The low-level experiments should be described as commissioning, safety
validation, and local model identification.

The later multi-level tests should support the stronger statement that the
controller was validated over a physically measured operating range.

Until those tests exist, do not claim full-range tank validation.

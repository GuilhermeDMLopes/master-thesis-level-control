# MPC_REAL_RAW_SAFE_V3H â€” additive state/process-disturbance MPC

## Scope

`MPC_MOVE_BLOCKED_NMPC_V3H` is an additive 4diac translation of the accepted
Python V3H reference. It is cloned from the validated V3E implementation.

This stage is source-level/offline only. It does not build or start FORTE and
does not authorize real actuation.

## Preserved V3E contract

V3H preserves:

- 500 ms controller period;
- 9.0 s transport delay;
- 18-sample AppliedDAC history;
- 60-step / 30 s prediction horizon;
- exact 13 canonical V3 target candidates;
- exporter-safe single outer candidate loop plus single inner prediction loop;
- 0..12000 DAC envelope;
- 750 DAC/update move limit;
- 1100 raw predicted soft limit;
- 1400 raw predicted hard limit;
- 1500 raw measured hard limit;
- default `ENABLE_REQUEST = FALSE`;
- existing fail-closed behavior and trip latch;
- `INPUT_BIAS_ESTIMATE_DAC = 0.0`.

V1, V2, V3, V3E and the rejected Python V3G artifacts remain unchanged.

## V3H disturbance estimator

The estimator runs only in the healthy active branch after the 18-sample delay
history is ready.

The canonical one-step prediction uses:

- previous `PV_MODEL`;
- oldest real AppliedDAC history sample `h00`;
- the exact existing V3E Hammerstein/dead-zone static nonlinearity;
- the exact V3 state coefficients.

Innovation:

`innovation[k] = PV_MODEL[k] - yhat_canonical[k|k-1]`

EWMA:

`d_hat[k] = 0.9*d_hat[k-1] + 0.1*innovation[k]`

Numerical clamp:

`-100 <= d_hat <= +100 raw/controller-step`

The estimator state is cleared by `RESET_REQUEST` and while
`ENABLE_REQUEST = FALSE`, preventing a stale learned disturbance from being
reused across commissioning enables.

## Prediction augmentation

The V3E state transition is preserved and receives one additive term:

`predicted_y := f_V3(predicted_y, delayed_u) + disturbance_hat_internal`

The estimate is held constant over all 60 steps of one optimizer evaluation,
matching the accepted Python V3H prediction contract.

## Why the 96-DAC command change is meaningful

The identified Hammerstein input has a dead-zone at approximately 11750 DAC.
The canonical equilibrium target is approximately 11845.63 DAC.

Therefore a command move from about 11846 to 11750 is only about 96 DAC in raw
actuator coordinates, but it removes essentially all modeled positive input
effect.

The preserved Python real-trace replay produced:

- 81.4% of post-SP high-DAC points at or below the dead-zone;
- 81.4% with at least 90% effective-input reduction;
- 0% premature dead-zone action in the <=400-raw screen;
- final equivalent learned steady shift about +367.3 raw;
- independent long-horizon model error about +367.5 raw.

## Additive system artifacts

This stage creates:

- FB type `MPC_MOVE_BLOCKED_NMPC_V3H`;
- Application `MPC_REAL_RAW_SAFE_V3H`;
- Resource `ResRealRawMPCV3H`;
- 12 mappings cloned from V3E.

The existing V3E artifacts are not modified semantically.

## Next gates

Before any real V3H operation:

1. refresh/reopen the project in Eclipse 4diac;
2. validate V3H FB parser and application/resource layout;
3. checkpoint the source;
4. export only `MPC_MOVE_BLOCKED_NMPC_V3H` with FORTE 1.x NG;
5. verify generated nested-loop C++;
6. build an isolated FORTE with the known Win32/open62541 settings;
7. perform offline type-availability smoke;
8. perform protected zero-output deployment;
9. only then consider one bounded real V3H experiment.

Real V3H actuation is not authorized by this source-translation stage.

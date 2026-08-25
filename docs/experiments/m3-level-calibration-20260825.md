# M3 operational level calibration - 2026-08-25

## Result

- M3 status: CLOSED_WITH_DYNAMIC_CAPTURE_LIMITATION
- Physical calibration range: 0 to 13 cm
- Requested nominal grid: 0, 2, 5, 10 and 15 cm
- Recorded real grid: 0, 3, 5, 8.5 and 13 cm
- Existing scale evaluated: level_cm = raw / 1000
- Controller scale changed: NO
- Real actuation complete: YES
- Final PLC zero output: YES for every accepted plateau

## Accepted points

| Physical height (cm) | Raw median | Raw mean | Applied DAC | raw/1000 (cm) | Nominal error (cm) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.0 | 257 | 259.429 | 0 | 0.257 | +0.257 |
| 3.0 | 1776 | 1747.667 | 16000 | 1.776 | -1.224 |
| 5.0 | 4465 | 4399.846 | 16000 | 4.465 | -0.535 |
| 8.5 | 8503 | 8506.605 | 16000 | 8.503 | +0.003 |
| 13.0 | 13791 | 13720.763 | 16000 | 13.791 | +0.791 |

The raw/1000 scale has RMSE 0,704 cm across all five points and RMSE 0,551 cm across the 5 to 13 cm control range. This is adequate for the remaining comparative experiments and does not justify another controller-scale change at this stage.

## Physical interpretation

The measurement tank has a permanent gravity drain at the bottom center. Water does not remain at a calibration height after the pump is turned off. The accepted positive points were therefore measured during the final capture interval while DAC 16000 remained applied.

The 3 cm capture is the largest deviation from raw/1000. It was collected during a fast lower-range transient and must not be treated as a static equilibrium point. The empty-tank baseline also varies with noise and observed offset. These effects are documented rather than expanded into another physical identification campaign.

## Decision

Retain the existing raw/1000 level scale for the remaining project work. Treat 0 to approximately 3 cm as a bottom/drain transition region and avoid claiming exact static calibration there. Use the preserved measured pairs for dissertation reporting and sensitivity discussion.

## Executor change

The only executor change extends the permitted hold duration from 20 to 90 seconds. The temporary DAC ceiling remains 16000, and zero-output verification, soft stop, gateway contract and physical confirmation remain unchanged.

## Evidence

The accepted point summary is stored in `data/sample/m3-level-calibration-20260825/calibration-points.csv`. Preserved source paths and SHA256 hashes are stored in `results/m3-level-calibration-20260825/summary.json`.

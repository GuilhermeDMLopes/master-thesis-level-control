# Final PI versus MPC V4 real-plant comparison

## Experimental basis

The comparison uses the final bounded 180 s runs at the same nominal physical
target of 15 cm, raw target of 17000, and actuator envelope of 0..16000 DAC.
The MPC V4 experiment was completed on 2026-08-29 and the final retuned PI
experiment on 2026-09-01. Both runs used the independent supervisor, healthy
PLC watchdog feedback, automatic FORTE termination, and verified zero output.

The manual physical observation is authoritative because the raw-count zero
offset varied between sessions. Raw metrics are retained for reproducibility
and for comparing the trajectories recorded by the common supervisor.

## Final quantitative comparison

| Metric | MPC V4 | PI, KP=4.0 and KI=0.10 |
|---|---:|---:|
| Physical final height | 15.0 cm | 14.7 cm |
| Active duration | 179.969 s | 179.937 s |
| 10%-90% rise time | 90.656 s | 119.610 s |
| First 90% target | 109.906 s | 138.406 s |
| Raw settling time, +/-5% | 122.031 s | not reached |
| Raw settling time, +/-2% | 177.344 s | not reached |
| Maximum median-9 level | 17086 raw | 16148 raw |
| Overshoot | 0.506% | 0.000% |
| IAE | 1091232.93 raw.s | 1124928.32 raw.s |
| ISE | 12700711917.84 raw^2.s | 12007192805.98 raw^2.s |
| Last-30-s mean level | 16848.45 raw | 15867.77 raw |
| Last-30-s mean error | 151.55 raw (0.891%) | 1132.23 raw (6.660%) |
| Last-30-s standard deviation | 107.59 raw | 187.41 raw |
| Last-30-s mean applied DAC | 14092.91 | 14188.76 |
| Applied-DAC total variation | 25800 | 30169 |
| Maximum applied DAC | 16000 | 16000 |
| Watchdog healthy throughout | yes | yes |
| Final zero output independently verified | yes | yes |

The PI IAE was 3.09% higher than the MPC
IAE, while its ISE was 5.46%
lower. This mixed integral-error result reflects the PI's faster early fill and
the MPC's substantially better final tracking. During the last 30 s, the PI
mean raw error was 7.47 times the
MPC error. The PI used 16.93%
more applied-DAC total variation.

## PI retuning evidence

The first matched PI attempt retained `KI=0.02` and reached approximately 6 cm.
Its maximum median-9 level was 6257 raw and its
last-30-s mean level was 5819.83 raw. The single
justified retuning to `KI=0.10` brought the physical level to 14.7 cm while the
independent rate limiter continued to govern the initial actuator ramp. No
additional PI tuning campaign was required.

## Interpretation

The PI provided a simple, stable baseline and reached the physical target with
approximately 0.3 cm absolute error and no overshoot. The MPC V4 response was
slower during part of the rise and had approximately 0.506% raw overshoot, but
it entered and remained within the raw tracking bands and achieved much lower
final error and variability. Both controllers converged to a similar final DAC
region near 14000, consistent with balancing the continuous bottom drain.

The result supports an engineering conclusion that the MPC V4 improved final
tracking and explicit constraint handling in this experiment. It does not
support a statistical superiority claim because only one accepted final run
per controller was executed and the raw-to-centimetre calibration varied
between sessions.

## Safety and closure

Both final runs completed with `ACTIVE_WINDOW_COMPLETE`. The watchdog remained
healthy, the independent supervisor terminated FORTE, and post-shutdown files
confirmed `Enable=FALSE` and `DAC=0` at both gateway and PLC. The practical
laboratory stage is closed; no additional real-plant experiment is required.

## Reproducibility

- MPC evidence: `data/sample/mpc-v4-target17000-20260829/`;
- final PI evidence: `data/sample/pi-v4-matched-20260901/`;
- first PI attempt: `data/sample/pi-v4-matched-first-attempt-20260829/`;
- generated metrics: `data/sample/pi-vs-mpc-v4-final-20260901/metrics.json`;
- generated figures: `docs/figures/pi-vs-mpc-v4-final-20260901/`;
- analysis script: `scripts/analyze_pi_mpc_v4_final.py`.

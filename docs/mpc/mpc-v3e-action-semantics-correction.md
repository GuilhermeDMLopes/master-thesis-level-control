# MPC V3E action-semantics correction

Date: 2026-08-22

## Correction

The previously committed classification

`DISCONNECTED_CANDIDATE_ACTION_GRAPH_CONFIRMED`

is **superseded**.

The earlier graph treated the 13 values as if a candidate target had to be
within 750 DAC of the current AppliedDAC to be selectable. That is not how the
implemented V3/V3E controller works.

Both the Python reference and 4diac implementation use the candidate as a
**target** and rate-limit the command toward it by at most 750 DAC per update.

For a target of zero starting from 11850 DAC, the implemented command semantics
produce this legal path:

`[11850.0, 11100.0, 10350.0, 9600.0, 8850.0, 8100.0, 7350.0, 6600.0, 5850.0, 5100.0, 4350.0, 3600.0, 2850.0, 2100.0, 1350.0, 600.0, 0.0]`

Thus zero is reachable in `16` updates, or
`8.0 s` at Ts=500 ms.

## Source-level implementation semantics

Python reference checks:

`{'prediction uses rate limit toward candidate target': True, 'final output uses rate limit toward best target': True}`

4diac V3E ST checks:

`{'prediction computes target error': True, 'prediction positive clamp': True, 'prediction negative clamp': True, 'prediction applies limited move': True, 'final command computes best-target error': True, 'final command applies limited move': True, 'zero target exists': True}`

The 4diac algorithm explicitly:

1. computes `delta_u := candidate_target - predicted_u`;
2. clamps `delta_u` to ??750;
3. applies `predicted_u := predicted_u + delta_u`;
4. after optimization, computes `delta_u := best_target - APPLIED_DAC`;
5. clamps again to ??750;
6. applies `command_candidate := APPLIED_DAC + delta_u`.

Therefore the 11500-DAC numerical gap between candidate *targets* does not
create a disconnected actuator command graph.

## Consequence for MPC V3F

The connected relative-action kernel committed in `4f49541` remains preserved
as an exploratory artifact, but its topology result is **not sufficient
justification** for translating it to 4diac/FORTE.

Do not implement V3F in 4diac from that premise alone.

## Real-trace optimizer-cost audit

The authoritative V3 objective/model, with the V3E 1100/1400/1500 safety
envelope, was evaluated on representative real V3E snapshots where Median9 was
above SP and AppliedDAC was in the high-DAC region.

Classification:

**MODEL_OBJECTIVE_PREFERS_HIGH_DAC_ON_REAL_HIGH_PV_SNAPSHOTS**

Representative snapshots:

- t=22.672s, Median9=461.0, AppliedDAC=11846.0, best target=11845.626677302696, zero cost=3959125.7083735364, eq cost=8160.604901968801, zero first command=11096.0
- t=29.516s, Median9=553.0, AppliedDAC=11846.0, best target=11845.626677302696, zero cost=4099661.3750390457, eq cost=229549.59367792628, zero first command=11096.0
- t=36.672s, Median9=716.0, AppliedDAC=11846.0, best target=11845.626677302696, zero cost=5203128.6848123325, eq cost=1517928.4675122388, zero first command=11096.0
- t=42.656s, Median9=757.0, AppliedDAC=11846.0, best target=11845.626677302696, zero cost=5659155.779775359, eq cost=2020467.0601838655, zero first command=11096.0
- t=48.375s, Median9=696.0, AppliedDAC=11846.0, best target=11845.626677302696, zero cost=5006708.336749844, eq cost=1298819.5839821422, zero first command=11096.0
- t=54.062s, Median9=777.0, AppliedDAC=11846.0, best target=11845.626677302696, zero cost=5907639.914603633, eq cost=2291639.7304797512, zero first command=11096.0
- t=60.047s, Median9=818.0, AppliedDAC=11846.0, best target=11845.626677302696, zero cost=6470397.772436523, eq cost=2900909.086021243, zero first command=11096.0

Next diagnostic focus:

**objective/model/committed-delay prediction; do not change candidate topology first**

## Baseline mismatch

The observed pre-active baseline around 227 raw versus the model baseline 288
raw remains a genuine model mismatch. A 227-raw baseline sensitivity calculation
is included in the audit JSON, but no model parameter is changed by this stage.

## Decision

- previous disconnected-candidate diagnosis: **SUPERSEDED**;
- V3F relative-action kernel: **preserved but not authorized for translation**;
- raw ceiling increase: **NO**;
- new real run: **NO**;
- next step: follow the optimizer-cost classification produced by this audit.

# Plant Identification Physical-Limit Review

## Status

This document is an offline evidence inventory and approval worksheet. It does not define physical limits, approve excitation values, or authorize a real-plant identification run.

## Validated PI baseline observations

```text
Source: data/sample/real-raw-pi-v1-monitor.csv
SHA256: 197D0F0113564EACC40D16325CF1760008C595CE815300DA8BE5841CAB060E07
Rows: 427
Duration: 180.39100000000002 s
Observed raw-level minimum: 136.0
Observed raw-level maximum: 787.0
Observed raw-level median: 411.0
Maximum observed level phase: AUTO_ACTIVE
Observed applied-DAC minimum: 0.0
Observed applied-DAC maximum: 12000.0
Observed applied-DAC median: 11187.0
Automatic rows: 167
```

These are observations from one PI commissioning run. They are not automatically valid as physical, operational, or safety limits. In particular, 787 raw counts is not an approved high-level trip, 12000 DAC counts is not an approved identification excitation, and 32000 is not automatically an approved experimental command.

## Evidence inventory summary

| Category | Matching lines | Files |
|---|---:|---:|
| Level calibration | 170 | 24 |
| Level limits | 190 | 17 |
| DAC limits | 743 | 61 |
| Pump threshold | 8 | 5 |
| Safety interlocks | 313 | 31 |

Keyword matches are review leads, not automatically authoritative values.

## Level-calibration evidence

| File | Line | Excerpt |
|---|---:|---|
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 171 | <FB Name="NivelScalePID" Type="F_DIV" Comment="" x="-21733.333333333336" y="-11466.666666666668"> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 184 | <FB Name="NivelScale" Type="F_DIV" Comment="" x="-31333.333333333336" y="-6133.333333333334"> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 235 | <FB Name="NivelScalePID_1" Type="F_DIV" Comment="" x="-37026.66666666667" y="-16160.0"> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 295 | <Connection Source="NivelTypePID.CNF" Destination="NivelScalePID.REQ" Comment="" dx1="133.33333333333334"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 296 | <Connection Source="NivelScalePID.CNF" Destination="PV_FILTERPID.REQ" Comment="" dx1="120.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 300 | <Connection Source="NivelType.CNF" Destination="NivelScale.REQ" Comment="" dx1="246.66666666666669"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 301 | <Connection Source="NivelScale.CNF" Destination="PV_FILTER.REQ" Comment="" dx1="253.33333333333334"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 308 | <Connection Source="NivelTypePID_1.CNF" Destination="NivelScalePID_1.REQ" Comment="" dx1="153.33333333333334"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 311 | <Connection Source="NivelScalePID_1.CNF" Destination="PV_FILTERPID_1.REQ" Comment="" dx1="86.66666666666667"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 352 | <Connection Source="NivelTypePID.OUT" Destination="NivelScalePID.IN1" Comment="" dx1="133.33333333333334"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 353 | <Connection Source="NivelScalePID.OUT" Destination="PV_FILTERPID.PV_IN" Comment="" dx1="120.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 357 | <Connection Source="NivelType.OUT" Destination="NivelScale.IN1" Comment="" dx1="180.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 358 | <Connection Source="NivelScale.OUT" Destination="PV_FILTER.PV_IN" Comment="" dx1="186.66666666666669"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 363 | <Connection Source="NivelScalePID_1.OUT" Destination="PV_FILTERPID_1.PV_IN" Comment="" dx1="86.66666666666667"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 366 | <Connection Source="NivelTypePID_1.OUT" Destination="NivelScalePID_1.IN1" Comment="" dx1="153.33333333333334"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 470 | <FB Name="OfflineLevelScale" Type="F_DIV" Comment="" x="133.33333333333334" y="1866.6666666666667"> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 512 | <Connection Source="OfflineLevelType.CNF" Destination="OfflineLevelScale.REQ" Comment="" dx1="80.0" dx2="80.0" dy="400.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 513 | <Connection Source="OfflineLevelScale.CNF" Destination="OfflinePVFilter.REQ" Comment="" dx1="80.0" dx2="80.0" dy="466.6666666666667"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 527 | <Connection Source="OfflineLevelType.OUT" Destination="OfflineLevelScale.IN1" Comment="" dx1="80.0" dx2="80.0" dy="400.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 528 | <Connection Source="OfflineLevelScale.OUT" Destination="OfflinePVFilter.PV_IN" Comment="" dx1="80.0" dx2="80.0" dy="466.6666666666667"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 554 | <FB Name="OfflineLevelScale" Type="F_DIV" Comment="" x="1600.0" y="2800.0"> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 594 | <Connection Source="OfflineLevelType.CNF" Destination="OfflineLevelScale.REQ" Comment="" dx1="80.0" dx2="80.0" dy="400.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 595 | <Connection Source="OfflineLevelScale.CNF" Destination="OfflinePVFilter.REQ" Comment="" dx1="80.0" dx2="80.0" dy="466.6666666666667"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 606 | <Connection Source="OfflineLevelScale.OUT" Destination="OfflinePVFilter.PV_IN" Comment="" dx1="80.0" dx2="80.0" dy="466.6666666666667"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 607 | <Connection Source="OfflineLevelType.OUT" Destination="OfflineLevelScale.IN1" Comment="" dx1="80.0" dx2="80.0" dy="400.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 619 | <Application Name="PI_REAL_RAW_SAFE" Comment="Real plant PI in raw counts with manual-zero startup, output bias, safe DAC limiting, and no automatic resource start"> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 621 | <FB Name="RawLevelRead" Type="SUBSCRIBE_1" Comment="Read raw level counts from the local gateway" x="1600.0" y="933.3333333333334"> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 625 | <FB Name="RawLevelType" Type="LREAL2LREAL" Comment="Preserve raw level counts as LREAL" x="1600.0" y="2000.0"> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 627 | <FB Name="RawPVFilter" Type="PV_FILTER" Comment="First-order filter for raw level counts" x="1600.0" y="3000.0"> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 631 | <FB Name="RawPI" Type="PI_LEVEL_CONTROLLER" Comment="Conservative PI controller in raw level counts and DAC deviation units" x="3200.0" y="933.3333333333334"> |

## Level-limit evidence

| File | Line | Excerpt |
|---|---:|---|
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 303 | <Connection Source="MPC_LEVEL.CNF" Destination="DAC_LIMITER.REQ" Comment="" dx1="533.3333333333334"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 360 | <Connection Source="MPC_LEVEL.DAC_OUT" Destination="DAC_LIMITER.DAC_IN" Comment="" dx1="440.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 645 | <FB Name="RawSafeDACLimiter" Type="SAFE_DAC_RATE_LIMITER" Comment="Final application-level DAC bounds and symmetric rate limit" x="3333.3333333333335" y="3333.3333333333335"> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 1047 | <FB Name="RawSafeDACLimiter" Type="SAFE_DAC_RATE_LIMITER" Comment="Final application-level DAC bounds and symmetric rate limit" x="3333.3333333333335" y="3333.3333333333335"> |
| `docs/control/safe-dac-rate-limiter-specification.md` | 167 | Reset is level-sensitive and deterministic. Repeated reset cycles keep the same |
| `docs/experiments/gateway-4diac-simulator-validation.md` | 354 | The current PLC simulator uses a deterministic level profile and does not yet represent the physical process dynamics. |
| `docs/experiments/gateway-reconnection-validation.md` | 150 | The exact level value depends on the deterministic simulator profile. The command and feedback values were the critical acceptance criteria. |
| `docs/experiments/open-loop-identification-protocol.md` | 38 | - an explicitly supplied maximum raw-level trip threshold; |
| `docs/experiments/open-loop-identification-protocol.md` | 66 | --initial-level-min-raw <APPROVED_INITIAL_MIN> ` |
| `docs/experiments/open-loop-identification-protocol.md` | 67 | --initial-level-max-raw <APPROVED_INITIAL_MAX> ` |
| `docs/experiments/open-loop-identification-protocol.md` | 68 | --maximum-level-raw <APPROVED_TRIP_LIMIT> ` |
| `docs/experiments/open-loop-identification-protocol.md` | 78 | Do not execute until the initial-level band, every DAC step, every hold duration, and the maximum raw-level trip threshold have been approved against the real plant and laboratory procedure. |
| `docs/experiments/open-loop-identification-protocol.md` | 83 | --initial-level-min-raw <APPROVED_INITIAL_MIN> ` |
| `docs/experiments/open-loop-identification-protocol.md` | 84 | --initial-level-max-raw <APPROVED_INITIAL_MAX> ` |
| `docs/experiments/open-loop-identification-protocol.md` | 85 | --maximum-level-raw <APPROVED_TRIP_LIMIT> ` |
| `docs/experiments/open-loop-identification-protocol.md` | 106 | - maximum raw-level trip threshold; |
| `docs/experiments/open-loop-identification-protocol.md` | 131 | 8. abort if raw level reaches the maximum trip threshold; |
| `docs/experiments/open-loop-identification-protocol.md` | 149 | The maximum observed level of 787 counts is not a physical limit. The maximum observed applied DAC of 12000 counts is not an automatically approved excitation value. |
| `docs/experiments/open-loop-identification-protocol.md` | 153 | - explicit physical level limits; |
| `docs/experiments/real-raw-pi-baseline-validation.md` | 62 | Raw level minimum: 207 |
| `docs/experiments/real-raw-pi-baseline-validation.md` | 63 | Raw level maximum: 787 |
| `docs/experiments/real-raw-pi-baseline-validation.md` | 66 | Rolling-median level minimum: 318.000 |
| `docs/experiments/real-raw-pi-baseline-validation.md` | 67 | Rolling-median level maximum: 736.000 |
| `docs/experiments/real-raw-pi-baseline-validation.md` | 75 | The maximum raw level observed over the complete recorded sequence was `787` counts. |
| `docs/experiments/real-raw-pi-identification-screening.json` | 155 | "operator_approved_maximum_level_required": true, |
| `docs/experiments/real-raw-pi-identification-screening.json` | 161 | "next_experiment_rule": "Use an approved multi-level open-loop sequence with an independently approved maximum raw-level trip. Do not infer the physical safety limit from the maximum value observed in this CSV.", |
| `docs/experiments/real-raw-pi-identification-screening.json` | 203 | "level_raw_max": 400.0, |
| `docs/experiments/real-raw-pi-identification-screening.json` | 205 | "level_raw_min": 360.0, |
| `docs/experiments/real-raw-pi-identification-screening.json` | 219 | "level_raw_max": 553.0, |
| `docs/experiments/real-raw-pi-identification-screening.json` | 221 | "level_raw_min": 136.0, |

## DAC-limit evidence

| File | Line | Excerpt |
|---|---:|---|
| `4diac/application/OPAS_Tank_System/DAC_RATE_LIMITER.fbt` | 2 | <FBType Name="DAC_RATE_LIMITER" Comment="Basic FB with empty ECC"> |
| `4diac/application/OPAS_Tank_System/DAC_RATE_LIMITER.fbt` | 11 | <With Var="MAX_DELTA_DAC"/> |
| `4diac/application/OPAS_Tank_System/DAC_RATE_LIMITER.fbt` | 12 | <With Var="DAC_MIN"/> |
| `4diac/application/OPAS_Tank_System/DAC_RATE_LIMITER.fbt` | 13 | <With Var="DAC_MAX"/> |
| `4diac/application/OPAS_Tank_System/DAC_RATE_LIMITER.fbt` | 24 | <VarDeclaration Name="MAX_DELTA_DAC" Type="LREAL" Comment=""/> |
| `4diac/application/OPAS_Tank_System/DAC_RATE_LIMITER.fbt` | 25 | <VarDeclaration Name="DAC_MIN" Type="LREAL" Comment=""/> |
| `4diac/application/OPAS_Tank_System/DAC_RATE_LIMITER.fbt` | 26 | <VarDeclaration Name="DAC_MAX" Type="LREAL" Comment=""/> |
| `4diac/application/OPAS_Tank_System/DAC_RATE_LIMITER.fbt` | 65 | IF delta > MAX_DELTA_DAC THEN |
| `4diac/application/OPAS_Tank_System/DAC_RATE_LIMITER.fbt` | 66 | DAC_OUT := last_dac + MAX_DELTA_DAC; |
| `4diac/application/OPAS_Tank_System/DAC_RATE_LIMITER.fbt` | 67 | ELSIF delta < -MAX_DELTA_DAC THEN |
| `4diac/application/OPAS_Tank_System/DAC_RATE_LIMITER.fbt` | 68 | DAC_OUT := last_dac - MAX_DELTA_DAC; |
| `4diac/application/OPAS_Tank_System/DAC_RATE_LIMITER.fbt` | 73 | IF DAC_OUT > DAC_MAX THEN |
| `4diac/application/OPAS_Tank_System/DAC_RATE_LIMITER.fbt` | 74 | DAC_OUT := DAC_MAX; |
| `4diac/application/OPAS_Tank_System/DAC_RATE_LIMITER.fbt` | 75 | ELSIF DAC_OUT < DAC_MIN THEN |
| `4diac/application/OPAS_Tank_System/DAC_RATE_LIMITER.fbt` | 76 | DAC_OUT := DAC_MIN; |
| `4diac/application/OPAS_Tank_System/MPC_LEVEL.fbt` | 16 | <With Var="DAC_MIN"/> |
| `4diac/application/OPAS_Tank_System/MPC_LEVEL.fbt` | 17 | <With Var="DAC_MAX"/> |
| `4diac/application/OPAS_Tank_System/MPC_LEVEL.fbt` | 41 | <VarDeclaration Name="DAC_MIN" Type="LREAL" Comment=""/> |
| `4diac/application/OPAS_Tank_System/MPC_LEVEL.fbt` | 42 | <VarDeclaration Name="DAC_MAX" Type="LREAL" Comment=""/> |
| `4diac/application/OPAS_Tank_System/MPC_LEVEL.fbt` | 109 | dac_candidate := DAC_MIN; |
| `4diac/application/OPAS_Tank_System/MPC_LEVEL.fbt` | 111 | WHILE dac_candidate <= DAC_MAX DO |
| `4diac/application/OPAS_Tank_System/MPC_LEVEL.fbt` | 134 | dac_candidate := DAC_MAX + 1.0; |
| `4diac/application/OPAS_Tank_System/MPC_LEVEL.fbt` | 141 | IF best_dac > DAC_MAX THEN |
| `4diac/application/OPAS_Tank_System/MPC_LEVEL.fbt` | 142 | best_dac := DAC_MAX; |
| `4diac/application/OPAS_Tank_System/MPC_LEVEL.fbt` | 143 | ELSIF best_dac < DAC_MIN THEN |
| `4diac/application/OPAS_Tank_System/MPC_LEVEL.fbt` | 144 | best_dac := DAC_MIN; |
| `4diac/application/OPAS_Tank_System/MPC_LEVEL.fbt` | 149 | IF DAC_MAX > 0.0 THEN |
| `4diac/application/OPAS_Tank_System/MPC_LEVEL.fbt` | 150 | MV_PERCENT := (DAC_OUT / DAC_MAX) * 100.0; |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 115 | <Parameter Name="IN2" Value="LREAL#32000.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 146 | <Parameter Name="DAC_MIN" Value="LREAL#0.0"/> |

## Pump-threshold evidence

| File | Line | Excerpt |
|---|---:|---|
| `docs/experiments/gateway-dynamic-plant-validation.md` | 153 | Keeping the DAC value at `32000` while setting `Enable = FALSE` was intentional. The dynamic model correctly removed the pump inflow while preserving the DAC command value. |
| `docs/experiments/gateway-dynamic-plant-validation.md` | 168 | - `Enable = FALSE` prevents pump inflow regardless of the DAC value; |
| `docs/experiments/open-loop-identification-protocol.md` | 18 | - pump-flow threshold; |
| `docs/gateway/plc-watchdog-integration.md` | 25 | The pump sound and water flow stopped at the watchdog trip. |
| `docs/simulation/offline-level-plant-model.md` | 42 | When `Enable = FALSE`, pump inflow is zero regardless of the DAC value. |
| `docs/simulation/offline-level-plant-model.md` | 66 | Pump inflow is: |
| `simulation/level_plant.py` | 87 | inflow(dac, enable) |
| `simulation/level_plant.py` | 94 | Inflow is proportional to the clamped DAC command when Enable is true. |

## Safety and interlock evidence

| File | Line | Excerpt |
|---|---:|---|
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 539 | <Application Name="PI_OFFLINE_SAFE_DAC_CLOSED_LOOP" Comment=""> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 583 | <FB Name="OfflineSafeDACLimiter" Type="SAFE_DAC_RATE_LIMITER" Comment="" x="3333.3333333333335" y="3333.3333333333335"> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 601 | <Connection Source="OfflineDACScale.CNF" Destination="OfflineSafeDACLimiter.REQ" Comment="" dx1="80.0" dx2="80.0" dy="400.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 602 | <Connection Source="OfflineSafeDACLimiter.CNF" Destination="OfflineDACType.REQ" Comment="" dx1="80.0" dx2="80.0" dy="600.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 614 | <Connection Source="OfflineDACScale.OUT" Destination="OfflineSafeDACLimiter.DAC_IN" Comment="" dx1="80.0" dx2="80.0" dy="400.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 615 | <Connection Source="OfflineSafeDACLimiter.DAC_OUT" Destination="OfflineDACType.IN" Comment="" dx1="80.0" dx2="80.0" dy="600.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 619 | <Application Name="PI_REAL_RAW_SAFE" Comment="Real plant PI in raw counts with manual-zero startup, output bias, safe DAC limiting, and no automatic resource start"> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 645 | <FB Name="RawSafeDACLimiter" Type="SAFE_DAC_RATE_LIMITER" Comment="Final application-level DAC bounds and symmetric rate limit" x="3333.3333333333335" y="3333.3333333333335"> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 652 | <FB Name="RawDACType" Type="F_LREAL_TO_INT" Comment="Convert safe DAC command to the gateway Int16 contract" x="3600.0" y="4533.333333333334"> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 672 | <Connection Source="RawDACBias.CNF" Destination="RawSafeDACLimiter.REQ" Comment="" dx1="80.0" dx2="80.0" dy="400.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 673 | <Connection Source="RawSafeDACLimiter.CNF" Destination="RawDACType.REQ" Comment="" dx1="80.0" dx2="80.0" dy="600.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 686 | <Connection Source="RawDACBias.OUT" Destination="RawSafeDACLimiter.DAC_IN" Comment="" dx1="80.0" dx2="80.0" dy="400.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 687 | <Connection Source="RawSafeDACLimiter.DAC_OUT" Destination="RawDACType.IN" Comment="" dx1="80.0" dx2="80.0" dy="600.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 939 | <Resource Name="ResOfflineSafeDAC" Type="EMB_RES" Comment="" x="0.0" y="0.0"> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 950 | <FB Name="OfflineSafeDACLimiter" Type="SAFE_DAC_RATE_LIMITER" Comment="" x="3333.3333333333335" y="3333.3333333333335"> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 991 | <Connection Source="OfflineDACScale.CNF" Destination="OfflineSafeDACLimiter.REQ" Comment="" dx1="80.0" dx2="80.0" dy="400.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 999 | <Connection Source="OfflineSafeDACLimiter.CNF" Destination="OfflineDACType.REQ" Comment="" dx1="80.0" dx2="80.0" dy="600.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 1008 | <Connection Source="OfflineDACScale.OUT" Destination="OfflineSafeDACLimiter.DAC_IN" Comment="" dx1="80.0" dx2="80.0" dy="400.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 1013 | <Connection Source="OfflineSafeDACLimiter.DAC_OUT" Destination="OfflineDACType.IN" Comment="" dx1="80.0" dx2="80.0" dy="600.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 1047 | <FB Name="RawSafeDACLimiter" Type="SAFE_DAC_RATE_LIMITER" Comment="Final application-level DAC bounds and symmetric rate limit" x="3333.3333333333335" y="3333.3333333333335"> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 1054 | <FB Name="RawDACType" Type="F_LREAL_TO_INT" Comment="Convert safe DAC command to the gateway Int16 contract" x="3600.0" y="4533.333333333334"> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 1074 | <Connection Source="RawDACBias.CNF" Destination="RawSafeDACLimiter.REQ" Comment="" dx1="80.0" dx2="80.0" dy="400.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 1075 | <Connection Source="RawSafeDACLimiter.CNF" Destination="RawDACType.REQ" Comment="" dx1="80.0" dx2="80.0" dy="600.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 1088 | <Connection Source="RawDACBias.OUT" Destination="RawSafeDACLimiter.DAC_IN" Comment="" dx1="80.0" dx2="80.0" dy="400.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 1089 | <Connection Source="RawSafeDACLimiter.DAC_OUT" Destination="RawDACType.IN" Comment="" dx1="80.0" dx2="80.0" dy="600.0"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 1139 | <Mapping From="PI_OFFLINE_SAFE_DAC_CLOSED_LOOP.OfflineDACScale" To="FORTE_PC.ResOfflineSafeDAC.OfflineDACScale"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 1140 | <Mapping From="PI_OFFLINE_SAFE_DAC_CLOSED_LOOP.OfflinePVFilter" To="FORTE_PC.ResOfflineSafeDAC.OfflinePVFilter"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 1141 | <Mapping From="PI_OFFLINE_SAFE_DAC_CLOSED_LOOP.OfflineLevelType" To="FORTE_PC.ResOfflineSafeDAC.OfflineLevelType"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 1142 | <Mapping From="PI_OFFLINE_SAFE_DAC_CLOSED_LOOP.OfflineSafeDACLimiter" To="FORTE_PC.ResOfflineSafeDAC.OfflineSafeDACLimiter"/> |
| `4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys` | 1143 | <Mapping From="PI_OFFLINE_SAFE_DAC_CLOSED_LOOP.OfflineEnableWrite" To="FORTE_PC.ResOfflineSafeDAC.OfflineEnableWrite"/> |

## Approval worksheet

| Parameter | Value | Unit | Status | Required before execution | Evidence/approval |
|---|---:|---|---|---|---|
| Raw level corresponding to an empty tank | — | raw count | `NOT_APPROVED` | YES | To be completed from physical documentation, PLC configuration, measurement, and laboratory approval |
| Raw level corresponding to overflow or physical maximum | — | raw count | `NOT_APPROVED` | YES | To be completed from physical documentation, PLC configuration, measurement, and laboratory approval |
| PLC or approved high-level trip | — | raw count | `NOT_APPROVED` | YES | To be completed from physical documentation, PLC configuration, measurement, and laboratory approval |
| Approved initial raw-level minimum | — | raw count | `NOT_APPROVED` | YES | To be completed from physical documentation, PLC configuration, measurement, and laboratory approval |
| Approved initial raw-level maximum | — | raw count | `NOT_APPROVED` | YES | To be completed from physical documentation, PLC configuration, measurement, and laboratory approval |
| Approved identification abort threshold | — | raw count | `NOT_APPROVED` | YES | To be completed from physical documentation, PLC configuration, measurement, and laboratory approval |
| Minimum DAC with repeatable positive pump flow | — | DAC count | `NOT_APPROVED` | YES | To be completed from physical documentation, PLC configuration, measurement, and laboratory approval |
| Maximum DAC permitted during identification | — | DAC count | `NOT_APPROVED` | YES | To be completed from physical documentation, PLC configuration, measurement, and laboratory approval |
| Approved ordered DAC plateaus | — | DAC count | `NOT_APPROVED` | YES | To be completed from physical documentation, PLC configuration, measurement, and laboratory approval |
| Approved hold duration for each plateau | — | s | `NOT_APPROVED` | YES | To be completed from physical documentation, PLC configuration, measurement, and laboratory approval |
| Approved total experiment duration | — | s | `NOT_APPROVED` | YES | To be completed from physical documentation, PLC configuration, measurement, and laboratory approval |
| Optional approved level-rate abort threshold | — | raw count/s | `NOT_APPROVED` | NO | To be completed from physical documentation, PLC configuration, measurement, and laboratory approval |

## Required evidence hierarchy

1. Physical tank and sensor documentation.
2. B&R PLC safety and scaling configuration.
3. Direct laboratory measurement with the actuator disabled where possible.
4. Previously validated real-plant evidence.
5. Documented engineering inference with margin.
6. Historical or provisional software values only as supporting context.

## Decision

```text
PHYSICAL LIMITS IDENTIFIED: NO
IDENTIFICATION LIMITS APPROVED: NO
REAL EXPERIMENT AUTHORIZED: NO
REPOSITORY EVIDENCE IS AUTHORITATIVE: NO
OBSERVED VALUES ARE SAFETY LIMITS: NO
MANUAL ENGINEERING REVIEW REQUIRED: YES
LABORATORY CONFIRMATION REQUIRED: YES
```

The open-loop identification command must remain in `--plan` mode until every execution-required field has an approved value and source.

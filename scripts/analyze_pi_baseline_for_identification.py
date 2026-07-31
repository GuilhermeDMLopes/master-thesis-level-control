from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_INPUT = Path(
    "data/sample/real-raw-pi-v1-monitor.csv"
)
DEFAULT_REPORT = Path(
    "docs/experiments/"
    "real-raw-pi-identification-screening.md"
)
DEFAULT_JSON = Path(
    "docs/experiments/"
    "real-raw-pi-identification-screening.json"
)
EXPECTED_BASELINE_SHA256 = (
    "197D0F0113564EACC40D16325CF1760008C595CE815300DA8BE5841CAB060E07"
)

REQUIRED_COLUMNS = {
    "timestamp",
    "elapsed_s",
    "phase",
    "level_raw",
    "rolling_median_level",
    "heartbeat",
    "watchdog_healthy",
    "watchdog_tripped",
    "safety_reset",
    "enable",
    "dac",
    "applied_enable",
    "applied_dac",
}


@dataclass(frozen=True)
class Sample:
    timestamp: str
    elapsed_s: float
    phase: str
    level_raw: float
    rolling_median_level: float
    heartbeat: int
    watchdog_healthy: bool
    watchdog_tripped: bool
    safety_reset: bool
    enable: bool
    dac: int
    applied_enable: bool
    applied_dac: int


def as_bool(value: str) -> bool:
    normalized = value.strip().lower()

    if normalized in {"true", "1", "yes"}:
        return True

    if normalized in {"false", "0", "no"}:
        return False

    raise ValueError(f"Invalid Boolean value: {value!r}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        for chunk in iter(
            lambda: stream.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest().upper()


def percentile(
    values: Sequence[float],
    probability: float,
) -> float:
    if not values:
        raise ValueError("Cannot calculate a percentile of no values.")

    ordered = sorted(values)

    if len(ordered) == 1:
        return float(ordered[0])

    position = probability * (len(ordered) - 1)
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = position - lower_index

    return (
        ordered[lower_index]
        + fraction
        * (
            ordered[upper_index]
            - ordered[lower_index]
        )
    )


def load_samples(path: Path) -> list[Sample]:
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as stream:
        reader = csv.DictReader(
            stream,
            delimiter=";",
        )

        if reader.fieldnames is None:
            raise RuntimeError("The CSV has no header.")

        missing = REQUIRED_COLUMNS.difference(
            reader.fieldnames
        )

        if missing:
            raise RuntimeError(
                "Missing CSV columns: "
                + ", ".join(sorted(missing))
            )

        samples = [
            Sample(
                timestamp=row["timestamp"],
                elapsed_s=float(row["elapsed_s"]),
                phase=row["phase"].strip(),
                level_raw=float(row["level_raw"]),
                rolling_median_level=float(
                    row["rolling_median_level"]
                ),
                heartbeat=int(float(row["heartbeat"])),
                watchdog_healthy=as_bool(
                    row["watchdog_healthy"]
                ),
                watchdog_tripped=as_bool(
                    row["watchdog_tripped"]
                ),
                safety_reset=as_bool(
                    row["safety_reset"]
                ),
                enable=as_bool(row["enable"]),
                dac=int(float(row["dac"])),
                applied_enable=as_bool(
                    row["applied_enable"]
                ),
                applied_dac=int(
                    float(row["applied_dac"])
                ),
            )
            for row in reader
        ]

    if not samples:
        raise RuntimeError("The CSV contains no data rows.")

    previous = samples[0].elapsed_s

    for sample in samples[1:]:
        if sample.elapsed_s < previous:
            raise RuntimeError(
                "elapsed_s is not monotonically non-decreasing."
            )

        previous = sample.elapsed_s

    return samples


def numeric_summary(
    values: Sequence[float],
) -> dict[str, float]:
    if not values:
        raise ValueError("Cannot summarize no values.")

    return {
        "minimum": min(values),
        "maximum": max(values),
        "median": statistics.median(values),
        "mean": statistics.fmean(values),
        "p05": percentile(values, 0.05),
        "p95": percentile(values, 0.95),
    }


def contiguous_phase_segments(
    samples: Sequence[Sample],
) -> list[dict[str, object]]:
    segments: list[list[Sample]] = []

    for sample in samples:
        if (
            not segments
            or segments[-1][-1].phase != sample.phase
        ):
            segments.append([sample])
        else:
            segments[-1].append(sample)

    result = []

    for index, segment in enumerate(segments, start=1):
        levels = [sample.level_raw for sample in segment]
        medians = [
            sample.rolling_median_level
            for sample in segment
        ]
        applied_dac = [
            sample.applied_dac
            for sample in segment
        ]

        result.append(
            {
                "index": index,
                "phase": segment[0].phase,
                "rows": len(segment),
                "start_s": segment[0].elapsed_s,
                "end_s": segment[-1].elapsed_s,
                "duration_s": (
                    segment[-1].elapsed_s
                    - segment[0].elapsed_s
                ),
                "level_raw_min": min(levels),
                "level_raw_max": max(levels),
                "level_raw_median": statistics.median(
                    levels
                ),
                "rolling_median_min": min(medians),
                "rolling_median_max": max(medians),
                "applied_dac_min": min(applied_dac),
                "applied_dac_max": max(applied_dac),
                "applied_dac_median": statistics.median(
                    applied_dac
                ),
            }
        )

    return result


def stable_positive_dac_segments(
    samples: Sequence[Sample],
    minimum_duration_s: float = 0.5,
) -> list[dict[str, object]]:
    groups: list[list[Sample]] = []

    for sample in samples:
        key = (
            sample.applied_enable,
            sample.applied_dac,
            sample.phase,
        )

        previous_key = None

        if groups:
            previous = groups[-1][-1]
            previous_key = (
                previous.applied_enable,
                previous.applied_dac,
                previous.phase,
            )

        if not groups or previous_key != key:
            groups.append([sample])
        else:
            groups[-1].append(sample)

    plateaus = []

    for group in groups:
        duration_s = (
            group[-1].elapsed_s
            - group[0].elapsed_s
        )

        if (
            group[0].applied_enable
            and group[0].applied_dac > 0
            and duration_s >= minimum_duration_s
        ):
            levels = [
                sample.rolling_median_level
                for sample in group
            ]

            plateaus.append(
                {
                    "phase": group[0].phase,
                    "applied_dac": group[0].applied_dac,
                    "rows": len(group),
                    "start_s": group[0].elapsed_s,
                    "end_s": group[-1].elapsed_s,
                    "duration_s": duration_s,
                    "rolling_median_start": levels[0],
                    "rolling_median_end": levels[-1],
                    "rolling_median_change": (
                        levels[-1] - levels[0]
                    ),
                }
            )

    return plateaus


def derivative_values(
    samples: Sequence[Sample],
) -> list[float]:
    derivatives = []

    for previous, current in zip(
        samples,
        samples[1:],
    ):
        dt = current.elapsed_s - previous.elapsed_s

        if dt <= 0.0:
            continue

        derivatives.append(
            (
                current.rolling_median_level
                - previous.rolling_median_level
            )
            / dt
        )

    return derivatives


def sample_intervals(
    samples: Sequence[Sample],
) -> list[float]:
    return [
        current.elapsed_s - previous.elapsed_s
        for previous, current in zip(
            samples,
            samples[1:],
        )
        if current.elapsed_s - previous.elapsed_s > 0.0
    ]


def analyze(
    samples: Sequence[Sample],
    source_path: Path,
    source_hash: str,
) -> dict[str, object]:
    intervals = sample_intervals(samples)
    phase_segments = contiguous_phase_segments(samples)
    plateaus = stable_positive_dac_segments(samples)

    levels = [sample.level_raw for sample in samples]
    medians = [
        sample.rolling_median_level
        for sample in samples
    ]
    applied_dac = [
        sample.applied_dac
        for sample in samples
    ]
    derivatives = derivative_values(samples)

    automatic = [
        sample
        for sample in samples
        if sample.phase == "AUTO_ACTIVE"
    ]
    active = [
        sample
        for sample in samples
        if sample.applied_enable
    ]

    auto_levels = [
        sample.rolling_median_level
        for sample in automatic
    ]
    auto_dac = [
        sample.applied_dac
        for sample in automatic
    ]

    command_mismatch = [
        abs(sample.dac - sample.applied_dac)
        for sample in samples
    ]
    enable_mismatch_count = sum(
        sample.enable != sample.applied_enable
        for sample in samples
    )

    safety = {
        "watchdog_unhealthy_rows": sum(
            not sample.watchdog_healthy
            for sample in samples
        ),
        "watchdog_tripped_rows": sum(
            sample.watchdog_tripped
            for sample in samples
        ),
        "safety_reset_rows": sum(
            sample.safety_reset
            for sample in samples
        ),
        "negative_applied_dac_rows": sum(
            sample.applied_dac < 0
            for sample in samples
        ),
        "applied_dac_above_12000_rows": sum(
            sample.applied_dac > 12000
            for sample in samples
        ),
        "final_zero_output": (
            not samples[-1].enable
            and samples[-1].dac == 0
            and not samples[-1].applied_enable
            and samples[-1].applied_dac == 0
        ),
    }

    max_level_sample = max(
        samples,
        key=lambda sample: sample.level_raw,
    )

    positive_dac = [
        sample.applied_dac
        for sample in active
        if sample.applied_dac > 0
    ]

    common_positive_dac = [
        {
            "applied_dac": value,
            "rows": count,
        }
        for value, count in Counter(
            positive_dac
        ).most_common(12)
    ]

    automatic_summary = None

    if automatic:
        automatic_summary = {
            "rows": len(automatic),
            "start_s": automatic[0].elapsed_s,
            "end_s": automatic[-1].elapsed_s,
            "duration_s": (
                automatic[-1].elapsed_s
                - automatic[0].elapsed_s
            ),
            "rolling_median_level": numeric_summary(
                auto_levels
            ),
            "applied_dac": numeric_summary(
                [
                    float(value)
                    for value in auto_dac
                ]
            ),
            "applied_dac_range": (
                max(auto_dac) - min(auto_dac)
            ),
        }

    interval_summary = (
        numeric_summary(intervals)
        if intervals
        else None
    )
    derivative_summary = (
        numeric_summary(derivatives)
        if derivatives
        else None
    )

    observed_positive_dac = None

    if positive_dac:
        observed_positive_dac = {
            "minimum": min(positive_dac),
            "maximum": max(positive_dac),
            "median": statistics.median(
                positive_dac
            ),
        }

    return {
        "schema_version": 1,
        "source": {
            "path": source_path.as_posix(),
            "sha256": source_hash,
        },
        "dataset": {
            "rows": len(samples),
            "duration_s": (
                samples[-1].elapsed_s
                - samples[0].elapsed_s
            ),
            "phase_names_in_order": [
                segment["phase"]
                for segment in phase_segments
            ],
            "sample_interval_s": interval_summary,
        },
        "level": {
            "raw": numeric_summary(levels),
            "rolling_median": numeric_summary(
                medians
            ),
            "maximum_observation": {
                "value": max_level_sample.level_raw,
                "elapsed_s": max_level_sample.elapsed_s,
                "phase": max_level_sample.phase,
            },
            "rolling_median_derivative_per_s":
                derivative_summary,
        },
        "actuator": {
            "applied_dac": numeric_summary(
                [
                    float(value)
                    for value in applied_dac
                ]
            ),
            "observed_positive_dac":
                observed_positive_dac,
            "common_positive_dac":
                common_positive_dac,
            "stable_positive_plateaus": plateaus,
            "command_applied_mismatch_rows": sum(
                mismatch != 0
                for mismatch in command_mismatch
            ),
            "maximum_command_applied_mismatch": max(
                command_mismatch
            ),
            "enable_applied_mismatch_rows":
                enable_mismatch_count,
        },
        "automatic_phase": automatic_summary,
        "active_rows": len(active),
        "safety": safety,
        "phase_segments": phase_segments,
        "decision": {
            "baseline_screening_completed": True,
            "dataset_is_open_loop": False,
            "real_plant_model_identified": False,
            "real_test_limits_auto_approved": False,
            "open_loop_data_required": True,
            "operator_approved_maximum_level_required":
                True,
            "multiple_excitation_levels_required": True,
        },
        "interpretation": {
            "primary_use": (
                "Observed-range and safety screening "
                "before open-loop identification."
            ),
            "limitation": (
                "The DAC was generated by manual staging "
                "and closed-loop PI control. Input and output "
                "are therefore coupled, so this dataset cannot "
                "by itself support an unbiased real-plant model."
            ),
            "next_experiment_rule": (
                "Use an approved multi-level open-loop sequence "
                "with an independently approved maximum raw-level "
                "trip. Do not infer the physical safety limit from "
                "the maximum value observed in this CSV."
            ),
        },
    }


def format_number(value: object) -> str:
    if value is None:
        return "not available"

    if isinstance(value, bool):
        return "YES" if value else "NO"

    if isinstance(value, int):
        return str(value)

    if isinstance(value, float):
        return f"{value:.3f}"

    return str(value)


def phase_table(
    segments: Iterable[dict[str, object]],
) -> str:
    lines = [
        (
            "| # | Phase | Start (s) | End (s) | "
            "Rows | Level min | Level max | "
            "Applied DAC min | Applied DAC max |"
        ),
        (
            "|---:|---|---:|---:|---:|---:|---:|"
            "---:|---:|"
        ),
    ]

    for segment in segments:
        lines.append(
            "| "
            f"{segment['index']} | "
            f"`{segment['phase']}` | "
            f"{format_number(segment['start_s'])} | "
            f"{format_number(segment['end_s'])} | "
            f"{segment['rows']} | "
            f"{format_number(segment['level_raw_min'])} | "
            f"{format_number(segment['level_raw_max'])} | "
            f"{segment['applied_dac_min']} | "
            f"{segment['applied_dac_max']} |"
        )

    return "\n".join(lines)


def plateau_table(
    plateaus: Sequence[dict[str, object]],
) -> str:
    if not plateaus:
        return (
            "No exact positive-DAC plateau lasting at least "
            "0.5 s was detected."
        )

    lines = [
        (
            "| Phase | Applied DAC | Start (s) | "
            "Duration (s) | Median-level change |"
        ),
        "|---|---:|---:|---:|---:|",
    ]

    for plateau in plateaus:
        lines.append(
            "| "
            f"`{plateau['phase']}` | "
            f"{plateau['applied_dac']} | "
            f"{format_number(plateau['start_s'])} | "
            f"{format_number(plateau['duration_s'])} | "
            f"{format_number(plateau['rolling_median_change'])} |"
        )

    return "\n".join(lines)


def build_markdown(
    analysis: dict[str, object],
) -> str:
    source = analysis["source"]
    dataset = analysis["dataset"]
    level = analysis["level"]
    actuator = analysis["actuator"]
    automatic = analysis["automatic_phase"]
    safety = analysis["safety"]
    decision = analysis["decision"]

    interval = dataset["sample_interval_s"]
    raw = level["raw"]
    rolling = level["rolling_median"]
    derivative = level[
        "rolling_median_derivative_per_s"
    ]
    maximum = level["maximum_observation"]
    applied = actuator["applied_dac"]
    observed_positive = actuator[
        "observed_positive_dac"
    ]

    auto_section = (
        "No `AUTO_ACTIVE` samples were found."
    )

    if automatic is not None:
        auto_section = f"""```text
Rows: {automatic['rows']}
Duration: {format_number(automatic['duration_s'])} s
Rolling-median level minimum: {format_number(automatic['rolling_median_level']['minimum'])}
Rolling-median level maximum: {format_number(automatic['rolling_median_level']['maximum'])}
Applied DAC minimum: {format_number(automatic['applied_dac']['minimum'])}
Applied DAC maximum: {format_number(automatic['applied_dac']['maximum'])}
Applied DAC range: {format_number(automatic['applied_dac_range'])}
```"""

    positive_section = (
        "No positive applied DAC was observed."
    )

    if observed_positive is not None:
        positive_section = f"""```text
Minimum positive applied DAC: {format_number(observed_positive['minimum'])}
Maximum positive applied DAC: {format_number(observed_positive['maximum'])}
Median positive applied DAC: {format_number(observed_positive['median'])}
```"""

    derivative_section = (
        "No valid derivative samples were available."
    )

    if derivative is not None:
        derivative_section = f"""```text
P05: {format_number(derivative['p05'])} raw-count/s
Median: {format_number(derivative['median'])} raw-count/s
P95: {format_number(derivative['p95'])} raw-count/s
Minimum: {format_number(derivative['minimum'])} raw-count/s
Maximum: {format_number(derivative['maximum'])} raw-count/s
```"""

    interval_section = (
        "No positive sampling intervals were available."
    )

    if interval is not None:
        interval_section = f"""```text
Median: {format_number(interval['median'])} s
P05: {format_number(interval['p05'])} s
P95: {format_number(interval['p95'])} s
Minimum: {format_number(interval['minimum'])} s
Maximum: {format_number(interval['maximum'])} s
```"""

    return f"""# Real Raw-Count PI Identification Screening

## Status

This is an offline screening of the validated PI baseline. It does not identify the real plant and does not approve a real open-loop test automatically.

## Source and integrity

```text
Source: {source['path']}
SHA256: {source['sha256']}
Rows: {dataset['rows']}
Recorded duration: {format_number(dataset['duration_s'])} s
```

## Scope

The baseline is useful for confirming observed operating ranges, recorded phases, command/application consistency, sampling behavior, and safety-state preservation.

It is not a valid standalone open-loop identification dataset. The actuator command was produced by manual staging and closed-loop PI behavior, so the measured input and output are coupled.

## Sampling

{interval_section}

## Observed level range

```text
Raw level minimum: {format_number(raw['minimum'])}
Raw level maximum: {format_number(raw['maximum'])}
Raw level median: {format_number(raw['median'])}

Rolling-median minimum: {format_number(rolling['minimum'])}
Rolling-median maximum: {format_number(rolling['maximum'])}
Rolling-median median: {format_number(rolling['median'])}

Maximum raw observation: {format_number(maximum['value'])}
Maximum observation time: {format_number(maximum['elapsed_s'])} s
Maximum observation phase: {maximum['phase']}
```

The maximum observed value is evidence from this run, not a physical or approved safety limit.

## Observed actuator range

```text
Applied DAC minimum: {format_number(applied['minimum'])}
Applied DAC maximum: {format_number(applied['maximum'])}
Applied DAC median: {format_number(applied['median'])}
Command/applied mismatch rows: {actuator['command_applied_mismatch_rows']}
Maximum command/applied mismatch: {actuator['maximum_command_applied_mismatch']}
Enable/applied-enable mismatch rows: {actuator['enable_applied_mismatch_rows']}
```

{positive_section}

## Automatic phase

{auto_section}

## Rolling-median level-rate screening

{derivative_section}

These rates are descriptive. They must not be interpreted as an identified process gain or time constant.

## Phase segments

{phase_table(analysis['phase_segments'])}

## Stable positive-DAC plateaus detected

{plateau_table(actuator['stable_positive_plateaus'])}

Exact plateaus can help locate sections for visual review, but they do not remove the closed-loop bias from this dataset.

## Safety screening

```text
Watchdog-unhealthy rows: {safety['watchdog_unhealthy_rows']}
Watchdog-tripped rows: {safety['watchdog_tripped_rows']}
SafetyReset rows: {safety['safety_reset_rows']}
Negative AppliedDAC rows: {safety['negative_applied_dac_rows']}
AppliedDAC above 12000 rows: {safety['applied_dac_above_12000_rows']}
Final zero-output state: {format_number(safety['final_zero_output'])}
```

## Identification decision

```text
BASELINE SCREENING COMPLETED: {format_number(decision['baseline_screening_completed'])}
DATASET IS OPEN LOOP: {format_number(decision['dataset_is_open_loop'])}
REAL PLANT MODEL IDENTIFIED: {format_number(decision['real_plant_model_identified'])}
REAL TEST LIMITS AUTO-APPROVED: {format_number(decision['real_test_limits_auto_approved'])}
OPEN-LOOP DATA REQUIRED: {format_number(decision['open_loop_data_required'])}
OPERATOR-APPROVED MAXIMUM LEVEL REQUIRED: {format_number(decision['operator_approved_maximum_level_required'])}
MULTIPLE EXCITATION LEVELS REQUIRED: {format_number(decision['multiple_excitation_levels_required'])}
```

## Required inputs before a real identification run

The following values still require explicit engineering and laboratory approval:

1. physical maximum raw-level limit and emergency margin;
2. approved initial level band;
3. staged DAC sequence, rather than an unreviewed single step;
4. hold time for each DAC level;
5. abort criteria for level rate, communication, and elapsed time;
6. repeat-run count and independent validation dataset.

The next real experiment should use multiple safe excitation levels and retain the validated PLC watchdog and fail-closed shutdown path.
"""


def write_outputs(
    analysis: dict[str, object],
    report_path: Path,
    json_path: Path,
) -> None:
    report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    json_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path.write_text(
        build_markdown(analysis),
        encoding="utf-8",
        newline="\n",
    )
    json_path.write_text(
        json.dumps(
            analysis,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Screen the validated real raw-count PI CSV for "
            "plant-identification readiness. This command is "
            "offline and performs no network or actuator access."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"input CSV (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT,
        help=f"Markdown report (default: {DEFAULT_REPORT})",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=DEFAULT_JSON,
        help=f"JSON result (default: {DEFAULT_JSON})",
    )
    parser.add_argument(
        "--expected-sha256",
        default=EXPECTED_BASELINE_SHA256,
        help=(
            "expected uppercase SHA256; pass an empty string "
            "to disable the integrity comparison"
        ),
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    args = build_parser().parse_args(argv)

    if not args.input.is_file():
        raise SystemExit(
            f"Input CSV not found: {args.input}"
        )

    source_hash = sha256(args.input)
    expected = args.expected_sha256.strip().upper()

    if expected and source_hash != expected:
        raise SystemExit(
            "Input CSV SHA256 mismatch: "
            f"expected {expected}, got {source_hash}"
        )

    samples = load_samples(args.input)
    result = analyze(
        samples,
        args.input,
        source_hash,
    )
    write_outputs(
        result,
        args.report,
        args.json,
    )

    print("REAL RAW PI IDENTIFICATION SCREENING")
    print("====================================")
    print(f"Source: {args.input}")
    print(f"Rows: {result['dataset']['rows']}")
    print(
        "Raw level range: "
        f"{result['level']['raw']['minimum']:.3f} to "
        f"{result['level']['raw']['maximum']:.3f}"
    )
    print(
        "Applied DAC range: "
        f"{result['actuator']['applied_dac']['minimum']:.3f} to "
        f"{result['actuator']['applied_dac']['maximum']:.3f}"
    )
    print(
        "Automatic rows: "
        + str(
            0
            if result["automatic_phase"] is None
            else result["automatic_phase"]["rows"]
        )
    )
    print(f"Report: {args.report}")
    print(f"JSON: {args.json}")
    print("NETWORK ACCESS: NO")
    print("ACTUATOR WRITES: NO")
    print("REAL PLANT MODEL IDENTIFIED: NO")
    print("REAL TEST LIMITS AUTO-APPROVED: NO")
    print("OPEN-LOOP DATA REQUIRED: YES")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

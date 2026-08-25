from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Sequence

DEFAULT_SCREENING = Path('docs/experiments/real-raw-pi-identification-screening.json')
DEFAULT_REPORT = Path('docs/experiments/plant-identification-limit-review.md')
DEFAULT_JSON = Path('docs/experiments/plant-identification-limit-review.json')
TEXT_SUFFIXES = {'.cmd','.fbt','.json','.md','.ps1','.py','.st','.sys','.txt','.xml','.yaml','.yml'}
PATTERNS = {
    'level_calibration': [r'LEVEL_SCALE', r'(raw|count).{0,50}(cm|mm|meter|metre)', r'(nivel|level).{0,40}(scale|calibration)'],
    'level_limits': [r'(maximum|max|min|minimum).{0,40}(nivel|level)', r'(nivel|level).{0,40}(limit|trip|max|min)', r'overflow', r'transbord'],
    'dac_limits': [r'DAC_MAX', r'DAC_MIN', r'MAX_DELTA_DAC', r'(dac|output).{0,40}(limit|max|min|range|saturation)', r'\b32000\b', r'\b12000\b'],
    'pump_threshold': [r'(pump|bomba).{0,60}(threshold|min|flow|vaz)', r'(flow|vaz).{0,60}(threshold|pump|bomba|dac)'],
    'safety_interlocks': [r'WatchdogHealthy', r'WatchdogTripped', r'SafetyReset', r'AppliedDAC', r'fail[- ]closed', r'(safe|safety|interlock|trip).{0,50}(dac|enable|output)'],
}
COMPILED = {k: [re.compile(p, re.I) for p in v] for k, v in PATTERNS.items()}


def tracked_files(root: Path) -> list[Path]:
    result = subprocess.run(['git','ls-files','-z'], cwd=root, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors='replace'))
    return [root / p.decode('utf-8', errors='surrogateescape') for p in result.stdout.split(b'\0') if p]


def scan(root: Path) -> list[dict[str, object]]:
    hits: list[dict[str, object]] = []
    excluded = {DEFAULT_REPORT.as_posix(), DEFAULT_JSON.as_posix()}
    for path in tracked_files(root):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        rel = path.relative_to(root).as_posix()
        if rel in excluded:
            continue
        text = path.read_text(encoding='utf-8', errors='replace')
        for line_no, line in enumerate(text.splitlines(), 1):
            excerpt = ' '.join(line.strip().split())[:220]
            for category, patterns in COMPILED.items():
                if any(p.search(line) for p in patterns):
                    hits.append({'category': category, 'path': rel, 'line': line_no, 'excerpt': excerpt})
    unique = {(h['category'], h['path'], h['line'], h['excerpt']): h for h in hits}
    return sorted(unique.values(), key=lambda h: (h['category'], h['path'], h['line']))


def observed(screening: dict[str, object]) -> dict[str, object]:
    source = screening['source']
    dataset = screening['dataset']
    level = screening['level']
    actuator = screening['actuator']
    automatic = screening.get('automatic_phase') or {}
    return {
        'source_path': source['path'],
        'source_sha256': source['sha256'],
        'rows': dataset['rows'],
        'duration_s': dataset['duration_s'],
        'level_raw_minimum': level['raw']['minimum'],
        'level_raw_maximum': level['raw']['maximum'],
        'level_raw_median': level['raw']['median'],
        'maximum_level_phase': level['maximum_observation']['phase'],
        'applied_dac_minimum': actuator['applied_dac']['minimum'],
        'applied_dac_maximum': actuator['applied_dac']['maximum'],
        'applied_dac_median': actuator['applied_dac']['median'],
        'automatic_rows': automatic.get('rows', 0),
    }


def approval_fields() -> list[dict[str, object]]:
    labels = [
        ('empty_tank_raw','Raw level corresponding to an empty tank','raw count',True),
        ('physical_overflow_raw','Raw level corresponding to overflow or physical maximum','raw count',True),
        ('plc_trip_raw','PLC or approved high-level trip','raw count',True),
        ('initial_level_min_raw','Approved initial raw-level minimum','raw count',True),
        ('initial_level_max_raw','Approved initial raw-level maximum','raw count',True),
        ('maximum_level_raw','Approved identification abort threshold','raw count',True),
        ('minimum_effective_dac','Minimum DAC with repeatable positive pump flow','DAC count',True),
        ('maximum_identification_dac','Maximum DAC permitted during identification','DAC count',True),
        ('dac_steps','Approved ordered DAC plateaus','DAC count',True),
        ('hold_durations_s','Approved hold duration for each plateau','s',True),
        ('maximum_experiment_duration_s','Approved total experiment duration','s',True),
        ('level_rate_abort_raw_per_s','Optional approved level-rate abort threshold','raw count/s',False),
    ]
    return [
        {'id': i, 'label': label, 'value': None, 'unit': unit, 'status': 'NOT_APPROVED', 'required_before_execute': required}
        for i, label, unit, required in labels
    ]


def build_result(screening: dict[str, object], hits: list[dict[str, object]]) -> dict[str, object]:
    summary = {}
    for category in PATTERNS:
        selected = [h for h in hits if h['category'] == category]
        summary[category] = {'hit_count': len(selected), 'file_count': len({h['path'] for h in selected})}
    return {
        'schema_version': 1,
        'observed_pi_baseline': observed(screening),
        'repository_evidence': {'category_summary': summary, 'hits': hits},
        'approval_fields': approval_fields(),
        'decision': {
            'physical_limits_identified': False,
            'identification_limits_approved': False,
            'real_experiment_authorized': False,
            'repository_evidence_is_authoritative': False,
            'observed_values_are_safety_limits': False,
            'manual_engineering_review_required': True,
            'laboratory_confirmation_required': True,
        },
    }


def evidence_table(hits: list[dict[str, object]], category: str) -> str:
    selected = [h for h in hits if h['category'] == category][:30]
    if not selected:
        return 'No matching tracked-text evidence was found.'
    rows = ['| File | Line | Excerpt |','|---|---:|---|']
    for h in selected:
        excerpt = str(h['excerpt']).replace('|', r'\|')
        rows.append(f"| `{h['path']}` | {h['line']} | {excerpt} |")
    return '\n'.join(rows)


def markdown(result: dict[str, object]) -> str:
    o = result['observed_pi_baseline']
    s = result['repository_evidence']['category_summary']
    hits = result['repository_evidence']['hits']
    fields = result['approval_fields']
    approvals = ['| Parameter | Value | Unit | Status | Required before execution | Evidence/approval |','|---|---:|---|---|---|---|']
    for f in fields:
        approvals.append(f"| {f['label']} | — | {f['unit']} | `{f['status']}` | {'YES' if f['required_before_execute'] else 'NO'} | To be completed from physical documentation, PLC configuration, measurement, and laboratory approval |")
    d = result['decision']
    return f'''# Plant Identification Physical-Limit Review

## Status

This document is an offline evidence inventory and approval worksheet. It does not define physical limits, approve excitation values, or authorize a real-plant identification run.

## Validated PI baseline observations

```text
Source: {o['source_path']}
SHA256: {o['source_sha256']}
Rows: {o['rows']}
Duration: {o['duration_s']} s
Observed raw-level minimum: {o['level_raw_minimum']}
Observed raw-level maximum: {o['level_raw_maximum']}
Observed raw-level median: {o['level_raw_median']}
Maximum observed level phase: {o['maximum_level_phase']}
Observed applied-DAC minimum: {o['applied_dac_minimum']}
Observed applied-DAC maximum: {o['applied_dac_maximum']}
Observed applied-DAC median: {o['applied_dac_median']}
Automatic rows: {o['automatic_rows']}
```

These are observations from one PI commissioning run. They are not automatically valid as physical, operational, or safety limits. In particular, 787 raw counts is not an approved high-level trip, 12000 DAC counts is not an approved identification excitation, and 32000 is not automatically an approved experimental command.

## Evidence inventory summary

| Category | Matching lines | Files |
|---|---:|---:|
| Level calibration | {s['level_calibration']['hit_count']} | {s['level_calibration']['file_count']} |
| Level limits | {s['level_limits']['hit_count']} | {s['level_limits']['file_count']} |
| DAC limits | {s['dac_limits']['hit_count']} | {s['dac_limits']['file_count']} |
| Pump threshold | {s['pump_threshold']['hit_count']} | {s['pump_threshold']['file_count']} |
| Safety interlocks | {s['safety_interlocks']['hit_count']} | {s['safety_interlocks']['file_count']} |

Keyword matches are review leads, not automatically authoritative values.

## Level-calibration evidence

{evidence_table(hits, 'level_calibration')}

## Level-limit evidence

{evidence_table(hits, 'level_limits')}

## DAC-limit evidence

{evidence_table(hits, 'dac_limits')}

## Pump-threshold evidence

{evidence_table(hits, 'pump_threshold')}

## Safety and interlock evidence

{evidence_table(hits, 'safety_interlocks')}

## Approval worksheet

{chr(10).join(approvals)}

## Required evidence hierarchy

1. Physical tank and sensor documentation.
2. B&R PLC safety and scaling configuration.
3. Direct laboratory measurement with the actuator disabled where possible.
4. Previously validated real-plant evidence.
5. Documented engineering inference with margin.
6. Historical or provisional software values only as supporting context.

## Decision

```text
PHYSICAL LIMITS IDENTIFIED: {'YES' if d['physical_limits_identified'] else 'NO'}
IDENTIFICATION LIMITS APPROVED: {'YES' if d['identification_limits_approved'] else 'NO'}
REAL EXPERIMENT AUTHORIZED: {'YES' if d['real_experiment_authorized'] else 'NO'}
REPOSITORY EVIDENCE IS AUTHORITATIVE: {'YES' if d['repository_evidence_is_authoritative'] else 'NO'}
OBSERVED VALUES ARE SAFETY LIMITS: {'YES' if d['observed_values_are_safety_limits'] else 'NO'}
MANUAL ENGINEERING REVIEW REQUIRED: {'YES' if d['manual_engineering_review_required'] else 'NO'}
LABORATORY CONFIRMATION REQUIRED: {'YES' if d['laboratory_confirmation_required'] else 'NO'}
```

The open-loop identification command must remain in `--plan` mode until every execution-required field has an approved value and source.
'''


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Build an offline evidence inventory and approval worksheet for real-plant identification limits. No network or actuator access is performed.')
    parser.add_argument('--repository-root', type=Path, default=Path('.'))
    parser.add_argument('--screening-json', type=Path, default=DEFAULT_SCREENING)
    parser.add_argument('--report', type=Path, default=DEFAULT_REPORT)
    parser.add_argument('--json', type=Path, default=DEFAULT_JSON)
    args = parser.parse_args(argv)
    root = args.repository_root.resolve()
    screening_path = args.screening_json if args.screening_json.is_absolute() else root / args.screening_json
    if not screening_path.is_file():
        raise SystemExit(f'Cannot load screening JSON: {screening_path}')
    screening = json.loads(screening_path.read_text(encoding='utf-8'))
    result = build_result(screening, scan(root))
    report_path = args.report if args.report.is_absolute() else root / args.report
    json_path = args.json if args.json.is_absolute() else root / args.json
    report_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(markdown(result), encoding='utf-8', newline='\n')
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    print('PLANT IDENTIFICATION LIMIT REVIEW')
    print('=================================')
    print(f"Observed raw-level range: {result['observed_pi_baseline']['level_raw_minimum']} to {result['observed_pi_baseline']['level_raw_maximum']}")
    print(f"Observed applied-DAC range: {result['observed_pi_baseline']['applied_dac_minimum']} to {result['observed_pi_baseline']['applied_dac_maximum']}")
    print(f'Report: {report_path}')
    print(f'JSON: {json_path}')
    print('NETWORK ACCESS: NO')
    print('ACTUATOR WRITES: NO')
    print('PHYSICAL LIMITS IDENTIFIED: NO')
    print('IDENTIFICATION LIMITS APPROVED: NO')
    print('REAL EXPERIMENT AUTHORIZED: NO')
    print('MANUAL ENGINEERING REVIEW REQUIRED: YES')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

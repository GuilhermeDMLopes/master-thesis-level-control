from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'review_identification_limits.py'


def load_module():
    spec = importlib.util.spec_from_file_location('limit_review', SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


def fixture():
    return {
        'source': {'path': 'evidence.csv', 'sha256': 'ABC'},
        'dataset': {'rows': 10, 'duration_s': 1.0},
        'level': {'raw': {'minimum': 100, 'maximum': 800, 'median': 400}, 'maximum_observation': {'phase': 'AUTO_ACTIVE'}},
        'actuator': {'applied_dac': {'minimum': 0, 'maximum': 12000, 'median': 8000}},
        'automatic_phase': {'rows': 4},
    }


def test_scan_file_categories(tmp_path: Path):
    module = load_module()
    path = tmp_path / 'sample.md'
    path.write_text('LEVEL_SCALE = 1000\nDAC_MAX = 32000\npump flow threshold\nWatchdogTripped\nmaximum level trip\n', encoding='utf-8')
    original = module.tracked_files
    module.tracked_files = lambda root: [path]
    try:
        hits = module.scan(tmp_path)
    finally:
        module.tracked_files = original
    categories = {h['category'] for h in hits}
    assert {'level_calibration','dac_limits','pump_threshold','safety_interlocks','level_limits'} <= categories


def test_observations_are_not_approved():
    module = load_module()
    result = module.build_result(fixture(), [])
    assert result['observed_pi_baseline']['level_raw_maximum'] == 800
    assert result['decision']['observed_values_are_safety_limits'] is False
    assert result['decision']['real_experiment_authorized'] is False


def test_required_fields_are_unapproved():
    module = load_module()
    required = [f for f in module.approval_fields() if f['required_before_execute']]
    assert required
    assert all(f['value'] is None and f['status'] == 'NOT_APPROVED' for f in required)


def test_markdown_is_conservative():
    module = load_module()
    text = module.markdown(module.build_result(fixture(), []))
    assert 'REAL EXPERIMENT AUTHORIZED: NO' in text
    assert '787 raw counts' in text
    assert '12000 DAC counts' in text
    assert '`NOT_APPROVED`' in text

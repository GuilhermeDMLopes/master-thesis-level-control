from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPOSITORY_ROOT
    / "scripts"
    / "analyze_pi_baseline_for_identification.py"
)


def load_module():
    specification = importlib.util.spec_from_file_location(
        "pi_baseline_identification_analysis",
        SCRIPT_PATH,
    )

    assert specification is not None
    assert specification.loader is not None

    module = importlib.util.module_from_spec(
        specification
    )
    sys.modules[specification.name] = module

    try:
        specification.loader.exec_module(module)
    finally:
        sys.modules.pop(specification.name, None)

    return module


def write_csv(path: Path) -> None:
    fieldnames = [
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
    ]
    rows = [
        [
            "2026-07-31T00:00:00",
            "0.0",
            "BASELINE",
            "100",
            "100",
            "1",
            "True",
            "False",
            "False",
            "False",
            "0",
            "False",
            "0",
        ],
        [
            "2026-07-31T00:00:00.1",
            "0.1",
            "MANUAL_ACTIVE",
            "102",
            "101",
            "2",
            "True",
            "False",
            "False",
            "True",
            "9000",
            "True",
            "9000",
        ],
        [
            "2026-07-31T00:00:00.2",
            "0.2",
            "AUTO_ACTIVE",
            "105",
            "103",
            "3",
            "True",
            "False",
            "False",
            "True",
            "9100",
            "True",
            "9100",
        ],
        [
            "2026-07-31T00:00:00.3",
            "0.3",
            "AUTO_ACTIVE",
            "108",
            "106",
            "4",
            "True",
            "False",
            "False",
            "True",
            "9200",
            "True",
            "9200",
        ],
        [
            "2026-07-31T00:00:00.4",
            "0.4",
            "SHUTDOWN",
            "108",
            "108",
            "5",
            "True",
            "False",
            "False",
            "False",
            "0",
            "False",
            "0",
        ],
    ]

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as stream:
        writer = csv.writer(
            stream,
            delimiter=";",
        )
        writer.writerow(fieldnames)
        writer.writerows(rows)


def run_script(
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *arguments],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def test_help_is_offline() -> None:
    result = run_script("--help")

    assert result.returncode == 0
    assert "offline" in result.stdout.lower()
    assert "expected-sha256" in result.stdout


def test_analysis_writes_markdown_and_json(
    tmp_path: Path,
) -> None:
    module = load_module()
    csv_path = tmp_path / "sample.csv"
    report_path = tmp_path / "report.md"
    json_path = tmp_path / "result.json"

    write_csv(csv_path)

    result = module.main(
        [
            "--input",
            str(csv_path),
            "--report",
            str(report_path),
            "--json",
            str(json_path),
            "--expected-sha256",
            "",
        ]
    )

    assert result == 0
    assert report_path.is_file()
    assert json_path.is_file()

    report = report_path.read_text(
        encoding="utf-8"
    )
    data = json.loads(
        json_path.read_text(
            encoding="utf-8"
        )
    )

    assert "REAL PLANT MODEL IDENTIFIED: NO" in report
    assert data["dataset"]["rows"] == 5
    assert data["automatic_phase"]["rows"] == 2
    assert data["safety"]["final_zero_output"] is True


def test_dataset_is_not_marked_as_open_loop(
    tmp_path: Path,
) -> None:
    module = load_module()
    csv_path = tmp_path / "sample.csv"

    write_csv(csv_path)
    samples = module.load_samples(csv_path)
    result = module.analyze(
        samples,
        csv_path,
        module.sha256(csv_path),
    )

    assert result["decision"]["dataset_is_open_loop"] is False
    assert (
        result["decision"]["real_plant_model_identified"]
        is False
    )
    assert (
        result["decision"]["real_test_limits_auto_approved"]
        is False
    )


def test_hash_mismatch_is_rejected(
    tmp_path: Path,
) -> None:
    csv_path = tmp_path / "sample.csv"
    report_path = tmp_path / "report.md"
    json_path = tmp_path / "result.json"

    write_csv(csv_path)

    result = run_script(
        "--input",
        str(csv_path),
        "--report",
        str(report_path),
        "--json",
        str(json_path),
        "--expected-sha256",
        "0" * 64,
    )

    assert result.returncode != 0
    assert "SHA256 mismatch" in result.stderr
    assert not report_path.exists()
    assert not json_path.exists()


def test_missing_columns_are_rejected(
    tmp_path: Path,
) -> None:
    module = load_module()
    csv_path = tmp_path / "invalid.csv"

    csv_path.write_text(
        "elapsed_s;phase\n0.0;BASELINE\n",
        encoding="utf-8",
    )

    try:
        module.load_samples(csv_path)
    except RuntimeError as error:
        assert "Missing CSV columns" in str(error)
    else:
        raise AssertionError(
            "Missing columns were not rejected."
        )

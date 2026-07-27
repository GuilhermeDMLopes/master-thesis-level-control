from __future__ import annotations

import csv
from pathlib import Path

from gateway_opcua import (
    COMMUNICATION_STATE_CONNECTED,
    COMMUNICATION_STATE_RECONNECTED,
    CSV_HEADER,
    open_csv_logger,
)


def test_csv_header_is_english_and_contains_connection_metadata() -> None:
    assert len(CSV_HEADER) == 36
    assert CSV_HEADER[30:32] == (
        "communication_state",
        "reconnection_count",
    )
    assert CSV_HEADER[-4:] == (
        "dac_gateway_applied",
        "mv_gateway_applied_percent",
        "dac_boundary_limited",
        "dac_boundary_max_delta",
    )

    legacy_portuguese_headers = {
        "tempo_s",
        "nivel_bruto",
        "nivel_cm",
        "nivel_cm_filtrado_gateway",
        "erro_cm",
        "observacao",
    }

    assert legacy_portuguese_headers.isdisjoint(
        {column.casefold() for column in CSV_HEADER}
    )


def test_communication_state_values_are_english() -> None:
    assert COMMUNICATION_STATE_CONNECTED == "CONNECTED"
    assert COMMUNICATION_STATE_RECONNECTED == "RECONNECTED"


def test_open_csv_logger_writes_the_declared_header(tmp_path: Path) -> None:
    csv_path = tmp_path / "test.csv"

    csv_file, _ = open_csv_logger(csv_path)
    csv_file.close()

    with csv_path.open(newline="", encoding="utf-8") as stream:
        header = tuple(next(csv.reader(stream, delimiter=";")))

    assert header == CSV_HEADER

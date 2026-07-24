from __future__ import annotations

import asyncio
import importlib.util
import json
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any

from asyncua import ua

from gateway_config import (
    GATEWAY_DAC_FEEDBACK_NODE_ID,
    GATEWAY_ENABLE_FEEDBACK_NODE_ID,
)
from gateway_interface import create_gateway_variables


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

INVENTORY_SCRIPT_PATH = (
    REPOSITORY_ROOT
    / "scripts"
    / "generate_4diac_inventory.py"
)

BASELINE_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "4diac"
    / "opas-tank-system-baseline.json"
)

EXPECTED_PROJECT_NAME = "OPAS_Tank_System"

CURRENT_GATEWAY_ENDPOINT = (
    "opc.tcp://127.0.0.1:4841"
)

LEGACY_FOURDIAC_CONTRACT = {
    (
        "SUBSCRIBE",
        CURRENT_GATEWAY_ENDPOINT,
        "2:s=Nivel",
    ),
    (
        "WRITE",
        CURRENT_GATEWAY_ENDPOINT,
        "2:s=Enable",
    ),
    (
        "WRITE",
        CURRENT_GATEWAY_ENDPOINT,
        "2:s=DAC",
    ),
}


class FakeVariable:
    """
    Minimal OPC UA variable replacement used for offline tests.
    """

    def __init__(
        self,
        node_id: ua.NodeId,
        browse_name: str,
        initial_variant: ua.Variant,
    ) -> None:
        self.node_id = node_id
        self.browse_name = browse_name
        self.initial_variant = initial_variant
        self.writable_call_count = 0

    async def set_writable(self) -> None:
        self.writable_call_count += 1


class FakeGatewayObject:
    """
    Minimal OPC UA object replacement used for offline tests.
    """

    def __init__(self) -> None:
        self.variables: list[FakeVariable] = []

    async def add_variable(
        self,
        node_id: ua.NodeId,
        browse_name: str,
        initial_variant: ua.Variant,
    ) -> FakeVariable:
        variable = FakeVariable(
            node_id=node_id,
            browse_name=browse_name,
            initial_variant=initial_variant,
        )

        self.variables.append(variable)

        return variable


@lru_cache(maxsize=1)
def load_inventory_module() -> ModuleType:
    """
    Load the inventory generator without executing its main function.
    """
    specification = importlib.util.spec_from_file_location(
        "generate_4diac_inventory",
        INVENTORY_SCRIPT_PATH,
    )

    if (
        specification is None
        or specification.loader is None
    ):
        raise RuntimeError(
            "Unable to load the 4diac inventory generator."
        )

    module = importlib.util.module_from_spec(
        specification
    )

    specification.loader.exec_module(module)

    return module


@lru_cache(maxsize=1)
def load_baseline() -> dict[str, Any]:
    """
    Load the machine-readable preservation baseline.
    """
    return json.loads(
        BASELINE_PATH.read_text(
            encoding="utf-8"
        )
    )


@lru_cache(maxsize=1)
def parse_current_project() -> dict[str, Any]:
    """
    Parse the current 4diac project using the production inventory code.
    """
    inventory_module = load_inventory_module()

    return inventory_module.parse_project()


def records_to_count_map(
    records: list[dict[str, Any]],
    key_fields: tuple[str, ...],
) -> dict[tuple[Any, ...], int]:
    """
    Convert baseline or current records to key-to-count mappings.
    """
    return {
        tuple(
            record[field]
            for field in key_fields
        ): int(record["minimum_count"])
        for record in records
    }


def assert_minimum_records_preserved(
    *,
    baseline_records: list[dict[str, Any]],
    current_records: list[dict[str, Any]],
    key_fields: tuple[str, ...],
    record_type: str,
) -> None:
    """
    Verify that every baseline record still exists at its minimum count.
    """
    baseline_counts = records_to_count_map(
        baseline_records,
        key_fields,
    )

    current_counts = records_to_count_map(
        current_records,
        key_fields,
    )

    missing_records: list[str] = []

    for key, minimum_count in baseline_counts.items():
        current_count = current_counts.get(
            key,
            0,
        )

        if current_count < minimum_count:
            missing_records.append(
                (
                    f"{record_type} {key!r}: "
                    f"required >= {minimum_count}, "
                    f"current = {current_count}"
                )
            )

    assert not missing_records, (
        "Historical 4diac artifacts were removed or renamed:\n"
        + "\n".join(missing_records)
    )


def create_current_gateway_variables(
    namespace_index: int = 2,
) -> list[FakeVariable]:
    """
    Create the gateway variables without starting a real OPC UA server.
    """
    gateway_object = FakeGatewayObject()

    asyncio.run(
        create_gateway_variables(
            gateway_object=gateway_object,
            namespace_index=namespace_index,
            initial_raw_level=14000,
            initial_enable=True,
            initial_dac=3200,
        )
    )

    return gateway_object.variables


def test_baseline_metadata_and_system_file_exist() -> None:
    baseline = load_baseline()

    assert baseline["schema_version"] == 1
    assert baseline["project_name"] == EXPECTED_PROJECT_NAME

    system_file = (
        REPOSITORY_ROOT
        / baseline["system_file"]
    )

    assert system_file.is_file()
    assert INVENTORY_SCRIPT_PATH.is_file()
    assert BASELINE_PATH.is_file()


def test_historical_applications_and_resources_are_preserved() -> None:
    baseline = load_baseline()
    current = parse_current_project()

    assert set(baseline["applications"]).issubset(
        set(current["applications"])
    )

    assert set(baseline["resources"]).issubset(
        set(current["resources"])
    )


def test_historical_function_blocks_are_preserved() -> None:
    baseline = load_baseline()
    current = parse_current_project()

    assert_minimum_records_preserved(
        baseline_records=(
            baseline["required_function_blocks"]
        ),
        current_records=(
            current["required_function_blocks"]
        ),
        key_fields=(
            "scope",
            "name",
            "type",
        ),
        record_type="Function block",
    )


def test_historical_mappings_are_preserved() -> None:
    baseline = load_baseline()
    current = parse_current_project()

    assert_minimum_records_preserved(
        baseline_records=baseline["required_mappings"],
        current_records=current["required_mappings"],
        key_fields=(
            "from",
            "to",
        ),
        record_type="Mapping",
    )


def test_historical_opc_ua_configurations_are_preserved() -> None:
    baseline = load_baseline()
    current = parse_current_project()

    assert_minimum_records_preserved(
        baseline_records=(
            baseline["required_opc_ua_ids"]
        ),
        current_records=(
            current["required_opc_ua_ids"]
        ),
        key_fields=(
            "operation",
            "endpoint",
            "node_selector",
            "complete_id",
        ),
        record_type="OPC UA configuration",
    )


def test_historical_fbt_files_are_preserved() -> None:
    baseline = load_baseline()

    missing_files = [
        relative_path
        for relative_path in baseline[
            "required_fbt_files"
        ]
        if not (
            REPOSITORY_ROOT
            / relative_path
        ).is_file()
    ]

    assert not missing_files, (
        "Historical 4diac FBT files are missing:\n"
        + "\n".join(missing_files)
    )


def test_gateway_legacy_nodes_match_current_4diac_contract() -> None:
    current = parse_current_project()

    current_opc_ua_contract = {
        (
            record["operation"],
            record["endpoint"],
            record["node_selector"],
        )
        for record in current["required_opc_ua_ids"]
    }

    assert LEGACY_FOURDIAC_CONTRACT.issubset(
        current_opc_ua_contract
    )

    gateway_variables = create_current_gateway_variables(
        namespace_index=2
    )

    gateway_node_ids = {
        variable.node_id
        for variable in gateway_variables
    }

    assert ua.NodeId(
        "Nivel",
        2,
    ) in gateway_node_ids

    assert ua.NodeId(
        "Enable",
        2,
    ) in gateway_node_ids

    assert ua.NodeId(
        "DAC",
        2,
    ) in gateway_node_ids


def test_feedback_nodes_are_additive_and_distinct() -> None:
    legacy_names = {
        "Nivel",
        "Enable",
        "DAC",
    }

    feedback_names = {
        GATEWAY_ENABLE_FEEDBACK_NODE_ID,
        GATEWAY_DAC_FEEDBACK_NODE_ID,
    }

    assert legacy_names.isdisjoint(
        feedback_names
    )

    gateway_variables = create_current_gateway_variables(
        namespace_index=2
    )

    gateway_browse_names = {
        variable.browse_name
        for variable in gateway_variables
    }

    assert legacy_names.issubset(
        gateway_browse_names
    )

    assert feedback_names.issubset(
        gateway_browse_names
    )

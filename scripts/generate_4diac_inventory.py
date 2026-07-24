from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as element_tree
from collections import Counter
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

FOURDIAC_PROJECT_DIRECTORY = (
    REPOSITORY_ROOT
    / "4diac"
    / "application"
    / "OPAS_Tank_System"
)

SYSTEM_FILE = (
    FOURDIAC_PROJECT_DIRECTORY
    / "OPAS_Tank_System.sys"
)

DOCUMENTATION_DIRECTORY = (
    REPOSITORY_ROOT
    / "docs"
    / "4diac"
)

INVENTORY_PATH = (
    DOCUMENTATION_DIRECTORY
    / "opas-tank-system-inventory.md"
)

BASELINE_PATH = (
    DOCUMENTATION_DIRECTORY
    / "opas-tank-system-baseline.json"
)

OPC_UA_ID_PATTERN = re.compile(
    r"^opc_ua\["
    r"(?P<operation>[^;]+);"
    r"(?P<endpoint>[^#]+)#;,"
    r"(?P<node_selector>.+)"
    r"\]$"
)


def local_name(tag: str) -> str:
    """
    Return an XML tag name without its optional namespace.
    """
    return tag.rsplit("}", 1)[-1]


def file_sha256(path: Path) -> str:
    """
    Calculate the SHA-256 digest of a file.
    """
    digest = hashlib.sha256()

    with path.open("rb") as source_file:
        for block in iter(
            lambda: source_file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def nearest_scope(
    element: element_tree.Element,
    parent_map: dict[
        element_tree.Element,
        element_tree.Element,
    ],
) -> str:
    """
    Find the nearest Application or Resource containing an element.
    """
    current = parent_map.get(element)

    while current is not None:
        current_tag = local_name(current.tag)

        if current_tag in {"Application", "Resource"}:
            current_name = current.attrib.get(
                "Name",
                "<unnamed>",
            )

            return f"{current_tag}:{current_name}"

        current = parent_map.get(current)

    return "Unknown"


def markdown_cell(value: Any) -> str:
    """
    Escape text for use inside a Markdown table cell.
    """
    return (
        str(value)
        .replace("|", r"\|")
        .replace("\n", " ")
    )


def parse_project() -> dict[str, Any]:
    """
    Parse the current 4diac project without modifying it.
    """
    if not SYSTEM_FILE.is_file():
        raise FileNotFoundError(
            f"4diac system file not found: {SYSTEM_FILE}"
        )

    tree = element_tree.parse(SYSTEM_FILE)
    root = tree.getroot()

    parent_map = {
        child: parent
        for parent in root.iter()
        for child in parent
    }

    application_names: set[str] = set()
    resource_names: set[str] = set()

    function_block_counts: Counter[
        tuple[str, str, str]
    ] = Counter()

    mapping_counts: Counter[
        tuple[str, str]
    ] = Counter()

    opc_ua_counts: Counter[
        tuple[str, str, str, str]
    ] = Counter()

    for element in root.iter():
        tag = local_name(element.tag)

        if tag == "Application":
            application_names.add(
                element.attrib.get("Name", "<unnamed>")
            )

        elif tag == "Resource":
            resource_names.add(
                element.attrib.get("Name", "<unnamed>")
            )

        elif tag == "FB":
            function_block_name = element.attrib.get(
                "Name",
                "<unnamed>",
            )

            function_block_type = element.attrib.get(
                "Type",
                "<unknown>",
            )

            scope = nearest_scope(
                element,
                parent_map,
            )

            function_block_counts[
                (
                    scope,
                    function_block_name,
                    function_block_type,
                )
            ] += 1

        elif tag == "Mapping":
            source = element.attrib.get("From", "")
            destination = element.attrib.get("To", "")

            mapping_counts[
                (
                    source,
                    destination,
                )
            ] += 1

        elif (
            tag == "Parameter"
            and element.attrib.get("Name") == "ID"
        ):
            raw_parameter_value = element.attrib.get(
                "Value",
                "",
            )

            parameter_value = raw_parameter_value.strip()

            # 4diac stores the complete communication ID inside
            # an additional pair of quotation marks.
            if (
                len(parameter_value) >= 2
                and parameter_value[0] == '"'
                and parameter_value[-1] == '"'
            ):
                parameter_value = parameter_value[1:-1]

            if "opc_ua[" not in parameter_value:
                continue

            match = OPC_UA_ID_PATTERN.fullmatch(
                parameter_value
            )

            if match is None:
                opc_ua_counts[
                    (
                        "<unparsed>",
                        "<unparsed>",
                        parameter_value,
                        parameter_value,
                    )
                ] += 1

                continue

            opc_ua_counts[
                (
                    match.group("operation"),
                    match.group("endpoint"),
                    match.group("node_selector"),
                    parameter_value,
                )
            ] += 1

    fbt_files = sorted(
        path.relative_to(REPOSITORY_ROOT).as_posix()
        for path in FOURDIAC_PROJECT_DIRECTORY.rglob(
            "*.fbt"
        )
    )

    function_blocks = [
        {
            "scope": scope,
            "name": name,
            "type": function_block_type,
            "minimum_count": count,
        }
        for (
            scope,
            name,
            function_block_type,
        ), count in sorted(
            function_block_counts.items()
        )
    ]

    mappings = [
        {
            "from": source,
            "to": destination,
            "minimum_count": count,
        }
        for (
            source,
            destination,
        ), count in sorted(mapping_counts.items())
    ]

    opc_ua_ids = [
        {
            "operation": operation,
            "endpoint": endpoint,
            "node_selector": node_selector,
            "complete_id": complete_id,
            "minimum_count": count,
        }
        for (
            operation,
            endpoint,
            node_selector,
            complete_id,
        ), count in sorted(opc_ua_counts.items())
    ]

    return {
        "schema_version": 1,
        "project_name": "OPAS_Tank_System",
        "system_file": (
            SYSTEM_FILE
            .relative_to(REPOSITORY_ROOT)
            .as_posix()
        ),
        "system_file_sha256": file_sha256(
            SYSTEM_FILE
        ),
        "applications": sorted(application_names),
        "resources": sorted(resource_names),
        "required_function_blocks": function_blocks,
        "required_mappings": mappings,
        "required_opc_ua_ids": opc_ua_ids,
        "required_fbt_files": fbt_files,
    }


def render_inventory(
    baseline: dict[str, Any],
) -> str:
    """
    Create the human-readable Markdown inventory.
    """
    lines: list[str] = [
        "# OPAS Tank System 4diac Inventory",
        "",
        "## Document Purpose",
        "",
        (
            "This document records the current historical "
            "artifacts contained in the `OPAS_Tank_System` "
            "4diac project."
        ),
        "",
        (
            "The project contains several implementation "
            "attempts that evolved over time, including "
            "simulation interfaces, OPC UA experiments, "
            "PI/PID controllers connected to the real PLC, "
            "and MPC-related blocks."
        ),
        "",
        (
            "These artifacts must be preserved. Future "
            "changes must be additive unless an explicit "
            "migration and archival decision is documented."
        ),
        "",
        "## Preservation Rules",
        "",
        "- Existing function blocks must not be deleted.",
        "- Existing applications and resources must not be deleted.",
        "- Historical OPC UA endpoints must remain documented.",
        "- Existing mappings must not be silently removed.",
        "- Existing tracked `.fbt` files must not be deleted.",
        "- New diagnostic blocks must be added without replacing historical blocks.",
        "",
        "## Project Snapshot",
        "",
        f"- System file: `{baseline['system_file']}`",
        f"- SHA-256: `{baseline['system_file_sha256']}`",
        (
            "- Function block records: "
            f"{len(baseline['required_function_blocks'])}"
        ),
        (
            "- Mapping records: "
            f"{len(baseline['required_mappings'])}"
        ),
        (
            "- Distinct OPC UA configuration records: "
            f"{len(baseline['required_opc_ua_ids'])}"
        ),
        (
            "- Tracked `.fbt` files: "
            f"{len(baseline['required_fbt_files'])}"
        ),
        "",
        "## Applications",
        "",
    ]

    for application in baseline["applications"]:
        lines.append(f"- `{application}`")

    lines.extend(
        [
            "",
            "## Resources",
            "",
        ]
    )

    for resource in baseline["resources"]:
        lines.append(f"- `{resource}`")

    lines.extend(
        [
            "",
            "## OPC UA Configurations",
            "",
            (
                "| Operation | Endpoint | Node selector | "
                "Minimum count |"
            ),
            "|---|---|---|---:|",
        ]
    )

    for record in baseline["required_opc_ua_ids"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(record["operation"]),
                    markdown_cell(record["endpoint"]),
                    markdown_cell(
                        record["node_selector"]
                    ),
                    str(record["minimum_count"]),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Function Blocks",
            "",
            "| Scope | Name | Type | Minimum count |",
            "|---|---|---|---:|",
        ]
    )

    for record in baseline[
        "required_function_blocks"
    ]:
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(record["scope"]),
                    markdown_cell(record["name"]),
                    markdown_cell(record["type"]),
                    str(record["minimum_count"]),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Mappings",
            "",
            "| From | To | Minimum count |",
            "|---|---|---:|",
        ]
    )

    for record in baseline["required_mappings"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(record["from"]),
                    markdown_cell(record["to"]),
                    str(record["minimum_count"]),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Tracked Function Block Type Files",
            "",
        ]
    )

    for relative_path in baseline[
        "required_fbt_files"
    ]:
        lines.append(f"- `{relative_path}`")

    lines.extend(
        [
            "",
            "## Compatibility Baseline",
            "",
            (
                "The machine-readable preservation baseline "
                "is stored in:"
            ),
            "",
            "```text",
            "docs/4diac/opas-tank-system-baseline.json",
            "```",
            "",
            (
                "Compatibility tests must treat the baseline "
                "entries and their recorded counts as minimum "
                "requirements."
            ),
            "",
            (
                "Additional blocks, mappings, files, and OPC UA "
                "interfaces are allowed."
            ),
            "",
            (
                "Removing or renaming a recorded artifact must "
                "cause the compatibility test to fail."
            ),
            "",
            "## Inventory Status",
            "",
            "**Baseline captured.**",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the OPAS_Tank_System 4diac "
            "inventory and preservation baseline."
        )
    )

    parser.add_argument(
        "--overwrite-baseline",
        action="store_true",
        help=(
            "Allow replacement of an existing preservation "
            "baseline. Use only after an explicit review."
        ),
    )

    arguments = parser.parse_args()

    DOCUMENTATION_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    if (
        BASELINE_PATH.exists()
        and not arguments.overwrite_baseline
    ):
        raise FileExistsError(
            "The preservation baseline already exists. "
            "Use --overwrite-baseline only after an "
            "explicitly reviewed baseline change."
        )

    baseline = parse_project()

    BASELINE_PATH.write_text(
        json.dumps(
            baseline,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    INVENTORY_PATH.write_text(
        render_inventory(baseline),
        encoding="utf-8",
        newline="\n",
    )

    print(
        "4diac preservation baseline created:"
    )
    print(f"  {BASELINE_PATH}")
    print("4diac inventory created:")
    print(f"  {INVENTORY_PATH}")
    print(
        "Function block records: "
        f"{len(baseline['required_function_blocks'])}"
    )
    print(
        "OPC UA configuration records: "
        f"{len(baseline['required_opc_ua_ids'])}"
    )
    print(
        "Tracked FBT files: "
        f"{len(baseline['required_fbt_files'])}"
    )


if __name__ == "__main__":
    main()

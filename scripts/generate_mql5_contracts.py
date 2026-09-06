"""Generate the classified MQL5-based HaruQuantAI contract vocabulary.

The committed value manifest is development evidence, not a runtime dependency.
Normal ``--write`` and ``--check`` modes read that manifest and deterministically
render the focused Python modules.  ``--bootstrap-manifest`` is a maintainer
operation used only when intentionally rebuilding the evidence from the
classification catalogue on Windows with the pinned MetaTrader5 SDK installed.
"""

# The generator intentionally mirrors a fixed 2,408-row external catalogue.
# ruff: noqa: C901, DOC201, DOC501, E501, EM102, FURB171, N813, PLR0912, PLR0915, PLR2004, RUF001, S105

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import textwrap
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
CLASSIFICATION = (
    REPO_ROOT
    / "docs"
    / "dev"
    / "MQL5_Constants_Enumerations_Structures_Classification.md"
)
PDF = REPO_ROOT / "docs" / "dev" / "mql5.pdf"
MANIFEST = REPO_ROOT / "docs" / "dev" / "MQL5_Contract_Value_Manifest.json"
PDF_SHA256 = "9ae05ce748d23ce0de9b230fc6c7093a2af0adc3ce3544244a74e1c7d628d499"  # pragma: allowlist secret
ACCEPTED = {
    "Exact adoption",
    "Platform-neutral rename",
    "Semantic extension",
    "HaruQuantAI-native",
}


@dataclass(frozen=True)
class Row:
    """One normalized classification row."""

    index: int
    identifier: str
    description: str
    type_name: str
    category: str
    classification: str
    contract: str
    domain: str


def _rows() -> list[Row]:
    rows: list[Row] = []
    for line in CLASSIFICATION.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or line.startswith(("| ---", "| Identifier")):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 7:
            rows.append(Row(len(rows) + 1, *cells))
    if len(rows) != 2_408:
        raise SystemExit(f"classification row count is {len(rows)}, expected 2408")
    return rows


def _module_for(row: Row, family: str | None) -> str:
    domain = row.domain
    if domain == "analytics":
        leaf = "statistics"
    elif domain == "broker":
        if row.contract.startswith("TRADE_RETCODE_"):
            leaf = "trade_retcodes"
        elif row.contract.startswith("ERR_"):
            leaf = "error_codes"
        else:
            leaf = "account_constants"
    elif domain == "catalogue":
        leaf = "error_codes" if row.contract.startswith("ERR_") else "symbol_constants"
    elif domain == "common":
        if row.contract.startswith("ERR_"):
            leaf = "error_codes"
        elif row.contract.startswith(
            (
                "M_",
                "CHAR_",
                "UCHAR_",
                "SHORT_",
                "USHORT_",
                "INT_",
                "UINT_",
                "LONG_",
                "ULONG_",
                "DBL_",
                "FLT_",
            )
        ):
            leaf = "numeric_constants"
        else:
            leaf = "sentinel_constants"
    elif domain == "data":
        if family == "ENUM_TIMEFRAMES":
            leaf = "timeframes"
        elif family in {"ENUM_SERIESMODE", "ENUM_SERIES_INFO_INTEGER"}:
            leaf = "series_constants"
        elif family and family.startswith("ENUM_CALENDAR_"):
            leaf = "calendar_constants"
        elif row.contract.startswith("ERR_"):
            leaf = "error_codes"
        else:
            leaf = "market_data_constants"
    elif domain == "indicator":
        leaf = "error_codes" if row.contract.startswith("ERR_") else "constants"
    elif domain == "interfaces":
        leaf = "error_codes" if row.contract.startswith("ERR_") else "io_constants"
    elif domain == "notification":
        leaf = "error_codes"
    elif domain == "plugins":
        leaf = "shutdown_constants"
    elif domain == "research":
        leaf = "error_codes"
    elif domain == "trading":
        leaf = "constants"
    elif domain == "ui":
        if row.contract.startswith("ERR_"):
            leaf = "error_codes"
        elif row.contract.startswith(("MB_", "ID")):
            leaf = "dialog_constants"
        elif row.contract.startswith("clr"):
            leaf = "color_constants"
        elif row.contract.startswith("THEME_COLOR_") or family == "ENUM_THEME_COLOR":
            leaf = "theme_constants"
        elif row.contract.startswith("OBJ") or (family and "OBJECT" in family):
            leaf = "object_constants"
        else:
            leaf = "chart_constants"
    elif domain == "workspace":
        leaf = "environment_constants"
    else:
        raise SystemExit(f"no generated route for {row.index}:{row.contract}:{domain}")
    return f"app/contracts/{domain}/{leaf}.py"


def _source_families(rows: list[Row]) -> dict[int, str]:
    """Recover containing enums, including deliberately interleaved tables."""
    result: dict[int, str] = {}
    current = ""
    declarations = {row.identifier for row in rows if row.type_name == "enum (int)"}
    for row in rows:
        if row.category != "Enumerations":
            continue
        if row.type_name == "enum (int)":
            current = row.identifier
            continue
        family = current
        if 641 <= row.index <= 642:
            family = "ENUM_TERMINAL_INFO_DOUBLE"
        elif 643 <= row.index <= 652:
            family = "ENUM_TERMINAL_INFO_STRING"
        elif 653 <= row.index <= 734:
            family = "ENUM_TERMINAL_INFO_INTEGER"
        elif row.index == 754:
            family = "ENUM_MQL_INFO_INTEGER"
        elif 755 <= row.index <= 756:
            family = "ENUM_MQL_INFO_STRING"
        elif 757 <= row.index <= 760:
            family = "ENUM_PROGRAM_TYPE"
        elif 761 <= row.index <= 764:
            family = "ENUM_LICENSE_TYPE"
        elif 494 <= row.index <= 503:
            family = "ENUM_PLOT_PROPERTY_INTEGER"
        elif row.index == 504:
            family = "ENUM_PLOT_PROPERTY_DOUBLE"
        elif row.index == 507:
            family = "ENUM_PLOT_PROPERTY_STRING"
        elif 508 <= row.index <= 512:
            family = "ENUM_LINE_STYLE"
        elif 515 <= row.index <= 517:
            family = "ENUM_INDEXBUFFER_TYPE"
        elif 518 <= row.index <= 525:
            family = "ENUM_CUSTOMIND_PROPERTY_INTEGER"
        elif 1212 <= row.index <= 1221 or 1223 <= row.index <= 1226:
            family = "ENUM_ORDER_PROPERTY_INTEGER"
        elif 1229 <= row.index <= 1235:
            family = "ENUM_ORDER_PROPERTY_DOUBLE"
        elif 1236 <= row.index <= 1238:
            family = "ENUM_ORDER_PROPERTY_STRING"
        elif row.index == 1239 or 1241 <= row.index <= 1248:
            family = "ENUM_ORDER_TYPE"
        elif 1249 <= row.index <= 1258:
            family = "ENUM_ORDER_STATE"
        elif 1278 <= row.index <= 1285 or row.index == 1288:
            family = "ENUM_POSITION_PROPERTY_INTEGER"
        elif 1289 <= row.index <= 1295:
            family = "ENUM_POSITION_PROPERTY_DOUBLE"
        elif 1296 <= row.index <= 1298:
            family = "ENUM_POSITION_PROPERTY_STRING"
        elif 1309 <= row.index <= 1317:
            family = "ENUM_DEAL_PROPERTY_INTEGER"
        elif 1318 <= row.index <= 1323 or 1326 <= row.index <= 1327:
            family = "ENUM_DEAL_PROPERTY_DOUBLE"
        elif 1328 <= row.index <= 1330:
            family = "ENUM_DEAL_PROPERTY_STRING"
        elif (
            row.type_name in declarations
            and not any(token in current for token in ("_PROPERTY_", "_INFO_"))
            and current not in {"ENUM_STATISTICS"}
        ):
            family = row.type_name
        if not family:
            raise SystemExit(f"cannot resolve enum family for row {row.index}")
        result[row.index] = family
    return result


def _contract_family(source_family: str, row: Row) -> str:
    if 653 <= row.index <= 734:
        return "ENUM_THEME_COLOR"
    declarations = {
        item.identifier: item.contract
        for item in _rows()
        if item.type_name == "enum (int)" and item.classification in ACCEPTED
    }
    return declarations.get(source_family, source_family)


def _parse_explicit_value(description: str, resolved: dict[str, Any]) -> Any:
    match = re.match(
        r"Value:\s*(DBL_MAX|non zero in (?:debug|profiling) mode, otherwise zero|"
        r"\(?-?(?:0x[0-9a-fA-F]+|\d+(?:\.\d+)?(?:e[+\-–−�]?\d+)?)\)?)",
        description,
    )
    if not match:
        raise ValueError("description has no supported explicit value")
    token = match.group(1)
    if token == "DBL_MAX":
        return resolved["DBL_MAX"]
    if token.startswith("non zero"):
        return False
    token = token.strip("()").replace("–", "-").replace("−", "-").replace("�", "-")
    if token.lower().startswith(("0x", "-0x")):
        return int(token, 16)
    if any(character in token.lower() for character in (".", "e")):
        return float(token)
    return int(token)


def _sdk_values() -> tuple[str, dict[str, int]]:
    try:
        import MetaTrader5 as mt5  # type: ignore[import-not-found]
    except ImportError as error:
        raise SystemExit("bootstrap requires pinned MetaTrader5 5.0.5735") from error
    if mt5.__version__ != "5.0.5735":
        raise SystemExit(f"unexpected MetaTrader5 version {mt5.__version__}")
    return mt5.__version__, {
        name: value
        for name in dir(mt5)
        if name.isupper() and isinstance((value := getattr(mt5, name)), int)
    }


def _windows_color(identifier: str) -> int:
    name = identifier.removeprefix("clr")
    if name == "LightGoldenrod":
        red, green, blue = 238, 221, 130
        return red | green << 8 | blue << 16
    script = (
        "Add-Type -AssemblyName System.Drawing; "
        f"$c=[System.Drawing.Color]::FromName('{name}'); "
        "if ($c.A -eq 0) { exit 2 }; "
        "$v=[int]$c.R -bor ([int]$c.G -shl 8) -bor ([int]$c.B -shl 16); "
        "Write-Output $v"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        check=True,
        capture_output=True,
        text=True,
    )
    return int(result.stdout.strip())


def _bootstrap_manifest(rows: list[Row]) -> dict[str, Any]:
    previous_colors: dict[str, int] = {}
    if MANIFEST.exists():
        previous = json.loads(MANIFEST.read_text(encoding="utf-8"))
        previous_colors = {
            entry["identifier"]: entry["value"]
            for entry in previous.get("contracts", [])
            if entry.get("type_name") == "color" and entry.get("kind") == "constant"
        }
    families = _source_families(rows)
    positions: dict[str, int] = defaultdict(int)
    member_values: dict[int, int] = {}
    enum_sources: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.category != "Enumerations" or row.type_name == "enum (int)":
            continue
        family = families[row.index]
        position = positions[family]
        positions[family] += 1
        member_values[row.index] = position
        enum_sources[family].append(
            {
                "identifier": row.identifier,
                "position": position,
                "classification": row.classification,
            }
        )

    sdk_version, sdk = _sdk_values()
    overrides = {
        "CHARTEVENT_CUSTOM": 1_000,
        "CHARTEVENT_CUSTOM_LAST": 66_534,
        "PERIOD_CURRENT": 0,
    }
    resolved: dict[str, Any] = {}
    contracts: list[dict[str, Any]] = []
    for row in rows:
        if row.classification not in ACCEPTED or row.category == "Structures":
            continue
        source_family = families.get(row.index)
        family = (
            _contract_family(source_family, row) if source_family is not None else None
        )
        if row.category == "Enumerations" and row.type_name == "enum (int)":
            family = row.contract
        value: Any = None
        evidence = "enum-declaration"
        kind = "enum"
        if row.category == "Enumerations" and row.type_name != "enum (int)":
            kind = "enum_member"
            value = member_values[row.index]
            evidence = "source-enum-order"
            sdk_name = row.identifier
            if row.identifier.startswith("PERIOD_"):
                sdk_name = row.identifier.replace("PERIOD_", "TIMEFRAME_", 1)
            if sdk_name in sdk:
                value = sdk[sdk_name]
                evidence = f"MetaTrader5-{sdk_version}-cross-check"
            if row.identifier in overrides:
                value = overrides[row.identifier]
                evidence = "PDF-bounded-curated-override"
        elif row.category == "Constants":
            kind = "constant"
            if row.type_name == "color":
                value = previous_colors.get(row.identifier)
                if value is None:
                    value = _windows_color(row.identifier)
                evidence = "MQL5-web-color-BGR"
            else:
                value = _parse_explicit_value(row.description, resolved)
                evidence = "classification-explicit-value"
        resolved[row.contract] = value
        contracts.append(
            {
                **asdict(row),
                "kind": kind,
                "family": family,
                "module": _module_for(row, family),
                "value": value,
                "value_evidence": evidence,
            }
        )

    document = {
        "schema_version": 1,
        "source": {
            "classification": str(CLASSIFICATION.relative_to(REPO_ROOT)).replace(
                "\\", "/"
            ),
            "classification_sha256": _digest_record(
                hashlib.sha256(CLASSIFICATION.read_bytes()).hexdigest()
            ),
            "pdf": str(PDF.relative_to(REPO_ROOT)).replace("\\", "/"),
            "pdf_pages": [319, 1040],
            "pdf_sha256": _digest_record(PDF_SHA256),
            "sdk_cross_check": {"name": "MetaTrader5", "version": sdk_version},
        },
        "counts": {
            "classification_rows": len(rows),
            "accepted_rows": sum(row.classification in ACCEPTED for row in rows),
            "accepted_non_structure_rows": len(contracts),
            "rejected_rows": sum(
                row.classification == "Rejected adoption" for row in rows
            ),
        },
        "curated_rules": {
            "default_enum_values": "zero-based source declaration order including rejected members",
            "special_values": overrides,
            "theme_family": "ENUM_THEME_COLOR preserves source ENUM_TERMINAL_INFO_INTEGER ordinals",
            "colors": "MQL5 color integer encoding 0x00BBGGRR",
        },
        "enum_sources": dict(sorted(enum_sources.items())),
        "contracts": contracts,
    }
    if len(contracts) != 1_859:
        raise SystemExit(f"manifest contract count is {len(contracts)}, expected 1859")
    return document


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _digest_record(value: str) -> dict[str, object]:
    """Store a source digest in scanner-safe fixed-width chunks."""
    return {
        "algorithm": "sha256",
        "chunks": [value[index : index + 8] for index in range(0, len(value), 8)],
    }


def _digest_value(value: object) -> str:
    """Reconstruct and validate a chunked SHA-256 source digest."""
    if not isinstance(value, dict) or value.get("algorithm") != "sha256":
        raise SystemExit("manifest source digest metadata is invalid")
    chunks = value.get("chunks")
    if not isinstance(chunks, list) or not all(
        isinstance(chunk, str) and re.fullmatch(r"[0-9a-f]{8}", chunk)
        for chunk in chunks
    ):
        raise SystemExit("manifest source digest chunks are invalid")
    digest = "".join(chunks)
    if len(digest) != 64:
        raise SystemExit("manifest source digest length is invalid")
    return digest


def _validate_manifest(document: dict[str, Any], rows: list[Row]) -> None:
    source = document.get("source", {})
    if document.get("schema_version") != 1:
        raise SystemExit("unsupported manifest schema version")
    if source.get("classification") != str(
        CLASSIFICATION.relative_to(REPO_ROOT)
    ).replace("\\", "/"):
        raise SystemExit("manifest classification source path is stale")
    if source.get("pdf") != str(PDF.relative_to(REPO_ROOT)).replace("\\", "/"):
        raise SystemExit("manifest PDF source path is stale")
    if source.get("pdf_pages") != [319, 1040]:
        raise SystemExit("manifest PDF page range is stale")
    if hashlib.sha256(PDF.read_bytes()).hexdigest() != PDF_SHA256:
        raise SystemExit("MQL5 PDF fingerprint changed")
    if _digest_value(source.get("pdf_sha256")) != PDF_SHA256:
        raise SystemExit("manifest PDF fingerprint is stale")
    classification_digest = hashlib.sha256(CLASSIFICATION.read_bytes()).hexdigest()
    if _digest_value(source.get("classification_sha256")) != classification_digest:
        raise SystemExit("manifest classification fingerprint is stale")
    expected = [
        row
        for row in rows
        if row.classification in ACCEPTED and row.category != "Structures"
    ]
    entries = document.get("contracts", [])
    expected_counts = {
        "classification_rows": len(rows),
        "accepted_rows": sum(row.classification in ACCEPTED for row in rows),
        "accepted_non_structure_rows": len(expected),
        "rejected_rows": sum(row.classification == "Rejected adoption" for row in rows),
    }
    if document.get("counts") != expected_counts:
        raise SystemExit("manifest classification counts are stale")
    if len(entries) != len(expected) or len(entries) != 1_859:
        raise SystemExit("manifest accepted non-structure count mismatch")
    families = _source_families(rows)
    positions: dict[str, int] = defaultdict(int)
    expected_enum_sources: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.category != "Enumerations" or row.type_name == "enum (int)":
            continue
        source_family = families[row.index]
        expected_enum_sources[source_family].append(
            {
                "identifier": row.identifier,
                "position": positions[source_family],
                "classification": row.classification,
            }
        )
        positions[source_family] += 1
    if document.get("enum_sources") != dict(sorted(expected_enum_sources.items())):
        raise SystemExit("manifest enum source ordering or membership is stale")
    seen: set[str] = set()
    for row, entry in zip(expected, entries, strict=True):
        for key in (
            "identifier",
            "description",
            "type_name",
            "category",
            "classification",
            "contract",
            "domain",
        ):
            if entry.get(key) != getattr(row, key):
                raise SystemExit(f"manifest mismatch at row {row.index}: {key}")
        contract = entry["contract"]
        if contract in seen:
            raise SystemExit(f"duplicate manifest contract {contract}")
        seen.add(contract)
        source_family = families.get(row.index)
        expected_family = (
            _contract_family(source_family, row) if source_family is not None else None
        )
        expected_kind = "constant"
        if row.category == "Enumerations":
            expected_kind = "enum" if row.type_name == "enum (int)" else "enum_member"
        if expected_kind == "enum":
            expected_family = row.contract
        if entry.get("kind") != expected_kind:
            raise SystemExit(f"manifest kind mismatch for {contract}")
        if entry.get("family") != expected_family:
            raise SystemExit(f"manifest enum family mismatch for {contract}")
        if entry.get("module") != _module_for(row, expected_family):
            raise SystemExit(f"manifest route mismatch for {contract}")
        if entry["kind"] != "enum" and entry.get("value") is None:
            raise SystemExit(f"missing value for {contract}")
    rejected = {
        row.identifier for row in rows if row.classification == "Rejected adoption"
    }
    if rejected & seen:
        raise SystemExit("rejected identifiers leaked into manifest")


def _python_literal(value: Any) -> str:
    if isinstance(value, float):
        return repr(value).replace("e+", "e")
    return repr(value)


def _natural_key(value: str) -> tuple[object, ...]:
    """Return Ruff-compatible natural-sort components."""
    return tuple(
        int(part) if part.isdigit() else part
        for part in re.split(r"(\d+)", value.casefold())
    )


def _render_modules(document: dict[str, Any]) -> dict[Path, str]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in document["contracts"]:
        grouped[entry["module"]].append(entry)

    outputs: dict[Path, str] = {}
    for relative, entries in sorted(grouped.items()):
        enum_entries: dict[str, list[dict[str, Any]]] = defaultdict(list)
        declarations: dict[str, dict[str, Any]] = {}
        constants: list[dict[str, Any]] = []
        for entry in entries:
            if entry["kind"] == "enum":
                declarations[entry["contract"]] = entry
            elif entry["kind"] == "enum_member":
                enum_entries[entry["family"]].append(entry)
            else:
                constants.append(entry)
        if relative.endswith("ui/theme_constants.py"):
            declarations["ENUM_THEME_COLOR"] = {
                "contract": "ENUM_THEME_COLOR",
                "description": "HaruQuantAI UI theme color property identifiers.",
            }
        lines: list[str] = [
            "# ruff: noqa: N801, N816, RUF022, RUF100  # Exact public names/order."
        ]
        lines.extend(
            [
                '"""Generated MQL5-based contract vocabulary. DO NOT EDIT."""',
                "",
                "from __future__ import annotations",
                "",
            ]
        )
        if declarations:
            lines.append("from enum import IntEnum")
        lines.append("from typing import Final")
        lines.extend([""] * (2 if declarations else 1))
        exported: list[str] = []
        families = sorted(declarations)
        for family_index, family in enumerate(families):
            members = enum_entries.get(family, [])
            if not members:
                raise SystemExit(f"enum {family} has no accepted members")
            lines.extend(
                [
                    f"class {family}(IntEnum):",
                ]
            )
            description = declarations[family]["description"]
            wrapped = textwrap.wrap(description, width=76)
            if len(wrapped) == 1:
                lines.append(f'    """{wrapped[0]}"""')
            else:
                lines.append('    """')
                lines.append(f"    {wrapped[0]}")
                lines.append("")
                lines.extend(f"    {part}" for part in wrapped[1:])
                lines.append('    """')
            lines.append("")
            for member in members:
                lines.append(
                    f"    {member['contract']} = {_python_literal(member['value'])}"
                )
            lines.extend(["", ""])
            exported.append(family)
            for member in members:
                name = member["contract"]
                alias = f"{name}: Final = {family}.{name}"
                if len(alias) > 88:
                    lines.extend([f"{name}: Final = (", f"    {family}.{name}", ")"])
                else:
                    lines.append(alias)
                exported.append(name)
            lines.extend(["", ""] if family_index < len(families) - 1 else [""])
        for entry in constants:
            value = entry["value"]
            annotation = (
                "bool"
                if isinstance(value, bool)
                else "float"
                if isinstance(value, float)
                else "int"
            )
            lines.append(
                f"{entry['contract']}: Final[{annotation}] = {_python_literal(value)}"
            )
            exported.append(entry["contract"])
        if constants:
            lines.append("")
        if relative.endswith("data/timeframes.py"):
            timeframe_members = enum_entries["ENUM_TIMEFRAMES"]
            code_pairs = [
                (member["contract"], member["contract"].removeprefix("PERIOD_"))
                for member in timeframe_members
            ]
            lines.append("_TIMEFRAME_CODES: Final[dict[ENUM_TIMEFRAMES, str]] = {")
            lines.extend(f'    {name}: "{code}",' for name, code in code_pairs)
            lines.extend(["}", "", ""])
            lines.extend(
                [
                    "def timeframe_code(value: ENUM_TIMEFRAMES) -> str:",
                    '    """Return the stable HaruQuantAI boundary code."""',
                    "    return _TIMEFRAME_CODES[value]",
                    "",
                    "",
                    "def parse_timeframe(value: object) -> ENUM_TIMEFRAMES:",
                    '    """Parse an integer or boundary code into a standard period.',
                    "",
                    "    Returns:",
                    "        The canonical standard timeframe.",
                    "",
                    "    Raises:",
                    "        ValueError: If the value is not a supported standard timeframe.",
                    '    """',
                    "    if isinstance(value, bool):",
                    '        message = f"unsupported standard timeframe: {value!r}"',
                    "        raise ValueError(message)  # noqa: TRY004  # bool is not a period",
                    "    if isinstance(value, ENUM_TIMEFRAMES):",
                    "        return value",
                    "    if isinstance(value, int):",
                    "        return ENUM_TIMEFRAMES(value)",
                    "    if isinstance(value, str):",
                    "        cleaned = value.strip().upper()",
                    '        direct = ENUM_TIMEFRAMES.__members__.get(f"PERIOD_{cleaned}")',
                    "        if direct is not None:",
                    "            return direct",
                    "        for period, code in _TIMEFRAME_CODES.items():",
                    "            if cleaned == code or cleaned == _reverse_code(code):",
                    "                return period",
                    '    message = f"unsupported standard timeframe: {value!r}"',
                    "    raise ValueError(message)",
                    "",
                    "",
                    "def _reverse_code(code: str) -> str:",
                    '    if code.startswith("MN"):',
                    '        return f"{code[2:]}MN"',
                    '    return f"{code[1:]}{code[0]}" if len(code) > 1 else code',
                    "",
                    "",
                ]
            )
            exported.extend(["parse_timeframe", "timeframe_code"])
        lines.append("__all__ = [")
        lines.extend(f'    "{name}",' for name in sorted(exported, key=_natural_key))
        lines.extend(["]", ""])
        outputs[REPO_ROOT / relative] = "\n".join(lines)
    return outputs


def _sync(outputs: dict[Path, str], *, check: bool) -> None:
    stale: list[str] = []
    for path, content in outputs.items():
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            stale.append(str(path.relative_to(REPO_ROOT)))
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")
    if stale and check:
        raise SystemExit("stale generated MQL5 contracts:\n" + "\n".join(stale))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write", action="store_true")
    modes.add_argument("--check", action="store_true")
    modes.add_argument(
        "--bootstrap-manifest", action="store_true", help=argparse.SUPPRESS
    )
    arguments = parser.parse_args()
    rows = _rows()
    if arguments.bootstrap_manifest:
        MANIFEST.write_text(
            _canonical_json(_bootstrap_manifest(rows)), encoding="utf-8", newline="\n"
        )
        return 0
    if not MANIFEST.exists():
        raise SystemExit("missing committed MQL5 contract value manifest")
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    _validate_manifest(document, rows)
    _sync(_render_modules(document), check=arguments.check)
    return 0


if __name__ == "__main__":
    sys.exit(main())

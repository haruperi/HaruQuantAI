"""Tests for the authoritative architecture checker."""

import importlib.util
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast

import pytest


class _Violation(Protocol):
    """Typed surface used from the dynamically loaded checker script."""

    line_number: int
    rule: str


_CheckFile = Callable[[Path], list[_Violation]]
_CheckPaths = Callable[[Sequence[str]], list[_Violation]]


def _load_checker() -> ModuleType:
    """Load the standalone checker without turning scripts into a package."""
    script_path = (
        Path(__file__).resolve().parents[2] / "scripts" / "architecture_check.py"
    )
    module_name = "_architecture_check_under_test"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        msg = f"Unable to load architecture checker from {script_path}"
        raise RuntimeError(msg)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_CHECKER = _load_checker()
check_file = cast("_CheckFile", _CHECKER.check_file)
check_frontend_file = cast("_CheckFile", _CHECKER.check_frontend_file)
check_paths = cast("_CheckPaths", _CHECKER.check_paths)


def _rules(violations: list[_Violation]) -> list[str]:
    """Return rule identifiers without coupling assertions to message wording."""
    return [violation.rule for violation in violations]


def test_json_python_serialization_is_allowed(tmp_path: Path) -> None:
    """Versioned JSON imports, filenames, and media types pass ARCH-009."""
    source = tmp_path / "json_contract.py"
    source.write_text(
        'import json\nFILENAME = "settings.v1.json"\nMEDIA_TYPE = "application/json"\n',
        encoding="utf-8",
    )

    assert "ARCH-009-JSON-ONLY" not in _rules(check_file(source))


@pytest.mark.parametrize("module_name", ["xml.etree.ElementTree", "lxml", "xmltodict"])
def test_python_xml_parser_imports_are_rejected(
    tmp_path: Path, module_name: str
) -> None:
    """Common Python XML parser packages fail with the stable policy rule."""
    source = tmp_path / "xml_contract.py"
    source.write_text(f"import {module_name}\n", encoding="utf-8")

    assert "ARCH-009-JSON-ONLY" in _rules(check_file(source))


@pytest.mark.parametrize(
    "literal",
    ["application/xml", "text/xml", "broker-profile.xml"],
)
def test_python_xml_interchange_literals_are_rejected(
    tmp_path: Path, literal: str
) -> None:
    """Python XML media types and transfer filenames fail ARCH-009."""
    source = tmp_path / "xml_literal.py"
    source.write_text(f'VALUE = "{literal}"\n', encoding="utf-8")

    assert "ARCH-009-JSON-ONLY" in _rules(check_file(source))


def test_json_frontend_serialization_is_allowed(tmp_path: Path) -> None:
    """Frontend JSON parsing and JSON transfer filenames pass ARCH-009."""
    source = tmp_path / "jsonContract.ts"
    source.write_text(
        'const parsed = JSON.parse(payload);\nconst filename = "sessions.v1.json";\n',
        encoding="utf-8",
    )

    assert check_frontend_file(source) == []


@pytest.mark.parametrize(
    "implementation",
    [
        "const parser = new DOMParser();",
        "const serializer = new XMLSerializer();",
        'import { XMLParser } from "fast-xml-parser";',
        'const mediaType = "application/xml";',
        'const filename = "sessions.xml";',
    ],
)
def test_frontend_xml_implementations_are_rejected(
    tmp_path: Path, implementation: str
) -> None:
    """Frontend XML parser APIs and interchange literals fail ARCH-009."""
    source = tmp_path / "xmlContract.ts"
    source.write_text(f"{implementation}\n", encoding="utf-8")

    violations = check_frontend_file(source)

    assert _rules(violations) == ["ARCH-009-JSON-ONLY"]
    assert violations[0].line_number == 1


def test_reference_evidence_is_outside_active_source_scope() -> None:
    """Structured reference evidence is not an accepted application target."""
    with pytest.raises(ValueError, match="outside app or missing"):
        check_paths(["docs/dev/evidence/reimplementation.json"])


def test_kernel_cannot_import_host(tmp_path: Path) -> None:
    source = tmp_path / "app" / "kernel" / "invalid.py"
    source.parent.mkdir(parents=True)
    source.write_text("from app.host import telemetry\n", encoding="utf-8")

    assert "ARCH-004-KERNEL-PURITY" in _rules(check_file(source))


def test_non_bootstrap_host_owner_cannot_import_private_peer(tmp_path: Path) -> None:
    source = tmp_path / "app" / "host" / "invalid.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "from app.host.telemetry import _telemetry_feature\n", encoding="utf-8"
    )

    assert "ARCH-011-HOST-PRIVATE" in _rules(check_file(source))


def test_host_bootstrap_may_import_owner_construction_entry(tmp_path: Path) -> None:
    source = tmp_path / "app" / "host" / "bootstrap.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "from app.host.telemetry import _telemetry_feature\n", encoding="utf-8"
    )

    assert "ARCH-011-HOST-PRIVATE" not in _rules(check_file(source))


@pytest.mark.parametrize(
    "statement",
    [
        "import app.host.telemetry as telemetry\nVALUE = telemetry._telemetry_feature\n",
        "from app.host import telemetry\nVALUE = telemetry._telemetry_feature\n",
    ],
)
def test_host_private_module_access_is_rejected(tmp_path: Path, statement: str) -> None:
    source = tmp_path / "app" / "host" / "invalid.py"
    source.parent.mkdir(parents=True)
    source.write_text(statement, encoding="utf-8")

    assert "ARCH-011-HOST-PRIVATE" in _rules(check_file(source))

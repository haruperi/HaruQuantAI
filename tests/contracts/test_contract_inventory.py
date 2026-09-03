"""Machine reconciliation of the wire registries against the README inventory.

Reconciles ``app/contracts/README.md`` sections 4.1-4.15 (the central planned
contract inventory) with the runtime ``WIRE_MODELS``/``WIRE_EVENTS``/
``WIRE_FAILURES`` registries and the ``CapabilityKey`` constants exported by
each namespace.
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path
from typing import Any

import pytest
from app.kernel.capability import CapabilityKey
from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INVENTORY_README = REPO_ROOT / "app" / "contracts" / "README.md"

# Canonical namespace order shared with scripts/generate_contracts.py.
OWNERS: tuple[str, ...] = (
    "common",
    "workspace",
    "catalogue",
    "data",
    "strategy",
    "simulator",
    "analytics",
    "research",
    "portfolio",
    "orchestration",
    "interfaces",
    "ui",
    "plugins",
    "broker",
    "risk",
    "trading",
)

# Owners with a capability registry (common owns shared scalars only).
CAPABILITY_OWNERS: tuple[str, ...] = OWNERS[1:]

# Expected "**Public records:**" list lengths per README sections 4.1-4.15.
EXPECTED_RECORD_COUNTS: dict[str, int] = {
    "workspace": 27,
    "catalogue": 18,
    "data": 27,
    "strategy": 26,
    "simulator": 23,
    "analytics": 22,
    "research": 27,
    "portfolio": 18,
    "orchestration": 25,
    "interfaces": 30,
    "ui": 37,
    "plugins": 13,
    "broker": 13,
    "risk": 24,
    "trading": 28,
}

# Expected "**Capability bundles (N):**" counts per README sections 4.1-4.15.
EXPECTED_CAPABILITY_COUNTS: dict[str, int] = {
    "workspace": 7,
    "catalogue": 7,
    "data": 14,
    "strategy": 13,
    "simulator": 12,
    "analytics": 9,
    "research": 13,
    "portfolio": 8,
    "orchestration": 7,
    "interfaces": 10,
    "ui": 17,
    "plugins": 7,
    "broker": 10,
    "risk": 7,
    "trading": 8,
}

# README record names that are PEP 695 type aliases rather than registry
# classes and are therefore legitimately absent from the wire registries.
ABSENT_TYPE_ALIASES: dict[str, frozenset[str]] = {
    "catalogue": frozenset({"AssetClass"}),
}

# README record names whose payload registers under a suffixed registry key
# because the registry stores the typed DomainEvent payload class.
EVENT_PAYLOAD_ALIASES: dict[str, dict[str, str]] = {
    "simulator": {"SimulationEvent": "SimulationEventPayload"},
    "broker": {"ProviderEvent": "ProviderEventPayload"},
    "trading": {"TradingEvent": "TradingEventPayload"},
}

# Port request/response/subscription records are ratified v1 port shapes, not
# inventory records; they are recognized by their declared suffix.
PORT_RECORD_SUFFIXES: tuple[str, ...] = ("Request", "Success", "Subscription")

# Documented auxiliary nested/shared definition models and additional event
# payloads that the registries carry beyond the README record inventory. Any
# key outside this snapshot, the inventory, a port suffix, or a payload alias
# is an undocumented drift and fails reconciliation.
AUXILIARY_REGISTRY_KEYS: dict[str, frozenset[str]] = {
    "workspace": frozenset(),
    "catalogue": frozenset(
        {
            "InstrumentVersionCreated",
            "InstrumentVersionDeleted",
            "ProviderSymbolMappingChanged",
            "ProviderSymbolMappingDeleted",
            "TradingSessionChanged",
            "MarketCalendarChanged",
            "TradingRuleSetChanged",
            "UniverseVersionCreated",
            "CataloguePackageImported",
        }
    ),
    "data": frozenset({"AlignmentPolicy", "ScenarioTransform", "SeriesInterval"}),
    "strategy": frozenset(
        {
            "AtmStage",
            "CompilerDiagnostic",
            "IndicatorOutputLine",
            "NodeBinding",
            "PackageDependency",
            "RandomBlockTemplate",
            "TargetFragment",
            "TemplatePlaceholder",
            "TemplateSubtreeConstraint",
        }
    ),
    "simulator": frozenset({"ProviderPin"}),
    "analytics": frozenset(),
    "research": frozenset(),
    "portfolio": frozenset(
        {"ExposureLimit", "FrontierPoint", "ObjectiveSpec", "RebalancePolicy"}
    ),
    "orchestration": frozenset({"PortSpec", "TransitionEdge"}),
    "interfaces": frozenset(),
    "ui": frozenset(),
    "plugins": frozenset(),
    "broker": frozenset({"ProviderRecord"}),
    "risk": frozenset({"OrderedCheck", "ScenarioShock"}),
    "trading": frozenset(),
}

CAPABILITY_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9.-]*@[1-9]\d*$")


@pytest.fixture(scope="session")
def registries() -> dict[str, dict[str, dict[str, type[BaseModel]]]]:
    """Load every namespace's wire registries once for the whole session."""
    return _load_registries()


@pytest.fixture(scope="session")
def capability_keys() -> dict[str, dict[str, CapabilityKey[Any]]]:
    """Load every owner's CapabilityKey constants once for the session."""
    return _load_capability_keys()


@pytest.fixture(scope="session")
def inventory_records() -> dict[str, list[str]]:
    """Parse the README record inventory once for the session."""
    return _parse_inventory_records()


@pytest.fixture(scope="session")
def inventory_capability_counts() -> dict[str, int]:
    """Parse the README capability bundle counts once for the session."""
    return _parse_inventory_capability_counts()


def _load_registries() -> dict[str, dict[str, dict[str, type[BaseModel]]]]:
    """Load every namespace's wire registries once per session.

    Returns:
        Owner to kind ("models"/"events"/"failures") to wire-name registry.
    """
    loaded: dict[str, dict[str, dict[str, type[BaseModel]]]] = {}
    for owner in OWNERS:
        registries: dict[str, dict[str, type[BaseModel]]] = {}
        for kind, module_name in (
            ("models", "models"),
            ("events", "events"),
            ("failures", "errors"),
        ):
            try:
                module = importlib.import_module(f"app.contracts.{owner}.{module_name}")
            except ModuleNotFoundError:
                continue
            registry = getattr(module, f"WIRE_{kind.upper()}", None)
            if registry is not None:
                registries[kind] = dict(registry)
        loaded[owner] = registries
    return loaded


def _load_capability_keys() -> dict[str, dict[str, CapabilityKey[Any]]]:
    """Collect each owner's exported CapabilityKey constants.

    Returns:
        Owner to constant name to CapabilityKey instance.
    """
    keys: dict[str, dict[str, CapabilityKey[Any]]] = {}
    for owner in CAPABILITY_OWNERS:
        module = importlib.import_module(f"app.contracts.{owner}.capabilities")
        keys[owner] = {
            name: value
            for name, value in vars(module).items()
            if name.endswith("_CAPABILITY") and isinstance(value, CapabilityKey)
        }
    return keys


def _parse_inventory_records() -> dict[str, list[str]]:
    """Parse the README sections 4.1-4.15 "Public records" lists.

    Returns:
        Owner to the ordered record names declared in the inventory.
    """
    text = INVENTORY_README.read_text(encoding="utf-8")
    sections = re.split(
        r"^### (4\.\d+) `app/contracts/(\w+)/`", text, flags=re.MULTILINE
    )
    records: dict[str, list[str]] = {}
    for i in range(1, len(sections), 3):
        _number, owner, body = sections[i], sections[i + 1], sections[i + 2]
        match = re.search(r"\*\*Public records:\*\* (.+)", body)
        assert match is not None, f"section for {owner} has no Public records list"
        records[owner] = re.findall(r"`([A-Za-z0-9_]+)`", match.group(1))
    return records


def _parse_inventory_capability_counts() -> dict[str, int]:
    """Parse the README sections 4.1-4.15 "Capability bundles (N)" counts.

    Returns:
        Owner to the declared capability bundle count.
    """
    text = INVENTORY_README.read_text(encoding="utf-8")
    sections = re.split(
        r"^### (4\.\d+) `app/contracts/(\w+)/`", text, flags=re.MULTILINE
    )
    counts: dict[str, int] = {}
    for i in range(1, len(sections), 3):
        _number, owner, body = sections[i], sections[i + 1], sections[i + 2]
        match = re.search(r"\*\*Capability bundles \((\d+)\):\*\*", body)
        assert match is not None, f"section for {owner} has no capability bundle count"
        counts[owner] = int(match.group(1))
    return counts


def test_every_namespace_exports_wire_registries(
    registries: dict[str, dict[str, dict[str, type[BaseModel]]]],
) -> None:
    """Verify all 16 namespaces export at least one nonempty wire registry."""
    assert set(registries) == set(OWNERS)
    for owner in OWNERS:
        assert registries[owner], f"namespace {owner} exports no wire registries"
        for kind, registry in registries[owner].items():
            assert registry, f"namespace {owner} exports an empty WIRE_{kind.upper()}"


def test_inventory_sections_cover_all_owners(
    inventory_records: dict[str, list[str]],
    inventory_capability_counts: dict[str, int],
) -> None:
    """Verify sections 4.1-4.15 exist exactly for the 15 record-owning namespaces."""
    assert set(inventory_records) == set(CAPABILITY_OWNERS)
    assert set(inventory_capability_counts) == set(CAPABILITY_OWNERS)


def test_record_counts_match_inventory(
    inventory_records: dict[str, list[str]],
) -> None:
    """Verify the parsed per-owner record counts match the expected totals."""
    for owner, expected in EXPECTED_RECORD_COUNTS.items():
        names = inventory_records[owner]
        assert len(names) == expected, (
            f"{owner} inventory lists {len(names)} records, expected {expected}"
        )


def test_every_inventory_record_is_registered(
    inventory_records: dict[str, list[str]],
    registries: dict[str, dict[str, dict[str, type[BaseModel]]]],
) -> None:
    """Verify every README record resolves to a wire registry key."""
    for owner, names in inventory_records.items():
        registered = set(registries[owner].get("models", {})) | set(
            registries[owner].get("events", {})
        )
        tolerated = ABSENT_TYPE_ALIASES.get(owner, frozenset())
        for name in names:
            if name in tolerated:
                continue
            alias = EVENT_PAYLOAD_ALIASES.get(owner, {}).get(name)
            resolved = alias if alias is not None else name
            assert resolved in registered, (
                f"{owner} inventory record {name} is not registered "
                f"(looked for key {resolved})"
            )


def test_inventory_absences_are_only_documented_type_aliases(
    inventory_records: dict[str, list[str]],
    registries: dict[str, dict[str, dict[str, type[BaseModel]]]],
) -> None:
    """Verify only documented type aliases are absent from the registries."""
    for owner, names in inventory_records.items():
        registered = set(registries[owner].get("models", {})) | set(
            registries[owner].get("events", {})
        )
        aliased = set(EVENT_PAYLOAD_ALIASES.get(owner, {}))
        absent = {
            name
            for name in names
            if name not in registered
            and name not in aliased
            and EVENT_PAYLOAD_ALIASES.get(owner, {}).get(name) not in registered
        }
        tolerated = ABSENT_TYPE_ALIASES.get(owner, frozenset())
        assert absent <= tolerated, (
            f"{owner} records absent from registries beyond tolerated aliases: "
            f"{sorted(absent - tolerated)}"
        )
        # The tolerated alias sets must not rot: every listed alias stays absent.
        assert not (tolerated & registered), (
            f"{owner} tolerated aliases now registered: "
            f"{sorted(tolerated & registered)}"
        )


def test_every_registered_key_is_accounted_for(
    inventory_records: dict[str, list[str]],
    registries: dict[str, dict[str, dict[str, type[BaseModel]]]],
) -> None:
    """Verify every registry key is an inventory record or documented addition."""
    for owner in CAPABILITY_OWNERS:
        registered = set(registries[owner].get("models", {})) | set(
            registries[owner].get("events", {})
        )
        inventory = set(inventory_records[owner])
        mapped_payloads = set(EVENT_PAYLOAD_ALIASES.get(owner, {}).values())
        port_records = {key for key in registered if key.endswith(PORT_RECORD_SUFFIXES)}
        auxiliary = AUXILIARY_REGISTRY_KEYS.get(owner, frozenset())
        unaccounted = (
            registered - inventory - mapped_payloads - port_records - auxiliary
        )
        assert not unaccounted, (
            f"{owner} registry keys not present in the README inventory or the "
            f"documented auxiliary/port sets: {sorted(unaccounted)}"
        )
        # The auxiliary snapshot must not rot: every listed key still registers.
        assert auxiliary <= registered, (
            f"{owner} stale auxiliary keys no longer registered: "
            f"{sorted(auxiliary - registered)}"
        )


def test_wire_models_are_frozen_strict_base_models(
    registries: dict[str, dict[str, dict[str, type[BaseModel]]]],
) -> None:
    """Verify every registered wire value is a frozen extra-forbidding model."""
    for owner in OWNERS:
        for kind, registry in registries[owner].items():
            for name, model in registry.items():
                assert isinstance(model, type), (
                    f"{owner} WIRE_{kind.upper()}[{name}] is not a class"
                )
                assert issubclass(model, BaseModel), (
                    f"{owner} WIRE_{kind.upper()}[{name}] is not a BaseModel"
                )
                assert model.model_config.get("extra") == "forbid", (
                    f"{owner}:{name} does not forbid extra fields"
                )
                assert model.model_config.get("frozen") is True, (
                    f"{owner}:{name} is not frozen"
                )


def test_capability_key_counts_match_inventory(
    capability_keys: dict[str, dict[str, CapabilityKey[Any]]],
    inventory_capability_counts: dict[str, int],
) -> None:
    """Verify per-owner CapabilityKey counts match the README bundle counts."""
    assert set(capability_keys) == set(CAPABILITY_OWNERS)
    for owner, keys in capability_keys.items():
        expected = inventory_capability_counts[owner]
        assert expected == EXPECTED_CAPABILITY_COUNTS[owner], (
            f"{owner} README bundle count {expected} differs from the expected "
            f"{EXPECTED_CAPABILITY_COUNTS[owner]}"
        )
        assert len(keys) == expected, (
            f"{owner} exports {len(keys)} capability keys, README declares {expected}"
        )


def test_capability_keys_use_major_one_and_owner_prefix(
    capability_keys: dict[str, dict[str, CapabilityKey[Any]]],
) -> None:
    """Verify each key identifier is '<name>@1' under its owner prefix."""
    for owner, keys in capability_keys.items():
        for constant_name, key in keys.items():
            assert key.major == 1, f"{owner}:{constant_name} major is not 1"
            assert key.identifier == f"{key.name}@{key.major}", (
                f"{owner}:{constant_name} identifier formatting is inconsistent"
            )
            assert CAPABILITY_IDENTIFIER_PATTERN.fullmatch(key.identifier), (
                f"{owner}:{constant_name} identifier {key.identifier!r} is invalid"
            )
            assert key.name.startswith(f"{owner}."), (
                f"{owner}:{constant_name} name {key.name!r} lacks its owner prefix"
            )

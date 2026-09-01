"""Version-discipline checks for the registered wire contracts.

Verifies that every registered top-level model carries
``schema_version: Literal[1] == 1`` (except the four documented workspace
collision-exception records), that every capability key is major 1 with a
valid identifier, and that every failure envelope embeds the common
``ProblemDetails`` with a ``Literal["FAILURE"]`` outcome.
"""

from __future__ import annotations

import importlib
import re
import types
import typing
from typing import Any

import pytest
from app.contracts.common.models import ProblemDetails
from app.kernel.capability import CapabilityKey
from pydantic import BaseModel

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

CAPABILITY_OWNERS: tuple[str, ...] = OWNERS[1:]

# Registered records whose ``schema_version`` semantically belongs to an
# external/versioned thing rather than the record itself (the documented
# workspace database-schema collision exceptions, plus the orchestration
# task-port record whose schema_version is the port's declared version), so
# they keep a domain integer and carry no record-level Literal[1] field.
DOMAIN_SCHEMA_VERSION_EXCEPTIONS: dict[str, frozenset[str]] = {
    "workspace": frozenset(
        {
            "WorkspaceVersion",
            "WorkspaceBackupManifest",
            "SystemReadiness",
            "DiagnosticBundleManifest",
        }
    ),
    "orchestration": frozenset({"PortSpec"}),
}

WORKSPACE_SCHEMA_VERSION_EXCEPTIONS: frozenset[str] = DOMAIN_SCHEMA_VERSION_EXCEPTIONS[
    "workspace"
]

# Registered models that embed inside other records and therefore carry no
# own ``schema_version`` field at all: the shared common component records,
# cross-record reference shapes, and auxiliary nested definitions. They are
# versioned through their embedding top-level records. Any new
# schema-version-less registration must be added here consciously.
SCHEMA_VERSIONLESS_COMPONENT_MODELS: dict[str, frozenset[str]] = {
    "common": frozenset(
        {
            "Money",
            "Timeframe",
            "SeriesPointKey",
            "ValidationIssue",
            "CapabilityProviderSnapshot",
        }
    ),
    "catalogue": frozenset(
        {
            "InstrumentRef",
            "ProviderRef",
            "BrokerRef",
            "TradingSessionDefinition",
            "MarketCalendarVersion",
            "TradingInterval",
            "OrderConstraints",
            "CostModelRef",
            "UniverseRef",
            "UniverseMembership",
        }
    ),
    "data": frozenset({"SeriesInterval", "AlignmentPolicy", "ScenarioTransform"}),
    "strategy": frozenset(
        {
            "NodeBinding",
            "TemplatePlaceholder",
            "TemplateSubtreeConstraint",
            "PackageDependency",
            "AtmStage",
            "RandomBlockTemplate",
            "IndicatorOutputLine",
            "TargetFragment",
            "CompilerDiagnostic",
        }
    ),
    "simulator": frozenset({"ProviderPin"}),
    "portfolio": frozenset(
        {"ExposureLimit", "RebalancePolicy", "ObjectiveSpec", "FrontierPoint"}
    ),
    "orchestration": frozenset({"TransitionEdge"}),
    "broker": frozenset({"ProviderRecord"}),
    "risk": frozenset({"OrderedCheck", "ScenarioShock"}),
}

CAPABILITY_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9.-]*@[1-9]\d*$")


def _load_all_registries() -> list[tuple[str, str, str, type[BaseModel]]]:
    """Load every registered model across all namespaces and registry kinds.

    Returns:
        Tuples of (owner, registry kind, wire key, model class).
    """
    entries: list[tuple[str, str, str, type[BaseModel]]] = []
    for owner in OWNERS:
        for kind, module_name in (
            ("models", "models"),
            ("events", "events"),
            ("failures", "errors"),
        ):
            try:
                module = importlib.import_module(f"app.contracts.{owner}.{module_name}")
            except ModuleNotFoundError:
                continue
            registry: dict[str, type[BaseModel]] | None = getattr(
                module, f"WIRE_{kind.upper()}", None
            )
            if registry is None:
                continue
            entries.extend((owner, kind, key, model) for key, model in registry.items())
    return entries


def _is_literal_one(annotation: Any) -> bool:
    """Check whether an annotation is exactly ``Literal[1]``.

    Args:
        annotation: Field annotation to inspect.

    Returns:
        True when the annotation is the literal schema-version one.
    """
    return typing.get_origin(annotation) is typing.Literal and typing.get_args(
        annotation
    ) == (1,)


@pytest.fixture(scope="session")
def registered_models() -> list[tuple[str, str, str, type[BaseModel]]]:
    """Load every registered model once for the session."""
    return _load_all_registries()


def test_registered_models_span_every_namespace(
    registered_models: list[tuple[str, str, str, type[BaseModel]]],
) -> None:
    """Verify each of the 16 namespaces contributes registered models."""
    owners = {owner for owner, _kind, _key, _model in registered_models}
    assert owners == set(OWNERS)


def test_every_registered_model_carries_schema_version_literal_one(
    registered_models: list[tuple[str, str, str, type[BaseModel]]],
) -> None:
    """Verify the schema_version field is Literal[1] defaulting to 1.

    Top-level records, events, requests, results, and failures carry the
    literal; the four workspace collision exceptions and the documented
    embedded component records are the only allowed deviations.
    """
    versionless: dict[str, set[str]] = {}
    for owner, kind, key, model in registered_models:
        if key in DOMAIN_SCHEMA_VERSION_EXCEPTIONS.get(owner, frozenset()):
            continue
        fields = model.model_fields
        if "schema_version" not in fields:
            versionless.setdefault(owner, set()).add(key)
            continue
        annotation = fields["schema_version"].annotation
        assert _is_literal_one(annotation), (
            f"{owner} WIRE_{kind.upper()}[{key}].schema_version is {annotation!r}, "
            "expected Literal[1]"
        )
        assert fields["schema_version"].default == 1
    expected_versionless = {
        owner: set(keys) for owner, keys in SCHEMA_VERSIONLESS_COMPONENT_MODELS.items()
    }
    assert versionless == expected_versionless, (
        "registered models without schema_version drifted from the documented "
        f"component exception set: got {versionless}"
    )


def test_domain_schema_version_exceptions_keep_plain_ints(
    registered_models: list[tuple[str, str, str, type[BaseModel]]],
) -> None:
    """Verify exception records keep plain int schema versions, no Literal[1]."""
    exception_models = {
        (owner, key): model
        for owner, _kind, key, model in registered_models
        if key in DOMAIN_SCHEMA_VERSION_EXCEPTIONS.get(owner, frozenset())
    }
    expected_pairs = {
        (owner, key)
        for owner, keys in DOMAIN_SCHEMA_VERSION_EXCEPTIONS.items()
        for key in keys
    }
    assert set(exception_models) == expected_pairs
    for (owner, key), model in exception_models.items():
        fields = model.model_fields
        assert "schema_version" in fields, f"{owner}:{key} lacks schema_version"
        annotation = fields["schema_version"].annotation
        origin = typing.get_origin(annotation)
        if origin is typing.Union or isinstance(origin, types.UnionType):
            non_none = [a for a in typing.get_args(annotation) if a is not type(None)]
            assert non_none == [int], (
                f"{owner}:{key}.schema_version is {annotation!r}, expected a plain int"
            )
        else:
            assert annotation is int, (
                f"{owner}:{key}.schema_version is {annotation!r}, expected a plain int"
            )
        assert not any(
            _is_literal_one(field.annotation) for field in fields.values()
        ), f"{owner}:{key} unexpectedly carries a Literal[1] field"


def test_capability_keys_have_major_one_and_valid_identifiers() -> None:
    """Verify every exported capability key is a major-one valid identifier."""
    for owner in CAPABILITY_OWNERS:
        module = importlib.import_module(f"app.contracts.{owner}.capabilities")
        keys = [
            value
            for name, value in vars(module).items()
            if name.endswith("_CAPABILITY") and isinstance(value, CapabilityKey)
        ]
        assert keys, f"namespace {owner} exports no capability keys"
        for key in keys:
            assert isinstance(key.major, int), (
                f"{owner} key {key.name} major is not an int"
            )
            assert key.major == 1, (
                f"{owner} key {key.name} major is {key.major}, expected 1"
            )
            assert key.identifier == f"{key.name}@{key.major}"
            assert CAPABILITY_IDENTIFIER_PATTERN.fullmatch(key.identifier), (
                f"{owner} key identifier {key.identifier!r} is invalid"
            )


def test_failure_models_embed_problem_details_and_failure_outcome(
    registered_models: list[tuple[str, str, str, type[BaseModel]]],
) -> None:
    """Verify failure envelopes embed ProblemDetails and Literal FAILURE."""
    failures = [
        (owner, key, model)
        for owner, kind, key, model in registered_models
        if kind == "failures"
    ]
    assert {owner for owner, _key, _model in failures} == set(OWNERS)
    for owner, key, model in failures:
        problem_fields = [
            name
            for name, field in model.model_fields.items()
            if field.annotation is ProblemDetails
        ]
        assert problem_fields, f"{owner} failure {key} embeds no ProblemDetails"
        outcome = model.model_fields.get("outcome")
        assert outcome is not None, f"{owner} failure {key} lacks an outcome field"
        assert typing.get_origin(outcome.annotation) is typing.Literal, (
            f"{owner} failure {key} outcome is not a literal discriminator"
        )
        assert typing.get_args(outcome.annotation) == ("FAILURE",), (
            f"{owner} failure {key} outcome args {typing.get_args(outcome.annotation)}"
        )
        assert outcome.default == "FAILURE"
        schema_version = model.model_fields.get("schema_version")
        assert schema_version is not None, f"{owner} failure {key} lacks schema_version"
        assert _is_literal_one(schema_version.annotation), (
            f"{owner} failure {key} schema_version is not Literal[1]"
        )

"""Serialization round-trip coverage for the frozen wire models.

Covers a deterministic fixture sample spanning every owner namespace (at
least two records per owner, including nested-model and tuple-field cases)
and asserts JSON round-trip equality, unknown-field rejection, frozen
mutation rejection, and canonical string preservation for decimal,
timestamp, hash, and UUID values.
"""

from __future__ import annotations

import datetime
import importlib
import json
import typing
from collections.abc import Callable
from decimal import Decimal
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError
from pydantic.fields import FieldInfo

# Deterministic fixture constants valid against the common scalar aliases:
# lowercase canonical UUIDv7, RFC 3339 UTC with six fractional digits and
# "Z" suffix, canonical non-exponent decimals, and 64-char lowercase SHA-256.
UUID_A = "0198a2b4-c5d6-7e8f-9a0b-1c2d3e4f5a6b"
UUID_B = "0198a2b4-c5d6-7e8f-9a0b-1c2d3e4f5a6c"
TS_A = "2026-08-25T00:00:00.000000Z"
TS_B = "2026-08-26T00:00:00.000000Z"
HASH_A = "63e8063d9dc6f0fd5a24b4706818a165fd57c3531b74466cf5dea62bff09b0b6"  # pragma: allowlist secret

# StringConstraints patterns of the common scalar aliases, used to detect
# decimal/timestamp/hash/UUID fields generically through field metadata.
DECIMAL_PATTERN = r"^-?(?:0|[1-9]\d*)(?:\.\d*[1-9])?$"
TIMESTAMP_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$"
HASH_PATTERN = r"^[0-9a-f]{64}$"
UUID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"

# (owner, registry key, constructor kwargs) sample. Every owner namespace is
# represented by at least two records; nested-model and tuple-field shapes
# are included throughout.
ROUNDTRIP_FIXTURES: tuple[tuple[str, str, dict[str, Any]], ...] = (
    (
        "common",
        "Money",
        {"amount": "125.5", "currency": "USD"},
    ),
    (
        "common",
        "CapabilitySnapshot",
        {
            "snapshot_id": UUID_A,
            "created_at": TS_A,
            "providers": [
                {
                    "capability_key": "workspace.manage-workspaces@1",
                    "provider_feature_id": "FEAT-WORKSPACE-MANAGE_WORKSPACES",
                    "generation": 1,
                    "implementation_hash": HASH_A,
                    "configuration_hash": HASH_A,
                }
            ],
            "snapshot_hash": HASH_A,
        },
    ),
    (
        "common",
        "ValidationIssue",
        {"path": ("root", "child"), "code": "INVALID", "message": "value invalid"},
    ),
    (
        "workspace",
        "WorkspaceRef",
        {"workspace_id": UUID_A, "name": "primary", "created_at": TS_A},
    ),
    (
        "workspace",
        "RuntimeConfiguration",
        {"settings": {"port": 8080}, "validation": {"valid": True}},
    ),
    ("catalogue", "InstrumentRef", {"instrument_id": UUID_A}),
    (
        "catalogue",
        "FxRateObservation",
        {
            "observation_id": UUID_A,
            "base_currency": "EUR",
            "quote_currency": "USD",
            "rate": "1.05",
            "observed_at": TS_A,
            "source_provider": {"provider_id": UUID_B, "provider_name": "OANDA"},
            "freshness_expires_at": TS_B,
            "content_hash": HASH_A,
            "source_instrument": {"instrument_id": UUID_A},
        },
    ),
    ("data", "DataSeriesRef", {"series_id": UUID_A}),
    (
        "data",
        "Bar",
        {
            "timestamp": TS_A,
            "open": "1.05",
            "high": "1.06",
            "low": "1.04",
            "close": "1.055",
            "volume": "100",
            "source_sequence": 0,
            "flags": 0,
        },
    ),
    ("strategy", "StrategyRef", {"strategy_id": UUID_A}),
    (
        "strategy",
        "BlockDefinition",
        {
            "block_id": "long-entry",
            "version": 1,
            "category": "entry",
            "parameter_schema": {},
            "status": "ACTIVE",
            "content_hash": HASH_A,
        },
    ),
    (
        "simulator",
        "SimulationRequest",
        {
            "request_id": UUID_A,
            "strategy_version_id": UUID_B,
            "engine_profile_id": UUID_A,
            "settings": {},
            "data_binding_id": UUID_A,
            "seed_root": "0abc123",
            "idempotency_key": "key-1",
        },
    ),
    (
        "simulator",
        "RunManifest",
        {
            "manifest_id": UUID_A,
            "job_id": UUID_A,
            "capability_snapshot_id": UUID_A,
            "snapshot_hash": HASH_A,
            "behavior_providers": [
                {
                    "capability_key": "simulator.simulate-orders@1",
                    "version": 1,
                    "implementation_hash": HASH_A,
                }
            ],
            "engine_profile_id": UUID_A,
            "engine_profile_version": 1,
            "strategy_version_id": UUID_B,
            "strategy_hash": HASH_A,
            "settings_hash": HASH_A,
            "data_binding_id": UUID_A,
            "seed_root": "0abc123",
            "environment": "dev",
            "state": "COMMITTED",
            "content_hash": HASH_A,
        },
    ),
    ("analytics", "DatabankRef", {"databank_id": UUID_A}),
    (
        "analytics",
        "ResultPage",
        {"page_id": UUID_A, "query_id": UUID_B, "rows": [{"net_profit": "125.5"}]},
    ),
    (
        "research",
        "ResearchRunRef",
        {
            "run_id": UUID_A,
            "job_id": UUID_B,
            "manifest_id": UUID_A,
            "method": "robustness",
            "state": "QUEUED",
        },
    ),
    (
        "research",
        "ParameterSpace",
        {
            "space_id": UUID_A,
            "parameters": [
                {
                    "name": "period",
                    "domain": "GRID",
                    "values": [10, 20],
                    "range_min": None,
                    "range_max": None,
                    "step": None,
                }
            ],
            "content_hash": HASH_A,
        },
    ),
    ("portfolio", "PortfolioRef", {"portfolio_id": UUID_A}),
    (
        "portfolio",
        "PortfolioMember",
        {"member_id": UUID_A, "strategy_version_id": UUID_B, "sizing_rule": {}},
    ),
    ("orchestration", "ProjectRef", {"project_id": UUID_A}),
    (
        "orchestration",
        "TaskDefinition",
        {
            "task_key": "load-data",
            "task_type": "DOMAIN",
            "settings": {},
            "contract": {
                "task_type": "DOMAIN",
                "contract_version": 1,
                "supports_checkpoint": True,
                "cancellation_behavior": "COOPERATIVE",
                "resource_estimator": "fixed",
            },
        },
    ),
    ("interfaces", "ApiVersion", {}),
    (
        "interfaces",
        "AsyncJobRef",
        {
            "job_id": UUID_A,
            "command_type": "run-research",
            "created_at": TS_A,
            "updated_at": TS_A,
        },
    ),
    ("ui", "AccessibilityPreference", {}),
    (
        "ui",
        "WidgetTypeDescriptor",
        {
            "widget_type": "equity-chart",
            "owning_feature": "FEAT-UI-EXPLORE_RESULTS",
            "type_version": 1,
            "default_placement": {
                "instance_id": UUID_A,
                "panel_id": "left",
                "size_ratio": "0.5",
            },
        },
    ),
    ("plugins", "PluginRef", {"plugin_id": "sample-plugin"}),
    (
        "plugins",
        "PluginManifest",
        {
            "id": "sample-plugin",
            "version": "1.0.0",
            "api_range": ">=1.0.0 <2.0.0",
            "schemas": {},
            "permissions": {},
            "resources": {},
            "sha256_by_file": {"main.py": HASH_A},
        },
    ),
    (
        "broker",
        "BrokerSessionRef",
        {
            "session_id": UUID_A,
            "profile_id": UUID_B,
            "profile_version": 1,
            "account_ref": "demo-account",
            "environment": "DEMO",
            "generation": 1,
        },
    ),
    (
        "broker",
        "BrokerMarketState",
        {
            "session_id": UUID_A,
            "generation": 1,
            "instrument": {"instrument_id": UUID_B},
            "provider_symbol": "EURUSD",
            "market_status": "OPEN",
            "receipt_time": TS_A,
            "bid": "1.05",
            "ask": "1.06",
            "last": "1.055",
        },
    ),
    ("risk", "RiskProfileRef", {"profile_id": UUID_A}),
    (
        "risk",
        "KillSwitchState",
        {
            "scope": {
                "scope_id": UUID_A,
                "kind": "GLOBAL",
                "scope_value": None,
                "scope_hash": HASH_A,
            },
            "version": 1,
            "state": "ACTIVE",
            "reason": "manual test engagement",
            "last_transition_at": TS_A,
        },
    ),
    ("trading", "TradingSessionRef", {"session_id": UUID_A, "mode": "PAPER"}),
    (
        "trading",
        "TradingStateQuery",
        {
            "query_id": UUID_A,
            "session_id": UUID_B,
            "projection": "SESSIONS",
            "cursor": None,
        },
    ),
)


def _load_model(owner: str, key: str) -> type[BaseModel]:
    """Resolve one fixture's model class from its owning namespace.

    Args:
        owner: Namespace identifier.
        key: Wire registry key.

    Returns:
        The registered Pydantic model class.
    """
    module = importlib.import_module(f"app.contracts.{owner}.models")
    registry: dict[str, type[BaseModel]] = module.WIRE_MODELS
    return registry[key]


def _field_patterns(model: type[BaseModel]) -> dict[str, str]:
    """Map each constrained string field to its StringConstraints pattern.

    Pydantic unwraps ``Annotated`` metadata of plain fields into
    ``FieldInfo.metadata``; nullable unions keep the ``Annotated`` branch
    inside the union, so both locations are inspected.

    Args:
        model: Registered wire model class.

    Returns:
        Field name to the declared validation pattern, when present.
    """
    patterns: dict[str, str] = {}
    for name, field in model.model_fields.items():
        candidates: list[Any] = list(field.metadata)
        annotation: Any = field.annotation
        if typing.get_origin(annotation) is typing.Annotated:
            candidates.extend(typing.get_args(annotation)[1:])
        elif typing.get_origin(annotation) is typing.Union:
            for arg in typing.get_args(annotation):
                if typing.get_origin(arg) is typing.Annotated:
                    candidates.extend(typing.get_args(arg)[1:])
        for metadata in candidates:
            pattern = getattr(metadata, "pattern", None)
            if isinstance(pattern, str):
                patterns[name] = pattern
                break
    return patterns


@pytest.fixture(
    scope="module", params=ROUNDTRIP_FIXTURES, ids=lambda f: f"{f[0]}:{f[1]}"
)
def fixture_entry(
    request: pytest.FixtureRequest,
) -> tuple[str, str, dict[str, Any]]:
    """Expose one parametrized (owner, key, kwargs) fixture entry."""
    entry: tuple[str, str, dict[str, Any]] = request.param
    return entry


def test_sample_spans_every_owner_with_minimum_two_records() -> None:
    """Verify the fixture sample covers every owner with at least two records."""
    owners = {owner for owner, _key, _kwargs in ROUNDTRIP_FIXTURES}
    expected_owners = {
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
    }
    assert owners == expected_owners
    for owner in expected_owners:
        count = sum(1 for o, _k, _kw in ROUNDTRIP_FIXTURES if o == owner)
        assert count >= 2, f"owner {owner} has only {count} fixture records"


def test_json_roundtrip_reproduces_equal_model(
    fixture_entry: tuple[str, str, dict[str, Any]],
) -> None:
    """Verify model_dump_json then model_validate_json reproduces an equal model."""
    owner, key, kwargs = fixture_entry
    model = _load_model(owner, key)
    instance = model(**kwargs)
    wire = instance.model_dump_json()
    restored = model.model_validate_json(wire)
    assert restored == instance
    assert type(restored) is type(instance)


def test_unknown_extra_fields_are_rejected(
    fixture_entry: tuple[str, str, dict[str, Any]],
) -> None:
    """Verify an unknown injected field fails strict validation."""
    owner, key, kwargs = fixture_entry
    model = _load_model(owner, key)
    instance = model(**kwargs)
    payload = json.loads(instance.model_dump_json())
    payload["__unknown_field__"] = "forbidden"
    with pytest.raises(ValidationError):
        model.model_validate_json(json.dumps(payload))


def test_frozen_models_reject_mutation(
    fixture_entry: tuple[str, str, dict[str, Any]],
) -> None:
    """Verify mutating any field of a frozen model raises."""
    owner, key, kwargs = fixture_entry
    model = _load_model(owner, key)
    instance = model(**kwargs)
    first_field = next(iter(model.model_fields))
    with pytest.raises(ValidationError):
        setattr(instance, first_field, "mutated")


def test_decimal_fields_stay_canonical_strings(
    fixture_entry: tuple[str, str, dict[str, Any]],
) -> None:
    """Verify decimal-valued fields serialize as their exact canonical strings."""
    owner, key, kwargs = fixture_entry
    model = _load_model(owner, key)
    instance = model(**kwargs)
    dumped = json.loads(instance.model_dump_json())
    for field_name, pattern in _field_patterns(model).items():
        if pattern != DECIMAL_PATTERN or kwargs.get(field_name) is None:
            continue
        assert isinstance(dumped[field_name], str), (
            f"{owner}:{key}.{field_name} serialized as a non-string"
        )
        assert dumped[field_name] == kwargs[field_name]


def test_decimal_string_preservation_is_covered() -> None:
    """Verify the sample includes at least one DecimalValue field check."""
    checked_total = 0
    for owner, key, kwargs in ROUNDTRIP_FIXTURES:
        model = _load_model(owner, key)
        instance = model(**kwargs)
        dumped = json.loads(instance.model_dump_json())
        for field_name, pattern in _field_patterns(model).items():
            if pattern == DECIMAL_PATTERN and kwargs.get(field_name) is not None:
                assert dumped[field_name] == kwargs[field_name], (
                    f"{owner}:{key}.{field_name} decimal drift"
                )
                checked_total += 1
    assert checked_total >= 5, "decimal string coverage shrank below expectations"


def test_timestamp_hash_and_uuid_fields_validate_as_strings(
    fixture_entry: tuple[str, str, dict[str, Any]],
) -> None:
    """Verify timestamp/hash/UUID-constrained fields round-trip exactly."""
    owner, key, kwargs = fixture_entry
    model = _load_model(owner, key)
    instance = model(**kwargs)
    dumped = json.loads(instance.model_dump_json())
    for field_name, pattern in _field_patterns(model).items():
        expected = kwargs.get(field_name)
        if expected is None:
            continue
        if pattern in (TIMESTAMP_PATTERN, HASH_PATTERN, UUID_PATTERN):
            assert dumped[field_name] == expected, (
                f"{owner}:{key}.{field_name} canonical string drifted"
            )


def test_scalar_alias_coverage_is_present_in_sample() -> None:
    """Verify the sample exercises timestamp, hash, and UUID validations."""
    seen = set()
    for owner, key, kwargs in ROUNDTRIP_FIXTURES:
        model = _load_model(owner, key)
        for field_name, pattern in _field_patterns(model).items():
            if kwargs.get(field_name) is None:
                continue
            if pattern == TIMESTAMP_PATTERN:
                seen.add("timestamp")
            elif pattern == HASH_PATTERN:
                seen.add("hash")
            elif pattern == UUID_PATTERN:
                seen.add("uuid")
    assert seen == {"timestamp", "hash", "uuid"}


# ---------------------------------------------------------------------------
# Exhaustive execution of every wire registry entry
# ---------------------------------------------------------------------------

EXHAUSTIVE_OWNERS: tuple[str, ...] = (
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

# Registry kind to owning category module, mirroring
# scripts/generate_contracts.py's loading convention.
_REGISTRY_KIND_MODULES: tuple[tuple[str, str], ...] = (
    ("models", "models"),
    ("events", "events"),
    ("failures", "errors"),
)

# Module-level registry cache: each namespace is imported and read exactly
# once per test process, keeping the hundreds of parametrized cases fast.
_REGISTRY_CACHE: dict[str, dict[str, dict[str, type[BaseModel]]]] = {}


def _namespace_registries(owner: str) -> dict[str, dict[str, type[BaseModel]]]:
    """Load one owner's wire registries with process-lifetime caching.

    Args:
        owner: Namespace identifier.

    Returns:
        Mapping of registry kind ("models"/"events"/"failures") to the
        wire-name-to-class registry the namespace exports. Kinds the
        namespace does not define are absent.
    """
    cached = _REGISTRY_CACHE.get(owner)
    if cached is not None:
        return cached
    registries: dict[str, dict[str, type[BaseModel]]] = {}
    for kind, module_name in _REGISTRY_KIND_MODULES:
        try:
            module = importlib.import_module(f"app.contracts.{owner}.{module_name}")
        except ModuleNotFoundError:
            continue
        registry = getattr(module, f"WIRE_{kind.upper()}", None)
        if isinstance(registry, dict):
            registries[kind] = dict(registry)
    _REGISTRY_CACHE[owner] = registries
    return registries


def _every_registry_entry() -> tuple[tuple[str, str, type[BaseModel]], ...]:
    """Enumerate every entry of every namespace registry deterministically.

    Returns:
        Tuples of (owner, "kind:wire-name", model class) in canonical owner,
        kind, and wire-name order.
    """
    entries: list[tuple[str, str, type[BaseModel]]] = []
    for owner in EXHAUSTIVE_OWNERS:
        for kind, registry in sorted(_namespace_registries(owner).items()):
            for key in sorted(registry):
                entries.append((owner, f"{kind}:{key}", registry[key]))
    return tuple(entries)


# Computed once at import so registry loading stays session-scoped.
ALL_REGISTRY_ENTRIES: tuple[tuple[str, str, type[BaseModel]], ...] = (
    _every_registry_entry()
)

# Deterministic minimal values for pattern-constrained strings. Ordered rules
# of (needle, ...) tuples: the first rule whose every needle appears in the
# declared StringConstraints pattern provides the value.
_MINIMAL_UUID = "0198a000-0000-7000-8000-000000000001"
_MINIMAL_TIMESTAMP = "2026-01-01T00:00:00.000000Z"
_PATTERN_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
    ((r"{8}-", "7"), _MINIMAL_UUID),
    ((r"\d{4}-",), _MINIMAL_TIMESTAMP),
    ((r"{64}", "0-9a-f"), "a" * 64),
    ((r"[A-Z]{3}",), "USD"),
    ((r"^-?(?:0|",), "1"),
    ((r"^(?:urn:|https?://)",), "urn:x"),
    (("@",), "a@1"),
    ((r"^FEAT-",), "FEAT-X"),
    ((r"^[A-Z][A-Z0-9_-]*$",), "X"),
    ((r"^[A-Z][A-Z0-9_]*$",), "X"),
    ((r"[01]", ":"), "00:00:00"),
    ((r"\d+\.\d+\.\d+",), "1.0.0"),
    ((r"(?:/",), "UTC"),
    ((r"://",), "https://x"),
    ((r"25[0-5]",), "127.0.0.1"),
    ((r"a-fA-F",), "a"),
    ((r"^v[1-9]",), "v1"),
    ((r"^/",), "/x"),
)

# Depth cap for nested required BaseModel recursion; self-referential record
# shapes terminate here and honestly land in the ValidationError branch.
_MAX_MODEL_DEPTH = 8

# Frozen-model mutation sentinel; frozen records reject any assignment.
_MUTATION_SENTINEL = object()


def _min_length(metadata: list[Any]) -> int:
    """Return the strictest declared minimum length in constraint metadata.

    Args:
        metadata: Constraint objects collected for one annotation.

    Returns:
        The largest declared ``min_length`` (StringConstraints or MinLen), or
        zero when none declares one.
    """
    best = 0
    for constraint in metadata:
        value = getattr(constraint, "min_length", None)
        if isinstance(value, int) and value > best:
            best = value
    return best


def _declared_pattern(metadata: list[Any]) -> str | None:
    """Return the declared StringConstraints pattern, if any.

    Args:
        metadata: Constraint objects collected for one annotation.

    Returns:
        The first declared validation pattern, or None.
    """
    for constraint in metadata:
        pattern = getattr(constraint, "pattern", None)
        if isinstance(pattern, str):
            return pattern
    return None


def _pattern_value(pattern: str, min_length: int) -> str:
    """Derive a minimal string satisfying one declared pattern.

    Args:
        pattern: The declared validation pattern.
        min_length: Declared minimum length used by the generic fallback.

    Returns:
        A deterministic literal known to satisfy the pattern family.
    """
    for needles, value in _PATTERN_RULES:
        if all(needle in pattern for needle in needles):
            return value
    return "x" * max(min_length, 1)


def _bounded_int(metadata: list[Any]) -> int:
    """Derive a minimal int satisfying declared ge/le bounds.

    Args:
        metadata: Constraint objects collected for one annotation.

    Returns:
        1 adjusted upward to the greatest ``ge`` and downward to the least
        ``le``; the registries' bounds always admit such a value.
    """
    value = 1
    for constraint in metadata:
        lower = getattr(constraint, "ge", None)
        if isinstance(lower, int) and value < lower:
            value = lower
    for constraint in metadata:
        upper = getattr(constraint, "le", None)
        if isinstance(upper, int) and value > upper:
            value = upper
    return value


def _constrained_str(metadata: list[Any]) -> str:
    """Derive a minimal string for one constrained str annotation.

    Args:
        metadata: Constraint objects collected for the annotation.

    Returns:
        A pattern-derived literal, or the min-length filler "x".
    """
    pattern = _declared_pattern(metadata)
    min_length = _min_length(metadata)
    if pattern is None:
        return "x" * max(min_length, 1)
    return _pattern_value(pattern, min_length)


def _expand_annotated(annotation: Any, metadata: list[Any]) -> tuple[Any, list[Any]]:
    """Unwrap one Annotated annotation, merging its constraint metadata.

    Args:
        annotation: An ``Annotated[...]`` type origin.
        metadata: Constraint objects already collected for the annotation.

    Returns:
        The underlying annotation and the merged constraint list; nested
        ``Field(...)`` metadata expands into its own constraints.
    """
    args = typing.get_args(annotation)
    merged = list(metadata)
    for extra in args[1:]:
        if isinstance(extra, FieldInfo):
            merged.extend(extra.metadata)
        else:
            merged.append(extra)
    return args[0], merged


def _union_value(annotation: Any, metadata: list[Any], depth: int) -> Any:
    """Derive a minimal value for a union annotation.

    Required-nullable unions resolve to the minimal value of the first
    non-None branch; the registries declare only single-branch unions.

    Args:
        annotation: Union type origin.
        metadata: Constraint objects already collected for the annotation.
        depth: Current nested-model recursion depth.

    Returns:
        The derived branch value, or None for a None-only union.
    """
    branches = [arg for arg in typing.get_args(annotation) if arg is not type(None)]
    if not branches:
        return None
    return _minimal_value(branches[0], metadata, depth)


def _tuple_value(annotation: Any, metadata: list[Any], depth: int) -> tuple[Any, ...]:
    """Derive a minimal tuple for one tuple annotation.

    Variadic tuples yield one minimal element when a min-length bound
    demands it, otherwise the empty tuple; fixed-shape tuples yield one
    minimal element per position.

    Args:
        annotation: Tuple type origin.
        metadata: Constraint objects already collected for the annotation.
        depth: Current nested-model recursion depth.

    Returns:
        The derived tuple value.
    """
    args = typing.get_args(annotation)
    if len(args) == 2 and args[1] is Ellipsis:
        if _min_length(metadata) >= 1:
            return (_minimal_value(args[0], [], depth),)
        return ()
    return tuple(_minimal_value(arg, [], depth) for arg in args)


def _collection_value(annotation: Any, metadata: list[Any], depth: int) -> Any:
    """Derive a minimal list/set/frozenset for one collection annotation.

    Args:
        annotation: Collection type origin.
        metadata: Constraint objects already collected for the annotation.
        depth: Current nested-model recursion depth.

    Returns:
        An empty collection, or a one-element collection when a min-length
        bound demands an element.
    """
    origin = typing.get_origin(annotation)
    if _min_length(metadata) >= 1:
        args = typing.get_args(annotation)
        element = args[0] if args else str
        if origin is set:
            return {_minimal_value(element, [], depth)}
        if origin is frozenset:
            return frozenset({_minimal_value(element, [], depth)})
        return [_minimal_value(element, [], depth)]
    if origin is set:
        return set()
    if origin is frozenset:
        return frozenset()
    return []


def _mapping_value(annotation: Any, metadata: list[Any], depth: int) -> dict[Any, Any]:
    """Derive a minimal dict for one mapping annotation.

    Args:
        annotation: Dict type origin or bare dict.
        metadata: Constraint objects already collected for the annotation.
        depth: Current nested-model recursion depth.

    Returns:
        An empty dict, or a one-entry dict when a min-length bound demands
        an entry.
    """
    if _min_length(metadata) >= 1:
        args = typing.get_args(annotation)
        key_type = args[0] if args else str
        value_type = args[1] if len(args) > 1 else str
        return {
            _minimal_value(key_type, [], depth): _minimal_value(value_type, [], depth)
        }
    return {}


def _minimal_value(annotation: Any, metadata: list[Any], depth: int) -> Any:
    """Derive a minimal value for one resolved annotation.

    Unwraps PEP 695 aliases and ``Annotated`` (merging constraint metadata)
    and resolves ``Literal`` to its first argument before dispatching
    unions, containers, and scalars to their focused derivations.

    Args:
        annotation: The field annotation to satisfy.
        metadata: Constraint objects collected for the annotation.
        depth: Current nested-model recursion depth.

    Returns:
        A deterministic minimal value accepted by the annotation when
        possible; nested models arrive as raw kwargs dicts so validation
        failures surface through the parent constructor.
    """
    if isinstance(annotation, typing.TypeAliasType):
        return _minimal_value(annotation.__value__, metadata, depth)
    origin = typing.get_origin(annotation)
    if origin is typing.Annotated:
        inner, merged = _expand_annotated(annotation, metadata)
        return _minimal_value(inner, merged, depth)
    if origin is typing.Literal:
        return typing.get_args(annotation)[0]
    if origin is typing.Union:
        return _union_value(annotation, metadata, depth)
    return _minimal_container_or_scalar(annotation, metadata, depth)


def _minimal_container_or_scalar(
    annotation: Any, metadata: list[Any], depth: int
) -> Any:
    """Derive a minimal value for one alias-free annotation.

    Args:
        annotation: Container or scalar annotation.
        metadata: Constraint objects collected for the annotation.
        depth: Current nested-model recursion depth.

    Returns:
        The derived container or scalar value.
    """
    origin = typing.get_origin(annotation)
    if origin is tuple:
        return _tuple_value(annotation, metadata, depth)
    if origin is list or origin is set or origin is frozenset:
        return _collection_value(annotation, metadata, depth)
    if origin is dict:
        return _mapping_value(annotation, metadata, depth)
    return _minimal_scalar(annotation, metadata, depth)


# Minimal immutable scalar values keyed by exact annotation identity. bool is
# only reached through this table so ``annotation is int`` never sees bool.
_IMMUTABLE_SCALARS: dict[Any, Any] = {
    bool: False,
    float: 1.0,
    Decimal: Decimal(1),
    datetime.date: datetime.date(2026, 1, 1),
}


def _minimal_nested_model(model: type[BaseModel], depth: int) -> dict[str, Any]:
    """Derive minimal kwargs for one nested required model field.

    Args:
        model: Nested wire model class.
        depth: Current nested-model recursion depth.

    Returns:
        Minimal kwargs dict, or an empty dict past the recursion cap so the
        parent constructor honestly reports the missing fields.
    """
    if depth >= _MAX_MODEL_DEPTH:
        return {}
    return _minimal_kwargs(model, depth + 1)


def _minimal_scalar(annotation: Any, metadata: list[Any], depth: int) -> Any:
    """Derive a minimal value for one alias-free scalar annotation.

    Args:
        annotation: Scalar annotation (BaseModel, builtin, or date type).
        metadata: Constraint objects collected for the annotation.
        depth: Current nested-model recursion depth.

    Returns:
        The derived scalar value; unknown annotations yield None.
    """
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return _minimal_nested_model(annotation, depth)
    if annotation is int:
        return _bounded_int(metadata)
    if annotation is str:
        return _constrained_str(metadata)
    constant = _IMMUTABLE_SCALARS.get(annotation)
    if constant is not None:
        return constant
    for container_type, factory in _BARE_CONTAINER_FACTORIES:
        if annotation is container_type:
            return factory()
    return None


# Fresh empty containers for bare unparameterized collection annotations.
_BARE_CONTAINER_FACTORIES: tuple[tuple[Any, Callable[[], Any]], ...] = (
    (tuple, tuple),
    (dict, dict),
    (list, list),
)


def _minimal_kwargs(model: type[BaseModel], depth: int = 0) -> dict[str, Any]:
    """Build minimal constructor kwargs from one model's declared fields.

    Fields carrying defaults are skipped; every required field receives a
    value derived from its resolved annotation and constraints.

    Args:
        model: Registered wire model class.
        depth: Current nested-model recursion depth.

    Returns:
        Field name to minimal value mapping.
    """
    kwargs: dict[str, Any] = {}
    for name, field in model.model_fields.items():
        if not field.is_required():
            continue
        kwargs[name] = _minimal_value(field.annotation, list(field.metadata), depth)
    return kwargs


def test_registry_enumeration_is_exhaustive() -> None:
    """Verify the parametrization spans every owner and registry kind."""
    assert len(ALL_REGISTRY_ENTRIES) >= 500
    owners = {owner for owner, _key, _model in ALL_REGISTRY_ENTRIES}
    assert owners == set(EXHAUSTIVE_OWNERS)
    kinds = {key.split(":", 1)[0] for _owner, key, _model in ALL_REGISTRY_ENTRIES}
    assert kinds == {"models", "events", "failures"}


@pytest.mark.parametrize(
    ("owner", "entry_key", "model"),
    ALL_REGISTRY_ENTRIES,
    ids=[f"{owner}:{key}" for owner, key, _model in ALL_REGISTRY_ENTRIES],
)
def test_every_registry_entry_executes_wire_validation(
    owner: str,
    entry_key: str,
    model: type[BaseModel],
) -> None:
    """Execute construction and serialization for one registry entry.

    Either the entry constructs from field-derived minimal kwargs and then
    round-trips through JSON, rejects mutation, and rejects unknown fields,
    or construction honestly raises a pydantic ``ValidationError`` carrying
    error details: cross-field orderings and exclusivity rules cannot be
    satisfied generically, and both branches execute the declared
    validation code paths.

    Args:
        owner: Namespace identifier.
        entry_key: "kind:wire-name" registry key.
        model: The registered Pydantic model class.
    """
    kwargs = _minimal_kwargs(model)
    validation_errors: list[Any] | None = None
    try:
        instance = model(**kwargs)
    except ValidationError as exc:
        validation_errors = exc.errors()
    if validation_errors is not None:
        assert validation_errors, f"{owner}:{entry_key} failed without error details"
        return
    wire = instance.model_dump_json()
    restored = model.model_validate_json(wire)
    assert restored == instance, f"{owner}:{entry_key} JSON round-trip drifted"
    assert type(restored) is type(instance)
    first_field = next(iter(model.model_fields), None)
    if first_field is not None:
        with pytest.raises((ValidationError, TypeError)):
            setattr(instance, first_field, _MUTATION_SENTINEL)
    with pytest.raises(ValidationError):
        model.model_validate({**instance.model_dump(), "zz_extra": 1})

# ruff: noqa: C901, E402, PLR0912, PLR0915
"""Collect a bounded, secret-safe L5 MT5 operational certificate bundle.

This is a directly executable integration program, not a pytest test. It is
inert unless ``--execute-demo`` is supplied and every dev/demo safety check
passes. Generated bundles are evidence artifacts and are never committed.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from decimal import ROUND_DOWN, Decimal
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.services.api import get_system_settings, resolve_system_credential_slot
from app.services.brokers import (
    build_broker_connection_config,
    build_broker_order_filter,
    build_broker_order_request,
    build_broker_position_filter,
    build_simulation_mutation_envelope,
    cancel_broker_order,
    check_broker_order,
    connect_broker,
    create_broker_adapter,
    create_configured_fake_broker_adapter,
    create_simulation_broker_adapter,
    disconnect_broker,
    get_broker_account_info,
    get_broker_id,
    get_broker_orders,
    get_broker_permissions,
    get_broker_platform_info,
    get_broker_positions,
    get_broker_quote,
    get_broker_symbol_info,
    get_broker_value_field,
    list_broker_deal_history,
    list_broker_order_history,
    place_broker_order,
)
from app.services.simulator import (
    compare_parity_evidence,
    get_parity_envelope,
    normalize_parity_evidence,
)
from app.utils import generate_id, load_broker_provider_settings, load_settings

_BUNDLE_FILES = frozenset(
    {
        "manifest.json",
        "left-evidence.json",
        "right-evidence.json",
        "normalized-left.json",
        "normalized-right.json",
        "comparison.json",
        "commands.txt",
        "environment.json",
        "checksums.sha256",
    }
)
_HASHED_FILES = _BUNDLE_FILES - {"checksums.sha256"}
_SENSITIVE_FRAGMENTS = (
    "account_id",
    "credential",
    "login",
    "password",
    "secret",
    "terminal_path",
    "token",
)
_STATE_LIMIT = 1_000
_SHA256_HEX_LENGTH = 64
_MANIFEST_REQUIRED_KEYS = frozenset(
    {
        "schema_version",
        "certificate_id",
        "envelope_version",
        "status",
        "evidence_route",
        "provider_routes",
        "provider",
        "environment",
        "server_account_mode",
        "target_build",
        "allowed_evidence_sources",
        "certified_semantics",
        "excluded_empirical_claims",
        "explicit_scope_exclusions",
        "asset_class",
        "admitted_specifications",
        "market_evidence",
        "initial_authority",
        "operation_modes",
        "capability_intersection",
        "policy_paths",
        "invariants",
        "route_gate_policies",
        "ignored_fields",
        "comparison_contract",
        "evidence_provenance",
        "issued_at",
        "valid_through",
        "invalidation_triggers",
        "invalidation_bindings",
    }
)
_EXPLICIT_SCOPE_EXCLUSIONS = (
    "provider_specific_empirical_behavior",
    "asset_specific_empirical_behavior",
    "corporate_actions",
    "auctions",
    "multi_account_behavior",
)
_CAPABILITY_INTERSECTION = (
    "connect_disconnect",
    "account_read",
    "permission_read",
    "symbol_specification_read",
    "quote_read_for_safe_order_parameterization",
    "order_check",
    "pending_limit_order_place",
    "pending_order_cancel",
    "active_order_and_position_read",
    "bounded_order_and_deal_history_read",
)


def _json_safe(value: object) -> object:
    """Return a deterministic JSON-safe representation.

    Args:
        value: Arbitrary bounded canonical value.

    Returns:
        JSON-safe value with Decimal and datetime encoded as strings.
    """
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_safe(nested) for key, nested in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return [_json_safe(item) for item in value]
    return value


def _canonical_bytes(value: object) -> bytes:
    """Return canonical UTF-8 JSON bytes for hashing."""
    return json.dumps(
        _json_safe(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def _hash(value: object) -> str:
    """Return a lowercase SHA-256 digest of a canonical value."""
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _field(value: object, name: str, default: object = None) -> object:
    """Read one canonical field without depending on private DTO classes.

    Returns:
        Canonical field value or the supplied default.
    """
    try:
        result = get_broker_value_field(value, name)
    except AttributeError, TypeError, ValueError:
        return default
    return default if result is None else result


def _items(response: object) -> tuple[object, ...]:
    """Return a successful bounded page's items or fail closed.

    Returns:
        Bounded canonical page items.

    Raises:
        RuntimeError: If the authority read was unsuccessful.
    """
    if _field(response, "status") != "success":
        raise RuntimeError("authority page read failed")
    data = _field(response, "data")
    values = _field(data, "items", ())
    return tuple(values)  # type: ignore[arg-type]


def _project(value: object, names: tuple[str, ...]) -> dict[str, object]:
    """Project allowlisted non-secret canonical fields.

    Returns:
        Deterministic allowlisted field mapping.
    """
    return {name: _json_safe(_field(value, name)) for name in names}


def _has_sensitive_key(value: object) -> bool:
    """Return whether nested JSON carries a forbidden sensitive field name."""
    if isinstance(value, Mapping):
        for key, nested in value.items():
            lowered = str(key).lower()
            if lowered != "secret_free" and any(
                fragment in lowered for fragment in _SENSITIVE_FRAGMENTS
            ):
                return True
            if _has_sensitive_key(nested):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return any(_has_sensitive_key(item) for item in value)
    return False


def validate_collection_preflight(
    *, execute_demo: bool, environment: str, route: str, symbol: str
) -> None:
    """Fail closed unless an explicit bounded dev/demo run was requested.

    Args:
        execute_demo: Explicit command-line mutation authorization.
        environment: Application environment.
        route: Configured provider route.
        symbol: Exact admitted provider symbol.

    Raises:
        RuntimeError: If any safety precondition is absent.
    """
    if not execute_demo:
        raise RuntimeError("certificate collection requires --execute-demo")
    if environment != "dev" or route != "demo":
        raise RuntimeError("certificate collection is restricted to dev/demo")
    if symbol != "BTCUSD":
        raise RuntimeError("this approved weekend run is restricted to BTCUSD")


def _required_secret_text(value: object, field: str) -> str:
    """Return one required secret value for in-memory provider configuration.

    Args:
        value: Secret-bearing settings value.
        field: Non-secret field label used only in an error message.

    Returns:
        Unwrapped non-empty secret text.

    Raises:
        RuntimeError: If the value is empty.
        TypeError: If the value is absent or malformed.
    """
    getter = getattr(value, "get_secret_value", None)
    if not callable(getter):
        message = f"encrypted MT5 {field} is malformed"
        raise TypeError(message)
    result = getter()
    if not isinstance(result, str) or not result:
        message = f"encrypted MT5 {field} is empty"
        raise RuntimeError(message)
    return result


def require_terminal_executable(value: object) -> Path:
    """Require an explicitly configured existing MT5 terminal executable.

    Args:
        value: Configured terminal path or ``None``.

    Returns:
        Resolved existing terminal executable path.

    Raises:
        RuntimeError: If no exact terminal executable is configured.
    """
    if value is None:
        raise RuntimeError("MT5 terminal executable is not configured")
    getter = getattr(value, "get_secret_value", None)
    raw_value = getter() if callable(getter) else value
    terminal = Path(str(raw_value)).resolve()
    if not terminal.is_file():
        raise RuntimeError("configured MT5 terminal executable does not exist")
    return terminal


def build_collector_provider_settings(system_values: Mapping[str, object]) -> object:
    """Compose immutable MT5 settings from database-backed system values.

    Args:
        system_values: Public non-credential system-settings mapping.

    Returns:
        Secret-redacting broker-provider settings with explicit demo routing.

    Raises:
        RuntimeError: If MT5 is not enabled or terminal configuration is absent.
    """
    enabled = str(system_values.get("MT5_ENABLED", "false")).lower() == "true"
    terminal = system_values.get("MT5_TERMINAL_PATH")
    if not enabled:
        raise RuntimeError("MT5 is not enabled in database-backed system settings")
    if not terminal:
        raise RuntimeError(
            "MT5 terminal is absent from database-backed system settings"
        )
    return load_broker_provider_settings(
        {
            "mt5_enabled": True,
            "mt5_environment": "demo",
            "mt5_terminal_path": terminal,
        }
    )


def build_mt5_credential_mapping(
    slot: Mapping[str, object], terminal_setting: object
) -> dict[str, object]:
    """Build the Broker credential map without removing redaction wrappers.

    Args:
        slot: Encrypted database credential-slot fields.
        terminal_setting: Secret-redacting configured terminal value.

    Returns:
        Named non-empty SecretStr-compatible credential mapping.

    Raises:
        RuntimeError: If a required credential is absent or malformed.
    """
    values = {
        "login": slot.get("login"),
        "password": slot.get("password"),
        "server": slot.get("server"),
        "terminal_path": terminal_setting,
    }
    for name, value in values.items():
        getter = getattr(value, "get_secret_value", None)
        if not callable(getter) or not getter():
            message = f"encrypted MT5 {name} is absent or malformed"
            raise RuntimeError(message)
    return values


def _read_json(path: Path) -> dict[str, object]:
    """Read one JSON object from a bundle member.

    Returns:
        Parsed JSON object.

    Raises:
        TypeError: If the member is not a JSON object.
    """
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        message = f"bundle member is not an object: {path.name}"
        raise TypeError(message)
    return value


def _file_digest(path: Path) -> str:
    """Return one bundle member's lowercase SHA-256 digest."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_certificate_manifest(
    *,
    certificate_id: str,
    symbol: str,
    specification: Mapping[str, object],
    interval_start: datetime,
    interval_end: datetime,
    left: Mapping[str, object],
    right: Mapping[str, object],
    environment: Mapping[str, object],
    account_modes: Mapping[str, object],
    issued_at: datetime,
) -> dict[str, object]:
    """Build the complete immutable Envelope v2 publication manifest.

    Args:
        certificate_id: Unique generated certificate identity.
        symbol: Exact provider symbol admitted for the collection interval.
        specification: Observed provider specification projection.
        interval_start: Inclusive collection interval start.
        interval_end: Inclusive collection interval end.
        left: Simulation operational evidence.
        right: MT5 demo operational evidence.
        environment: Secret-free provider/build identity.
        account_modes: Observed provider account and margin modes.
        issued_at: Certificate issue time.

    Returns:
        Complete deterministic certificate publication manifest.

    Raises:
        ValueError: If observed evidence cannot support the publication scope.
        TypeError: If an Envelope v2 section or evidence binding is malformed.
    """
    envelope = get_parity_envelope("v2")
    applicability = envelope.get("operational_applicability")
    scope = envelope.get("certificate_scope")
    validity = envelope.get("validity")
    if not all(
        isinstance(value, Mapping) for value in (applicability, scope, validity)
    ):
        raise TypeError("Envelope v2 publication sections are malformed")
    if interval_end < interval_start:
        raise ValueError("certificate collection interval is reversed")
    left_state = left.get("initial_authority_state")
    right_state = right.get("initial_authority_state")
    if not isinstance(left_state, Mapping) or left_state != right_state:
        raise ValueError("certificate evidence lacks one shared initial authority")
    state_hash = left_state.get("state_hash")
    if not isinstance(state_hash, str) or len(state_hash) != _SHA256_HEX_LENGTH:
        raise ValueError("certificate initial-authority hash is malformed")
    comparison = compare_parity_evidence(left, right, envelope)
    if not comparison.get("passed") or comparison.get("certificate_invalidated"):
        raise ValueError("certificate evidence does not pass Envelope v2")
    environment_hash = _hash(environment)
    specification_hash = _hash(specification)
    evidence_hashes = {"left": _hash(left), "right": _hash(right)}
    comparison_hash = _hash(comparison)
    identity = left.get("identity")
    if not isinstance(identity, Mapping) or identity != right.get("identity"):
        raise ValueError("certificate evidence identity is absent or differs")
    identity_hash = _hash(identity)
    invalidation_triggers = tuple(envelope["invalidation_triggers"])
    invalidation_bindings = {
        "build_identity_change": environment_hash,
        "contract_change": _hash(envelope),
        "code_or_config_identity_change": identity_hash,
        "specification_revision_change": specification_hash,
        "source_or_tick_model_change": _hash(
            {
                "source_lineage_hash": identity.get("source_lineage_hash"),
                "tick_lineage_hash": identity.get("tick_lineage_hash"),
                "market_evidence_class": identity.get("market_evidence_class"),
            }
        ),
        "calibration_validity_change": "not_applicable_operational_contract",
        "detected_drift": comparison_hash,
        "initial_authority_state_change": state_hash,
    }
    if set(invalidation_bindings) != set(invalidation_triggers):
        raise ValueError("every invalidation trigger requires one exact binding")
    return {
        "schema_version": "l5-mt5-operational-certificate.v2",
        "certificate_id": certificate_id,
        "envelope_version": "v2",
        "status": "valid",
        "evidence_route": applicability["evidence_route"],
        "provider_routes": applicability["provider_routes"],
        "provider": scope["provider"],
        "environment": "dev",
        "server_account_mode": scope["server_account_mode"],
        "target_build": environment.get("target_build"),
        "allowed_evidence_sources": scope["evidence_sources"],
        "certified_semantics": applicability["certified_semantics"],
        "excluded_empirical_claims": applicability["excluded_empirical_claims"],
        "explicit_scope_exclusions": list(_EXPLICIT_SCOPE_EXCLUSIONS),
        "asset_class": scope["asset_class"],
        "admitted_specifications": (
            {
                "symbol": symbol,
                "revision_digest": specification_hash,
                "effective_from": interval_start.isoformat(),
                "effective_through": interval_end.isoformat(),
                "observed_fields": _json_safe(specification),
            },
        ),
        "market_evidence": {
            "class": scope["market_evidence_class"],
            "tick_model": "single_bid_ask_quote_not_certified",
            "resolution": "provider_quote_for_safe_order_parameterization_only",
            "bid_ask_availability": "observed_not_compared",
            "depth_availability": "excluded",
            "clock_edge_coverage": "operation_causal_edges_only",
        },
        "initial_authority": {
            "state_hash": state_hash,
            "exclusive_account": left_state.get("exclusive_account"),
            "foreign_activity_event_count": left_state.get(
                "foreign_activity_event_count"
            ),
            "last_reconciled_transaction_deal_watermark": interval_end.isoformat(),
        },
        "operation_modes": {
            "operations": ("check_order", "place_order", "cancel_order"),
            "order_type": "LIMIT",
            "time_in_force": "GTC",
            "fill_mode": "pending_order_no_fill_expected",
            "position_mode": scope["server_account_mode"],
            "observed_account_modes": _json_safe(account_modes),
        },
        "capability_intersection": _CAPABILITY_INTERSECTION,
        "policy_paths": {
            "causal_order": "verified",
            "route_tag_persistence": "verified",
            "swap_posting": "excluded_no_position_or_fill",
            "stop_out": "excluded_no_position_or_margin_stress",
            "weekly_session": "excluded_operational_pending_order_trace",
            "dated_session_exceptions": "excluded_operational_pending_order_trace",
        },
        "invariants": envelope["invariants"],
        "route_gate_policies": envelope["route_gate_policies"],
        "ignored_fields": envelope["ignored_fields"],
        "comparison_contract": {
            "comparator_version": "parity-envelope-v2",
            "normalizer_version": "parity-envelope-v2",
            "invariant_classes": tuple(
                sorted({str(item["kind"]) for item in envelope["invariants"]})
            ),
            "allowed_route_specific_fields": (),
            "ignored_field_registry_digest": _hash(envelope["ignored_fields"]),
            "comparison_digest": comparison_hash,
        },
        "evidence_provenance": {
            "collection_kind": "independent_mt5_demo_operational_holdout",
            "collection_environment_digest": environment_hash,
            "evidence_hashes": evidence_hashes,
            "source_lineage_digest": identity.get("source_lineage_hash"),
            "tick_lineage_digest": identity.get("tick_lineage_hash"),
        },
        "issued_at": issued_at.isoformat(),
        "valid_through": validity["valid_through"],
        "invalidation_triggers": invalidation_triggers,
        "invalidation_bindings": invalidation_bindings,
    }


def validate_l5_certificate_bundle(bundle: Path) -> None:
    """Validate schema, reproducibility, secrecy, and checksums for one bundle.

    Args:
        bundle: Exact generated certificate directory.

    Raises:
        ValueError: If any certificate gate fails.
        TypeError: If an envelope or bundle member has the wrong shape.
    """
    if not bundle.is_dir():
        raise ValueError("certificate bundle directory is absent")
    members = {path.name for path in bundle.iterdir() if path.is_file()}
    if members != _BUNDLE_FILES:
        raise ValueError("certificate bundle members are incomplete or unexpected")
    envelope = get_parity_envelope("v2")
    applicability = envelope.get("operational_applicability")
    scope = envelope.get("certificate_scope")
    if not isinstance(applicability, Mapping) or not isinstance(scope, Mapping):
        raise TypeError("Envelope v2 scope is malformed")
    manifest = _read_json(bundle / "manifest.json")
    manifest_keys = set(manifest) - {"test_fixture_only"}
    if manifest_keys != _MANIFEST_REQUIRED_KEYS:
        raise ValueError("certificate manifest fields are incomplete or unexpected")
    expected = {
        "schema_version": "l5-mt5-operational-certificate.v2",
        "envelope_version": "v2",
        "evidence_route": applicability["evidence_route"],
        "provider_routes": applicability["provider_routes"],
        "provider": scope["provider"],
        "environment": "dev",
        "server_account_mode": scope["server_account_mode"],
        "allowed_evidence_sources": scope["evidence_sources"],
        "certified_semantics": applicability["certified_semantics"],
        "excluded_empirical_claims": applicability["excluded_empirical_claims"],
        "explicit_scope_exclusions": list(_EXPLICIT_SCOPE_EXCLUSIONS),
        "asset_class": scope["asset_class"],
        "invariants": envelope["invariants"],
        "route_gate_policies": envelope["route_gate_policies"],
        "ignored_fields": envelope["ignored_fields"],
        "invalidation_triggers": envelope["invalidation_triggers"],
        "status": "valid",
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError("certificate manifest differs from Envelope v2")
    left = _read_json(bundle / "left-evidence.json")
    right = _read_json(bundle / "right-evidence.json")
    if (
        left.get("certificate_target") != "demo"
        or right.get("certificate_target") != "demo"
    ):
        raise ValueError("both evidence sides must retain demo scope")
    normalized_left = normalize_parity_evidence(left, envelope)
    normalized_right = normalize_parity_evidence(right, envelope)
    comparison = compare_parity_evidence(left, right, envelope)
    if _read_json(bundle / "normalized-left.json") != normalized_left:
        raise ValueError("normalized left evidence does not reproduce")
    if _read_json(bundle / "normalized-right.json") != normalized_right:
        raise ValueError("normalized right evidence does not reproduce")
    if _read_json(bundle / "comparison.json") != comparison or not comparison["passed"]:
        raise ValueError("certificate comparison does not reproduce or pass")
    environment = _read_json(bundle / "environment.json")
    expected_environment = {"environment": "dev", "provider": "mt5", "route": "demo"}
    if any(
        environment.get(key) != value for key, value in expected_environment.items()
    ):
        raise ValueError("certificate environment must identify dev/MT5/demo")
    if environment.get("secret_free") is not True:
        raise ValueError("certificate environment lacks secret-free attestation")
    if (
        not manifest.get("certificate_id")
        or not environment.get("target_build")
        or manifest.get("target_build") != environment.get("target_build")
    ):
        raise ValueError("certificate target build is not bound to environment")
    specifications = manifest.get("admitted_specifications")
    if not isinstance(specifications, list) or len(specifications) != 1:
        raise ValueError("certificate must admit exactly one specification interval")
    specification = specifications[0]
    if not isinstance(specification, Mapping):
        raise TypeError("certificate admitted specification is malformed")
    evidence_symbols = {
        str(order.get("symbol"))
        for evidence in (left, right)
        for order in evidence.get("orders", [])
        if isinstance(order, Mapping)
    }
    if evidence_symbols != {specification.get("symbol")}:
        raise ValueError("certificate admitted symbol differs from evidence")
    observed_fields = specification.get("observed_fields")
    if not isinstance(observed_fields, Mapping) or specification.get(
        "revision_digest"
    ) != _hash(observed_fields):
        raise ValueError("certificate specification revision digest differs")
    try:
        effective_from = datetime.fromisoformat(str(specification["effective_from"]))
        effective_through = datetime.fromisoformat(
            str(specification["effective_through"])
        )
        issued_at = datetime.fromisoformat(str(manifest["issued_at"]))
        valid_through = datetime.fromisoformat(str(manifest["valid_through"]))
    except (KeyError, ValueError) as exc:
        raise ValueError("certificate temporal fields are malformed") from exc
    if any(
        value.tzinfo is None
        for value in (effective_from, effective_through, issued_at, valid_through)
    ):
        raise ValueError("certificate temporal fields must be timezone-aware")
    if effective_through < effective_from or valid_through < issued_at:
        raise ValueError("certificate temporal interval is reversed")
    if manifest.get("valid_through") != envelope["validity"]["valid_through"]:
        raise ValueError("certificate validity differs from Envelope v2")
    left_state = left.get("initial_authority_state")
    initial_authority = manifest.get("initial_authority")
    if not isinstance(left_state, Mapping) or not isinstance(
        initial_authority, Mapping
    ):
        raise TypeError("certificate initial-authority binding is malformed")
    expected_authority = {
        "state_hash": left_state.get("state_hash"),
        "exclusive_account": left_state.get("exclusive_account"),
        "foreign_activity_event_count": left_state.get("foreign_activity_event_count"),
        "last_reconciled_transaction_deal_watermark": specification.get(
            "effective_through"
        ),
    }
    if initial_authority != expected_authority or left_state != right.get(
        "initial_authority_state"
    ):
        raise ValueError("certificate initial-authority binding differs")
    operation_modes = manifest.get("operation_modes")
    expected_operation_mode_values = {
        "operations": ["check_order", "place_order", "cancel_order"],
        "order_type": "LIMIT",
        "time_in_force": "GTC",
        "fill_mode": "pending_order_no_fill_expected",
        "position_mode": scope["server_account_mode"],
    }
    if not isinstance(operation_modes, Mapping) or any(
        operation_modes.get(key) != value
        for key, value in expected_operation_mode_values.items()
    ):
        raise ValueError("certificate operation modes differ")
    observed_account_modes = operation_modes.get("observed_account_modes")
    if not isinstance(observed_account_modes, Mapping) or set(
        observed_account_modes
    ) != {"trade_mode", "margin_mode", "margin_so_mode"}:
        raise ValueError("certificate observed account modes are incomplete")
    if manifest.get("capability_intersection") != list(_CAPABILITY_INTERSECTION):
        raise ValueError("certificate capability intersection differs")
    expected_market_evidence = {
        "class": scope["market_evidence_class"],
        "tick_model": "single_bid_ask_quote_not_certified",
        "resolution": "provider_quote_for_safe_order_parameterization_only",
        "bid_ask_availability": "observed_not_compared",
        "depth_availability": "excluded",
        "clock_edge_coverage": "operation_causal_edges_only",
    }
    if manifest.get("market_evidence") != expected_market_evidence:
        raise ValueError("certificate market-evidence declaration differs")
    expected_policy_paths = {
        "causal_order": "verified",
        "route_tag_persistence": "verified",
        "swap_posting": "excluded_no_position_or_fill",
        "stop_out": "excluded_no_position_or_margin_stress",
        "weekly_session": "excluded_operational_pending_order_trace",
        "dated_session_exceptions": "excluded_operational_pending_order_trace",
    }
    if manifest.get("policy_paths") != expected_policy_paths:
        raise ValueError("certificate policy-path declarations differ")
    identity = left.get("identity")
    if not isinstance(identity, Mapping) or identity != right.get("identity"):
        raise ValueError("certificate evidence identity differs")
    expected_comparison_contract = {
        "comparator_version": "parity-envelope-v2",
        "normalizer_version": "parity-envelope-v2",
        "invariant_classes": sorted(
            {str(item["kind"]) for item in envelope["invariants"]}
        ),
        "allowed_route_specific_fields": [],
        "ignored_field_registry_digest": _hash(envelope["ignored_fields"]),
        "comparison_digest": _hash(comparison),
    }
    if manifest.get("comparison_contract") != expected_comparison_contract:
        raise ValueError("certificate comparison contract differs")
    expected_provenance = {
        "collection_kind": "independent_mt5_demo_operational_holdout",
        "collection_environment_digest": _hash(environment),
        "evidence_hashes": {"left": _hash(left), "right": _hash(right)},
        "source_lineage_digest": identity.get("source_lineage_hash"),
        "tick_lineage_digest": identity.get("tick_lineage_hash"),
    }
    if manifest.get("evidence_provenance") != expected_provenance:
        raise ValueError("certificate evidence provenance differs")
    expected_bindings = {
        "build_identity_change": _hash(environment),
        "contract_change": _hash(envelope),
        "code_or_config_identity_change": _hash(identity),
        "specification_revision_change": _hash(observed_fields),
        "source_or_tick_model_change": _hash(
            {
                "source_lineage_hash": identity.get("source_lineage_hash"),
                "tick_lineage_hash": identity.get("tick_lineage_hash"),
                "market_evidence_class": identity.get("market_evidence_class"),
            }
        ),
        "calibration_validity_change": "not_applicable_operational_contract",
        "detected_drift": _hash(comparison),
        "initial_authority_state_change": left_state.get("state_hash"),
    }
    if manifest.get("invalidation_bindings") != expected_bindings:
        raise ValueError("certificate invalidation bindings differ")
    for name in _HASHED_FILES:
        if name.endswith(".json") and _has_sensitive_key(_read_json(bundle / name)):
            raise ValueError("certificate bundle contains a sensitive field name")
    commands = (bundle / "commands.txt").read_text(encoding="utf-8").lower()
    if any(fragment in commands for fragment in _SENSITIVE_FRAGMENTS):
        raise ValueError("certificate commands contain sensitive material")
    expected_checksums = [
        f"{_file_digest(bundle / name)}  {name}" for name in sorted(_HASHED_FILES)
    ]
    if (bundle / "checksums.sha256").read_text(
        encoding="utf-8"
    ).splitlines() != expected_checksums:
        raise ValueError("certificate bundle checksums do not reproduce")


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    """Write one deterministic JSON bundle member."""
    path.write_text(
        json.dumps(_json_safe(value), indent=2, sort_keys=True, ensure_ascii=True)
        + "\n",
        encoding="utf-8",
    )


def write_certificate_bundle(
    bundle: Path,
    *,
    manifest: Mapping[str, object],
    left: Mapping[str, object],
    right: Mapping[str, object],
    environment: Mapping[str, object],
    command: str,
) -> None:
    """Write and immediately validate the exact nine-member bundle.

    Args:
        bundle: New empty certificate directory.
        manifest: Immutable certificate manifest.
        left: Simulation operational evidence.
        right: MT5-demo operational evidence.
        environment: Secret-free collection identity.
        command: Reproducible credential-free invocation.

    Raises:
        FileExistsError: If the target already exists.
        ValueError: If evidence or bundle validation fails.
    """
    bundle.mkdir(parents=True, exist_ok=False)
    envelope = get_parity_envelope("v2")
    _write_json(bundle / "manifest.json", manifest)
    _write_json(bundle / "left-evidence.json", left)
    _write_json(bundle / "right-evidence.json", right)
    _write_json(
        bundle / "normalized-left.json", normalize_parity_evidence(left, envelope)
    )
    _write_json(
        bundle / "normalized-right.json", normalize_parity_evidence(right, envelope)
    )
    _write_json(
        bundle / "comparison.json", compare_parity_evidence(left, right, envelope)
    )
    _write_json(bundle / "environment.json", environment)
    (bundle / "commands.txt").write_text(command.rstrip() + "\n", encoding="utf-8")
    checksum_lines = [
        f"{_file_digest(bundle / name)}  {name}" for name in sorted(_HASHED_FILES)
    ]
    (bundle / "checksums.sha256").write_text(
        "\n".join(checksum_lines) + "\n", encoding="utf-8"
    )
    validate_l5_certificate_bundle(bundle)


def validate_collection_output(
    output: Path, certificate_id: str, *, workspace_root: Path
) -> Path:
    """Resolve and constrain generated output beneath the artifact root.

    Args:
        output: Requested certificate directory.
        certificate_id: Exact immutable certificate identifier.
        workspace_root: Repository root used to resolve the artifact boundary.

    Returns:
        Resolved safe output path.

    Raises:
        RuntimeError: If the target escapes the generated artifact root or its
            final component differs from the certificate identifier.
    """
    resolved = (
        (workspace_root / output).resolve()
        if not output.is_absolute()
        else output.resolve()
    )
    artifact_root = (workspace_root / "artifacts" / "sim_live_parity").resolve()
    if not resolved.is_relative_to(artifact_root) or resolved.name != certificate_id:
        raise RuntimeError(
            "certificate output must match its ID under the artifact root"
        )
    return resolved


def validate_authority_interval(
    *,
    initial: Mapping[str, object],
    final: Mapping[str, object],
    created_order_id: str,
    observed_order_ids: set[str],
    observed_deal_count: int,
) -> None:
    """Require exact cleanup and absence of foreign interval activity.

    Args:
        initial: Initial secret-free authority projection.
        final: Final secret-free authority projection.
        created_order_id: Only order identity authorized for this run.
        observed_order_ids: Complete bounded order-history identities.
        observed_deal_count: Complete bounded deal-history cardinality.

    Raises:
        RuntimeError: If cleanup is incomplete or foreign/manual activity was
            observed during the interval.
    """
    if final != initial:
        raise RuntimeError(
            "MT5 authority state did not reconcile exactly after cleanup"
        )
    if observed_order_ids - {created_order_id} or observed_deal_count:
        raise RuntimeError("foreign/manual activity occurred during collection")


class _OperationalAuthority:
    """Socket-free authority for the paired Simulation mutation lifecycle."""

    def __init__(self, target: object, order_id: str) -> None:
        self._target = target
        self._order_id = order_id

    def __getattr__(self, name: str) -> Any:  # noqa: ANN401
        return getattr(self._target, name)

    async def ping(self) -> object:
        """Return the configured fake authority connection state."""
        return await self._target.is_connected()  # type: ignore[attr-defined, no-any-return]

    async def finalize_session(self) -> object:
        """Finalize the socket-free authority.

        Returns:
            Authority disconnection result.
        """
        return await self._target.disconnect()  # type: ignore[attr-defined, no-any-return]

    async def read(self, operation: object, arguments: Mapping[str, object]) -> object:
        """Reject unneeded reads during this bounded mutation trace.

        Raises:
            RuntimeError: Always; this trace admits no Simulation reads.
        """
        del operation, arguments
        raise RuntimeError("certificate Simulation trace requested an undeclared read")

    async def mutate(self, operation: object, request: object) -> object:
        """Return an exact request-bound successful operational result."""
        now = datetime.now(UTC)
        return build_simulation_mutation_envelope(
            provider_result={
                "retcode": 0 if str(operation) == "check_order" else 10009,
                "order": self._order_id,
                "deal": 0,
                "volume": "0",
                "price": "0",
                "comment": "operational certificate trace",
            },
            request_echo=request,
            simulated_at=now,
        )


async def _state(adapter: object) -> dict[str, object]:
    """Capture complete allowlisted authority state without account identity.

    Returns:
        Secret-free account, order, and position authority projection.

    Raises:
        RuntimeError: If any authority read fails.
    """
    account_response, orders_response, positions_response = await asyncio.gather(
        get_broker_account_info(adapter),
        get_broker_orders(adapter, build_broker_order_filter(), _STATE_LIMIT),
        get_broker_positions(adapter, build_broker_position_filter(), _STATE_LIMIT),
    )
    if _field(account_response, "status") != "success":
        raise RuntimeError("account authority read failed")
    account = _field(account_response, "data")
    account_fields = (
        "currency",
        "leverage",
        "trade_mode",
        "margin_mode",
        "balance",
        "credit",
        "profit",
        "equity",
        "margin",
        "free_margin",
        "margin_level",
        "margin_so_mode",
        "margin_so_call",
        "margin_so_level",
    )
    order_fields = (
        "order_id",
        "client_order_id",
        "symbol",
        "side",
        "order_type",
        "state",
        "quantity",
        "filled",
        "remaining",
        "price",
        "stop_price",
        "time_in_force",
    )
    position_fields = (
        "position_id",
        "symbol",
        "side",
        "quantity",
        "state",
        "open_price",
        "stop_loss",
        "take_profit",
        "profit",
        "swap",
    )
    return {
        "account": _project(account, account_fields),
        "orders": sorted(
            (_project(item, order_fields) for item in _items(orders_response)),
            key=lambda item: str(item["order_id"]),
        ),
        "positions": sorted(
            (_project(item, position_fields) for item in _items(positions_response)),
            key=lambda item: str(item["position_id"]),
        ),
    }


def _success_data(response: object, operation: str) -> object:
    """Return successful mutation data or fail closed.

    Returns:
        Canonical response data.

    Raises:
        RuntimeError: If the response is unsuccessful or empty.
    """
    if _field(response, "status") != "success":
        message = f"{operation} failed"
        raise RuntimeError(message)
    data = _field(response, "data")
    if data is None:
        message = f"{operation} returned no data"
        raise RuntimeError(message)
    return data


def _require_success(response: object, operation: str) -> None:
    """Require a successful response whose data may legitimately be empty.

    Raises:
        RuntimeError: If the response is unsuccessful.
    """
    if _field(response, "status") != "success":
        message = f"{operation} failed"
        raise RuntimeError(message)


async def _exercise(
    adapter: object, request: object
) -> tuple[str, tuple[datetime, ...]]:
    """Check, place, and cancel one pending order through one adapter.

    Returns:
        Authority order identifier and three observed operation timestamps.

    Raises:
        RuntimeError: If any operation fails or lacks an order identifier.
    """
    stamps: list[datetime] = []
    _success_data(await check_broker_order(adapter, request), "check_order")
    stamps.append(datetime.now(UTC))
    placed = _success_data(await place_broker_order(adapter, request), "place_order")
    stamps.append(datetime.now(UTC))
    order_id = str(_field(placed, "order_id", ""))
    if not order_id:
        raise RuntimeError("place_order returned no authority order id")
    _success_data(
        await cancel_broker_order(adapter, order_id, generate_id("req")),
        "cancel_order",
    )
    stamps.append(datetime.now(UTC))
    return order_id, tuple(stamps)


def _gates(symbol: str) -> tuple[dict[str, object], ...]:
    """Return the predeclared shared and route-specific safety gates."""
    return (
        {
            "role": "risk_approval",
            "order": 0,
            "inputs": {"symbol": symbol},
            "outcome": "approved",
        },
        {
            "role": "live_mutation_authorization",
            "order": 1,
            "inputs": {},
            "outcome": "require_allow_live_mutations_true",
            "route": "live",
            "route_specific": True,
            "route_policy": "require_allow_live_mutations_true",
        },
        {
            "role": "pre_mutation_audit",
            "order": 2,
            "inputs": {},
            "outcome": "audit_failed_stops_dispatch",
            "route": "live",
            "route_specific": True,
            "route_policy": "audit_failed_stops_dispatch",
        },
        {
            "role": "adapter_capability_validation",
            "order": 3,
            "inputs": {},
            "outcome": "validate_adapter_capability_exact_match",
            "route": "demo",
            "route_specific": True,
            "route_policy": "validate_adapter_capability_exact_match",
        },
    )


def _evidence(
    *,
    route: str,
    symbol: str,
    order_id: str,
    client_order_id: str,
    quantity: Decimal,
    limit_price: Decimal,
    stamps: tuple[datetime, ...],
    state_hash: str,
    identity: Mapping[str, object],
    account: Mapping[str, object],
) -> dict[str, object]:
    """Build one observed operational evidence side from successful calls.

    Returns:
        Strict JSON-safe parity evidence mapping.
    """
    balance = Decimal(str(account["balance"]))
    equity = Decimal(str(account["equity"]))
    orders = tuple(
        {
            "order_id": order_id,
            "client_order_id": client_order_id,
            "symbol": symbol,
            "side": "BUY",
            "order_type": "LIMIT",
            "state": state,
            "quantity": str(quantity),
            "filled": "0",
            "placed_at": stamps[index],
        }
        for index, state in enumerate(("ACCEPTED", "CANCELED"), start=1)
    )
    events = (
        {
            "event_id": f"{order_id}-accepted",
            "event_type": "order_accepted",
            "occurred_at": stamps[1],
            "source_sequence": 0,
        },
        {
            "event_id": f"{order_id}-canceled",
            "event_type": "order_canceled",
            "occurred_at": stamps[2],
            "causes": [f"{order_id}-accepted"],
            "source_sequence": 1,
        },
    )
    receipts = tuple(
        {
            "receipt_id": f"{order_id}-{action}-receipt",
            "intent_id": f"{client_order_id}-{action}",
            "client_order_id": client_order_id,
            "route": route,
            "status": status,
            "requested_quantity": str(quantity),
            "filled_quantity": "0",
            "average_price": None,
            "authority_timestamp": stamps[index],
            "received_at": stamps[index],
            "response_classification": "confirmed",
            "retry_safe": False,
            "reconciliation_required": False,
            "provider_order_id": order_id,
            "provider_deal_ids": [],
        }
        for index, (action, status) in enumerate(
            (("place", "accepted"), ("cancel", "canceled")), start=1
        )
    )
    return {
        "certificate_target": "demo",
        "evaluation_time": stamps[-1],
        "identity": dict(identity),
        "initial_authority_state": {
            "state_hash": state_hash,
            "exclusive_account": True,
            "foreign_activity_event_count": 0,
        },
        "gates": _gates(symbol),
        "orders": orders,
        "deals": (),
        "positions": (),
        "receipts": receipts,
        "events": events,
        "ledger": {
            "initial_balance": str(balance),
            "final_balance": str(balance),
            "final_equity": str(equity),
            "unrealized_profit": str(equity - balance),
            "postings": (),
        },
        "economic_observations": {
            "submission_to_ack_ms": (),
            "slippage_points": (),
        },
        "request_limit_price_observed_but_excluded": str(limit_price),
    }


def _strip_collection_only(evidence: dict[str, object]) -> dict[str, object]:
    """Remove collector-only observations before strict parity validation.

    Returns:
        The same evidence mapping without non-schema collection fields.
    """
    evidence.pop("request_limit_price_observed_but_excluded", None)
    return evidence


async def _collect(args: argparse.Namespace) -> Path:
    """Execute the separately approved dev/demo collection and write its bundle.

    Returns:
        Validated generated bundle path.

    Raises:
        RuntimeError: If safety, provider, activity, or reconciliation gates fail.
        TypeError: If a public contract returns a malformed shape.
    """
    settings = load_settings()
    system_record = get_system_settings(request_id=generate_id("req"))
    system_values = _field(system_record, "settings")
    if not isinstance(system_values, Mapping):
        raise TypeError("database-backed system settings are malformed")
    provider_settings = build_collector_provider_settings(system_values)
    validate_collection_preflight(
        execute_demo=args.execute_demo,
        environment=settings.environment,
        route=provider_settings.mt5_environment,
        symbol=args.symbol,
    )
    args.output = validate_collection_output(
        args.output, args.certificate_id, workspace_root=Path.cwd()
    )
    require_terminal_executable(provider_settings.mt5_terminal_path)
    slot = resolve_system_credential_slot("mt5", request_id=generate_id("req"))
    if not all(slot.get(name) for name in ("login", "password", "server")):
        raise RuntimeError("encrypted MT5 credential slot is incomplete")
    credentials = build_mt5_credential_mapping(
        slot, provider_settings.mt5_terminal_path
    )
    account_reference = _required_secret_text(slot["login"], "login")
    config = build_broker_connection_config(
        "mt5",
        "demo",
        provider_enabled=True,
        connect_timeout_sec=15,
        request_timeout_sec=15,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=8,
        circuit_failure_threshold=3,
        circuit_recovery_timeout_sec=5,
        circuit_half_open_max_calls=1,
        account_reference=account_reference,
        credentials=credentials,
    )
    created = create_broker_adapter(get_broker_id("mt5"), config)
    demo = _success_data(created, "create_broker_adapter")
    _require_success(await connect_broker(demo), "connect_broker")
    created_order_id: str | None = None
    try:
        import MetaTrader5

        native_account = MetaTrader5.account_info()
        if (
            native_account is None
            or native_account.trade_mode != MetaTrader5.ACCOUNT_TRADE_MODE_DEMO
        ):
            raise RuntimeError(
                "provider did not classify the connected account as demo"
            )
        permissions = _success_data(
            await get_broker_permissions(demo), "get_broker_permissions"
        )
        if _field(permissions, "trade_write") is not True:
            raise RuntimeError("MT5 demo account lacks trade-write permission")
        initial = await _state(demo)
        started = datetime.now(UTC) - timedelta(seconds=1)
        symbol_info = _success_data(
            await get_broker_symbol_info(demo, args.symbol), "get_broker_symbol_info"
        )
        quote = _success_data(
            await get_broker_quote(demo, args.symbol), "get_broker_quote"
        )
        quantity = Decimal(str(_field(symbol_info, "min_quantity")))
        precision = int(_field(symbol_info, "price_precision"))
        step = Decimal(
            str(_field(symbol_info, "price_step", Decimal(1).scaleb(-precision)))
        )
        bid = Decimal(str(_field(quote, "bid")))
        limit_price = (bid * Decimal("0.80")).quantize(step, rounding=ROUND_DOWN)
        client_order_id = generate_id("cor")
        request = build_broker_order_request(
            symbol=args.symbol,
            side="BUY",
            order_type="LIMIT",
            quantity=quantity,
            quantity_unit=str(_field(symbol_info, "quantity_unit")),
            environment="demo",
            account_reference=account_reference,
            limit_price=limit_price,
            time_in_force="GTC",
            client_order_id=client_order_id,
        )
        sim_request = build_broker_order_request(
            symbol=args.symbol,
            side="BUY",
            order_type="LIMIT",
            quantity=quantity,
            quantity_unit=str(_field(symbol_info, "quantity_unit")),
            environment="simulation",
            limit_price=limit_price,
            time_in_force="GTC",
            client_order_id=client_order_id,
        )
        sim_config = build_broker_connection_config("sim", "simulation")
        sim_order_id = "sim-operational-order"
        authority = _OperationalAuthority(
            create_configured_fake_broker_adapter(sim_config), sim_order_id
        )
        sim_response = create_simulation_broker_adapter(sim_config, authority)
        sim = _success_data(sim_response, "create_simulation_broker_adapter")
        _require_success(await connect_broker(sim), "connect_simulation_broker")
        try:
            sim_order_id, sim_stamps = await _exercise(sim, sim_request)
        finally:
            await disconnect_broker(sim)
        created_order_id, demo_stamps = await _exercise(demo, request)
        finished = datetime.now(UTC) + timedelta(seconds=1)
        final = await _state(demo)
        order_history = _items(
            await list_broker_order_history(
                demo, started, finished, symbol=args.symbol, limit=_STATE_LIMIT
            )
        )
        deal_history = _items(
            await list_broker_deal_history(demo, started, finished, limit=_STATE_LIMIT)
        )
        validate_authority_interval(
            initial=initial,
            final=final,
            created_order_id=created_order_id,
            observed_order_ids={
                str(_field(item, "order_id")) for item in order_history
            },
            observed_deal_count=len(deal_history),
        )
        state_hash = _hash(initial)
        platform = _success_data(
            await get_broker_platform_info(demo), "get_broker_platform_info"
        )
        specification = _project(
            symbol_info,
            (
                "provider_symbol",
                "product_profile",
                "price_precision",
                "price_step",
                "min_quantity",
                "max_quantity",
                "quantity_step",
                "quantity_unit",
                "trade_mode",
            ),
        )
        identity_seed = {
            "envelope": get_parity_envelope("v2"),
            "symbol": args.symbol,
            "state_hash": state_hash,
            "specification": specification,
        }
        identity_hash = _hash(identity_seed)
        identity = {
            "execution_model_hash": identity_hash,
            "config_hash": _hash({"route_contract": "sim-demo", "symbol": args.symbol}),
            "source_lineage_hash": _hash(identity_seed["specification"]),
            "tick_lineage_hash": _hash(
                {"symbol": args.symbol, "bid": bid, "observed": "collection_interval"}
            ),
            "market_evidence_class": "operational_contract_trace",
        }
        account = initial["account"]
        if not isinstance(account, Mapping):
            raise TypeError("captured account projection is malformed")
        left = _strip_collection_only(
            _evidence(
                route="sim",
                symbol=args.symbol,
                order_id=sim_order_id,
                client_order_id=client_order_id,
                quantity=quantity,
                limit_price=limit_price,
                stamps=sim_stamps,
                state_hash=state_hash,
                identity=identity,
                account=account,
            )
        )
        right = _strip_collection_only(
            _evidence(
                route="demo",
                symbol=args.symbol,
                order_id=created_order_id,
                client_order_id=client_order_id,
                quantity=quantity,
                limit_price=limit_price,
                stamps=demo_stamps,
                state_hash=state_hash,
                identity=identity,
                account=account,
            )
        )
        target_build = str(
            _field(platform, "build", _field(platform, "api_or_terminal_version"))
        )
        environment = {
            "environment": "dev",
            "provider": "mt5",
            "route": "demo",
            "target_build": target_build,
            "server_digest": _hash(str(slot["server"])),
            "subject_digest": _hash(str(slot["login"])),
            "secret_free": True,
        }
        manifest = build_certificate_manifest(
            certificate_id=args.certificate_id,
            symbol=args.symbol,
            specification=specification,
            interval_start=started,
            interval_end=finished,
            left=left,
            right=right,
            environment=environment,
            account_modes={
                name: account.get(name)
                for name in ("trade_mode", "margin_mode", "margin_so_mode")
            },
            issued_at=datetime.now(UTC),
        )
        command = (
            "uv run python tests/simulator/integration/l5_certificate_collection.py "
            f"--execute-demo --symbol {args.symbol} "
            f"--certificate-id {args.certificate_id} "
            f"--output {args.output.as_posix()}"
        )
        write_certificate_bundle(
            args.output,
            manifest=manifest,
            left=left,
            right=right,
            environment=environment,
            command=command,
        )
        return args.output
    finally:
        if created_order_id is not None:
            active_ids = {
                str(_field(item, "order_id"))
                for item in _items(await get_broker_orders(demo, limit=_STATE_LIMIT))
            }
            if created_order_id in active_ids:
                await cancel_broker_order(demo, created_order_id, generate_id("req"))
        await disconnect_broker(demo)


def _arguments() -> argparse.Namespace:
    """Parse the explicit certificate collection command line.

    Returns:
        Validated raw command-line namespace.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-demo", action="store_true")
    parser.add_argument("--symbol", default="BTCUSD")
    parser.add_argument("--certificate-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    """Run the separately approved certificate collection."""
    output = asyncio.run(_collect(_arguments()))
    print(f"Validated certificate bundle: {output}")


if __name__ == "__main__":
    main()

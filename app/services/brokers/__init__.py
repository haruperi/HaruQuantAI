"""Approved Brokers domain package-root public API.

Every cross-domain consumer must import these standalone functions from
``app.services.brokers``. The public API surface consists exclusively of
standalone functions. Classes, contracts, DTOs, enums, and protocols remain
internal implementation details.
"""

import typing

# Explicit imports keep type checking exact; runtime stays lazy.
if typing.TYPE_CHECKING:
    from app.services.brokers._shared.connections import (
        create_connected_broker,
        resolve_provider_connection_config,
    )
    from app.services.brokers._shared.factory import (
        create_broker_adapter,
        get_registered_brokers,
    )
    from app.services.brokers._shared.health import record_yahoo_health_checkpoint
    from app.services.brokers._shared.public import (
        attach_broker_protection,
        build_broker_order_protection_request,
        build_broker_position_reduce_request,
        calculate_broker_margin,
        calculate_broker_profit,
        cancel_broker_order,
        check_broker_order,
        close_broker_position,
        connect_broker,
        disconnect_broker,
        get_broker_account_info,
        get_broker_asset_info,
        get_broker_balances,
        get_broker_commission_estimate,
        get_broker_connection_events,
        get_broker_connection_status,
        get_broker_deal,
        get_broker_feature_flags,
        get_broker_historical_bars,
        get_broker_last_error,
        get_broker_market_status,
        get_broker_order,
        get_broker_order_book,
        get_broker_orders,
        get_broker_permissions,
        get_broker_platform_info,
        get_broker_position,
        get_broker_positions,
        get_broker_quote,
        get_broker_server_time,
        get_broker_spread,
        get_broker_symbol_info,
        get_broker_symbols,
        get_broker_ticks,
        get_broker_trading_sessions,
        is_broker_connected,
        list_broker_account_transactions,
        list_broker_accounts,
        list_broker_assets,
        list_broker_deal_history,
        list_broker_order_history,
        list_broker_subscriptions,
        modify_broker_order,
        modify_broker_position,
        ping_broker,
        place_broker_order,
        reconnect_broker,
        reduce_broker_position,
        refresh_broker_session,
        replace_broker_order,
        select_broker_account,
        select_broker_symbol,
        subscribe_broker_bars,
        subscribe_broker_order_book,
        subscribe_broker_quotes,
        supports_broker_capability,
        unsubscribe_broker,
    )
    from app.services.brokers.binance.health import record_binance_health_checkpoint
    from app.services.brokers.canonical_contracts.account_snapshot import (
        build_broker_account_snapshot,
        parse_broker_account_snapshot,
    )
    from app.services.brokers.canonical_contracts.error_catalog import (
        get_broker_error_catalog,
    )
    from app.services.brokers.canonical_contracts.health import (
        build_broker_health,
        parse_broker_health,
    )
    from app.services.brokers.canonical_contracts.public import (
        build_broker_connection_config,
        build_broker_margin_request,
        build_broker_order_filter,
        build_broker_order_modification_request,
        build_broker_order_request,
        build_broker_order_request_v2,
        build_broker_position_close_request,
        build_broker_position_filter,
        build_broker_position_modification_request,
        build_broker_profit_request,
        build_broker_value,
        get_broker_adapter_contract_version,
        get_broker_adapter_schema_id,
        get_broker_capability_id,
        get_broker_connection_account_reference,
        get_broker_connection_environment,
        get_broker_connection_id,
        get_broker_environment,
        get_broker_error_code,
        get_broker_feature_flag_environment,
        get_broker_feature_flag_id,
        get_broker_id,
        get_broker_resubmission_policy,
        get_broker_uncertainty,
        get_broker_value_field,
        is_broker_connection_enabled,
    )
    from app.services.brokers.canonical_contracts.reconciliation import (
        build_broker_reconciliation_snapshot,
        parse_broker_reconciliation_snapshot,
    )
    from app.services.brokers.canonical_contracts.unknown_outcome import (
        build_broker_unknown_result,
        enforce_no_blind_resubmission,
        is_broker_unknown_result,
    )
    from app.services.brokers.conformance.public import (
        build_broker_calculation_fixture,
        collect_broker_calculation_fixture,
        create_configured_fake_broker_adapter,
        create_fake_broker_adapter,
        dump_broker_calculation_fixture,
        parse_broker_calculation_fixture,
        run_broker_adapter_conformance,
        set_fake_broker_error,
    )
    from app.services.brokers.ctrader.health import record_ctrader_health_checkpoint
    from app.services.brokers.dukascopy.health import record_dukascopy_health_checkpoint
    from app.services.brokers.metatrader.health import (
        record_metatrader_health_checkpoint,
    )
    from app.services.brokers.metatrader.snapshot_gateway import (
        acquire_metatrader_snapshot_symbols,
        get_metatrader_snapshot_gateway_status,
        release_metatrader_snapshot_symbols,
        start_metatrader_snapshot_gateway,
        stop_metatrader_snapshot_gateway,
        stream_metatrader_book_snapshots,
        stream_metatrader_snapshots,
    )
    from app.services.brokers.metatrader.specifications import (
        build_provider_specification_snapshot,
        dump_provider_specification_snapshot,
        get_broker_provider_specification,
        get_provider_specification_snapshot_field,
        parse_provider_specification_snapshot,
        verify_provider_specification_snapshot,
    )
    from app.services.brokers.migrations.public import run_broker_migrations
    from app.services.brokers.simulation.public import (
        build_simulation_mutation_envelope,
        build_simulation_read_envelope,
        create_simulation_broker_adapter,
        finalize_simulation_broker_session,
    )

# Public export name to the module and attribute that owns it. Resolved on
# first access so importing this boundary never loads every feature.
_EXPORTS: dict[str, tuple[str, str]] = {
    "acquire_metatrader_snapshot_symbols": (
        "app.services.brokers.metatrader.snapshot_gateway",
        "acquire_metatrader_snapshot_symbols",
    ),
    "attach_broker_protection": (
        "app.services.brokers._shared.public",
        "attach_broker_protection",
    ),
    "build_broker_account_snapshot": (
        "app.services.brokers.canonical_contracts.account_snapshot",
        "build_broker_account_snapshot",
    ),
    "build_broker_calculation_fixture": (
        "app.services.brokers.conformance.public",
        "build_broker_calculation_fixture",
    ),
    "build_broker_connection_config": (
        "app.services.brokers.canonical_contracts.public",
        "build_broker_connection_config",
    ),
    "build_broker_health": (
        "app.services.brokers.canonical_contracts.health",
        "build_broker_health",
    ),
    "build_broker_margin_request": (
        "app.services.brokers.canonical_contracts.public",
        "build_broker_margin_request",
    ),
    "build_broker_order_filter": (
        "app.services.brokers.canonical_contracts.public",
        "build_broker_order_filter",
    ),
    "build_broker_order_modification_request": (
        "app.services.brokers.canonical_contracts.public",
        "build_broker_order_modification_request",
    ),
    "build_broker_order_protection_request": (
        "app.services.brokers._shared.public",
        "build_broker_order_protection_request",
    ),
    "build_broker_order_request": (
        "app.services.brokers.canonical_contracts.public",
        "build_broker_order_request",
    ),
    "build_broker_order_request_v2": (
        "app.services.brokers.canonical_contracts.public",
        "build_broker_order_request_v2",
    ),
    "build_broker_position_close_request": (
        "app.services.brokers.canonical_contracts.public",
        "build_broker_position_close_request",
    ),
    "build_broker_position_filter": (
        "app.services.brokers.canonical_contracts.public",
        "build_broker_position_filter",
    ),
    "build_broker_position_modification_request": (
        "app.services.brokers.canonical_contracts.public",
        "build_broker_position_modification_request",
    ),
    "build_broker_position_reduce_request": (
        "app.services.brokers._shared.public",
        "build_broker_position_reduce_request",
    ),
    "build_broker_profit_request": (
        "app.services.brokers.canonical_contracts.public",
        "build_broker_profit_request",
    ),
    "build_broker_reconciliation_snapshot": (
        "app.services.brokers.canonical_contracts.reconciliation",
        "build_broker_reconciliation_snapshot",
    ),
    "build_broker_unknown_result": (
        "app.services.brokers.canonical_contracts.unknown_outcome",
        "build_broker_unknown_result",
    ),
    "build_broker_value": (
        "app.services.brokers.canonical_contracts.public",
        "build_broker_value",
    ),
    "build_provider_specification_snapshot": (
        "app.services.brokers.metatrader.specifications",
        "build_provider_specification_snapshot",
    ),
    "build_simulation_mutation_envelope": (
        "app.services.brokers.simulation.public",
        "build_simulation_mutation_envelope",
    ),
    "build_simulation_read_envelope": (
        "app.services.brokers.simulation.public",
        "build_simulation_read_envelope",
    ),
    "calculate_broker_margin": (
        "app.services.brokers._shared.public",
        "calculate_broker_margin",
    ),
    "calculate_broker_profit": (
        "app.services.brokers._shared.public",
        "calculate_broker_profit",
    ),
    "cancel_broker_order": (
        "app.services.brokers._shared.public",
        "cancel_broker_order",
    ),
    "check_broker_order": ("app.services.brokers._shared.public", "check_broker_order"),
    "close_broker_position": (
        "app.services.brokers._shared.public",
        "close_broker_position",
    ),
    "collect_broker_calculation_fixture": (
        "app.services.brokers.conformance.public",
        "collect_broker_calculation_fixture",
    ),
    "connect_broker": ("app.services.brokers._shared.public", "connect_broker"),
    "create_broker_adapter": (
        "app.services.brokers._shared.factory",
        "create_broker_adapter",
    ),
    "create_configured_fake_broker_adapter": (
        "app.services.brokers.conformance.public",
        "create_configured_fake_broker_adapter",
    ),
    "create_connected_broker": (
        "app.services.brokers._shared.connections",
        "create_connected_broker",
    ),
    "create_fake_broker_adapter": (
        "app.services.brokers.conformance.public",
        "create_fake_broker_adapter",
    ),
    "create_simulation_broker_adapter": (
        "app.services.brokers.simulation.public",
        "create_simulation_broker_adapter",
    ),
    "disconnect_broker": ("app.services.brokers._shared.public", "disconnect_broker"),
    "dump_broker_calculation_fixture": (
        "app.services.brokers.conformance.public",
        "dump_broker_calculation_fixture",
    ),
    "dump_provider_specification_snapshot": (
        "app.services.brokers.metatrader.specifications",
        "dump_provider_specification_snapshot",
    ),
    "enforce_no_blind_resubmission": (
        "app.services.brokers.canonical_contracts.unknown_outcome",
        "enforce_no_blind_resubmission",
    ),
    "finalize_simulation_broker_session": (
        "app.services.brokers.simulation.public",
        "finalize_simulation_broker_session",
    ),
    "get_broker_account_info": (
        "app.services.brokers._shared.public",
        "get_broker_account_info",
    ),
    "get_broker_adapter_contract_version": (
        "app.services.brokers.canonical_contracts.public",
        "get_broker_adapter_contract_version",
    ),
    "get_broker_adapter_schema_id": (
        "app.services.brokers.canonical_contracts.public",
        "get_broker_adapter_schema_id",
    ),
    "get_broker_asset_info": (
        "app.services.brokers._shared.public",
        "get_broker_asset_info",
    ),
    "get_broker_balances": (
        "app.services.brokers._shared.public",
        "get_broker_balances",
    ),
    "get_broker_capability_id": (
        "app.services.brokers.canonical_contracts.public",
        "get_broker_capability_id",
    ),
    "get_broker_commission_estimate": (
        "app.services.brokers._shared.public",
        "get_broker_commission_estimate",
    ),
    "get_broker_connection_account_reference": (
        "app.services.brokers.canonical_contracts.public",
        "get_broker_connection_account_reference",
    ),
    "get_broker_connection_environment": (
        "app.services.brokers.canonical_contracts.public",
        "get_broker_connection_environment",
    ),
    "get_broker_connection_events": (
        "app.services.brokers._shared.public",
        "get_broker_connection_events",
    ),
    "get_broker_connection_id": (
        "app.services.brokers.canonical_contracts.public",
        "get_broker_connection_id",
    ),
    "get_broker_connection_status": (
        "app.services.brokers._shared.public",
        "get_broker_connection_status",
    ),
    "get_broker_deal": ("app.services.brokers._shared.public", "get_broker_deal"),
    "get_broker_environment": (
        "app.services.brokers.canonical_contracts.public",
        "get_broker_environment",
    ),
    "get_broker_error_catalog": (
        "app.services.brokers.canonical_contracts.error_catalog",
        "get_broker_error_catalog",
    ),
    "get_broker_error_code": (
        "app.services.brokers.canonical_contracts.public",
        "get_broker_error_code",
    ),
    "get_broker_feature_flag_environment": (
        "app.services.brokers.canonical_contracts.public",
        "get_broker_feature_flag_environment",
    ),
    "get_broker_feature_flag_id": (
        "app.services.brokers.canonical_contracts.public",
        "get_broker_feature_flag_id",
    ),
    "get_broker_feature_flags": (
        "app.services.brokers._shared.public",
        "get_broker_feature_flags",
    ),
    "get_broker_historical_bars": (
        "app.services.brokers._shared.public",
        "get_broker_historical_bars",
    ),
    "get_broker_id": (
        "app.services.brokers.canonical_contracts.public",
        "get_broker_id",
    ),
    "get_broker_last_error": (
        "app.services.brokers._shared.public",
        "get_broker_last_error",
    ),
    "get_broker_market_status": (
        "app.services.brokers._shared.public",
        "get_broker_market_status",
    ),
    "get_broker_order": ("app.services.brokers._shared.public", "get_broker_order"),
    "get_broker_order_book": (
        "app.services.brokers._shared.public",
        "get_broker_order_book",
    ),
    "get_broker_orders": ("app.services.brokers._shared.public", "get_broker_orders"),
    "get_broker_permissions": (
        "app.services.brokers._shared.public",
        "get_broker_permissions",
    ),
    "get_broker_platform_info": (
        "app.services.brokers._shared.public",
        "get_broker_platform_info",
    ),
    "get_broker_position": (
        "app.services.brokers._shared.public",
        "get_broker_position",
    ),
    "get_broker_positions": (
        "app.services.brokers._shared.public",
        "get_broker_positions",
    ),
    "get_broker_provider_specification": (
        "app.services.brokers.metatrader.specifications",
        "get_broker_provider_specification",
    ),
    "get_broker_quote": ("app.services.brokers._shared.public", "get_broker_quote"),
    "get_broker_resubmission_policy": (
        "app.services.brokers.canonical_contracts.public",
        "get_broker_resubmission_policy",
    ),
    "get_broker_server_time": (
        "app.services.brokers._shared.public",
        "get_broker_server_time",
    ),
    "get_broker_spread": ("app.services.brokers._shared.public", "get_broker_spread"),
    "get_broker_symbol_info": (
        "app.services.brokers._shared.public",
        "get_broker_symbol_info",
    ),
    "get_broker_symbols": ("app.services.brokers._shared.public", "get_broker_symbols"),
    "get_broker_ticks": ("app.services.brokers._shared.public", "get_broker_ticks"),
    "get_broker_trading_sessions": (
        "app.services.brokers._shared.public",
        "get_broker_trading_sessions",
    ),
    "get_broker_uncertainty": (
        "app.services.brokers.canonical_contracts.public",
        "get_broker_uncertainty",
    ),
    "get_broker_value_field": (
        "app.services.brokers.canonical_contracts.public",
        "get_broker_value_field",
    ),
    "get_metatrader_snapshot_gateway_status": (
        "app.services.brokers.metatrader.snapshot_gateway",
        "get_metatrader_snapshot_gateway_status",
    ),
    "get_provider_specification_snapshot_field": (
        "app.services.brokers.metatrader.specifications",
        "get_provider_specification_snapshot_field",
    ),
    "get_registered_brokers": (
        "app.services.brokers._shared.factory",
        "get_registered_brokers",
    ),
    "is_broker_connected": (
        "app.services.brokers._shared.public",
        "is_broker_connected",
    ),
    "is_broker_connection_enabled": (
        "app.services.brokers.canonical_contracts.public",
        "is_broker_connection_enabled",
    ),
    "is_broker_unknown_result": (
        "app.services.brokers.canonical_contracts.unknown_outcome",
        "is_broker_unknown_result",
    ),
    "list_broker_account_transactions": (
        "app.services.brokers._shared.public",
        "list_broker_account_transactions",
    ),
    "list_broker_accounts": (
        "app.services.brokers._shared.public",
        "list_broker_accounts",
    ),
    "list_broker_assets": ("app.services.brokers._shared.public", "list_broker_assets"),
    "list_broker_deal_history": (
        "app.services.brokers._shared.public",
        "list_broker_deal_history",
    ),
    "list_broker_order_history": (
        "app.services.brokers._shared.public",
        "list_broker_order_history",
    ),
    "list_broker_subscriptions": (
        "app.services.brokers._shared.public",
        "list_broker_subscriptions",
    ),
    "modify_broker_order": (
        "app.services.brokers._shared.public",
        "modify_broker_order",
    ),
    "modify_broker_position": (
        "app.services.brokers._shared.public",
        "modify_broker_position",
    ),
    "parse_broker_account_snapshot": (
        "app.services.brokers.canonical_contracts.account_snapshot",
        "parse_broker_account_snapshot",
    ),
    "parse_broker_calculation_fixture": (
        "app.services.brokers.conformance.public",
        "parse_broker_calculation_fixture",
    ),
    "parse_broker_health": (
        "app.services.brokers.canonical_contracts.health",
        "parse_broker_health",
    ),
    "parse_broker_reconciliation_snapshot": (
        "app.services.brokers.canonical_contracts.reconciliation",
        "parse_broker_reconciliation_snapshot",
    ),
    "parse_provider_specification_snapshot": (
        "app.services.brokers.metatrader.specifications",
        "parse_provider_specification_snapshot",
    ),
    "ping_broker": ("app.services.brokers._shared.public", "ping_broker"),
    "place_broker_order": ("app.services.brokers._shared.public", "place_broker_order"),
    "reconnect_broker": ("app.services.brokers._shared.public", "reconnect_broker"),
    "record_binance_health_checkpoint": (
        "app.services.brokers.binance.health",
        "record_binance_health_checkpoint",
    ),
    "record_ctrader_health_checkpoint": (
        "app.services.brokers.ctrader.health",
        "record_ctrader_health_checkpoint",
    ),
    "record_dukascopy_health_checkpoint": (
        "app.services.brokers.dukascopy.health",
        "record_dukascopy_health_checkpoint",
    ),
    "record_metatrader_health_checkpoint": (
        "app.services.brokers.metatrader.health",
        "record_metatrader_health_checkpoint",
    ),
    "record_yahoo_health_checkpoint": (
        "app.services.brokers._shared.health",
        "record_yahoo_health_checkpoint",
    ),
    "reduce_broker_position": (
        "app.services.brokers._shared.public",
        "reduce_broker_position",
    ),
    "refresh_broker_session": (
        "app.services.brokers._shared.public",
        "refresh_broker_session",
    ),
    "release_metatrader_snapshot_symbols": (
        "app.services.brokers.metatrader.snapshot_gateway",
        "release_metatrader_snapshot_symbols",
    ),
    "replace_broker_order": (
        "app.services.brokers._shared.public",
        "replace_broker_order",
    ),
    "resolve_provider_connection_config": (
        "app.services.brokers._shared.connections",
        "resolve_provider_connection_config",
    ),
    "run_broker_adapter_conformance": (
        "app.services.brokers.conformance.public",
        "run_broker_adapter_conformance",
    ),
    "run_broker_migrations": (
        "app.services.brokers.migrations.public",
        "run_broker_migrations",
    ),
    "select_broker_account": (
        "app.services.brokers._shared.public",
        "select_broker_account",
    ),
    "select_broker_symbol": (
        "app.services.brokers._shared.public",
        "select_broker_symbol",
    ),
    "set_fake_broker_error": (
        "app.services.brokers.conformance.public",
        "set_fake_broker_error",
    ),
    "start_metatrader_snapshot_gateway": (
        "app.services.brokers.metatrader.snapshot_gateway",
        "start_metatrader_snapshot_gateway",
    ),
    "stop_metatrader_snapshot_gateway": (
        "app.services.brokers.metatrader.snapshot_gateway",
        "stop_metatrader_snapshot_gateway",
    ),
    "stream_metatrader_book_snapshots": (
        "app.services.brokers.metatrader.snapshot_gateway",
        "stream_metatrader_book_snapshots",
    ),
    "stream_metatrader_snapshots": (
        "app.services.brokers.metatrader.snapshot_gateway",
        "stream_metatrader_snapshots",
    ),
    "subscribe_broker_bars": (
        "app.services.brokers._shared.public",
        "subscribe_broker_bars",
    ),
    "subscribe_broker_order_book": (
        "app.services.brokers._shared.public",
        "subscribe_broker_order_book",
    ),
    "subscribe_broker_quotes": (
        "app.services.brokers._shared.public",
        "subscribe_broker_quotes",
    ),
    "supports_broker_capability": (
        "app.services.brokers._shared.public",
        "supports_broker_capability",
    ),
    "unsubscribe_broker": ("app.services.brokers._shared.public", "unsubscribe_broker"),
    "verify_provider_specification_snapshot": (
        "app.services.brokers.metatrader.specifications",
        "verify_provider_specification_snapshot",
    ),
}


def __getattr__(name: str) -> object:
    """Resolve one public export on first access.

    Args:
        name: Public export name.

    Returns:
        The resolved public function.

    Raises:
        AttributeError: If the name is not part of the public boundary.
    """
    target = _EXPORTS.get(name)
    if target is None:
        message = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(message)
    from importlib import import_module

    return getattr(import_module(target[0]), target[1])


def __dir__() -> list[str]:
    """List the public export surface.

    Returns:
        Sorted public export names.
    """
    return sorted(_EXPORTS)


__all__ = (
    "acquire_metatrader_snapshot_symbols",
    "attach_broker_protection",
    "build_broker_account_snapshot",
    "build_broker_calculation_fixture",
    "build_broker_connection_config",
    "build_broker_health",
    "build_broker_margin_request",
    "build_broker_order_filter",
    "build_broker_order_modification_request",
    "build_broker_order_protection_request",
    "build_broker_order_request",
    "build_broker_order_request_v2",
    "build_broker_position_close_request",
    "build_broker_position_filter",
    "build_broker_position_modification_request",
    "build_broker_position_reduce_request",
    "build_broker_profit_request",
    "build_broker_reconciliation_snapshot",
    "build_broker_unknown_result",
    "build_broker_value",
    "build_provider_specification_snapshot",
    "build_simulation_mutation_envelope",
    "build_simulation_read_envelope",
    "calculate_broker_margin",
    "calculate_broker_profit",
    "cancel_broker_order",
    "check_broker_order",
    "close_broker_position",
    "collect_broker_calculation_fixture",
    "connect_broker",
    "create_broker_adapter",
    "create_configured_fake_broker_adapter",
    "create_connected_broker",
    "create_fake_broker_adapter",
    "create_simulation_broker_adapter",
    "disconnect_broker",
    "dump_broker_calculation_fixture",
    "dump_provider_specification_snapshot",
    "enforce_no_blind_resubmission",
    "finalize_simulation_broker_session",
    "get_broker_account_info",
    "get_broker_adapter_contract_version",
    "get_broker_adapter_schema_id",
    "get_broker_asset_info",
    "get_broker_balances",
    "get_broker_capability_id",
    "get_broker_commission_estimate",
    "get_broker_connection_account_reference",
    "get_broker_connection_environment",
    "get_broker_connection_events",
    "get_broker_connection_id",
    "get_broker_connection_status",
    "get_broker_deal",
    "get_broker_environment",
    "get_broker_error_catalog",
    "get_broker_error_code",
    "get_broker_feature_flag_environment",
    "get_broker_feature_flag_id",
    "get_broker_feature_flags",
    "get_broker_historical_bars",
    "get_broker_id",
    "get_broker_last_error",
    "get_broker_market_status",
    "get_broker_order",
    "get_broker_order_book",
    "get_broker_orders",
    "get_broker_permissions",
    "get_broker_platform_info",
    "get_broker_position",
    "get_broker_positions",
    "get_broker_provider_specification",
    "get_broker_quote",
    "get_broker_resubmission_policy",
    "get_broker_server_time",
    "get_broker_spread",
    "get_broker_symbol_info",
    "get_broker_symbols",
    "get_broker_ticks",
    "get_broker_trading_sessions",
    "get_broker_uncertainty",
    "get_broker_value_field",
    "get_metatrader_snapshot_gateway_status",
    "get_provider_specification_snapshot_field",
    "get_registered_brokers",
    "is_broker_connected",
    "is_broker_connection_enabled",
    "is_broker_unknown_result",
    "list_broker_account_transactions",
    "list_broker_accounts",
    "list_broker_assets",
    "list_broker_deal_history",
    "list_broker_order_history",
    "list_broker_subscriptions",
    "modify_broker_order",
    "modify_broker_position",
    "parse_broker_account_snapshot",
    "parse_broker_calculation_fixture",
    "parse_broker_health",
    "parse_broker_reconciliation_snapshot",
    "parse_provider_specification_snapshot",
    "ping_broker",
    "place_broker_order",
    "reconnect_broker",
    "record_binance_health_checkpoint",
    "record_ctrader_health_checkpoint",
    "record_dukascopy_health_checkpoint",
    "record_metatrader_health_checkpoint",
    "record_yahoo_health_checkpoint",
    "reduce_broker_position",
    "refresh_broker_session",
    "release_metatrader_snapshot_symbols",
    "replace_broker_order",
    "resolve_provider_connection_config",
    "run_broker_adapter_conformance",
    "run_broker_migrations",
    "select_broker_account",
    "select_broker_symbol",
    "set_fake_broker_error",
    "start_metatrader_snapshot_gateway",
    "stop_metatrader_snapshot_gateway",
    "stream_metatrader_book_snapshots",
    "stream_metatrader_snapshots",
    "subscribe_broker_bars",
    "subscribe_broker_order_book",
    "subscribe_broker_quotes",
    "supports_broker_capability",
    "unsubscribe_broker",
    "verify_provider_specification_snapshot",
)

"""Approved function-only public boundary for Portfolio."""

import typing

# Explicit imports keep type checking exact; runtime stays lazy.
if typing.TYPE_CHECKING:
    from app.services.portfolio.api import (
        activate_portfolio,
        assess_portfolio_drift,
        construct_portfolio,
        create_portfolio_handle,
        create_portfolio_value,
        dump_portfolio_value,
        execute_portfolio_handle_operation,
        get_portfolio_definition,
        get_portfolio_error_catalog,
        get_portfolio_history,
        get_portfolio_status,
        get_portfolio_value_field,
        is_portfolio_handle,
        is_portfolio_value,
        recompute_portfolio_measurement,
        register_portfolio_definition,
        rollback_portfolio,
        submit_portfolio_rebalance,
        to_portfolio_error_payload,
    )
    from app.services.portfolio.evidence import validate_construction_evidence
    from app.services.portfolio.ledger import (
        build_reversal_batch,
        build_snapshot,
        cash_balance,
        create_ledger_service,
        ingest_event,
        is_balanced,
        recompute_balances,
        validate_snapshot,
    )
    from app.services.portfolio.ledger.contracts import (
        build_ledger_account,
        build_ledger_entry,
        build_posting_batch,
        parse_ledger_account,
        parse_ledger_entry,
        parse_posting_batch,
    )
    from app.services.portfolio.margin import (
        build_portfolio_risk_health,
        calculate_margin_view,
    )
    from app.services.portfolio.migrations import (
        get_portfolio_migrations,
        run_portfolio_migrations,
    )
    from app.services.portfolio.rebalancing.cross_account import (
        assess_common_mode_exposure,
        measure_cross_account_correlation,
    )
    from app.services.portfolio.reconciliation import (
        build_lifecycle_postings,
        reconcile_portfolio,
    )
    from app.services.portfolio.state.runtime import (
        build_portfolio_state_store,
        execute_portfolio_state_store_operation,
    )
    from app.services.portfolio.valuation import calculate_portfolio_valuation

# Public export name to the module and attribute that owns it. Resolved on
# first access so importing this boundary never loads every feature.
_EXPORTS: dict[str, tuple[str, str]] = {
    "activate_portfolio": ("app.services.portfolio.api", "activate_portfolio"),
    "assess_common_mode_exposure": (
        "app.services.portfolio.rebalancing.cross_account",
        "assess_common_mode_exposure",
    ),
    "assess_portfolio_drift": ("app.services.portfolio.api", "assess_portfolio_drift"),
    "build_ledger_account": (
        "app.services.portfolio.ledger.contracts",
        "build_ledger_account",
    ),
    "build_ledger_entry": (
        "app.services.portfolio.ledger.contracts",
        "build_ledger_entry",
    ),
    "build_lifecycle_postings": (
        "app.services.portfolio.reconciliation",
        "build_lifecycle_postings",
    ),
    "build_portfolio_risk_health": (
        "app.services.portfolio.margin",
        "build_portfolio_risk_health",
    ),
    "build_portfolio_state_store": (
        "app.services.portfolio.state.runtime",
        "build_portfolio_state_store",
    ),
    "build_posting_batch": (
        "app.services.portfolio.ledger.contracts",
        "build_posting_batch",
    ),
    "build_reversal_batch": ("app.services.portfolio.ledger", "build_reversal_batch"),
    "build_snapshot": ("app.services.portfolio.ledger", "build_snapshot"),
    "calculate_margin_view": ("app.services.portfolio.margin", "calculate_margin_view"),
    "calculate_portfolio_valuation": (
        "app.services.portfolio.valuation",
        "calculate_portfolio_valuation",
    ),
    "cash_balance": ("app.services.portfolio.ledger", "cash_balance"),
    "construct_portfolio": ("app.services.portfolio.api", "construct_portfolio"),
    "create_ledger_service": ("app.services.portfolio.ledger", "create_ledger_service"),
    "create_portfolio_handle": (
        "app.services.portfolio.api",
        "create_portfolio_handle",
    ),
    "create_portfolio_value": ("app.services.portfolio.api", "create_portfolio_value"),
    "dump_portfolio_value": ("app.services.portfolio.api", "dump_portfolio_value"),
    "execute_portfolio_handle_operation": (
        "app.services.portfolio.api",
        "execute_portfolio_handle_operation",
    ),
    "execute_portfolio_state_store_operation": (
        "app.services.portfolio.state.runtime",
        "execute_portfolio_state_store_operation",
    ),
    "get_portfolio_definition": (
        "app.services.portfolio.api",
        "get_portfolio_definition",
    ),
    "get_portfolio_error_catalog": (
        "app.services.portfolio.api",
        "get_portfolio_error_catalog",
    ),
    "get_portfolio_history": ("app.services.portfolio.api", "get_portfolio_history"),
    "get_portfolio_migrations": (
        "app.services.portfolio.migrations",
        "get_portfolio_migrations",
    ),
    "get_portfolio_status": ("app.services.portfolio.api", "get_portfolio_status"),
    "get_portfolio_value_field": (
        "app.services.portfolio.api",
        "get_portfolio_value_field",
    ),
    "ingest_event": ("app.services.portfolio.ledger", "ingest_event"),
    "is_balanced": ("app.services.portfolio.ledger", "is_balanced"),
    "is_portfolio_handle": ("app.services.portfolio.api", "is_portfolio_handle"),
    "is_portfolio_value": ("app.services.portfolio.api", "is_portfolio_value"),
    "measure_cross_account_correlation": (
        "app.services.portfolio.rebalancing.cross_account",
        "measure_cross_account_correlation",
    ),
    "parse_ledger_account": (
        "app.services.portfolio.ledger.contracts",
        "parse_ledger_account",
    ),
    "parse_ledger_entry": (
        "app.services.portfolio.ledger.contracts",
        "parse_ledger_entry",
    ),
    "parse_posting_batch": (
        "app.services.portfolio.ledger.contracts",
        "parse_posting_batch",
    ),
    "recompute_balances": ("app.services.portfolio.ledger", "recompute_balances"),
    "recompute_portfolio_measurement": (
        "app.services.portfolio.api",
        "recompute_portfolio_measurement",
    ),
    "reconcile_portfolio": (
        "app.services.portfolio.reconciliation",
        "reconcile_portfolio",
    ),
    "register_portfolio_definition": (
        "app.services.portfolio.api",
        "register_portfolio_definition",
    ),
    "rollback_portfolio": ("app.services.portfolio.api", "rollback_portfolio"),
    "run_portfolio_migrations": (
        "app.services.portfolio.migrations",
        "run_portfolio_migrations",
    ),
    "submit_portfolio_rebalance": (
        "app.services.portfolio.api",
        "submit_portfolio_rebalance",
    ),
    "to_portfolio_error_payload": (
        "app.services.portfolio.api",
        "to_portfolio_error_payload",
    ),
    "validate_construction_evidence": (
        "app.services.portfolio.evidence",
        "validate_construction_evidence",
    ),
    "validate_snapshot": ("app.services.portfolio.ledger", "validate_snapshot"),
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
    "activate_portfolio",
    "assess_common_mode_exposure",
    "assess_portfolio_drift",
    "build_ledger_account",
    "build_ledger_entry",
    "build_lifecycle_postings",
    "build_portfolio_risk_health",
    "build_portfolio_state_store",
    "build_posting_batch",
    "build_reversal_batch",
    "build_snapshot",
    "calculate_margin_view",
    "calculate_portfolio_valuation",
    "cash_balance",
    "construct_portfolio",
    "create_ledger_service",
    "create_portfolio_handle",
    "create_portfolio_value",
    "dump_portfolio_value",
    "execute_portfolio_handle_operation",
    "execute_portfolio_state_store_operation",
    "get_portfolio_definition",
    "get_portfolio_error_catalog",
    "get_portfolio_history",
    "get_portfolio_migrations",
    "get_portfolio_status",
    "get_portfolio_value_field",
    "ingest_event",
    "is_balanced",
    "is_portfolio_handle",
    "is_portfolio_value",
    "measure_cross_account_correlation",
    "parse_ledger_account",
    "parse_ledger_entry",
    "parse_posting_batch",
    "recompute_balances",
    "recompute_portfolio_measurement",
    "reconcile_portfolio",
    "register_portfolio_definition",
    "rollback_portfolio",
    "run_portfolio_migrations",
    "submit_portfolio_rebalance",
    "to_portfolio_error_payload",
    "validate_construction_evidence",
    "validate_snapshot",
)

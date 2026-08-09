"""Approved function-only public boundary for Portfolio."""

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
from app.services.portfolio.ledger.contracts import (
    build_ledger_account,
    build_ledger_entry,
    build_posting_batch,
    parse_ledger_account,
    parse_ledger_entry,
    parse_posting_batch,
)
from app.services.portfolio.migrations import (
    get_portfolio_migrations,
    run_portfolio_migrations,
)
from app.services.portfolio.rebalancing.cross_account import (
    assess_common_mode_exposure,
    measure_cross_account_correlation,
)
from app.services.portfolio.state.runtime import (
    build_portfolio_state_store,
    execute_portfolio_state_store_operation,
)

__all__ = (
    "activate_portfolio",
    "assess_common_mode_exposure",
    "assess_portfolio_drift",
    "build_ledger_account",
    "build_ledger_entry",
    "build_portfolio_state_store",
    "build_posting_batch",
    "construct_portfolio",
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
    "is_portfolio_handle",
    "is_portfolio_value",
    "measure_cross_account_correlation",
    "parse_ledger_account",
    "parse_ledger_entry",
    "parse_posting_batch",
    "recompute_portfolio_measurement",
    "register_portfolio_definition",
    "rollback_portfolio",
    "run_portfolio_migrations",
    "submit_portfolio_rebalance",
    "to_portfolio_error_payload",
    "validate_construction_evidence",
)

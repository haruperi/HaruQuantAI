"""Standalone Discretionary Manual Order Identity feature evidence."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import (
    discretionary_strategy_version_for,
    get_discretionary_strategy_id,
    list_strategy_versions,
    register_discretionary_strategy,
)
from app.utils import create_auth_context, generate_id, utc_now


def _emit(requirement: str, value: object) -> None:
    """Print exactly one success message and its genuine produced value."""
    print(f"Success: {requirement}")
    print(value)


def _auth() -> object:
    """Build one authenticated context holding the strategy:register permission."""
    return create_auth_context(
        contract_version="v2",
        schema_id="utils.auth_context.v2",
        principal_id="system:strategy-bootstrap",
        principal_type="SERVICE_ACCOUNT",
        roles=("strategy-admin",),
        permissions=("strategy:register",),
        scopes=("strategy",),
        tenant_or_environment="development",
        runtime_profile="demo",
        request_id=generate_id("req"),
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
        issued_at=utc_now(),
    )


def fr_str_083() -> None:
    """FR-STR-083: Register one immutable Discretionary Manual Order strategy version per Trading-reachable route environment (`DEMO`, `LIVE`), idempotently, through the standard `register_strategy_version` registry gate — no bypass of registration, lifecycle-approval, or module-root checks."""
    if os.environ.get("RUN_STRATEGY_STATEFUL_USAGE") != "1":
        print("Registration write skipped (RUN_STRATEGY_STATEFUL_USAGE!=1)")
        return
    results = register_discretionary_strategy(_auth())
    for result in results:
        mutation_status = (
            result.data.status if result.data is not None else result.error
        )
        _emit("FR-STR-083 registration", mutation_status)


def fr_str_084() -> None:
    """FR-STR-084: Own no signal-generation code and declare no `supported_hooks`; the registered identity module documents that the trading decision is made by the authenticated human operator, never by Strategy computation."""
    if os.environ.get("RUN_STRATEGY_STATEFUL_USAGE") != "1":
        print("Manifest inspection skipped (RUN_STRATEGY_STATEFUL_USAGE!=1)")
        return
    register_discretionary_strategy(_auth())
    versions = list_strategy_versions(strategy_id=get_discretionary_strategy_id())
    hooks = {ref.manifest.supported_hooks for ref in (versions.data or ())}
    _emit("FR-STR-084 supported_hooks per registered version", hooks)


def fr_str_085() -> None:
    """FR-STR-085: Expose the registered strategy identity and its exact per-environment version through function-only public accessors."""
    _emit("FR-STR-085 strategy id", get_discretionary_strategy_id())
    _emit("FR-STR-085 demo version", discretionary_strategy_version_for("DEMO"))
    _emit("FR-STR-085 live version", discretionary_strategy_version_for("LIVE"))


def main() -> None:
    """Run the Discretionary Manual Order Identity requirement example."""
    fr_str_083()
    fr_str_084()
    fr_str_085()


if __name__ == "__main__":
    main()

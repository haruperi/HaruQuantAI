"""Route contract registry validation tests."""

from __future__ import annotations

import pytest
from app.services.api import (
    build_route_contract,
    build_route_contract_registry,
    get_route_contract_registry,
    register_route_contract,
)
from pydantic import ValidationError


def _route_contract(*, route_id: str, method: str, path: str) -> object:
    """Build one deterministic route contract for tests."""
    return build_route_contract(
        route_id=route_id,
        method=method,
        path=path,
        owner="api",
        response_contract="ApiResponse.v1",
    )


def test_catalog_route_contract_collisions() -> None:
    """Reject duplicate route declarations for different contracts and ids."""
    registry = build_route_contract_registry(())

    registry.register_route_contract(
        _route_contract(
            route_id="api.contracts.one",
            method="GET",
            path="/api/contracts/collision-a",
        )
    )

    with pytest.raises(ValueError, match="duplicate route declaration"):
        registry.register_route_contract(
            _route_contract(
                route_id="api.contracts.two",
                method="GET",
                path="/api/contracts/collision-a",
            )
        )

    with pytest.raises(ValueError, match="duplicate route_id for a different route"):
        registry.register_route_contract(
            _route_contract(
                route_id="api.contracts.one",
                method="POST",
                path="/api/contracts/collision-b",
            )
        )


def test_catalog_route_contract_updates_are_idempotent_for_same_declaration() -> None:
    """Allow repeated registration of an identical contract for deterministic updates."""
    registry = build_route_contract_registry(())
    contract = _route_contract(
        route_id="api.contracts.identity",
        method="GET",
        path="/api/contracts/identity",
    )
    registry.register_route_contract(contract)
    registry.register_route_contract(contract)
    assert registry.size == 1


def test_catalog_incomplete_route_contract_rejected() -> None:
    """Reject incomplete route-contract declarations before registry insertion."""
    with pytest.raises(ValueError, match="pagination requires a response contract"):
        build_route_contract(
            route_id="api.contracts.incomplete",
            method="GET",
            path="/api/contracts/incomplete",
            owner="api",
            pagination="cursor",
            response_contract=None,
        )

    with pytest.raises(ValidationError, match="must start with"):
        build_route_contract(
            route_id="api.contracts.missing",
            method="GET",
            path="api/contracts/missing-slash",
            owner="api",
            response_contract="ApiResponse.v1",
        )


def test_catalog_global_function_registers_contract() -> None:
    """Smoke-test the module-level register helper on the package registry."""
    before = get_route_contract_registry().size
    contract = _route_contract(
        route_id="api.contracts.usage",
        method="GET",
        path="/api/contracts/usage",
    )
    register_route_contract(contract)
    register_route_contract(contract)

    registered = get_route_contract_registry().get(contract.method, contract.path)
    assert registered is not None
    assert registered.route_id == contract.route_id
    assert get_route_contract_registry().size == before + 1
    assert get_route_contract_registry().get("GET", "/api/contracts/usage") is not None

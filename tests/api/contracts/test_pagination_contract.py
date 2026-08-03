"""Pagination limits and determinism exposed by the canonical OpenAPI contract."""

from app.services.api import create_api_app
from app.services.api.contracts.catalog import create_canonical_route_contract_registry

_API_DEFAULT_PAGE_SIZE = 50
_API_MAX_PAGE_SIZE = 200


def test_symbol_list_has_bounded_page_size() -> None:
    """The list route publishes the default and maximum page size."""
    operation = create_api_app().openapi()["paths"]["/api/v1/data/symbols"]["get"]
    parameters = {item["name"]: item for item in operation["parameters"]}
    limit = parameters["limit"]["schema"]
    assert limit["default"] == _API_DEFAULT_PAGE_SIZE
    assert limit["minimum"] == 1
    assert limit["maximum"] == _API_MAX_PAGE_SIZE


def test_paginated_routes_declare_cursor_and_limit() -> None:
    """Every paginated route exposes a cursor and a bounded limit parameter."""
    registry = create_canonical_route_contract_registry()
    for contract in registry.all():
        if not getattr(contract, "paginated", False):
            continue
        app = create_api_app()
        operation = app.openapi()["paths"][contract.path][contract.method.lower()]
        param_names = {item["name"] for item in operation.get("parameters", [])}
        assert "limit" in param_names, (
            f"{contract.route_id} must declare a limit parameter"
        )
        assert "cursor" in param_names, (
            f"{contract.route_id} must declare a cursor parameter"
        )


def test_pagination_limits_are_deterministic_across_builds() -> None:
    """The default and max page size are identical across two app builds."""
    op1 = create_api_app().openapi()["paths"]["/api/v1/data/symbols"]["get"]
    op2 = create_api_app().openapi()["paths"]["/api/v1/data/symbols"]["get"]
    limit1 = {p["name"]: p for p in op1["parameters"]}["limit"]["schema"]
    limit2 = {p["name"]: p for p in op2["parameters"]}["limit"]["schema"]
    assert limit1 == limit2

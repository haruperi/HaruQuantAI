"""Pagination limits exposed by the canonical OpenAPI contract."""

from app.services.api import create_api_app


def test_symbol_list_has_bounded_page_size() -> None:
    """The list route publishes the default and maximum page size."""
    operation = create_api_app().openapi()["paths"]["/api/v1/data/symbols"]["get"]
    parameters = {item["name"]: item for item in operation["parameters"]}
    limit = parameters["limit"]["schema"]
    assert limit["default"] == 50
    assert limit["minimum"] == 1
    assert limit["maximum"] == 200

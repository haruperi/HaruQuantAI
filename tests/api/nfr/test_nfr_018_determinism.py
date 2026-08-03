"""NFR-API-018: Contract registration, route ordering, and idempotency determinism.

Verifies that:
- Building the canonical route registry twice produces the same ordered output.
- The OpenAPI path inventory is deterministic across two app builds.
- The route contract count is stable.
"""

from app.services.api import create_api_app
from app.services.api.contracts.catalog import create_canonical_route_contract_registry


class TestNfrApi018Determinism:
    """NFR-API-018: determinism verification."""

    @staticmethod
    def test_route_registry_order_is_deterministic() -> None:
        """Two fresh registries yield the same ordered sequence of route ids."""
        registry_a = create_canonical_route_contract_registry()
        registry_b = create_canonical_route_contract_registry()
        ids_a = [c.route_id for c in registry_a.all()]
        ids_b = [c.route_id for c in registry_b.all()]
        assert ids_a == ids_b

    @staticmethod
    def test_route_registry_size_is_stable() -> None:
        """The registry size is the same across builds."""
        size_a = create_canonical_route_contract_registry().size
        size_b = create_canonical_route_contract_registry().size
        assert size_a == size_b
        assert size_a > 0

    @staticmethod
    def test_openapi_paths_are_deterministic() -> None:
        """Two app builds produce the same set of OpenAPI paths."""
        paths_a = set(create_api_app().openapi()["paths"].keys())
        paths_b = set(create_api_app().openapi()["paths"].keys())
        assert paths_a == paths_b

    @staticmethod
    def test_openapi_operation_inventory_is_deterministic() -> None:
        """The (method, path) inventory is identical across builds."""
        spec_a = create_api_app().openapi()
        spec_b = create_api_app().openapi()
        ops_a: set[str] = set()
        ops_b: set[str] = set()
        for path, methods in spec_a["paths"].items():
            for method in methods:
                if method in ("get", "post", "put", "delete", "patch"):
                    ops_a.add(f"{method.upper()} {path}")
        for path, methods in spec_b["paths"].items():
            for method in methods:
                if method in ("get", "post", "put", "delete", "patch"):
                    ops_b.add(f"{method.upper()} {path}")
        assert ops_a == ops_b

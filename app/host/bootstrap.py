"""Application composition root for approved host owners."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.host.catalog import CatalogRoot, _catalog_feature
from app.host.execution import _execution_feature
from app.host.gateway import GatewayConfig, _gateway_feature
from app.host.telemetry import (
    DEFAULT_DIAGNOSTIC_CAPACITY,
    DEFAULT_MAX_SUBSCRIBERS,
    _telemetry_feature,
)
from app.kernel.bootstrapper import Runtime
from app.kernel.feature import Feature


def approved_catalog_roots(repo_root: Path | None = None) -> tuple[CatalogRoot, ...]:
    """Return explicit CatalogRoot configurations for approved quantitative families."""
    base = (repo_root or Path(__file__).resolve().parent.parent) / "plugins"
    return (
        CatalogRoot(
            logical_family="indicators",
            path=base / "indicators",
            accepted_kinds=("indicator",),
        ),
        CatalogRoot(
            logical_family="comparisons",
            path=base / "comparisons",
            accepted_kinds=("comparison",),
        ),
        CatalogRoot(
            logical_family="exporters",
            path=base / "exporters",
            accepted_kinds=("exporter",),
        ),
        CatalogRoot(
            logical_family="workspaces",
            path=base / "workspaces",
            accepted_kinds=("workspace",),
        ),
    )


def create_runtime(
    *,
    telemetry_max_subscribers: int = DEFAULT_MAX_SUBSCRIBERS,
    diagnostic_capacity: int = DEFAULT_DIAGNOSTIC_CAPACITY,
    catalog_roots: tuple[CatalogRoot, ...] = (),
    gateway_config: GatewayConfig | None = None,
    gateway_auto_start: bool = False,
) -> Runtime:
    """Construct a fresh, inactive runtime for the currently approved host."""
    telemetry = _telemetry_feature(
        max_subscribers=telemetry_max_subscribers,
        diagnostic_capacity=diagnostic_capacity,
    )
    catalog = _catalog_feature(roots=catalog_roots)
    execution = _execution_feature()

    def telemetry_factory() -> Feature:
        return telemetry

    def catalog_factory() -> Feature:
        return catalog

    def execution_factory() -> Feature:
        return execution

    feature_factories: list[Callable[[], Feature]] = [
        telemetry_factory,
        catalog_factory,
        execution_factory,
    ]

    if gateway_config is not None:
        gateway = _gateway_feature(gateway_config, auto_start=gateway_auto_start)

        def gateway_factory() -> Feature:
            return gateway

        feature_factories.append(gateway_factory)

    return Runtime(
        tuple(feature_factories),
        diagnostic_sink=telemetry.diagnose,
    )


__all__ = ("approved_catalog_roots", "create_runtime")

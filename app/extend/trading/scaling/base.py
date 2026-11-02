"""Base contracts and registry for StrategyQuant position scaling methods.

Description:
    Provides abstract base class ScalingMethod and registry ScalingMethodsList
    for scaling order execution volume conforming to StrategyQuant
    SQ.Trading.Scaling specifications.

Purpose:
    FEAT-TRADING-SCALING: Define standard scaling contract and registry.

Key Capabilities:
    - FR-TRADING-SCALING-BASE: Base contract for position scaling models.
    - FR-TRADING-SCALING-REGISTRY: Singleton registry for custom scaling methods.
    - FR-TRADING-SCALING-XML: Serialization and deserialization of scaling configs.

Python API Usage:
    from app.extend.trading.scaling.base import ScalingMethod, ScalingMethodsList
    registry = ScalingMethodsList.get()
    method = registry.create("NoScaling")

CLI Usage:
    uv run pytest tests/extend/test_trading_catalog.py --no-cov
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


class ScalingMethod(ABC):
    """Abstract base class for position scaling methods."""

    name: str = "ScalingMethod"
    category: str = "Trading.Scaling"

    def setName(self, name: str) -> None:  # noqa: N802
        """Set descriptive scaling method name."""
        self.name = name

    @abstractmethod
    def scale_size(self, requested_size: float) -> float:
        """Calculate scaled order volume given the requested size.

        Args:
            requested_size: Unscaled initial order size.

        Returns:
            Scaled final order volume.
        """

    def scale_orders(self, orders: list[Any]) -> list[Any]:
        """Apply scaling logic across a collection of orders.

        Args:
            orders: Collection of order objects.

        Returns:
            Collection of orders with adjusted volumes.
        """
        logger.debug("FR-TRADING-SCALING-BASE: scale_orders on %d orders", len(orders))
        return orders

    def getXML(self) -> dict[str, Any]:  # noqa: N802
        """Serialize scaling configuration into XML dictionary.

        Returns:
            Dictionary matching StrategyQuant XML serialization structure.
        """
        params: dict[str, Any] = {
            k: v
            for k, v in self.__dict__.items()
            if not k.startswith("_") and k not in {"name", "category"}
        }
        xml_dict = {
            "tag": "Scaling",
            "children": [
                {
                    "tag": "Method",
                    "attributes": {"type": self.__class__.__name__},
                    "parameters": params,
                }
            ],
        }
        logger.debug("FR-TRADING-SCALING-XML: getXML for %s", self.__class__.__name__)
        return xml_dict

    def setFromXML(self, element: dict[str, Any]) -> None:  # noqa: N802
        """Deserialize scaling configuration from XML dictionary.

        Args:
            element: Dictionary containing Method tag and parameters.

        Raises:
            ValueError: If Method element is missing.
        """
        method_elem: dict[str, Any] | None = None
        for child in element.get("children", []):
            if child.get("tag") == "Method":
                method_elem = child
                break
        if method_elem is None:
            raise ValueError(
                "Cannot set up Scaling method. Method xml element not found"
            )
        self.setName(
            method_elem.get("attributes", {}).get("type", self.__class__.__name__)
        )
        params = method_elem.get("parameters", {})
        for k, v in params.items():
            if hasattr(self, k):
                setattr(self, k, v)
        logger.debug(
            "FR-TRADING-SCALING-XML: setFromXML for %s", self.__class__.__name__
        )


class ScalingMethodsList:
    """Registry coordinating all StrategyQuant scaling method snippets."""

    _instance: ClassVar[ScalingMethodsList | None] = None
    _classes: dict[str, type[ScalingMethod]]

    def __init__(self) -> None:
        self._classes = {}
        logger.info("FR-TRADING-SCALING-REGISTRY: initialized ScalingMethodsList")

    @classmethod
    def get(cls) -> ScalingMethodsList:
        """Obtain singleton instance of ScalingMethodsList."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def register(cls, name: str, method_cls: type[ScalingMethod]) -> None:
        """Register a scaling method class under the given name."""
        instance = cls.get()
        instance._classes[name] = method_cls  # noqa: SLF001
        logger.debug(
            "FR-TRADING-SCALING-REGISTRY: registered method '%s' -> %s",
            name,
            method_cls.__name__,
        )

    @classmethod
    def create(
        cls,
        name: str,
        *args: Any,
        **kwargs: Any,
    ) -> ScalingMethod:
        """Create a new instance of a registered scaling method.

        Args:
            name: Class name or registered snippet identifier.
            *args: Positional constructor arguments.
            **kwargs: Keyword constructor arguments.

        Returns:
            Instantiated ScalingMethod.

        Raises:
            KeyError: If method name is not registered.
        """
        instance = cls.get()
        method_cls = instance._classes.get(name)  # noqa: SLF001
        if method_cls is None:
            raise KeyError(f"Nonexisting custom class: {name}")
        logger.debug(
            "FR-TRADING-SCALING-REGISTRY: creating instance of %s",
            name,
        )
        return method_cls(*args, **kwargs)

    @classmethod
    def list_available(cls) -> list[str]:
        """Return names of all registered scaling classes."""
        return sorted(cls.get()._classes.keys())  # noqa: SLF001

    @classmethod
    def get_available_classes(cls) -> list[type[ScalingMethod]]:
        """Return list of all registered ScalingMethod classes."""
        return list(cls.get()._classes.values())  # noqa: SLF001


__all__ = [
    "ScalingMethod",
    "ScalingMethodsList",
]

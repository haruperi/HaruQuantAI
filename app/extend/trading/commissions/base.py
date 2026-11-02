"""Base contracts and registry for StrategyQuant commission methods.

Description:
    Provides abstract base class CommissionsMethod, registry CommissionsMethodsList,
    and helper inspection functions for calculating trading commissions on order entry
    and exit conforming to StrategyQuant SQ.Trading.Commissions specifications.

Purpose:
    FEAT-TRADING-COMMISSIONS: Define standard commissions contract and registry.

Key Capabilities:
    - FR-TRADING-COMMISSIONS-BASE: Base contract and helpers for order commission.
    - FR-TRADING-COMMISSIONS-REGISTRY: Singleton registry for commission methods.
    - FR-TRADING-COMMISSIONS-XML: Serialization and deserialization of configs.

Python API Usage:
    from app.extend.trading.commissions.base import (
        CommissionsMethod,
        CommissionsMethodsList,
    )
    registry = CommissionsMethodsList.get()
    method = registry.create("PerTrade", commission=5.0)

CLI Usage:
    uv run pytest tests/extend/test_trading_catalog.py --no-cov
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


def get_order_size(order: Any) -> float:
    """Extract order size in lots/shares from an order object or dictionary.

    Args:
        order: Order instance, dictionary, or numeric fallback.

    Returns:
        Order size as a non-negative float.
    """
    if hasattr(order, "getSize") and callable(order.getSize):
        return max(float(order.getSize()), 0.0)
    if hasattr(order, "size"):
        return max(float(order.size), 0.0)
    if hasattr(order, "_size"):
        return max(float(order._size), 0.0)  # noqa: SLF001
    if isinstance(order, dict):
        return max(float(order.get("size", 1.0)), 0.0)
    if isinstance(order, (int, float)):
        return max(float(order), 0.0)
    return 1.0


def get_order_open_price(order: Any) -> float:
    """Extract order open/execution price from an order object or dictionary.

    Args:
        order: Order instance, dictionary, or numeric fallback.

    Returns:
        Order open price as a float.
    """
    if hasattr(order, "getOpenPrice") and callable(order.getOpenPrice):
        return float(order.getOpenPrice())
    if hasattr(order, "open_price"):
        return float(order.open_price)
    if hasattr(order, "_open_price"):
        return float(order._open_price)  # noqa: SLF001
    if isinstance(order, dict):
        return float(order.get("open_price", 0.0))
    return 0.0


def get_order_close_price(order: Any) -> float:
    """Extract order close price from an order object or dictionary.

    Args:
        order: Order instance, dictionary, or numeric fallback.

    Returns:
        Order close price as a float.
    """
    if hasattr(order, "getClosePrice") and callable(order.getClosePrice):
        return float(order.getClosePrice())
    if hasattr(order, "close_price"):
        return float(order.close_price)
    if hasattr(order, "_close_price"):
        return float(order._close_price)  # noqa: SLF001
    if isinstance(order, dict):
        return float(order.get("close_price", 0.0))
    return 0.0


def is_pending_order(order: Any) -> bool:
    """Determine whether an order is a pending entry order.

    Args:
        order: Order instance or dictionary.

    Returns:
        True if order is pending entry, False otherwise.
    """
    if hasattr(order, "isPendingOrder") and callable(order.isPendingOrder):
        return bool(order.isPendingOrder())
    if hasattr(order, "is_pending"):
        return bool(order.is_pending)
    if hasattr(order, "is_pending_order"):
        return bool(order.is_pending_order)
    if hasattr(order, "_is_pending"):
        return bool(order._is_pending)  # noqa: SLF001
    if isinstance(order, dict):
        return bool(order.get("is_pending", False))
    return False


class CommissionsMethod(ABC):
    """Abstract base class for trade commissions calculation."""

    name: str = "CommissionsMethod"
    category: str = "Trading.Commissions"

    def setName(self, name: str) -> None:  # noqa: N802
        """Set descriptive method name."""
        self.name = name

    @abstractmethod
    def computeCommissionsOnOpen(  # noqa: N802
        self,
        order: Any,
        tickSize: float = 0.0001,  # noqa: N803
        pointValue: float = 1.0,  # noqa: N803
    ) -> float:
        """Compute commission charged when an order opens.

        Args:
            order: ILiveOrder or compatible order representation.
            tickSize: Minimum price increment for instrument.
            pointValue: Currency value of 1 full point movement.

        Returns:
            Calculated commission in account currency.
        """

    @abstractmethod
    def computeCommissionsOnClose(  # noqa: N802
        self,
        order: Any,
        tickSize: float = 0.0001,  # noqa: N803
        pointValue: float = 1.0,  # noqa: N803
    ) -> float:
        """Compute commission charged when an order closes.

        Args:
            order: ILiveOrder or compatible order representation.
            tickSize: Minimum price increment for instrument.
            pointValue: Currency value of 1 full point movement.

        Returns:
            Calculated commission in account currency.
        """

    def compute_commission(
        self,
        *,
        size: float = 1.0,
        open_price: float = 1.0,
        close_price: float | None = None,
        point_value: float = 1.0,
    ) -> float:
        """Legacy keyword-argument adapter for total round-turn commission.

        Args:
            size: Position volume in lots/contracts/shares.
            open_price: Entry execution price.
            close_price: Optional exit execution price.
            point_value: Currency value of one point.

        Returns:
            Total round-turn trade commission.
        """
        synthetic_order = {
            "size": size,
            "open_price": open_price,
            "close_price": close_price if close_price is not None else open_price,
            "is_pending": False,
        }
        fee_open = self.computeCommissionsOnOpen(
            synthetic_order, pointValue=point_value
        )
        fee_close = self.computeCommissionsOnClose(
            synthetic_order, pointValue=point_value
        )
        total = fee_open + fee_close
        logger.debug(
            "FR-TRADING-COMMISSIONS-BASE: compute_commission open=%f close=%f total=%f",
            fee_open,
            fee_close,
            total,
        )
        return round(total, 6)

    def getXML(self) -> dict[str, Any]:  # noqa: N802
        """Serialize configuration parameters into XML element dictionary.

        Returns:
            Dictionary matching StrategyQuant XML serialization structure.
        """
        params: dict[str, Any] = {
            k: v
            for k, v in self.__dict__.items()
            if not k.startswith("_") and k not in {"name", "category"}
        }
        xml_dict = {
            "tag": "Commissions",
            "children": [
                {
                    "tag": "Method",
                    "attributes": {"type": self.__class__.__name__},
                    "parameters": params,
                }
            ],
        }
        logger.debug(
            "FR-TRADING-COMMISSIONS-XML: getXML for %s", self.__class__.__name__
        )
        return xml_dict

    def setFromXML(self, element: dict[str, Any]) -> None:  # noqa: N802
        """Deserialize configuration parameters from XML element dictionary.

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
                "Cannot set up Commissions method. Method xml element not found"
            )
        self.setName(
            method_elem.get("attributes", {}).get("type", self.__class__.__name__)
        )
        params = method_elem.get("parameters", {})
        for k, v in params.items():
            if hasattr(self, k):
                setattr(self, k, v)
        logger.debug(
            "FR-TRADING-COMMISSIONS-XML: setFromXML for %s", self.__class__.__name__
        )


class CommissionsMethodsList:
    """Registry coordinating all StrategyQuant commission method snippets."""

    _instance: ClassVar[CommissionsMethodsList | None] = None
    _classes: dict[str, type[CommissionsMethod]]

    def __init__(self) -> None:
        self._classes = {}
        logger.info(
            "FR-TRADING-COMMISSIONS-REGISTRY: initialized CommissionsMethodsList"
        )

    @classmethod
    def get(cls) -> CommissionsMethodsList:
        """Obtain singleton instance of CommissionsMethodsList."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def register(cls, name: str, method_cls: type[CommissionsMethod]) -> None:
        """Register a commission method class under the given name."""
        instance = cls.get()
        instance._classes[name] = method_cls  # noqa: SLF001
        logger.debug(
            "FR-TRADING-COMMISSIONS-REGISTRY: registered method '%s' -> %s",
            name,
            method_cls.__name__,
        )

    @classmethod
    def create(
        cls,
        name: str,
        *args: Any,
        **kwargs: Any,
    ) -> CommissionsMethod:
        """Create a new instance of a registered commission method.

        Args:
            name: Class name or registered snippet identifier.
            *args: Positional constructor arguments.
            **kwargs: Keyword constructor arguments.

        Returns:
            Instantiated CommissionsMethod.

        Raises:
            KeyError: If method name is not registered.
        """
        instance = cls.get()
        method_cls = instance._classes.get(name)  # noqa: SLF001
        if method_cls is None:
            raise KeyError(f"Nonexisting custom class: {name}")
        logger.debug(
            "FR-TRADING-COMMISSIONS-REGISTRY: creating instance of %s",
            name,
        )
        return method_cls(*args, **kwargs)

    @classmethod
    def list_available(cls) -> list[str]:
        """Return names of all registered commission classes."""
        return sorted(cls.get()._classes.keys())  # noqa: SLF001

    @classmethod
    def get_available_classes(cls) -> list[type[CommissionsMethod]]:
        """Return list of all registered CommissionsMethod classes."""
        return list(cls.get()._classes.values())  # noqa: SLF001


__all__ = [
    "CommissionsMethod",
    "CommissionsMethodsList",
    "get_order_close_price",
    "get_order_open_price",
    "get_order_size",
    "is_pending_order",
]

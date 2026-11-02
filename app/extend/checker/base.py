"""Base checker class and XML element utilities for strategy AST verification.

Description:
    Provides the abstract base class for StrategyQuant-compatible strategy
    checkers along with shared XML Element navigation and serialization
    utilities used to validate strategy building blocks.

Purpose:
    FEAT-RETESTER-CHECKER: Strategy parameter and property verification.

Key Capabilities:
    - FR-checker-base: Abstract verification interface and AST element utilities.

Python API Usage:
    from app.extend.checker.base import Checker, parse_element
    elem = parse_element("<Item key='RSI' />")

CLI Usage:
    python -c "from app.extend.checker.base import Checker; print(Checker)"
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Any

from app.core.host.logging import get_logger

logger = get_logger(__name__)


def parse_element(element: Any) -> ET.Element | None:
    """Parse input into an xml.etree.ElementTree.Element if possible.

    Args:
        element: An existing Element, an XML string, or bytes.

    Returns:
        ET.Element if parsing succeeds, otherwise None.
    """
    if isinstance(element, ET.Element):
        return element
    if isinstance(element, (str, bytes)):
        try:
            return ET.fromstring(element)  # noqa: S314
        except ET.ParseError:
            logger.debug("FR-checker-base: failed to parse XML string")
            return None
    return None


def element_to_string(element: ET.Element) -> str:
    """Serialize an ElementTree Element to a raw XML string.

    Args:
        element: XML element to serialize.

    Returns:
        Raw XML string representation.
    """
    return ET.tostring(element, encoding="unicode")


def find_all_items(element: ET.Element) -> list[ET.Element]:
    """Find all descendant Item elements within an element.

    Args:
        element: Root element to search.

    Returns:
        List of all descendant elements with tag 'Item'.
    """
    return element.findall(".//Item")


class Checker(ABC):
    """Abstract base class for strategy AST/block verification checkers."""

    @classmethod
    @abstractmethod
    def check(cls, element: Any, *args: Any, **kwargs: Any) -> bool:
        """Evaluate strategy element against checker validation rules.

        Args:
            element: Strategy XML element (Element, str, or dict) or first operand.
            *args: Variable positional arguments for checker implementations.
            **kwargs: Variable keyword arguments for checker implementations.

        Returns:
            True if element passes checker validation, False otherwise.
        """

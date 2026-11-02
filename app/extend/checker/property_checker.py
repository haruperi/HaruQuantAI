"""Property checker verifying IsRising/IsFalling blocks and property mappings.

Description:
    Verifies that IsRising and IsFalling strategy property AST blocks contain
    valid indicator sub-blocks with a Shift parameter and no bar-time units
    (Hour, Minute, DayOfWeek). Also supports dictionary-based strategy
    property verification for backwards compatibility.

Purpose:
    FEAT-RETESTER-CHECKER: Strategy parameter and property verification.

Key Capabilities:
    - FR-checker-property: Verify that strategy properties match required constraints.

Python API Usage:
    from app.extend.checker.property_checker import PropertyChecker
    valid = PropertyChecker.check({"Symbol": "EURUSD"}, {"Symbol": "EURUSD"})

CLI Usage:
    python -m app.cli checker property --strategy '{"Symbol": "EURUSD"}'
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Mapping
from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.checker.base import Checker, element_to_string, parse_element

logger = get_logger(__name__)


class PropertyChecker(Checker):
    """Verifies strategy property AST blocks and property dictionary requirements."""

    @classmethod
    @override
    def check(cls, element: Any, *args: Any, **kwargs: Any) -> bool:
        """Polymorphic check supporting both AST elements and property dicts.

        Args:
            element: XML Element, XML string, or properties Mapping.
            *args: Additional positional arguments (e.g. required mapping).
            **kwargs: Additional keyword arguments.

        Returns:
            True if valid, False otherwise.
        """
        is_dict_check = isinstance(element, Mapping) and (args or "required" in kwargs)
        if is_dict_check:
            required: Mapping[str, Any] = args[0] if args else kwargs["required"]
            return cls.check_dict(element, required)

        return cls.check_block(element)

    @classmethod
    def check_dict(
        cls,
        strategy_properties: Mapping[str, Any],
        required: Mapping[str, Any],
    ) -> bool:
        """Check that all required properties exist and match strategy properties.

        Args:
            strategy_properties: Existing strategy properties.
            required: Required property key/value map.

        Returns:
            True if all required items match, otherwise False.
        """
        for key, expected_value in required.items():
            if key not in strategy_properties:
                logger.info("FR-checker-property: missing required property %s", key)
                return False
            actual_value = strategy_properties[key]
            if actual_value != expected_value:
                logger.info(
                    "FR-checker-property: mismatch for %s: expected %r, got %r",
                    key,
                    expected_value,
                    actual_value,
                )
                return False

        logger.debug(
            "FR-checker-property: all %d required properties matched", len(required)
        )
        return True

    @classmethod
    def check_block(cls, el_block: Any) -> bool:
        """Validate an IsRising or IsFalling AST block Element or XML string.

        Args:
            el_block: XML Element or XML string.

        Returns:
            True if block passes property validation, False otherwise.
        """
        elem = parse_element(el_block)
        if elem is None:
            logger.info("FR-checker-property: element is None or unparseable")
            return False

        return_type = elem.attrib.get("returnType")
        if return_type is not None and return_type != "boolean":
            # it is not a property, skip it
            return True

        key = elem.attrib.get("key", "")
        if key.lower() not in ("isrising", "isfalling"):
            # it is not IsRising/Falling property, skip
            return True

        el_indicator = cls.get_parameter(elem, "Indicator")
        if el_indicator is None:
            # it doesn't have Indicator parameters, skip it
            return True

        return cls._verify_indicator_content(el_indicator)

    @classmethod
    def _verify_indicator_content(cls, el_indicator: ET.Element) -> bool:
        """Verify presence of Shift and absence of bar-time blocks."""
        xml1 = element_to_string(el_indicator)

        if "#Shift#" not in xml1:
            logger.info("FR-checker-property: block lacks Shift parameter")
            return False

        time_units = ("Hour", "Minute", "DayOfWeek")
        if any(unit in xml1 for unit in time_units):
            logger.info("FR-checker-property: bar-time block in IsRising/Falling")
            return False

        return True

    @classmethod
    def get_parameter(
        cls, el_block: ET.Element, parameter_name: str
    ) -> ET.Element | None:
        """Get parameter Element matching '#<parameter_name>#'.

        Args:
            el_block: Parent container element.
            parameter_name: Base parameter name without hash marks.

        Returns:
            Matching parameter Element or None.
        """
        fixed_key = cls.fix_key(parameter_name)
        for el_param in list(el_block):
            key = el_param.attrib.get("key")
            if key is not None and key == fixed_key:
                return el_param
        return None

    @staticmethod
    def fix_key(parameter_name: str) -> str:
        """Enclose parameter name in hash marks: '#<name>#'.

        Args:
            parameter_name: Base parameter name.

        Returns:
            Formatted key with surrounding hash marks.
        """
        return f"#{parameter_name}#"

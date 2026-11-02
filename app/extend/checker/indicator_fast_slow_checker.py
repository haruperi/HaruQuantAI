"""Fast/Slow and Min/Max indicator parameter validation checker.

Description:
    Verifies that fast indicator periods are strictly less than slow periods
    and minimum periods are strictly less than maximum periods within strategy
    AST blocks and parameter configurations.

Purpose:
    FEAT-RETESTER-CHECKER: Strategy parameter and property verification.

Key Capabilities:
    - FR-checker-fast-slow: Verify that fast indicator periods are less than slow.

Python API Usage:
    from app.extend.checker.indicator_fast_slow_checker import (
        IndicatorFastSlowChecker,
    )
    valid = IndicatorFastSlowChecker.check({"FastPeriod": 12, "SlowPeriod": 26})

CLI Usage:
    python -m app.cli checker fast-slow --fast 12 --slow 26
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Mapping, Sequence
from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.checker.base import Checker, find_all_items, parse_element

logger = get_logger(__name__)


class IndicatorFastSlowChecker(Checker):
    """Verifies that fast periods are strictly less than slow periods."""

    @classmethod
    @override
    def check(cls, element: Any, *args: Any, **kwargs: Any) -> bool:
        """Polymorphic check method supporting both AST elements and parameter dicts.

        Args:
            element: XML Element, XML string, or parameter Mapping.
            *args: Additional positional arguments (e.g. pairs for dict check).
            **kwargs: Additional keyword arguments.

        Returns:
            True if all fast/slow constraints are satisfied, False otherwise.
        """
        if isinstance(element, Mapping):
            default_pairs = (("FastPeriod", "SlowPeriod"),)
            pairs: Sequence[tuple[str, str]] = (
                args[0] if args else kwargs.get("pairs", default_pairs)
            )
            return cls.check_dict(element, pairs)

        return cls.check_block(element)

    @classmethod
    def check_dict(
        cls,
        parameters: Mapping[str, int | float],
        pairs: Sequence[tuple[str, str]] = (("FastPeriod", "SlowPeriod"),),
    ) -> bool:
        """Check all present (fast_key, slow_key) pairs satisfy fast < slow.

        Args:
            parameters: Strategy parameter dictionary.
            pairs: Sequence of parameter key pairs to check.

        Returns:
            True if for every present pair, parameters[fast] < parameters[slow].
        """
        for fast_key, slow_key in pairs:
            if fast_key in parameters and slow_key in parameters:
                fast_val = float(parameters[fast_key])
                slow_val = float(parameters[slow_key])
                if fast_val >= slow_val:
                    logger.info(
                        "FR-checker-fast-slow: failed %s (%.1f) >= %s (%.1f)",
                        fast_key,
                        fast_val,
                        slow_key,
                        slow_val,
                    )
                    return False

        logger.debug("FR-checker-fast-slow: all fast/slow period constraints satisfied")
        return True

    @classmethod
    def check_block(cls, el_block: Any) -> bool:
        """Validate AST block Element or XML string for Fast/Slow and Min/Max hierarchy.

        Args:
            el_block: XML Element or XML string.

        Returns:
            True if all components satisfy period ordering, False otherwise.
        """
        elem = parse_element(el_block)
        if elem is None:
            logger.info("FR-checker-fast-slow: element is None or unparseable")
            return False

        if not cls._check_fast_slow(elem):
            return False

        list_items = find_all_items(elem)
        return all(cls._check_fast_slow(item) for item in list_items)

    @classmethod
    def _check_fast_slow(cls, el_item: ET.Element) -> bool:
        """Inspect Param children of an Item for Fast/Slow and Min/Max constraints."""
        children = [c for c in list(el_item) if c.tag == "Param"]

        # check Fast, Slow
        el_fast = cls._find_in_params(children, "#Fast")
        if el_fast is not None:
            el_slow = cls._find_in_params(children, "#Slow")
            if el_slow is not None and not cls._check_period_pair(el_fast, el_slow):
                return False

        # check Min, Max
        el_min = cls._find_in_params(children, "#MinPeriod")
        if el_min is not None:
            el_max = cls._find_in_params(children, "#MaxPeriod")
            if el_max is not None and not cls._check_period_pair(el_min, el_max):
                return False

        return True

    @staticmethod
    def _check_period_pair(el_first: ET.Element, el_second: ET.Element) -> bool:
        """Ensure el_first int period is strictly less than el_second int period."""
        first_str = (el_first.text or "").strip()
        second_str = (el_second.text or "").strip()

        try:
            first_period = int(first_str)
            second_period = int(second_str)
            if first_period >= second_period:
                logger.info(
                    "FR-checker-fast-slow: %d >= %d constraint violation",
                    first_period,
                    second_period,
                )
                return False
        except ValueError:
            return True

        return True

    @staticmethod
    def _find_in_params(
        children: list[ET.Element], parameter_name: str
    ) -> ET.Element | None:
        """Find Param element matching prefix and int type."""
        for el_param in children:
            key = el_param.attrib.get("key")
            if key is not None and key.startswith(parameter_name):
                param_type = el_param.attrib.get("type")
                if param_type == "int":
                    return el_param
        return None

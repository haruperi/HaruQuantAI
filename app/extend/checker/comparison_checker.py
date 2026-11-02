"""Comparison checker for strategy AST block comparisons and scalar values.

Description:
    Validates AST comparison blocks for valid operand types, ensuring left and
    right sides are not identical, indicators are compared only to compatible
    indicators or numbers, bar time blocks follow orientation and value range
    rules, and time ranges follow HHMM formatting. Also supports scalar
    comparison evaluation for backwards compatibility.

Purpose:
    FEAT-RETESTER-CHECKER: Strategy parameter and property verification.

Key Capabilities:
    - FR-checker-comparison: Compare scalar values and AST comparison blocks.

Python API Usage:
    from app.extend.checker.comparison_checker import ComparisonChecker
    valid = ComparisonChecker.check(10.0, "<", 20.0)

CLI Usage:
    python -m app.cli checker comparison --left 10 --op "<" --right 20
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any, Literal, override

from app.core.host.logging import get_logger
from app.extend.checker.base import Checker, element_to_string, parse_element

logger = get_logger(__name__)

OperatorType = Literal["<", "<=", ">", ">=", "==", "!="]
FLOAT_TOLERANCE = 1e-9
MAX_HOUR = 23
MAX_MINUTE = 59
MAX_DAY_OF_WEEK = 6


class ComparisonChecker(Checker):
    """Evaluates strategy comparison AST elements and scalar comparison expressions."""

    @classmethod
    @override
    def check(cls, element: Any, *args: Any, **kwargs: Any) -> bool:
        """Polymorphic check method supporting both AST elements and scalar comparisons.

        If element is a number and operator is provided in args or kwargs,
        evaluates scalar comparison. Otherwise treats element as an AST block.

        Args:
            element: XML Element/string or left float value.
            *args: Additional positional arguments (e.g. operator, right_value).
            **kwargs: Additional keyword arguments.

        Returns:
            Boolean evaluation result.
        """
        valid_ops = ("<", "<=", ">", ">=", "==", "!=")
        is_scalar = isinstance(element, (int, float)) or (
            args and isinstance(args[0], str) and args[0] in valid_ops
        )
        if is_scalar:
            left_val = float(element) if isinstance(element, (int, float)) else 0.0
            operator: OperatorType = args[0] if args else kwargs.get("operator", "==")
            right_val = (
                float(args[1])
                if len(args) > 1
                else float(kwargs.get("right_value", 0.0))
            )
            return cls.check_scalar(left_val, operator, right_val)

        return cls.check_block(element)

    @classmethod
    def check_scalar(
        cls, left_value: float, operator: OperatorType, right_value: float
    ) -> bool:
        """Compare left and right float values with given operator.

        Args:
            left_value: Left-hand operand.
            operator: Comparison operator.
            right_value: Right-hand operand.

        Returns:
            Boolean evaluation result.
        """
        ops = {
            "<": left_value < right_value,
            "<=": left_value <= right_value,
            ">": left_value > right_value,
            ">=": left_value >= right_value,
            "==": abs(left_value - right_value) < FLOAT_TOLERANCE,
            "!=": abs(left_value - right_value) >= FLOAT_TOLERANCE,
        }
        res = ops.get(operator, False)

        logger.debug(
            "FR-checker-comparison: %.4f %s %.4f -> %s",
            left_value,
            operator,
            right_value,
            res,
        )
        return res

    @classmethod
    def check_block(cls, el_block: Any) -> bool:
        """Validate an AST comparison block Element or XML string.

        Args:
            el_block: XML Element or XML string representing the block.

        Returns:
            True if block passes comparison checker validation, False otherwise.
        """
        elem = parse_element(el_block)
        if elem is None:
            logger.info("FR-checker-comparison: block element is None or unparseable")
            return False

        return_type = elem.attrib.get("returnType")
        if return_type is not None and return_type != "boolean":
            # it is not a comparison, skip it
            return True

        el_left = cls.get_parameter(elem, "#Left#")
        el_right = cls.get_parameter(elem, "#Right#")

        if el_left is None or el_right is None:
            # it doesn't have Left/Right parameters, skip it
            return cls.check_if_it_isnt_not_block(elem)

        if cls.check_incorrect_number_indicators_comparison(el_left, el_right, elem):
            # cannot compare two different number indicators
            return False

        return not cls.check_left_right_are_same(el_left, el_right)

    @classmethod
    def check_if_it_isnt_not_block(cls, el_block: ET.Element) -> bool:
        """Check if block is a 'Not' block and validates its returnType.

        Args:
            el_block: Block element.

        Returns:
            True if valid, False if invalid boolean Not block.
        """
        key = el_block.attrib.get("key", "")
        if key != "Not":
            return True

        el_value = cls.get_parameter(el_block, "#Value#")
        if el_value is None:
            return True

        ret_type = el_value.attrib.get("returnType")
        return not (ret_type is not None and ret_type != "boolean")

    @classmethod
    def check_incorrect_number_indicators_comparison(
        cls, el_left: ET.Element, el_right: ET.Element, el_comparison: ET.Element
    ) -> bool:
        """Check whether indicator comparison between left and right is invalid.

        Args:
            el_left: Left operand element.
            el_right: Right operand element.
            el_comparison: Comparison container block.

        Returns:
            True if comparison is incorrect, False if valid.
        """
        ret_type_l = el_left.attrib.get("returnType")
        ret_type_r = el_right.attrib.get("returnType")

        if ret_type_l is None or ret_type_r is None:
            return False

        if ret_type_l != ret_type_r:
            # cannot compare values of different types
            return True

        if ret_type_l == "number" and ret_type_r == "number":
            return cls._check_number_operands(el_left, el_right, el_comparison)

        return cls._check_range_times(el_left, el_right)

    @classmethod
    def _check_number_operands(
        cls, el_left: ET.Element, el_right: ET.Element, el_comparison: ET.Element
    ) -> bool:
        """Validate category rules when both operands return 'number'."""
        cat_type_l = el_left.attrib.get("categoryType")
        cat_type_r = el_right.attrib.get("categoryType")

        if cat_type_l is None or cat_type_r is None:
            return False

        key_l = el_left.attrib.get("key", "")
        key_r = el_right.attrib.get("key", "")

        if cat_type_l == "indicator" and cat_type_r == "indicator":
            return key_l != key_r

        if cat_type_l == "indicator" and cat_type_r == "other":
            return key_r != "Number"

        if cat_type_l == "other" and cat_type_r == "indicator":
            return key_l != "Number"

        if cat_type_l == "other" and cat_type_r == "other":
            return cls._check_other_and_other(
                key_l, key_r, el_left, el_right, el_comparison
            )

        return False

    @classmethod
    def _check_other_and_other(
        cls,
        key_l: str,
        key_r: str,
        el_left: ET.Element,
        el_right: ET.Element,
        el_comparison: ET.Element,
    ) -> bool:
        """Validate comparison when both operands are category 'other'."""
        if key_l == "Number":
            return cls.is_bar_time_block(key_r)

        if key_r == "Number":
            if cls.is_bar_time_block(key_l):
                if cls.check_bad_time_range(el_left, el_right):
                    return True
                comp_key = el_comparison.attrib.get("key", "")
                return "Crosses" in comp_key
            return True

        return cls.is_bar_time_block(key_l) and cls.is_bar_time_block(key_r)

    @classmethod
    def _check_range_times(cls, el_left: ET.Element, el_right: ET.Element) -> bool:
        """Check HHMM time validity for HighestInRange and LowestInRange blocks."""
        range_names = ("HighestInRange", "LowestInRange")
        key_l = el_left.attrib.get("key", "")
        bad_l = key_l in range_names and not cls.check_correct_hhmm_time(el_left)

        key_r = el_right.attrib.get("key", "")
        bad_r = key_r in range_names and not cls.check_correct_hhmm_time(el_right)

        return bad_l or bad_r

    @classmethod
    def check_correct_hhmm_time(cls, el_hl_block: ET.Element) -> bool:
        """Verify HHMM time format for HighestInRange and LowestInRange blocks.

        Args:
            el_hl_block: Block element.

        Returns:
            True if all time parameters are valid HHMM, False otherwise.
        """
        for el_param in list(el_hl_block):
            key = el_param.attrib.get("key")
            if key in ("#TimeFrom#", "#TimeTo#"):
                s_val = (el_param.text or "").strip()
                if not s_val:
                    continue
                try:
                    val = int(s_val)
                    hh = val // 100
                    mm = val % 100
                    if hh < 0 or hh > MAX_HOUR:
                        logger.info("FR-checker-comparison: bad hour: %d", val)
                        return False
                    if mm < 0 or mm > MAX_MINUTE:
                        logger.info("FR-checker-comparison: bad minute: %d", val)
                        return False
                except ValueError:
                    return False
        return True

    @classmethod
    def check_bad_time_range(
        cls, el_bar_time_block: ET.Element, el_number: ET.Element
    ) -> bool:
        """Check if number value is out of bounds for bar time block.

        Args:
            el_bar_time_block: Bar time block element.
            el_number: Number block element.

        Returns:
            True if time range is invalid, False if valid.
        """
        el_param = el_number.find("Param")
        if el_param is None:
            return False

        str_number_val = (el_param.text or "").strip()
        try:
            number_value = int(float(str_number_val))
        except ValueError, TypeError:
            return False

        key = el_bar_time_block.attrib.get("key", "")
        if "Hour" in key and (number_value < 0 or number_value > MAX_HOUR):
            return True
        if "Minute" in key and (number_value < 0 or number_value > MAX_MINUTE):
            return True
        return bool(
            "DayOfWeek" in key and (number_value < 0 or number_value > MAX_DAY_OF_WEEK)
        )

    @staticmethod
    def is_bar_time_block(key: str | None) -> bool:
        """Check whether block key represents a bar time component.

        Args:
            key: Block key string.

        Returns:
            True if key is Hour, Minute, or DayOfWeek, False otherwise.
        """
        if not key:
            return False
        return "Hour" in key or "Minute" in key or "DayOfWeek" in key

    @classmethod
    def check_left_right_are_same(
        cls, el_left: ET.Element, el_right: ET.Element
    ) -> bool:
        """Verify whether left and right operands serialize to identical raw XML.

        Args:
            el_left: Left operand element.
            el_right: Right operand element.

        Returns:
            True if left and right are identical, False otherwise.
        """
        xml1 = element_to_string(el_left)
        xml2 = element_to_string(el_right)
        return xml1 == xml2

    @staticmethod
    def get_parameter(el_block: ET.Element, parameter_name: str) -> ET.Element | None:
        """Get Item child from a Param child matching parameter_name key.

        Args:
            el_block: Container element.
            parameter_name: Name of parameter (e.g. #Left#).

        Returns:
            Child Item Element if found, otherwise None.
        """
        for el_param in list(el_block):
            key = el_param.attrib.get("key")
            if key == parameter_name:
                item = el_param.find("Item")
                if item is not None:
                    return item
                return el_param
        return None

"""Shared HaruQuant exception and error taxonomy helpers.

Defines shared HaruQuant exception types, error descriptors, and deterministic
MT5/runtime error lookup helpers.

This module is a utility error taxonomy, not an official AI tool file. It does
not expose agent-callable tools. Execution, broker, risk, data, and validation
tools can import these helpers internally when converting platform errors into
clear structured responses.

Exported AI Tools:
    None.

Public Helpers:
    - message_for: Return a known MT5/runtime message for a code.
    - error_from_retcode: Resolve a return code into ErrorInfo.
    - error_name: Return the canonical name for a return code.
    - is_success_retcode: Return True when a code indicates success.
    - descriptor_from_payload: Build an ErrorDescriptor from a raw mapping.
    - descriptor_to_dict: Convert an ErrorDescriptor into a JSON-safe dict.
    - error_info_to_dict: Convert ErrorInfo into a JSON-safe dict.
    - exception_from_descriptor: Return a typed TradeError for a descriptor.
    - raise_for_retcode: Raise a typed/clear exception for a failing retcode.

Classes:
    - ErrorDescriptor
    - ErrorInfo
    - ErrorContext
    - ErrorEnvelope
    - HaruQuantError
    - ConfigurationError
    - ValidationError
    - PolicyError
    - InfrastructureError
    - DomainError
    - TradeError
    - InvalidRequestError
    - InvalidVolumeError
    - InvalidPriceError
    - InvalidStopsError
    - TradeDisabledError
    - MarketClosedError
    - NoMoneyError
    - NoQuotesError
    - BrokerError
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, TypeAlias

from tools.utils.logger import logger

ErrorPayload: TypeAlias = Mapping[str, Any]
DescriptorDict: TypeAlias = dict[str, Any]

UNKNOWN_ERROR_CODE = -1
UNKNOWN_ERROR_NAME = "UNKNOWN"
UNKNOWN_ERROR_MESSAGE = "Unknown error"

SUCCESS_RETCODES = frozenset({0, 10008, 10009, 10010})
USER_ERROR_CODE_OFFSET = 65536


@dataclass(frozen=True)
class ErrorDescriptor:
    """
    Normalized error payload used across HaruQuant trading workflows.

    Args:
        code (int): Numeric error code.
        name (str): Canonical error name.
        message (str): Human-readable error message.
        domain (str): Error domain, for example ``trade`` or ``mt5``.
        retryable (bool): Whether the failed operation may be retried safely.
    """

    code: int
    name: str
    message: str
    domain: str = "trade"
    retryable: bool = False


@dataclass(frozen=True)
class ErrorInfo:
    """
    Metadata describing an MT5/runtime/trade error code.

    Args:
        code (int): Numeric error code.
        name (str): Canonical error name.
        message (str): Human-readable message.
        domain (str): Error domain.
        retryable (bool): Whether the operation may be retried safely.
    """

    code: int
    name: str
    message: str
    domain: str = "trade"
    retryable: bool = False


@dataclass(frozen=True)
class ErrorContext:
    """
    Lightweight context for an error.

    Args:
        code (str): Short category or contextual code.
        detail (str): Additional detail for troubleshooting.
    """

    code: str = "unknown"
    detail: str = ""


@dataclass(frozen=True)
class ErrorEnvelope:
    """
    Envelope wrapping an error descriptor with optional context.

    Args:
        descriptor (ErrorDescriptor): Primary normalized error descriptor.
        context (ErrorContext | None): Optional contextual metadata.
    """

    descriptor: ErrorDescriptor
    context: ErrorContext | None = None


class HaruQuantError(Exception):
    """
    Base exception for HaruQuant application errors.

    Args:
        message (str): Human-readable error message.
        code (str | None): Optional deterministic error code.
    """

    def __init__(self, message: str, *, code: str | None = None) -> None:
        """Initialize the base HaruQuant exception."""
        self.code = code or self.__class__.__name__
        self.message = _require_non_empty_string(message, "message")
        super().__init__(self.message)


HaruError = HaruQuantError


class ConfigurationError(HaruQuantError):
    """Raised when environment or settings configuration is invalid."""


class ValidationError(HaruQuantError):
    """Raised when internal validation fails before a safe response is built."""


class PolicyError(HaruQuantError):
    """Raised when deterministic policy prevents an operation."""


class InfrastructureError(HaruQuantError):
    """Raised when infrastructure, platform, or dependency behavior fails."""


class DomainError(HaruQuantError):
    """Raised when domain-level business logic fails."""


class TradeError(DomainError):
    """
    Base exception for trading-related failures.

    Args:
        descriptor (ErrorDescriptor): Normalized trade error descriptor.
        detail (str | None): Optional additional detail.
    """

    def __init__(self, descriptor: ErrorDescriptor, detail: str | None = None) -> None:
        """Initialize a trade exception from an ErrorDescriptor."""
        self.descriptor = descriptor
        self.detail = detail
        text = detail or descriptor.message
        super().__init__(
            f"[{descriptor.name}] {text} (code={descriptor.code})",
            code=descriptor.name,
        )


class InvalidRequestError(TradeError):
    """Raised for malformed or rejected trade requests."""


class InvalidVolumeError(TradeError):
    """Raised for invalid order volume levels."""


class InvalidPriceError(TradeError):
    """Raised for invalid price levels."""


class InvalidStopsError(TradeError):
    """Raised for invalid stop loss or take profit levels."""


class TradeDisabledError(TradeError):
    """Raised when trading is disabled for the account or symbol."""


class MarketClosedError(TradeError):
    """Raised when an operation is attempted while the market is closed."""


class NoMoneyError(TradeError):
    """Raised when margin or balance is insufficient for the request."""


class NoQuotesError(TradeError):
    """Raised when no price quotes are available from the server."""


class BrokerError(TradeError):
    """Raised for broker-side trade errors without a more specific class."""


MT5_MESSAGES: dict[int, str] = {
    0: "The operation completed successfully",
    1: "Unexpected internal error",
    2: "Wrong parameter in the inner call of the client terminal function",
    3: "Wrong parameter when calling the system function",
    4: "Not enough memory to perform the system function",
    5: "The structure contains string, dynamic array, structure, or class objects",
    6: "Array of a wrong type, wrong size, or damaged dynamic array object",
    7: (
        "Not enough memory for array relocation, or resizing a static array was "
        "attempted"
    ),
    8: "Not enough memory for string relocation",
    9: "Not initialized string",
    10: "Invalid date and/or time",
    11: "Requested array size exceeds 2 GB",
    12: "Wrong pointer",
    13: "Wrong type of pointer",
    14: "System function is not allowed to call",
    4001: "Wrong chart ID",
    4002: "Chart does not respond",
    4003: "Chart not found",
    4004: "No Expert Advisor in the chart that could handle the event",
    4005: "Chart opening error",
    4006: "Failed to change chart symbol and period",
    4007: "Failed to create timer",
    4008: "Wrong chart property ID",
    4009: "Error creating screenshots",
    4010: "Error navigating through chart",
    4011: "Error applying template",
    4012: "Subwindow containing the indicator was not found",
    4013: "Error adding an indicator to chart",
    4014: "Error deleting an indicator from the chart",
    4015: "Indicator not found on the specified chart",
    4201: "Error working with a graphical object",
    4202: "Graphical object was not found",
    4203: "Wrong ID of a graphical object property",
    4204: "Unable to get date corresponding to the value",
    4205: "Unable to get value corresponding to the date",
    4301: "Unknown symbol",
    4302: "Symbol is not selected in MarketWatch",
    4303: "Wrong identifier of a symbol property",
    4304: "Time of the last tick is not known",
    4305: "Error adding or deleting a symbol in MarketWatch",
    4401: "Requested history not found",
    4402: "Wrong ID of the history property",
    4501: "Global variable of the client terminal is not found",
    4502: "Global variable of the client terminal with the same name already exists",
    4503: "Email sending failed",
    4504: "Sound playing failed",
    4505: "Wrong identifier of the program property",
    4506: "Wrong identifier of the terminal property",
    4507: "File sending via FTP failed",
    4508: "Error in sending notification",
    4601: "Not enough memory for the distribution of indicator buffers",
    4602: "Wrong indicator buffer index",
    4603: "Wrong ID of the custom indicator property",
    4701: "Wrong account property ID",
    4702: "Wrong trade property ID",
    4703: "Trading by Expert Advisors prohibited",
    4704: "Position not found",
    4705: "Order not found",
    4706: "Deal not found",
    4707: "Trade request sending failed",
    4801: "Unknown symbol",
    4802: "Indicator cannot be created",
    4803: "Not enough memory to add the indicator",
    4804: "The indicator cannot be applied to another indicator",
    4805: "Error applying an indicator to chart",
    4806: "Requested data not found",
    4807: "Wrong indicator handle",
    4808: "Wrong number of parameters when creating an indicator",
    4809: "No parameters when creating an indicator",
    4810: "First parameter in the array must be the custom indicator name",
    4811: "Invalid parameter type in the array when creating an indicator",
    4812: "Wrong index of the requested indicator buffer",
    4901: "Depth Of Market can not be added",
    4902: "Depth Of Market can not be removed",
    4903: "The data from Depth Of Market can not be obtained",
    4904: "Error subscribing to receive new Depth Of Market data",
    5001: "More than 64 files cannot be opened at the same time",
    5002: "Invalid file name",
    5003: "Too long file name",
    5004: "File opening error",
    5005: "Not enough memory for cache to read",
    5006: "File deleting error",
    5007: "A file with this handle was closed, or was not opened",
    5008: "Wrong file handle",
    5009: "The file must be opened for writing",
    5010: "The file must be opened for reading",
    5011: "The file must be opened as binary",
    5012: "The file must be opened as text",
    5013: "The file must be opened as text or CSV",
    5014: "The file must be opened as CSV",
    5015: "File reading error",
    5016: "String size must be specified because the file is opened as binary",
    5017: "Text file is required for string arrays; other arrays require binary",
    5018: "This is not a file, this is a directory",
    5019: "File does not exist",
    5020: "File can not be rewritten",
    5021: "Wrong directory name",
    5022: "Directory does not exist",
    5023: "This is a file, not a directory",
    5024: "The directory cannot be removed",
    5025: "Failed to clear the directory",
    5026: "Failed to write a resource to a file",
    5201: "No date in the string",
    5202: "Wrong date in the string",
    5203: "Wrong time in the string",
    5204: "Error converting string to date",
    5205: "Not enough memory for the string",
    5206: "The string length is less than expected",
    5207: "Too large number, more than ULONG_MAX",
    5208: "Invalid format string",
    5209: "Amount of format specifiers is more than the parameters",
    5210: "Amount of parameters is more than the format specifiers",
    5211: "Damaged parameter of string type",
    5212: "Position outside the string",
    5213: "Zero added to the string end, a useless operation",
    5214: "Unknown data type when converting to a string",
    5215: "Damaged string object",
    5401: "Copying incompatible arrays",
    5402: "Receiving array is AS_SERIES and has insufficient size",
    5403: "Too small array, the starting position is outside the array",
    5404: "An array of zero length",
    5405: "Must be a numeric array",
    5406: "Must be a one-dimensional array",
    5407: "Timeseries cannot be used",
    5408: "Must be an array of type double",
    5409: "Must be an array of type float",
    5410: "Must be an array of type long",
    5411: "Must be an array of type int",
    5412: "Must be an array of type short",
    5413: "Must be an array of type char",
    5601: "OpenCL functions are not supported on this computer",
    5602: "Internal error occurred when running OpenCL",
    5603: "Invalid OpenCL handle",
    5604: "Error creating the OpenCL context",
    5605: "Failed to create a run queue in OpenCL",
    5606: "Error occurred when compiling an OpenCL program",
    5607: "Too long kernel name",
    5608: "Error creating an OpenCL kernel",
    5609: "Error setting parameters for the OpenCL kernel",
    5610: "OpenCL program runtime error",
    5611: "Invalid size of the OpenCL buffer",
    5612: "Invalid offset in the OpenCL buffer",
    5613: "Failed to create an OpenCL buffer",
    10004: "Requote",
    10006: "Request rejected",
    10007: "Request canceled by trader",
    10008: "Order placed",
    10009: "Request completed",
    10010: "Only part of the request was completed",
    10011: "Request processing error",
    10012: "Request canceled by timeout",
    10013: "Invalid request",
    10014: "Invalid volume",
    10015: "Invalid price",
    10016: "Invalid stops",
    10017: "Trade is disabled",
    10018: "Market is closed",
    10019: "There is not enough money to complete the request",
    10020: "Prices changed",
    10021: "There are no quotes to process the request",
    10022: "Invalid expiration",
    10023: "Order state changed",
    10024: "Too frequent requests",
    10025: "No changes in request",
    10026: "Autotrading disabled by server",
    10027: "Autotrading disabled by client",
    10028: "Request locked for processing",
    10029: "Order or position frozen",
    10030: "Invalid order filling type",
    10031: "No connection with the trade server",
    10032: "Only long positions allowed",
    10033: "Only short positions allowed",
    10034: "Only closing positions allowed",
    10035: "Position closed",
    10036: "Invalid close volume",
}

RETCODE_INFO: dict[int, ErrorInfo] = {
    0: ErrorInfo(0, "OK", "The operation completed successfully"),
    10004: ErrorInfo(10004, "TRADE_RETCODE_REQUOTE", "Requote", "trade", True),
    10006: ErrorInfo(10006, "TRADE_RETCODE_REJECT", "Request rejected", "trade", True),
    10007: ErrorInfo(10007, "TRADE_RETCODE_CANCEL", "Request canceled by trader"),
    10008: ErrorInfo(10008, "TRADE_RETCODE_PLACED", "Order placed"),
    10009: ErrorInfo(10009, "TRADE_RETCODE_DONE", "Request completed"),
    10010: ErrorInfo(
        10010,
        "TRADE_RETCODE_DONE_PARTIAL",
        "Only part of the request was completed",
    ),
    10011: ErrorInfo(
        10011,
        "TRADE_RETCODE_ERROR",
        "Request processing error",
        "trade",
        True,
    ),
    10012: ErrorInfo(
        10012,
        "TRADE_RETCODE_TIMEOUT",
        "Request canceled by timeout",
        "trade",
        True,
    ),
    10013: ErrorInfo(10013, "TRADE_RETCODE_INVALID", "Invalid request"),
    10014: ErrorInfo(10014, "TRADE_RETCODE_INVALID_VOLUME", "Invalid volume"),
    10015: ErrorInfo(10015, "TRADE_RETCODE_INVALID_PRICE", "Invalid price"),
    10016: ErrorInfo(10016, "TRADE_RETCODE_INVALID_STOPS", "Invalid stops"),
    10017: ErrorInfo(10017, "TRADE_RETCODE_TRADE_DISABLED", "Trade is disabled"),
    10018: ErrorInfo(
        10018,
        "TRADE_RETCODE_MARKET_CLOSED",
        "Market is closed",
        "trade",
        True,
    ),
    10019: ErrorInfo(
        10019,
        "TRADE_RETCODE_NO_MONEY",
        "There is not enough money to complete the request",
    ),
    10020: ErrorInfo(
        10020,
        "TRADE_RETCODE_PRICE_CHANGED",
        "Prices changed",
        "trade",
        True,
    ),
    10021: ErrorInfo(
        10021,
        "TRADE_RETCODE_PRICE_OFF",
        "There are no quotes to process the request",
        "trade",
        True,
    ),
    10022: ErrorInfo(10022, "TRADE_RETCODE_INVALID_EXPIRATION", "Invalid expiration"),
    10023: ErrorInfo(
        10023,
        "TRADE_RETCODE_ORDER_CHANGED",
        "Order state changed",
        "trade",
        True,
    ),
    10024: ErrorInfo(
        10024,
        "TRADE_RETCODE_TOO_MANY_REQUESTS",
        "Too frequent requests",
        "trade",
        True,
    ),
    10025: ErrorInfo(10025, "TRADE_RETCODE_NO_CHANGES", "No changes in request"),
    10026: ErrorInfo(
        10026,
        "TRADE_RETCODE_SERVER_DISABLES_AT",
        "Autotrading disabled by server",
    ),
    10027: ErrorInfo(
        10027,
        "TRADE_RETCODE_CLIENT_DISABLES_AT",
        "Autotrading disabled by client",
    ),
    10028: ErrorInfo(
        10028,
        "TRADE_RETCODE_LOCKED",
        "Request locked for processing",
        "trade",
        True,
    ),
    10029: ErrorInfo(10029, "TRADE_RETCODE_FROZEN", "Order or position frozen"),
    10030: ErrorInfo(10030, "TRADE_RETCODE_INVALID_FILL", "Invalid order filling type"),
    10031: ErrorInfo(
        10031,
        "TRADE_RETCODE_CONNECTION",
        "No connection with the trade server",
        "trade",
        True,
    ),
    10032: ErrorInfo(10032, "TRADE_RETCODE_ONLY_REAL", "Only long positions allowed"),
    10033: ErrorInfo(
        10033, "TRADE_RETCODE_LIMIT_ORDERS", "Only short positions allowed"
    ),
    10034: ErrorInfo(
        10034, "TRADE_RETCODE_LIMIT_VOLUME", "Only closing positions allowed"
    ),
    10035: ErrorInfo(10035, "TRADE_RETCODE_INVALID_ORDER", "Position closed"),
    10036: ErrorInfo(10036, "TRADE_RETCODE_POSITION_CLOSED", "Invalid close volume"),
}

RETCODE_EXCEPTION_TYPES: dict[int, type[TradeError]] = {
    10013: InvalidRequestError,
    10014: InvalidVolumeError,
    10015: InvalidPriceError,
    10016: InvalidStopsError,
    10017: TradeDisabledError,
    10018: MarketClosedError,
    10019: NoMoneyError,
    10021: NoQuotesError,
}


def _require_int(value: Any, field_name: str) -> int:
    """
    Validate an integer input.

    Args:
        value (Any): Candidate integer value.
        field_name (str): Field name used in error messages.

    Returns:
        int: Validated integer.

    Raises:
        TypeError: If the value is not an integer.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer.")

    return int(value)


def _require_non_empty_string(value: Any, field_name: str) -> str:
    """
    Validate and normalize a required string input.

    Args:
        value (Any): Candidate string value.
        field_name (str): Field name used in error messages.

    Returns:
        str: Trimmed non-empty string.

    Raises:
        TypeError: If the value is not a string.
        ValueError: If the string is empty.
    """
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string.")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty.")

    return normalized


def message_for(code: int) -> str | None:
    """
    Return the known MT5/runtime human-readable message for a code.

    Args:
        code (int): Numeric MT5/runtime/trade return code.

    Returns:
        str | None: Known message, or ``None`` when the code is unknown.

    Raises:
        TypeError: If ``code`` is not an integer.
    """
    safe_code = _require_int(code, "code")
    result = MT5_MESSAGES.get(safe_code)
    logger.debug(
        "Retrieved message for code | code=%s | found=%s",
        safe_code,
        result is not None,
    )
    return result


def error_from_retcode(code: int) -> ErrorInfo:
    """
    Resolve an MT5/runtime/trade return code into ErrorInfo.

    Args:
        code (int): Numeric MT5/runtime/trade return code.

    Returns:
        ErrorInfo: Deterministic error information for the code.

    Raises:
        TypeError: If ``code`` is not an integer.
    """
    safe_code = _require_int(code, "code")

    if safe_code in RETCODE_INFO:
        return RETCODE_INFO[safe_code]

    message = message_for(safe_code)
    if message is not None:
        return ErrorInfo(
            code=safe_code,
            name="MT5_RUNTIME_ERROR",
            message=message,
            domain="mt5",
            retryable=False,
        )

    if safe_code >= USER_ERROR_CODE_OFFSET:
        return ErrorInfo(
            code=safe_code,
            name="USER_ERROR",
            message=f"User error {safe_code - USER_ERROR_CODE_OFFSET}",
            domain="mt5",
            retryable=False,
        )

    return ErrorInfo(
        code=safe_code,
        name=UNKNOWN_ERROR_NAME,
        message=UNKNOWN_ERROR_MESSAGE,
        domain="trade",
        retryable=False,
    )


def error_name(code: int) -> str:
    """
    Return the canonical error name for a return code.

    Args:
        code (int): Numeric MT5/runtime/trade return code.

    Returns:
        str: Canonical error name.

    Raises:
        TypeError: If ``code`` is not an integer.
    """
    return error_from_retcode(code).name


def is_success_retcode(code: int) -> bool:
    """
    Return True when a return code indicates success or partial success.

    Args:
        code (int): Numeric MT5/runtime/trade return code.

    Returns:
        bool: True when the code represents success.

    Raises:
        TypeError: If ``code`` is not an integer.
    """
    safe_code = _require_int(code, "code")
    return safe_code in SUCCESS_RETCODES


def descriptor_from_payload(
    payload: ErrorPayload | None,
    *,
    fallback_code: int = UNKNOWN_ERROR_CODE,
) -> ErrorDescriptor:
    """
    Build an ErrorDescriptor from a raw broker, tool, or runtime payload.

    Args:
        payload (ErrorPayload | None): Raw error mapping. ``None`` returns the
            unknown fallback descriptor.
        fallback_code (int, optional): Code used when the payload does not
            provide one.

    Returns:
        ErrorDescriptor: Normalized error descriptor.

    Raises:
        TypeError: If payload is not a mapping or fallback_code/code is invalid.
        ValueError: If required string fields are empty.
    """
    safe_fallback_code = _require_int(fallback_code, "fallback_code")

    if payload is None:
        return ErrorDescriptor(
            code=safe_fallback_code,
            name=UNKNOWN_ERROR_NAME,
            message=UNKNOWN_ERROR_MESSAGE,
            domain="trade",
            retryable=False,
        )

    if not isinstance(payload, Mapping):
        raise TypeError("payload must be a mapping or None.")

    raw_code = payload.get("code", safe_fallback_code)
    code = _require_int(raw_code, "payload.code")
    info = error_from_retcode(code)

    name = _require_non_empty_string(payload.get("name", info.name), "payload.name")
    message = _require_non_empty_string(
        payload.get("message", info.message),
        "payload.message",
    )
    domain = _require_non_empty_string(
        payload.get("domain", info.domain),
        "payload.domain",
    )
    retryable = bool(payload.get("retryable", info.retryable))

    descriptor = ErrorDescriptor(
        code=code,
        name=name,
        message=message,
        domain=domain,
        retryable=retryable,
    )

    logger.debug(
        "Created ErrorDescriptor from payload | name=%s | code=%s | domain=%s",
        descriptor.name,
        descriptor.code,
        descriptor.domain,
    )
    return descriptor


def descriptor_to_dict(descriptor: ErrorDescriptor) -> DescriptorDict:
    """
    Convert an ErrorDescriptor into a JSON-safe dictionary.

    Args:
        descriptor (ErrorDescriptor): Descriptor to convert.

    Returns:
        DescriptorDict: JSON-safe descriptor dictionary.

    Raises:
        TypeError: If descriptor is not an ErrorDescriptor.
    """
    if not isinstance(descriptor, ErrorDescriptor):
        raise TypeError("descriptor must be an ErrorDescriptor.")

    return asdict(descriptor)


def error_info_to_dict(info: ErrorInfo) -> DescriptorDict:
    """
    Convert ErrorInfo into a JSON-safe dictionary.

    Args:
        info (ErrorInfo): Error information to convert.

    Returns:
        DescriptorDict: JSON-safe error info dictionary.

    Raises:
        TypeError: If info is not an ErrorInfo.
    """
    if not isinstance(info, ErrorInfo):
        raise TypeError("info must be an ErrorInfo.")

    return asdict(info)


def exception_from_descriptor(
    descriptor: ErrorDescriptor,
    detail: str | None = None,
) -> TradeError:
    """
    Return a typed trading exception for a descriptor.

    Args:
        descriptor (ErrorDescriptor): Normalized error descriptor.
        detail (str | None, optional): Additional detail for the exception.

    Returns:
        TradeError: Typed trade exception instance.

    Raises:
        TypeError: If descriptor is not an ErrorDescriptor.
        TypeError: If detail is provided but is not a string.
        ValueError: If detail is provided but empty.
    """
    if not isinstance(descriptor, ErrorDescriptor):
        raise TypeError("descriptor must be an ErrorDescriptor.")

    safe_detail = None
    if detail is not None:
        safe_detail = _require_non_empty_string(detail, "detail")

    exc_type = RETCODE_EXCEPTION_TYPES.get(descriptor.code, BrokerError)
    exception = exc_type(descriptor=descriptor, detail=safe_detail)

    logger.debug(
        "Mapped descriptor to exception | code=%s | exception=%s",
        descriptor.code,
        exc_type.__name__,
    )
    return exception


def raise_for_retcode(code: int, message: str = "") -> None:
    """
    Raise a typed or broker trade exception for a failing return code.

    Success return codes do not raise.

    Args:
        code (int): Numeric MT5/runtime/trade return code.
        message (str, optional): Optional contextual message.

    Raises:
        TypeError: If ``code`` or ``message`` has an invalid type.
        TradeError: If ``code`` is not a success retcode.
    """
    safe_code = _require_int(code, "code")
    safe_message = ""
    if message:
        safe_message = _require_non_empty_string(message, "message")

    if is_success_retcode(safe_code):
        logger.debug(
            "Retcode indicates success; no exception raised | code=%s", safe_code
        )
        return

    info = error_from_retcode(safe_code)
    descriptor = ErrorDescriptor(
        code=info.code,
        name=info.name,
        message=info.message,
        domain=info.domain,
        retryable=info.retryable,
    )

    detail = safe_message or None
    exception = exception_from_descriptor(descriptor, detail=detail)

    logger.error(
        "Raising exception for retcode | code=%s | name=%s | message=%s",
        safe_code,
        descriptor.name,
        detail or descriptor.message,
    )
    raise exception


__all__ = [
    "BrokerError",
    "ConfigurationError",
    "DescriptorDict",
    "DomainError",
    "ErrorContext",
    "ErrorDescriptor",
    "ErrorEnvelope",
    "ErrorInfo",
    "ErrorPayload",
    "HaruError",
    "HaruQuantError",
    "InfrastructureError",
    "InvalidPriceError",
    "InvalidRequestError",
    "InvalidStopsError",
    "InvalidVolumeError",
    "MarketClosedError",
    "MT5_MESSAGES",
    "NoMoneyError",
    "NoQuotesError",
    "PolicyError",
    "RETCODE_EXCEPTION_TYPES",
    "RETCODE_INFO",
    "SUCCESS_RETCODES",
    "TradeDisabledError",
    "TradeError",
    "UNKNOWN_ERROR_CODE",
    "ValidationError",
    "descriptor_from_payload",
    "descriptor_to_dict",
    "error_from_retcode",
    "error_info_to_dict",
    "error_name",
    "exception_from_descriptor",
    "is_success_retcode",
    "message_for",
    "raise_for_retcode",
]

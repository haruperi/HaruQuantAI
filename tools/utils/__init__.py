"""
Utility helpers and approved utility tools exposed by the HaruQuant utils package.

This package intentionally exposes both:
    - normal production utility helpers, such as ``logger`` and result builders;
    - approved AI-callable utility tools, such as multiprocessing logger tools.

Official AI Tools:
    - init_worker_logger
    - configure_multiprocess_listener

Utility Helpers:
    - configuration loading
    - logger
    - Logger
    - StructlogAdapter
    - success_result
    - error_result
    - blocked_result
    - needs_approval_result
    - needs_clarification_result
    - shared exception and error taxonomy helpers
    - trace ID generation and validation helpers
"""

# config.py utility helpers
from tools.utils.config import (
    DEFAULT_APP_NAME,
    DEFAULT_ENV_FILE,
    DEFAULT_ENVIRONMENT,
    DEFAULT_LOG_LEVEL,
    VALID_ENVIRONMENTS,
    VALID_LOG_LEVELS,
    Settings,
    get_environment,
    get_settings,
    is_production,
    is_test,
)

# errors.py utility helpers
from tools.utils.errors import (
    MT5_MESSAGES,
    RETCODE_EXCEPTION_TYPES,
    RETCODE_INFO,
    SUCCESS_RETCODES,
    UNKNOWN_ERROR_CODE,
    BrokerError,
    ConfigurationError,
    DescriptorDict,
    DomainError,
    ErrorContext,
    ErrorDescriptor,
    ErrorEnvelope,
    ErrorInfo,
    ErrorPayload,
    HaruError,
    HaruQuantError,
    InfrastructureError,
    InvalidPriceError,
    InvalidRequestError,
    InvalidStopsError,
    InvalidVolumeError,
    MarketClosedError,
    NoMoneyError,
    NoQuotesError,
    PolicyError,
    TradeDisabledError,
    TradeError,
    ValidationError,
    descriptor_from_payload,
    descriptor_to_dict,
    error_from_retcode,
    error_info_to_dict,
    error_name,
    exception_from_descriptor,
    is_success_retcode,
    message_for,
    raise_for_retcode,
)

# ids.py utility helpers
from tools.utils.ids import (
    ID_SEPARATOR,
    REQUEST_ID_PREFIX,
    RUN_ID_PREFIX,
    TOOL_CALL_ID_PREFIX,
    UUID_HEX_LENGTH,
    VALID_ID_PREFIXES,
    WORKFLOW_ID_PREFIX,
    is_request_id,
    is_run_id,
    is_tool_call_id,
    is_valid_prefixed_id,
    is_workflow_id,
    new_request_id,
    new_run_id,
    new_tool_call_id,
    new_workflow_id,
)

# logger.py utilities and AI tools
from tools.utils.logger import (
    CRITICAL,
    DEBUG,
    DEFAULT_LEVELS,
    ERROR,
    INFO,
    SUCCESS,
    TRACE,
    WARNING,
    CompatRecord,
    Logger,
    StructlogAdapter,
    configure_default_file_sinks,
    configure_multiprocess_listener,
    init_worker_logger,
    logger,
)

# result.py utility helpers
from tools.utils.result import (
    ERROR_APPROVAL_REQUIRED,
    ERROR_INVALID_INPUT,
    ERROR_MISSING_INPUT,
    ERROR_POLICY_BLOCKED,
    ERROR_UNKNOWN,
    ERROR_VALIDATION_FAILED,
    STATUS_BLOCKED,
    STATUS_ERROR,
    STATUS_NEEDS_APPROVAL,
    STATUS_NEEDS_CLARIFICATION,
    STATUS_SUCCESS,
    VALID_RESULT_STATUSES,
    blocked_result,
    error_result,
    needs_approval_result,
    needs_clarification_result,
    success_result,
)

__all__ = [
    # config.py utilities
    "DEFAULT_APP_NAME",
    "DEFAULT_ENV_FILE",
    "DEFAULT_ENVIRONMENT",
    "DEFAULT_LOG_LEVEL",
    "Settings",
    "VALID_ENVIRONMENTS",
    "VALID_LOG_LEVELS",
    "get_environment",
    "get_settings",
    "is_production",
    "is_test",
    # errors.py utilities
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
    # ids.py utilities
    "ID_SEPARATOR",
    "REQUEST_ID_PREFIX",
    "RUN_ID_PREFIX",
    "TOOL_CALL_ID_PREFIX",
    "UUID_HEX_LENGTH",
    "VALID_ID_PREFIXES",
    "WORKFLOW_ID_PREFIX",
    "is_request_id",
    "is_run_id",
    "is_tool_call_id",
    "is_valid_prefixed_id",
    "is_workflow_id",
    "new_request_id",
    "new_run_id",
    "new_tool_call_id",
    "new_workflow_id",
    # logger.py utilities
    "CRITICAL",
    "DEBUG",
    "DEFAULT_LEVELS",
    "ERROR",
    "INFO",
    "SUCCESS",
    "TRACE",
    "WARNING",
    "CompatRecord",
    "Logger",
    "StructlogAdapter",
    "configure_default_file_sinks",
    "logger",
    # logger.py official AI tools
    "configure_multiprocess_listener",
    "init_worker_logger",
    # result.py constants
    "ERROR_APPROVAL_REQUIRED",
    "ERROR_INVALID_INPUT",
    "ERROR_MISSING_INPUT",
    "ERROR_POLICY_BLOCKED",
    "ERROR_UNKNOWN",
    "ERROR_VALIDATION_FAILED",
    "STATUS_BLOCKED",
    "STATUS_ERROR",
    "STATUS_NEEDS_APPROVAL",
    "STATUS_NEEDS_CLARIFICATION",
    "STATUS_SUCCESS",
    "VALID_RESULT_STATUSES",
    # result.py utility helpers
    "blocked_result",
    "error_result",
    "needs_approval_result",
    "needs_clarification_result",
    "success_result",
]

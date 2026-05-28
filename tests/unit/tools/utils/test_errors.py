"""Unit tests for tools.utils.errors."""

from __future__ import annotations

import pytest

from tools.utils.errors import (
    BrokerError,
    ConfigurationError,
    DomainError,
    ErrorDescriptor,
    ErrorInfo,
    HaruError,
    HaruQuantError,
    InvalidVolumeError,
    MarketClosedError,
    NoMoneyError,
    NoQuotesError,
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


def test_foundation_exception_hierarchy() -> None:
    assert issubclass(ConfigurationError, HaruQuantError)
    assert issubclass(ValidationError, HaruQuantError)
    assert issubclass(DomainError, HaruQuantError)
    assert HaruError is HaruQuantError


def test_trade_exception_hierarchy() -> None:
    assert issubclass(TradeError, DomainError)
    assert issubclass(InvalidVolumeError, TradeError)
    assert issubclass(MarketClosedError, TradeError)
    assert issubclass(NoMoneyError, TradeError)
    assert issubclass(NoQuotesError, TradeError)


def test_haruquant_error_requires_non_empty_message() -> None:
    with pytest.raises(ValueError, match="message cannot be empty"):
        HaruQuantError("")


def test_message_for_known_and_unknown_codes() -> None:
    assert message_for(10014) == "Invalid volume"
    assert message_for(999999) is None


def test_message_for_rejects_non_integer_code() -> None:
    with pytest.raises(TypeError, match="code must be an integer"):
        message_for("10014")  # type: ignore[arg-type]


def test_error_from_retcode_known_trade_code() -> None:
    info = error_from_retcode(10014)

    assert isinstance(info, ErrorInfo)
    assert info.code == 10014
    assert info.name == "TRADE_RETCODE_INVALID_VOLUME"
    assert info.domain == "trade"


def test_error_from_retcode_known_mt5_runtime_code() -> None:
    info = error_from_retcode(4301)

    assert info.code == 4301
    assert info.name == "MT5_RUNTIME_ERROR"
    assert info.domain == "mt5"
    assert info.message == "Unknown symbol"


def test_error_from_retcode_user_error_code() -> None:
    info = error_from_retcode(65537)

    assert info.name == "USER_ERROR"
    assert info.message == "User error 1"


def test_error_from_retcode_unknown_code() -> None:
    info = error_from_retcode(123456)

    assert info.name == "USER_ERROR"
    assert info.domain == "mt5"


def test_error_name_returns_canonical_name() -> None:
    assert error_name(10018) == "TRADE_RETCODE_MARKET_CLOSED"


@pytest.mark.parametrize("code", [0, 10008, 10009, 10010])
def test_is_success_retcode_true_for_success_codes(code: int) -> None:
    assert is_success_retcode(code) is True


@pytest.mark.parametrize("code", [10013, 10014, 10018, 10031])
def test_is_success_retcode_false_for_failure_codes(code: int) -> None:
    assert is_success_retcode(code) is False


def test_descriptor_from_payload_none_uses_fallback() -> None:
    descriptor = descriptor_from_payload(None, fallback_code=-99)

    assert descriptor == ErrorDescriptor(
        code=-99,
        name="UNKNOWN",
        message="Unknown error",
        domain="trade",
        retryable=False,
    )


def test_descriptor_from_payload_valid_payload() -> None:
    descriptor = descriptor_from_payload(
        {
            "code": 10014,
            "name": "CUSTOM_INVALID_VOLUME",
            "message": "Volume is too small.",
            "domain": "trade",
            "retryable": False,
        }
    )

    assert descriptor.code == 10014
    assert descriptor.name == "CUSTOM_INVALID_VOLUME"
    assert descriptor.message == "Volume is too small."


def test_descriptor_from_payload_uses_retcode_defaults() -> None:
    descriptor = descriptor_from_payload({"code": 10018})

    assert descriptor.code == 10018
    assert descriptor.name == "TRADE_RETCODE_MARKET_CLOSED"
    assert descriptor.message == "Market is closed"
    assert descriptor.retryable is True


def test_descriptor_from_payload_rejects_invalid_payload_type() -> None:
    with pytest.raises(TypeError, match="payload must be a mapping"):
        descriptor_from_payload(["not", "mapping"])  # type: ignore[arg-type]


def test_descriptor_from_payload_rejects_invalid_code() -> None:
    with pytest.raises(TypeError, match="payload.code must be an integer"):
        descriptor_from_payload({"code": "10014"})


def test_descriptor_to_dict_and_error_info_to_dict_are_json_safe() -> None:
    descriptor = descriptor_from_payload({"code": 10014})
    info = error_from_retcode(10014)

    assert descriptor_to_dict(descriptor)["code"] == 10014
    assert error_info_to_dict(info)["name"] == "TRADE_RETCODE_INVALID_VOLUME"


def test_exception_from_descriptor_maps_known_trade_code() -> None:
    descriptor = descriptor_from_payload({"code": 10014})
    exception = exception_from_descriptor(descriptor, detail="Bad lot size.")

    assert isinstance(exception, InvalidVolumeError)
    assert exception.descriptor.code == 10014
    assert "Bad lot size" in str(exception)


def test_exception_from_descriptor_uses_broker_error_for_unknown_trade_code() -> None:
    descriptor = descriptor_from_payload({"code": 999})
    exception = exception_from_descriptor(descriptor)

    assert isinstance(exception, BrokerError)


def test_exception_from_descriptor_rejects_invalid_descriptor() -> None:
    with pytest.raises(TypeError, match="descriptor must be an ErrorDescriptor"):
        exception_from_descriptor({"code": 10014})  # type: ignore[arg-type]


def test_raise_for_retcode_does_not_raise_for_success_code() -> None:
    raise_for_retcode(10009)


def test_raise_for_retcode_raises_typed_exception() -> None:
    with pytest.raises(InvalidVolumeError):
        raise_for_retcode(10014, message="Order check failed.")


def test_raise_for_retcode_rejects_empty_message_when_provided() -> None:
    with pytest.raises(InvalidVolumeError):
        raise_for_retcode(10014)

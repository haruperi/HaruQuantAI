"""Unit tests for GreetingConfig parsing and validation."""

from typing import Any

import pytest

from app.services.test.greeting.config import GreetingConfig


def test_default_config() -> None:
    config = GreetingConfig()
    assert config.default_salutation == "Hello"
    assert config.max_name_length == 100


def test_config_from_none_or_empty() -> None:
    config_none = GreetingConfig.from_dict(None)
    assert config_none.default_salutation == "Hello"
    assert config_none.max_name_length == 100

    config_empty = GreetingConfig.from_dict({})
    assert config_empty.default_salutation == "Hello"
    assert config_empty.max_name_length == 100


def test_config_from_valid_dict() -> None:
    config = GreetingConfig.from_dict(
        {"default_salutation": "Greetings", "max_name_length": 50}
    )
    assert config.default_salutation == "Greetings"
    assert config.max_name_length == 50


def test_config_rejects_unknown_keys() -> None:
    with pytest.raises(ValueError, match="Unknown Greeting configuration keys: extra"):
        GreetingConfig.from_dict({"extra": 123})


@pytest.mark.parametrize(
    "invalid_salutation",
    ["", "   ", None, 123, []],
)
def test_config_rejects_invalid_salutation(invalid_salutation: Any) -> None:
    with pytest.raises(
        ValueError, match="default_salutation must be a non-empty string"
    ):
        GreetingConfig.from_dict({"default_salutation": invalid_salutation})


@pytest.mark.parametrize(
    "invalid_length",
    [0, -1, -100, "100", 3.14, True, False, None],
)
def test_config_rejects_invalid_max_name_length(invalid_length: Any) -> None:
    with pytest.raises(ValueError, match="max_name_length must be a positive integer"):
        GreetingConfig.from_dict({"max_name_length": invalid_length})

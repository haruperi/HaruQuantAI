"""Unit tests and usage verification for GreetingServiceImpl and greeting logic."""

from typing import Any

import pytest

from app.contracts.test.greeting import GreetingRequest
from app.services.test.greeting.greeting import (
    GreetingServiceImpl,
    _run_usage_example,
    generate_greeting_message,
)


def test_generate_greeting_message_success() -> None:
    msg, name, salutation = generate_greeting_message(
        name="Alice", salutation="Hello", max_name_length=100
    )
    assert msg == "Hello, Alice!"
    assert name == "Alice"
    assert salutation == "Hello"


def test_generate_greeting_message_trims_whitespace() -> None:
    msg, name, salutation = generate_greeting_message(
        name="   Bob Smith   ", salutation="  Hi  ", max_name_length=100
    )
    assert msg == "Hi, Bob Smith!"
    assert name == "Bob Smith"
    assert salutation == "Hi"


def test_generate_greeting_message_boundary_exact_max_length() -> None:
    max_len = 10
    exact_name = "A" * max_len
    msg, name, _ = generate_greeting_message(
        name=exact_name, salutation="Hello", max_name_length=max_len
    )
    assert msg == f"Hello, {exact_name}!"
    assert name == exact_name


@pytest.mark.parametrize(
    "blank_name",
    ["", "   ", "\t\n", None, 123],
)
def test_generate_greeting_message_rejects_empty_or_blank_name(
    blank_name: Any,
) -> None:
    with pytest.raises(ValueError, match="Caller name must not be empty or blank"):
        generate_greeting_message(
            name=blank_name, salutation="Hello", max_name_length=100
        )


def test_generate_greeting_message_rejects_exceeding_length() -> None:
    max_len = 5
    with pytest.raises(
        ValueError, match="Caller name exceeds maximum allowed length of 5"
    ):
        generate_greeting_message(
            name="Toolong", salutation="Hello", max_name_length=max_len
        )


@pytest.mark.asyncio
async def test_greeting_service_default_generation() -> None:
    service = GreetingServiceImpl()
    req = GreetingRequest(name="World")
    response = await service.generate_greeting(req)
    assert response.message == "Hello, World!"
    assert response.name == "World"
    assert response.salutation == "Hello"


@pytest.mark.asyncio
async def test_greeting_service_custom_request_salutation() -> None:
    service = GreetingServiceImpl(default_salutation="Hello")
    req = GreetingRequest(name="Dana", salutation="Good morning")
    response = await service.generate_greeting(req)
    assert response.message == "Good morning, Dana!"
    assert response.name == "Dana"
    assert response.salutation == "Good morning"


@pytest.mark.asyncio
async def test_greeting_service_custom_service_default() -> None:
    service = GreetingServiceImpl(default_salutation="Howdy", max_name_length=50)
    req = GreetingRequest(name="Partner")
    response = await service.generate_greeting(req)
    assert response.message == "Howdy, Partner!"
    assert response.name == "Partner"
    assert response.salutation == "Howdy"


@pytest.mark.asyncio
async def test_greeting_service_rejects_invalid_inputs() -> None:
    service = GreetingServiceImpl(max_name_length=10)
    with pytest.raises(ValueError, match="Caller name must not be empty or blank"):
        await service.generate_greeting(GreetingRequest(name="  "))

    with pytest.raises(
        ValueError, match="Caller name exceeds maximum allowed length of 10"
    ):
        await service.generate_greeting(GreetingRequest(name="12345678901"))


@pytest.mark.asyncio
async def test_usage_example_execution() -> None:
    """Verify that the designated primary domain-logic usage harness executes."""
    await _run_usage_example()

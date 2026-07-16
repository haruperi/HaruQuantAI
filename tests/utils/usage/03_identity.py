"""Executable trace-identifier examples."""

from app.utils import derive_stable_id, generate_id, validate_id


def example_generate_id() -> str:
    """Generate a request identifier."""
    return generate_id("req")


def example_validate_id() -> str:
    """Validate a generated identifier."""
    value = example_generate_id()
    return validate_id(value, expected_prefix="req")


def example_derive_stable_id() -> str:
    """Derive deterministic identity evidence."""
    return derive_stable_id("cor", "strategy:v1")


def main() -> None:
    """Run all identifier examples."""
    generated_id = example_generate_id()
    validated_id = validate_id(generated_id, expected_prefix="req")
    stable_id = example_derive_stable_id()
    assert validated_id.startswith("req-")
    assert stable_id == example_derive_stable_id()
    print("Generated request ID:", generated_id)
    print("Validated request ID:", validated_id)
    print("Stable correlation ID:", stable_id)


if __name__ == "__main__":
    main()

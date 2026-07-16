"""Executable stage-one policy-validation example."""

from app.utils import RedactionPolicy, SecurityError


def example_policy_validation() -> None:
    """Reject a protected credential allowlist."""
    try:
        RedactionPolicy(allowlisted_paths=frozenset({"broker.client_secret"}))
    except SecurityError:
        return
    raise AssertionError("protected credential field was allowlisted")


def main() -> None:
    """Run stage-one security policy validation."""
    example_policy_validation()
    print("Redaction policy: protected credential allowlist rejected")


if __name__ == "__main__":
    main()

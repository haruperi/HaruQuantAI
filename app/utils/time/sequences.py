"""Caller-owned monotonic sequence allocation."""

from collections.abc import Callable, MutableMapping

from app.utils.errors.exceptions import ValidationError


def next_sequence(
    scope: str, counter: MutableMapping[str, int] | Callable[[str], int]
) -> int:
    """Allocate a strictly increasing sequence in a caller-owned scope.

    Args:
        scope: Non-empty caller scope.
        counter: Caller-owned mapping or allocator.

    Returns:
        Next monotonic sequence.

    Raises:
        ValidationError: If scope or counter output is invalid.
    """
    if not scope or scope != scope.strip():
        raise ValidationError("SEQUENCE_SCOPE_INVALID")
    if callable(counter):
        value = counter(scope)
        if isinstance(value, bool) or value < 0:
            raise ValidationError("SEQUENCE_VALUE_INVALID")
        return value
    previous = counter.get(scope, -1)
    if isinstance(previous, bool) or not isinstance(previous, int) or previous < -1:
        raise ValidationError("SEQUENCE_VALUE_INVALID")
    value = previous + 1
    counter[scope] = value
    return value

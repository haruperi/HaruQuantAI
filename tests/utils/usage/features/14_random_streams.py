"""Standalone usage evidence for FEAT-UTIL-13."""

from app.utils import (
    derive_random_stream,
    get_stream_identity,
    next_choice,
    next_int,
    next_uniform,
)


def main() -> None:
    """Run deterministic independent random draws."""
    stream = derive_random_stream(42, "demo")
    assert get_stream_identity(stream)["stream_name"] == "demo"
    uniform, stream = next_uniform(stream)
    integer, stream = next_int(stream, lower=1, upper=6)
    choice, stream = next_choice(stream, ["A", "B"], weights=[1, 2])
    print("SUCCESS: FEAT-UTIL-13 random streams completed")
    print(f"Data -> draws={(uniform, integer, choice)}, stream={stream}")


if __name__ == "__main__":
    main()

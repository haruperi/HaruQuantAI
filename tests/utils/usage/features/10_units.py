"""Standalone usage evidence for FEAT-UTIL-09."""

from app.utils import add_exact, build_exact_unit, quantize_exact


def main() -> None:
    """Run exact-unit construction, arithmetic, and quantization."""
    total = add_exact(
        build_exact_unit("1.25", kind="MONEY", currency="USD"),
        build_exact_unit("2.25", kind="MONEY", currency="USD"),
    )
    result = quantize_exact(total, "0.1", direction="DOWN")
    print("SUCCESS: FEAT-UTIL-09 exact units completed")
    print(f"Data -> exact_unit={result}")


if __name__ == "__main__":
    main()

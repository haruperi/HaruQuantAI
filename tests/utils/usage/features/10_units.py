"""Standalone usage evidence for FEAT-UTIL-09."""

from app.utils import (
    add_exact,
    build_exact_unit,
    compare_exact,
    get_max_decimal_places,
    get_supported_unit_kinds,
    parse_exact_unit,
    quantize_exact,
    scale_exact,
    subtract_exact,
    unit_kind_requires_currency,
)


def main() -> None:
    """Run exact-unit construction, arithmetic, and quantization."""
    total = add_exact(
        build_exact_unit("1.25", kind="MONEY", currency="USD"),
        build_exact_unit("2.25", kind="MONEY", currency="USD"),
    )
    result = quantize_exact(total, "0.1", direction="DOWN")
    parsed = parse_exact_unit(result)
    assert compare_exact(parsed, result) == 0
    assert scale_exact(parsed, 2)["amount"] == "7.0"
    assert subtract_exact(total, build_exact_unit("1", kind="MONEY", currency="USD"))
    assert get_max_decimal_places() > 0
    assert "MONEY" in get_supported_unit_kinds()
    assert unit_kind_requires_currency("MONEY")
    print("SUCCESS: FEAT-UTIL-09 exact units completed")
    print(f"Data -> exact_unit={result}")


if __name__ == "__main__":
    main()

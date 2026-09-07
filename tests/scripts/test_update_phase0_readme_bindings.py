"""Tests for authoritative domain README binding normalization."""

from __future__ import annotations

from scripts.update_phase0_readme_bindings import normalized


def test_normalization_resolves_documentary_placeholders() -> None:
    """Open binding markers become explicit without fabricating runtime acceptance."""
    source = (
        "[Plan](x/HaruQuantAI_Phased_Feature_Implementation_Plan.md)\n"
        "| NOT_REVALIDATED | `data.example@1` | open |\n"
        "| BINDING_PENDING | keys | types | yes | validation |\n"
        "Literal protocol/DTO/operation symbols: bind to the compatible selected "
        "contract before implementation; no alternate signature is invented here.\n"
    )

    result = normalized(source, "a" * 40, "b" * 40)

    assert "Phased_Feature_Implementation_Plan.md" in result
    assert "DOCUMENTARY_BOUND" in result
    assert "PHASE0_BOUND" in result
    assert "BINDING_PENDING" not in result
    assert "no alternate signature is invented here" not in result
    assert "without claiming runtime certification" in result

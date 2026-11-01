"""Unit tests for BlockNegaterRegistry and all 15 negater definitions."""

from __future__ import annotations

import pytest
from app.extend.negater.catalog import (
    BlockNegaterRegistry,
    OscillatorComparisonsNegater,
    UpperLowerNegater,
)


def test_golden_fixture_oscillator_negater() -> None:
    """Verify golden fixture: RSI(14) > 70 negates to RSI(14) < 30."""
    res = OscillatorComparisonsNegater.negate("RSI(14) > 70")
    assert res == "RSI(14) < 30"

    # Also test via BlockNegaterRegistry
    res_reg = BlockNegaterRegistry.negate_node(
        "OscillatorComparisonsNegater", "RSI(14) > 70"
    )
    assert res_reg == "RSI(14) < 30"


def test_golden_fixture_band_negater() -> None:
    """Verify golden fixture: Close[1] CrossesAbove BollingerBands.Upper(20, 2)."""
    orig = "Close[1] CrossesAbove BollingerBands.Upper(20, 2)"
    expected = "Close[1] CrossesBelow BollingerBands.Lower(20, 2)"
    res = UpperLowerNegater.negate(orig)
    assert res == expected

    res_reg = BlockNegaterRegistry.negate_node("UpperLowerNegater", orig)
    assert res_reg == expected


def test_registry_contains_all_15_negaters() -> None:
    """Ensure exactly 15 negaters are registered."""
    negaters = BlockNegaterRegistry.list_negaters()
    assert len(negaters) == 15
    expected_15 = [
        "ActionsNegater",
        "AndOrNegater",
        "ComparisonsNegater",
        "OscillatorComparisonsNegater",
        "CDataIndyNegater",
        "ConditionsNegater",
        "UpperLowerNegater",
        "FiboNegater",
        "FractalNegater",
        "PivotsNegater",
        "UlcerNegater",
        "FormulaNegater",
        "FunctionsNegater",
        "CBlockNegater",
        "DefaultNegater",
    ]
    for n in expected_15:
        assert n in negaters


def test_actions_negater() -> None:
    """Test ActionsNegater swaps Long and Short entries/exits."""
    assert (
        BlockNegaterRegistry.negate_node("ActionsNegater", "EnterAtMarket(Long)")
        == "EnterAtMarket(Short)"
    )
    assert BlockNegaterRegistry.negate_node("ActionsNegater", "ExitLong") == "ExitShort"
    assert BlockNegaterRegistry.negate_node("ActionsNegater", "ExitShort") == "ExitLong"


def test_comparisons_and_pivots_negaters() -> None:
    """Test Comparisons and Pivots negater behavior."""
    assert (
        BlockNegaterRegistry.negate_node(
            "ComparisonsNegater", "Close[1] CrossesAbove Open[1]"
        )
        == "Close[1] CrossesBelow Open[1]"
    )
    assert BlockNegaterRegistry.negate_node("PivotsNegater", "High > R1") == "High > S1"
    assert (
        BlockNegaterRegistry.negate_node("FunctionsNegater", "Highest(Close, 20)")
        == "Lowest(Close, 20)"
    )


def test_unknown_negater_raises() -> None:
    """Ensure unknown negater name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown negater"):
        BlockNegaterRegistry.negate_node("NonExistentNegater", "foo")


def test_dict_negaters_coverage() -> None:
    """Ensure dictionary nodes across negaters are properly inverted."""
    # ActionsNegater dict
    d_act_long = {"action_type": "EnterAtMarket", "direction": "Long"}
    assert (
        BlockNegaterRegistry.negate_node("ActionsNegater", d_act_long)["direction"]
        == "Short"
    )

    d_act_short = {"action_type": "EnterAtMarket", "direction": "Short"}
    assert (
        BlockNegaterRegistry.negate_node("ActionsNegater", d_act_short)["direction"]
        == "Long"
    )

    d_exit_long = {"action_type": "ExitLong"}
    assert (
        BlockNegaterRegistry.negate_node("ActionsNegater", d_exit_long)["action_type"]
        == "ExitShort"
    )

    d_exit_short = {"action_type": "ExitShort"}
    assert (
        BlockNegaterRegistry.negate_node("ActionsNegater", d_exit_short)["action_type"]
        == "ExitLong"
    )

    # AndOrNegater dict
    d_and_or = {
        "type": "AND",
        "children": [
            {"operator": ">", "threshold": 50},
            {"operator": "<", "threshold": 20},
        ],
    }
    neg_and_or = BlockNegaterRegistry.negate_node("AndOrNegater", d_and_or)
    assert neg_and_or["children"][0]["operator"] == "<"
    assert neg_and_or["children"][1]["operator"] == ">"

    # ComparisonsNegater dict
    assert (
        BlockNegaterRegistry.negate_node("ComparisonsNegater", {"operator": ">="})[
            "operator"
        ]
        == "<="
    )
    assert (
        BlockNegaterRegistry.negate_node("ComparisonsNegater", {"operator": "<="})[
            "operator"
        ]
        == ">="
    )
    assert (
        BlockNegaterRegistry.negate_node(
            "ComparisonsNegater", {"operator": "IsGreater"}
        )["operator"]
        == "IsLower"
    )
    assert (
        BlockNegaterRegistry.negate_node("ComparisonsNegater", {"operator": "IsLower"})[
            "operator"
        ]
        == "IsGreater"
    )

    # OscillatorComparisonsNegater dict
    osc_dict = {"operator": ">", "threshold": 70, "indicator": "RSI(14)"}
    neg_osc = BlockNegaterRegistry.negate_node("OscillatorComparisonsNegater", osc_dict)
    assert neg_osc["operator"] == "<"
    assert neg_osc["threshold"] == 30.0

    # CDataIndyNegater
    assert (
        BlockNegaterRegistry.negate_node("CDataIndyNegater", "High > 10") == "Low > 10"
    )
    assert (
        BlockNegaterRegistry.negate_node("CDataIndyNegater", {"field": "High"})["field"]
        == "Low"
    )
    assert (
        BlockNegaterRegistry.negate_node("CDataIndyNegater", {"field": "Low"})["field"]
        == "High"
    )

    # ConditionsNegater composite
    assert (
        BlockNegaterRegistry.negate_node("ConditionsNegater", "RSI(14) > 80")
        == "RSI(14) < 20"
    )
    assert "Lower(20, 2)" in BlockNegaterRegistry.negate_node(
        "ConditionsNegater", "Close[1] CrossesAbove BollingerBands.Upper(20, 2)"
    )

    # UpperLowerNegater dict
    assert (
        BlockNegaterRegistry.negate_node("UpperLowerNegater", {"band": "Upper"})["band"]
        == "Lower"
    )
    assert (
        BlockNegaterRegistry.negate_node("UpperLowerNegater", {"band": "Lower"})["band"]
        == "Upper"
    )

    # FiboNegater
    assert (
        BlockNegaterRegistry.negate_node("FiboNegater", {"level": 0.382})["level"]
        == 0.618
    )

    # FractalNegater
    assert (
        BlockNegaterRegistry.negate_node("FractalNegater", "UpFractal") == "DownFractal"
    )
    assert (
        BlockNegaterRegistry.negate_node("FractalNegater", "DownFractal") == "UpFractal"
    )

    # PivotsNegater
    assert BlockNegaterRegistry.negate_node("PivotsNegater", "R2") == "S2"
    assert BlockNegaterRegistry.negate_node("PivotsNegater", "S1") == "R1"

    # UlcerNegater
    assert BlockNegaterRegistry.negate_node("UlcerNegater", "Ulcer > 5") == "Ulcer < 5"

    # FormulaNegater
    assert BlockNegaterRegistry.negate_node("FormulaNegater", "A + B") == "A - B"
    assert BlockNegaterRegistry.negate_node("FormulaNegater", "A - B") == "A + B"

    # CBlockNegater
    assert (
        BlockNegaterRegistry.negate_node("CBlockNegater", {"direction": 1})["direction"]
        == -1
    )
    assert (
        BlockNegaterRegistry.negate_node("CBlockNegater", {"direction": "Long"})[
            "direction"
        ]
        == "Short"
    )
    assert (
        BlockNegaterRegistry.negate_node("CBlockNegater", {"direction": "Short"})[
            "direction"
        ]
        == "Long"
    )

    # DefaultNegater
    assert BlockNegaterRegistry.negate_node("DefaultNegater", "A > B") == "A < B"

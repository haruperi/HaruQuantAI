"""Unit tests for BlockNegaterRegistry, NegatersList, and all 15 negater definitions."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from app.extend.negater import (
    ActionsNegater,
    AndOrNegater,
    BlockNegaterRegistry,
    CBlockNegater,
    CDataIndyNegater,
    ComparisonsNegater,
    ConditionsNegater,
    DefaultNegater,
    FiboNegater,
    FormulaNegater,
    FractalNegater,
    FunctionsNegater,
    OscillatorComparisonsNegater,
    PivotsNegater,
    UlcerNegater,
    UpperLowerNegater,
)


@dataclass
class DummyOrder:
    direction: str | int


@dataclass
class DummyFieldObj:
    field: str


@dataclass
class DummyOpObj:
    operator: str


@dataclass
class DummyFiboObj:
    FiboLevel: float


@dataclass
class DummyOutputObj:
    OutputIndex: int


@dataclass
class DummyUlcerObj:
    Mode: int


@dataclass
class DummyFuncObj:
    function: str


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


def test_pipeline_registration_and_order() -> None:
    """Ensure NegatersList orders negaters according to sort order."""
    pipeline = BlockNegaterRegistry.build_pipeline()
    orders = [cls.order for cls in pipeline.registered_classes]
    assert orders == sorted(orders)
    assert orders[0] == 100  # AndOrNegater
    assert orders[-1] == 1_000_000  # DefaultNegater

    # Pipeline negating a string
    res = pipeline.negate("RSI(14) > 70")
    assert res == "RSI(14) < 30"

    # Unhandled pass-through
    assert pipeline.negate(12345) == 12345


def test_actions_negater() -> None:
    """Test ActionsNegater across strings, dicts, and objects."""
    assert ActionsNegater.negate("EnterAtMarket(Long)") == "EnterAtMarket(Short)"
    assert ActionsNegater.negate("EnterAtStop(Short)") == "EnterAtStop(Long)"
    assert ActionsNegater.negate("EnterAtLimit(Long)") == "EnterAtLimit(Short)"
    assert ActionsNegater.negate("ExitLong") == "ExitShort"
    assert ActionsNegater.negate("ExitShort") == "ExitLong"

    # Dict with integer direction and exit methods
    d_act = {
        "direction": 1,
        "exit_methods": [{"action_type": "ExitLong", "direction": "Long"}],
    }
    neg_act = ActionsNegater.negate(d_act)
    assert neg_act["direction"] == -1
    assert neg_act["exit_methods"][0]["action_type"] == "ExitShort"

    d_act_neg1 = {"direction": -1}
    assert ActionsNegater.negate(d_act_neg1)["direction"] == 1

    # Object representation
    obj_long = DummyOrder("Long")
    ActionsNegater.negate(obj_long)
    assert obj_long.direction == "Short"

    obj_short = DummyOrder("Short")
    ActionsNegater.negate(obj_short)
    assert obj_short.direction == "Long"

    obj_int = DummyOrder(1)
    ActionsNegater.negate(obj_int)
    assert obj_int.direction == -1


def test_and_or_negater() -> None:
    """Test AndOrNegater recursing on children and preserving structure."""
    tree = {
        "type": "OR",
        "children": [
            "Close[1] CrossesAbove Open[1]",
            "RSI(14) > 70",
        ],
    }
    neg_tree = AndOrNegater.negate(tree)
    assert neg_tree["children"][0] == "Close[1] CrossesBelow Open[1]"
    assert neg_tree["children"][1] == "RSI(14) < 30"
    assert AndOrNegater.negate("plain string") == "plain string"


def test_c_block_negater() -> None:
    """Test CBlockNegater direction inversion and oscillator centering."""
    assert CBlockNegater.negate({"direction": 1})["direction"] == -1
    assert CBlockNegater.negate({"direction": "Long"})["direction"] == "Short"
    assert CBlockNegater.negate({"direction": "Short"})["direction"] == "Long"

    # Number vs Oscillator Indicator
    block_left_num = {"left": 70, "right": "RSI(14)"}
    neg_lr = CBlockNegater.negate(block_left_num)
    assert neg_lr["left"] == 30.0

    block_right_num = {"left": "RSI(14)", "right": 80}
    neg_rl = CBlockNegater.negate(block_right_num)
    assert neg_rl["right"] == 20.0

    # Object representation
    obj = DummyOrder("Long")
    CBlockNegater.negate(obj)
    assert obj.direction == "Short"
    CBlockNegater.negate(obj)
    assert obj.direction == "Long"
    obj_int = DummyOrder(1)
    CBlockNegater.negate(obj_int)
    assert obj_int.direction == -1


def test_c_data_indy_negater() -> None:
    """Test CDataIndyNegater swapping High and Low extremes."""
    assert CDataIndyNegater.negate("High > 10") == "Low > 10"
    assert CDataIndyNegater.negate("Low < 5") == "High < 5"

    d_high = {"field": "High", "value_index": 0}
    neg_d = CDataIndyNegater.negate(d_high)
    assert neg_d["field"] == "Low"
    assert neg_d["value_index"] == 1

    d_low = {"field": "Low", "value_index": 1}
    neg_d_low = CDataIndyNegater.negate(d_low)
    assert neg_d_low["field"] == "High"
    assert neg_d_low["value_index"] == 0

    obj = DummyFieldObj("High")
    CDataIndyNegater.negate(obj)
    assert obj.field == "Low"
    CDataIndyNegater.negate(obj)
    assert obj.field == "High"


def test_comparisons_and_pivots_negaters() -> None:
    """Test Comparisons and Pivots negater behavior."""
    assert (
        ComparisonsNegater.negate("Close[1] CrossesAbove Open[1]")
        == "Close[1] CrossesBelow Open[1]"
    )
    assert (
        ComparisonsNegater.negate("Close[1] CrossesBelow Open[1]")
        == "Close[1] CrossesAbove Open[1]"
    )
    assert ComparisonsNegater.negate("A IsRising") == "A IsFalling"
    assert ComparisonsNegater.negate("A IsFalling") == "A IsRising"
    assert ComparisonsNegater.negate("A >= B") == "A <= B"
    assert ComparisonsNegater.negate("A <= B") == "A >= B"
    assert ComparisonsNegater.negate("A == B") == "A == B"

    # Object representation
    obj = DummyOpObj(">")
    ComparisonsNegater.negate(obj)
    assert obj.operator == "<"

    # PivotsNegater strings
    assert PivotsNegater.negate("High > R1") == "High > S1"
    assert PivotsNegater.negate("Low < S2") == "Low < R2"
    assert PivotsNegater.negate("High > R3") == "High > S3"

    # Pivots output indices (0, 1, 2, 3, 4, 5, 6)
    for in_idx, out_idx in [
        (0, 0),
        (1, 4),
        (2, 5),
        (3, 6),
        (4, 1),
        (5, 2),
        (6, 3),
    ]:
        res_dict = PivotsNegater.negate({"output_index": in_idx})
        assert res_dict["output_index"] == out_idx

    # Pivots line names
    assert PivotsNegater.negate({"line_name": "R1"})["line_name"] == "S1"
    assert PivotsNegater.negate({"line_name": "S3"})["line_name"] == "R3"

    # Pivots object
    piv_obj = DummyOutputObj(1)
    PivotsNegater.negate(piv_obj)
    assert piv_obj.OutputIndex == 4


def test_fibo_negater() -> None:
    """Test FiboNegater ratio reflection around 1.0."""
    assert FiboNegater.negate({"level": 0.382})["level"] == 0.618
    assert FiboNegater.negate({"level": 0.236})["level"] == 0.764
    assert FiboNegater.negate("FiboLevel = 0.382") == "FiboLevel = 0.618"

    obj = DummyFiboObj(0.382)
    FiboNegater.negate(obj)
    assert obj.FiboLevel == 0.618


def test_formula_and_functions_negater() -> None:
    """Test FormulaNegater and FunctionsNegater."""
    assert FormulaNegater.negate("A + B - C") == "A - B + C"
    assert FormulaNegater.negate({"operator": "+"})["operator"] == "-"
    assert FormulaNegater.negate({"operator": "-"})["operator"] == "+"

    assert FunctionsNegater.negate("Highest(Close, 20)") == "Lowest(Close, 20)"
    assert FunctionsNegater.negate("Lowest(Close, 20)") == "Highest(Close, 20)"
    assert FunctionsNegater.negate({"function": "Highest"})["function"] == "Lowest"
    assert FunctionsNegater.negate({"function": "Lowest"})["function"] == "Highest"

    func_obj = DummyFuncObj("Highest")
    FunctionsNegater.negate(func_obj)
    assert func_obj.function == "Lowest"
    FunctionsNegater.negate(func_obj)
    assert func_obj.function == "Highest"


def test_fractal_and_ulcer_negaters() -> None:
    """Test FractalNegater and UlcerNegater."""
    assert FractalNegater.negate("UpFractal") == "DownFractal"
    assert FractalNegater.negate("DownFractal") == "UpFractal"
    assert FractalNegater.negate({"output_index": 0})["output_index"] == 1
    assert FractalNegater.negate({"output_index": 1})["output_index"] == 0
    assert FractalNegater.negate({"direction": "Up"})["direction"] == "Down"

    frac_obj = DummyOutputObj(0)
    FractalNegater.negate(frac_obj)
    assert frac_obj.OutputIndex == 1

    # Ulcer Index
    assert UlcerNegater.negate({"mode": 1})["mode"] == 2
    assert UlcerNegater.negate({"mode": 2})["mode"] == 1
    ulcer_obj = DummyUlcerObj(1)
    UlcerNegater.negate(ulcer_obj)
    assert ulcer_obj.Mode == 2
    UlcerNegater.negate(ulcer_obj)
    assert ulcer_obj.Mode == 1


def test_oscillator_comparisons_and_zero_center() -> None:
    """Test OscillatorComparisonsNegater with 50-midpoint and 0-midpoint."""
    assert OscillatorComparisonsNegater.negate("RSI(14) > 70") == "RSI(14) < 30"
    assert (
        OscillatorComparisonsNegater.negate("Stochastic.K(14, 3, 3) >= 80")
        == "Stochastic.K(14, 3, 3) <= 20"
    )

    # Zero-centered indicator (e.g. CCI)
    assert OscillatorComparisonsNegater.negate("CCI(14) > 100") == "CCI(14) < -100"
    assert (
        OscillatorComparisonsNegater.negate("MACD(12, 26, 9) < -5")
        == "MACD(12, 26, 9) > 5"
    )

    # Dict representation
    cci_dict = {"operator": ">", "threshold": 100, "indicator": "CCI(14)"}
    neg_cci = OscillatorComparisonsNegater.negate(cci_dict)
    assert neg_cci["operator"] == "<"
    assert neg_cci["threshold"] == -100


def test_conditions_and_upper_lower_negaters() -> None:
    """Test ConditionsNegater composite and UpperLowerNegater."""
    assert "Lower(20, 2)" in ConditionsNegater.negate(
        "Close[1] CrossesAbove BollingerBands.Upper(20, 2)"
    )
    assert ConditionsNegater.negate("RSI(14) > 70") == "RSI(14) < 30"
    assert ConditionsNegater.negate("Close > Open") == "Close < Open"

    cond_dict = {"indicator": "RSI(14)", "operator": ">", "threshold": 70}
    assert ConditionsNegater.negate(cond_dict)["threshold"] == 30.0

    # UpperLowerNegater dict & obj
    d_band = {"band": "Upper", "output_index": 0, "operator": ">"}
    neg_band = UpperLowerNegater.negate(d_band)
    assert neg_band["band"] == "Lower"
    assert neg_band["output_index"] == 1
    assert neg_band["operator"] == "<"

    band_obj = DummyOutputObj(0)
    UpperLowerNegater.negate(band_obj)
    assert band_obj.OutputIndex == 1


def test_default_negater_and_unknown_raises() -> None:
    """Test DefaultNegater and unknown registry identifier."""
    assert DefaultNegater.negate("A > B") == "A < B"

    with pytest.raises(ValueError, match="Unknown negater"):
        BlockNegaterRegistry.negate_node("InvalidNegater", "foo")

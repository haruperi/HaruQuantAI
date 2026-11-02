"""Verification tests for the 751-file donor extension cohort reconciliation."""

from __future__ import annotations

import json

from app.extend.blocks.bar_time._common import DateTime
from app.extend.money_management import (
    ATRRiskBasedSizing,
    BasePositionSizer,
    CryptoFixedAmount,
    CryptoFixedBalancePct,
    CryptoSizeByPrice,
    FixedAmount,
    FixedSize,
    PickerFixedAmount,
    PickerRiskFixedPctOfAccount,
    RiskFixedBalancePct,
    RiskFixedPctOfAccount,
    SimpleMartingaleMM,
    StocksSizeByPrice,
)
from app.extend.trading import (
    NoneCommission,
    NoScaling,
    PercentageBasedCommission,
    PerTradeCommission,
    SizeBasedCommission,
    StockpickerCommission,
)
from app.extend.trading_options import (
    DontTradeOnWeekends,
    ExitAtEndOfDay,
    ExitOnFriday,
    LimitTimeRange,
    MaxDistanceFromMarket,
    MaxTradesPerDay,
    MinMaxSLPT,
    UseInitialSLPT,
)
from app.workspace.code_editor._common import EXTEND_DIR, PROJECT_ROOT
from app.workspace.code_editor.path_policy import builtin_files, inspect_path
from app.workspace.code_editor.routes import CodeEditor


def test_cohort_ledger_accounts_for_all_751_donor_files():
    ledger_path = (
        PROJECT_ROOT / "docs/dev/fixtures/code-editor-extension-cohort-ledger.json"
    )
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert ledger["total_donor_files"] == 751
    expected_counts = {
        "Blocks": 670,
        "Calculators": 7,
        "Functions": 4,
        "Internal": 36,
        "Trading": 6,
        "TradingOptions": 8,
        "ExitMethods": 5,
        "MoneyManagement": 12,
        "RiskManagement": 1,
        "TALibIndicators": 1,
        "Utils": 1,
    }
    assert ledger["category_counts"] == expected_counts
    entries = ledger["entries"]
    assert len(entries) == 751
    for entry in entries:
        assert len(entry["sha256"]) == 64
        assert entry["classification"]
        assert entry["python_target"]


def test_builtin_manifest_and_editor_compilation_of_new_cohorts():
    builtin_files.cache_clear()
    shipped = {
        p.relative_to(PROJECT_ROOT).as_posix()
        for p in EXTEND_DIR.rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and not any(
            part.startswith((".", "commands_", "accept_", "impsess_"))
            for part in p.parts
        )
    }
    assert shipped == set(builtin_files())
    for rel_path in (
        "app/extend/what_if/by_days.py",
        "app/extend/checker/checkers.py",
        "app/extend/columns/trades/balance.py",
    ):
        info = inspect_path(rel_path)
        assert info.ownership == "builtin"
        assert info.protected is True

    editor = CodeEditor()
    mm_res = editor.compile_file("app/extend/what_if/by_days.py")
    assert mm_res["success"] is True
    sizers_res = editor.compile_file("app/extend/money_management/sizers.py")
    assert sizers_res["success"] is True
    sizing_res = editor.compile_file("app/extend/money_management/sizing.py")
    assert sizing_res["success"] is True


def test_all_12_money_management_sizers():
    sizers: list[BasePositionSizer] = [
        FixedSize(size=0.25, decimals=2),
        FixedAmount(risked_money=200.0, decimals=2, lots_if_no_mm=0.1, max_lots=5.0),
        RiskFixedPctOfAccount(
            risk_in_pct=2.0, decimals=2, lots_if_no_mm=0.1, max_lots=10.0
        ),
        RiskFixedBalancePct(
            risk_in_pct=2.0,
            decimals=2,
            lots_if_no_mm=0.1,
            max_lots=10.0,
            account_balance=10000.0,
        ),
        ATRRiskBasedSizing(
            risk_in_pct=2.0,
            atr_period=14,
            atr_multiplier=2.0,
            decimals=2,
            lots_if_no_mm=0.1,
            max_lots=10.0,
        ),
        StocksSizeByPrice(
            capital_pct=50.0, decimals=0, lots_if_no_mm=1.0, max_lots=500.0
        ),
        CryptoFixedAmount(
            risked_money=100.0, decimals=4, lots_if_no_mm=0.01, max_lots=50.0
        ),
        CryptoFixedBalancePct(
            risk_in_pct=2.0, decimals=4, lots_if_no_mm=0.01, max_lots=50.0
        ),
        CryptoSizeByPrice(
            capital_pct=10.0, decimals=4, lots_if_no_mm=0.01, max_lots=50.0
        ),
        PickerFixedAmount(
            amount=1000.0, decimals=0, lots_if_no_mm=1.0, max_lots=1000.0
        ),
        PickerRiskFixedPctOfAccount(
            risk_in_pct=10.0, decimals=0, lots_if_no_mm=1.0, max_lots=1000.0
        ),
        SimpleMartingaleMM(
            mm_StartLots=0.1, mm_Multiplier=2.0, mm_MaxLots=0.5, mm_Decimals=2
        ),
    ]
    assert len(sizers) == 12
    for sizer in sizers:
        lots = sizer.compute_size(10000.0, 20.0, 10.0)
        assert lots > 0.0
        fallback = sizer.compute_size(0.0, 0.0, 0.0)
        assert fallback >= 0.0

    martingale = SimpleMartingaleMM(
        mm_StartLots=0.1, mm_Multiplier=2.0, mm_MaxLots=0.5, mm_Decimals=2
    )
    assert martingale.compute_size(10000.0, 20.0) == 0.1
    martingale.record_trade_outcome(-50.0)
    assert martingale.compute_size(10000.0, 20.0) == 0.2
    martingale.record_trade_outcome(-50.0)
    assert martingale.compute_size(10000.0, 20.0) == 0.4
    martingale.record_trade_outcome(-50.0)
    # 0.8 > max_lots (0.5) -> resets to start_lots (0.1)
    assert martingale.compute_size(10000.0, 20.0) == 0.1
    martingale.record_trade_outcome(100.0)
    assert martingale.consecutive_losses == 0


def test_all_6_trading_commission_and_scaling_models():
    c_none = NoneCommission()
    assert c_none.compute_commission(size=2.0, open_price=100.0) == 0.0

    c_per_trade = PerTradeCommission(commission=6.5)
    assert c_per_trade.compute_commission(size=2.0, open_price=100.0) == 6.5
    assert c_per_trade.compute_commission(size=0.0, open_price=100.0) == 0.0

    c_size = SizeBasedCommission(commission_per_lot=7.0)
    assert c_size.compute_commission(size=2.5, open_price=1.1) == 17.5

    c_pct = PercentageBasedCommission(commission_pct=0.1)
    assert (
        c_pct.compute_commission(
            size=10.0, open_price=100.0, close_price=100.0, point_value=1.0
        )
        == 1.0
    )

    c_picker = StockpickerCommission(
        min_commission=1.0,
        max_commission_pct=1.0,
        per_share_commission=0.01,
        percentage_commission=0.0,
    )
    assert (
        c_picker.compute_commission(size=50.0, open_price=100.0, close_price=100.0)
        == 2.0
    )

    scaling = NoScaling()
    assert scaling.scale_size(3.5) == 3.5


def test_all_8_trading_options():
    fri_late = DateTime.to_long(2024, 1, 5, 21, 0, 0)  # Friday 21:00
    sat_noon = DateTime.to_long(2024, 1, 6, 12, 0, 0)  # Saturday 12:00
    sun_early = DateTime.to_long(2024, 1, 7, 18, 0, 0)  # Sunday 18:00
    mon_morning = DateTime.to_long(2024, 1, 8, 10, 0, 0)  # Monday 10:00

    weekend_opt = DontTradeOnWeekends(
        friday_close_time="20:00", sunday_open_time="22:00"
    )
    assert weekend_opt.is_trading_allowed(fri_late) is False
    assert weekend_opt.is_trading_allowed(sat_noon) is False
    assert weekend_opt.is_trading_allowed(sun_early) is False
    assert weekend_opt.is_trading_allowed(mon_morning) is True

    eod_opt = ExitAtEndOfDay(exit_time="20:30")
    assert eod_opt.should_exit(fri_late) is True
    assert eod_opt.should_exit(mon_morning) is False

    fri_opt = ExitOnFriday(exit_time="20:00")
    assert fri_opt.should_exit(fri_late) is True
    assert fri_opt.should_exit(mon_morning) is False

    range_opt = LimitTimeRange(
        range_from="09:00", range_to="16:00", exit_at_end_of_range=True
    )
    assert range_opt.is_entry_allowed(mon_morning) is True
    assert range_opt.should_exit(mon_morning) is False
    assert range_opt.is_entry_allowed(fri_late) is False
    assert range_opt.should_exit(fri_late) is True

    dist_opt = MaxDistanceFromMarket(max_distance_pct=2.0)
    assert dist_opt.is_order_price_valid(market_price=100.0, order_price=101.5) is True
    assert dist_opt.is_order_price_valid(market_price=100.0, order_price=105.0) is False

    max_trades_opt = MaxTradesPerDay(max_trades=2)
    assert max_trades_opt.is_entry_allowed(1) is True
    assert max_trades_opt.is_entry_allowed(2) is False

    slpt_opt = MinMaxSLPT(min_sl=15.0, max_sl=100.0, min_pt=20.0, max_pt=150.0)
    assert slpt_opt.clamp_sl_pips(5.0) == 15.0
    assert slpt_opt.clamp_sl_pips(250.0) == 100.0
    assert slpt_opt.clamp_pt_pips(10.0) == 20.0
    assert slpt_opt.clamp_pt_pips(200.0) == 150.0

    init_slpt = UseInitialSLPT(use_initial_sl_pt=True)
    assert init_slpt.should_attach_initial_brackets() is True

/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.options.parameters;

import com.strategyquant.tradinglib.Editor;
import com.strategyquant.tradinglib.ForEngine;
import com.strategyquant.tradinglib.Help;
import com.strategyquant.tradinglib.Parameter;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.TradingOption;
import com.strategyquant.tradinglib.engine.stockpicker.constants.PickerEodTypes;
import com.strategyquant.tradinglib.engine.stockpicker.constants.PickerTriggerTypes;
import com.strategyquant.tradinglib.strategy.xml.XmlStrategyException;

public class StockpickerOptions
extends TradingOption {
    @Parameter(name="Entry type", defaultValue="5", category="Stockpicker")
    @Help(value="Entry type - when the entry condition is checked")
    @Editor(type=40, values="Randomly generated=0,From strategy=1,On Bar Open=5,On Bar Close=10,Before Bar Open=15")
    @ForEngine(value="SP,SA")
    public int PickerEntryType;
    @Parameter(name="Exit type", defaultValue="5", category="Stockpicker")
    @Help(value="Exit type - when the exit condition is checked")
    @Editor(type=40, values="Randomly generated=0,From strategy=1,On Bar Open=5,On Bar Close=10,Before Bar Open=15")
    @ForEngine(value="SP,SA")
    public int PickerExitType;
    @Parameter(name="Exit End Of Day Long", defaultValue="5", category="Stockpicker")
    @Help(value="When to place close at end of day - it can be at real day close or next market open")
    @Editor(type=40, values="Randomly generated=0,From strategy=1,Yes=5,No=10")
    @ForEngine(value="SP,SA")
    public int PickerEndOfDayLong;
    @Parameter(name="Exit End Of Day Short", defaultValue="5", category="Stockpicker")
    @Help(value="When to place close at end of day - it can be at real day close or next market open")
    @Editor(type=40, values="Randomly generated=0,From strategy=1,Yes=5,No=10")
    @ForEngine(value="SP,SA")
    public int PickerEndOfDayShort;
    @Parameter(name="Max Open Positions Long", defaultValue="8", minValue=0.0, maxValue=500.0, category="Stockpicker")
    @Help(value="Max Open Positions configuration for Position score rule - how many stocks will be open at the same time")
    @ForEngine(value="SP")
    public int PickerMaxOpenPositionsLong;
    @Parameter(name="Max Open Positions Short", defaultValue="8", minValue=0.0, maxValue=500.0, category="Stockpicker")
    @Help(value="Max Open Positions configuration for Position score rule - how many stocks will be open at the same time")
    @ForEngine(value="SP")
    public int PickerMaxOpenPositionsShort;
    @Parameter(name="Store Stockpicker Logs", defaultValue="false", category="Stockpicker")
    @Help(value="Store stockpicker logs in the backtest result?")
    @ForEngine(value="SP,SA")
    public boolean PickerStoreLogs;
    @Parameter(name="Allow Better Limit Fill", defaultValue="false", category="Stockpicker")
    @Help(value="Fills limit orders at a better market price when available.")
    @ForEngine(value="SP,SA")
    public boolean PickerAllowBetterLimitFill;

    @Override
    public boolean OnBarUpdate(StrategyBase strategyBase) throws Exception {
        return true;
    }

    @Override
    public boolean isUsedInTrading() {
        return false;
    }

    @Override
    public TradingOption getClone() {
        StockpickerOptions stockpickerOptions = new StockpickerOptions();
        stockpickerOptions.PickerEntryType = this.PickerEntryType;
        stockpickerOptions.PickerExitType = this.PickerExitType;
        stockpickerOptions.PickerEndOfDayLong = this.PickerEndOfDayLong;
        stockpickerOptions.PickerEndOfDayShort = this.PickerEndOfDayShort;
        stockpickerOptions.PickerMaxOpenPositionsLong = this.PickerMaxOpenPositionsLong;
        stockpickerOptions.PickerMaxOpenPositionsShort = this.PickerMaxOpenPositionsShort;
        stockpickerOptions.PickerStoreLogs = this.PickerStoreLogs;
        stockpickerOptions.PickerAllowBetterLimitFill = this.PickerAllowBetterLimitFill;
        return stockpickerOptions;
    }

    public byte getEntryType(byte by) throws XmlStrategyException {
        return this.optionValue("PickerEntryType", (byte)this.PickerEntryType, by, PickerTriggerTypes.AvailableOptions);
    }

    public byte getExitType(byte by) throws XmlStrategyException {
        return this.optionValue("PickerExitType", (byte)this.PickerExitType, by, PickerTriggerTypes.AvailableOptions);
    }

    public byte getEndOfDayLong(byte by) throws XmlStrategyException {
        return this.optionValue("PickerEndOfDayLong", (byte)this.PickerEndOfDayLong, by, PickerEodTypes.AvailableOptions);
    }

    public byte getEndOfDayShort(byte by) throws XmlStrategyException {
        return this.optionValue("PickerEndOfDayShort", (byte)this.PickerEndOfDayShort, by, PickerEodTypes.AvailableOptions);
    }

    private byte optionValue(String string, byte by, byte by2, byte[] byArray) throws XmlStrategyException {
        if (by == 0 || by == 1) {
            return by2;
        }
        byte by3 = -1;
        for (int i = 0; i < byArray.length; ++i) {
            if (byArray[i] != by) continue;
            by3 = by;
            break;
        }
        if (by3 == -1) {
            throw new XmlStrategyException(String.format("Unexpected value %d for option %s.", by, string));
        }
        return by3;
    }

    public int getMaxOpenPositionsLong(int n) {
        if (this.PickerMaxOpenPositionsLong == 0) {
            return n;
        }
        return this.PickerMaxOpenPositionsLong;
    }

    public int getMaxOpenPositionsShort(int n) {
        if (this.PickerMaxOpenPositionsShort == 0) {
            return n;
        }
        return this.PickerMaxOpenPositionsShort;
    }

    public boolean storeLogs() {
        return this.PickerStoreLogs;
    }

    public boolean allowBetterLimitFill() {
        return this.PickerAllowBetterLimitFill;
    }
}


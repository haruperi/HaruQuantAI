/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.snippets.CustomClasses
 *  com.strategyquant.lib.snippets.NonexistingCustomClassException
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.options;

import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.snippets.CustomClasses;
import com.strategyquant.lib.snippets.NonexistingCustomClassException;
import com.strategyquant.tradinglib.TradingOption;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.options.parameters.BrokerOption;
import com.strategyquant.tradinglib.options.parameters.LimitOver;
import com.strategyquant.tradinglib.options.parameters.MarketOpenSession;
import com.strategyquant.tradinglib.options.parameters.RealisticGapsHandling;
import com.strategyquant.tradinglib.options.parameters.ReservedBars;
import com.strategyquant.tradinglib.options.parameters.SessionOption;
import com.strategyquant.tradinglib.options.parameters.StockpickerOptions;
import com.strategyquant.tradinglib.options.parameters.StoreChartData;
import java.util.List;
import org.jdom2.Element;

public class TradingOptionsList
extends CustomClasses<TradingOption> {
    private static TradingOptionsList instance;

    public static TradingOptionsList getInstance() {
        if (instance == null) {
            instance = new TradingOptionsList();
        }
        return instance;
    }

    private TradingOptionsList() {
        this.setDirName("TradingOptions");
        this.setExpectedClassType(TradingOption.class);
        this.loadAvailableClasses();
    }

    private void loadBuiltinClass(String string) {
        try {
            this.add(this.getNewBuiltInClass(string));
        }
        catch (Exception exception) {
            String string2 = String.format("Error loading builtin class '%s': '%s'", string, exception);
            this.addError(string, string2);
        }
    }

    public void loadAvailableClasses() {
        super.loadAvailableClasses();
        this.loadBuiltinClass("SessionOption");
        this.loadBuiltinClass("ReservedBars");
        this.loadBuiltinClass("StoreChartData");
        this.loadBuiltinClass("RealisticGapsHandling");
        this.loadBuiltinClass("StockpickerOptions");
        this.loadBuiltinClass("BrokerOption");
        this.loadBuiltinClass("MarketOpenSession");
        this.loadBuiltinClass("LimitOver");
    }

    public TradingOptions cloneAvailableClasses() {
        TradingOptions tradingOptions = new TradingOptions();
        for (TradingOption tradingOption : this.getAvailableClasses()) {
            String string = tradingOption.getClass().getSimpleName();
            TradingOption tradingOption2 = this.getNewBuiltInClass(string);
            if (tradingOption2 == null) {
                tradingOption2 = (TradingOption)this.createNew(string);
            }
            tradingOptions.add(tradingOption2);
        }
        return tradingOptions;
    }

    public TradingOptions parseOptionsFromXml(Element element) {
        TradingOptions tradingOptions = this.cloneAvailableClasses();
        if (element == null) {
            return tradingOptions;
        }
        Element element2 = XMLUtil.tryAddElement((Element)element, (String)"Params");
        List list = element2.getChildren("Param");
        for (int i = 0; i < list.size(); ++i) {
            Element element3 = (Element)list.get(i);
            try {
                String string = element3.getAttributeValue("className");
                if (string.equals("DontUsePriceRangeInConditions") || string.equals("ReplacePendingOrders") || string.equals("ComputeDailyStats") || string.equals("UseInitialSL")) continue;
                try {
                    TradingOption tradingOption = this.findClassByName(tradingOptions, string);
                    tradingOption.setFromParameterEl(element3);
                }
                catch (Exception exception) {
                    Log.debug(string + " is not exist. " + string + " will not be loaded.");
                }
                continue;
            }
            catch (Exception exception) {
                Log.error("Exc.", (Throwable)exception);
            }
        }
        return tradingOptions;
    }

    public TradingOption findClassByName(TradingOptions tradingOptions, String string) throws NonexistingCustomClassException {
        for (TradingOption tradingOption : tradingOptions) {
            if (!tradingOption.getClass().getSimpleName().equals(string)) continue;
            return tradingOption;
        }
        throw new NonexistingCustomClassException(string);
    }

    public TradingOption getNewBuiltInClass(String string) {
        switch (string) {
            case "SessionOption": {
                return new SessionOption();
            }
            case "StoreChartData": {
                return new StoreChartData();
            }
            case "RealisticGapsHandling": {
                return new RealisticGapsHandling();
            }
            case "ReservedBars": {
                return new ReservedBars();
            }
            case "StockpickerOptions": {
                return new StockpickerOptions();
            }
            case "BrokerOption": {
                return new BrokerOption();
            }
            case "MarketOpenSession": {
                return new MarketOpenSession();
            }
            case "LimitOver": {
                return new LimitOver();
            }
        }
        return null;
    }
}


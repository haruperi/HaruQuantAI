/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.options;

import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.TradingOption;
import com.strategyquant.tradinglib.options.TradingOptionsList;
import com.strategyquant.tradinglib.options.parameters.ReservedBars;
import com.strategyquant.tradinglib.options.parameters.StoreChartData;
import java.util.ArrayList;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TradingOptions
extends ArrayList<TradingOption> {
    public static final Logger Log = LoggerFactory.getLogger((String)"TradingOptions");

    public TradingOptions getClone() throws CloneNotSupportedException {
        TradingOptions tradingOptions = new TradingOptions();
        for (int i = 0; i < this.size(); ++i) {
            TradingOption tradingOption = (TradingOption)this.get(i);
            tradingOptions.add(tradingOption.getClone());
        }
        return tradingOptions;
    }

    public static String list() {
        Element element = new Element("Options");
        boolean bl = MainApp.checkProduct((String)"BACKTESTNODE");
        List list = TradingOptionsList.getInstance().getAvailableClasses();
        for (TradingOption tradingOption : list) {
            if (tradingOption == null || bl && (tradingOption instanceof StoreChartData || tradingOption instanceof ReservedBars)) continue;
            element.addContent((Content)tradingOption.getXML());
        }
        return XMLUtil.elementToString((Element)element);
    }
}


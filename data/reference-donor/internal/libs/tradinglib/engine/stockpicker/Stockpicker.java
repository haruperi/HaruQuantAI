/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.engine.stockpicker;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.engine.stockpicker.backtester.BacktestData;
import com.strategyquant.tradinglib.talib.TALibIndicators;
import java.io.File;
import java.util.ArrayList;
import org.jdom2.Element;

public class Stockpicker {
    public TALibIndicators TALibIndicators = new TALibIndicators();
    public boolean LongEntryExists = false;
    public boolean ShortEntryExists = false;
    public int MaxOpenPositionsLong = 0;
    public int MaxOpenPositionsShort = 0;
    public byte entryType;
    public byte exitType;
    public byte eodLong;
    public byte eodShort;
    public byte strategyTriggeredAt;
    public BacktestData data;
    public boolean singleAsset = false;
    private static boolean debugMode = false;
    private static File debugModeFile = null;

    public int getCurrentBar(int n) {
        return this.data.getCurrentBar(n);
    }

    public byte strategyTriggeredAt() {
        return this.strategyTriggeredAt;
    }

    public byte entryType() {
        return this.entryType;
    }

    public byte exitType() {
        return this.exitType;
    }

    public boolean isSingleAssetStrategy() {
        return this.singleAsset;
    }

    public long TimeCurrent() throws TradingException {
        return this.data.getCurrentTime();
    }

    public int BarCurrent() {
        return this.data.getCurrentBar();
    }

    public void setData(BacktestData backtestData) {
        this.data = backtestData;
    }

    public static boolean isDebugModeEnabled() {
        if (debugModeFile == null) {
            debugModeFile = new File(MainApp.getDataPath() + "/pickerdebug.txt");
            debugMode = debugModeFile.exists();
        }
        return debugMode;
    }

    public void clear() {
        if (this.TALibIndicators != null) {
            this.TALibIndicators.clear();
        }
    }

    public int getMaxOpenPositions() {
        int n = 0;
        if (this.LongEntryExists) {
            n += this.MaxOpenPositionsLong;
        }
        if (this.ShortEntryExists) {
            n += this.MaxOpenPositionsShort;
        }
        return n;
    }

    public static int getMaxOpenPosition(Element element, int n) {
        if (Stockpicker.isEntryRuleEmpty(element, n)) {
            return 0;
        }
        ArrayList arrayList = new ArrayList();
        XMLUtil.findAll((Element)element, (String)"Rule", arrayList);
        block0: for (Element element2 : arrayList) {
            String string;
            int n2;
            String string2 = element2.getAttributeValue("type");
            if (string2 == null || !string2.equals("StockpickerPS") || n != (n2 = (string = element2.getAttributeValue("name")).equalsIgnoreCase("Position Score Long") ? 1 : -1)) continue;
            ArrayList arrayList2 = new ArrayList();
            XMLUtil.findAllWithKey((Element)element2, (String)"Item", (String)"AssignVariable", arrayList2);
            for (Element element3 : arrayList2) {
                if (XMLUtil.findFirstWithKey((Element)element3, (String)"Param", (String)"#MaxOpenPositions#") == null) continue;
                Element element4 = XMLUtil.findFirstWithKey((Element)element3, (String)"Param", (String)"#Value#");
                if (element4 == null) continue block0;
                return Integer.valueOf(element4.getText());
            }
        }
        return 0;
    }

    private static boolean isEntryRuleEmpty(Element element, int n) {
        ArrayList arrayList = new ArrayList();
        XMLUtil.findAll((Element)element, (String)"Rule", arrayList);
        for (Element element2 : arrayList) {
            String string;
            int n2;
            String string2 = element2.getAttributeValue("type");
            if (string2 == null || !string2.equals("StockpickerEntryExit") || n != (n2 = (string = element2.getAttributeValue("name")).equalsIgnoreCase("Long") ? 1 : -1)) continue;
            Element element3 = element2.getChild("Entry");
            return element3 == null || element3.getChildren().isEmpty();
        }
        return false;
    }
}


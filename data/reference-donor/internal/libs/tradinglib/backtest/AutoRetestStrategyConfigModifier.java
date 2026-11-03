/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.TimeframeManager
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.backtest.AutoRetestSettings;
import java.util.ArrayList;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AutoRetestStrategyConfigModifier {
    private static final Logger Log = LoggerFactory.getLogger(AutoRetestStrategyConfigModifier.class);

    public static void modifySettings(Element element, Element element2) throws Exception {
        AutoRetestSettings autoRetestSettings = new AutoRetestSettings();
        autoRetestSettings.init(element2);
        Element element3 = element.getChild("Data");
        AutoRetestStrategyConfigModifier.modifyDataSettings(element3, autoRetestSettings);
        if (autoRetestSettings.useCustomMoneyManagement()) {
            element.removeChild("RiskMoneyManagement");
            element.addContent((Content)element2.getChild("RiskMoneyManagement").clone());
        }
        if (autoRetestSettings.useCustomTradingOptions()) {
            element.removeChild("Options");
            element.addContent((Content)element2.getChild("Options").clone());
        }
        element.removeChild("Rankings");
        element.addContent((Content)element2.getChild("Rankings").clone());
        element.removeChild("CrossChecks");
        element.addContent((Content)element2.getChild("CrossChecks").clone());
        AutoRetestStrategyConfigModifier.modifyAdditionalMarketsSettings(element.getChild("CrossChecks").getChild("RetestOnAdditionalMarkets"), element3);
        element.removeChild("ATMs");
        if (element2.getChild("ATMs") != null) {
            element.addContent((Content)element2.getChild("ATMs").clone());
        }
    }

    private static void modifyDataSettings(Element element, AutoRetestSettings autoRetestSettings) throws Exception {
        Object object;
        Element element2 = element.getChild("Setups");
        List list = element2.getChildren("Setup");
        String string = null;
        String string2 = null;
        for (int i = 0; i < list.size(); ++i) {
            DataInfo dataInfo;
            Element element3 = (Element)list.get(i);
            Element element4 = element3.getChild("Chart");
            if (element4 == null) continue;
            object = element4.getAttributeValue("symbol");
            if (i == 0) {
                string = element3.getAttributeValue("dateTo");
                AutoRetestStrategyConfigModifier.modifySetup(element3, autoRetestSettings);
                object = element4.getAttributeValue("symbol");
            }
            if ((dataInfo = DataManager.getDataInfo((String)"History", (String)object)) == null) continue;
            String string3 = SQTime.formatDate((long)dataInfo.dateTo);
            if (i == 0) {
                string2 = autoRetestSettings.useCustomDates() ? autoRetestSettings.getDateTo() : string3;
            }
            element3.setAttribute("dateTo", string2);
        }
        Element element5 = XMLUtil.getChildElem((Element)element, (String)"OutOfSample", (String)"<OutOfSample showGraph='false'/>");
        if (autoRetestSettings.useCustomDates()) {
            element5.removeContent();
        } else {
            try {
                if (string != null && string2 != null) {
                    long l = SQTime.parseDateToMilis(string);
                    object = element5.getChildren("Range");
                    boolean bl = false;
                    for (int i = 0; i < object.size(); ++i) {
                        Element element6 = (Element)object.get(i);
                        long l2 = SQTime.parseDateToMilis((String)element6.getAttributeValue("dateTo"));
                        if (l2 != l) continue;
                        element6.setAttribute("dateTo", string2);
                        bl = true;
                        break;
                    }
                    if (!bl) {
                        Element element7 = new Element("Range");
                        element7.setAttribute("dateFrom", string);
                        element7.setAttribute("dateTo", string2);
                        element5.addContent((Content)element7);
                    }
                } else {
                    Log.error("Cannot update OOS ranges. prevDateTo: " + string + ", newDateTo: " + string2);
                }
            }
            catch (Exception exception) {
                Log.error("Updating OOS ranges failed", (Throwable)exception);
            }
        }
    }

    private static void modifySetup(Element element, AutoRetestSettings autoRetestSettings) {
        List list = element.getChildren("Chart");
        Element element2 = (Element)list.get(0);
        if (autoRetestSettings.useCustomEngine()) {
            element.setAttribute("engine", autoRetestSettings.getEngine());
        }
        if (autoRetestSettings.useCustomSymbol()) {
            element2.setAttribute("symbol", autoRetestSettings.getSymbol());
        }
        if (autoRetestSettings.useCustomTimeframe()) {
            element2.setAttribute("timeframe", autoRetestSettings.getTimeframe());
        }
        if (autoRetestSettings.useCustomDates()) {
            element.setAttribute("dateFrom", autoRetestSettings.getDateFrom());
            element.setAttribute("dateTo", autoRetestSettings.getDateTo());
        }
        if (autoRetestSettings.useCustomPrecision()) {
            element.setAttribute("testPrecision", "" + autoRetestSettings.getPrecision());
        }
        if (autoRetestSettings.useCustomSlippage()) {
            element.setAttribute("slippage", "" + autoRetestSettings.getSlippage());
        }
        if (autoRetestSettings.useCustomMinDistance()) {
            element.setAttribute("minDist", "" + autoRetestSettings.getMinDistance());
        }
        if (autoRetestSettings.useCustomSpread()) {
            element2.setAttribute("spread", "" + autoRetestSettings.getSpread());
        }
        ArrayList<AutoRetestSettings.Subchart> arrayList = autoRetestSettings.getSubcharts();
        int n = Math.min(list.size(), arrayList.size() + 1);
        for (int i = 1; i < n; ++i) {
            Element element3 = (Element)list.get(i);
            AutoRetestSettings.Subchart subchart = arrayList.get(i - 1);
            element3.setAttribute("symbol", subchart.symbol);
            element3.setAttribute("timeframe", subchart.timeframe);
            element3.setAttribute("spread", "" + autoRetestSettings.getSpread());
        }
        if (autoRetestSettings.useCustomCommissions()) {
            element.removeChild("Commissions");
            Element element4 = autoRetestSettings.getCommissions().getXML();
            element.addContent((Content)element4);
        }
        if (autoRetestSettings.useCustomSwap()) {
            element.removeChild("Swap");
            Element element5 = autoRetestSettings.getSwap().getXML();
            element.addContent((Content)element5);
        }
    }

    private static void modifyAdditionalMarketsSettings(Element element, Element element2) {
        if (!XMLUtil.elementIs((Element)element, (String)"use")) {
            return;
        }
        try {
            Element element3 = XMLUtil.getChildElem((Element)element, (String)"Settings");
            Element element4 = XMLUtil.getChildElem((Element)element3, (String)"Setups");
            List list = element4.getChildren("Setup");
            Element element5 = XMLUtil.getChildElem((Element)XMLUtil.getChildElem((Element)element2, (String)"Setups"), (String)"Setup");
            Element element6 = XMLUtil.getChildElem((Element)element5, (String)"Chart");
            for (int i = 0; i < list.size(); ++i) {
                try {
                    Element element7 = (Element)list.get(i);
                    Element element8 = XMLUtil.getChildElem((Element)element7, (String)"MainTestValues");
                    List list2 = element7.getChildren("Chart");
                    if (XMLUtil.elementIs((Element)element8, (String)"dates")) {
                        element7.setAttribute("dateFrom", element5.getAttributeValue("dateFrom"));
                        element7.setAttribute("dateTo", element5.getAttributeValue("dateTo"));
                    }
                    if (XMLUtil.elementIs((Element)element8, (String)"precision")) {
                        element7.setAttribute("testPrecision", element5.getAttributeValue("testPrecision"));
                    }
                    if (XMLUtil.elementIs((Element)element8, (String)"distance")) {
                        element7.setAttribute("minDist", element5.getAttributeValue("minDist"));
                    }
                    if (XMLUtil.elementIs((Element)element8, (String)"slippage")) {
                        element7.setAttribute("slippage", element5.getAttributeValue("slippage"));
                    }
                    if (XMLUtil.elementIs((Element)element8, (String)"session")) {
                        element7.setAttribute("session", element5.getAttributeValue("session"));
                    }
                    if (XMLUtil.elementIs((Element)element8, (String)"commissions")) {
                        element7.removeChild("Commissions");
                        element7.addContent((Content)element5.getChild("Commissions").clone());
                    }
                    for (int j = 0; j < list2.size(); ++j) {
                        Element element9 = (Element)list2.get(j);
                        String string = element9.getAttributeValue("symbol");
                        if (XMLUtil.elementIs((Element)element8, (String)"timeframe")) {
                            DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)string);
                            String string2 = dataInfo.timeframe;
                            String string3 = element6.getAttributeValue("timeframe");
                            if (TimeframeManager.getMillis((String)string2) <= TimeframeManager.getMillis((String)string3)) {
                                element9.setAttribute("timeframe", string3);
                            }
                        }
                        if (!XMLUtil.elementIs((Element)element8, (String)"spread")) continue;
                        element9.setAttribute("spread", element6.getAttributeValue("spread"));
                    }
                    continue;
                }
                catch (Exception exception) {
                    Log.error("Preparing RetestOnAdditionalMarkets setup #" + (i + 1) + " failed", (Throwable)exception);
                }
            }
        }
        catch (Exception exception) {
            Log.error("Preparing RetestOnAdditionalMarkets cross check settings failed", (Throwable)exception);
        }
    }
}


/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.basket.BasketDto
 *  com.strategyquant.datalib.basket.BasketOfStocksManager
 *  com.strategyquant.datalib.basket.StockDto
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Task.impl.AutomaticRetest;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.basket.StockDto;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class XmlChartCombinator {
    public static final Logger Log = LoggerFactory.getLogger(XmlChartCombinator.class);

    private List<Variation> getVariations(String symbol, String timeframe) {
        LinkedList<Variation> result = new LinkedList<Variation>();
        String[] symbols = symbol.split(",");
        String[] timeframes = timeframe.split(",");
        for (String iSymbol : symbols = this.transformStockGroups(symbols)) {
            if (!(iSymbol = iSymbol.trim()).equals("") && DataManager.getDataInfo((String)"History", (String)iSymbol) == null) {
                throw new RuntimeException(L.t((String)"Symbol not found", (Object[])new Object[0]) + " " + iSymbol);
            }
            for (String iTimeframe : timeframes) {
                iTimeframe = iTimeframe.trim();
                result.add(new Variation(iSymbol, iTimeframe));
            }
        }
        return result;
    }

    private String[] transformStockGroups(String[] symbols) {
        HashSet<String> stocks = new HashSet<String>();
        for (String iSymbol : symbols) {
            if ((iSymbol = iSymbol.trim()).startsWith("[")) {
                BasketDto stockGroup = BasketOfStocksManager.getInstance().getBasket(iSymbol);
                if (stockGroup == null) {
                    throw new RuntimeException(L.t((String)"Unknown stockgroup", (Object[])new Object[0]) + " " + iSymbol);
                }
                List stocksFromGroup = BasketOfStocksManager.getInstance().getStocks(stockGroup.getId().intValue());
                for (StockDto stock : stocksFromGroup) {
                    DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)stock.getTicker());
                    if (dataInfo != null && dataInfo.dateFrom > 0L) {
                        stocks.add(stock.getTicker());
                        continue;
                    }
                    Log.debug("Symbol from group {} not found or is without any data", (Object)stock.getTicker());
                }
                continue;
            }
            stocks.add(iSymbol);
        }
        return stocks.toArray(new String[0]);
    }

    private <T> List<List<T>> getCartesian(List<List<T>> lists) {
        ArrayList<List<Object>> result = new ArrayList<List<T>>();
        result.add(new ArrayList());
        for (List<T> list : lists) {
            ArrayList next = new ArrayList();
            for (List list2 : result) {
                for (T item : list) {
                    ArrayList<T> extended = new ArrayList<T>(list2);
                    extended.add(item);
                    next.add(extended);
                }
            }
            result = next;
        }
        return result;
    }

    private String getMainSymbol(Element elSettings) {
        if (elSettings == null) {
            return null;
        }
        Element elData = elSettings.getChild("Data");
        if (elData == null) {
            return null;
        }
        Element elSetups = elData.getChild("Setups");
        if (elSetups == null) {
            return null;
        }
        Element elSetup = elSetups.getChild("Setup");
        if (elSetup == null) {
            return null;
        }
        Element elChart = elSetup.getChild("Chart");
        if (elChart == null) {
            return null;
        }
        return elChart.getAttributeValue("symbol");
    }

    public List<Element> getSettingXMLVariations(Element settingsXML, Element lastSettingsXML) throws Exception {
        Element iSettingsOfSymbolTimeframeXML = settingsXML.clone();
        Element elData = iSettingsOfSymbolTimeframeXML.getChild("CustomData");
        Element elSetups = elData.getChild("Setups");
        List setups = elSetups.getChildren("Setup");
        ArrayList<Element> result = new ArrayList<Element>();
        for (int a = 0; a < setups.size(); ++a) {
            Element elSetup = (Element)setups.get(a);
            Element mainTestValues = elSetup.getChild("MainTestValues");
            String symbolFromStrategy = mainTestValues.getAttributeValue("symbol", "false");
            String tfFromStrategy = mainTestValues.getAttributeValue("timeframe", "false");
            List elCharts = elSetup.getChildren("Chart");
            LinkedList perChartVariants = new LinkedList();
            for (int i = 0; i < elCharts.size(); ++i) {
                Element iChart = (Element)elCharts.get(i);
                String symbol = iChart.getAttributeValue("symbol");
                String timeframe = iChart.getAttributeValue("timeframe");
                if (i == 0) {
                    if ("true".equals(symbolFromStrategy)) {
                        symbol = "";
                    }
                    if ("true".equals(tfFromStrategy)) {
                        timeframe = "H1";
                    }
                }
                List<Variation> variations = this.getVariations(symbol, timeframe);
                perChartVariants.add(variations);
            }
            String mainSymbol = null;
            List allCombos = this.getCartesian(perChartVariants);
            for (List combo : allCombos) {
                String mainSymbolFromLastSetting;
                Element newSettings = settingsXML.clone();
                Element elNewData = newSettings.getChild("CustomData");
                Element elNewSetups = elNewData.getChild("Setups");
                Element elNewSetup = elNewSetups.getChild("Setup");
                List newCharts = elNewSetup.getChildren("Chart");
                for (int i = 0; i < newCharts.size(); ++i) {
                    Element ch = (Element)newCharts.get(i);
                    Variation v = (Variation)combo.get(i);
                    ch.setAttribute("symbol", v.symbol);
                    ch.setAttribute("timeframe", v.timeframe);
                    if (i != 0) continue;
                    mainSymbol = v.symbol;
                }
                DataInfo dataInfo = DataManager.getDataInfo((String)"History", mainSymbol);
                if ("".equals(mainSymbol) && (mainSymbolFromLastSetting = this.getMainSymbol(lastSettingsXML)) != null) {
                    dataInfo = DataManager.getDataInfo((String)"History", (String)mainSymbolFromLastSetting);
                }
                if (dataInfo != null) {
                    Element mainTestValuesNew = elNewSetup.getChild("MainTestValues");
                    String distanceMode = mainTestValuesNew.getAttributeValue("distance", "strategy");
                    String spreadMode = mainTestValuesNew.getAttributeValue("spread", "strategy");
                    String commisionMode = mainTestValuesNew.getAttributeValue("commissions", "strategy");
                    String slippageMode = mainTestValuesNew.getAttributeValue("slippage", "strategy");
                    String swapMode = mainTestValuesNew.getAttributeValue("swap", "strategy");
                    InstrumentInfo instrument = dataInfo.symbolInfo;
                    if (distanceMode.equals("instrument")) {
                        elNewSetup.setAttribute("minDist", String.valueOf(instrument.minDistance));
                    }
                    if (slippageMode.equals("instrument")) {
                        elNewSetup.setAttribute("slippage", String.valueOf(instrument.defaultSlippage));
                    }
                    if (spreadMode.equals("instrument")) {
                        ((Element)newCharts.get(0)).setAttribute("spread", String.valueOf(instrument.defaultSpread));
                    }
                    if (commisionMode.equals("instrument")) {
                        Element methodEl = XMLUtil.stringToElement((String)instrument.commissions);
                        Element commisionEl = new Element("Commissions");
                        commisionEl.addContent((Content)methodEl);
                        elNewSetup.removeChild("Commissions");
                        elNewSetup.addContent((Content)commisionEl);
                    }
                    if (swapMode.equals("instrument")) {
                        Element instrumentSwapEl = XMLUtil.stringToElement((String)instrument.swap);
                        elNewSetup.removeChild("Swap");
                        elNewSetup.addContent((Content)instrumentSwapEl);
                    }
                }
                result.add(newSettings);
            }
        }
        return result;
    }

    private static class Variation {
        String symbol;
        String timeframe;

        public Variation(String symbol, String timeframe) {
            this.symbol = symbol;
            this.timeframe = timeframe;
        }
    }
}


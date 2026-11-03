/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.TimeframeManager
 *  com.strategyquant.datalib.instrument.InstrumentManager
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.time.SQTimeOld
 *  com.strategyquant.pluginlib.SQPluginManager
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  com.strategyquant.tradinglib.results.file.MissingInstrumentException
 *  com.strategyquant.tradinglib.strategy.xml.SQ3StrategyConverter
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Loader.impl.SQ3;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.time.SQTimeOld;
import com.strategyquant.plugin.Loader.impl.SQ3.OrderParser;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.results.file.MissingInstrumentException;
import com.strategyquant.tradinglib.strategy.xml.SQ3StrategyConverter;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.util.HashMap;
import java.util.List;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

class SQFileLoaderSQ3Xml {
    public static final Logger Log = LoggerFactory.getLogger((String)"SQFileLoaderSQ3Xml");

    SQFileLoaderSQ3Xml() {
    }

    public void load(ResultsGroup resultsGroup, Element rootNode, boolean exceptionOnMissingInstrument, String missingInstrumentReplacement) throws Exception {
        Element elSQ3Strategy = rootNode.getChild("Strategy");
        Element elSQ4Strategy = null;
        if (elSQ3Strategy != null) {
            if (elSQ3Strategy.getAttributeValue("note") != null) {
                resultsGroup.specialValues().setString(SpecialValues.Note, elSQ3Strategy.getAttributeValue("note"));
            }
            elSQ4Strategy = SQ3StrategyConverter.getInstance().convert(elSQ3Strategy);
        }
        Element testResultsEl = rootNode.getChild("TestResults");
        SettingsMap mainSettings = SQFileLoaderSQ3Xml.parseSettings(testResultsEl);
        String symbol = mainSettings.getString("Symbol").intern();
        String setupName = mainSettings.getString("Symbol") + "-" + TimeframeManager.translateSQ3TFToString((int)mainSettings.getInt("Timeframe")).intern();
        this.buildLastSettingsXml(resultsGroup, mainSettings);
        this.addOrdersAndSetup(resultsGroup, testResultsEl.getChild("Orders"), symbol, setupName, exceptionOnMissingInstrument, missingInstrumentReplacement);
        Element elAdditionalDataResults = testResultsEl.getChild("AdditionalDataResults");
        if (elAdditionalDataResults != null) {
            for (Element elAdResult : elAdditionalDataResults.getChild("AdResults").getChildren()) {
                SettingsMap adSettings = SQFileLoaderSQ3Xml.parseAdSettings(elAdResult);
                symbol = adSettings.getString("Symbol").intern();
                setupName = adSettings.getString("Symbol") + "-" + TimeframeManager.translateSQ3TFToString((int)adSettings.getInt("Timeframe")).intern();
                this.addOrdersAndSetup(resultsGroup, elAdResult.getChild("Orders"), symbol, setupName, exceptionOnMissingInstrument, missingInstrumentReplacement);
            }
        }
        resultsGroup.specialValues().setString(SpecialValues.Symbol, mainSettings.getString("Symbol"));
        SQTimeOld time = (SQTimeOld)mainSettings.get("DateFrom");
        resultsGroup.specialValues().set(SpecialValues.HistoryFrom, (Object)time.getMilis());
        time = (SQTimeOld)mainSettings.get("DateTo");
        resultsGroup.specialValues().set(SpecialValues.HistoryTo, (Object)time.getMilis());
        resultsGroup.specialValues().setString(SpecialValues.Timeframe, TimeframeManager.translateSQ3TFToString((int)mainSettings.getInt("Timeframe")));
        if (elSQ4Strategy != null) {
            resultsGroup.portfolio().addStrategyXml(elSQ4Strategy);
        }
    }

    private void buildLastSettingsXml(ResultsGroup resultsGroup, SettingsMap settings) {
        try {
            ISQTask buildTask = null;
            for (ISQTask task : SQPluginManager.getPlugins(ISQTask.class)) {
                if (!task.getType().equals("Build")) continue;
                buildTask = task;
                break;
            }
            if (buildTask == null) {
                return;
            }
            Element elSettings = buildTask.getDefaultConfig("task_forex.xml").getChild("Settings");
            Element elData = elSettings.getChild("Data");
            Element elSetups = elData.getChild("Setups");
            Element elSetup = elSetups.getChild("Setup");
            Element elChart = elSetup.getChild("Chart");
            elSetup.setAttribute("dateFrom", SQTime.toUIDateString((long)((SQTimeOld)settings.get("DateFrom")).getDateInMs()));
            elSetup.setAttribute("dateTo", SQTime.toUIDateString((long)((SQTimeOld)settings.get("DateTo")).getDateInMs()));
            String testPrecision = settings.get("testPrecision") + "";
            elSetup.setAttribute("testPrecision", testPrecision);
            elSetup.setAttribute("realSpread", (Integer.parseInt(testPrecision) == 4) + "");
            elSetup.setAttribute("slippage", settings.get("slippage") + "");
            elSetup.setAttribute("minDist", settings.get("minDistance") + "");
            elChart.setAttribute("symbol", settings.get("symbol") + "");
            elChart.setAttribute("timeframe", TimeframeManager.translateSQ3TFToString((int)Integer.parseInt(settings.get("timeframe") + "")));
            elChart.setAttribute("spread", settings.get("spread") + "");
            Element elRiskMoneyManagement = elSettings.getChild("RiskMoneyManagement");
            Element elMoneyManagement = elRiskMoneyManagement.getChild("MoneyManagement");
            Element elInitialCapital = elMoneyManagement.getChild("InitialCapital");
            elInitialCapital.setText(settings.get("MoneyManagement.InitialCapital") + "");
            Element elRankings = elSettings.getChild("Rankings");
            Element elMaxStrategies = elRankings.getChild("MaxStrategies");
            elMaxStrategies.setText(settings.get("maxRecordsInDatabank") + "");
            String lastSettings = XMLUtil.elementToString((Element)elSettings);
            resultsGroup.setLastSettings(lastSettings);
        }
        catch (Exception e) {
            Log.error("Cannot load settings of strategy. Exc.", (Throwable)e);
        }
    }

    private void addOrdersAndSetup(ResultsGroup resultsGroup, Element elOrders, String symbol, String setupName, boolean exceptionOnMissingInstrument, String missingInstrumentReplacement) throws Exception {
        if (resultsGroup.hasResult(setupName)) {
            setupName = resultsGroup.generateUniqueResultKeyName(setupName);
        }
        resultsGroup.addSubresult(setupName, new SettingsMap());
        int record = 0;
        OrdersList ordersList = new OrdersList("addOrddersAndSetup");
        HashMap<Integer, String> uniqueSymbolsMap = new HashMap<Integer, String>();
        for (Element elOrder : elOrders.getChildren()) {
            Order order = OrderParser.parse(elOrder, "2.0");
            order.Symbol = symbol;
            order.SetupName = setupName;
            order.Order = record++;
            ordersList.add(order);
        }
        if (ordersList.size() > 0) {
            new Order();
            for (int i = 0; i < ordersList.size(); ++i) {
                Order order = ordersList.get(i);
                if (uniqueSymbolsMap.containsKey(order.Symbol.hashCode())) continue;
                uniqueSymbolsMap.put(order.Symbol.hashCode(), order.Symbol);
            }
            for (String uniqueSymbol : uniqueSymbolsMap.values()) {
                InstrumentInfo ii;
                if (!InstrumentManager.checkInstrumentExists((String)uniqueSymbol)) {
                    if (exceptionOnMissingInstrument) {
                        ii = InstrumentManager.findClosestInstrument((String)uniqueSymbol);
                        if (ii == null) {
                            throw new MissingInstrumentException(uniqueSymbol);
                        }
                    } else {
                        ii = missingInstrumentReplacement == null ? InstrumentManager.findClosestInstrument((String)uniqueSymbol) : InstrumentManager.getInstrumentInfo((String)missingInstrumentReplacement);
                    }
                } else {
                    ii = InstrumentManager.getInstrumentInfo((String)uniqueSymbol);
                }
                resultsGroup.symbols().add(uniqueSymbol, ii.instrument, ii);
            }
            resultsGroup.orders().addAll(ordersList);
        }
        ordersList.clear();
    }

    private static SettingsMap parseAdSettings(Element elAdResult) {
        SettingsMap settings = new SettingsMap();
        settings.set("Symbol", (Object)elAdResult.getChild("symbol").getValue());
        settings.set("Timeframe", (Object)XMLUtil.getInt((Element)elAdResult, (String)"timeframe", (int)1));
        settings.set("DateFrom", (Object)new SQTimeOld(XMLUtil.getLong((Element)elAdResult, (String)"dateFrom", (int)0) * 1000L));
        settings.set("DateTo", (Object)new SQTimeOld(XMLUtil.getLong((Element)elAdResult, (String)"dateTo", (int)0) * 1000L));
        settings.set("MoneyManagement.InitialCapital", (Object)XMLUtil.getDouble((Element)elAdResult, (String)"capitalSize", (double)10000.0));
        settings.set("TestPrecision", (Object)elAdResult.getChild("testPrecision").getValue());
        settings.set("Spread", (Object)elAdResult.getChild("spread").getValue());
        settings.set("Slippage", (Object)elAdResult.getChild("slippage").getValue());
        settings.set("MinDistance", (Object)elAdResult.getChild("minDistance").getValue());
        return settings;
    }

    private static SettingsMap parseSettings(Element testResultsEl) {
        SettingsMap settings = new SettingsMap();
        Element resultsEl = testResultsEl.getChild("Results");
        if (resultsEl == null) {
            return null;
        }
        List list = resultsEl.getChildren();
        for (Element el : list) {
            if (!el.getName().equalsIgnoreCase("SettingsFile")) continue;
            Element settingsEl = el.getChild("Settings");
            SQFileLoaderSQ3Xml.parseParameters(settings, settingsEl);
            settings.set("Symbol", (Object)settingsEl.getChild("symbol").getValue());
            settings.set("Timeframe", (Object)XMLUtil.getInt((Element)settingsEl, (String)"timeframe", (int)1));
            settings.set("DateFrom", (Object)new SQTimeOld(XMLUtil.getLong((Element)settingsEl, (String)"dateFrom", (int)0) * 1000L));
            settings.set("DateTo", (Object)new SQTimeOld(XMLUtil.getLong((Element)settingsEl, (String)"dateTo", (int)0) * 1000L));
            settings.set("MoneyManagement.InitialCapital", (Object)XMLUtil.getDouble((Element)settingsEl, (String)"capitalSize", (double)10000.0));
            break;
        }
        return settings;
    }

    private static void parseParameters(SettingsMap settings, Element settingsEl) {
        for (Element el : settingsEl.getChildren()) {
            String key = el.getName();
            String value = SQFileLoaderSQ3Xml.parseSettingValue(el.getName(), el.getValue());
            if (value == null) continue;
            settings.set(key, (Object)value);
        }
    }

    public static String parseSettingValue(String setting, String value) {
        if (setting.equalsIgnoreCase("CustomConditions")) {
            return null;
        }
        if (setting.equalsIgnoreCase("generationType")) {
            int type = Integer.parseInt(value);
            if (type == 1) {
                value = "GenerationRandom";
            } else if (type == 2) {
                value = "GenerationFromDatabank";
            }
        } else if (setting.equalsIgnoreCase("tradingSides")) {
            int type = Integer.parseInt(value);
            if (type == 1) {
                value = "OnlyLong";
            } else if (type == 2) {
                value = "OnlyShort";
            } else if (type == 3) {
                value = "BothLong&Short";
            }
        } else if (setting.equalsIgnoreCase("selectionType")) {
            int type = Integer.parseInt(value);
            if (type == 0) {
                value = "RouletteWheelSelection";
            } else if (type == 1) {
                value = "SigmaScaling";
            } else if (type == 2) {
                value = "StochasticUniversalSampling";
            } else if (type == 3) {
                value = "Truncationselection";
            }
        } else if (setting.equalsIgnoreCase("dateFrom") || setting.equalsIgnoreCase("dateTo") || setting.equalsIgnoreCase("oosDateFrom") || setting.equalsIgnoreCase("oosDateTo") || setting.equalsIgnoreCase("tradeTimeFrom") || setting.equalsIgnoreCase("tradeTimeTo")) {
            new SQTimeOld();
            value = SQTimeOld.toString((int)Integer.parseInt(value));
        } else if (setting.equalsIgnoreCase("timeframe")) {
            int type = Integer.parseInt(value);
        } else if (setting.equalsIgnoreCase("testingMode")) {
            int type = Integer.parseInt(value);
            if (type == 1000) {
                value = "ModeEvolution";
            } else if (type == 2000) {
                value = "ModeRandom";
            } else if (type == 3000) {
                value = "ModeTest";
            } else if (type == 4000) {
                value = "ModeOptimize";
            }
        } else if (setting.equalsIgnoreCase("testPrecision")) {
            int type = Integer.parseInt(value);
        } else if (setting.equalsIgnoreCase("buildGoal")) {
            int type = Integer.parseInt(value);
            if (type == 1) {
                value = "GoalComplete";
            } else if (type == 3) {
                value = "GoalPartial";
            }
        } else if (setting.equalsIgnoreCase("mmType")) {
            int type = Integer.parseInt(value);
            if (type == 0) {
                value = "Fixed";
            } else if (type == 1) {
                value = "RiskFixedPerc";
            }
        }
        return value;
    }
}


/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TimeframeManager
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  org.apache.commons.lang3.RandomStringUtils
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.TradingOption;
import com.strategyquant.tradinglib.generator.StrategyTemplateGenerator;
import com.strategyquant.tradinglib.moneymanagement.MoneyManagementMethodsList;
import com.strategyquant.tradinglib.options.TradingOptionsList;
import com.strategyquant.tradinglib.propertygrid.IPGParameter;
import com.strategyquant.tradinglib.results.SpecialValues;
import java.io.File;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import org.apache.commons.lang3.RandomStringUtils;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StrategyXMLModifier {
    private static final Logger Log = LoggerFactory.getLogger(StrategyXMLModifier.class);
    private static final DateFormat dateFormat = new SimpleDateFormat("MM/dd/yyyy HH:mm");
    public static final String MM_FROM_STRATEGY = "fromStrategy";

    public static Element getUpdatedStrategyXML(ResultsGroup resultsGroup) {
        return StrategyXMLModifier.getUpdatedStrategyXML(resultsGroup, MM_FROM_STRATEGY, null);
    }

    public static Element getUpdatedStrategyXML(ResultsGroup resultsGroup, String string, String string2) {
        try {
            return StrategyXMLModifier.getUpdatedStrategyXML(resultsGroup, resultsGroup.portfolio().getStrategyXml().clone(), string, resultsGroup.getName(), resultsGroup.getLastSettings(), string2);
        }
        catch (Exception exception) {
            Log.error("Cannot update strategy XML from last settings (2).", (Throwable)exception);
            return null;
        }
    }

    public static Element getUpdatedStrategyXML(ResultsGroup resultsGroup, Element element, String string, String string2, String string3, String string4) {
        try {
            TradingOption tradingOption;
            Object object;
            Element element2;
            StrategyXMLModifier.addOptions(element, string2, string4);
            StrategyXMLModifier.addLastBacktestInfo(resultsGroup, element);
            if (string3 != null) {
                element2 = XMLUtil.stringToElement((String)string3);
                if (element2 != null) {
                    Element element3;
                    try {
                        element.removeChild("TradingOptions");
                        object = element2.getChild("Options").getChild("BuildTradingOptions").clone();
                        object.setName("TradingOptions");
                        element.addContent((Content)object);
                    }
                    catch (Exception exception) {
                        Log.warn("Cannot read trading options from last settings of strategy '{}'", (Object)string2);
                    }
                    try {
                        object = element.getChild("Strategy");
                        object.removeChild("MoneyManagement");
                        element3 = StrategyXMLModifier.getMoneyManagement(element2.getChild("RiskMoneyManagement").getChild("MoneyManagement"), string);
                        object.addContent((Content)element3);
                        StrategyXMLModifier.updateChartSettings(element, element2);
                    }
                    catch (Exception exception) {
                        Log.warn("Cannot read money management from last settings of strategy '{}'", (Object)string2);
                    }
                    try {
                        object = element.getChild("options");
                        element3 = object.getChild("MinDistance");
                        tradingOption = element2.getChild("Data").getChild("Setups").getChild("Setup");
                        double d = Double.parseDouble(tradingOption.getAttributeValue("minDist"));
                        element3.setText("" + d);
                        String string5 = tradingOption.getAttributeValue("engine");
                        Element element4 = object.getChild("BacktestEngine");
                        if (element4 == null) {
                            element4 = new Element("BacktestEngine");
                            object.addContent((Content)element4);
                        }
                        element4.setText(string5);
                    }
                    catch (Exception exception) {
                        Log.warn("Cannot read min distance from last settings of strategy '{}'", (Object)string2);
                    }
                    try {
                        object = element.getChild("ATMs");
                        if (object == null) {
                            object = new Element("ATMs");
                            element.addContent((Content)object);
                        }
                        StrategyXMLModifier.addMandatoryEmptyATM((Element)object);
                    }
                    catch (Exception exception) {
                        Log.warn("Cannot read trading options from last settings of strategy '{}'", (Object)string2);
                    }
                } else {
                    Log.warn("Cannot get last settings of strategy '{}'", (Object)string2);
                    StrategyXMLModifier.createDefaultMMSettings(element, string);
                }
            } else {
                Log.warn("No last settings available for strategy '{}'", (Object)string2);
                StrategyXMLModifier.createDefaultMMSettings(element, string);
            }
            element2 = XMLUtil.tryAddElement((Element)element, (String)"AvailableTradingOptions");
            element2.removeContent();
            object = TradingOptionsList.getInstance().getAvailableClasses();
            for (int i = 0; i < object.size(); ++i) {
                tradingOption = (TradingOption)object.get(i);
                if (tradingOption.isInbuild()) continue;
                element2.addContent((Content)new Element("TradingOption").setText(tradingOption.getClass().getSimpleName()));
            }
        }
        catch (Exception exception) {
            Log.error("Cannot update strategy XML from last settings.", (Throwable)exception);
        }
        return element;
    }

    public static void addMandatoryEmptyATM(Element element) {
        List list = element.getChildren("ATM");
        if (list == null || list.isEmpty()) {
            Element element2 = new Element("ATM");
            element2.setAttribute("empty", "true");
            element.addContent((Content)element2);
            element.addContent((Content)element2.clone());
            element.setAttribute("enable", "false");
        }
    }

    private static void updateChartSettings(Element element, Element element2) {
        try {
            Element element3 = element2.getChild("Data");
            Element element4 = element3.getChild("Setups").getChild("Setup");
            Element element5 = element.getChild("Strategy").getChild("Datas");
            List list = element5.getChildren("data");
            List list2 = element4.getChildren("Chart");
            Element element6 = (Element)list2.get(0);
            String string = element6.getAttributeValue("symbol");
            for (int i = 0; i < list2.size(); ++i) {
                Element element7;
                Element element8;
                Element element9 = (Element)list2.get(i);
                String string2 = element9.getAttributeValue("symbol");
                Element element10 = null;
                if (i < list.size()) {
                    element10 = (Element)list.get(i);
                    element8 = element10.getChild("symbol");
                    element8.setText(i == 0 ? "NULL" : string2);
                    element7 = element10.getChild("timeFrame");
                    element7.setText(i == 0 ? "0" : String.valueOf(TimeframeManager.getMillis((String)element9.getAttributeValue("timeframe")) / 60000L));
                } else {
                    element10 = new Element("data");
                    element8 = new Element("id").setText(String.valueOf(i));
                    element7 = new Element("symbol").setText(i == 0 ? "NULL" : string2);
                    Element element11 = new Element("chart").setText(i == 0 ? "Main chart" : "Subchart " + i);
                    Element element12 = new Element("timeFrame").setText(i == 0 ? "0" : String.valueOf(TimeframeManager.getMillis((String)element9.getAttributeValue("timeframe")) / 60000L));
                    element10.addContent((Content)element8).addContent((Content)element7).addContent((Content)element11).addContent((Content)element12);
                    element5.addContent((Content)element10);
                }
                StrategyTemplateGenerator.addTickSizeToDataElem(element10, string2, string);
            }
        }
        catch (Exception exception) {
            Log.error("Updating data settings failed", (Throwable)exception);
        }
    }

    public static void addOptions(Element element, String string, String string2) {
        Element element2 = element.getChild("options");
        if (element2 != null) {
            Element element3;
            Element element4 = element2.getChild("ID");
            if (element4 == null) {
                element2.addContent((Content)new Element("ID").setText(StrategyXMLModifier.getID()));
            }
            if ((element3 = element2.getChild("MinDistance")) != null) {
                try {
                    Double.parseDouble(element3.getText());
                }
                catch (Exception exception) {
                    element3.setText("0");
                }
            } else {
                element2.addContent((Content)new Element("MinDistance").setText("0"));
            }
            Element element5 = element2.getChild("StrategyName");
            if (element5 == null) {
                element2.addContent((Content)new Element("StrategyName").setText(string));
            } else {
                element5.setText(string);
            }
            Element element6 = element2.getChild("Version");
            if (element6 != null) {
                element6.setText(MainApp.printAppVersion((boolean)false));
            } else {
                try {
                    element2.addContent((Content)new Element("Version").setText(MainApp.printAppVersion((boolean)false)));
                }
                catch (Exception exception) {
                    element2.addContent((Content)new Element("Version").setText("N/A"));
                }
            }
            Element element7 = element2.getChild("Date");
            Date date = new Date();
            if (element7 != null) {
                element7.setText(dateFormat.format(date));
            } else {
                try {
                    element2.addContent((Content)new Element("Date").setText(dateFormat.format(date)));
                }
                catch (Exception exception) {
                    element2.addContent((Content)new Element("Date").setText("N/A"));
                }
            }
            return;
        }
        element2 = new Element("options");
        element.addContent(0, (Content)element2);
        element2.addContent((Content)new Element("StrategyName").setText(string));
        try {
            element2.addContent((Content)new Element("StrategyClassName").setText(SQUtils.correctClassName((String)SQUtils.stripExtension((String)new File(string2).getName()))));
        }
        catch (Exception exception) {
            element2.addContent((Content)new Element("StrategyClassName").setText(SQUtils.correctClassName((String)string)));
        }
        String string3 = element.getChild("Strategy").getAttributeValue("engine");
        element2.addContent((Content)new Element("Engine").setText(string3));
        element2.addContent((Content)new Element("OnlineVersion").setText("false"));
        try {
            element2.addContent((Content)new Element("Version").setText(MainApp.printAppVersion((boolean)false)));
        }
        catch (Exception exception) {
            element2.addContent((Content)new Element("Version").setText("N/A"));
        }
        Date date = new Date();
        element2.addContent((Content)new Element("Date").setText(dateFormat.format(date)));
        element2.addContent((Content)new Element("ID").setText(StrategyXMLModifier.getID()));
        element2.addContent((Content)new Element("MinDistance").setText("0"));
    }

    private static String getID() {
        return RandomStringUtils.randomAlphabetic((int)8);
    }

    private static void addLastBacktestInfo(ResultsGroup resultsGroup, Element element) {
        if (resultsGroup != null && resultsGroup.specialValues() != null) {
            long l = resultsGroup.specialValues().getLong(SpecialValues.HistoryFrom, 0L);
            long l2 = resultsGroup.specialValues().getLong(SpecialValues.HistoryTo, 0L);
            String string = null;
            try {
                string = resultsGroup.mainResult().getString(SpecialValues.Symbol, null);
            }
            catch (Exception exception) {
                // empty catch block
            }
            String string2 = null;
            try {
                string2 = resultsGroup.mainResult().getString(SpecialValues.Timeframe, null);
            }
            catch (Exception exception) {
                // empty catch block
            }
            Element element2 = element.getChild("options");
            if (element2 != null) {
                Element element3 = element2.getChild("Backtest");
                if (element3 == null) {
                    element3 = new Element("Backtest");
                    element2.addContent((Content)element3);
                }
                element3.removeContent();
                XMLUtil.tryAddNode((Element)element3, (String)"DateFrom", (String)(l > 0L ? SQTime.formatDate((long)l) : "??"));
                XMLUtil.tryAddNode((Element)element3, (String)"DateTo", (String)(l2 > 0L ? SQTime.formatDate((long)l2) : "??"));
                XMLUtil.tryAddNode((Element)element3, (String)"Symbol", (String)(string != null ? string : "??"));
                XMLUtil.tryAddNode((Element)element3, (String)"Timeframe", (String)(string2 != null ? string2 : "??"));
            }
        }
    }

    private static Element getMoneyManagement(Element element, String string) throws Exception {
        Object object;
        Element element2 = element.clone();
        element2.removeContent();
        Element element3 = new Element("Method");
        element2.addContent((Content)element3);
        Element element4 = new Element("Params");
        element3.addContent((Content)element4);
        if (string.equals(MM_FROM_STRATEGY)) {
            object = element.getChildren("Method");
            if (object.size() == 1) {
                element2.setAttribute("type", StrategyXMLModifier.addMMParams(element4, (Element)object.get(0)));
            } else {
                for (int i = 0; i < object.size(); ++i) {
                    Element element5 = (Element)object.get(i);
                    if (!XMLUtil.elementIs((Element)element5, (String)"use")) continue;
                    element2.setAttribute("type", StrategyXMLModifier.addMMParams(element4, element5));
                    break;
                }
            }
        } else {
            element2.setAttribute("type", StrategyXMLModifier.addMMParams(element4, string));
        }
        object = element.getChildText("InitialCapital");
        object = object != null ? object : "10000";
        Element element6 = new Element("InitialCapital");
        element6.setText((String)object);
        element2.addContent((Content)element6);
        return element2;
    }

    private static void createDefaultMMSettings(Element element, String string) throws Exception {
        if (string.equals(MM_FROM_STRATEGY)) {
            if (StrategyXMLModifier.hasValidMMSettings(element)) {
                return;
            }
            string = "FixedSize";
        }
        Element element2 = element.getChild("Strategy");
        element2.removeChild("MoneyManagement");
        Element element3 = new Element("MoneyManagement");
        element3.setAttribute("type", string);
        Element element4 = new Element("InitialCapital");
        element4.setText("10000");
        element3.addContent((Content)element4);
        Element element5 = new Element("Method");
        element5.setAttribute("type", string);
        element5.setAttribute("use", "true");
        Element element6 = new Element("Params");
        StrategyXMLModifier.addMMParams(element6, string);
        element5.addContent((Content)element6);
        element3.addContent((Content)element5);
        element2.addContent((Content)element3);
    }

    private static boolean hasValidMMSettings(Element element) {
        try {
            Element element2 = element.getChild("Strategy");
            Element element3 = element2.getChild("MoneyManagement");
            Element element4 = element3.getChild("Method");
            Element element5 = element4.getChild("Params");
            if (element5 != null) {
                return true;
            }
        }
        catch (Exception exception) {
            Log.error("Strategy contains invalid MM settings", (Throwable)exception);
        }
        return false;
    }

    private static String addMMParams(Element element, String string) throws Exception {
        MoneyManagementMethod moneyManagementMethod = (MoneyManagementMethod)MoneyManagementMethodsList.get().findClassByName(string);
        StrategyXMLModifier.addMMParams(element, moneyManagementMethod);
        return moneyManagementMethod.getClass().getSimpleName();
    }

    private static String addMMParams(Element element, Element element2) throws Exception {
        MoneyManagementMethod moneyManagementMethod = null;
        try {
            moneyManagementMethod = MoneyManagementMethodsList.createFromXml(element2);
            StrategyXMLModifier.addMMParams(element, moneyManagementMethod);
        }
        catch (Exception exception) {
            Log.error("Incorrect MoneyManagement settings, using FixedSize...");
            moneyManagementMethod = (MoneyManagementMethod)MoneyManagementMethodsList.get().findClassByName("FixedSize");
            StrategyXMLModifier.addMMParams(element, moneyManagementMethod);
        }
        return moneyManagementMethod != null ? moneyManagementMethod.getClass().getSimpleName() : null;
    }

    public static void addMMParams(Element element, MoneyManagementMethod moneyManagementMethod) throws Exception {
        Element element2 = moneyManagementMethod.getXML().getChild("Method");
        List list = element2.getChild("Params").getChildren("Param");
        for (Element element3 : list) {
            String string = element3.getAttributeValue("key");
            boolean bl = false;
            for (IPGParameter iPGParameter : moneyManagementMethod.getParams()) {
                if (!iPGParameter.getKey().equals(string)) continue;
                String string2 = String.valueOf(moneyManagementMethod.getPGParameterValue(string));
                Element element4 = new Element("Param");
                element4.setAttribute("key", "#" + string + "#");
                element4.setAttribute("varname", "null");
                element4.setAttribute("type", StrategyXMLModifier.printMMParamType(iPGParameter.getType()));
                element4.setAttribute("value", string2);
                element4.setText(string2);
                element.addContent((Content)element4);
                bl = true;
                break;
            }
            if (bl) continue;
            Log.error("PG Parameter '" + string + "' not found");
        }
    }

    private static String printMMParamType(int n) {
        switch (n) {
            case 1: {
                return "int";
            }
            case 2: {
                return "double";
            }
            case 3: {
                return "boolean";
            }
            case 30: {
                return "string";
            }
            case 4: {
                return "int";
            }
            case 5: {
                return "string";
            }
            case 20: {
                return "int";
            }
            case 10: {
                return "int";
            }
        }
        return "string";
    }
}


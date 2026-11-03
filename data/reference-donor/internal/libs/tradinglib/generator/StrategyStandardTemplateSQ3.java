/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.jdom2.JDOMException
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.generator;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.generator.IStrategyTemplate;
import com.strategyquant.tradinglib.generator.StrategyTemplateGenerator;
import java.io.File;
import java.io.IOException;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StrategyStandardTemplateSQ3
implements IStrategyTemplate {
    public static final Logger Log = LoggerFactory.getLogger((String)"StrategyStandardTemplateSQ3");
    protected static final String MN_NAME = "MagicNumber";
    protected static final String MN_LONG_NAME = "MagicLong";
    protected static final String MN_SHORT_NAME = "MagicShort";
    protected static final String MN_LONG_ID = "11111111-1111-1111-1111-111111111111";
    protected static final String MN_SHORT_ID = "22222222-2222-2222-2222-222222222222";
    protected Element elSettings;
    protected Element elWhatToBuild;
    protected IRandomGenerator rng;
    protected boolean entrySymmetry;
    protected boolean exitSymmetry;
    protected String marketSides;
    protected boolean containsExitRule;
    protected boolean useSameIdForLongShort;
    protected List<Element> elCharts;
    protected String strategyType;
    protected Element elBlocks;
    protected boolean replacePendingOrders = false;
    protected static final int KeepExisting = 0;
    protected static final int Replace = 1;
    protected static final int Add = 2;
    protected static final int AddOrReplace = 2;
    protected static final int UnknownRule = 0;
    protected static final int LongEntry = 1;
    protected static final int ShortEntry = 2;
    protected static final int LongExit = 3;
    protected static final int ShortExit = 4;
    protected int entryLongImprovement;
    protected int entryShortImprovement;
    protected int orderLongImprovement;
    protected int orderShortImprovement;
    protected int exitLongImprovement;
    protected int exitShortImprovement;
    protected String longMagicNumberValue = "";
    protected String shortMagicNumberValue = "";

    public StrategyStandardTemplateSQ3(Element element, IRandomGenerator iRandomGenerator) {
        Element element2;
        Element element3;
        this.rng = iRandomGenerator;
        this.elSettings = element;
        this.elBlocks = element.getChild("Blocks");
        this.elWhatToBuild = element.getChild("WhatToBuild");
        Element element4 = this.elWhatToBuild.getChild("MarketSides");
        this.marketSides = element4.getAttributeValue("type");
        this.entrySymmetry = false;
        this.exitSymmetry = false;
        if (this.marketSides.equals("both")) {
            this.entrySymmetry = Boolean.parseBoolean(element4.getChildText("EntrySymmetry"));
            this.exitSymmetry = Boolean.parseBoolean(element4.getChildText("ExitSymmetry"));
        }
        this.strategyType = this.elWhatToBuild.getChild("StrategyType").getAttributeValue("type");
        this.useSameIdForLongShort = true;
        this.containsExitRule = this.checkContainsExitRule(this.elBlocks);
        Element element5 = element.getChild("Options");
        if (element5 != null && (element3 = element5.getChild("BuildTradingOptions")) != null && (element2 = XMLUtil.getOptionParameter((Element)element3, (String)"ReplacePendingOrders")) != null) {
            this.replacePendingOrders = Boolean.parseBoolean(element2.getText());
        }
        this.elCharts = ((Element)element.getChild("Data").getChild("Setups").getChildren("Setup").get(0)).getChildren("Chart");
    }

    @Override
    public Element generate() throws Exception {
        Element element = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq3/template.xml"));
        this.addEntryRules(element);
        this.addExitRules(element);
        this.addDatas(element);
        this.addVariables(element);
        return element;
    }

    protected void addVariables(Element element) {
        Element element2 = element.getChild("Strategy").getChild("Variables");
        if (this.useSameIdForLongShort) {
            this.createVariable(element2, MN_LONG_ID, MN_NAME, 11111);
        } else {
            this.createVariable(element2, MN_LONG_ID, MN_LONG_NAME, 11111);
            this.createVariable(element2, MN_SHORT_ID, MN_SHORT_NAME, 22222);
        }
    }

    protected void createVariable(Element element, String string, String string2, int n) {
        Element element2 = new Element("variable");
        element2.addContent((Content)new Element("id").addContent(string));
        element2.addContent((Content)new Element("name").addContent(string2));
        element2.addContent((Content)new Element("type").addContent("int"));
        element2.addContent((Content)new Element("value").addContent(Integer.toString(n)));
        element2.addContent((Content)new Element("makeExternal").addContent("true"));
        element.addContent((Content)element2);
    }

    protected void addDatas(Element element) {
        Element element2 = element.getChild("Strategy").getChild("Datas");
        String string = null;
        for (int i = 0; i < this.elCharts.size(); ++i) {
            Element element3 = this.elCharts.get(i);
            Element element4 = new Element("data");
            element4.addContent((Content)new Element("id").setText(Integer.toString(i)));
            if (i == 0) {
                element4.addContent((Content)new Element("chart").setText("Main chart"));
                string = element3.getAttributeValue("symbol");
                element4.addContent((Content)new Element("symbol").setText("NULL"));
                element4.addContent((Content)new Element("timeFrame").setText("0"));
                StrategyTemplateGenerator.addTickSizeToDataElem(element4, string, string);
            } else {
                element4.addContent((Content)new Element("chart").setText(String.format("Subchart %d", i)));
                String string2 = string;
                if (element3.getAttributeValue("symbol").equals(string)) {
                    element4.addContent((Content)new Element("symbol").setText("NULL"));
                } else {
                    string2 = element3.getAttributeValue("symbol");
                    element4.addContent((Content)new Element("symbol").setText(string2));
                }
                element4.addContent((Content)new Element("timeFrame").setText(StrategyStandardTemplateSQ3.convertTimeframeToWizard(element3.getAttributeValue("timeframe"))));
                StrategyTemplateGenerator.addTickSizeToDataElem(element4, string2, string);
            }
            element2.addContent((Content)element4);
        }
    }

    public static String convertTimeframeToWizard(String string) {
        switch (string) {
            case "M1": {
                return "1";
            }
            case "M5": {
                return "5";
            }
            case "M15": {
                return "15";
            }
            case "M30": {
                return "30";
            }
            case "H1": {
                return "60";
            }
            case "H4": {
                return "240";
            }
            case "D1": {
                return "1440";
            }
            case "Weekly": {
                return "10080";
            }
            case "Monthly": {
                return "43200";
            }
        }
        return "0";
    }

    private void addEntryRules(Element element) throws Exception {
        Element element2;
        Element element3;
        if (this.marketSides.equals("both") || this.marketSides.equals("long")) {
            element3 = this.createEntryRule("Long entry", "RandomConditionLong", null, false, 1);
            element2 = this.createRandomAction(element3.getChild("Then").getChild("Item"), "RandomActionLong", 1, null, false, false);
            element3.getChild("Then").addContent((Content)element2.detach());
            this.addRule(element, element3, 1);
        }
        if (this.marketSides.equals("short") || this.marketSides.equals("both")) {
            element3 = this.createEntryRule("Short entry", "RandomConditionShort", "RandomConditionLong", this.entrySymmetry, -1);
            element2 = this.createRandomAction(element3.getChild("Then").getChild("Item"), "RandomActionShort", -1, "RandomActionLong", this.entrySymmetry, this.exitSymmetry);
            element3.getChild("Then").addContent((Content)element2.detach());
            this.addRule(element, element3, -1);
        }
    }

    private void addExitRules(Element element) throws Exception {
        if (this.containsExitRule) {
            Element element2;
            if (this.marketSides.equals("both") || this.marketSides.equals("long")) {
                element2 = this.createExitRule("Long exit", "RandomConditionLongExit", 1, null, false);
                this.addRule(element, element2, 1);
            }
            if (this.marketSides.equals("short") || this.marketSides.equals("both")) {
                element2 = this.createExitRule("Short exit", "RandomConditionShortExit", -1, "RandomConditionLongExit", this.exitSymmetry);
                this.addRule(element, element2, -1);
            }
        }
    }

    private Element createExitRule(String string, String string2, int n, String string3, boolean bl) throws Exception {
        Element element = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq3/exitrule.xml"));
        element.setAttribute("name", string);
        this.configureRandomExitCondition(element.getChild("If").getChild("Item"), string2, string3, n, bl);
        Element element2 = (Element)element.getChild("Then").getChild("Item").getChildren("Param").get(1);
        if (!element2.getAttributeValue("key").equals("#Direction#")) {
            throw new Exception("Second parameter in exit action is not direction!");
        }
        element2.addContent(Integer.toString(n));
        Element element3 = (Element)element.getChild("Then").getChild("Item").getChildren("Param").get(2);
        if (!element3.getAttributeValue("key").equals("#MagicNumber#")) {
            throw new Exception("Third parameter in exit action is not MagicNumber!");
        }
        if (n == 1) {
            element3.setText(MN_LONG_ID);
        } else if (this.useSameIdForLongShort) {
            element3.setText(MN_LONG_ID);
        } else {
            element3.setText(MN_SHORT_ID);
        }
        return element;
    }

    protected void configureRandomExitConditionOnly(Element element, String string, String string2, boolean bl) {
        Element element2 = element.getChild("Param");
        if (!bl) {
            element.setAttribute("key", "RandomCondition");
            element.setAttribute("name", "RandomCondition");
            element.setAttribute("display", "RandomCondition(@Chart@#Identification#)");
            element.setAttribute("generated", "random");
            element2.addContent(string);
            element2.setAttribute("ownRandomKey", "true");
        } else {
            element.setAttribute("key", "NegatedCondition");
            element.setAttribute("name", "NegatedCondition");
            element.setAttribute("display", "NegatedCondition(#Identification#)");
            element.setAttribute("generated", "negated");
            element2.addContent(string2);
        }
    }

    protected void configureRandomExitCondition(Element element, String string, String string2, int n, boolean bl) throws Exception {
        Element element2;
        Element element3 = ((Element)element.getChildren("Block").get(0)).getChild("Item");
        if (n == 1) {
            element3.setAttribute("key", "MarketPositionIsLong");
            element3.setAttribute("name", "Market Position Is Long");
            element3.setAttribute("display", "Market Position(#Symbol#, #MagicNumber#, &amp;quot;#Comment#&amp;quot;) is Long");
            element2 = (Element)element3.getChildren("Param").get(1);
            if (!element2.getAttributeValue("key").equals("#MagicNumber#")) {
                throw new Exception("Missing MagicNumber parameetr!");
            }
            element2.setText(MN_LONG_ID);
        } else {
            element3.setAttribute("key", "MarketPositionIsShort");
            element3.setAttribute("name", "Market Position Is Short");
            element3.setAttribute("display", "Market Position(#Symbol#, #MagicNumber#, &amp;quot;#Comment#&amp;quot;) is Short");
            element2 = (Element)element3.getChildren("Param").get(1);
            if (!element2.getAttributeValue("key").equals("#MagicNumber#")) {
                throw new Exception("Second parameter in exit action is not MagicNumber!");
            }
            if (this.useSameIdForLongShort) {
                element2.setText(MN_LONG_ID);
            } else {
                element2.setText(MN_SHORT_ID);
            }
        }
        element2 = ((Element)element.getChildren("Block").get(1)).getChild("Item");
        this.configureRandomExitConditionOnly(element2, string, string2, bl);
    }

    private Element createEntryRule(String string, String string2, String string3, boolean bl, int n) throws Exception {
        Element element = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq3/entryrule.xml"));
        element.setAttribute("name", string);
        Element element2 = ((Element)element.getChild("If").getChild("Item").getChildren("Block").get(0)).getChild("Item");
        Element element3 = XMLUtil.getItemParameter((Element)element2, (String)"#MagicNumber#", (boolean)true);
        if (n == 1 || this.useSameIdForLongShort) {
            element3.setText(MN_LONG_ID);
        } else {
            element3.setText(MN_SHORT_ID);
        }
        Element element4 = ((Element)element.getChild("If").getChild("Item").getChildren("Block").get(1)).getChild("Item");
        Element element5 = element4.getChild("Param");
        if (!bl) {
            element4.setAttribute("key", "RandomCondition");
            element4.setAttribute("name", "RandomCondition");
            element4.setAttribute("display", "RandomCondition(@Chart@#Identification#)");
            element4.setAttribute("generated", "random");
            element5.addContent(string2);
            element5.setAttribute("ownRandomKey", "true");
        } else {
            element4.setAttribute("key", "NegatedCondition");
            element4.setAttribute("name", "NegatedCondition");
            element4.setAttribute("display", "NegatedCondition(#Identification#)");
            element4.setAttribute("generated", "negated");
            element5.addContent(string3);
        }
        return element;
    }

    protected Element createRandomAction(Element element, String string, int n, String string2, boolean bl, boolean bl2) throws JDOMException, IOException, Exception {
        Element element22;
        Object object;
        Element element3;
        if (!bl && n == 1 || this.marketSides.equals("short")) {
            element3 = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq3/randomaction.xml"));
            object = XMLUtil.getItemParameter((Element)element3, (String)"#Identification#", (boolean)true);
            object.setText(string);
            element22 = XMLUtil.getItemParameter((Element)element3, (String)"#MagicNumber#", (boolean)true);
            if (this.useSameIdForLongShort) {
                element22.setAttribute("defaultValue", MN_NAME);
                element22.setText(MN_LONG_ID);
            } else {
                element22.setAttribute("defaultValue", MN_LONG_NAME);
                element22.setText(MN_LONG_ID);
            }
        } else {
            element3 = bl2 ? XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq3/oppositeaction_exitsymmetry.xml")) : XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq3/oppositeaction_exitunsymmetry.xml"));
            if (n == -1 && bl && bl2) {
                object = XMLUtil.getItemParameter((Element)element3, (String)"#Identification#", (boolean)true);
                object.setText(string2);
                element3.setAttribute("key", "OppositeAction");
                element3.setAttribute("name", "OppositeAction");
                element3.setAttribute("display", "OppositeAction(#Identification#)");
                element3.setAttribute("generate", "opposite");
            } else {
                object = XMLUtil.getItemParameter((Element)element3, (String)"#Identification#", (boolean)true);
                object.setText(string);
            }
            for (Element element22 : element3.getChildren("Param")) {
                String string3 = element22.getAttributeValue("generate");
                if (string3 == null || !string3.equals("opposite")) continue;
                element22.setAttribute("identification", string2);
            }
            object = XMLUtil.getItemParameter((Element)element3, (String)"#MagicNumber#", (boolean)true);
            if (this.useSameIdForLongShort) {
                object.setAttribute("defaultValue", MN_NAME);
                object.setText(MN_LONG_ID);
            } else {
                object.setAttribute("defaultValue", MN_SHORT_NAME);
                object.setText(MN_SHORT_ID);
            }
        }
        if (n == -1 && !bl && (object = XMLUtil.getItemParameter((Element)element3, (String)"#Price#", (boolean)false)) != null) {
            object.setAttribute("generate", "random");
            object.setAttribute("identification", string);
        }
        object = XMLUtil.getItemParameter((Element)element3, (String)"#Direction#", (boolean)true);
        object.setText(Integer.toString(n));
        if (this.replacePendingOrders) {
            element22 = XMLUtil.getItemParameter((Element)element3, (String)"#ReplaceExisting#", (boolean)true);
            element22.setText("true");
        }
        return element3;
    }

    private void addRule(Element element, Element element2, int n) {
        Element element3 = (Element)element.getChild("Strategy").getChild("Rules").getChild("Events").getChildren("Event").get(1);
        try {
            Element element4 = XMLUtil.getItemParameter((Element)element2, (String)"#Direction#", (boolean)false);
            if (element4 != null) {
                element4.setText(Integer.toString(n));
            }
        }
        catch (Exception exception) {
            // empty catch block
        }
        element2.detach();
        element3.addContent((Content)element2);
    }

    private boolean checkContainsExitRule(Element element) {
        Element element2 = element.getChild("ExitTypes");
        for (Element element3 : element2.getChildren()) {
            if (!element3.getAttributeValue("key").equals("_ExitRule_")) continue;
            return true;
        }
        return false;
    }

    @Override
    public void setUseSameIdForLongShort(boolean bl) {
        this.useSameIdForLongShort = bl;
    }

    protected Element getImproverThen(Element element, int n) throws Exception {
        int n2;
        int n3;
        switch (n) {
            case 1: {
                n3 = this.orderLongImprovement;
                n2 = this.exitLongImprovement;
                break;
            }
            case 2: {
                n3 = this.orderShortImprovement;
                n2 = this.exitShortImprovement;
                break;
            }
            default: {
                n3 = 0;
                n2 = 0;
            }
        }
        if (n3 == 0 && n2 == 0) {
            return element.getChild("Then").detach();
        }
        Element element2 = this.getStandardActionChild(element.getChild("Then"));
        if (element2 == null) {
            Element element3 = new Element("Then");
            return element3;
        }
        this.getCurrentMagicNumberSetting(element2, n);
        Element element4 = this.getImproverActionElement(n3, element2, n);
        this.addPriceParameter(element4, element2, n3, n);
        Element element5 = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq3/randomaction.xml"));
        List list = element5.getChildren("Param");
        for (int i = 0; i < list.size(); ++i) {
            Element element6;
            Element element7 = (Element)list.get(i);
            String string = element7.getAttributeValue("key");
            if (string.equals("#Identification#") || string.equals("#Price#")) continue;
            boolean bl = string.contains(".");
            if (!bl || n2 == 0) {
                element6 = XMLUtil.getItemParameter((Element)element2, (String)string, (boolean)false);
                if (element6 != null) {
                    element4.addContent((Content)element6.clone());
                    continue;
                }
                if (n == 1 || !this.exitSymmetry) {
                    element7.setAttribute("generate", "random");
                    element4.addContent((Content)element7.clone());
                    continue;
                }
                element7.setAttribute("generate", "opposite");
                element7.setAttribute("identification", "RandomActionLong");
                element4.addContent((Content)element7.clone());
                continue;
            }
            element6 = XMLUtil.getItemParameter((Element)element2, (String)string, (boolean)false);
            if (element6 == null) continue;
            boolean bl2 = this.isUsedParameter(element6);
            if (n2 == 1 && !bl2) {
                element4.addContent((Content)element6.clone());
                continue;
            }
            if (n2 == 2 && bl2) {
                element4.addContent((Content)element6.clone());
                continue;
            }
            if (n == 1 || !this.exitSymmetry) {
                element7.setAttribute("generate", "random");
                element4.addContent((Content)element7.clone());
                continue;
            }
            element7.setAttribute("generate", "opposite");
            element7.setAttribute("identification", "RandomActionLong");
            element4.addContent((Content)element7.clone());
        }
        Element element8 = new Element("Then");
        element8.addContent((Content)element4);
        return element8;
    }

    protected boolean isUsedParameter(Element element) throws Exception {
        Element element2 = element.getChild("Formula");
        if (element2 != null) {
            String string = element2.getAttributeValue("key");
            if (string.contains(".None")) {
                return false;
            }
        } else {
            String string = element.getText();
            String string2 = element.getAttributeValue("defaultValue");
            if (string2 != null && string2.equals(string)) {
                return false;
            }
        }
        return true;
    }

    private void addPriceParameter(Element element, Element element2, int n, int n2) throws Exception {
        Element element3;
        if (n == 0 && (element3 = XMLUtil.getItemParameter((Element)element2, (String)"#Price#", (boolean)false)) != null) {
            element.addContent((Content)element3.clone());
            return;
        }
        element3 = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq3/entry_priceparam.xml"));
        if (n2 == 1 || !this.entrySymmetry) {
            element3.setAttribute("generate", "random");
        } else {
            element3.setAttribute("generate", "opposite");
        }
        element.addContent((Content)element3.detach());
    }

    private Element getImproverActionElement(int n, Element element, int n2) {
        Element element2;
        if (n == 0) {
            element2 = element.clone();
            element2.removeContent();
            this.addIdentificationParameter(element2, "randomId", n2 == 1 ? "RandomActionLong" : "RandomActionShort");
        } else {
            element2 = new Element("Item");
            if (n2 == 1 || !this.entrySymmetry) {
                element2.setAttribute("key", "RandomAction");
                element2.setAttribute("name", "RandomAction");
                element2.setAttribute("returnType", "none");
                element2.setAttribute("display", "RandomAction(#Identification#)");
                element2.setAttribute("generate", "random");
                element2.setAttribute("superType", "action");
                element2.setAttribute("categoryType", "randomBlock");
                this.addIdentificationParameter(element2, "randomId", n2 == 1 ? "RandomActionLong" : "RandomActionShort");
            } else {
                element2.setAttribute("key", "OppositeAction");
                element2.setAttribute("name", "OppositeAction");
                element2.setAttribute("returnType", "none");
                element2.setAttribute("display", "OppositeAction(#Identification#)");
                element2.setAttribute("generate", "opposite");
                element2.setAttribute("superType", "action");
                element2.setAttribute("categoryType", "randomBlock");
                this.addIdentificationParameter(element2, "randomIdCombo", "RandomActionLong");
            }
        }
        return element2;
    }

    protected void addIdentificationParameter(Element element, String string, String string2) {
        Element element2 = new Element("Param");
        element2.setAttribute("key", "#Identification#");
        element2.setAttribute("name", "Identification");
        element2.setAttribute("type", "string");
        element2.setAttribute("controlType", string);
        if (string.equals("randomId")) {
            element2.setAttribute("ownRandomKey", "true");
        }
        element2.addContent(string2);
        element.addContent((Content)element2);
    }

    private void getCurrentMagicNumberSetting(Element element, int n) throws Exception {
        Element element2 = XMLUtil.getItemParameter((Element)element, (String)"#MagicNumber#", (boolean)false);
        if (element2 != null) {
            if (n == 1) {
                this.longMagicNumberValue = element2.getText();
            } else {
                this.shortMagicNumberValue = element2.getText();
            }
        }
    }

    protected Element getStandardActionChild(Element element) throws Exception {
        List list = element.getChildren();
        if (list.size() == 0) {
            return null;
        }
        if (list.size() > 1) {
            throw new Exception("Strategy doesn't have standard format - THEN part contains more than one action!");
        }
        Element element2 = (Element)list.get(0);
        String string = element2.getAttributeValue("returnType");
        if (!(string != null && string.equals("order") || this.checkIsOpenOrderAction(element2))) {
            throw new Exception("Strategy doesn't have standard format - THEN action is not an order!");
        }
        return element2.clone();
    }

    private boolean checkIsOpenOrderAction(Element element) {
        String string = element.getAttributeValue("key");
        return string.startsWith("EnterAt") || string.startsWith("EnterReverseAt");
    }
}


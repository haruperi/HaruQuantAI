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
import java.io.File;
import java.io.IOException;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StrategyStockpickerTemplate
implements IStrategyTemplate {
    public static final Logger Log = LoggerFactory.getLogger((String)"StrategyStockpickerTemplate");
    public static final String SGN_LONG_ENTRY_ID = "33333333-1111-1111-3333-333333333333";
    public static final String SGN_LONG_ENTRY_NAME = "LongEntrySignal";
    public static final String SGN_LONG_EXIT_ID = "33333333-1111-2222-3333-333333333333";
    public static final String SGN_LONG_EXIT_NAME = "LongExitSignal";
    public static final String SGN_SHORT_ENTRY_ID = "33333333-2222-1111-3333-333333333333";
    public static final String SGN_SHORT_ENTRY_NAME = "ShortEntrySignal";
    public static final String SGN_SHORT_EXIT_ID = "33333333-2222-2222-3333-333333333333";
    public static final String SGN_SHORT_EXIT_NAME = "ShortExitSignal";
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
    protected int probabilityExitRule;
    protected int probabilityEODRule;

    public StrategyStockpickerTemplate(Element element, IRandomGenerator iRandomGenerator) {
        this.rng = iRandomGenerator;
        this.elSettings = element;
        this.elBlocks = element.getChild("Blocks");
        this.elWhatToBuild = element.getChild("WhatToBuild");
        Element element2 = this.elWhatToBuild.getChild("MarketSides");
        this.marketSides = element2.getAttributeValue("type");
        this.entrySymmetry = false;
        this.exitSymmetry = false;
        if (this.marketSides.equals("both")) {
            this.entrySymmetry = Boolean.parseBoolean(element2.getChildText("EntrySymmetry"));
            this.exitSymmetry = Boolean.parseBoolean(element2.getChildText("ExitSymmetry"));
        }
        this.strategyType = this.elWhatToBuild.getChild("StrategyType").getAttributeValue("type");
        this.useSameIdForLongShort = true;
        this.checkContainsExitEODRules(this.elBlocks);
        this.elCharts = ((Element)element.getChild("Data").getChild("Setups").getChildren("Setup").get(0)).getChildren("Chart");
    }

    @Override
    public Element generate() throws Exception {
        Element element = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sp/template.xml"));
        Element element2 = (Element)element.getChild("Strategy").getChild("Rules").getChild("Events").getChildren("Event").get(1);
        this.addRules(element2);
        this.addVariables(element);
        this.setExitsProbability(element);
        return element;
    }

    protected void addRules(Element element) throws Exception {
        this.addRules(element, "entryexitrule.xml");
        this.addPositionScoreRule(element, "positionscorerulelong.xml");
        this.addPositionScoreRule(element, "positionscoreruleshort.xml");
    }

    private void addPositionScoreRule(Element element, String string) throws JDOMException, IOException, Exception {
        Element element2 = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sp/" + string)).detach();
        element.addContent((Content)element2);
    }

    protected void addRules(Element element, String string) throws JDOMException, IOException, Exception {
        Element element2 = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sp/" + string));
        Element element3 = element2.clone().detach();
        element3.setAttribute("name", "Long");
        element.addContent((Content)element3);
        Element element4 = this.createEntry("RandomConditionLong", null, false, 1);
        element3.addContent((Content)element4);
        Element element5 = this.createOrder("RandomActionLong", null, 1, false, false);
        if (element5 != null) {
            element3.addContent((Content)element5);
        }
        Element[] elementArray = this.createExits("RandomConditionLongExit", null, false, 1);
        for (int i = 0; i < elementArray.length; ++i) {
            element3.addContent((Content)elementArray[i]);
        }
        Element element6 = element2.clone().detach();
        element6.setAttribute("name", "Short");
        element.addContent((Content)element6);
        element4 = this.createEntry("RandomConditionShort", "RandomConditionLong", this.entrySymmetry, -1);
        element6.addContent((Content)element4);
        element5 = this.createOrder("RandomActionShort", "RandomActionLong", -1, this.entrySymmetry, this.exitSymmetry);
        if (element5 != null) {
            element6.addContent((Content)element5);
        }
        elementArray = this.createExits("RandomConditionShortExit", "RandomConditionLongExit", this.entrySymmetry, -1);
        for (int i = 0; i < elementArray.length; ++i) {
            element6.addContent((Content)elementArray[i]);
        }
    }

    private Element createEmptyEntry() {
        Element element = new Element("Entry");
        return element;
    }

    private Element createEntry(String string, String string2, boolean bl, int n) throws Exception {
        if (n == 1 ? !this.marketSides.equals("both") && !this.marketSides.equals("long") : !this.marketSides.equals("short") && !this.marketSides.equals("both")) {
            return this.createEmptyEntry();
        }
        Element element = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sp/entry.xml"));
        Element element2 = element.getChild("Item");
        if (element2 == null) {
            throw new Exception("Cannot find RandomCondition Item for Entry!");
        }
        Element element3 = element2.getChild("Param");
        if (element3 == null) {
            throw new Exception("Cannot find Identification param for Entry!");
        }
        if (!bl) {
            element2.setAttribute("key", "RandomCondition");
            element2.setAttribute("name", "RandomCondition");
            element2.setAttribute("display", "RandomCondition(@Chart@#Identification#)");
            element2.setAttribute("generate", "random");
            element2.setAttribute("generated", "random");
            element3.setText(string);
            element3.setAttribute("ownRandomKey", "true");
        } else {
            element2.setAttribute("key", "NegatedCondition");
            element2.setAttribute("name", "NegatedCondition");
            element2.setAttribute("display", "NegatedCondition(#Identification#)");
            element2.setAttribute("generate", "opposite");
            element2.removeAttribute("generated");
            element3.setAttribute("controlType", "randomIdCombo");
            element3.setText(string2);
        }
        return element.detach();
    }

    private Element createOrder(String string, String string2, int n, boolean bl, boolean bl2) throws Exception {
        Element element4;
        Object object;
        Element element2;
        Element element3;
        if (n == 1 ? !this.marketSides.equals("both") && !this.marketSides.equals("long") : !this.marketSides.equals("short") && !this.marketSides.equals("both")) {
            return null;
        }
        if (!bl && n == 1 || this.marketSides.equals("short")) {
            element3 = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sp/randomaction.xml"));
            element2 = element3.getChild("Item");
            object = XMLUtil.getItemParameter((Element)element2, (String)"#Identification#", (boolean)true);
            object.setText(string);
            element4 = XMLUtil.getItemParameter((Element)element2, (String)"#MagicNumber#", (boolean)true);
            if (this.useSameIdForLongShort) {
                element4.setAttribute("defaultValue", MN_NAME);
                element4.setText(MN_LONG_ID);
            } else {
                element4.setAttribute("defaultValue", MN_LONG_NAME);
                element4.setText(MN_LONG_ID);
            }
        } else {
            element3 = bl2 ? XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sp/oppositeaction_exitsymmetry.xml")) : XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sp/oppositeaction_exitunsymmetry.xml"));
            element2 = element3.getChild("Item");
            if (n == -1 && bl && bl2) {
                object = XMLUtil.getItemParameter((Element)element2, (String)"#Identification#", (boolean)true);
                object.setText(string2);
                element2.setAttribute("key", "OppositeAction");
                element2.setAttribute("name", "OppositeAction");
                element2.setAttribute("display", "OppositeAction(#Identification#)");
                element2.setAttribute("generate", "opposite");
            } else {
                object = XMLUtil.getItemParameter((Element)element2, (String)"#Identification#", (boolean)true);
                object.setText(string);
            }
            for (Element element4 : element2.getChildren("Param")) {
                String string3 = element4.getAttributeValue("generate");
                if (string3 == null || !string3.equals("opposite")) continue;
                element4.setAttribute("identification", string2);
            }
            object = XMLUtil.getItemParameter((Element)element2, (String)"#MagicNumber#", (boolean)true);
            if (this.useSameIdForLongShort) {
                object.setAttribute("defaultValue", MN_NAME);
                object.setText(MN_LONG_ID);
            } else {
                object.setAttribute("defaultValue", MN_SHORT_NAME);
                object.setText(MN_SHORT_ID);
            }
        }
        if (n == -1 && !bl && (object = XMLUtil.getItemParameter((Element)element2, (String)"#Price#", (boolean)false)) != null) {
            object.setAttribute("generate", "random");
            object.setAttribute("identification", string);
        }
        object = XMLUtil.getItemParameter((Element)element2, (String)"#Direction#", (boolean)true);
        object.setText(Integer.toString(n));
        if (this.replacePendingOrders) {
            element4 = XMLUtil.getItemParameter((Element)element2, (String)"#ReplaceExisting#", (boolean)true);
            element4.setText("true");
        }
        return element3.detach();
    }

    private Element[] createExits(String string, String string2, boolean bl, int n) throws Exception {
        Element[] elementArray = new Element[]{this.createExitEOD(), this.createExit(string, string2, bl, n)};
        return elementArray;
    }

    private Element createExitEOD() {
        Element element = new Element("Exit");
        if (this.probabilityEODRule > 0) {
            element.setAttribute("atEndOfDay", "DayClose");
        } else {
            element.setAttribute("atEndOfDay", "None");
        }
        return element;
    }

    private Element createExit(String string, String string2, boolean bl, int n) throws Exception {
        Element element;
        Element element2 = new Element("Exit");
        if (this.probabilityExitRule == 0) {
            return element2;
        }
        if (n == 1 && (this.marketSides.equals("both") || this.marketSides.equals("long"))) {
            element = this.createExitCondition(string, string2, n, false);
            element2.addContent((Content)element);
        }
        if (n == -1 && (this.marketSides.equals("short") || this.marketSides.equals("both"))) {
            element = this.createExitCondition(string, string2, n, this.exitSymmetry);
            element2.addContent((Content)element);
        }
        return element2;
    }

    private Element createExitCondition(String string, String string2, int n, boolean bl) {
        Element element = new Element("Item");
        element.setAttribute("returnType", "boolean");
        element.setAttribute("ignoreInBuilder", "true");
        element.setAttribute("randomTemplate", "true");
        element.setAttribute("superType", "condition");
        Element element2 = new Element("Param");
        element2.setAttribute("key", "#Identification#");
        element2.setAttribute("name", "Identification");
        element2.setAttribute("type", "string");
        element2.setAttribute("controlType", "randomId");
        element2.setAttribute("ownRandomKey", "true");
        element.addContent((Content)element2);
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
        return element;
    }

    @Override
    public void setUseSameIdForLongShort(boolean bl) {
        this.useSameIdForLongShort = bl;
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

    private void checkContainsExitEODRules(Element element) {
        this.probabilityExitRule = 0;
        this.probabilityEODRule = 0;
        Element element2 = element.getChild("ExitTypes");
        for (Element element3 : element2.getChildren()) {
            if (element3.getAttributeValue("key").equals("_ExitRule_") && element3.getAttributeValue("use").equals("true")) {
                this.probabilityExitRule = Integer.parseInt(element3.getAttributeValue("probability"));
            }
            if (!element3.getAttributeValue("key").equals("_ExitEOD_") || !element3.getAttributeValue("use").equals("true")) continue;
            this.probabilityEODRule = Integer.parseInt(element3.getAttributeValue("probability"));
        }
    }

    protected void setExitsProbability(Element element) {
        Element element2 = element.getChild("Strategy");
        element2.setAttribute("probabilityExitRule", Integer.toString(this.probabilityExitRule));
        element2.setAttribute("probabilityEODRule", Integer.toString(this.probabilityEODRule));
    }

    public static void setExitsProbability(Element element, Element element2, IRandomGenerator iRandomGenerator) {
        StrategyStockpickerTemplate strategyStockpickerTemplate = new StrategyStockpickerTemplate(element2, iRandomGenerator);
        strategyStockpickerTemplate.setExitsProbability(element);
    }
}


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
import com.strategyquant.tradinglib.generator.StrategyStandardTemplateSQ3;
import java.io.File;
import java.io.IOException;
import org.jdom2.Content;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StrategyStandardTemplateSQ4
extends StrategyStandardTemplateSQ3 {
    public static final Logger Log = LoggerFactory.getLogger((String)"StrategyStandardTemplateSQ4");
    public static final String SGN_LONG_ENTRY_ID = "33333333-1111-1111-3333-333333333333";
    public static final String SGN_LONG_ENTRY_NAME = "LongEntrySignal";
    public static final String SGN_LONG_EXIT_ID = "33333333-1111-2222-3333-333333333333";
    public static final String SGN_LONG_EXIT_NAME = "LongExitSignal";
    public static final String SGN_SHORT_ENTRY_ID = "33333333-2222-1111-3333-333333333333";
    public static final String SGN_SHORT_ENTRY_NAME = "ShortEntrySignal";
    public static final String SGN_SHORT_EXIT_ID = "33333333-2222-2222-3333-333333333333";
    public static final String SGN_SHORT_EXIT_NAME = "ShortExitSignal";

    public StrategyStandardTemplateSQ4(Element element, IRandomGenerator iRandomGenerator) {
        super(element, iRandomGenerator);
    }

    @Override
    public Element generate() throws Exception {
        Element element = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq4/template.xml"));
        Element element2 = (Element)element.getChild("Strategy").getChild("Rules").getChild("Events").getChildren("Event").get(1);
        this.addRules(element2);
        this.addDatas(element);
        this.addVariables(element);
        return element;
    }

    @Override
    protected void addVariables(Element element) {
        Element element2 = element.getChild("Strategy").getChild("Variables");
        if (this.useSameIdForLongShort) {
            this.createVariable(element2, "11111111-1111-1111-1111-111111111111", "MagicNumber", 11111);
        } else {
            this.createVariable(element2, "11111111-1111-1111-1111-111111111111", "MagicLong", 11111);
            this.createVariable(element2, "22222222-2222-2222-2222-222222222222", "MagicShort", 22222);
        }
        this.createBoolVariable(element2, SGN_LONG_ENTRY_ID, SGN_LONG_ENTRY_NAME, false);
        this.createBoolVariable(element2, SGN_SHORT_ENTRY_ID, SGN_SHORT_ENTRY_NAME, false);
        if (this.containsExitRule) {
            this.createBoolVariable(element2, SGN_LONG_EXIT_ID, SGN_LONG_EXIT_NAME, false);
            this.createBoolVariable(element2, SGN_SHORT_EXIT_ID, SGN_SHORT_EXIT_NAME, false);
        }
    }

    private void createBoolVariable(Element element, String string, String string2, boolean bl) {
        Element element2 = new Element("variable");
        element2.addContent((Content)new Element("id").addContent(string));
        element2.addContent((Content)new Element("name").addContent(string2));
        element2.addContent((Content)new Element("type").addContent("boolean"));
        element2.addContent((Content)new Element("value").addContent(Boolean.toString(bl)));
        element2.addContent((Content)new Element("makeExternal").addContent("false"));
        element.addContent((Content)element2);
    }

    private void addRules(Element element) throws Exception {
        Element element2 = this.getSignalRule();
        element.addContent((Content)element2);
        if (this.containsExitRule) {
            this.addEntryRule(element, "Long entry", "longentryrule.xml", 1);
            this.addEntryRule(element, "Short entry", "shortentryrule.xml", -1);
            this.addExitRule(element, "Long exit", "longexitrule.xml", 1);
            this.addExitRule(element, "Short exit", "shortexitrule.xml", -1);
        } else {
            this.addEntryRule(element, "Long entry", "longentryrulenoexit.xml", 1);
            this.addEntryRule(element, "Short entry", "shortentryrulenoexit.xml", -1);
        }
    }

    private void addEntryRule(Element element, String string, String string2, int n) throws JDOMException, IOException, Exception {
        Element element2 = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq4/" + string2)).detach();
        element2.setAttribute("name", string);
        element.addContent((Content)element2);
        if (n == 1) {
            if (this.marketSides.equals("both") || this.marketSides.equals("long")) {
                Element element3 = this.createRandomAction(element2.getChild("Then").getChild("Item"), "RandomActionLong", 1, null, false, false);
                element2.getChild("Then").addContent((Content)element3.detach());
            }
        } else if (this.marketSides.equals("both") || this.marketSides.equals("short")) {
            Element element4 = this.createRandomAction(element2.getChild("Then").getChild("Item"), "RandomActionShort", -1, "RandomActionLong", this.entrySymmetry, this.exitSymmetry);
            element2.getChild("Then").addContent((Content)element4.detach());
        }
    }

    private void addExitRule(Element element, String string, String string2, int n) throws JDOMException, IOException, Exception {
        Element element2 = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq4/" + string2)).detach();
        element2.setAttribute("name", string);
        element.addContent((Content)element2);
        if (n == -1) {
            Element element3;
            try {
                element3 = XMLUtil.getItemParameter((Element)element2.getChild("Then").getChild("Item"), (String)"#Direction#", (boolean)false);
                if (element3 != null) {
                    element3.setText(Integer.toString(n));
                }
            }
            catch (Exception exception) {
                // empty catch block
            }
            if (!this.useSameIdForLongShort) {
                element3 = (Element)((Element)element2.getChild("If").getChild("Item").getChildren("Block").get(1)).getChild("Item").getChildren("Param").get(1);
                element3.setText("22222222-2222-2222-2222-222222222222");
                element3 = (Element)element2.getChild("Then").getChild("Item").getChildren("Param").get(2);
                element3.setText("22222222-2222-2222-2222-222222222222");
            }
        }
    }

    protected Element getSignalRule() throws JDOMException, IOException, Exception {
        Element element = new Element("Rule");
        element.setAttribute("name", "Trading signals");
        element.setAttribute("type", "Signal");
        element.setAttribute("everyTick", "false");
        Element element2 = new Element("signals");
        element.addContent((Content)element2);
        element2.addContent((Content)this.getEntrySignalCondition(1, "RandomConditionLong", null));
        element2.addContent((Content)this.getEntrySignalCondition(-1, "RandomConditionShort", "RandomConditionLong"));
        if (this.containsExitRule) {
            Element element3 = this.getExitSignalCondition(1, "RandomConditionLongExit", null);
            if (element3 != null) {
                element2.addContent((Content)element3);
            }
            if ((element3 = this.getExitSignalCondition(-1, "RandomConditionShortExit", "RandomConditionLongExit")) != null) {
                element2.addContent((Content)element3);
            }
        }
        return element;
    }

    protected Element getEntrySignalCondition(int n, String string, String string2) throws JDOMException, IOException, Exception {
        Element element = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq4/signalentry.xml"));
        element.setAttribute("variable", n == 1 ? SGN_LONG_ENTRY_ID : SGN_SHORT_ENTRY_ID);
        if (n == 1 && this.marketSides.equals("short") || n == -1 && this.marketSides.equals("long")) {
            element.removeContent();
            Element element2 = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq4/itemfalse.xml"));
            element.addContent((Content)element2.detach());
        } else {
            Element element3 = element.getChild("Item");
            Element element4 = element3.getChild("Param");
            if (n == 1 || !this.entrySymmetry) {
                element3.setAttribute("key", "RandomCondition");
                element3.setAttribute("name", "RandomCondition");
                element3.setAttribute("display", "RandomCondition(@Chart@#Identification#)");
                element3.setAttribute("generated", "random");
                element4.addContent(string);
                element4.setAttribute("ownRandomKey", "true");
            } else {
                element3.setAttribute("key", "NegatedCondition");
                element3.setAttribute("name", "NegatedCondition");
                element3.setAttribute("display", "NegatedCondition(#Identification#)");
                element3.setAttribute("generated", "negated");
                element4.addContent(string2);
            }
        }
        return element.detach();
    }

    protected Element getExitSignalCondition(int n, String string, String string2) throws JDOMException, IOException, Exception {
        Element element = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq4/signalexit.xml"));
        element.setAttribute("variable", n == 1 ? SGN_LONG_EXIT_ID : SGN_SHORT_EXIT_ID);
        if (n == 1 && this.marketSides.equals("short") || n == -1 && this.marketSides.equals("long")) {
            element.removeContent();
            Element element2 = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq4/itemfalse.xml"));
            element.addContent((Content)element2.detach());
        } else {
            Element element3 = element.getChild("Item");
            Element element4 = element3.getChild("Param");
            if (n == 1 || !this.exitSymmetry) {
                element3.setAttribute("key", "RandomCondition");
                element3.setAttribute("name", "RandomCondition");
                element3.setAttribute("display", "RandomCondition(#Identification#)");
                element3.setAttribute("generated", "random");
                element4.addContent(string);
                element4.setAttribute("ownRandomKey", "true");
            } else {
                element3.setAttribute("key", "NegatedCondition");
                element3.setAttribute("name", "NegatedCondition");
                element3.setAttribute("display", "NegatedCondition(#Identification#)");
                element3.setAttribute("generated", "negated");
                element4.addContent(string2);
            }
        }
        return element.detach();
    }
}


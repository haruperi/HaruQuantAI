/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.pluginlib.program.IProgram
 *  com.strategyquant.pluginlib.program.Program
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.generator;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.generator.StrategyStandardTemplateSQ3;
import java.io.File;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StrategyImproveTemplateSQ3
extends StrategyStandardTemplateSQ3 {
    public static final Logger Log = LoggerFactory.getLogger((String)"StrategyImproveTemplate");

    public StrategyImproveTemplateSQ3(Element element, IRandomGenerator iRandomGenerator) {
        super(element, iRandomGenerator);
    }

    @Override
    public Element generate() throws Exception {
        Object object;
        IProgram iProgram;
        Element element;
        File file;
        String string = this.elWhatToBuild.getChild("StrategyType").getAttributeValue("strategyFile");
        if (!string.contains("/") && !string.contains("\\")) {
            string = MainApp.getDataPath() + "user/strategies/" + string;
        }
        if (!(file = new File(string)).exists()) {
            throw new Exception(L.t((String)"Improver - Strategy '%s' doesn't exist!", (Object[])new Object[]{string}));
        }
        if (string.endsWith(".xml")) {
            element = XMLUtil.fileToXmlElement((File)file);
        } else {
            iProgram = Program.get((String)"Loader");
            object = (ResultsGroup)iProgram.call("loadFile", new Object[]{string, false});
            element = ((ResultsGroup)object).getStrategyXml();
        }
        if (element == null) {
            throw new Exception(L.t((String)"Improver - No strategy found in file '%s' !", (Object[])new Object[]{string}));
        }
        iProgram = element.getChild("Strategy");
        object = new Element("StrategyFile");
        Element element2 = new Element("Strategy");
        object.addContent((Content)element2);
        element2.setAttribute("name", iProgram.getAttributeValue("name"));
        element2.setAttribute("engine", iProgram.getAttributeValue("engine"));
        this.copyElement("Note", (Element)iProgram, element2);
        this.copyElement("Description", (Element)iProgram, element2);
        this.copyElement("MoneyManagement", (Element)iProgram, element2);
        this.copyElement("GlobalSLPT", (Element)iProgram, element2);
        this.createTemplateRules((Element)iProgram, element2);
        this.copyElement("Variables", (Element)iProgram, element2);
        this.copyElement("Datas", (Element)iProgram, element2);
        return object;
    }

    private void createTemplateRules(Element element, Element element2) throws Exception {
        this.loadImproverSettings();
        Element element3 = new Element("Rules");
        element2.addContent((Content)element3);
        Element element4 = new Element("Events");
        element3.addContent((Content)element4);
        for (Element element5 : element.getChild("Rules").getChild("Events").getChildren("Event")) {
            Element element6 = new Element("Event");
            element6.setAttribute("key", element5.getAttributeValue("key"));
            element4.addContent((Content)element6);
            for (Element element7 : element5.getChildren("Rule")) {
                String string = element7.getAttributeValue("type");
                String string2 = element7.getAttributeValue("name");
                boolean bl = XMLUtil.getBooleanAttr((Element)element7, (String)"everyTick", (boolean)false);
                if (!string.equals("IfThen")) {
                    element6.addContent((Content)element7.clone());
                    continue;
                }
                Element element8 = new Element("Rule");
                element8.setAttribute("type", string);
                element8.setAttribute("name", string2);
                element8.setAttribute("everyTick", String.valueOf(bl));
                Element element9 = element7.getChild("Descriptions");
                if (element9 != null) {
                    element8.addContent((Content)element9.detach());
                }
                int n = this.recognizeRuleType(string2, string);
                Element element10 = this.getIf(element7, n);
                element8.addContent((Content)element10);
                Element element11 = this.getImproverThen(element7, n);
                element8.addContent((Content)element11);
                element6.addContent((Content)element8);
            }
        }
    }

    private Element getIf(Element element, int n) throws Exception {
        int n2;
        switch (n) {
            case 1: {
                n2 = this.entryLongImprovement;
                break;
            }
            case 2: {
                n2 = this.entryShortImprovement;
                break;
            }
            case 3: {
                n2 = this.exitLongImprovement;
                break;
            }
            case 4: {
                n2 = this.exitShortImprovement;
                break;
            }
            default: {
                n2 = 0;
            }
        }
        if (n2 == 0) {
            return element.getChild("If").detach();
        }
        if (n2 == 1) {
            Object object;
            Element element2 = null;
            if (n == 1 || n == 2) {
                element2 = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq3/entrycondition.xml"));
                if (n == 1) {
                    this.configureRandomEntryCondition(element2, "RandomConditionLong", null, false);
                } else {
                    this.configureRandomEntryCondition(element2, "RandomConditionShort", "RandomConditionLong", this.entrySymmetry);
                }
            } else {
                element2 = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq3/exitcondition.xml"));
                if (n == 3) {
                    this.configureRandomExitCondition(element2, "RandomConditionLongExit", null, 1, false);
                } else {
                    this.configureRandomExitCondition(element2, "RandomConditionShortExit", "RandomConditionLongExit", -1, this.exitSymmetry);
                }
                if (n == 3 || n == 4) {
                    Element element3;
                    String string = object = n == 3 ? this.longMagicNumberValue : this.shortMagicNumberValue;
                    if (object != null && !((String)object).equals("") && (element3 = element2.getChild("Block").getChild("Item")) != null) {
                        Element element4 = XMLUtil.getItemParameter((Element)element3, (String)"#MagicNumber#", (boolean)false);
                        element4.setText((String)object);
                    }
                }
            }
            object = new Element("If");
            object.addContent((Content)element2.detach());
            return object;
        }
        if (n2 == 2 || n2 == 2) {
            Element element5 = element.getChild("If").detach();
            Element element6 = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq3/conditiononly.xml"));
            if (n == 1 || n == 2) {
                if (n == 1) {
                    this.configureRandomEntryCondition(element6, "RandomConditionLong", null, false);
                } else {
                    this.configureRandomEntryCondition(element6, "RandomConditionShort", "RandomConditionLong", this.entrySymmetry);
                }
            } else if (n == 3) {
                this.configureRandomExitConditionOnly(element6, "RandomConditionLongExit", null, false);
            } else {
                this.configureRandomExitConditionOnly(element6, "RandomConditionShortExit", "RandomConditionLongExit", this.exitSymmetry);
            }
            Element element7 = new Element("Block");
            element7.addContent((Content)element6.detach());
            Element element8 = element5.getChild("Item");
            if (element8 != null) {
                String string = element8.getAttributeValue("key");
                if (string == null || !string.equals("AND")) {
                    Element element9 = new Element("Item");
                    element9.setAttribute("key", "AND");
                    Element element10 = new Element("Block");
                    element9.addContent((Content)element8.detach());
                    element9.addContent((Content)element7.detach());
                    element5.addContent((Content)element9);
                } else {
                    Element element11 = element8;
                    element11.addContent((Content)element7.detach());
                }
            }
            return element5;
        }
        throw new Exception("Incorrect improvement action!");
    }

    private void configureRandomEntryCondition(Element element, String string, String string2, boolean bl) {
        Element element2 = element.getChild("Param");
        Element element3 = element;
        if (element2 == null) {
            element3 = ((Element)element.getChildren("Block").get(1)).getChild("Item");
            element2 = element3.getChild("Param");
        }
        if (!bl) {
            element3.setAttribute("key", "RandomCondition");
            element3.setAttribute("name", "RandomCondition");
            element3.setAttribute("display", "RandomCondition(@Chart@#Identification#)");
            element3.setAttribute("generated", "random");
            element2.addContent(string);
            element2.setAttribute("ownRandomKey", "true");
        } else {
            element3.setAttribute("key", "NegatedCondition");
            element3.setAttribute("name", "NegatedCondition");
            element3.setAttribute("display", "NegatedCondition(#Identification#)");
            element3.setAttribute("generated", "negated");
            element2.addContent(string2);
        }
    }

    private Element getThenOld(Element element, int n) throws Exception {
        Object object;
        Element element2;
        Element element3;
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
        if ((n == 1 || n == 2) && (element3 = this.getStandardActionChild(element.getChild("Then"))) != null && (element2 = XMLUtil.getItemParameter((Element)element3, (String)"#MagicNumber#", (boolean)false)) != null) {
            if (n == 1) {
                this.longMagicNumberValue = element2.getText();
            } else {
                this.shortMagicNumberValue = element2.getText();
            }
        }
        if (n3 == 0 && n2 == 0) {
            return element.getChild("Then").detach();
        }
        element2 = n == 1 || !this.entrySymmetry ? XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq3/randomaction.xml")) : (this.exitSymmetry ? XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq3/oppositeaction_exitsymmetry.xml")) : XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq3/oppositeaction_exitunsymmetry.xml")));
        element3 = n3 == 0 ? this.getStandardActionChild(element.getChild("Then")) : element2.clone();
        element3.removeContent();
        if (n == 1 || !this.entrySymmetry) {
            this.addIdentificationParameter(element3, "randomId", n == 1 ? "RandomActionLong" : "RandomActionShort");
        } else {
            this.addIdentificationParameter(element3, "randomIdCombo", "RandomActionLong");
        }
        Element element4 = this.getStandardActionChild(element.getChild("Then"));
        if (n2 == 0) {
            for (Element element5 : element4.getChildren("Param")) {
                element3.addContent((Content)element5.clone());
            }
        } else {
            object = element2.getChildren("Param");
            for (int i = 0; i < object.size(); ++i) {
                Element element6 = (Element)object.get(i);
                if (element6.getAttributeValue("key").equals("#Identification#")) continue;
                String string = element6.getAttributeValue("key");
                Element element7 = XMLUtil.getItemParameter((Element)element4, (String)string, (boolean)false);
                if (element7 == null) {
                    if (n3 == 0) continue;
                    element3.addContent((Content)element6.clone());
                    continue;
                }
                if (string.contains(".")) {
                    boolean bl = this.isUsedParameter(element7);
                    if (n2 == 0 || n2 == 1 && !bl) {
                        element3.addContent((Content)element7.clone());
                        continue;
                    }
                    element3.addContent((Content)element6.clone());
                    continue;
                }
                Element element8 = n3 == 0 ? element7.clone() : element6.clone();
                if (element8.getAttributeValue("key").equals("#MagicNumber#")) {
                    // empty if block
                }
                element3.addContent((Content)element8);
            }
        }
        object = new Element("Then");
        object.addContent((Content)element3);
        return object;
    }

    private int recognizeRuleType(String string, String string2) {
        if (!string2.equals("IfThen")) {
            return 0;
        }
        if ((string = string.toUpperCase()).contains("LONG")) {
            if (string.contains("EXIT")) {
                return 3;
            }
            return 1;
        }
        if (string.contains("SHORT")) {
            if (string.contains("EXIT")) {
                return 4;
            }
            return 2;
        }
        return 0;
    }

    private void loadImproverSettings() {
        Element element = this.elSettings.getChild("PartsToImprove");
        Element element2 = element.getChild("EntryRules");
        Element element3 = element.getChild("OrderTypes");
        Element element4 = element.getChild("ExitRules");
        this.entryLongImprovement = this.recognizeImproveType(element2.getChild("LongImprovement"));
        this.entryShortImprovement = this.entrySymmetry ? this.entryLongImprovement : this.recognizeImproveType(element2.getChild("ShortImprovement"));
        this.orderLongImprovement = this.recognizeImproveType(element3.getChild("LongImprovement"));
        this.orderShortImprovement = this.recognizeImproveType(element3.getChild("ShortImprovement"));
        this.exitLongImprovement = this.recognizeImproveType(element4.getChild("LongImprovement"));
        this.exitShortImprovement = this.recognizeImproveType(element4.getChild("ShortImprovement"));
    }

    private int recognizeImproveType(Element element) {
        int n = 1;
        String string = element.getAttributeValue("use");
        if (string.equals("false")) {
            return 0;
        }
        String string2 = element.getAttributeValue("action");
        if (string2 != null) {
            switch (string2) {
                case "add": {
                    return 2;
                }
                case "replace": {
                    return 1;
                }
                case "add-or-replace": {
                    return 2;
                }
            }
        }
        return n;
    }

    private void copyElement(String string, Element element, Element element2) {
        Element element3 = element.getChild(string);
        if (element3 == null) {
            return;
        }
        element2.addContent((Content)element3.detach());
    }
}


/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
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
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.generator.StrategyStandardTemplateSQ4;
import java.io.File;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StrategyImproveTemplateSQ4
extends StrategyStandardTemplateSQ4 {
    public static final Logger Log = LoggerFactory.getLogger((String)"StrategyImproveTemplate");

    public StrategyImproveTemplateSQ4(Element element, IRandomGenerator iRandomGenerator) {
        super(element, iRandomGenerator);
    }

    @Override
    public Element generate() throws Exception {
        ResultsGroup resultsGroup;
        IProgram iProgram;
        Element element;
        File file;
        String string = this.elWhatToBuild.getChild("StrategyType").getAttributeValue("strategyFile");
        if (!string.contains("/") && !string.contains("\\")) {
            string = MainApp.getDataPath() + "user/strategies/" + string;
        }
        if (!(file = new File(string)).exists()) {
            throw new Exception(String.format("Improver - Strategy '%s' doesn't exist!", string));
        }
        if (string.endsWith(".xml")) {
            element = XMLUtil.fileToXmlElement((File)file);
        } else {
            iProgram = Program.get((String)"Loader");
            resultsGroup = (ResultsGroup)iProgram.call("loadFile", new Object[]{string, false});
            element = resultsGroup.getStrategyXml();
        }
        if (element == null) {
            throw new Exception(String.format("Improver - No strategy found in file '%s' !", string));
        }
        iProgram = element.getChild("Strategy");
        XMLUtil.removeAttribute((Element)iProgram, (String)"generate");
        XMLUtil.removeAttribute((Element)iProgram, (String)"generated");
        resultsGroup = new Element("StrategyFile");
        Element element2 = new Element("Strategy");
        resultsGroup.addContent((Content)element2);
        element2.setAttribute("name", iProgram.getAttributeValue("name"));
        element2.setAttribute("engine", iProgram.getAttributeValue("engine"));
        this.copyElement("Note", (Element)iProgram, element2);
        this.copyElement("Description", (Element)iProgram, element2);
        this.copyElement("MoneyManagement", (Element)iProgram, element2);
        this.copyElement("GlobalSLPT", (Element)iProgram, element2);
        this.createTemplateRules((Element)iProgram, element2);
        this.copyElement("Variables", (Element)iProgram, element2);
        this.copyElement("Datas", (Element)iProgram, element2);
        return resultsGroup;
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
            List list = element5.getChildren("Rule");
            for (int i = 0; i < list.size(); ++i) {
                Element element7;
                Element element8;
                Element element9 = (Element)list.get(i);
                String string = element9.getAttributeValue("type");
                String string2 = element9.getAttributeValue("name");
                boolean bl = XMLUtil.getBooleanAttr((Element)element9, (String)"everyTick", (boolean)false);
                if (string.equals("Signal")) {
                    element8 = new Element("Rule");
                    element8.setAttribute("type", string);
                    element8.setAttribute("name", string2);
                    element8.setAttribute("everyTick", String.valueOf(bl));
                    element7 = element9.getChild("Descriptions");
                    if (element7 != null) {
                        element8.addContent((Content)element7.detach());
                    }
                    Element element10 = this.getSignals(element9);
                    element8.addContent((Content)element10);
                    element6.addContent((Content)element8);
                    continue;
                }
                if (string.equals("IfThen")) {
                    element8 = new Element("Rule");
                    element8.setAttribute("type", string);
                    element8.setAttribute("name", string2);
                    element8.setAttribute("everyTick", String.valueOf(bl));
                    element7 = element9.getChild("Descriptions");
                    if (element7 != null) {
                        element8.addContent((Content)element7.detach());
                    }
                    int n = this.recognizeRuleType(string2, string);
                    Element element11 = element9.getChild("If").clone();
                    element8.addContent((Content)element11);
                    Element element12 = this.getImproverThen(element9, n);
                    element8.addContent((Content)element12);
                    element6.addContent((Content)element8);
                    continue;
                }
                element6.addContent((Content)element9.clone());
            }
        }
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

    private Element getSignals(Element element) throws Exception {
        Element element2;
        Element element3;
        Element element4;
        Element element5 = new Element("signals");
        Element element6 = this.getSignal(element, 1);
        if (element6 != null) {
            element5.addContent((Content)element6);
        }
        if ((element4 = this.getSignal(element, 2)) != null) {
            element5.addContent((Content)element4);
        }
        if ((element3 = this.getSignal(element, 3)) != null) {
            element5.addContent((Content)element3);
        }
        if ((element2 = this.getSignal(element, 4)) != null) {
            element5.addContent((Content)element2);
        }
        return element5;
    }

    private Element getSignal(Element element, int n) throws Exception {
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
                throw new Exception("No signal type detected");
            }
        }
        Element element2 = this.getSignalByType(element, n);
        if (element2 == null) {
            element2 = this.getSignalByType(element, n);
            return null;
        }
        if (n2 == 0) {
            return element2.detach();
        }
        if (n2 == 1) {
            Element element3 = null;
            if (n == 1) {
                element3 = this.getEntrySignalCondition(1, "RandomConditionLong", null);
            } else if (n == 2) {
                element3 = this.getEntrySignalCondition(-1, "RandomConditionShort", "RandomConditionLong");
            } else if (n == 3) {
                element3 = this.getExitSignalCondition(1, "RandomConditionLongExit", null);
            } else if (n == 4) {
                element3 = this.getExitSignalCondition(-1, "RandomConditionShortExit", "RandomConditionLongExit");
            }
            return element3;
        }
        if (n2 == 2 || n2 == 2) {
            Element element4;
            Element element5;
            if (n == 1) {
                element5 = this.getSignalRandomCondition(1, "RandomConditionLong", null);
            } else if (n == 2) {
                element5 = this.getSignalRandomCondition(-1, "RandomConditionShort", "RandomConditionLong");
            } else if (n == 3) {
                element5 = this.getSignalRandomCondition(1, "RandomConditionLongExit", null);
            } else if (n == 4) {
                element5 = this.getSignalRandomCondition(-1, "RandomConditionShortExit", "RandomConditionLongExit");
            } else {
                throw new Exception("No signal type detected");
            }
            List list = element2.getChildren();
            if (list.size() <= 0) {
                element4 = element5;
            } else {
                Element element6 = (Element)element2.getChildren().get(0);
                Element element7 = new Element("Item");
                element7.setAttribute("key", "AND");
                Element element8 = new Element("Block");
                element7.addContent((Content)element8);
                element8.addContent((Content)element6.detach());
                element8 = new Element("Block");
                element7.addContent((Content)element8);
                element8.addContent((Content)element5.detach());
                element4 = element7;
            }
            element2.addContent((Content)element4);
            return element2.detach();
        }
        throw new Exception("Incorrect improvement action!");
    }

    private Element getSignalRandomCondition(int n, String string, String string2) {
        Element element = new Element("Item");
        Element element2 = new Element("Param");
        element.addContent((Content)element2);
        element2.setAttribute("key", "#Identification#");
        element2.setAttribute("name", "Identification");
        element2.setAttribute("type", "string");
        if (n == 1 || !this.entrySymmetry) {
            element.setAttribute("key", "RandomCondition");
            element.setAttribute("name", "RandomCondition");
            element.setAttribute("display", "RandomCondition(@Chart@#Identification#)");
            element.setAttribute("generated", "random");
            element2.addContent(string);
            element2.setAttribute("controlType", "randomId");
            element2.setAttribute("ownRandomKey", "true");
        } else {
            element.setAttribute("key", "NegatedCondition");
            element.setAttribute("name", "NegatedCondition");
            element.setAttribute("display", "NegatedCondition(#Identification#)");
            element.setAttribute("generated", "negated");
            element2.addContent(string2);
            element2.setAttribute("controlType", "randomIdCombo");
        }
        return element;
    }

    private Element getSignalByType(Element element, int n) throws Exception {
        List list = element.getChild("signals").getChildren("signal");
        String string = null;
        switch (n) {
            case 1: {
                string = "33333333-1111-1111-3333-333333333333";
                break;
            }
            case 2: {
                string = "33333333-2222-1111-3333-333333333333";
                break;
            }
            case 3: {
                string = "33333333-1111-2222-3333-333333333333";
                break;
            }
            case 4: {
                string = "33333333-2222-2222-3333-333333333333";
            }
        }
        if (string == null) {
            throw new Exception("Incorrect signalType");
        }
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            if (!element2.getAttributeValue("variable").equals(string)) continue;
            return element2;
        }
        switch (n) {
            case 1: {
                if (list.size() != 4) break;
                return (Element)list.get(0);
            }
            case 2: {
                if (list.size() != 3) break;
                return (Element)list.get(0);
            }
            case 3: {
                if (list.size() != 2) break;
                return (Element)list.get(0);
            }
            case 4: {
                if (list.size() != 1) break;
                return (Element)list.get(0);
            }
        }
        return null;
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
            element3.setAttribute("display", "RandomCondition(#Identification#)");
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
        Element element2 = n == 1 || !this.entrySymmetry ? XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq3/randomaction.xml")) : (this.exitSymmetry ? XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq3/oppositeaction_exitsymmetry.xml")) : XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sq3/oppositeaction_exitunsymmetry.xml")));
        Element element3 = n3 == 0 ? this.getStandardActionChild(element.getChild("Then")) : element2.clone();
        element3.removeContent();
        if (n == 1 || !this.entrySymmetry) {
            this.addIdentificationParameter(element3, "randomId", n == 1 ? "RandomActionLong" : "RandomActionShort");
        } else if (this.entrySymmetry && !this.exitSymmetry && n == 2) {
            this.addIdentificationParameter(element3, "randomIdCombo", "RandomActionShort");
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
                    Element element8 = element6.clone();
                    element3.addContent((Content)element8);
                    continue;
                }
                Element element9 = n3 == 0 ? element7.clone() : element6.clone();
                if (element9.getAttributeValue("key").equals("#MagicNumber#")) {
                    // empty if block
                }
                element3.addContent((Content)element9);
            }
        }
        object = new Element("Then");
        object.addContent((Content)element3);
        return object;
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


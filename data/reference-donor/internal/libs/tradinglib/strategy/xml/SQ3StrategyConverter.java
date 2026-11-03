/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  org.jdom2.Attribute
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.jdom2.JDOMException
 */
package com.strategyquant.tradinglib.strategy.xml;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.blocks.random.BlockDefinition;
import com.strategyquant.tradinglib.blocks.random.BlockParameter;
import com.strategyquant.tradinglib.blocks.random.BlocksConfig;
import java.io.File;
import java.io.IOException;
import java.io.StringReader;
import java.io.StringWriter;
import java.util.List;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.stream.StreamResult;
import javax.xml.transform.stream.StreamSource;
import org.jdom2.Attribute;
import org.jdom2.Content;
import org.jdom2.Element;
import org.jdom2.JDOMException;

public class SQ3StrategyConverter {
    private static SQ3StrategyConverter instance;
    private Transformer transformer;
    private BlocksConfig blocksConfig = BlocksConfig.getConfig();
    private Element defaultSize = new Element("Formula");
    private Element defaultRangeLevel;
    private Element defaultRange;
    private Element defaultSLPT;
    private int existingRules;

    public static synchronized SQ3StrategyConverter getInstance() throws Exception {
        if (instance == null) {
            instance = new SQ3StrategyConverter();
        }
        return instance;
    }

    public SQ3StrategyConverter() throws JDOMException, IOException, Exception {
        this.defaultSize.setAttribute("key", "SQ.Formulas.Size.UseGlobalMM");
        this.defaultRangeLevel = new Element("Formula");
        this.defaultRangeLevel.setAttribute("key", "SQ.Formulas.RangeLevel.None");
        this.defaultRange = new Element("Formula");
        this.defaultRange.setAttribute("key", "SQ.Formulas.Range.None");
        this.defaultSLPT = new Element("Formula");
        this.defaultSLPT.setAttribute("key", "SQ.Formulas.SLPT.None");
    }

    public Element convert(Element element) throws Exception {
        String string = "transformStrategyQuant.xslt";
        try {
            if (element.getChild("Strategy").getChildren("TradeRule").size() > 0) {
                string = "transformEA.xslt";
            }
        }
        catch (Exception exception) {
            // empty catch block
        }
        StreamSource streamSource = new StreamSource(new File(MainApp.getDataPath() + "internal/web/SQWIZARD/xslt/" + string));
        TransformerFactory transformerFactory = TransformerFactory.newInstance();
        this.transformer = transformerFactory.newTransformer(streamSource);
        String string2 = XMLUtil.elementToString((Element)element);
        StreamSource streamSource2 = new StreamSource(new StringReader(string2));
        StringWriter stringWriter = new StringWriter();
        StreamResult streamResult = new StreamResult(stringWriter);
        this.transformer.transform(streamSource2, streamResult);
        String string3 = ((Object)stringWriter).toString();
        string3 = this.normalizeXml(string3);
        string3 = SQUtils.fixRenamedActionParams((String)string3);
        Element element2 = XMLUtil.stringToElement((String)string3);
        this.existingRules = 0;
        element2 = this.fixStrategy(element2);
        this.removeUnusedMagicVariables(element2);
        this.removeEmptyBlocks(element2);
        return element2;
    }

    private void removeUnusedMagicVariables(Element element) {
        String string = XMLUtil.elementToString((Element)element);
        this.removeUnusedVariable("MagicNumber", string, element);
        this.removeUnusedVariable("MagicLong", string, element);
        this.removeUnusedVariable("MagicShort", string, element);
    }

    private void removeUnusedVariable(String string, String string2, Element element) {
        Object object;
        int n;
        int n2 = 0;
        boolean bl = false;
        while ((n = string2.indexOf(string, n2)) != -1) {
            object = string2.substring(n + string.length(), n + string.length() + 5);
            if (!((String)object).equals("</id>") && !((String)object).equals("</nam")) {
                bl = true;
                break;
            }
            n2 = n + 1;
        }
        if (bl) {
            return;
        }
        Element element2 = element.getChild("Strategy").getChild("Variables");
        object = element2.getChildren();
        for (int i = 0; i < object.size(); ++i) {
            Element element3 = (Element)object.get(i);
            Element element4 = element3.getChild("id");
            String string3 = element4.getText();
            if (!string3.equals(string)) continue;
            element2.removeContent((Content)element3);
            break;
        }
    }

    private Element fixStrategy(Element element) throws Exception {
        String string;
        Element element2 = this.copyElement(element);
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            String string2;
            Element element3 = (Element)list.get(i);
            Element element4 = null;
            switch (string2 = element3.getName()) {
                case "Item": {
                    element4 = this.fixItem(element3);
                    break;
                }
                case "Rule": {
                    element4 = this.fixRule(element3);
                    break;
                }
                default: {
                    element4 = this.fixStrategy(element3);
                }
            }
            element2.addContent((Content)element4);
        }
        if (list.size() == 0 && (string = element.getText()) != null) {
            element2.setText(string);
        }
        return element2;
    }

    private Element fixRule(Element element) throws Exception {
        Element element2 = this.fixStrategy(element);
        String string = null;
        switch (this.existingRules) {
            case 0: {
                string = "Long Entry";
                break;
            }
            case 1: {
                string = "Short Entry";
                break;
            }
            case 2: {
                string = "Long Exit";
                break;
            }
            case 3: {
                string = "Short Exit";
            }
        }
        ++this.existingRules;
        if (string == null) {
            throw new Exception("Rule name not recognized!");
        }
        element2.setAttribute("name", string);
        return element2;
    }

    private Element copyElement(Element element) {
        Element element2 = new Element(element.getName());
        List list = element.getAttributes();
        for (int i = 0; i < list.size(); ++i) {
            element2.setAttribute(((Attribute)list.get(i)).getName(), ((Attribute)list.get(i)).getValue());
        }
        return element2;
    }

    private Element fixItem(Element element) throws Exception {
        Element element2 = this.copyElement(element);
        element2 = this.fixItemAttributes(element2);
        String string = element.getAttributeValue("key");
        BlockDefinition blockDefinition = this.blocksConfig.getBlock(string);
        if (string.equals("AND") || string.equals("OR")) {
            return this.processAndOr(element2, element, this.existingRules);
        }
        for (int i = 0; i < blockDefinition.parameters.size(); ++i) {
            String string2;
            String string3;
            String string4;
            BlockParameter blockParameter = (BlockParameter)blockDefinition.parameters.get(i);
            Element element3 = this.findParamByKey(element, blockParameter.key);
            Element element4 = null;
            if (element3 == null) {
                element4 = blockParameter.getParamElement();
                string4 = element4.getAttributeValue("isFormula");
                if (string4 == null || string4.equals("false")) {
                    string3 = element4.getAttributeValue("defaultValue");
                    if (string3 == null) {
                        throw new Exception("Element doesn't have default value!");
                    }
                    string2 = element4.getAttributeValue("key");
                    if (!string2.equals("#ReplaceExisting#") || !XMLUtil.elementIs((Element)element4, (String)"variable")) {
                        element4.setText(string3);
                    }
                    if (string2.equals("#MagicNumber#")) {
                        element4.setAttribute("variable", "true");
                        element4.setAttribute("variableType", "INT");
                    }
                    if (string2.equals("#Direction#") && (this.existingRules == 1 || this.existingRules == 3)) {
                        element4.setText("-1");
                    }
                } else {
                    switch (string3 = element4.getAttributeValue("key")) {
                        case "#Size#": {
                            element4.addContent((Content)this.defaultSize.clone());
                            break;
                        }
                        case "#MoveSL2BE.MoveSL2BE#": {
                            element4.addContent((Content)this.defaultRangeLevel.clone());
                            break;
                        }
                        case "#MoveSL2BE.SL2BEAddPips#": {
                            element4.addContent((Content)this.defaultRange.clone());
                            break;
                        }
                        case "#TrailingStop.TrailingStop#": {
                            element4.addContent((Content)this.defaultRangeLevel.clone());
                            break;
                        }
                        case "#TrailingStop.TrailingActivation#": {
                            element4.addContent((Content)this.defaultRange.clone());
                            break;
                        }
                        case "#StopLoss.StopLoss#": {
                            element4.addContent((Content)this.defaultSLPT.clone());
                            break;
                        }
                        case "#ProfitTarget.ProfitTarget#": {
                            element4.addContent((Content)this.defaultSLPT.clone());
                            break;
                        }
                        default: {
                            throw new Exception("Unknown item " + string);
                        }
                    }
                }
            } else {
                element4 = blockParameter.getParamElement();
                if (element3.getChildren().size() > 1) {
                    throw new Exception("Has more than 1 child");
                }
                if (element3.getChildren().size() > 0) {
                    string4 = (Element)element3.getChildren().get(0);
                    string3 = null;
                    switch (string2 = string4.getName()) {
                        case "Item": {
                            string3 = this.fixItem((Element)string4);
                            break;
                        }
                        case "Formula": {
                            string3 = this.fixStrategy((Element)string4);
                        }
                    }
                    if (string3 == null) {
                        throw new Exception("Unknown child element: " + string2);
                    }
                    element4.addContent((Content)string3);
                } else {
                    string4 = element4.getAttributeValue("key");
                    if (string4.equals("#MagicNumber#")) {
                        element4.setAttribute("variable", "true");
                        element4.setAttribute("variableType", "INT");
                    } else if (string4.equals("#ReplaceExisting#") && XMLUtil.elementIs((Element)element3, (String)"variable")) {
                        element4.setAttribute("variable", "true");
                        element4.setAttribute("variableType", "BOOL");
                    } else if (string4.equals("#Variable#") && XMLUtil.elementIs((Element)element3, (String)"variable")) {
                        element4.setAttribute("variable", "true");
                    }
                    element4.setText(element3.getText());
                }
                element4.setName(element3.getName());
            }
            element2.addContent((Content)element4);
        }
        return element2;
    }

    private Element processAndOr(Element element, Element element2, int n) throws Exception {
        List list = element2.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            Element element3;
            String string;
            Element element4 = (Element)list.get(i);
            switch (string = element4.getName()) {
                case "Item": {
                    element3 = this.fixItem(element4);
                    break;
                }
                default: {
                    element3 = this.fixStrategy(element4);
                }
            }
            element.addContent((Content)element3);
        }
        return element;
    }

    private Element fixItemAttributes(Element element) throws Exception {
        String string = element.getAttributeValue("key");
        if (string.equals("AND") || string.equals("OR")) {
            return element;
        }
        BlockDefinition blockDefinition = this.blocksConfig.getBlock(string);
        if (blockDefinition == null) {
            throw new Exception("Key " + string + " wasn't found in blocks");
        }
        Element element2 = blockDefinition.getXml();
        List list = element2.getAttributes();
        for (int i = 0; i < list.size(); ++i) {
            String string2 = element.getAttributeValue(((Attribute)list.get(i)).getName());
            if (string2 != null) continue;
            element.setAttribute(((Attribute)list.get(i)).getName(), ((Attribute)list.get(i)).getValue());
        }
        return element;
    }

    private Element findParamByKey(Element element, String string) {
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            String string2 = ((Element)list.get(i)).getAttributeValue("key");
            if (string2 == null || !string2.equals(string)) continue;
            return (Element)list.get(i);
        }
        return null;
    }

    private String normalizeXml(String string) {
        return string.replace("<ParamX", "<Param").replace("</ParamX", "</Param").replace("xmlns:wizard=\"http://example.com/wizard\"", "").replace("\n", "").replace("\r", "").replace("\t", "").replaceAll(" +", " ").replace("> <", "><").replace(" >", ">");
    }

    private void removeEmptyBlocks(Element element) {
        List list = element.getChildren();
        block7: for (int i = list.size() - 1; i >= 0; --i) {
            String string;
            Element element2 = (Element)list.get(i);
            switch (string = element2.getName()) {
                case "Item": 
                case "Block": {
                    String string2 = element2.getAttributeValue("key");
                    if (string2 != null && string2.equals("AlwaysTrue")) continue block7;
                    if (element2.getChildren().size() == 0) {
                        element.removeContent((Content)element2);
                        continue block7;
                    }
                    this.removeEmptyBlocks(element2);
                    continue block7;
                }
                default: {
                    if (element2.getChildren().size() <= 0) continue block7;
                    this.removeEmptyBlocks(element2);
                }
            }
        }
    }
}


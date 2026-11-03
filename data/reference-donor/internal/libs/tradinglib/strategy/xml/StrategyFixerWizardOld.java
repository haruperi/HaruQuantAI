/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.constants.SQPaths
 *  org.jdom2.Attribute
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.jdom2.JDOMException
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.strategy.xml;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.tradinglib.BlockDefinitionException;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;
import org.jdom2.Attribute;
import org.jdom2.Content;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StrategyFixerWizardOld {
    public static final Logger Log = LoggerFactory.getLogger((String)"StrategyFixerWizardOld");
    public static final String currentVersion = "3.9.131";
    private static HashMap<String, String> blockCategoryTypes;
    private static Map<String, List<Attribute>> itemAttributes;

    public static String fixStrategy(String string) throws Exception {
        return StrategyFixerWizardOld.fixStrategy(string, SQPaths.wizardConfigPath, false);
    }

    public static String fixStrategy(String string, String string2, boolean bl) throws Exception {
        Element element = XMLUtil.stringToElement((String)string);
        if (!bl && StrategyFixerWizardOld.checkVersion(element)) {
            return string;
        }
        StrategyFixerWizardOld.loadCategoryTypesAndAttributes(string2);
        string = SQUtils.removeUTF8BOM((String)string);
        string = SQUtils.removeXmlns((String)string);
        string = StrategyFixerWizardOld.fixCategoryTypes(element);
        string = StrategyFixerWizardOld.fixMissingAttributes(element);
        string = StrategyFixerWizardOld.fixMoneyManagement(element);
        string = SQUtils.fixRenamedActionParams((String)string);
        string = SQUtils.fixHeikenAshi((String)string);
        string = string.replaceAll("help=\".*?\"", "");
        return string;
    }

    public static String fixMissingAttributes(Element element) throws Exception {
        ArrayList arrayList = XMLUtil.getNestedElements((Element)element, (String)"Item");
        for (int i = 0; i < arrayList.size(); ++i) {
            List<Attribute> list;
            Element element2 = (Element)arrayList.get(i);
            String string = element2.getAttributeValue("key");
            if (string == null || (list = itemAttributes.get(string)) == null) continue;
            StrategyFixerWizardOld.addMissingAttributes(element2, list);
        }
        return XMLUtil.xmlToString((Element)element);
    }

    private static void addMissingAttributes(Element element, List<Attribute> list) {
        List list2 = element.getAttributes();
        Set set = list2.stream().map(Attribute::getName).collect(Collectors.toSet());
        Map map = list.stream().collect(Collectors.toMap(Attribute::getName, Function.identity()));
        for (String string : map.keySet()) {
            if (set.contains(string)) continue;
            element.getAttributes().add(new Attribute(string, ((Attribute)map.get(string)).getValue()));
        }
    }

    public static boolean checkVersion(Element element) {
        try {
            String string = element.getAttributeValue("Version");
            String[] stringArray = string.split("\\.");
            String[] stringArray2 = currentVersion.split("\\.");
            for (int i = 0; i < stringArray2.length; ++i) {
                if (i >= stringArray.length || Integer.parseInt(stringArray[i]) >= Integer.parseInt(stringArray2[i])) continue;
                return false;
            }
            return stringArray.length == stringArray2.length;
        }
        catch (Exception exception) {
            return false;
        }
    }

    public static String fixMoneyManagement(Element element) throws JDOMException, IOException, BlockDefinitionException {
        ArrayList arrayList = XMLUtil.getNestedElements((Element)element, (String)"MoneyManagement");
        for (int i = 0; i < arrayList.size(); ++i) {
            Element element2 = (Element)arrayList.get(i);
            if (element2.getChild("Method") != null) continue;
            Element element3 = new Element("Method");
            element3.setAttribute("type", element2.getAttributeValue("type"));
            element3.setAttribute("use", "true");
            Element element4 = new Element("Params");
            Element element5 = element2.getChild("params");
            String string = "Param";
            if (element5 == null) {
                element5 = element2.getChild("Parameters");
                string = "Parameter";
            }
            if (element5 != null) {
                List list = element5.getChildren(string);
                for (int j = 0; j < list.size(); ++j) {
                    Element element6 = (Element)list.get(j);
                    element4.addContent((Content)element6.clone().setName("Param"));
                }
                element2.removeContent((Content)element5);
            }
            element3.addContent((Content)element4);
            element2.addContent((Content)element3);
        }
        return XMLUtil.xmlToString((Element)element);
    }

    private static void fixBlockAttributes(Element element) throws BlockDefinitionException {
        List list = element.getChildren();
        if (list != null) {
            for (int i = 0; i < list.size(); ++i) {
                String string;
                String string2;
                Element element2 = (Element)list.get(i);
                if (element2.getName().equals("Item") && (string2 = element2.getAttributeValue("key")) != null && (string = blockCategoryTypes.get(string2)) != null) {
                    element2.setAttribute("categoryType", string);
                }
                if (element2.getChildren() == null) continue;
                StrategyFixerWizardOld.fixBlockAttributes(element2);
            }
        }
    }

    public static String fixCategoryTypes(Element element) throws JDOMException, IOException, BlockDefinitionException {
        StrategyFixerWizardOld.fixBlockAttributes(element);
        element.setAttribute("Version", currentVersion);
        return XMLUtil.xmlToString((Element)element);
    }

    private static void loadCategoryTypesAndAttributes(String string) throws Exception {
        if (blockCategoryTypes != null) {
            return;
        }
        blockCategoryTypes = new HashMap();
        itemAttributes = new HashMap<String, List<Attribute>>();
        File file = new File(string);
        if (!file.exists()) {
            throw new Exception("Wizard config file not found.");
        }
        Element element = XMLUtil.fileToXmlElement((File)file);
        ArrayList arrayList = XMLUtil.getNestedElements((Element)element, (String)"Item");
        for (int i = 0; i < arrayList.size(); ++i) {
            Element element2 = (Element)arrayList.get(i);
            String string2 = element2.getAttributeValue("key");
            String string3 = element2.getAttributeValue("categoryType");
            if (string2 != null && string3 != null) {
                blockCategoryTypes.put(string2, string3);
            }
            itemAttributes.put(string2, element2.getAttributes());
        }
    }
}


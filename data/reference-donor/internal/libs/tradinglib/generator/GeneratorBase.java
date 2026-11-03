/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.SettingsMap
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.generator;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.blocks.random.ReplacementsConfig;
import com.strategyquant.tradinglib.generator.GenerateException;
import com.strategyquant.tradinglib.generator.RandomAndOr;
import com.strategyquant.tradinglib.generator.RandomAndOrList;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class GeneratorBase {
    public static final Logger Log = LoggerFactory.getLogger((String)"GeneratorBase");
    protected Element elTemplate;
    protected IRandomGenerator rng;
    protected ReplacementsConfig replacements;
    protected HashMap<String, Element> generatedElements;

    protected void addTemplateVariablesToBuildSettings(SettingsMap settingsMap) {
        for (Element element : this.elTemplate.getChild("Strategy").getChild("Variables").getChildren()) {
            settingsMap.set(element.getChildText("name"), (Object)element.getChildText("id"));
        }
    }

    protected void getIdentifiers(Element element, ArrayList<String> arrayList, HashMap<String, Element> hashMap, boolean bl) throws GenerateException {
        String string = null;
        String string2 = null;
        String string3 = null;
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            Object object;
            Element element2 = (Element)list.get(i);
            if ((element2.getName().equals("Item") || element2.getName().equals("Param")) && (object = element2.getAttributeValue("generate")) != null) {
                if (bl && ((String)object).equals("random")) {
                    arrayList.add(element2.getName().equals("Item") ? GeneratorBase.findIdentifierInParams(element2, true) : GeneratorBase.findIdentifierInParams(element, true));
                } else if (!bl && (((String)object).equals("same") || ((String)object).equals("opposite"))) {
                    if (element2.getName().equals("Item")) {
                        arrayList.add(GeneratorBase.findIdentifierInParams(element2, true));
                    } else {
                        string = element2.getAttributeValue("identification");
                        if (string == null) {
                            string = element2.getAttributeValue("identificator");
                        }
                        if ((string2 = element.getAttributeValue("key")) == null) {
                            string2 = "Unknown";
                        }
                        if ((string3 = element2.getAttributeValue("key")) == null) {
                            string3 = "Unknown";
                        }
                        if (string == null) {
                            throw new GenerateException(String.format("Bad configuration - Identification not found in item '%s->%s'", string2, string3));
                        }
                        if (!hashMap.containsKey(string)) {
                            throw new GenerateException(String.format("Bad configuration - No random block found for identifier '%s' referenced by '%s->%s'", string, string2, string3));
                        }
                        Element element3 = hashMap.get(string);
                        Element element4 = this.getRandomBlockParamElement(element3, string3);
                        if (element4 == null) {
                            throw new GenerateException(String.format("Bad configuration - No parameter with key '%s' found in random block with identifier '%s' referenced by '%s->%s'", string3, string, string2, string3));
                        }
                        arrayList.add(string);
                    }
                }
            }
            if ((object = element2.getChildren()) == null) continue;
            this.getIdentifiers(element2, arrayList, hashMap, bl);
        }
    }

    public static void checkUniqueRandomIdentifiers(Element element, HashMap<String, Element> hashMap) throws GenerateException {
        String string = element.getName();
        if (string.equals("RandomGroups")) {
            return;
        }
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            String string2;
            Element element2 = (Element)list.get(i);
            List list2 = element2.getChildren();
            if ((element2.getName().equals("Item") || element2.getName().equals("Param")) && (string2 = element2.getAttributeValue("generate")) != null && string2.equals("random")) {
                Element element3 = element2.getName().equals("Item") ? element2 : element;
                String string3 = GeneratorBase.findIdentifierInParams(element3, true);
                if (!hashMap.containsKey(string3)) {
                    element3.setAttribute("isParameter", element2.getName().equals("Item") ? "false" : "true");
                    hashMap.put(string3, element3);
                } else if (hashMap.get(string3) != element3) {
                    throw new GenerateException(String.format("Bad configuration - Identification '%s' used in more than one random blocks!", string3));
                }
            }
            if ((list2 = element2.getChildren()) == null) continue;
            GeneratorBase.checkUniqueRandomIdentifiers(element2, hashMap);
        }
    }

    protected static String findIdentifierInParams(Element element, boolean bl) throws GenerateException {
        if (!element.getName().equals("Item")) {
            throw new GenerateException(String.format("Bad configuration - element is not Item, it is '%s'", element.getName()));
        }
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            String string = element2.getAttributeValue("key");
            if (string == null || !string.equals("#Identification#")) continue;
            return element2.getValue();
        }
        String string = element.getAttributeValue("key");
        if (string == null) {
            string = "Unknown";
        }
        if (bl) {
            throw new GenerateException(String.format("Bad configuration - Identification not found in item '%s'", string));
        }
        return null;
    }

    protected void findAndOrBlocks(Element element, RandomAndOrList randomAndOrList) throws GenerateException {
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            List list2 = element2.getChildren();
            if (element2.getName().equals("Item")) {
                Object object;
                String string = element2.getAttributeValue("key");
                if (string.equals("RND")) {
                    object = new RandomAndOr(element2);
                    randomAndOrList.add(object);
                } else if (string.startsWith("Random")) {
                    object = this.getRandomBlockId(element2);
                    randomAndOrList.setRAO(1, (String)object);
                } else if (string.startsWith("Same") || string.startsWith("Negate")) {
                    object = this.getRandomBlockId(element2);
                    randomAndOrList.setRAO(2, (String)object);
                }
            }
            if ((list2 = element2.getChildren()) == null) continue;
            this.findAndOrBlocks(element2, randomAndOrList);
        }
    }

    protected String getRandomBlockId(Element element) throws GenerateException {
        List list = element.getChildren("Param");
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            if (!element2.getAttributeValue("key").equals("#Identification#")) continue;
            return element2.getValue();
        }
        throw new GenerateException("No parameter found for Random block!");
    }

    protected String getRandomBlockParamValue(Element element, String string) {
        List list = element.getChildren("Param");
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            if (!element2.getAttributeValue("key").equals(string)) continue;
            return element2.getValue();
        }
        return null;
    }

    protected Element getRandomBlockParamElement(Element element, String string) {
        List list = element.getChildren("Param");
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            if (!element2.getAttributeValue("key").equals(string)) continue;
            return element2;
        }
        return null;
    }
}


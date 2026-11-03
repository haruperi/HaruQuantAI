/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.XMLUtil
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  it.unimi.dsi.fastutil.ints.IntIterator
 *  it.unimi.dsi.fastutil.ints.IntSet
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  it.unimi.dsi.fastutil.objects.ObjectListIterator
 *  org.jdom2.Attribute
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gp.strategies;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.Blocks;
import com.strategyquant.tradinglib.IBlock;
import com.strategyquant.tradinglib.NegatersList;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.generator.GenerateException;
import com.strategyquant.tradinglib.generator.Negaters;
import com.strategyquant.tradinglib.gp.AbstractFactory;
import com.strategyquant.tradinglib.gp.GPIDs;
import com.strategyquant.tradinglib.gp.IEvolutionaryOperator;
import com.strategyquant.tradinglib.gp.strategies.Node;
import com.strategyquant.tradinglib.task.settings.buildtype.BuildType;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.ints.IntIterator;
import it.unimi.dsi.fastutil.ints.IntSet;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import it.unimi.dsi.fastutil.objects.ObjectListIterator;
import java.util.ArrayList;
import java.util.List;
import org.jdom2.Attribute;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class FixNonRandomBlocks
implements IEvolutionaryOperator<Node> {
    private static final Logger Log = LoggerFactory.getLogger((String)"FixNonRandomBlocks");
    private final BuildType buildType;
    private NegatersList negatersList;

    public FixNonRandomBlocks(BuildType buildType) throws GenerateException {
        this.buildType = buildType;
        this.negatersList = Negaters.list();
    }

    @Override
    public List<Node> apply(List<Node> list, IRandomGenerator iRandomGenerator, AbstractFactory<Node> abstractFactory, int n, int n2) throws Exception {
        ArrayList<Node> arrayList = new ArrayList<Node>(list.size());
        for (int i = 0; i < list.size(); ++i) {
            Node node = list.get(i);
            if (this.shouldBeFixed(node)) {
                GPIDs gPIDs = node.getGPIDs();
                StrategyBase strategyBase = null;
                strategyBase = this.fixNonRandomElements(strategyBase, node, gPIDs.toString());
                this.fixFuzzyConditions(strategyBase, node, gPIDs.toString());
            }
            arrayList.add(node);
        }
        return arrayList;
    }

    private boolean shouldBeFixed(Node node) {
        if (!node.isModified()) {
            return false;
        }
        return this.buildType.entrySymmetry || this.buildType.exitSymmetry;
    }

    private StrategyBase fixNonRandomElements(StrategyBase strategyBase, Node node, String string) throws Exception {
        Int2ObjectOpenHashMap int2ObjectOpenHashMap = new Int2ObjectOpenHashMap();
        Int2ObjectOpenHashMap int2ObjectOpenHashMap2 = new Int2ObjectOpenHashMap();
        Int2ObjectOpenHashMap int2ObjectOpenHashMap3 = new Int2ObjectOpenHashMap();
        Element element = node.getStrategy();
        this.findAllGeneratedElements(element, (Int2ObjectOpenHashMap<ObjectArrayList<Element>>)int2ObjectOpenHashMap, (Int2ObjectOpenHashMap<ObjectArrayList<Element>>)int2ObjectOpenHashMap2, (Int2ObjectOpenHashMap<ObjectArrayList<Element>>)int2ObjectOpenHashMap3);
        IntSet intSet = int2ObjectOpenHashMap.keySet();
        IntIterator intIterator = intSet.iterator();
        while (intIterator.hasNext()) {
            int n = (Integer)intIterator.next();
            ObjectArrayList objectArrayList = (ObjectArrayList)int2ObjectOpenHashMap.get(n);
            for (Element element2 : objectArrayList) {
                Element element3;
                Element element42;
                ObjectArrayList objectArrayList2;
                String string2 = element2.getAttributeValue("randomId");
                if (string2 == null) continue;
                if (int2ObjectOpenHashMap2.containsKey(n)) {
                    objectArrayList2 = (ObjectArrayList)int2ObjectOpenHashMap2.get(n);
                    for (Element element42 : objectArrayList2) {
                        element3 = element2.clone();
                        if (!this.compatibleBlocks(element42 = this.specialHandlingNumberParams(element42, element3), element3)) continue;
                        this.replaceElement(element42, element3, "same", string2);
                    }
                }
                if (!int2ObjectOpenHashMap3.containsKey(n)) continue;
                if (strategyBase == null) {
                    strategyBase = StrategyBase.createXmlStrategy(node.getStrategy(), "FixNonRandomBlocksStrategy");
                }
                if ((objectArrayList2 = this.negate(element2, strategyBase)) == null) continue;
                this.fixMagicNumber((Element)objectArrayList2, element2);
                ObjectListIterator objectListIterator = (ObjectArrayList)int2ObjectOpenHashMap3.get(n);
                element42 = objectListIterator.iterator();
                while (element42.hasNext()) {
                    element3 = (Element)element42.next();
                    if (!this.compatibleBlocks(element3 = this.specialHandlingNumberParams(element3, (Element)objectArrayList2), (Element)objectArrayList2)) continue;
                    this.replaceElement(element3, (Element)objectArrayList2, "negated", string2);
                }
            }
        }
        return strategyBase;
    }

    private Element specialHandlingNumberParams(Element element, Element element2) {
        String string = element.getName();
        String string2 = element2.getName();
        if (!string.equals("Item") || !string2.equals("Param")) {
            return element;
        }
        String string3 = element2.getAttributeValue("key");
        Element element3 = XMLUtil.getItemParameterNoException((Element)element, (String)string3);
        if (element3 != null) {
            return element3;
        }
        return element;
    }

    private boolean compatibleBlocks(Element element, Element element2) {
        String string;
        String string2 = element.getName();
        if (!string2.equals(string = element.getName())) {
            return false;
        }
        if (string2.equals("Item")) {
            return this.compatibleItemBlocks(element, element2);
        }
        return this.compatibleParamBlocks(element, element2);
    }

    private boolean compatibleParamBlocks(Element element, Element element2) {
        String string = element.getAttributeValue("key");
        String string2 = element2.getAttributeValue("key");
        String string3 = element.getAttributeValue("type");
        String string4 = element2.getAttributeValue("type");
        if (string3 == null || string4 == null) {
            return false;
        }
        if (!string.equals(string2)) {
            return false;
        }
        return string3.equals(string4);
    }

    private boolean compatibleItemBlocks(Element element, Element element2) {
        String string = element.getAttributeValue("key");
        String string2 = element2.getAttributeValue("key");
        String string3 = element.getAttributeValue("returnType");
        String string4 = element2.getAttributeValue("returnType");
        if (string3 == null || string4 == null) {
            return !(!string.equals("AND") && !string.equals("OR") || !string2.equals("AND") && !string2.equals("OR"));
        }
        if (string3.equals(string4)) {
            return true;
        }
        if (string3.equals("pricerange") && (string4.equals("price") || string4.equals("range"))) {
            return true;
        }
        return string4.equals("pricerange") && (string3.equals("price") || string3.equals("range"));
    }

    private void fixMagicNumber(Element element, Element element2) throws Exception {
        Element element3 = null;
        if (element2 != null) {
            element3 = XMLUtil.getItemParameter((Element)element2, (String)"#MagicNumber#", (boolean)false);
        }
        Element element4 = null;
        if (element != null) {
            element4 = XMLUtil.getItemParameter((Element)element, (String)"#MagicNumber#", (boolean)false);
        }
        if (element3 != null && element4 != null) {
            List list = element3.getAttributes();
            for (int i = 0; i < list.size(); ++i) {
                Attribute attribute = (Attribute)list.get(i);
                element4.setAttribute(attribute.clone());
            }
            element4.setText(element3.getText());
        }
    }

    private void replaceElement(Element element, Element element2, String string, String string2) throws Exception {
        String string3;
        if (!element.getName().equals(element2.getName())) {
            if (element.getName().equals("Param") && element2.getName().equals("Item")) {
                string3 = element.getAttributeValue("key");
                if (string3 == null) {
                    return;
                }
                if ((element2 = XMLUtil.getItemParameter((Element)element2, (String)string3, (boolean)false)) == null) {
                    return;
                }
            } else {
                return;
            }
        }
        if (element.getName().equals("Param")) {
            string3 = element.getAttributeValue("key");
            if (string3 == null) {
                return;
            }
            String string4 = element2.getAttributeValue("key");
            if (string4 == null) {
                return;
            }
            if (!string4.equals(string3)) {
                return;
            }
        }
        element2 = element2.clone();
        this.fixGeneratedAttribute(element2, string, string2, true);
        string3 = element.getParentElement();
        if (string3 == null) {
            return;
        }
        int n = this.findChildIndex((Element)string3, element);
        if (n < 0) {
            throw new Exception("Cannot find child!");
        }
        string3.setContent(n, (Content)element2);
    }

    private int findChildIndex(Element element, Element element2) {
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            Element element3 = (Element)list.get(i);
            if (element3 != element2) continue;
            return i;
        }
        return -1;
    }

    private void fixGeneratedAttribute(Element element, String string, String string2, boolean bl) {
        Object object;
        if (bl) {
            element.setAttribute("generated", string);
            element.setAttribute("randomId", string2);
        } else {
            object = element.getAttributeValue("randomId");
            String string3 = element.getAttributeValue("generated");
            if (object != null && string3 != null && ((String)object).equals(string2)) {
                element.setAttribute("generated", string);
            }
        }
        object = element.getChildren();
        for (int i = 0; i < object.size(); ++i) {
            Element element2 = (Element)object.get(i);
            String string4 = element2.getAttributeValue("randomId");
            String string5 = element2.getAttributeValue("generated");
            if (string4 != null && string5 != null && string4.equals(string2)) {
                element2.setAttribute("generated", string);
            }
            this.fixGeneratedAttribute(element2, string, string2, false);
        }
    }

    private Element negate(Element element, StrategyBase strategyBase) throws BlockDefinitionException {
        String string = element.getAttributeValue("key");
        try {
            IBlock iBlock = Blocks.getBlockObject(string, strategyBase, element);
            IBlock iBlock2 = this.negatersList.negate(iBlock, strategyBase);
            Element element2 = Blocks.generateBlockTreeXml(iBlock2);
            return element2;
        }
        catch (BlockDefinitionException blockDefinitionException) {
            Log.debug("Cannot find block (non serious issue): " + string);
            return null;
        }
    }

    private void findAllGeneratedElements(Element element, Int2ObjectOpenHashMap<ObjectArrayList<Element>> int2ObjectOpenHashMap, Int2ObjectOpenHashMap<ObjectArrayList<Element>> int2ObjectOpenHashMap2, Int2ObjectOpenHashMap<ObjectArrayList<Element>> int2ObjectOpenHashMap3) throws Exception {
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            ObjectArrayList objectArrayList;
            Element element2 = (Element)list.get(i);
            String string = element2.getAttributeValue("generated");
            if (string == null) {
                this.findAllGeneratedElements(element2, int2ObjectOpenHashMap, int2ObjectOpenHashMap2, int2ObjectOpenHashMap3);
                continue;
            }
            String string2 = element2.getAttributeValue("randomId");
            if (string2 == null) {
                string2 = this.getRandomIdFromChildren(element2);
            }
            if (string2 == null) {
                this.findAllGeneratedElements(element2, int2ObjectOpenHashMap, int2ObjectOpenHashMap2, int2ObjectOpenHashMap3);
                continue;
            }
            if (!this.buildType.exitSymmetry && string2.equals("RandomConditionLongExit")) {
                this.findAllGeneratedElements(element2, int2ObjectOpenHashMap, int2ObjectOpenHashMap2, int2ObjectOpenHashMap3);
                continue;
            }
            if (!this.buildType.entrySymmetry && string2.equals("RandomConditionLong")) {
                this.findAllGeneratedElements(element2, int2ObjectOpenHashMap, int2ObjectOpenHashMap2, int2ObjectOpenHashMap3);
                continue;
            }
            int n = string2.hashCode();
            if (string.equals("random")) {
                objectArrayList = (ObjectArrayList)int2ObjectOpenHashMap.get(n);
                if (objectArrayList == null) {
                    objectArrayList = new ObjectArrayList();
                }
                objectArrayList.add((Object)element2);
                int2ObjectOpenHashMap.put(n, (Object)objectArrayList);
            } else if (string.equals("same")) {
                objectArrayList = (ObjectArrayList)int2ObjectOpenHashMap2.get(n);
                if (objectArrayList == null) {
                    objectArrayList = new ObjectArrayList();
                }
                objectArrayList.add((Object)element2);
                int2ObjectOpenHashMap2.put(n, (Object)objectArrayList);
            } else if (string.startsWith("negated")) {
                objectArrayList = (ObjectArrayList)int2ObjectOpenHashMap3.get(n);
                if (objectArrayList == null) {
                    objectArrayList = new ObjectArrayList();
                }
                objectArrayList.add((Object)element2);
                int2ObjectOpenHashMap3.put(n, (Object)objectArrayList);
            } else {
                throw new Exception(String.format("Unknown generated attribute '%s'", string));
            }
            this.findAllGeneratedElements(element2, int2ObjectOpenHashMap, int2ObjectOpenHashMap2, int2ObjectOpenHashMap3);
        }
    }

    private String getRandomIdFromChildren(Element element) {
        Element element2 = XMLUtil.getItemParameterNoException((Element)element, (String)"#Identification#");
        if (element2 != null) {
            return element2.getText();
        }
        return null;
    }

    private void fixFuzzyConditions(StrategyBase strategyBase, Node node, String string) throws Exception {
        Element element = node.getStrategy();
        Int2ObjectOpenHashMap<Element> int2ObjectOpenHashMap = this.findSignals(element);
        if (int2ObjectOpenHashMap != null) {
            strategyBase = this.fixLongShortConditions(strategyBase, element, int2ObjectOpenHashMap, "33333333-1111-1111-3333-333333333333", "33333333-2222-1111-3333-333333333333");
            strategyBase = this.fixLongShortConditions(strategyBase, element, int2ObjectOpenHashMap, "33333333-1111-2222-3333-333333333333", "33333333-1111-2222-3333-333333333333");
        }
    }

    private StrategyBase fixLongShortConditions(StrategyBase strategyBase, Element element, Int2ObjectOpenHashMap<Element> int2ObjectOpenHashMap, String string, String string2) throws Exception {
        if (!int2ObjectOpenHashMap.containsKey(string.hashCode()) || !int2ObjectOpenHashMap.containsKey(string2.hashCode())) {
            return strategyBase;
        }
        Element element2 = (Element)int2ObjectOpenHashMap.get(string.hashCode());
        Element element3 = (Element)int2ObjectOpenHashMap.get(string2.hashCode());
        List list = element2.getChildren();
        List list2 = element3.getChildren();
        if (list.size() != list2.size()) {
            return strategyBase;
        }
        for (int i = 0; i < list.size(); ++i) {
            Element element4 = (Element)list.get(i);
            Element element5 = (Element)list2.get(i);
            String string3 = element4.getAttributeValue("randomId");
            if (string3 == null) continue;
            if (strategyBase == null) {
                strategyBase = StrategyBase.createXmlStrategy(element, "FixNonRandomBlocksStrategy");
            }
            Element element6 = this.negate(element4, strategyBase);
            this.fixMagicNumber(element6, element4);
            this.replaceElement(element5, element6, "negated", string3);
        }
        return strategyBase;
    }

    private Int2ObjectOpenHashMap<Element> findSignals(Element element) {
        Int2ObjectOpenHashMap int2ObjectOpenHashMap = new Int2ObjectOpenHashMap();
        List list = element.getChild("Strategy").getChild("Rules").getChild("Events").getChildren("Event");
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            List list2 = element2.getChildren("Rule");
            for (int j = 0; j < list2.size(); ++j) {
                Element element3 = (Element)list2.get(j);
                String string = element3.getAttributeValue("type");
                if (string == null || !string.equals("SignalFuzzy")) continue;
                List list3 = element3.getChild("signals").getChildren("signal");
                for (int k = 0; k < list3.size(); ++k) {
                    Element element4 = (Element)list3.get(k);
                    String string2 = element4.getAttributeValue("variable");
                    if (string2 == null) continue;
                    int n = string2.hashCode();
                    int2ObjectOpenHashMap.put(n, (Object)element4);
                }
            }
        }
        if (int2ObjectOpenHashMap.size() == 0) {
            return null;
        }
        return int2ObjectOpenHashMap;
    }

    private List<Element> getFuzzyConditions(Element element, String string) {
        return null;
    }
}


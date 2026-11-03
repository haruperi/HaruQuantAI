/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  it.unimi.dsi.fastutil.ints.Int2IntOpenHashMap
 *  org.jdom2.Attribute
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gp.strategies;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.blocks.random.RandomValueConfig;
import com.strategyquant.tradinglib.gp.AbstractFactory;
import com.strategyquant.tradinglib.gp.GPIDs;
import com.strategyquant.tradinglib.gp.IEvolutionaryOperator;
import com.strategyquant.tradinglib.gp.SelectedBlockGroups;
import com.strategyquant.tradinglib.gp.strategies.BuildSettings;
import com.strategyquant.tradinglib.gp.strategies.GenEvoChecker;
import com.strategyquant.tradinglib.gp.strategies.Node;
import com.strategyquant.tradinglib.gp.strategies.NodeElement;
import com.strategyquant.tradinglib.gp.strategies.NodeFactory;
import it.unimi.dsi.fastutil.ints.Int2IntOpenHashMap;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;
import org.jdom2.Attribute;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class NodeCrossover
implements IEvolutionaryOperator<Node> {
    public static final Logger Log = LoggerFactory.getLogger((String)"NodeCrossover");
    private final double crossoverProbability;
    private final int crossoverPoints;
    private boolean LimitSLPTRRR;
    private double LimitSLPTRRRFromCoef;
    private double LimitSLPTRRRToCoef;
    private SelectedBlockGroups selectedBlockGroups;

    public NodeCrossover(double d, int n, BuildSettings buildSettings, SelectedBlockGroups selectedBlockGroups) {
        this.crossoverProbability = d;
        this.crossoverPoints = n;
        this.selectedBlockGroups = selectedBlockGroups;
        SettingsMap settingsMap = buildSettings.getBuildSettingsMap();
        this.LimitSLPTRRR = settingsMap.getBoolean("LimitSLPTRRR");
        if (this.LimitSLPTRRR) {
            double d2 = settingsMap.getInt("LimitSLPTRRRFrom");
            double d3 = settingsMap.getInt("LimitSLPTRRRTo");
            this.LimitSLPTRRRFromCoef = 1.0 / (d2 / 100.0);
            this.LimitSLPTRRRToCoef = 1.0 / (d3 / 100.0);
        }
    }

    @Override
    public List<Node> apply(List<Node> list, IRandomGenerator iRandomGenerator, AbstractFactory<Node> abstractFactory, int n, int n2) throws Exception {
        List<Node> list2 = new ArrayList<Node>(list.size());
        Int2IntOpenHashMap int2IntOpenHashMap = new Int2IntOpenHashMap();
        int n3 = list.size();
        NodeFactory nodeFactory = (NodeFactory)abstractFactory;
        int n4 = 3;
        do {
            list2 = this._apply(list, iRandomGenerator, list2, n, n2, nodeFactory);
            if (--n4 <= 0) continue;
            this.removeDuplicates(list2, n3, int2IntOpenHashMap);
        } while (list2.size() < n3 && n4 > 0);
        return list2;
    }

    private void removeDuplicates(List<Node> list, int n, Int2IntOpenHashMap int2IntOpenHashMap) {
        int n2 = (int)((double)n * 0.2);
        n2 = Math.min(10, n2);
        n2 = Math.max(2, n2);
        Iterator<Node> iterator = list.iterator();
        while (iterator.hasNext()) {
            Node node = iterator.next();
            int n3 = node.getHash();
            int n4 = 0;
            if (int2IntOpenHashMap.containsKey(n3)) {
                n4 = int2IntOpenHashMap.get(n3);
            }
            if (n4 >= n2) {
                iterator.remove();
                continue;
            }
            int2IntOpenHashMap.put(n3, ++n4);
        }
    }

    public List<Node> _apply(List<Node> list, IRandomGenerator iRandomGenerator, List<Node> list2, int n, int n2, NodeFactory nodeFactory) throws Exception {
        ArrayList<Node> arrayList = new ArrayList<Node>(list);
        Collections.shuffle(arrayList);
        int n3 = arrayList.size();
        Iterator iterator = arrayList.iterator();
        while (iterator.hasNext() && list2.size() < n3) {
            Node node = (Node)iterator.next();
            if (iterator.hasNext()) {
                Node node2 = (Node)iterator.next();
                int n4 = 0;
                if (iRandomGenerator.probability(this.crossoverProbability)) {
                    n4 = 1 + iRandomGenerator.nextInt(this.crossoverPoints);
                }
                if (n4 > 0) {
                    List<Node> list3 = this.mate(node, node2, n4, iRandomGenerator, n, n2, nodeFactory);
                    list2.addAll(list3);
                    continue;
                }
                list2.add(node);
                list2.add(node2);
                continue;
            }
            list2.add(node);
        }
        if (list2.size() > n3) {
            list2.remove(list2.size() - 1);
        }
        return list2;
    }

    public List<Node> mate(Node node, Node node2, int n, IRandomGenerator iRandomGenerator, int n2, int n3, NodeFactory nodeFactory) throws Exception {
        Node node3;
        Node node4;
        int n4 = 0;
        ArrayList<Node> arrayList = new ArrayList<Node>(2);
        Element element = node.getStrategy().clone();
        Element element2 = node2.getStrategy().clone();
        int n5 = node.getHash();
        int n6 = node2.getHash();
        GPIDs gPIDs = node.getGPIDs();
        GPIDs gPIDs2 = node.getGPIDs();
        boolean bl = false;
        if (this.makeCrossover(element, element2, n, iRandomGenerator, n4, nodeFactory)) {
            bl = true;
        }
        if (!bl) {
            node4 = node.clone();
            node3 = node2.clone();
        } else {
            GPIDs gPIDs3;
            int n7 = XMLUtil.xmlToStringRaw((Element)element).hashCode();
            int n8 = XMLUtil.xmlToStringRaw((Element)element2).hashCode();
            String string = node.getGPIDs().toShortString();
            String string2 = node2.getGPIDs().toShortString();
            if (n7 == n5) {
                node4 = node.clone();
            } else if (n7 == n6) {
                node4 = node.clone();
            } else {
                node4 = new Node(element);
                gPIDs3 = new GPIDs();
                gPIDs3.islandIndex = n2;
                gPIDs3.generationIndex = n3;
                gPIDs3.generationType = "Crossover";
                gPIDs3.parent1 = string;
                gPIDs3.parent2 = string2;
                node4.setGPIDs(gPIDs3);
                node4.setModified();
            }
            if (n8 == n5) {
                node3 = node.clone();
            } else if (n8 == n6) {
                node3 = node.clone();
            } else {
                node3 = new Node(element2);
                gPIDs3 = new GPIDs();
                gPIDs3.islandIndex = n2;
                gPIDs3.generationIndex = n3;
                gPIDs3.generationType = "Crossover";
                gPIDs3.parent1 = string;
                gPIDs3.parent2 = string2;
                node3.setGPIDs(gPIDs3);
                node3.setModified();
            }
        }
        arrayList.add(node4);
        arrayList.add(node3);
        return arrayList;
    }

    private boolean checkBadFormula(Element element) {
        ArrayList arrayList = new ArrayList();
        XMLUtil.findAllWithKey((Element)element, (String)"Param", (String)"#StopLoss.StopLoss#", arrayList);
        for (int i = 0; i < arrayList.size(); ++i) {
            Element element2 = (Element)arrayList.get(i);
            if (element2.getChildren().size() != 0) continue;
            return true;
        }
        return false;
    }

    private boolean makeCrossover(Element element, Element element2, int n, IRandomGenerator iRandomGenerator, int n2, NodeFactory nodeFactory) throws Exception {
        ArrayList<NodeElement> arrayList = new ArrayList<NodeElement>();
        ArrayList<NodeElement> arrayList2 = new ArrayList<NodeElement>();
        this.recognizeReplacableElements(element, arrayList, false);
        this.recognizeReplacableElements(element2, arrayList2, false);
        if (arrayList.isEmpty() || arrayList2.isEmpty()) {
            return false;
        }
        int n3 = arrayList.size() * 2;
        int n4 = 0;
        int n5 = 0;
        while (true) {
            ++n2;
            ++n5;
            if (--n3 <= 0 || n4 >= n || arrayList.size() == 0 || arrayList2.size() == 0) break;
            int n6 = iRandomGenerator.nextInt(arrayList.size());
            NodeElement nodeElement = arrayList.get(n6);
            ArrayList<NodeElement> arrayList3 = this.findCompatibleElements(nodeElement, arrayList2);
            if (arrayList3 == null) {
                this.removeFromReplacable(arrayList, nodeElement);
                continue;
            }
            int n7 = iRandomGenerator.nextInt(arrayList3.size());
            NodeElement nodeElement2 = arrayList3.get(n7);
            this.replaceElements(nodeElement, nodeElement2);
            ++n4;
            this.removeFromReplacable(arrayList, nodeElement);
            this.removeFromReplacable(arrayList2, nodeElement2);
        }
        if (n4 > 0) {
            if (GenEvoChecker.fixZeroPeriodsAndExits(element) == null) {
                return false;
            }
            if (GenEvoChecker.fixZeroPeriodsAndExits(element2) == null) {
                return false;
            }
            if (!GenEvoChecker.passedRRRCheck(element, this.LimitSLPTRRR, this.LimitSLPTRRRToCoef, this.LimitSLPTRRRFromCoef)) {
                return false;
            }
            if (!GenEvoChecker.passedRRRCheck(element2, this.LimitSLPTRRR, this.LimitSLPTRRRToCoef, this.LimitSLPTRRRFromCoef)) {
                return false;
            }
            if (!this.selectedBlockGroups.passed(element, false)) {
                return false;
            }
            return this.selectedBlockGroups.passed(element2, false);
        }
        return false;
    }

    private void logReplacableElements(ArrayList<NodeElement> arrayList, String string) {
        String string2 = "";
        for (NodeElement nodeElement : arrayList) {
            string2 = string2 + "------------------------------------\n";
            string2 = string2 + XMLUtil.elementToString((Element)nodeElement.element);
            string2 = string2 + "------------------------------------\n";
        }
        SQUtils.stringToFile((String)(MainApp.getDataPath() + "tests/tmp/generated/" + string), (String)string2);
    }

    private void removeFromReplacable(ArrayList<NodeElement> arrayList, NodeElement nodeElement) {
        arrayList.remove(nodeElement);
        Iterator<NodeElement> iterator = arrayList.iterator();
        while (iterator.hasNext()) {
            NodeElement nodeElement2 = iterator.next();
            if (nodeElement2 == nodeElement) {
                iterator.remove();
                continue;
            }
            if (nodeElement2.elementParent != nodeElement.element) continue;
            iterator.remove();
        }
    }

    private void replaceElements(NodeElement nodeElement, NodeElement nodeElement2) {
        NodeElement nodeElement3 = new NodeElement(nodeElement.element.clone(), nodeElement.elementParent);
        this.replaceElement(nodeElement, nodeElement2);
        this.replaceElement(nodeElement2, nodeElement3);
    }

    private void replaceElement(NodeElement nodeElement, NodeElement nodeElement2) {
        String string;
        int n;
        List list = nodeElement.element.getAttributes();
        int n2 = list.size();
        for (n = 0; n < n2; ++n) {
            string = ((Attribute)list.get(0)).getName();
            if (string.equals("generated") || string.equals("randomId")) continue;
            nodeElement.element.removeAttribute(string);
        }
        list = nodeElement2.element.getAttributes();
        n2 = list.size();
        for (n = 0; n < n2; ++n) {
            string = ((Attribute)list.get(n)).getName();
            if (string.equals("generated") || string.equals("randomId")) continue;
            nodeElement.element.setAttribute(string, ((Attribute)list.get(n)).getValue());
        }
        nodeElement.element.removeContent();
        List list2 = nodeElement2.element.getChildren();
        if (list2.size() > 0) {
            while (list2.size() > 0) {
                nodeElement.element.addContent((Content)((Element)list2.get(0)).detach());
            }
        } else if (nodeElement.element.getName().equals("Param")) {
            nodeElement.element.setText(nodeElement2.element.getText());
        }
    }

    private void recognizeReplacableElements(Element element, ArrayList<NodeElement> arrayList, boolean bl) {
        Object object;
        String string;
        Object object2;
        String string2 = element.getName();
        if (string2.equals("Item")) {
            object2 = element.getAttributeValue("generated");
            if (object2 != null && ((String)object2).equals("random") && (string = element.getAttributeValue("returnType")) != null && (string.equals("boolean") || string.equals("price") || string.equals("number"))) {
                object = element.getAttributeValue("key");
                arrayList.add(new NodeElement(element));
                bl = true;
            }
        } else if (string2.equals("Param")) {
            String string3;
            object2 = element.getAttributeValue("generated");
            if ((bl || object2 != null && ((String)object2).equals("random")) && !(string = element.getAttributeValue("key")).equals("#Shift#") && !string.equals("#Direction#") && !string.contains("Magic") && (object = element.getAttributeValue("type")) != null && (((String)object).equals("int") || ((String)object).equals("double") || ((String)object).equals("boolean")) && (string3 = element.getAttributeValue("variable")) == null) {
                arrayList.add(new NodeElement(element));
            }
        }
        object2 = element.getChildren();
        if (object2 != null && object2.size() > 0) {
            for (int i = 0; i < object2.size(); ++i) {
                object = (Element)object2.get(i);
                this.recognizeReplacableElements((Element)object, arrayList, bl);
            }
        }
    }

    private ArrayList<NodeElement> findCompatibleElements(NodeElement nodeElement, ArrayList<NodeElement> arrayList) {
        ArrayList<NodeElement> arrayList2 = null;
        boolean bl = nodeElement.element.getName().equals("Item");
        String string = nodeElement.element.getAttributeValue("key");
        for (int i = 0; i < arrayList.size(); ++i) {
            String string2;
            String string3;
            String string4;
            NodeElement nodeElement2 = arrayList.get(i);
            if (bl) {
                if (!nodeElement2.element.getName().equals("Item") || !(string4 = nodeElement.element.getAttributeValue("returnType")).equals(string3 = nodeElement2.element.getAttributeValue("returnType"))) continue;
                arrayList2 = this.addToCompatibleElements(arrayList2, nodeElement2);
                continue;
            }
            string4 = nodeElement2.element.getAttributeValue("key");
            if (!string.equals(string4) || !(string3 = nodeElement.element.getAttributeValue("type")).equals(string2 = nodeElement2.element.getAttributeValue("type"))) continue;
            String string5 = nodeElement.element.getAttributeValue("randomId");
            String string6 = nodeElement2.element.getAttributeValue("randomId");
            if (string5 != null && (string6 == null || !string5.equals(string6)) || !this.randomRangedValuesMatch(nodeElement.element, nodeElement2.element, string3)) continue;
            arrayList2 = this.addToCompatibleElements(arrayList2, nodeElement2);
        }
        return arrayList2;
    }

    private boolean randomRangedValuesMatch(Element element, Element element2, String string) {
        String string2 = element.getAttributeValue("randomValue");
        if (string2 == null || string2.isBlank()) {
            return true;
        }
        try {
            double d = Double.MIN_VALUE;
            RandomValueConfig randomValueConfig = null;
            String string3 = element2.getText();
            if (string3 != null && !string3.isBlank()) {
                if (string.equals("double")) {
                    d = Double.parseDouble(string3);
                    randomValueConfig = RandomValueConfig.parseRandomValue(string2, true);
                } else if (string.equals("int")) {
                    d = Integer.parseInt(string3);
                    randomValueConfig = RandomValueConfig.parseRandomValue(string2, true);
                }
            }
            if (randomValueConfig != null && d != Double.MIN_VALUE) {
                boolean bl = randomValueConfig.isInValidRange(d);
                if (!bl) {
                    // empty if block
                }
                return bl;
            }
        }
        catch (Exception exception) {
            Log.error("Exception ", (Throwable)exception);
        }
        return true;
    }

    private ArrayList<NodeElement> addToCompatibleElements(ArrayList<NodeElement> arrayList, NodeElement nodeElement) {
        if (arrayList == null) {
            arrayList = new ArrayList();
        }
        arrayList.add(nodeElement);
        return arrayList;
    }
}


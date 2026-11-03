/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gp.strategies;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.generator.RulePart;
import com.strategyquant.tradinglib.generator.RuleType;
import com.strategyquant.tradinglib.gp.AbstractFactory;
import com.strategyquant.tradinglib.gp.strategies.Node;
import com.strategyquant.tradinglib.gp.strategies.NodeFactory;
import java.util.List;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class GeneratedObject {
    public static final Logger Log = LoggerFactory.getLogger((String)"GeneratedObject");
    private static final int TypeItem = 1;
    private static final int TypeParam = 2;
    private int GID;
    private int parentGID;
    private Element el;
    private Element elParent;
    private int type;
    private static final String NumberParamElement = "<Param key=\"#Number#\" name=\"Number\" type=\"double\" defaultValue=\"0\" controlType=\"jspinner\" minValue=\"-999999999\" maxValue=\"999999999\" step=\"1\" builderStep=\"1\">XXXXX</Param>";

    public GeneratedObject(int n, Element element) {
        this(n, element, 0);
    }

    public GeneratedObject(int n, Element element, int n2) {
        this.GID = n;
        this.parentGID = n2;
        this.el = element;
        switch (element.getName()) {
            case "Item": {
                this.type = 1;
                break;
            }
            case "Param": {
                this.type = 2;
                break;
            }
            default: {
                throw new IllegalArgumentException("Element is not Item neither Param!");
            }
        }
        if (this.type == 2) {
            String string = element.getParentElement();
            if (string.getName().equals("Item")) {
                this.elParent = string;
            } else if ((string = string.getParentElement()).getName().equals("Item")) {
                this.elParent = string;
            } else {
                throw new IllegalArgumentException("Cannot find parent element of this Param!");
            }
        }
    }

    public Element mutate(IRandomGenerator iRandomGenerator, AbstractFactory<Node> abstractFactory) throws Exception {
        String string;
        Element element;
        Element element2;
        String string2;
        NodeFactory nodeFactory;
        if (this.el == null) {
            Log.error("el is null, this shouldn't happen!");
            return null;
        }
        String string3 = this.el.getAttributeValue("type");
        if (string3 != null && string3.equals("data")) {
            return null;
        }
        String string4 = this.el.getAttributeValue("key");
        if (string4 == null) {
            Log.error("key is null, this shouldn't happen! XML: {}", (Object)XMLUtil.elementToString((Element)this.el));
            return null;
        }
        if (string4.equals("#Comment#") || string4.equals("#Size#") || string4.equals("#Symbol#")) {
            return null;
        }
        if (string4.equals("#Number#") && (nodeFactory = this.el.getParentElement()) != null && (nodeFactory = nodeFactory.getParentElement()) != null && ((string2 = (element2 = nodeFactory.getParentElement()).getAttributeValue("key")).equals("IsGreater") || string2.equals("IsLower") || string2.equals("IsGreaterOrEqual") || string2.equals("IsLowerOrEqual") || string2.equals("Equals") || string2.equals("NotEquals")) && (element = this.getParameter(element2, "#Left#")) != null && this.isBarTimeBlock(string = element.getAttributeValue("key"))) {
            int n = this.generateCorrectRandomNumber(iRandomGenerator, string);
            String string5 = NumberParamElement.replace("XXXXX", Integer.toString(n));
            return XMLUtil.stringToElement((String)string5);
        }
        nodeFactory = (NodeFactory)abstractFactory;
        if (this.el.getName().equals("Param")) {
            return this.mutateParam(iRandomGenerator, nodeFactory);
        }
        return this.mutateItem(iRandomGenerator, nodeFactory);
    }

    private int generateCorrectRandomNumber(IRandomGenerator iRandomGenerator, String string) {
        if (string.contains("Hour")) {
            return iRandomGenerator.nextInt(23);
        }
        if (string.contains("Minute")) {
            return iRandomGenerator.nextInt(59);
        }
        if (string.contains("DayOfWeek")) {
            return iRandomGenerator.nextInt(6);
        }
        return 0;
    }

    private Element getParameter(Element element, String string) {
        for (Element element2 : element.getChildren()) {
            String string2 = element2.getAttributeValue("key");
            if (string2 == null || !string2.equals(string)) continue;
            return element2.getChild("Item");
        }
        return null;
    }

    private boolean isBarTimeBlock(String string) {
        return string.contains("Hour") || string.contains("Minute") || string.contains("DayOfWeek");
    }

    private Element mutateItem(IRandomGenerator iRandomGenerator, NodeFactory nodeFactory) {
        return null;
    }

    private Element mutateParam(IRandomGenerator iRandomGenerator, NodeFactory nodeFactory) throws Exception {
        String string;
        String string2;
        int n;
        int n2;
        String string3 = this.elParent.getAttributeValue("randomId");
        if (string3 == null) {
            string3 = this.findRandomIdInSiblings();
        }
        if (string3 == null) {
            throw new IllegalArgumentException("randomId attribute not found in Param parent item or siblings!");
        }
        Element element = XMLUtil.copyElement((Element)this.elParent);
        Element element2 = nodeFactory.generateRandomBlock(string3, element, n2 = RulePart.recognizeRulePartFromParents(this.elParent), n = RuleType.recognizeRuleTypeFromParents(this.elParent));
        if (element2 == null) {
            return null;
        }
        Element element3 = XMLUtil.getItemParameter((Element)element2, (String)this.el.getAttributeValue("key"), (boolean)true);
        if (this.el.getAttributeValue("key").contains(".")) {
            string2 = this.getFormulaValues(this.el);
            string = this.getFormulaValues(element3);
        } else {
            string2 = this.el.getText();
            string = element3.getText();
        }
        if (string.equals(string2) && !string2.equals("")) {
            return null;
        }
        return element3;
    }

    private String findRandomIdInSiblings() {
        List list = this.elParent.getChildren("Param");
        for (int i = 0; i < list.size(); ++i) {
            Element element = (Element)list.get(i);
            String string = element.getAttributeValue("controlType");
            if (string == null || !string.equals("randomId")) continue;
            return element.getText();
        }
        return null;
    }

    private String getFormulaValues(Element element) {
        StringBuilder stringBuilder = new StringBuilder();
        this.getFormulaValuesRecursive(stringBuilder, element);
        return stringBuilder.toString();
    }

    private void getFormulaValuesRecursive(StringBuilder stringBuilder, Element element) {
        Object object;
        if (element.getName().equals("Formula")) {
            stringBuilder.append(element.getAttributeValue("key"));
            stringBuilder.append(",");
        }
        if (element.getName().equals("Param") && !((String)(object = element.getText())).equals("")) {
            stringBuilder.append((String)object);
            stringBuilder.append(",");
        }
        if ((object = element.getChildren()) != null && object.size() > 0) {
            for (int i = 0; i < object.size(); ++i) {
                Element element2 = (Element)object.get(i);
                this.getFormulaValuesRecursive(stringBuilder, element2);
            }
        }
    }

    public int getParentGID() {
        return this.parentGID;
    }

    public int getGID() {
        return this.GID;
    }

    public void print() {
        System.out.println(String.format("ID: %d, %s - %s, parent: %d", this.GID, this.el.getName(), this.el.getAttributeValue("key"), this.parentGID));
    }

    public Element getElement() {
        return this.el;
    }

    public Element getParentElement() {
        return this.elParent;
    }
}


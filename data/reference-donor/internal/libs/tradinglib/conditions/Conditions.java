/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.conditions;

import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.conditions.IConditionValue;
import com.strategyquant.tradinglib.conditions.NumericValue;
import java.util.ArrayList;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class Conditions {
    private static final Logger Log = LoggerFactory.getLogger(Conditions.class);
    protected ArrayList<Condition> conditions = new ArrayList();
    protected boolean conditionsFilled = false;
    protected boolean omit = false;

    public int count() {
        return this.conditions.size();
    }

    public void checkConditions(Element element) {
        Element element2 = element.getChild("Conditions");
        if (element2 != null) {
            String string = element2.getAttributeValue("conditionsType");
            if (string == null || !string.equals("use") && !string.equals("omit")) {
                string = "use";
            }
            this.omit = string.equals("omit");
            for (Element element3 : element2.getChildren("Condition")) {
                boolean bl = XMLUtil.tryGetBoolAttr((Element)element3, (String)"use");
                if (!bl) continue;
                Element element4 = element3.getChild("Left-Side");
                Element element5 = element3.getChild("Right-Side");
                Element element6 = element3.getChild("Comparator");
                if (element4 == null || element5 == null || element6 == null) continue;
                IConditionValue iConditionValue = this.loadConditionValue(element4);
                IConditionValue iConditionValue2 = this.loadConditionValue(element5);
                String string2 = element6.getAttributeValue("value");
                if (iConditionValue == null || iConditionValue2 == null) continue;
                Condition condition = new Condition(bl, iConditionValue, iConditionValue2, string2);
                this.conditions.add(condition);
                this.conditionsFilled = true;
            }
        } else {
            this.conditionsFilled = false;
            return;
        }
    }

    /*
     * Enabled force condition propagation
     * Lifted jumps to return sites
     */
    private IConditionValue loadConditionValue(Element element) {
        String string = element.getAttributeValue("valueType");
        IConditionValue iConditionValue = null;
        if (!string.equals("numeric")) return this.getConditionValue(string, element);
        Element element2 = element.getChild("Numeric-Value");
        if (element2 == null) return null;
        double d = XMLUtil.tryGetDoubleAttr((Element)element2, (String)"value");
        return new NumericValue(d);
    }

    public boolean fitsConditions(Object object) {
        if (this.conditionsFilled) {
            for (Condition condition : this.conditions) {
                try {
                    boolean bl = condition.isMet(object);
                    if ((this.omit || bl) && (!this.omit || !bl)) continue;
                    return false;
                }
                catch (Exception exception) {
                    Log.error("Error while checking condition", (Throwable)exception);
                }
            }
        }
        return true;
    }

    public boolean filled() {
        return this.conditionsFilled;
    }

    protected abstract IConditionValue getConditionValue(String var1, Element var2);
}


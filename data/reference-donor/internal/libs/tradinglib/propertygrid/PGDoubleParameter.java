/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.propertygrid;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.propertygrid.IPGParameter;
import org.jdom2.Element;

public class PGDoubleParameter
implements IPGParameter {
    private String key;
    private String name;
    private String category;
    private String activator;
    private String description;
    private double min;
    private double max;
    private double step;
    private double value;
    private int decimals;
    private String engine;

    @Override
    public String getKey() {
        return this.key;
    }

    public void setKey(String string) {
        this.key = string;
    }

    public String getDescription() {
        return this.description;
    }

    public void setDescription(String string) {
        this.description = string;
    }

    public double getMin() {
        return this.min;
    }

    public void setMin(double d) {
        this.min = d;
    }

    public double getMax() {
        return this.max;
    }

    public void setMax(double d) {
        this.max = d;
    }

    public double getStep() {
        return this.step;
    }

    public void setStep(double d) {
        this.step = d;
    }

    public double getValue() {
        return this.value;
    }

    public void setValue(double d) {
        this.value = d;
    }

    @Override
    public String getCategory() {
        return this.category;
    }

    @Override
    public void setCategory(String string) {
        this.category = string;
    }

    @Override
    public String getEngine() {
        return this.engine;
    }

    @Override
    public void setEngine(String string) {
        this.engine = string;
    }

    @Override
    public String getName() {
        return this.name;
    }

    public void setName(String string) {
        this.name = string;
    }

    public int getDecimals() {
        return this.decimals;
    }

    public void setDecimals(int n) {
        this.decimals = n;
    }

    public Element getXML() {
        Element element = new Element("Param");
        XMLUtil.trySetAttr((Element)element, (String)"key", (Object)this.key);
        XMLUtil.trySetAttr((Element)element, (String)"name", (Object)this.name);
        XMLUtil.trySetAttr((Element)element, (String)"dataType", (Object)String.valueOf(2));
        XMLUtil.trySetAttr((Element)element, (String)"min", (Object)String.valueOf(this.min));
        XMLUtil.trySetAttr((Element)element, (String)"max", (Object)String.format("%f", this.max));
        XMLUtil.trySetAttr((Element)element, (String)"step", (Object)String.valueOf(this.step));
        XMLUtil.trySetAttr((Element)element, (String)"value", (Object)String.valueOf(this.value));
        XMLUtil.trySetAttr((Element)element, (String)"description", (Object)this.description);
        if (this.activator != null) {
            XMLUtil.trySetAttr((Element)element, (String)"activator", (Object)this.activator);
        }
        XMLUtil.trySetAttr((Element)element, (String)"decimals", (Object)String.valueOf(this.decimals));
        return element;
    }

    public void setFromXML(Element element) {
        this.key = element.getAttributeValue("key");
        this.min = XMLUtil.tryGetDoubleAttr((Element)element, (String)"min");
        this.max = XMLUtil.tryGetDoubleAttr((Element)element, (String)"max");
        this.step = XMLUtil.tryGetDoubleAttr((Element)element, (String)"step");
        this.value = XMLUtil.tryGetDoubleAttr((Element)element, (String)"value");
        this.description = element.getAttributeValue("description");
        this.activator = element.getAttributeValue("activator");
        this.decimals = XMLUtil.tryGetIntAttr((Element)element, (String)"decimals");
    }

    @Override
    public int getType() {
        return 2;
    }

    @Override
    public String print() {
        return SQUtils.d2String((double)this.value, (int)this.decimals);
    }

    @Override
    public void setValue(String string) {
        this.value = Double.parseDouble(string);
    }

    @Override
    public String getActivator() {
        return this.activator;
    }

    @Override
    public void setActivator(String string) {
        this.activator = string;
    }
}


/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.propertygrid;

import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.propertygrid.IPGParameter;
import org.jdom2.Element;

public class PGBooleanParameter
implements IPGParameter {
    private String key;
    private String name;
    private String category;
    private String activator;
    private String description;
    private boolean value;
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

    public boolean getValue() {
        return this.value;
    }

    public void setValue(boolean bl) {
        this.value = bl;
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

    public Element getXML() {
        Element element = new Element("Param");
        XMLUtil.trySetAttr((Element)element, (String)"key", (Object)this.key);
        XMLUtil.trySetAttr((Element)element, (String)"name", (Object)this.name);
        XMLUtil.trySetAttr((Element)element, (String)"dataType", (Object)String.valueOf(3));
        XMLUtil.trySetAttr((Element)element, (String)"value", (Object)(this.value + ""));
        XMLUtil.trySetAttr((Element)element, (String)"description", (Object)this.description);
        if (this.activator != null) {
            XMLUtil.trySetAttr((Element)element, (String)"activator", (Object)this.activator);
        }
        return element;
    }

    public void setFromXML(Element element) {
        this.key = element.getAttributeValue("key");
        this.value = XMLUtil.tryGetBoolAttr((Element)element, (String)"value");
        this.description = element.getAttributeValue("description");
        this.activator = element.getAttributeValue("activator");
    }

    @Override
    public int getType() {
        return 3;
    }

    @Override
    public String print() {
        return this.value ? "Yes" : "No";
    }

    @Override
    public void setValue(String string) {
        this.value = Boolean.parseBoolean(string);
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


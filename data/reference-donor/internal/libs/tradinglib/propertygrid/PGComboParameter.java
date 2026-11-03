/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Content
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.propertygrid;

import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.propertygrid.IPGParameter;
import java.util.Map;
import java.util.TreeMap;
import org.jdom2.Content;
import org.jdom2.Element;

public class PGComboParameter
implements IPGParameter {
    private String key;
    private String name;
    private String category;
    private String activator;
    private String description;
    private String value;
    private String engine;
    private TreeMap<String, String> options = new TreeMap();

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

    public String getValue() {
        return this.value;
    }

    @Override
    public void setValue(String string) {
        this.value = string;
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

    public TreeMap<String, String> getOptions() {
        return this.options;
    }

    public void setOptions(TreeMap<String, String> treeMap) {
        this.options = treeMap;
    }

    public Element getXML() {
        Element element = new Element("Param");
        XMLUtil.trySetAttr((Element)element, (String)"key", (Object)this.key);
        XMLUtil.trySetAttr((Element)element, (String)"name", (Object)this.name);
        XMLUtil.trySetAttr((Element)element, (String)"dataType", (Object)String.valueOf(5));
        XMLUtil.trySetAttr((Element)element, (String)"value", (Object)String.valueOf(this.value));
        XMLUtil.trySetAttr((Element)element, (String)"description", (Object)this.description);
        if (this.activator != null) {
            XMLUtil.trySetAttr((Element)element, (String)"activator", (Object)this.activator);
        }
        Element element2 = new Element("Options");
        for (String string : this.options.keySet()) {
            Element element3 = new Element("Option");
            element3.setAttribute("name", this.options.get(string));
            element3.setText(string);
            element2.addContent((Content)element3);
        }
        element.addContent((Content)element2);
        return element;
    }

    public void setFromXML(Element element) {
        this.key = element.getAttributeValue("key");
        this.value = element.getAttributeValue("value");
        this.description = element.getAttributeValue("description");
        this.activator = element.getAttributeValue("activator");
        Element element2 = element.getChild("Options");
        if (element2 != null) {
            int n = element2.getChildren("Option").size();
            this.options.clear();
            for (int i = 0; i < n; ++i) {
                Element element3 = (Element)element2.getChildren("Option").get(i);
                String string = element3.getAttributeValue("name");
                String string2 = element3.getTextNormalize();
                this.options.put(string, string2);
            }
        }
    }

    @Override
    public int getType() {
        return 5;
    }

    @Override
    public String print() {
        for (Map.Entry<String, String> entry : this.options.entrySet()) {
            if (!this.value.equals(entry.getValue())) continue;
            return entry.getKey();
        }
        return this.value;
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


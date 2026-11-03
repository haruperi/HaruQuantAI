/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.jdom2.Content
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib;

import com.strategyquant.tradinglib.propertygrid.ParametersTableItem;
import org.jdom2.Content;
import org.jdom2.Element;

public abstract class ScalingMethod
extends ParametersTableItem {
    public String name = null;

    public void setName(String string) {
        this.name = string;
    }

    @Override
    public Element getXML() {
        Element element = new Element("Scaling");
        Element element2 = new Element("Method");
        element2.setAttribute("type", this.getClass().getSimpleName());
        Element element3 = super.getXML();
        element2.addContent((Content)element3);
        element.addContent((Content)element2);
        return element;
    }

    @Override
    public void setFromXML(Element element) throws Exception {
        Element element2 = this.getUsedSubelement(element, "Method");
        if (element2 == null) {
            throw new Exception("Cannot set up MoneyManagement method. Method xml element not found");
        }
        this.setName(element2.getAttributeValue("type"));
        super.setFromXML(element2);
    }
}


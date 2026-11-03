/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.atm.sizes;

import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.atm.sizes.AbstractATMPositionSize;
import org.jdom2.Element;

public class SizeFixedLots
extends AbstractATMPositionSize {
    private double Lots;

    public SizeFixedLots(Element element, int n, double d) {
        super(element, n, d);
        this.Lots = XMLUtil.getItemDoubleParam((Element)element, (String)"Lots", (double)0.01);
    }

    @Override
    public Element getXML() {
        Element element = new Element("PositionSize");
        element.setAttribute("key", "SizeFixedLots");
        XMLUtil.setItemDoubleParam((Element)element, (String)"Lots", (double)this.Lots);
        return element;
    }

    @Override
    public double computeSize(double d, double d2, boolean bl) {
        if (bl) {
            return d - d2;
        }
        double d3 = this.Lots;
        if (d3 < this.minimalSize) {
            d3 = this.minimalSize;
        }
        return d3;
    }

    public String toString() {
        return String.format("Close %s lots", this.Lots);
    }
}


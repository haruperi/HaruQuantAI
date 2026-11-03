/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.atm.sizes;

import com.strategyquant.tradinglib.atm.sizes.AbstractATMPositionSize;
import org.jdom2.Element;

public class SizeAllRemaining
extends AbstractATMPositionSize {
    public SizeAllRemaining(Element element, int n, double d) {
        super(element, n, d);
    }

    @Override
    public Element getXML() {
        Element element = new Element("PositionSize");
        element.setAttribute("key", "SizeAllRemaining");
        return element;
    }

    @Override
    public double computeSize(double d, double d2, boolean bl) {
        return d - d2;
    }

    public String toString() {
        return "Close remaining position";
    }
}


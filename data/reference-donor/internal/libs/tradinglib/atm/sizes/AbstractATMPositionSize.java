/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.atm.sizes;

import org.jdom2.Element;

public abstract class AbstractATMPositionSize {
    protected int sizeDecimals;
    protected double minimalSize;

    public AbstractATMPositionSize(Element element, int n, double d) {
        this.sizeDecimals = n;
        this.minimalSize = d;
    }

    public abstract double computeSize(double var1, double var3, boolean var5);

    public abstract Element getXML();
}


/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.atm.sizes;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.atm.sizes.AbstractATMPositionSize;
import org.jdom2.Element;

public class SizePercents
extends AbstractATMPositionSize {
    private int Percents;

    public SizePercents(Element element, int n, double d) {
        super(element, n, d);
        this.Percents = XMLUtil.getItemIntParam((Element)element, (String)"Percents", (int)50);
    }

    @Override
    public Element getXML() {
        Element element = new Element("PositionSize");
        element.setAttribute("key", "SizePercents");
        XMLUtil.setItemIntParam((Element)element, (String)"Percents", (int)this.Percents);
        return element;
    }

    @Override
    public double computeSize(double d, double d2, boolean bl) {
        if (bl) {
            return d - d2;
        }
        double d3 = SQUtils.round((double)(d / 100.0 * (double)this.Percents), (int)this.sizeDecimals);
        if (d3 < this.minimalSize) {
            d3 = this.minimalSize;
        }
        return d3;
    }

    public String toString() {
        return String.format("Close %s%% of position", this.Percents);
    }
}


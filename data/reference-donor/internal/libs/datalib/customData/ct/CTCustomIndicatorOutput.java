/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 */
package com.strategyquant.datalib.customData.ct;

import com.strategyquant.lib.XMLUtil;
import org.jdom2.Element;

public class CTCustomIndicatorOutput {
    public String name;
    public String el;
    public String jf;
    public String mt4;
    public String mt5;

    public CTCustomIndicatorOutput(Element element) throws Exception {
        this.name = XMLUtil.getAttr((Element)element, (String)"name");
        this.el = element.getChildText("EL");
        this.jf = element.getChildText("JF");
        this.mt4 = element.getChildText("MT4");
        this.mt5 = element.getChildText("MT5");
    }
}


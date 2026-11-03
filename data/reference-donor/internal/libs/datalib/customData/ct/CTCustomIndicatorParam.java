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

public class CTCustomIndicatorParam {
    public String name;
    public String type;
    public String value;

    public CTCustomIndicatorParam(Element element) throws Exception {
        this.name = XMLUtil.getAttr((Element)element, (String)"name");
        this.type = XMLUtil.getAttr((Element)element, (String)"type");
        this.value = XMLUtil.getAttr((Element)element, (String)"defaultValue");
    }
}


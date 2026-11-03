/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 */
package com.strategyquant.plugin.App.impl.SQXBusiness;

import com.strategyquant.lib.XMLUtil;
import org.jdom2.Element;

public class EAParameter {
    public String originalName;
    public String newName;
    public String type;
    public String value;
    public boolean isCategory;
    public int position;

    public EAParameter(Element elParam) {
        this.originalName = elParam.getAttributeValue("name");
        this.newName = elParam.getAttributeValue("newName");
        this.type = elParam.getAttributeValue("type");
        this.value = elParam.getAttributeValue("value");
        this.isCategory = XMLUtil.getBooleanAttr((Element)elParam, (String)"isCategory", (boolean)false);
        this.position = XMLUtil.getIntAttr((Element)elParam, (String)"position", (int)0);
    }
}


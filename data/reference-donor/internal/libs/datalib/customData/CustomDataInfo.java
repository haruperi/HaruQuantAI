/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.settings.IXMLAble
 *  org.jdom2.Element
 *  org.json.JSONArray
 */
package com.strategyquant.datalib.customData;

import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.settings.IXMLAble;
import java.io.Serializable;
import org.jdom2.Element;
import org.json.JSONArray;

public class CustomDataInfo
implements Serializable,
IXMLAble {
    public static final String Name = "name";
    public static final String CodeMT4 = "mt4";
    public static final String CodeMT5 = "mt5";
    public static final String CodeEL = "el";
    public int id;
    public String name;
    public int dataType;
    public int values;
    public JSONArray valuesObject;
    public String timeframe;
    public String filename;
    public long dateFrom = 0L;
    public long dateTo = 0L;
    public int rows = 0;
    public int totalDays;

    public String getValue(int n, String string) throws Exception {
        try {
            Object object = this.valuesObject.getJSONObject(n).get(string);
            if (object instanceof String) {
                return object.toString();
            }
            return null;
        }
        catch (Exception exception) {
            throw new Exception("Failed to return value.", exception);
        }
    }

    public void setValues(String string) {
        this.valuesObject = new JSONArray(string);
        this.values = 0;
        for (int i = 0; i < this.valuesObject.length(); ++i) {
            Object object = this.valuesObject.getJSONObject(i).get(Name);
            if (!(object instanceof String) || object.toString().length() <= 0) continue;
            ++this.values;
        }
    }

    public Element getXML() {
        Element element = new Element("IndicatorDataInfo");
        XMLUtil.trySetAttr((Element)element, (String)Name, (Object)this.name);
        XMLUtil.trySetAttr((Element)element, (String)"type", (Object)(this.dataType + ""));
        XMLUtil.trySetAttr((Element)element, (String)"count", (Object)(this.values + ""));
        XMLUtil.trySetAttr((Element)element, (String)"values", (Object)this.valuesObject.toString());
        return element;
    }

    public void setFromXML(Element element) throws Exception {
        this.name = element.getAttributeValue(Name);
        this.dataType = XMLUtil.tryGetIntAttr((Element)element, (String)"type");
        this.values = XMLUtil.tryGetIntAttr((Element)element, (String)"count");
        this.valuesObject = new JSONArray(element.getAttributeValue("values"));
    }
}


/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataSeries
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.indicatorTester;

import com.strategyquant.datalib.DataSeries;
import com.strategyquant.indicatorTester.IndicatorTesterConfig;
import com.strategyquant.indicatorTester.IndyParameter;
import com.strategyquant.tradinglib.ChartData;
import java.io.File;
import java.util.ArrayList;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;

public class IndicatorInfo {
    public String simpleName;
    public String className;
    public String title;
    public boolean ignored = false;
    public int returnType;
    public int shift = 0;
    public ArrayList<String> outputBuffers = new ArrayList();
    public ArrayList<IndyParameter> parameters = new ArrayList();

    public ArrayList<JSONObject> getJSONList() {
        ArrayList<JSONObject> arrayList = new ArrayList<JSONObject>();
        for (String string : this.outputBuffers) {
            JSONObject jSONObject = new JSONObject();
            JSONArray jSONArray = new JSONArray();
            String string2 = this.simpleName + (string.equals("Value") ? "" : "." + string);
            jSONObject.put("name", (Object)string2);
            jSONObject.put("value", (Object)string2);
            jSONObject.put("className", (Object)this.className);
            jSONObject.put("shift", this.shift);
            for (IndyParameter indyParameter : this.parameters) {
                if (indyParameter.className.equals(ChartData.class.getSimpleName())) continue;
                indyParameter.value = indyParameter.className.equals(DataSeries.class.getSimpleName()) ? "Close" : indyParameter.defaultValue;
                jSONArray.put((Object)indyParameter.toJSON());
            }
            jSONObject.put("parameters", (Object)jSONArray);
            arrayList.add(jSONObject);
        }
        return arrayList;
    }

    public Element getXML(String string) {
        Element element = new Element("Test");
        element.setAttribute("use", "true");
        element.setAttribute("indicator", string);
        element.setAttribute("parameters", this.getParams());
        element.setAttribute("decimals", "6");
        element.setAttribute("result", "");
        element.setAttribute("shift", String.valueOf(this.shift));
        String string2 = string + ".csv";
        File file = new File(IndicatorTesterConfig.defaultConfigFilePath + "/" + string2);
        element.setAttribute("fileName", string2);
        element.setAttribute("exists", file.exists() ? "yes" : "no");
        return element;
    }

    private String getParams() {
        String string = "";
        if (this.parameters.isEmpty()) {
            return string;
        }
        for (IndyParameter indyParameter : this.parameters) {
            if (indyParameter.className.equals(ChartData.class.getSimpleName())) continue;
            string = string + (indyParameter.value != null ? indyParameter.value : indyParameter.defaultValue) + ",";
        }
        return string.length() > 0 ? string.substring(0, string.length() - 1) : string;
    }
}


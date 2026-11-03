/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.tradinglib.WhatIf
 *  com.strategyquant.tradinglib.whatif.WhatIfMethodsList
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.CrossCheck.impl.WhatIf;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.WhatIf;
import com.strategyquant.tradinglib.whatif.WhatIfMethodsList;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.List;
import java.util.Map;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class WhatIfServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(WhatIfServlet.class);

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            case "list": {
                return this.onList(parameterMap);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    private String onList(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        JSONArray data = new JSONArray();
        List methods = WhatIfMethodsList.get().getAvailableClasses();
        for (int i = 0; i < methods.size(); ++i) {
            WhatIf method = (WhatIf)methods.get(i);
            JSONObject row = new JSONObject();
            JSONArray rowData = new JSONArray();
            rowData.put(false);
            rowData.put((Object)method.printFormatedName());
            JSONObject methodObj = new JSONObject();
            methodObj.put("display", (Object)method.getFormatedName());
            methodObj.put("config", (Object)XMLUtil.elementToString((Element)method.getXML()));
            row.put("userdata", (Object)methodObj);
            row.put("id", (Object)method.getClass().getSimpleName());
            row.put("data", (Object)rowData);
            data.put((Object)row);
        }
        response.put("rows", (Object)data);
        response.put("success", (Object)L.t((String)"Methods listed.", (Object[])new Object[0]));
        return response.toString();
    }
}


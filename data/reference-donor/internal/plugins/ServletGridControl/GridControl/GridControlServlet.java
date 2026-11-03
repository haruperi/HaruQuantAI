/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.lib.L
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Servlet.impl.GridControl;

import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.L;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class GridControlServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(GridControlServlet.class);

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "getData": {
                return this.onGetData(args);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    private String onGetData(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        response.put("gridData", (Object)new JSONObject(SQGrid.getGridClient().getGridDescriptions()));
        response.put("success", (Object)L.t((String)"Databanks listed.", (Object[])new Object[0]));
        return response.toString();
    }
}


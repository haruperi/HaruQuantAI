/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.tradinglib.build.BuildTemplatesManager
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Element
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Servlet.impl.Builder;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.build.BuildTemplatesManager;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.jdom2.Element;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BuilderServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(BuilderServlet.class);

    protected String execute(String command, Map<String, String[]> args, String method) {
        switch (command) {
            case "getTemplate": {
                return this.onGetBuildTemplate(args);
            }
        }
        return BuilderServlet.apiErrorJSON((String)L.t((String)"Execution failed. Incorrect url arguments '%s'.", (Object[])new Object[]{command}), null);
    }

    private String onGetBuildTemplate(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String templateName = args.get("template")[0];
            response.put("template", (Object)XMLUtil.elementToString((Element)BuildTemplatesManager.getTemplateXML((String)templateName)));
        }
        catch (Exception ex) {
            return BuilderServlet.apiErrorJSON((String)L.t((String)"Cannot get build template.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Builder template returned.", (Object[])new Object[0]));
        return response.toString();
    }
}


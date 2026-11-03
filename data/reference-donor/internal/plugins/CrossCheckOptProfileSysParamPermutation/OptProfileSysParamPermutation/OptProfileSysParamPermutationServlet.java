/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.CrossCheck.impl.OptProfileSysParamPermutation;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.File;
import java.util.Map;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OptProfileSysParamPermutationServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(OptProfileSysParamPermutationServlet.class);

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            case "getDefaultSPPConditions": {
                return this.onGetDefaultSPPConditions();
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    private String onGetDefaultSPPConditions() throws Exception {
        JSONObject response = new JSONObject();
        String path = SQPaths.pluginsDirPath + "/CrossCheckOptProfileSysParamPermutation/SPPDefaultConditions.xml";
        String conditions = SQUtils.fileToString((File)new File(path));
        response.put("conditions", (Object)conditions);
        response.put("success", (Object)"ok");
        return response.toString();
    }
}


/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Settings.impl.AdvancedTM;

import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AdvancedTMServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(AdvancedTMServlet.class);

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            default: 
        }
        throw new Exception("Unknown command '" + command + "'.");
    }
}


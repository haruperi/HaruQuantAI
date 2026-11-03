/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataManager.impl.Home;

import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class HomeServlet
extends HttpJSONServlet {
    private static final long serialVersionUID = 1L;
    private static final Logger Log = LoggerFactory.getLogger(HomeServlet.class);

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            default: 
        }
        throw new Exception("Unknown command '" + command + "'.");
    }
}


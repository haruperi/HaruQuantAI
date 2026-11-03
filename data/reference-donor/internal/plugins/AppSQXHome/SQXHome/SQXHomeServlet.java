/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.App.impl.SQXHome;

import com.strategyquant.lib.L;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SQXHomeServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(SQXHomeServlet.class);

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            default: 
        }
        throw new Exception(L.t((String)"Unknown command '%s'.", (Object[])new Object[]{command}));
    }
}


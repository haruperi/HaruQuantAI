/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.PrecachedRequest
 *  com.strategyquant.tradinglib.fitnessfunction.FitnessOptions
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.FitnessMethod.impl.StrategyResult;

import com.strategyquant.tradinglib.PrecachedRequest;
import com.strategyquant.tradinglib.fitnessfunction.FitnessOptions;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class FitnessMethodStrategyResultServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(FitnessMethodStrategyResultServlet.class);

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            case "list": {
                return this.onList();
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    @PrecachedRequest(relativeURL="/fitnessMethodStrategyResult/list")
    private String onList() throws Exception {
        return FitnessOptions.list();
    }
}


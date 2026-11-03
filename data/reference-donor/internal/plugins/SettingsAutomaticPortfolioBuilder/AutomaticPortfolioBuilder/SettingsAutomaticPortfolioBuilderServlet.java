/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.SampleTypes
 *  com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterFitness
 *  com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterFitnessList
 *  com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterUtils
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.SampleTypes;
import com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterFitness;
import com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterFitnessList;
import com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterUtils;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.math.BigInteger;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SettingsAutomaticPortfolioBuilderServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(SettingsAutomaticPortfolioBuilderServlet.class);

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "getNumberOfPossiblePortfolios": {
                return this.getNumberOfPossiblePortfolios(args);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    private String getNumberOfPossiblePortfolios(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        int selected = Integer.valueOf(this.tryGetParamValue(args, "selected"));
        int min = Integer.valueOf(this.tryGetParamValue(args, "min"));
        int max = Integer.valueOf(this.tryGetParamValue(args, "max"));
        if (selected < 0) {
            Databank databank = this.getDatabank(args);
            selected = databank.size();
        }
        BigInteger numberOfPossiblePortfolios = PortfolioMasterUtils.calculateMaxNumberOfPortfolios((int)selected, (int)min, (int)max);
        response.put("numberOfPossiblePortfolios", (Object)numberOfPossiblePortfolios);
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private Databank getDatabank(Map<String, String[]> args) throws Exception {
        String projectName = this.tryGetParam(args, "project")[0];
        String databankName = this.tryGetParam(args, "databank")[0];
        SQProject project = ProjectEngine.get((String)projectName);
        if (!project.getDatabanks().containsKey((Object)databankName)) {
            throw new Exception(L.t((String)"Databank '%s' doesn't exist.", (Object[])new Object[]{databankName}));
        }
        return (Databank)project.getDatabanks().get((Object)databankName);
    }

    public JSONArray getFitnessTypes() throws Exception {
        JSONArray types = new JSONArray();
        for (PortfolioMasterFitness type : PortfolioMasterFitnessList.getInstance().getAvailableClasses()) {
            String className = type.getClass().getSimpleName();
            types.put((Object)new JSONObject().put("type", (Object)(className + PortfolioMasterFitness.SampleKeyIS)).put("name", (Object)(type.getName() + " " + SampleTypes.typeToFullString((byte)10))));
            types.put((Object)new JSONObject().put("type", (Object)(className + PortfolioMasterFitness.SampleKeyFull)).put("name", (Object)(type.getName() + " " + SampleTypes.typeToFullString((byte)127))));
        }
        return types;
    }

    public static String sampleTypeKey(byte type) {
        switch (type) {
            case 10: {
                return "IS";
            }
            case 127: {
                return "Full";
            }
        }
        return "IS";
    }
}


/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 */
package com.strategyquant.tradinglib.results;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.backtest.SQBacktester;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import java.util.Map;

public class DatabankResultsGroupProvider
implements IResultsGroupProvider {
    @Override
    public ResultsGroup get(Map<String, String[]> map, String string) throws Exception {
        String string2;
        String string3 = map.containsKey("projectName") ? this.tryGetParam(map, "projectName")[0] : this.tryGetParam(map, "project")[0];
        boolean bl = false;
        try {
            bl = Boolean.parseBoolean(this.tryGetParam(map, "algoWizard")[0]);
        }
        catch (Exception exception) {
            try {
                string2 = map.containsKey("strategy") ? "strategy" : "strategyName";
                bl = bl || this.tryGetParam(map, string2)[0].startsWith("AlgoWizard");
            }
            catch (Exception exception2) {
                // empty catch block
            }
        }
        if (bl) {
            String string4 = this.tryGetParam(map, "backtestID")[0];
            return SQBacktester.getResultsGroup(string4);
        }
        String string5 = map.containsKey("databankName") ? this.tryGetParam(map, "databankName")[0] : this.tryGetParam(map, "databank")[0];
        string2 = map.containsKey("strategyName") ? this.tryGetParam(map, "strategyName")[0] : this.tryGetParam(map, "strategy")[0];
        Databank databank = (Databank)ProjectEngine.get(string3).getDatabanks().get(string5);
        if (databank == null) {
            throw new Exception(L.t((String)"Databank '%s' not found in project '%s'!", (Object[])new Object[]{string5, string3}));
        }
        return databank.getLocked(string2, string);
    }

    private String[] tryGetParam(Map<String, String[]> map, String string) throws Exception {
        if (!map.containsKey(string)) {
            throw new Exception("Parameter '" + string + "' is missing.");
        }
        return map.get(string);
    }

    @Override
    public String getFilePath(ResultsGroup resultsGroup) {
        return resultsGroup.getFilePath();
    }
}


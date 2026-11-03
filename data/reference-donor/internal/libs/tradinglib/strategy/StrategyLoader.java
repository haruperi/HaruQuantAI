/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.program.IProgram
 *  com.strategyquant.pluginlib.program.Program
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.strategy;

import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.results.file.MissingInstrumentException;
import com.strategyquant.tradinglib.strategy.StrategyMerger;
import org.json.JSONObject;

public class StrategyLoader {
    private static boolean cancelLoadingRecords = false;
    private static boolean waitingForInstrument = false;

    public static ResultsGroup loadStrategy(SQProject sQProject, String string, String string2, double d) throws Exception {
        IProgram iProgram = Program.get((String)"Loader");
        block5: while (true) {
            if (cancelLoadingRecords) {
                sQProject.getProgress().update("load", 100.0, "canceled");
                return null;
            }
            try {
                ResultsGroup resultsGroup = (ResultsGroup)iProgram.call("loadFile", new Object[]{string2});
                resultsGroup.updated = true;
                if (resultsGroup.specialValues().containsKey(SpecialValues.IsMergedPortfolio)) {
                    resultsGroup.setMergedResults(StrategyMerger.loadSplitResultsFromSource(string2));
                }
                if (cancelLoadingRecords) {
                    sQProject.getProgress().update("load", 100.0, "canceled");
                    return null;
                }
                sQProject.getProgress().update("load", d, null);
                return resultsGroup;
            }
            catch (MissingInstrumentException missingInstrumentException) {
                sQProject.getProgress().update("load", d, null, "selectInstrument", new JSONObject().put("reportName", (Object)string).put("symbol", (Object)missingInstrumentException.getSymbol()).put("databankLoading", true));
                waitingForInstrument = true;
                while (true) {
                    if (!waitingForInstrument) continue block5;
                    try {
                        Thread.sleep(500L);
                    }
                    catch (Exception exception) {}
                }
            }
            catch (OutOfMemoryError outOfMemoryError) {
                sQProject.getProgress().update("load", 100.0, "Some strategies were not loaded. " + outOfMemoryError.getMessage());
                throw outOfMemoryError;
            }
            break;
        }
    }

    public static void init() {
        cancelLoadingRecords = false;
        waitingForInstrument = false;
    }

    public static void cancel() {
        cancelLoadingRecords = true;
        waitingForInstrument = false;
    }

    public static void instrumentSelected() {
        waitingForInstrument = false;
    }

    public static boolean isCanceled() {
        return cancelLoadingRecords;
    }
}


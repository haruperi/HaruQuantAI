/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.StopPauseEngine;

public class LoadDataProgressEngine {
    private ProgressEngine pe;
    private String symbolTF;
    private String testName;

    public LoadDataProgressEngine(ProgressEngine progressEngine) {
        this.pe = progressEngine;
    }

    public StopPauseEngine getProgressEngine() {
        return this.pe;
    }

    public void printToLog(String string) {
        this.pe.printToLog(string);
    }

    public void setParams(String string, String string2, String string3) {
        this.symbolTF = String.format("%s / %s", string2, string3);
        this.testName = string;
    }

    public String getSymbolTF() {
        return this.symbolTF;
    }

    public String getTestName() {
        return this.testName;
    }

    public void onDataPreparationFinished(double d, long l) {
    }
}


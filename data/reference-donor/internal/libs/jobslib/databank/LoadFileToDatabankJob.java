/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.program.IProgram
 *  com.strategyquant.pluginlib.program.Program
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.ResultsGroup
 */
package com.strategyquant.jobslib.databank;

import com.strategyquant.jobslib.SQJob;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import java.io.File;

public class LoadFileToDatabankJob
extends SQJob {
    private Databank databank;
    private File file;

    public LoadFileToDatabankJob(File file, Databank databank) {
        this.file = file;
        this.databank = databank;
    }

    @Override
    public void run() throws Exception {
        IProgram iProgram = Program.get((String)"Loader");
        ResultsGroup resultsGroup = (ResultsGroup)iProgram.call("loadFile", new Object[]{this.file.getAbsolutePath()});
        this.databank.add(resultsGroup, true);
        this.databank.updateBestResults(resultsGroup);
    }
}


/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridClient
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.lib.L
 *  com.strategyquant.tradinglib.dukascopy.ImportInfo
 *  com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress
 *  com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataSource.impl.Darwinex.importdata;

import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.L;
import com.strategyquant.plugin.DataSource.impl.Darwinex.importdata.DarwinexImportJob;
import com.strategyquant.tradinglib.dukascopy.ImportInfo;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DarwinexImport {
    public static final Logger Log = LoggerFactory.getLogger(DarwinexImport.class);
    private static final String IMPORT_DARWINEX_JOB = "DarwinexImportJob_";
    private static DarwinexImport instance;

    public static synchronized DarwinexImport get() {
        if (instance == null) {
            instance = new DarwinexImport();
        }
        return instance;
    }

    public void stop(String symbol) {
        String ident = IMPORT_DARWINEX_JOB + symbol;
        SQGrid.getGridClient().stop(ident);
    }

    public void pause(String symbol) {
        String ident = IMPORT_DARWINEX_JOB + symbol;
        SQGrid.getGridClient().pause(ident);
    }

    public void restart(String symbol) {
        String ident = IMPORT_DARWINEX_JOB + symbol;
        SQGrid.getGridClient().restart(ident);
    }

    public void importData(ImportInfo importInfo, String path, DataManagerProgressListener listener) {
        try {
            if (SQGrid.getGridClient().countRunningJobs(IMPORT_DARWINEX_JOB + importInfo.symbol) != 0L) {
                throw new RuntimeException(L.t((String)"Import from Darwinex is already running.", (Object[])new Object[0]));
            }
            DataManagerDataProgress.get().setProgress(importInfo.symbol, 0, L.t((String)"Waiting...", (Object[])new Object[0]));
            String ident = IMPORT_DARWINEX_JOB + importInfo.symbol;
            DarwinexImportJob job = new DarwinexImportJob(importInfo, path, ident);
            if (listener != null) {
                job.setProgressListener(listener);
            }
            ArrayList<DarwinexImportJob> jobs = new ArrayList<DarwinexImportJob>(1);
            jobs.add(job);
            GridClient gridClient = SQGrid.getGridClient();
            gridClient.executeOnGrid(ident, jobs);
        }
        catch (Exception e) {
            Log.error("", (Throwable)e);
            if (listener != null) {
                listener.onError("Error - " + e.getMessage());
            }
            throw new RuntimeException(e);
        }
    }
}


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
package com.strategyquant.plugin.DataSource.impl.TD;

import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.L;
import com.strategyquant.plugin.DataSource.impl.TD.job.ImportFileJob;
import com.strategyquant.tradinglib.dukascopy.ImportInfo;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TDDataManager {
    public static final Logger Log = LoggerFactory.getLogger(TDDataManager.class);
    private static final String IMPORT_TDDATA_JOB = "ImportTDDataJob_";
    private static TDDataManager instance;

    public static synchronized TDDataManager get() {
        if (instance == null) {
            instance = new TDDataManager();
        }
        return instance;
    }

    public void stopTDImport(String symbol) {
        String ident = IMPORT_TDDATA_JOB + symbol;
        SQGrid.getGridClient().stop(ident);
    }

    public void pauseTDImport(String symbol) {
        String ident = IMPORT_TDDATA_JOB + symbol;
        SQGrid.getGridClient().pause(ident);
    }

    public void restartTDImport(String symbol) {
        String ident = IMPORT_TDDATA_JOB + symbol;
        SQGrid.getGridClient().restart(ident);
    }

    public void importTDData(ImportInfo importInfo, String path, DataManagerProgressListener listener) {
        try {
            if (SQGrid.getGridClient().countRunningJobs(IMPORT_TDDATA_JOB + importInfo.symbol) != 0L) {
                throw new RuntimeException(L.t((String)"Import from Dukascopy is already running.", (Object[])new Object[0]));
            }
            DataManagerDataProgress.get().setProgress(importInfo.symbol, 0, L.t((String)"Waiting...", (Object[])new Object[0]));
            String ident = IMPORT_TDDATA_JOB + importInfo.symbol;
            ImportFileJob job = new ImportFileJob(importInfo, path, ident);
            if (listener != null) {
                job.setProgressListener(listener);
            }
            ArrayList<ImportFileJob> jobs = new ArrayList<ImportFileJob>(1);
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


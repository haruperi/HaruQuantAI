/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.metatrader4.Mt4SymbolProperties
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.utils.IProgressListener
 *  com.strategyquant.tradinglib.mt4.Mt4Exporter
 */
package com.strategyquant.plugin.DataManager.impl.Data.job;

import com.strategyquant.datalib.metatrader4.Mt4SymbolProperties;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.lib.L;
import com.strategyquant.lib.utils.IProgressListener;
import com.strategyquant.tradinglib.mt4.Mt4Exporter;

public class MT4ExportJob
extends GridJob<Void> {
    private Mt4Exporter exporter;
    private IProgressListener listener;

    public MT4ExportJob(String jobId, String sqSymbol, String mt4Symbol, String encoding, long fromDate, long toDate, String dataFolder, String serverName, Mt4SymbolProperties symbolProperties, String timeframe, String exportMode, String targetTimezone, IProgressListener listener) {
        super(jobId, 0, null);
        this.listener = listener;
        this.exporter = new Mt4Exporter(sqSymbol, mt4Symbol, encoding, fromDate, toDate, dataFolder, serverName, symbolProperties, timeframe, exportMode, targetTimezone, listener);
    }

    public Void call() throws Exception {
        this.listener.setMessage(L.t((String)"Starting export to MT4...", (Object[])new Object[0]));
        this.listener.onProgress(1.0);
        this.exporter.export();
        this.listener.onProgress(100.0);
        this.listener.setMessage(this.exporter.isCanceled() ? L.t((String)"Stopped", (Object[])new Object[0]) : L.t((String)"Completed", (Object[])new Object[0]));
        return null;
    }

    public void messageReceived(GridMessage message) {
        super.messageReceived(message);
        switch (message.getMessageID()) {
            case 4: {
                this.exporter.cancel();
                break;
            }
            case 2: {
                this.exporter.pause();
                break;
            }
            case 3: {
                this.exporter.restart();
            }
        }
    }
}


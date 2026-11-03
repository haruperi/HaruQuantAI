/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.utils.IProgressListener
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataManager.impl.Data.job;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.lib.L;
import com.strategyquant.lib.utils.IProgressListener;
import com.strategyquant.plugin.DataManager.impl.Data.job.MT5Exporter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MT5ExportJob
extends GridJob<Void> {
    private static final Logger LOG = LoggerFactory.getLogger(MT5ExportJob.class);
    private MT5Exporter exporter = new MT5Exporter();
    private IProgressListener listener;
    private String connection;
    private String symbol;
    private String timeframe;
    private String filePath;
    private long fromDate;
    private long toDate;
    private String spreadType;
    private double spreadPips;
    private double spreadPoints;
    private String targetTimezone;

    public MT5ExportJob(String jobId, IProgressListener listener, String connection, String symbol, String timeframe, String spreadType, double spreadPoints, double spreadPips, String filePath, long fromDate, long toDate, String targetTimezone) {
        super(jobId, 0, null);
        this.listener = listener;
        this.connection = connection;
        this.symbol = symbol;
        this.timeframe = timeframe;
        this.filePath = filePath;
        this.fromDate = fromDate;
        this.toDate = toDate;
        this.spreadType = spreadType;
        this.spreadPoints = spreadPoints;
        this.spreadPips = spreadPips;
        this.targetTimezone = targetTimezone;
    }

    public Void call() throws Exception {
        try {
            this.listener.setMessage(L.t((String)"Starting export to MT5...", (Object[])new Object[0]));
            this.exporter.exportData(this.listener, this.connection, this.symbol, this.timeframe, this.spreadType, this.spreadPoints, this.spreadPips, this.filePath, this.fromDate, this.toDate, this.targetTimezone);
        }
        catch (Exception e) {
            LOG.error("Error while exporting data", (Throwable)e);
            this.listener.onError(e.getMessage());
        }
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


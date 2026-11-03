/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.utils.IProgressListener
 */
package com.strategyquant.plugin.DataManager.impl.Data.csvexport;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.lib.L;
import com.strategyquant.lib.utils.IProgressListener;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.CsvExporter;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.format.Format;

public class CsvExportJob
extends GridJob<Void> {
    private CsvExporter exporter = new CsvExporter();
    private IProgressListener listener;
    private String connection;
    private String symbol;
    private String timeframe;
    private String session;
    private String filePath;
    private long fromDate;
    private long toDate;
    private Format format;
    private String targetTimezone;

    public CsvExportJob(String jobId, IProgressListener listener, String connection, String symbol, String timeframe, String session, String filePath, long fromDate, long toDate, Format format, String targetTimezone) {
        super(jobId, 0, null);
        this.listener = listener;
        this.connection = connection;
        this.symbol = symbol;
        this.timeframe = timeframe;
        this.session = session;
        this.filePath = filePath;
        this.fromDate = fromDate;
        this.toDate = toDate;
        this.format = format;
        this.targetTimezone = targetTimezone;
    }

    public Void call() throws Exception {
        this.listener.setMessage(L.t((String)"Starting Export to CSV...", (Object[])new Object[0]));
        this.exporter.exportData(this.listener, this.connection, this.symbol, this.timeframe, this.session, this.filePath, this.fromDate, this.toDate, this.format, this.targetTimezone);
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


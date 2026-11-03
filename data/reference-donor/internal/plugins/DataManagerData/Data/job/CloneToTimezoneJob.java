/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.data.DataCloner
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.historyData.dto.TickerDto
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.utils.IProgressListener
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.MultiProgressListener
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataManager.impl.Data.job;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.DataCloner;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.historyData.dto.TickerDto;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.lib.L;
import com.strategyquant.lib.utils.IProgressListener;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.MultiProgressListener;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CloneToTimezoneJob
extends GridJob<Void> {
    private static final Logger Log = LoggerFactory.getLogger(CloneToTimezoneJob.class);
    private DataCloner cloner = new DataCloner();
    private IProgressListener listener;
    private volatile boolean cancel;
    private String symbol;
    private String toSymbol;
    private String toTimezone;
    private int shiftHours;
    private boolean removeWeekends;
    private TickerDto ticker;

    public CloneToTimezoneJob(String jobId, String symbol, String toSymbol, String toTimezone, int shiftHours, boolean removeWeekends, TickerDto ticker, MultiProgressListener listener) {
        super(jobId, 0, null);
        this.listener = listener;
        this.symbol = symbol;
        this.toSymbol = toSymbol;
        this.toTimezone = toTimezone;
        this.shiftHours = shiftHours;
        this.removeWeekends = removeWeekends;
        this.ticker = ticker;
    }

    public Void call() throws Exception {
        this.listener.setMessage(L.t((String)"Starting clone...", (Object[])new Object[0]));
        this.listener.onProgress(1.0);
        try {
            DataInfo sourceSymbolInfo = DataManager.getDataInfo((String)"History", (String)this.symbol);
            this.cloner.createSymbol(this.toSymbol, sourceSymbolInfo);
            this.sendDataUpdate();
            this.cloner.cloneToTimezone(this.symbol, this.toSymbol, this.toTimezone, this.shiftHours, this.removeWeekends, this.ticker, this.listener);
            this.sendDataUpdate();
            this.listener.onProgress(100.0);
            this.listener.setMessage(this.cancel ? L.t((String)"Stopped", (Object[])new Object[0]) : L.t((String)"Completed", (Object[])new Object[0]));
        }
        catch (Exception e) {
            Log.error("Error while performing cloning", (Throwable)e);
            this.listener.onError(L.t((String)("Error while cloning data: " + e.getMessage()), (Object[])new Object[0]));
        }
        return null;
    }

    private void sendDataUpdate() {
        try {
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)this.toSymbol, (String)"add"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        catch (Exception e) {
            Log.error("Cannot send websocket data update. ", (Throwable)e);
        }
    }

    public void messageReceived(GridMessage message) {
        super.messageReceived(message);
        switch (message.getMessageID()) {
            case 4: {
                this.cancel = true;
                this.cloner.cancel();
                break;
            }
            case 2: {
                this.cloner.pause();
                break;
            }
            case 3: {
                this.cloner.restart();
            }
        }
    }
}


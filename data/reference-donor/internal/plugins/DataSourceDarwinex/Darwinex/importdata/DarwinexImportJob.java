/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.basket.BasketOfStocksManager
 *  com.strategyquant.datalib.darwinex.DarwinexUtils
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.tradinglib.dukascopy.ImportInfo
 *  com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress
 *  com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  it.unimi.dsi.fastutil.longs.Long2ObjectAVLTreeMap
 *  it.unimi.dsi.fastutil.longs.Long2ObjectMap$Entry
 *  org.joda.time.format.DateTimeFormat
 *  org.joda.time.format.DateTimeFormatter
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataSource.impl.Darwinex.importdata;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.darwinex.DarwinexUtils;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.dukascopy.ImportInfo;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import it.unimi.dsi.fastutil.longs.Long2ObjectAVLTreeMap;
import it.unimi.dsi.fastutil.longs.Long2ObjectMap;
import java.io.File;
import java.text.DecimalFormat;
import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DarwinexImportJob
extends GridJob<Void> {
    private static final long serialVersionUID = 1L;
    public static final Logger Log = LoggerFactory.getLogger(DarwinexImportJob.class);
    DataBinWriterNew writer = null;
    String fileName;
    String tempFileName;
    private ImportInfo importInfo;
    private String path;
    private volatile boolean stopped;
    private volatile boolean paused;
    private DataManagerProgressListener listener;
    private DateTimeFormatter dateFormatter = DateTimeFormat.forPattern((String)"yyyy-MM-dd");
    private static DecimalFormat int2Form = new DecimalFormat("00");
    double lastAsk = 0.0;
    double lastBid = 0.0;
    double lastVolume = 1.0;

    public DarwinexImportJob(ImportInfo importInfo, String path, String jobId) throws Exception {
        super(jobId, 0, null);
        this.importInfo = importInfo;
        this.path = path;
    }

    private void evalFromTo(File folder) {
        Long maxDate;
        Long minDate = this.getMinMaxDate(folder.getAbsolutePath(), true);
        if (minDate != null) {
            this.importInfo.dateFrom = minDate;
        }
        if ((maxDate = this.getMinMaxDate(folder.getAbsolutePath(), false)) != null) {
            this.importInfo.dateTo = maxDate;
        }
    }

    private Long getMinMaxDate(String root, boolean min) {
        File folder = new File(root);
        if (!folder.exists()) {
            return null;
        }
        long time = 0L;
        long fileTime = 0L;
        File[] files = folder.listFiles();
        for (int i = 0; i < files.length; ++i) {
            try {
                fileTime = this.parseTime(files[i]);
            }
            catch (Exception e) {
                Log.error("Cannot parse file.", (Throwable)e);
            }
            if (time == 0L) {
                time = fileTime;
                continue;
            }
            if (min) {
                if (time <= fileTime) continue;
                time = fileTime;
                continue;
            }
            if (time >= fileTime) continue;
            time = fileTime;
        }
        return time;
    }

    private long parseTime(File file) {
        String name = file.getName();
        int pos = name.indexOf(46);
        if (pos >= 0) {
            name = name.substring(0, pos);
        }
        String[] items = name.split("_");
        return this.dateFormatter.parseMillis(items[2]);
    }

    public void messageReceived(GridMessage message) {
        super.messageReceived(message);
        switch (message.getMessageID()) {
            case 4: {
                this.stopped = true;
                break;
            }
            case 2: {
                this.paused = true;
                break;
            }
            case 3: {
                this.paused = false;
            }
        }
    }

    private void finish() {
        try {
            int totalDays = SQTime.getDaysBetween((long)this.importInfo.fromTime, (long)this.importInfo.toTime) + 1;
            long secondsRecords = totalDays * 86400;
            DataManager.updateData((String)"History", (String)this.importInfo.symbol, (long)this.importInfo.fromTime, (long)this.importInfo.toTime, (int)this.importInfo.rows, (long)secondsRecords, (int)1, (String)"TICK", (String)"Etc/UCT");
            if (BasketOfStocksManager.getInstance() != null) {
                BasketOfStocksManager.getInstance().updateGroupsOfSymbols();
                SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getBaskets(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            }
            try {
                this.writer.close();
            }
            catch (Exception exception) {
                // empty catch block
            }
            this.listener.setMessage(this.stopped ? L.t((String)"Stopped", (Object[])new Object[0]) : L.t((String)"Completed", (Object[])new Object[0]));
            new File(this.tempFileName).renameTo(new File(this.fileName));
            this.listener.onProgress(100.0);
            this.listener.onFinish();
        }
        catch (Exception e) {
            Log.error("Error while saving results", (Throwable)e);
            throw new RuntimeException(L.t((String)"Error while saving results", (Object[])new Object[0]));
        }
    }

    private void initWriter() throws Exception {
        this.listener.setMessage(L.t((String)"Preparing data files", (Object[])new Object[]{true}));
        this.writer = DataBinWriterNew.getInstance((int)2, (String)MainApp.getDataPath(), (InstrumentInfo)this.importInfo.instrumentInfo);
        this.fileName = DataManager.getDataFileName((String)"History", (String)this.importInfo.symbol, (String)"TICK", (String)"No Session");
        this.tempFileName = DataManager.getTempFileName((String)this.fileName);
        this.writer.setFileName(this.tempFileName);
        this.writer.open();
    }

    public void setProgressListener(DataManagerProgressListener progressListener) {
        this.listener = progressListener;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public Void call() throws Exception {
        try {
            this.initWriter();
            File folder = new File(new File(this.path), this.importInfo.origSymbol);
            if (!folder.exists()) {
                this.listener.setMessage(L.t((String)"Completed - no data found", (Object[])new Object[]{true}));
                Void void_ = null;
                return void_;
            }
            this.evalFromTo(folder);
            this.listener.setMessage(L.t((String)"Importing Darwinex data ...", (Object[])new Object[]{true}));
            this.listener.onProgress(1.0);
            double daysToImport = SQTime.getDaysBetween((long)this.importInfo.dateFrom, (long)this.importInfo.dateTo) + 1;
            double day = 0.0;
            Long2ObjectAVLTreeMap data = new Long2ObjectAVLTreeMap();
            for (long date = this.importInfo.dateFrom; date <= this.importInfo.dateTo; date += 86400000L) {
                String dateStr = this.dateFormatter.print(date);
                for (int hour = 0; hour < 24; ++hour) {
                    File askFile = new File(folder, this.importInfo.origSymbol + "_ASK_" + dateStr + "_" + int2Form.format(hour) + ".log.gz");
                    File bidFile = new File(folder, this.importInfo.origSymbol + "_BID_" + dateStr + "_" + int2Form.format(hour) + ".log.gz");
                    this.writeData(askFile, bidFile, (Long2ObjectAVLTreeMap<VersatileData>)data);
                }
                this.listener.onProgress((day += 1.0) / daysToImport * 100.0);
                if (this.stopped) break;
                this.checkPaused();
            }
            this.finish();
            this.sendRefreshMessage();
        }
        catch (Exception e) {
            Log.error("Error while importing Darwinex data", (Throwable)e);
            this.listener.onError(L.t((String)"Error while importing Darwinex data", (Object[])new Object[]{true}));
        }
        finally {
            DataManagerDataProgress.get().removeListener(this.importInfo.symbol);
        }
        return null;
    }

    private void writeData(File askFile, File bidFile, Long2ObjectAVLTreeMap<VersatileData> data) throws Exception {
        if (!askFile.exists() && !bidFile.exists()) {
            return;
        }
        data.clear();
        DarwinexUtils.getTickData((File)askFile, data, (boolean)true);
        DarwinexUtils.getTickData((File)bidFile, data, (boolean)false);
        for (Long2ObjectMap.Entry item : data.long2ObjectEntrySet()) {
            long time = item.getLongKey();
            VersatileData tickData = (VersatileData)item.getValue();
            if (tickData.ask == 0.0) {
                tickData.ask = this.lastAsk;
            }
            if (tickData.bid == 0.0) {
                tickData.bid = this.lastBid;
            }
            if (tickData.volume == 0.0) {
                tickData.volume = this.lastVolume;
            }
            this.lastAsk = tickData.ask;
            this.lastBid = tickData.bid;
            this.lastVolume = tickData.volume;
            this.writer.writeData(tickData);
            ++this.importInfo.rows;
            if (this.importInfo.fromTime == 0L) {
                this.importInfo.fromTime = time;
            }
            this.importInfo.toTime = time;
        }
    }

    private void checkPaused() throws InterruptedException {
        if (!this.paused) {
            return;
        }
        this.listener.onPause();
        while (this.paused && !this.stopped) {
            Thread.sleep(100L);
        }
        this.listener.onContinue();
    }

    private void sendRefreshMessage() {
        try {
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)this.importInfo.symbol, (String)"import"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        catch (Exception e) {
            Log.error("Cannot send data Websocket message. ", (Throwable)e);
        }
    }
}


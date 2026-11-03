/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.app.MainApp
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.mt5api;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.mt5api.Mt5ApiImportInfo;
import com.strategyquant.tradinglib.mt5api.Mt5ApiManager;
import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.tradinglib.python.PythonRunner;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.nio.file.Files;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Mt5ApiDownloaderJob
extends GridJob<Void> {
    private static final long serialVersionUID = 1L;
    public static final Logger Log = LoggerFactory.getLogger(Mt5ApiDownloaderJob.class);
    private DataManagerProgressListener listener;
    private DataInfo dataInfo;
    private Mt5ApiImportInfo importInfo;
    private long fromTime;
    private long toTime;
    private int rows;
    private volatile boolean paused;
    private volatile boolean stopped;

    public Mt5ApiDownloaderJob(String string, DataManagerProgressListener dataManagerProgressListener, DataInfo dataInfo, Mt5ApiImportInfo mt5ApiImportInfo) {
        super(string, 0, null);
        this.listener = dataManagerProgressListener;
        this.dataInfo = dataInfo;
        this.importInfo = mt5ApiImportInfo;
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

    private File downloadToFile() throws Exception {
        PythonRunner.ProgressCallbackAdapter progressCallbackAdapter = new PythonRunner.ProgressCallbackAdapter(){

            @Override
            public void onMessage(String string) {
                Log.debug(string);
                Mt5ApiDownloaderJob.this.listener.setMessage(string);
            }

            @Override
            public void onError(String string) {
                Log.error("Error while fetching symbol list: " + string);
                Mt5ApiDownloaderJob.this.listener.onError(string);
            }

            @Override
            public void onProgress(double d) {
                double d2 = d * 100.0;
                Mt5ApiDownloaderJob.this.listener.onProgress(d2 * 0.5);
            }

            @Override
            public void onResult(String string) {
            }
        };
        Mt5ApiManager.Source source = this.importInfo.path == null ? Mt5ApiManager.Source.installed : Mt5ApiManager.Source.portable;
        File file = Mt5ApiManager.get().downloadData(source, this.importInfo.path, this.dataInfo, this.importInfo.dateFrom, this.importInfo.dateTo, progressCallbackAdapter);
        return file;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public Void call() throws Exception {
        long l = this.dataInfo.dateFrom;
        if (l > 0L) {
            this.listener.onError("MT5 Api ticker are not updatable");
            return null;
        }
        try {
            boolean bl = this.dataInfo.timeframe.equals("TICK");
            File file = this.downloadToFile();
            this.copyData(file, bl);
            try {
                Files.delete(file.toPath());
            }
            catch (Exception exception) {
                // empty catch block
            }
            this.finish(bl);
        }
        catch (Exception exception) {
            Log.error("", (Throwable)exception);
            this.listener.onError("Error while downloading");
        }
        finally {
            this.listener.onProgress(100.0);
            this.listener.setMessage(L.t((String)"Completed", (Object[])new Object[0]));
            this.sendRefreshMessage();
        }
        return null;
    }

    public void messageReceived(GridMessage gridMessage) {
        super.messageReceived(gridMessage);
        switch (gridMessage.getMessageID()) {
            case 4: {
                this.stopped = true;
                this.listener.setMessage(L.t((String)"Stopping download - please wait", (Object[])new Object[0]));
                Mt5ApiManager.get().cancel();
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

    private void finish(boolean bl) {
        if (this.rows == 0) {
            return;
        }
        long l = bl ? (long)this.rows : (long)(this.rows * 60);
        DataManager.updateData((String)"History", (String)this.importInfo.symbol, (long)this.fromTime, (long)this.toTime, (int)this.rows, (long)l, (int)1, (String)this.dataInfo.timeframe, (String)"Exchange");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void copyData(File file, boolean bl) throws Exception {
        if (this.stopped) {
            return;
        }
        int n = bl ? 2 : 1;
        DataBinWriterNew dataBinWriterNew = DataBinWriterNew.getInstance((int)n, (String)MainApp.getDataPath(), (InstrumentInfo)this.importInfo.instrumentInfo);
        String string = DataManager.getDataFileName((String)"History", (String)this.importInfo.symbol, (String)this.dataInfo.timeframe, (String)"No Session");
        dataBinWriterNew.setFileName(string);
        dataBinWriterNew.open();
        this.fromTime = -1L;
        this.toTime = -1L;
        this.rows = 0;
        long l = file.length();
        long l2 = 0L;
        try (BufferedReader bufferedReader = new BufferedReader(new FileReader(file));){
            String string2;
            while ((string2 = bufferedReader.readLine()) != null) {
                l2 += (long)(string2.length() + 1);
                if (this.stopped) {
                    break;
                }
                this.checkPaused();
                if ((string2 = string2.trim()).isEmpty() || string2.contains("time")) continue;
                try {
                    VersatileData versatileData = bl ? this.parseTickLine(string2) : this.parseOhlcLine(string2);
                    dataBinWriterNew.writeData(versatileData);
                    ++this.rows;
                    if (this.fromTime == -1L) {
                        this.fromTime = versatileData.time;
                    }
                    this.toTime = versatileData.time;
                    this.listener.setMessage("Writing " + SQTime.formatDate((long)versatileData.time));
                }
                catch (Exception exception) {
                    Log.error("", (Throwable)exception);
                }
                finally {
                    double d = (double)l2 / (double)l;
                    this.listener.onProgress(50.0 + d * 0.5);
                }
            }
        }
        finally {
            dataBinWriterNew.close();
        }
    }

    private void sendRefreshMessage() {
        try {
            SQWebSocketManager.addToDataQueue(WSDataObjects.getData(this.importInfo.symbol, "download"), "SQUANT", "QDM", "AlgoWizard");
        }
        catch (Exception exception) {
            Log.error("Cannot send data Websocket message. ", (Throwable)exception);
        }
    }

    private VersatileData parseOhlcLine(String string) {
        VersatileData versatileData = new VersatileData();
        String[] stringArray = string.split(",");
        versatileData.time = SQTime.parseToMilis((String)stringArray[0], (String)"yyyy-MM-dd HH:mm:ss");
        versatileData.open = Double.valueOf(stringArray[1]);
        versatileData.high = Double.valueOf(stringArray[2]);
        versatileData.low = Double.valueOf(stringArray[3]);
        versatileData.close = Double.valueOf(stringArray[4]);
        versatileData.volume = Double.valueOf(stringArray[5]);
        return versatileData;
    }

    private VersatileData parseTickLine(String string) {
        long l;
        VersatileData versatileData = new VersatileData();
        String[] stringArray = string.split(",");
        versatileData.time = l = SQTime.parseToMilis((String)stringArray[0], (String)"yyyy-MM-dd HH:mm:ss.SSS");
        versatileData.ask = Double.valueOf(stringArray[2]);
        versatileData.bid = Double.valueOf(stringArray[1]);
        versatileData.volume = Double.valueOf(stringArray[4]);
        return versatileData;
    }
}

